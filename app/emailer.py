import logging
from html import escape

import requests

from . import config

log = logging.getLogger("mese.email")


def _send(to: str, subject: str, html: str) -> bool:
    if not config.RESEND_API_KEY:
        log.warning("Nincs RESEND_API_KEY, az e-mail nem ment ki: %s -> %s", subject, to)
        return False
    try:
        r = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {config.RESEND_API_KEY}"},
            json={"from": config.EMAIL_FROM, "to": [to], "subject": subject, "html": html},
            timeout=20,
        )
        if r.status_code >= 300:
            log.error("Resend hiba %s: %s", r.status_code, r.text[:500])
            return False
        return True
    except Exception:
        log.exception("E-mail küldési hiba")
        return False


def _layout(body: str) -> str:
    return (
        '<div style="font-family:Georgia,serif;color:#1F2A44;max-width:520px;margin:auto;'
        'line-height:1.6;font-size:16px">' + body + "</div>"
    )


def _button(url: str, label: str) -> str:
    return (
        f'<p><a href="{escape(url)}" style="display:inline-block;background:#1F2A44;color:#fff;'
        f'padding:12px 22px;border-radius:24px;text-decoration:none;font-family:Arial,sans-serif">'
        f"{escape(label)}</a></p>"
    )


def send_welcome(to: str, login_url: str) -> bool:
    body = (
        "<h2>Köszönjük a vásárlást!</h2>"
        "<p>A hozzáférésed aktív. Az alábbi gombbal bármelyik eszközön beléphetsz, "
        "és elkészítheted az első mesét.</p>"
        + _button(login_url, "Belépés a mesékhez")
        + f"<p style='color:#6B7385;font-size:14px'>A link {config.LOGIN_LINK_MINUTES} percig érvényes, "
        "és egyszer használható. Később a főoldalon bármikor kérhetsz újat.</p>"
    )
    return _send(to, "A mesekönyvtárad elkészült", _layout(body))


def send_login_link(to: str, login_url: str) -> bool:
    body = (
        "<p>Belépési linket kértél a Varázslatos Mesékhez.</p>"
        + _button(login_url, "Belépés")
        + f"<p style='color:#6B7385;font-size:14px'>A link {config.LOGIN_LINK_MINUTES} percig érvényes. "
        "Ha nem te kérted, nyugodtan hagyd figyelmen kívül ezt a levelet.</p>"
    )
    return _send(to, "Belépési link – Varázslatos Mesék", _layout(body))
