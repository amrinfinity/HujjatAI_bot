import re
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from pdf_fonts import register_fonts
from pdf_footer import page_callbacks
from schemas import ActData


def format_date(value: str) -> str:
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).strftime("%d.%m.%Y")
        except ValueError:
            continue
    return value


def format_money(amount: float) -> str:
    formatted = f"{amount:,.0f}".replace(",", " ")
    if amount != int(amount):
        formatted = f"{amount:,.2f}".replace(",", " ")
    return f"{formatted} so'm"


def make_styles(regular: str, bold: str):
    return {
        "title": ParagraphStyle(
            "Title", fontName=bold, fontSize=14, leading=18, alignment=1, spaceAfter=6
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", fontName=regular, fontSize=10, leading=14, alignment=1, spaceAfter=14
        ),
        "body": ParagraphStyle("Body", fontName=regular, fontSize=10, leading=14, spaceAfter=6),
        "cell": ParagraphStyle("Cell", fontName=regular, fontSize=9, leading=12),
        "cell_bold": ParagraphStyle("CellBold", fontName=bold, fontSize=9, leading=12),
        "cell_center": ParagraphStyle(
            "CellCenter", fontName=regular, fontSize=9, leading=12, alignment=1
        ),
    }


def table_style(header_rows: int = 1):
    return TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#2563eb")),
        ("BACKGROUND", (0, 0), (-1, header_rows - 1), colors.HexColor("#dbeafe")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ])


def p(text: str, style) -> Paragraph:
    return Paragraph(str(text).replace("\n", "<br/>"), style)


def claims_text(data: ActData) -> str:
    if data.has_claims == "Ha" and data.claims_details:
        return f"Ha: {data.claims_details}"
    return data.has_claims


def create_act_pdf(data: ActData, filepath: Path) -> None:
    regular, bold = register_fonts()
    styles = make_styles(regular, bold)
    act_date = format_date(data.date)
    contract_date = format_date(data.contract_date)
    grand_text = format_money(data.grand_total)
    if data.grand_total_words:
        grand_text += f" ({data.grand_total_words})"

    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,
    )

    story = [
        p("XIZMAT KO'RSATISH AKTI", styles["title"]),
        p("(ishni qabul qilish akti)", styles["subtitle"]),
        p(f"№ {data.act_number}  {act_date} sana, {data.city} sh.", styles["subtitle"]),
        Spacer(1, 0.3 * cm),
        p("Ushbu akt quyidagi tomonlar o'rtasida tuzildi:", styles["body"]),
        p(f"<b>Buyurtmachi:</b> {data.customer_name}", styles["body"]),
        p(f"<b>Ijrochi:</b> {data.executor_name}", styles["body"]),
        p(
            f"Asos: {data.contract_number} sonli shartnoma ({contract_date} sana).",
            styles["body"],
        ),
        Spacer(1, 0.2 * cm),
        p(
            "Haqiqatan ham, Ijrochi quyidagi xizmatlarni ko'rsatdi va "
            "Buyurtmachi ushbu xizmatlarni qabul qildi:",
            styles["body"],
        ),
        Spacer(1, 0.3 * cm),
    ]

    header = [
        p("№", styles["cell_bold"]),
        p("Ishning nomi/tavsifi", styles["cell_bold"]),
        p("Birlik", styles["cell_bold"]),
        p("Miqdori", styles["cell_bold"]),
        p("Narxi", styles["cell_bold"]),
        p("Jami summa", styles["cell_bold"]),
    ]
    rows = [header]
    for item in data.items:
        rows.append([
            p(str(item.number), styles["cell_center"]),
            p(item.description, styles["cell"]),
            p(item.unit, styles["cell_center"]),
            p(f"{item.quantity:g}", styles["cell_center"]),
            p(format_money(item.price), styles["cell"]),
            p(format_money(item.total), styles["cell"]),
        ])

    rows.append([
        p("", styles["cell"]),
        p("JAMI:", styles["cell_bold"]),
        p("", styles["cell"]),
        p("", styles["cell"]),
        p("", styles["cell"]),
        p(format_money(data.grand_total), styles["cell_bold"]),
    ])

    items_table = Table(
        rows,
        colWidths=[1.0 * cm, 6.5 * cm, 1.8 * cm, 1.8 * cm, 2.5 * cm, 2.9 * cm],
        repeatRows=1,
    )
    items_table.setStyle(table_style())
    story.append(items_table)
    story.append(Spacer(1, 0.5 * cm))

    story.extend([
        p(f"Jami bajarilgan ishlar qiymati: {grand_text}ni tashkil etadi.", styles["body"]),
        p(f"Ko'rsatilgan xizmatlar sifati: {data.quality_status}.", styles["body"]),
        p(
            f"Tomonlarning bir-biriga moddiy va boshqa da'volari: {claims_text(data)}.",
            styles["body"],
        ),
        p("Ushbu akt ikki nusxada tuzildi va tomonlar tomonidan imzolandi.", styles["body"]),
        Spacer(1, 0.5 * cm),
    ])

    sign_header = [
        p("BUYURTMACHI", styles["cell_bold"]),
        p("IJROCHI", styles["cell_bold"]),
    ]
    sign_rows = [
        sign_header,
        [p(f"F.I.Sh. / Nomi: {data.customer_name}", styles["cell"]),
         p(f"F.I.Sh. / Nomi: {data.executor_name}", styles["cell"])],
        [p("Imzo: _______________________", styles["cell"]),
         p("Imzo: _______________________", styles["cell"])],
        [p(f"Sana: {act_date}", styles["cell"]),
         p(f"Sana: {act_date}", styles["cell"])],
    ]
    sign_table = Table(sign_rows, colWidths=[8.5 * cm, 8.5 * cm])
    sign_table.setStyle(table_style())
    story.append(sign_table)

    on_first, on_later = page_callbacks(regular)
    doc.build(story, onFirstPage=on_first, onLaterPages=on_later)


def safe_filename(customer_name: str, act_date: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", customer_name, flags=re.UNICODE)
    slug = re.sub(r"[\s_]+", "_", slug.strip()).lower()[:30] or "buyurtmachi"
    date_part = act_date.replace("-", "")
    if len(date_part) != 8:
        date_part = datetime.now().strftime("%Y%m%d")
    return f"akt_{slug}_{date_part}.pdf"
