import hashlib
import secrets
import uuid
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id          BIGSERIAL PRIMARY KEY,
    email       TEXT UNIQUE NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS purchases (
    stripe_session_id TEXT PRIMARY KEY,
    customer_id       BIGINT NOT NULL REFERENCES customers(id),
    amount            INTEGER,
    currency          TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash  TEXT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at  TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS login_links (
    token_hash  TEXT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS books (
    id          UUID PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    story_slug  TEXT NOT NULL,
    child_name  TEXT NOT NULL,
    gender      TEXT NOT NULL,
    fields      JSONB NOT NULL,
    overrides   JSONB NOT NULL DEFAULT '{}',
    dedication  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS books_customer_idx ON books (customer_id, created_at DESC);
"""


@contextmanager
def conn():
    with psycopg.connect(config.DATABASE_URL, row_factory=dict_row) as c:
        yield c


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def init_db():
    with conn() as c:
        c.execute(SCHEMA)


# --- Vásárlók ---------------------------------------------------------------

def record_purchase(email: str, session_id: str, amount: int | None, currency: str | None):
    """Rögzíti a vásárlást. Visszaadja: (customer_id, új_vásárlás_e). Idempotens."""
    email = email.strip().lower()
    with conn() as c:
        row = c.execute(
            "INSERT INTO customers (email) VALUES (%s) "
            "ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email RETURNING id",
            (email,),
        ).fetchone()
        customer_id = row["id"]
        cur = c.execute(
            "INSERT INTO purchases (stripe_session_id, customer_id, amount, currency) "
            "VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (session_id, customer_id, amount, currency),
        )
        return customer_id, cur.rowcount == 1


def get_customer_by_email(email: str):
    with conn() as c:
        return c.execute(
            "SELECT * FROM customers WHERE email=%s", (email.strip().lower(),)
        ).fetchone()


# --- Belépés ----------------------------------------------------------------

def create_session(customer_id: int) -> str:
    token = secrets.token_urlsafe(32)
    with conn() as c:
        c.execute(
            "INSERT INTO sessions (token_hash, customer_id, expires_at) "
            "VALUES (%s, %s, now() + make_interval(days => %s))",
            (_hash(token), customer_id, config.SESSION_DAYS),
        )
    return token


def get_customer_by_session(token: str | None):
    if not token:
        return None
    with conn() as c:
        return c.execute(
            "SELECT c.* FROM sessions s JOIN customers c ON c.id = s.customer_id "
            "WHERE s.token_hash=%s AND s.expires_at > now()",
            (_hash(token),),
        ).fetchone()


def delete_session(token: str):
    with conn() as c:
        c.execute("DELETE FROM sessions WHERE token_hash=%s", (_hash(token),))


def create_login_link(customer_id: int) -> str:
    token = secrets.token_urlsafe(32)
    with conn() as c:
        c.execute(
            "INSERT INTO login_links (token_hash, customer_id, expires_at) "
            "VALUES (%s, %s, now() + make_interval(mins => %s))",
            (_hash(token), customer_id, config.LOGIN_LINK_MINUTES),
        )
    return f"{config.BASE_URL}/belepes?token={token}"


def consume_login_link(token: str):
    """Egyszer használható link. Visszaadja a customer_id-t vagy None-t."""
    with conn() as c:
        row = c.execute(
            "UPDATE login_links SET used_at=now() "
            "WHERE token_hash=%s AND used_at IS NULL AND expires_at > now() "
            "RETURNING customer_id",
            (_hash(token),),
        ).fetchone()
        return row["customer_id"] if row else None


# --- Személyre szabott mesék ---------------------------------------------------

def create_book(customer_id: int, story_slug: str, gender: str, fields: dict,
                overrides: dict, dedication: str | None) -> str:
    book_id = str(uuid.uuid4())
    with conn() as c:
        c.execute(
            "INSERT INTO books (id, customer_id, story_slug, child_name, gender, fields, overrides, dedication) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (book_id, customer_id, story_slug, fields["nev"], gender, Jsonb(fields), Jsonb(overrides), dedication),
        )
    return book_id


def get_book(customer_id: int, book_id: str):
    try:
        uuid.UUID(book_id)
    except ValueError:
        return None
    with conn() as c:
        return c.execute(
            "SELECT * FROM books WHERE id=%s AND customer_id=%s", (book_id, customer_id)
        ).fetchone()


def list_books(customer_id: int, limit: int = 100):
    with conn() as c:
        return c.execute(
            "SELECT id, story_slug, child_name, created_at FROM books "
            "WHERE customer_id=%s ORDER BY created_at DESC LIMIT %s",
            (customer_id, limit),
        ).fetchall()


def delete_book(customer_id: int, book_id: str) -> bool:
    try:
        uuid.UUID(book_id)
    except ValueError:
        return False
    with conn() as c:
        return c.execute(
            "DELETE FROM books WHERE id=%s AND customer_id=%s", (book_id, customer_id)
        ).rowcount == 1
