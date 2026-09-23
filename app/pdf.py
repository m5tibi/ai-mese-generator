import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from PIL import Image as PILImage
from reportlab.graphics.shapes import Circle, Drawing

from . import config

INK = colors.HexColor("#1F2A44")
GOLD = colors.HexColor("#D9A23A")
MUTED = colors.HexColor("#6B7385")

_fonts_ready = False

# A fejezetképek magassága (pt): akkora, hogy a fejezet lehetőleg egy oldalra férjen
MAX_IMG_H = 230
MIN_IMG_H = 120


def _register_fonts():
    global _fonts_ready
    if _fonts_ready:
        return
    f = config.FONTS_DIR
    pdfmetrics.registerFont(TTFont("BookSerif", str(f / "DejaVuSerif.ttf")))
    pdfmetrics.registerFont(TTFont("BookSerif-Bold", str(f / "DejaVuSerif-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("BookSerif-Italic", str(f / "DejaVuSerif-Italic.ttf")))
    pdfmetrics.registerFont(TTFont("BookDisplay", str(f / "Fraunces-SoftBold.ttf")))
    pdfmetrics.registerFontFamily(
        "BookSerif", normal="BookSerif", bold="BookSerif-Bold",
        italic="BookSerif-Italic", boldItalic="BookSerif-Bold",
    )
    _fonts_ready = True


def _styles():
    return {
        "cover_title": ParagraphStyle(
            "CoverTitle", fontName="BookDisplay", fontSize=24, leading=29,
            textColor=INK, alignment=TA_CENTER, spaceAfter=10,
        ),
        "cover_sub": ParagraphStyle(
            "CoverSub", fontName="BookSerif-Italic", fontSize=12, leading=17,
            textColor=MUTED, alignment=TA_CENTER, spaceAfter=18,
        ),
        "dedication": ParagraphStyle(
            "Dedication", fontName="BookSerif-Italic", fontSize=12, leading=19,
            textColor=INK, alignment=TA_CENTER,
        ),
        "chapter": ParagraphStyle(
            "Chapter", fontName="BookDisplay", fontSize=16, leading=21,
            textColor=INK, spaceBefore=6, spaceAfter=12,
        ),
        "the_end": ParagraphStyle(
            "TheEnd", fontName="BookSerif-Italic", fontSize=12, leading=17,
            textColor=MUTED, alignment=TA_CENTER, spaceBefore=10,
        ),
        "body": ParagraphStyle(
            "Body", fontName="BookSerif", fontSize=11.5, leading=18.5,
            textColor=INK, alignment=TA_LEFT, spaceAfter=9,
        ),
    }


def _image(path, max_w: float, max_h: float):
    if not path:
        return None
    with PILImage.open(path) as im:
        w, h = im.size
    scale = min(max_w / w, max_h / h)
    img = Image(str(path), width=w * scale, height=h * scale)
    img.hAlign = "CENTER"
    return img


def _moon(width: float) -> Drawing:
    """Díszítés a borítóra, amíg a mesének nincs borítóképe."""
    d = Drawing(width, 170)
    cx = width / 2
    d.add(Circle(cx, 85, 52, fillColor=GOLD, strokeColor=None))
    d.add(Circle(cx + 24, 100, 48, fillColor=colors.white, strokeColor=None))
    for x, y, r in [(-95, 140, 2.6), (-60, 40, 1.8), (80, 150, 2.2), (110, 60, 1.6), (-120, 90, 1.4), (55, 20, 1.5)]:
        d.add(Circle(cx + x, y, r, fillColor=GOLD, strokeColor=None))
    return d


def build_pdf(book: dict) -> bytes:
    """book: templates.render() kimenete."""
    _register_fonts()
    s = _styles()
    buf = io.BytesIO()

    page_w, page_h = A5
    margin = 42
    content_w = page_w - 2 * margin
    footer_text = f"Varázslatos Mesék • Készült {book['child_name']} részére"

    def decorate(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(GOLD)
        canvas.setLineWidth(1.2)
        canvas.rect(20, 20, page_w - 40, page_h - 40)
        canvas.setFont("BookSerif-Italic", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawCentredString(page_w / 2, 27, footer_text)
        if doc.page > 1:
            canvas.drawRightString(page_w - 30, 27, str(doc.page - 1))
        canvas.restoreState()

    doc = SimpleDocTemplate(
        buf, pagesize=A5,
        leftMargin=margin, rightMargin=margin, topMargin=margin, bottomMargin=margin + 6,
        title=book["title"], author="Varázslatos Mesék",
    )

    flow = [Spacer(1, 18), Paragraph(escape(book["title"]), s["cover_title"])]
    flow.append(Paragraph(f"Készült {escape(book['child_name'])} részére", s["cover_sub"]))
    cover = _image(book.get("cover"), content_w * 0.9, 300)
    if cover:
        flow += [cover, Spacer(1, 16)]
    else:
        flow += [Spacer(1, 30), _moon(content_w), Spacer(1, 30)]
    if book.get("dedication"):
        flow.append(Paragraph(escape(book["dedication"]).replace("\n", "<br/>"), s["dedication"]))
    flow.append(PageBreak())

    chapters = book["chapters"]
    frame_w = doc.width - 12           # a Frame alapból 6 pt belső margót használ
    frame_h = doc.height - 12
    for i, ch in enumerate(chapters):
        title = Paragraph(escape(ch["title"]), s["chapter"]) if ch.get("title") else None
        paras = [Paragraph(escape(p), s["body"]) for p in ch["paragraphs"]]
        if i == len(chapters) - 1:
            paras.append(Paragraph("Vége", s["the_end"]))

        # Mennyi hely marad a képnek, hogy a fejezet egy oldalra férjen?
        text_h = sum(p.wrap(frame_w, frame_h)[1] + p.style.spaceBefore + p.style.spaceAfter for p in paras)
        if title:
            text_h += title.wrap(frame_w, frame_h)[1] + s["chapter"].spaceBefore + s["chapter"].spaceAfter
        room = frame_h - text_h - 14 - 4   # kép alatti térköz + biztonsági ráhagyás
        if room >= MIN_IMG_H:
            img = _image(ch.get("image"), content_w * 0.85, min(MAX_IMG_H, room))
        else:
            # Hosszú fejezet: a kép egész oldalt kap a szöveg előtt, mint egy képeskönyvben
            full = _image(ch.get("image"), frame_w, frame_h - 40)
            if full:
                flow += [Spacer(1, max(0, (frame_h - full.drawHeight) / 2 - 10)), full, PageBreak()]
            img = None

        head = [img, Spacer(1, 12)] if img else []
        if title:
            head.append(title)
        if paras:
            head.append(paras[0])
        flow.append(KeepTogether(head))
        flow.extend(paras[1:])
        if i < len(chapters) - 1:
            flow.append(PageBreak())

    doc.build(flow, onFirstPage=decorate, onLaterPages=decorate)
    return buf.getvalue()
