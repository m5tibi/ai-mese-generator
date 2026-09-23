"""Mesék ellenőrzése és minta PDF-ek készítése: python -m app.check_stories"""
import sys
from pathlib import Path

from . import pdf, templates

SAMPLES = [("Bence", "fiu"), ("Zsófi", "lany"), ("Ábel", "fiu")]


def main():
    templates.load_all()
    out = Path("proof")
    out.mkdir(exist_ok=True)
    for slug, err in templates.errors().items():
        print(f"HIBA  {slug}: {err}")
    for story in templates.catalog():
        print(f"OK    {story.slug}: {story.title} ({len(story.chapters)} fejezet)")
        for name, gender in SAMPLES:
            values = templates.clean_values(story, {"nev": name})
            forms = templates.word_forms(story, values)
            print("        " + "; ".join(
                f"{f['value']}: " + ", ".join(x["form"] for x in f["forms"]) for f in forms))
            book = templates.render(story, values, gender)
            (out / f"{story.slug}_{name}.pdf").write_bytes(pdf.build_pdf(book))
    print(f"Minta PDF-ek: {out.resolve()}")
    sys.exit(1 if templates.errors() else 0)


if __name__ == "__main__":
    main()
