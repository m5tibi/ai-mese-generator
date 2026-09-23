"""Előre megírt mesék betöltése és személyre szabása.

Minden mese egy mappa a stories/ alatt, benne egy mese.md és a képek.
A formátum leírása: stories/README.md
"""
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import config, hu

log = logging.getLogger("mese.templates")

PLACEHOLDER = re.compile(r"\{([^{}\n]+)\}")
SLOT = re.compile(r"^(?:(?P<art>[Aa]z?) )?(?P<key>[^\W\d]\w*)(?:\+(?P<rag>\w+))?$")
IMAGE_LINE = re.compile(r"^!\[[^\]]*\]\(([^)\s]+)\)\s*$")
VALUE_OK = re.compile(r"^[^\W\d_]+(?:[ .'’-]+[^\W\d_]+)*\.?$")

BUILTIN_FIELDS = [{"kulcs": "nev", "cimke": "A gyermek neve", "tipus": "nev", "kotelezo": True}]


class StoryError(Exception):
    pass


class ValueProblem(ValueError):
    pass


@dataclass
class Chapter:
    title: str
    image: Path | None
    paragraphs: list[str]


@dataclass
class Story:
    slug: str
    folder: Path
    title: str
    description: str
    age: str
    order: int
    cover: Path | None
    fields: list[dict]
    chapters: list[Chapter]
    uses_gender: bool = False
    slots: set = field(default_factory=set)   # {(kulcs, rag)}
    themes: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def field(self, key: str) -> dict | None:
        return next((f for f in self.fields if f["kulcs"] == key), None)

    def public(self) -> dict:
        return {
            "id": self.slug,
            "title": self.title,
            "description": self.description,
            "age": self.age,
            "cover": f"/stories/{self.slug}/{self.cover.name}" if self.cover else None,
            "uses_gender": self.uses_gender,
            "themes": self.themes,
            "fields": [
                {"key": f["kulcs"], "label": f["cimke"], "default": f.get("alapertelmezes", ""),
                 "required": bool(f.get("kotelezo")), "hint": f.get("sugo", "")}
                for f in self.fields
            ],
        }


# --- Betöltés ------------------------------------------------------------------

def _split_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        raise StoryError("Hiányzik a fejléc (--- ... ---)")
    _, head, body = text.split("---", 2)
    meta = yaml.safe_load(head) or {}
    if not isinstance(meta, dict):
        raise StoryError("A fejléc nem érvényes YAML")
    return meta, body


def _parse_body(body: str, folder: Path, warnings: list) -> list[Chapter]:
    chapters: list[Chapter] = []
    current = None
    buf: list[str] = []

    def flush_paragraph():
        if buf and current is not None:
            current.paragraphs.append(" ".join(s.strip() for s in buf))
        buf.clear()

    for line in body.splitlines():
        if line.startswith("# "):
            flush_paragraph()
            current = Chapter(title=line[2:].strip(), image=None, paragraphs=[])
            chapters.append(current)
            continue
        if current is None:
            if line.strip():
                raise StoryError("A szöveg előtt kell egy '# Fejezetcím' sor")
            continue
        m = IMAGE_LINE.match(line.strip())
        if m:
            flush_paragraph()
            path = folder / m.group(1)
            if path.exists():
                current.image = path
            else:
                warnings.append(f"Hiányzó kép: {m.group(1)} ({current.title})")
        elif not line.strip():
            flush_paragraph()
        else:
            buf.append(line)
    flush_paragraph()
    if not chapters:
        raise StoryError("Nincs egyetlen fejezet sem")
    return chapters


