"""Végpont-tesztek valódi Postgres-szel, a Stripe és a Resend mockolva.

Futtatás: TEST_DATABASE_URL=postgresql://... python -m pytest
A tesztek minden táblát ürítenek, ezért soha ne éles adatbázison futtasd.
"""
import os
import types

import pytest

DB_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DB_URL, reason="nincs TEST_DATABASE_URL")

from app import config, db, emailer, main, ratelimit  # noqa: E402

TAG = config.STRIPE_PRODUCT_TAG


@pytest.fixture
def client(monkeypatch):
    from fastapi.testclient import TestClient

    monkeypatch.setattr(config, "DATABASE_URL", DB_URL)
    sent = []
    monkeypatch.setattr(emailer, "_send", lambda to, subject, html: sent.append((to, subject)) or True)
    ratelimit.reset()
    with TestClient(main.app, follow_redirects=False) as c:
        with db.conn() as conn:
            conn.execute("TRUNCATE books, login_links, sessions, purchases, customers")
        c.sent = sent
        yield c


def fake_session(monkeypatch, **overrides):
    data = {
        "id": "cs_test_1", "payment_status": "paid", "metadata": {"product": TAG},
        "customer_details": {"email": "Szulo@Pelda.hu"}, "customer_email": None,
        "amount_total": 500000, "currency": "huf",
    }
    data.update(overrides)
    obj = types.SimpleNamespace(to_dict=lambda: data)
    monkeypatch.setattr(main.stripe.checkout.Session, "retrieve", lambda sid: obj)
    return data


def test_success_logs_in_once(client, monkeypatch):
    fake_session(monkeypatch)
    r = client.get("/sikeres?session_id=cs_test_1")
    assert r.status_code == 303 and r.headers["location"] == "/mesek"
    assert config.SESSION_COOKIE in r.cookies
    assert client.sent == [("Szulo@Pelda.hu", "A mesekönyvtárad elkészült")]

    # Ugyanazzal a sütivel: marad bent
    assert client.get("/sikeres?session_id=cs_test_1").headers["location"] == "/mesek"

    # Más eszközön (süti nélkül) az URL már nem léptet be, és nem megy ki újabb levél
    client.cookies.clear()
    r = client.get("/sikeres?session_id=cs_test_1")
    assert r.headers["location"] == "/?hiba=sikeres"
    assert config.SESSION_COOKIE not in r.cookies
    assert len(client.sent) == 1


def test_success_link_expires(client, monkeypatch):
    fake_session(monkeypatch)
    db.record_purchase("szulo@pelda.hu", "cs_test_1", 500000, "huf")
    with db.conn() as conn:
        conn.execute("UPDATE purchases SET created_at = now() - interval '2 hours'")
    assert client.get("/sikeres?session_id=cs_test_1").headers["location"] == "/?hiba=sikeres"


@pytest.mark.parametrize("overrides", [
    {"metadata": {}},                                           # más termék a Stripe-fiókon
    {"metadata": {"product": "valami-mas"}},
    {"customer_details": None, "customer_email": None},        # nincs e-mail cím
])
def test_success_rejects_foreign_or_incomplete(client, monkeypatch, overrides):
    fake_session(monkeypatch, **overrides)
    r = client.get("/sikeres?session_id=cs_test_1")
    assert r.headers["location"] == "/?hiba=ellenorzes"
    assert client.sent == []


def test_success_unpaid_and_garbage(client, monkeypatch):
    fake_session(monkeypatch, payment_status="unpaid")
    assert client.get("/sikeres?session_id=cs_test_1").headers["location"] == "/?hiba=fizetes"
    assert client.get("/sikeres?session_id=barmi").headers["location"] == "/?hiba=fizetes"


def webhook_event(**overrides):
    import json
    s = {"id": "cs_test_1", "payment_status": "paid", "metadata": {"product": TAG},
         "customer_details": {"email": "szulo@pelda.hu"}, "amount_total": 500000, "currency": "huf"}
    s.update(overrides)
    return json.dumps({"type": "checkout.session.completed", "data": {"object": s}})


