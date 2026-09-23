# Mesék írása

Minden mese egy külön mappa ebben a könyvtárban. A mappa neve a mese azonosítója
(ékezet és szóköz nélkül, pl. `roka`, `kis-hableany`). A mappában van egy `mese.md` és a képek.

```
stories/
  roka/
    mese.md
    borito.jpeg
    1.jpeg
    2.jpeg
```

Új mese: hozz létre egy mappát, írd meg a `mese.md`-t, futtasd le az ellenőrzést (lent), és pushold.
A szerver induláskor tölti be a meséket.

## A mese.md felépítése

```markdown
---
cim: A bátor kis róka és a titokzatos erdő
leiras: Rövid ismertető a mesekatalógusba (1–2 mondat).
korosztaly: 3–7 év
sorrend: 1              # a katalógusban ez alapján rendez
borito: borito.jpeg     # nem kötelező
mezok:                  # a névén kívül a szülő által átírható dolgok
  - kulcs: plussz
    cimke: Kedvenc plüssállatának neve
    alapertelmezes: Bogyó
    sugo: Ő is elkíséri a kalandra.      # nem kötelező magyarázó szöveg
  - kulcs: etel
    cimke: Kedvenc nasija
    tipus: szo            # nev (alapértelmezett, nagy kezdőbetű) vagy szo (köznév)
    alapertelmezes: mézeskalács
---

# Első fejezet címe

![](1.jpeg)

Egyszer volt, hol nem volt, élt egy {kisfiú|kislány}, akit úgy hívtak: {nev}.

Második bekezdés. A bekezdéseket üres sor választja el.

# Második fejezet címe
...
```

A gyermek neve (`nev`) mindig van, ezt nem kell a `mezok` közé felvenni. Minden más mezőnek
kell alapértelmezés (ha a szülő üresen hagyja), vagy `kotelezo: true`.

## Helyőrzők

| Írd így                | Eredmény (Bence / Ábel / Zsófi)            |
|------------------------|--------------------------------------------|
| `{nev}`                | Bence, Ábel, Zsófi                         |
| `{nev+val}`            | Bencével, Ábellel, Zsófival                |
| `{nev+t}`              | Bencét, Ábelt, Zsófit                      |
| `{nev+nak}`            | Bencének, Ábelnek, Zsófinak                |
| `{nev+hoz}`            | Bencéhez, Ábelhez, Zsófihoz                |
| `{kisfiú\|kislány}`    | fiúnál az első, lánynál a második          |
| `{az etel+t}`          | a mézeskalácsot, az almát                  |
| `{Etel}`               | nagy kezdőbetűvel (mondat elején)          |

A ragot mindig **mély hangrendű** alakban írd, a program alakítja át:
`val` (-val/-vel), `va` (-vá/-vé), `t` (tárgyeset), `nak`, `ban`, `ba`, `bol`, `rol`, `ra`,
`tol`, `nal`, `hoz`, `ert`, `ig`, `kent`, `ek` (Bencéék). Az ékezetes írás is jó (`ból`, `ról`).

Birtokos alakokat (Bence kutyája, Bencéé) nem tud a program. Ezeket írd körül:
„{nev} kutyája” helyett „a kutya, akit {nev} a legjobban szeretett”.

**Köznévnél** (tipus: szo) a szabálytalan tövek (ló → lovat, kenyér → kenyeret) hibásak lehetnek.
Ilyen mezőben a szülőtől egy egyszerű szót kérj, és a súgóban adj rá példát.

A szülő a felületen látja, milyen alakban kerül a név a mesébe, és ha kell, kijavíthatja.

## Képek

A `![](fajl.jpeg)` sor a fejezet illusztrációja (fejezetenként egy). JPEG vagy PNG, nagyjából
1000 px széles elég. Fekvő és álló kép is jó, a program arányosan méretezi.

## Ellenőrzés

```bash
python -m app.check_stories          # hibák listája + minta PDF-ek a proof/ mappába
```

Minden mesét három mintanévvel (Bence, Zsófi, Ábel) készít el, így átolvashatod a ragozást.
