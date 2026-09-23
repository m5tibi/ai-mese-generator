import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
STORIES_DIR = BASE_DIR / "stories"


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


# Nyilvános URL, pl. https://ai-mese-generator.onrender.com (a végén perjel nélkül)
BASE_URL = env("BASE_URL", "http://localhost:10000").rstrip("/")

DATABASE_URL = env("DATABASE_URL")

STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET")
PRICE_HUF = int(env("PRICE_HUF", "5000"))
PRODUCT_NAME = env("PRODUCT_NAME", "Varázslatos Mesék - Örökös hozzáférés")

RESEND_API_KEY = env("RESEND_API_KEY")
# Élesben ellenőrzött domainről kell küldeni, pl. "Varázslatos Mesék <mese@sajatdomain.hu>"
EMAIL_FROM = env("EMAIL_FROM", "Varázslatos Mesék <onboarding@resend.dev>")

SESSION_COOKIE = "mese_session"
SESSION_DAYS = 180
LOGIN_LINK_MINUTES = 60
COOKIE_SECURE = BASE_URL.startswith("https://")
