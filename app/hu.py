"""Magyar toldalékolás nevekhez és egyszerű főnevekhez.

A sablonokban a ragot mély hangrendű alakban kell megadni (pl. {nev+val}, {nev+nak}),
a motor ebből képzi a helyes alakot: Bencével, Ábellel, Zsófival, Gergőhöz, Örsöt.

Heurisztika: a legtöbb magyar és gyakori külföldi névre jó, de nem tévedhetetlen.
Ezért a felületen a szülő látja és szükség esetén javíthatja az alakokat.
"""

BACK = set("aáoóuú")
FRONT_UNROUNDED = set("eéií")
FRONT_ROUNDED = set("öőüű")
VOWELS = BACK | FRONT_UNROUNDED | FRONT_ROUNDED

# Hosszú (kétjegyű / háromjegyű) mássalhangzók, a leghosszabb elöl
DIGRAPHS = ["dzs", "cs", "dz", "gy", "ly", "ny", "sz", "ty", "zs"]

# rag (kanonikus, mély alak) -> (mély, magas, magas-ajakkerekítéses)
SUFFIXES = {
    "nak": ("nak", "nek", "nek"),
    "ban": ("ban", "ben", "ben"),
    "ba": ("ba", "be", "be"),
    "bol": ("ból", "ből", "ből"),
    "rol": ("ról", "ről", "ről"),
    "ra": ("ra", "re", "re"),
    "tol": ("tól", "től", "től"),
    "nal": ("nál", "nél", "nél"),
    "hoz": ("hoz", "hez", "höz"),
    "ert": ("ért", "ért", "ért"),
    "ig": ("ig", "ig", "ig"),
    "kent": ("ként", "ként", "ként"),
    "ek": ("ék", "ék", "ék"),       # Bencéék, Annáék
}
ASSIMILATING = {"val": ("al", "el", "el"), "va": ("á", "é", "é")}  # -val/-vel, -vá/-vé
ACCUSATIVE = "t"

# ékezet nélküli írásmódok elfogadása a sablonban
ALIASES = {"ból": "bol", "ről": "rol", "ról": "rol", "tól": "tol", "nál": "nal", "ért": "ert",
           "ként": "kent", "vá": "va", "ék": "ek"}

ALL_SUFFIXES = set(SUFFIXES) | set(ASSIMILATING) | {ACCUSATIVE}

# Ezek után a tárgyrag kötőhang nélkül járul (ha előttük magánhangzó áll): Ábelt, Jánost
SONORANT_SIBILANT = ("ny", "ly", "sz", "zs", "l", "r", "n", "j", "s", "z")


def normalize_suffix(suffix: str) -> str:
    s = suffix.strip().lower()
    return ALIASES.get(s, s)


def harmony(word: str) -> int:
    """0 = mély, 1 = magas, 2 = magas, ajakkerekítéses."""
    w = word.lower()
    vowels = [c for c in w if c in VOWELS]
    if not vowels:
        return 1
    last = vowels[-1]
    if last in BACK:
        return 0
    if last in FRONT_ROUNDED:
        return 2
    if last in "ií":
        # Az i/í semleges: a korábbi magánhangzó dönt (Zsófi -> Zsófival, Lili -> Lilivel)
        for v in reversed(vowels):
            if v in BACK:
                return 0
            if v in FRONT_ROUNDED:
                return 2
            if v in "eé":
                return 1
        return 1
    # e / é: magánhangzóra végződő, mély elemet tartalmazó szó mély (Máté -> Mátéval)
    if w.endswith(last) and any(v in BACK for v in vowels):
        return 0
    return 1


def _lengthen(word: str) -> str:
    if word.endswith("a"):
        return word[:-1] + "á"
    if word.endswith("e"):
        return word[:-1] + "é"
    return word


def _last_consonant(word: str) -> str:
    w = word.lower()
    for d in DIGRAPHS:
        if w.endswith(d):
            return d
    return w[-1]


def _ends_with_vowel(word: str) -> bool:
    return word[-1].lower() in VOWELS


def _double_final(word: str) -> str:
    """Ábel -> Ábell, Bálint -> Bálintt, Kovács -> Kováccs."""
    w = word.lower()
    if w.endswith("x"):
        return word + "sz"                      # Max -> Maxszal
    cons = _last_consonant(word)
    # már eleve kettőzött: Marcell, Anett, Benett, Emmett -> nem triplázunk
    if len(w) > len(cons) and w[-len(cons) - 1] == cons[0] and len(cons) == 1:
        return word
    if len(cons) == 1:
        return word + word[-1]
    # kétjegyű betű kettőzése: az első jelet ismételjük (sz -> ssz, cs -> ccs)
    return word[: -len(cons)] + word[-len(cons)] + word[-len(cons):]


def inflect(word: str, suffix: str) -> str:
    word = word.strip()
    if not word:
        return word
    suffix = normalize_suffix(suffix)
    h = harmony(word)
    vowel_final = _ends_with_vowel(word)

    if suffix == ACCUSATIVE:
        if vowel_final:
            return _lengthen(word) + "t"
        w = word.lower()
        cons = _last_consonant(word)
        before = w[: -len(cons)]
        if cons in SONORANT_SIBILANT and before and before[-1] in VOWELS:
            return word + "t"
        return word + ("ot", "et", "öt")[h]

    if suffix in ASSIMILATING:
        tail = ASSIMILATING[suffix][h]
        if vowel_final:
            return _lengthen(word) + "v" + tail
        return _double_final(word) + tail

    if suffix in SUFFIXES:
        forms = SUFFIXES[suffix]
        base = word if suffix == "kent" else _lengthen(word)
        return base + forms[h]

    raise ValueError(f"Ismeretlen rag: {suffix}")


def article(word: str) -> str:
    """Határozott névelő: a / az."""
    return "az" if word[:1].lower() in VOWELS else "a"