def _scan_slots(texts: list[str], known: set[str]) -> tuple[set, bool]:
    slots, uses_gender = set(), False
    for text in texts:
        for m in PLACEHOLDER.finditer(text):
            inner = m.group(1)
            if "|" in inner:
                if inner.count("|") != 1:
                    raise StoryError(f"A {{fiú|lány}} választásban pontosan egy | kell: {{{inner}}}")
                uses_gender = True
                continue
            s = SLOT.match(inner)
            if not s:
                raise StoryError(f"Értelmezhetetlen helyőrző: {{{inner}}}")
            key = s["key"].lower()
            if key not in known:
                raise StoryError(f"Ismeretlen mező: {{{inner}}} (vedd fel a 'mezok' közé)")
            rag = hu.normalize_suffix(s["rag"]) if s["rag"] else None
            if rag and rag not in hu.ALL_SUFFIXES:
                raise StoryError(f"Ismeretlen rag: {{{inner}}}")
            slots.add((key, rag))
    return slots, uses_gender


def load_story(folder: Path) -> Story:
    meta, body = _split_front_matter((folder / "mese.md").read_text(encoding="utf-8"))
    for req in ("cim",):
        if not meta.get(req):
            raise StoryError(f"Hiányzik a fejlécből: {req}")

    fields = [dict(f) for f in BUILTIN_FIELDS]
    for f in meta.get("mezok") or []:
        if not isinstance(f, dict) or not f.get("kulcs") or not f.get("cimke"):
            raise StoryError("Minden mezőnek kell 'kulcs' és 'cimke'")
        f["kulcs"] = str(f["kulcs"]).lower()
        f.setdefault("tipus", "nev")
        if f["tipus"] not in ("nev", "szo"):
            raise StoryError(f"Ismeretlen mezőtípus: {f['tipus']}")
        if f["kulcs"] == "nev":
            raise StoryError("A 'nev' mező beépített, nem kell felvenni")
        if not f.get("alapertelmezes") and not f.get("kotelezo"):
            raise StoryError(f"A nem kötelező '{f['kulcs']}' mezőnek kell alapértelmezés")
        fields.append(f)

    warnings: list[str] = []
    cover = folder / meta["borito"] if meta.get("borito") else None
    if cover and not cover.exists():
        warnings.append(f"Hiányzó borítókép: {meta['borito']}")
        cover = None

    themes = [str(t) for t in (meta.get("temak") or [])]
    unknown = [t for t in themes if t not in _themes]
    if unknown:
        raise StoryError(f"Ismeretlen téma: {', '.join(unknown)} (lásd stories/temak.yaml)")

    chapters = _parse_body(body, folder, warnings)
    texts = [meta["cim"]] + [c.title for c in chapters] + [p for c in chapters for p in c.paragraphs]
    slots, uses_gender = _scan_slots(texts, {f["kulcs"] for f in fields})

    return Story(
        slug=folder.name, folder=folder, title=str(meta["cim"]),
        description=str(meta.get("leiras", "")), age=str(meta.get("korosztaly", "")),
        order=int(meta.get("sorrend", 100)), cover=cover, fields=fields,
        chapters=chapters, uses_gender=uses_gender, slots=slots,
        themes=themes, warnings=warnings,
    )


_catalog: dict[str, Story] = {}
_errors: dict[str, str] = {}
_themes: dict[str, dict] = {}


def _load_themes():
    _themes.clear()
    path = config.STORIES_DIR / "temak.yaml"
    if not path.exists():
        return
    for i, t in enumerate(yaml.safe_load(path.read_text(encoding="utf-8")) or []):
        _themes[str(t["kulcs"])] = {"id": str(t["kulcs"]), "label": str(t["nev"]),
                                    "description": str(t.get("leiras", "")), "order": i}


def load_all() -> dict[str, Story]:
    _catalog.clear()
    _errors.clear()
    _load_themes()
    for folder in sorted(p for p in config.STORIES_DIR.iterdir() if (p / "mese.md").exists()):
        try:
            story = load_story(folder)
            _catalog[folder.name] = story
            for w in story.warnings:
                log.warning("%s: %s", folder.name, w)
        except (StoryError, yaml.YAMLError, OSError, ValueError) as e:
            _errors[folder.name] = str(e)
            log.error("Hibás mese kihagyva (%s): %s", folder.name, e)
    log.info("%d mese betöltve", len(_catalog))
    return _catalog


def catalog() -> list[Story]:
    return sorted(_catalog.values(), key=lambda s: (s.order, s.title))


