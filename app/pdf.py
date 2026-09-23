import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
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
        "body": ParagraphStyle(
            "Body", fontName="BookSerif", fontSize=11.5, leading=18.5,
            textColor=INK, alignment=TA_JUSTIFY, spaceAfter=9,
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
    for i, ch in enumerate(chapters):
        img = _image(ch.get("image"), content_w * 0.8, 210)
        paragraphs = ch["paragraphs"]
        head = [img, Spacer(1, 12)] if img else []
        if ch.get("title"):
            head.append(Paragraph(escape(ch["title"]), s["chapter"]))
        if paragraphs:
            head.append(Paragraph(escape(paragraphs[0]), s["body"]))
        flow.append(KeepTogether(head))
        for p in paragraphs[1:]:
            flow.append(Paragraph(escape(p), s["body"]))
        if i < len(chapters) - 1:
            flow.append(PageBreak())

    flow += [Spacer(1, 14), Paragraph("Vége", s["cover_sub"])]
    doc.build(flow, onFirstPage=decorate, onLaterPages=decorate)
    return buf.getvalue()
