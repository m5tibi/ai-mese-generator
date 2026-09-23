# Varázslatos Mesék

Előre megírt, illusztrált esti mesék, amelyekben a gyerek a főszereplő. A szülő egyszer fizet
(Stripe), utána választ a mesék közül, beírja a gyerek nevét és a mese többi személyre szabható
részét (pl. plüssállat neve, kedvenc nasi), és letölti a mesekönyvet PDF-ben.

A névcsere nem egyszerű szövegcsere: a program magyar toldalékolással illeszti a neveket
(Bencével, Ábellel, Zsófival, Gergőhöz), a szülő pedig látja és szükség esetén javíthatja az alakokat.

## Felépítés

```
app/
  main.py            FastAPI: oldalak, fizetés, belépés, mesekönyvek API
  templates.py       mesesablonok betöltése, ellenőrzése, kitöltése
  hu.py              magyar toldalékolás (magánhangzó-illeszkedés, hasonulás)
  pdf.py             A5-ös mesekönyv PDF (ReportLab)
  db.py              Postgres (vásárlók, belépések, mentett mesekönyvek)
  emailer.py         e-mailek (Resend)
  check_stories.py   mesék ellenőrzése, minta PDF-ek
stories/             a mesék, mesénként egy mappa; írási útmutató: stories/README.md
static/              index.html (főoldal, katalógus, vásárlás), app.html (mesekönyvtár)
assets/              CSS, betűtípusok
```

## Folyamat

1. Főoldal: katalógus, e-mail cím, Stripe Checkout.
2. Fizetés után a `/sikeres?session_id=...` oldalon a szerver ellenőrzi a fizetést, beléptet
   (httpOnly süti), és e-mailben belépési linket küld.
3. `/mesek`: mese kiválasztása, adatok, letöltés. A mentett mesekönyvek újra letölthetők vagy törölhetők.
   A PDF letöltéskor készül, így ha javítasz egy mesén, a régi mesekönyvek is a javított szöveggel jönnek le.
4. Más eszközön: főoldal, „Belépési link küldése” (egyszer használható, 60 percig érvényes).

## Helyi futtatás

```bash
pip install -r requirements.txt
cp .env.example .env   # töltsd ki, majd: export $(grep -v '^#' .env | xargs)
python -m app.check_stories
uvicorn app.main:app --reload --port 10000
stripe listen --forward-to localhost:10000/webhook
```

## Render

A `render.yaml` létrehozza a webszolgáltatást és egy Postgres adatbázist. A titkos kulcsokat a
Render felületén kell megadni. Stripe webhook: `https://<domain>/webhook`, esemény:
`checkout.session.completed`. A Render ingyenes Postgres példánya korlátozott ideig él;
tartós használatra fizetős csomag vagy külső Postgres (pl. Supabase) kell.
