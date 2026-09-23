import json
import logging
import re
import unicodedata
from contextlib import asynccontextmanager
from typing import Literal
from html import escape
from urllib.parse import parse_qs, quote

import stripe
from fastapi import Cookie, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field, field_validator

from . import config, db, emailer, pdf, templates

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("mese")

stripe.api_key = config.STRIPE_SECRET_KEY


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    templates.load_all()
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
app.mount("/assets", StaticFiles(directory=config.ASSETS_DIR), name="assets")

IMAGE_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


@app.get("/stories/{slug}/{filename}", include_in_schema=False)
def story_image(slug: str, filename: str):
    """Csak a borítóképek publikusak, a mese szövege nem."""
    story = templates.get(slug)
    if not story or not story.cover or story.cover.name != filename:
        raise HTTPException(404)
    return FileResponse(story.cover, media_type=IMAGE_TYPES.get(story.cover.suffix.lower()),
                        headers={"Cache-Control": "public, max-age=86400"})


# --- Segédfüggvények ----------------------------------------------------------

def current_customer(token: str | None):
    customer = db.get_customer_by_session(token)
    if not customer:
        raise HTTPException(status_code=401, detail="Lépj be újra a folytatáshoz.")
    return customer


def _login_response(customer_id: int, target: str = "/mesek") -> RedirectResponse:
    token = db.create_session(customer_id)
    resp = RedirectResponse(target, status_code=303)
    resp.set_cookie(
        config.SESSION_COOKIE, token,
        max_age=config.SESSION_DAYS * 86400, httponly=True,
        secure=config.COOKIE_SECURE, samesite="lax",
    )
    return resp


def _ascii_filename(name: str) -> str:
    base = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    base = re.sub(r"[^A-Za-z0-9]+", "_", base).strip("_")
    return base or "mese"


# --- Oldalak ---------------------------------------------------------------------

@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
def index():
    html = (config.STATIC_DIR / "index.html").read_text(encoding="utf-8")
    price = f"{config.PRICE_HUF:,}".replace(",", "\u00a0")  # 5 000
    return HTMLResponse(html.replace("{{PRICE}}", price))


@app.get("/mesek", include_in_schema=False)
def app_page(mese_session: str | None = Cookie(default=None)):
    if not db.get_customer_by_session(mese_session):
        return RedirectResponse("/?belepes=1", status_code=303)
    return FileResponse(config.STATIC_DIR / "app.html")


@app.get("/sikeres", include_in_schema=False)
def payment_success(session_id: str = ""):
    """A Stripe ide irányít fizetés után. Ellenőrizzük a fizetést és beléptetjük a vevőt."""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception:
        log.exception("Stripe session lekérési hiba")
        return RedirectResponse("/?hiba=fizetes", status_code=303)
    if session.payment_status != "paid":
        return RedirectResponse("/?hiba=fizetes", status_code=303)

    email = (session.customer_details.email if session.customer_details else None) or session.customer_email
    customer_id, is_new = db.record_purchase(email, session.id, session.amount_total, session.currency)
    if is_new:
        emailer.send_welcome(email, db.create_login_link(customer_id))
    return _login_response(customer_id)


@app.get("/belepes", include_in_schema=False)
def login_page(token: str = "", mese_session: str | None = Cookie(default=None)):
    """A GET nem használja el a linket: a levelezők és vírusirtók linkellenőrzői
    megnyitják a linkeket, mielőtt a felhasználó rákattintana. A belépés egy gombnyomással
    (POST) történik, ezt a linkellenőrzők nem csinálják meg."""
    if db.get_customer_by_session(mese_session):
        return RedirectResponse("/mesek", status_code=303)
    if not token or not db.login_link_valid(token):
        return RedirectResponse("/?hiba=link", status_code=303)
    html = (config.STATIC_DIR / "belepes.html").read_text(encoding="utf-8")
    return HTMLResponse(html.replace("{{TOKEN}}", escape(token, quote=True)),
                        headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})


@app.post("/belepes", include_in_schema=False)
async def login_with_link(request: Request):
    form = parse_qs((await request.body()).decode("utf-8", "ignore"))
    token = (form.get("token") or [""])[0]
    customer_id = db.consume_login_link(token) if token else None
    if not customer_id:
        return RedirectResponse("/?hiba=link", status_code=303)
    return _login_response(customer_id)


@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"ok": True}


# --- Fizetés -----------------------------------------------------------------------

class CheckoutIn(BaseModel):
    email: EmailStr


@app.post("/api/checkout")
def create_checkout(body: CheckoutIn):
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            customer_email=body.email,
            line_items=[{
                "price_data": {
                    "currency": "huf",
                    "product_data": {"name": config.PRODUCT_NAME},
                    "unit_amount": config.PRICE_HUF * 100,  # a Stripe a HUF-ot fillérben kéri
                },
                "quantity": 1,
            }],
            success_url=f"{config.BASE_URL}/sikeres?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{config.BASE_URL}/",
            locale="hu",
            managed_payments={"enabled": False},
        )
    except Exception:
        log.exception("Stripe checkout hiba")
        raise HTTPException(502, "A fizetési oldal most nem érhető el. Próbáld újra pár perc múlva.")
    return {"url": session.url}