def themes() -> list[dict]:
    """Csak azok a témák, amelyekben van mese."""
    used = {t for s in _catalog.values() for t in s.themes}
    return [t for t in sorted(_themes.values(), key=lambda t: t["order"]) if t["id"] in used]


def get(slug: str) -> Story | None:
    return _catalog.get(slug)


def errors() -> dict[str, str]:
    return dict(_errors)


# --- Személyre szabás ----------------------------------------------------------

def _normalize_value(value: str, kind: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if kind == "nev":
        # lili -> Lili, anna-mária -> Anna-Mária, de: Kati néni, Laci bácsi
        value = re.sub(r"(^|[ \-])(\w)", lambda m: m.group(1) + m.group(2).upper(), value)
        value = re.sub(r"(?<= )(Néni|Bácsi)\b", lambda m: m.group(0).lower(), value)
    return value


def clean_values(story: Story, raw: dict) -> dict:
    """Ellenőrzi és kiegészíti az értékeket. Hibás értéknél ValueProblem."""
    values = {}
    for f in story.fields:
        v = str(raw.get(f["kulcs"]) or "").strip()
        if not v:
            if f.get("kotelezo"):
                raise ValueProblem(f"Add meg: {f['cimke'].lower()}.")
            v = str(f.get("alapertelmezes", ""))
        if len(v) > 30 or not VALUE_OK.match(v):
            raise ValueProblem(f"„{f['cimke']}”: csak betűket, szóközt és kötőjelet írj, legfeljebb 30 karaktert.")
        values[f["kulcs"]] = _normalize_value(v, f.get("tipus", "nev"))
    return values


def clean_overrides(story: Story, raw: dict | None) -> dict:
    overrides = {}
    allowed = {f"{k}+{r}" for k, r in story.slots if r}
    for k, v in (raw or {}).items():
        v = re.sub(r"\s+", " ", str(v)).strip()
        if k in allowed and v:
            if len(v) > 40 or not VALUE_OK.match(v):
                raise ValueProblem(f"Hibás alak: {v}")
            overrides[k] = v
    return overrides


def word_forms(story: Story, values: dict, overrides: dict | None = None) -> list[dict]:
    """A mesében ténylegesen használt ragozott alakok, hogy a szülő ellenőrizhesse."""
    overrides = overrides or {}
    out = []
    for f in story.fields:
        rags = sorted(r for k, r in story.slots if k == f["kulcs"] and r)
        forms = []
        for r in rags:
            key = f"{f['kulcs']}+{r}"
            forms.append({"key": key, "form": overrides.get(key) or hu.inflect(values[f["kulcs"]], r)})
        if forms:
            out.append({"field": f["kulcs"], "label": f["cimke"], "value": values[f["kulcs"]], "forms": forms})
    return out


def _fill(text: str, values: dict, gender: str, overrides: dict) -> str:
    def repl(m):
        inner = m.group(1)
        if "|" in inner:
            boy, girl = (s.strip() for s in inner.split("|"))
            return girl if gender == "lany" else boy
        s = SLOT.match(inner)
        key = s["key"].lower()
        rag = hu.normalize_suffix(s["rag"]) if s["rag"] else None
        word = values[key]
        if rag:
            word = overrides.get(f"{key}+{rag}") or hu.inflect(word, rag)
        if s["key"][0].isupper():
            word = word[:1].upper() + word[1:]
        if s["art"]:
            art = hu.article(word)
            word = (art.capitalize() if s["art"][0].isupper() else art) + " " + word
        return word

    return PLACEHOLDER.sub(repl, text)


def render(story: Story, values: dict, gender: str, overrides: dict | None = None,
           dedication: str | None = None) -> dict:
    overrides = overrides or {}
    fill = lambda t: _fill(t, values, gender, overrides)
    return {
        "title": fill(story.title),
        "child_name": values["nev"],
        "dedication": dedication or "",
        "cover": story.cover,
        "chapters": [
            {"title": fill(c.title), "image": c.image, "paragraphs": [fill(p) for p in c.paragraphs]}
            for c in story.chapters
        ],
    }
