from reportlab.lib import colors
from reportlab.lib.units import cm

from pdf_fonts import register_fonts

FOOTER_TEXT = "Ushbu hujjat @HujjatAI_Bot orqali 10 soniyada yaratildi"
PAGE_NUM_FONT_SIZE = 8
FOOTER_FONT_SIZE = 6
FOOTER_Y = 1.0 * cm
PAGE_NUM_COLOR = colors.HexColor("#1e293b")
FOOTER_COLOR = colors.HexColor("#94a3b8")


def draw_page_footer(canvas, doc) -> None:
    regular, _ = register_fonts()
    page_num = canvas.getPageNumber()
    page_width = doc.pagesize[0]
    center_x = page_width / 2
    right_x = page_width - doc.rightMargin

    canvas.saveState()

    canvas.setFont(regular, PAGE_NUM_FONT_SIZE)
    canvas.setFillColor(PAGE_NUM_COLOR)
    canvas.drawCentredString(center_x, FOOTER_Y, str(page_num))

    canvas.setFont(regular, FOOTER_FONT_SIZE)
    canvas.setFillColor(FOOTER_COLOR)
    canvas.drawRightString(right_x, FOOTER_Y, FOOTER_TEXT)

    canvas.restoreState()


def page_callbacks(_font_name: str = ""):
    """font_name kept for backward compatibility with existing PDF generators."""

    def _draw(canvas, doc):
        draw_page_footer(canvas, doc)

    return _draw, _draw
