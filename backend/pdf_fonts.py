from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONTS_DIR = Path(__file__).resolve().parent / "fonts"

FONT_REGULAR = "NotoSans"
FONT_BOLD = "NotoSans-Bold"
_fonts_registered = False


def register_fonts() -> tuple[str, str]:
    global _fonts_registered
    if not _fonts_registered:
        regular = FONTS_DIR / "NotoSans-Regular.ttf"
        bold = FONTS_DIR / "NotoSans-Bold.ttf"
        if regular.exists():
            pdfmetrics.registerFont(TTFont(FONT_REGULAR, str(regular)))
        if bold.exists():
            pdfmetrics.registerFont(TTFont(FONT_BOLD, str(bold)))
        _fonts_registered = True

    regular_name = FONT_REGULAR if FONT_REGULAR in pdfmetrics.getRegisteredFontNames() else "Helvetica"
    bold_name = FONT_BOLD if FONT_BOLD in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
    return regular_name, bold_name