def test_webhook_then_success(client, monkeypatch):
    monkeypatch.setattr(main.stripe.Webhook, "construct_event", lambda *a: None)
    assert client.post("/webhook", content=webhook_event()).status_code == 200
    assert client.post("/webhook", content=webhook_event()).status_code == 200  # Stripe újraküldés
    assert len(client.sent) == 1

    # A webhook nem használja el az automatikus belépést, és nem megy ki második levél
    fake_session(monkeypatch)
    assert client.get("/sikeres?session_id=cs_test_1").headers["location"] == "/mesek"
    assert len(client.sent) == 1


def test_webhook_ignores_foreign_product(client, monkeypatch):
    monkeypatch.setattr(main.stripe.Webhook, "construct_event", lambda *a: None)
    client.post("/webhook", content=webhook_event(metadata={}))
    assert client.sent == []
    assert db.get_customer_by_email("szulo@pelda.hu") is None


def test_webhook_bad_signature(client):
    assert client.post("/webhook", content=webhook_event()).status_code == 400


def test_checkout_sets_metadata_and_rate_limit(client, monkeypatch):
    calls = []
    monkeypatch.setattr(main.stripe.checkout.Session, "create",
                        lambda **kw: calls.append(kw) or types.SimpleNamespace(url="https://stripe.test"))
    for _ in range(10):
        assert client.post("/api/checkout", json={"email": "a@pelda.hu"}).status_code == 200
    assert calls[0]["metadata"] == {"product": TAG}
    assert client.post("/api/checkout", json={"email": "a@pelda.hu"}).status_code == 429


def test_login_link_flow_and_limits(client):
    db.record_purchase("szulo@pelda.hu", "cs_test_1", 500000, "huf")
    for _ in range(5):
        assert client.post("/api/login-link", json={"email": "SZULO@pelda.hu"}).json() == {"ok": True}
    assert len(client.sent) == 3                     # címenként legfeljebb 3 levél / 15 perc

    for _ in range(5):                               # ismeretlen cím: ugyanaz a válasz, levél nélkül
        client.post("/api/login-link", json={"email": "idegen@pelda.hu"})
    assert len(client.sent) == 3
    assert client.post("/api/login-link", json={"email": "x@pelda.hu"}).status_code == 429  # IP-korlát

    link = db.create_login_link(db.get_customer_by_email("szulo@pelda.hu")["id"])
    token = link.split("token=")[1]
    assert client.get(f"/belepes?token={token}").status_code == 200
    r = client.post("/belepes", data={"token": token})
    assert r.headers["location"] == "/mesek" and config.SESSION_COOKIE in r.cookies
    client.cookies.clear()
    assert client.post("/belepes", data={"token": token}).headers["location"] == "/?hiba=link"


def test_cleanup_expired(client):
    cid, _ = db.record_purchase("szulo@pelda.hu", "cs_test_1", 500000, "huf")
    with db.conn() as conn:
        conn.execute("INSERT INTO sessions VALUES ('old', %s, now(), now() - interval '1 day')", (cid,))
        conn.execute("INSERT INTO login_links VALUES ('old', %s, now() - interval '2 days', NULL)", (cid,))
    db.cleanup_expired()
    with db.conn() as conn:
        assert conn.execute("SELECT count(*) AS n FROM sessions").fetchone()["n"] == 0
        assert conn.execute("SELECT count(*) AS n FROM login_links").fetchone()["n"] == 0


def test_books_roundtrip(client, monkeypatch):
    fake_session(monkeypatch)
    client.get("/sikeres?session_id=cs_test_1")
    r = client.post("/api/books", json={"story_id": "roka", "fields": {"nev": "marcell"}})
    assert r.status_code == 201
    pdf = client.get(r.json()["pdf"])
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    forms = client.post("/api/preview", json={"story_id": "roka", "fields": {"nev": "Marcell"}}).json()
    assert forms["forms"][0]["forms"] == [{"key": "nev+t", "form": "Marcellt"}]