@app.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request):
    payload = await request.body()
    try:
        stripe.Webhook.construct_event(
            payload, request.headers.get("stripe-signature", ""), config.STRIPE_WEBHOOK_SECRET
        )
    except Exception:
        raise HTTPException(400, "Érvénytelen aláírás")

    event = json.loads(payload)  # az aláírás már ellenőrizve
    if event.get("type") == "checkout.session.completed":
        s = event["data"]["object"]
        email = (s.get("customer_details") or {}).get("email") or s.get("customer_email")
        if s.get("payment_status") == "paid" and email:
            customer_id, is_new = db.record_purchase(email, s["id"], s.get("amount_total"), s.get("currency"))
            if is_new:
                emailer.send_welcome(email, db.create_login_link(customer_id))
    return {"received": True}


# --- Belépés -------------------------------------------------------------------------

class LoginLinkIn(BaseModel):
    email: EmailStr


@app.post("/api/login-link")
def request_login_link(body: LoginLinkIn):
    customer = db.get_customer_by_email(body.email)
    if customer:
        emailer.send_login_link(customer["email"], db.create_login_link(customer["id"]))
    # Mindig ugyanazt válaszoljuk, hogy ne lehessen kideríteni, ki vásárolt
    return {"ok": True}


@app.post("/api/logout")
def logout(mese_session: str | None = Cookie(default=None)):
    if mese_session:
        db.delete_session(mese_session)
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(config.SESSION_COOKIE)
    return resp


@app.get("/api/me")
def me(mese_session: str | None = Cookie(default=None)):
    c = current_customer(mese_session)
    return {"email": c["email"]}


# --- Mesék --------------------------------------------------------------------------

@app.get("/api/catalog")
def catalog():
    return {"themes": templates.themes(), "stories": [s.public() for s in templates.catalog()]}


class BookIn(BaseModel):
    story_id: str = Field(max_length=60)
    gender: Literal["fiu", "lany"] = "fiu"
    fields: dict[str, str] = Field(default_factory=dict)
    overrides: dict[str, str] = Field(default_factory=dict)
    dedication: str | None = Field(default=None, max_length=300)

    @field_validator("dedication", mode="before")
    @classmethod
    def clean_dedication(cls, v):
        if not isinstance(v, str):
            return v
        v = "".join(ch for ch in v if unicodedata.category(ch)[0] != "C" or ch == "\n")
        v = re.sub(r"\n{3,}", "\n\n", v).strip()
        return v or None


def _prepare(body: BookIn):
    story = templates.get(body.story_id)
    if not story:
        raise HTTPException(404, "Ez a mese már nem érhető el.")
    if len(body.fields) > 20 or len(body.overrides) > 50:
        raise HTTPException(422, "Túl sok mező.")
    try:
        values = templates.clean_values(story, body.fields)
        overrides = templates.clean_overrides(story, body.overrides)
    except templates.ValueProblem as e:
        raise HTTPException(422, str(e))
    return story, values, overrides


@app.post("/api/preview")
def preview(body: BookIn):
    """A mesében használt ragozott alakok, hogy a szülő ellenőrizhesse (belépés nélkül is)."""
    story, values, overrides = _prepare(body)
    return {"forms": templates.word_forms(story, values, overrides)}


@app.post("/api/books", status_code=201)
def create_book(body: BookIn, mese_session: str | None = Cookie(default=None)):
    c = current_customer(mese_session)
    story, values, overrides = _prepare(body)
    book_id = db.create_book(c["id"], story.slug, body.gender, values, overrides, body.dedication)
    return {"id": book_id, "pdf": f"/api/books/{book_id}/pdf"}


@app.get("/api/books")
def list_books(mese_session: str | None = Cookie(default=None)):
    c = current_customer(mese_session)
    out = []
    for r in db.list_books(c["id"]):
        story = templates.get(r["story_slug"])
        out.append({
            "id": str(r["id"]), "child_name": r["child_name"],
            "title": story.title if story else "Már nem elérhető mese",
            "available": story is not None, "created_at": r["created_at"].isoformat(),
        })
    return out


@app.delete("/api/books/{book_id}")
def delete_book(book_id: str, mese_session: str | None = Cookie(default=None)):
    c = current_customer(mese_session)
    if not db.delete_book(c["id"], book_id):
        raise HTTPException(404, "Nincs ilyen mese.")
    return {"ok": True}


@app.get("/api/books/{book_id}/pdf")
def download_pdf(book_id: str, mese_session: str | None = Cookie(default=None)):
    c = current_customer(mese_session)
    b = db.get_book(c["id"], book_id)
    story = templates.get(b["story_slug"]) if b else None
    if not b or not story:
        raise HTTPException(404, "Ez a mese nem érhető el.")
    # A sablon közben változhatott (pl. új mező), ezért újra ellenőrizzük az értékeket
    try:
        values = templates.clean_values(story, b["fields"])
    except templates.ValueProblem as e:
        raise HTTPException(409, f"A mese frissült, készítsd el újra. ({e})")
    book = templates.render(story, values, b["gender"], b["overrides"], b["dedication"])
    name = b["child_name"]
    disposition = (
        f'attachment; filename="mese_{_ascii_filename(name)}.pdf"; '
        f"filename*=UTF-8''{quote(f'mese_{name}.pdf')}"
    )
    return Response(pdf.build_pdf(book), media_type="application/pdf",
                    headers={"Content-Disposition": disposition})
