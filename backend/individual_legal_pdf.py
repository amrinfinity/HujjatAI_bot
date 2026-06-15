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
from schemas import IndividualLegalContractData


def format_date(value: str) -> str:
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).strftime("%d.%m.%Y")
        except ValueError:
            continue
    return value


def format_contract_date(value: str) -> str:
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            dt = datetime.strptime(value, fmt)
            months = [
                "", "yanvar", "fevral", "mart", "aprel", "may", "iyun",
                "iyul", "avgust", "sentyabr", "oktyabr", "noyabr", "dekabr",
            ]
            return f'"{dt.day}" {months[dt.month]} {dt.year}'
        except ValueError:
            continue
    return value


def format_money(amount: float, currency: str) -> str:
    if currency == "USD":
        return f"${amount:,.0f}".replace(",", " ")
    return f"{amount:,.0f}".replace(",", " ") + " so'm"


def payment_methods_text(methods: list[str]) -> str:
    return ", ".join(methods)



def make_styles(regular: str, bold: str):
    return {
        "title": ParagraphStyle("Title", fontName=bold, fontSize=14, leading=18, alignment=1, spaceAfter=4),
        "subtitle": ParagraphStyle("Subtitle", fontName=regular, fontSize=10, leading=13, alignment=1, spaceAfter=8),
        "meta": ParagraphStyle("Meta", fontName=regular, fontSize=10, leading=14, alignment=2, spaceAfter=12),
        "section": ParagraphStyle("Section", fontName=bold, fontSize=11, leading=15, spaceBefore=10, spaceAfter=6),
        "body": ParagraphStyle("Body", fontName=regular, fontSize=10, leading=14, spaceAfter=4),
        "footer": ParagraphStyle(
            "Footer", fontName=regular, fontSize=8, leading=10, alignment=1,
            textColor=colors.HexColor("#64748b"), spaceBefore=16,
        ),
        "cell": ParagraphStyle("Cell", fontName=regular, fontSize=9, leading=12),
        "cell_bold": ParagraphStyle("CellBold", fontName=bold, fontSize=9, leading=12),
    }


def table_style():
    return TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#2563eb")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbeafe")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ])


def p(text: str, style) -> Paragraph:
    return Paragraph(text.replace("\n", "<br/>"), style)


def create_individual_legal_pdf(data: IndividualLegalContractData, filepath: Path) -> None:
    regular, bold = register_fonts()
    styles = make_styles(regular, bold)
    legal = data.legal_entity
    individual = data.individual
    is_client_legal = data.contract_type == "client_legal"

    doc = SimpleDocTemplate(
        str(filepath), pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm, topMargin=2 * cm, bottomMargin=2.5 * cm,
    )

    story = []
    story.append(p("XIZMAT KO'RSATISH SHARTNOMASI", styles["title"]))
    story.append(p(
        f"No {data.contract_number}<br/>"
        f"Sana: {format_contract_date(data.contract_date)} yil<br/>"
        f"Joy: {data.contract_place}",
        styles["meta"],
    ))

    # 1. Tomonlar
    story.append(p("1. SHARTNOMA TOMONLARI", styles["section"]))
    story.append(p(
        "Ushbu shartnoma bir tomondan Buyurtmachi va ikkinchi tomondan Ijrochi o'rtasida tuzildi.",
        styles["body"],
    ))

    parties_table_rows = [
        ["Ma'lumot", "YURIDIK SHAXS", "JISMONIY SHAXS"],
        ["Tashkilot / F.I.Sh.:", legal.org_name, individual.full_name],
        ["STIR / Pasport:", legal.stir, individual.passport],
        ["MFY / JSHSHIR:", legal.mfy, individual.pinfl],
        ["Manzil:", legal.legal_address, individual.address],
        ["Direktor / Tel:", f"{legal.director_name} ({legal.director_position})", individual.phone],
        ["Tel/Email:", f"{legal.phone} / {legal.email}", f"{individual.email}"],
        ["Hisob / Karta:", legal.account_number, individual.card_number],
        ["Bank:", legal.bank_name, individual.bank_name],
    ]

    if is_client_legal:
        parties_table_rows[0] = ["Ma'lumot", "BUYURTMACHI (Yuridik)", "IJROCHI (Jismoniy)"]
    else:
        parties_table_rows[0] = ["Ma'lumot", "IJROCHI (Yuridik)", "BUYURTMACHI (Jismoniy)"]

    tbl = Table(
        [[p(c, styles["cell_bold"] if r == 0 or c == row[0] else styles["cell"]) for c in row]
         for r, row in enumerate(parties_table_rows)],
        colWidths=[3.5 * cm, 6 * cm, 6 * cm],
        repeatRows=1,
    )
    tbl.setStyle(table_style())
    story.append(tbl)

    # 2. Predmet
    story.append(p("2. SHARTNOMA PREDMETI", styles["section"]))
    story.append(p(
        f"Ijrochi Buyurtmachiga \"{data.service_type}\" xizmatini ko'rsatish majburiyatini oladi.",
        styles["body"],
    ))
    story.append(p(data.service_description, styles["body"]))
    story.append(p(f"Ish hajmi: {data.work_scope}", styles["body"]))

    # 3. Muddat
    story.append(p("3. ISH MUDDATI", styles["section"]))
    story.append(p(
        f"Ishlar {format_date(data.start_date)} dan {format_date(data.end_date)} gacha, "
        f"jami {data.duration_days} kun ichida bajariladi.",
        styles["body"],
    ))

    # 4. To'lov
    final_percent = 100 - data.advance_percent
    story.append(p("4. TO'LOV SHARTLARI", styles["section"]))
    story.append(p(
        f"Shartnoma umumiy summasi: {format_money(data.total_amount, data.currency)}",
        styles["body"],
    ))
    pay_rows = [
        ["Bosqich", "Foiz", "Summa", "Sharti"],
        [
            "Avans",
            f"{data.advance_percent:g}%",
            format_money(data.advance_amount, data.currency),
            "Shartnoma imzolanganidan so'ng 5 ish kuni ichida.",
        ],
        [
            "Yakuniy to'lov",
            f"{final_percent:g}%",
            format_money(data.final_amount, data.currency),
            "Ish qabul qilingandan so'ng 10 ish kuni ichida.",
        ],
    ]
    pay_tbl = Table(
        [[p(c, styles["cell_bold"] if r == 0 else styles["cell"]) for c in row] for r, row in enumerate(pay_rows)],
        colWidths=[2.5 * cm, 1.5 * cm, 3 * cm, 8.5 * cm],
        repeatRows=1,
    )
    pay_tbl.setStyle(table_style())
    story.append(pay_tbl)
    story.append(p(
        f"To'lov usuli: {payment_methods_text(data.payment_methods)}. "
        f"Kechiktirilgan to'lov uchun har kun {data.penalty_percent:g}% penya hisoblanadi.",
        styles["body"],
    ))

    # 5. NDA
    story.append(p("5. MAXFIYLIK (NDA)", styles["section"]))
    if data.nda_required:
        story.append(p(
            f"Taraflar shartnoma doirasida olingan barcha ma'lumotlarni maxfiy saqlashga majbur. "
            f"Maxfiylik muddati: shartnoma tugaganidan so'ng {data.nda_years} yil.",
            styles["body"],
        ))
    else:
        story.append(p("Maxfiylik shartnomasi (NDA) talab qilinmaydi.", styles["body"]))

    # 6. Kafolat
    story.append(p("6. KAFOLAT VA JAVOBGARLIK", styles["section"]))
    story.append(p(
        f"Ijrochi xizmatni topshirgandan so'ng {data.warranty_months} oy davomida kafolat beradi. "
        f"Moliyaviy javobgarlik chegarasi: {data.liability_limit}.",
        styles["body"],
    ))

    # 7. Fors-major
    story.append(p("7. FORS-MAJOR", styles["section"]))
    story.append(p(
        "Tabiiy ofatlar, urush, davlat cheklovlari va boshqa fors-major holatlar yuzaga kelganda "
        "taraflar majburiyatlarini bajarmaganligi uchun javobgar emas.",
        styles["body"],
    ))

    # 8. Bahslar
    story.append(p("8. BAHSLARNI HAL QILISH", styles["section"]))
    story.append(p(
        "Nizolar avval yozma muzokaralar yo'li bilan hal qilinadi. Kelishuv bo'lmasa, "
        "bahslar O'zbekiston Respublikasi qonunchiligiga muvofiq sud tartibida ko'rib chiqiladi.",
        styles["body"],
    ))

    # 9. Yakun qoidalar
    story.append(p("9. YAKUN QOIDALAR", styles["section"]))
    story.append(p(
        "Shartnoma ikki nusxada, bir xil yuridik kuch bilan tuziladi. Imzolangan kundan kuchga kiradi. "
        "Har qanday o'zgartirish faqat yozma kelishuv bilan amalga oshiriladi.",
        styles["body"],
    ))

    # 10. Rekvizitlar
    story.append(p("10. TOMONLAR REKVIZITLARI", styles["section"]))

    if is_client_legal:
        client_block = [
            ["BUYURTMACHI (Yuridik shaxs)", ""],
            [f"Tashkilot: {legal.org_name}", ""],
            [f"STIR: {legal.stir}  MFY: {legal.mfy}", ""],
            [f"Manzil: {legal.legal_address}", ""],
            [f"Direktor: {legal.director_name}", ""],
            [f"Tel/Email: {legal.phone} / {legal.email}", ""],
            [f"Hisob: {legal.account_number}  Bank: {legal.bank_name}", ""],
            ["Imzo: _______________  Muhr: (o'rni)", ""],
        ]
        executor_block = [
            ["IJROCHI (Jismoniy shaxs)", ""],
            [f"F.I.Sh.: {individual.full_name}", ""],
            [f"Pasport: {individual.passport}  JSHSHIR: {individual.pinfl}", ""],
            [f"Manzil: {individual.address}", ""],
            [f"Tel/Email: {individual.phone} / {individual.email}", ""],
            [f"Karta: {individual.card_number}  Bank: {individual.bank_name}", ""],
            ["Imzo: _______________", ""],
            ["Sana: _______________", ""],
        ]
    else:
        client_block = [
            ["BUYURTMACHI (Jismoniy shaxs)", ""],
            [f"F.I.Sh.: {individual.full_name}", ""],
            [f"Pasport: {individual.passport}  JSHSHIR: {individual.pinfl}", ""],
            [f"Manzil: {individual.address}", ""],
            [f"Tel/Email: {individual.phone} / {individual.email}", ""],
            [f"Karta: {individual.card_number}  Bank: {individual.bank_name}", ""],
            ["Imzo: _______________", ""],
            ["Sana: _______________", ""],
        ]
        executor_block = [
            ["IJROCHI (Yuridik shaxs)", ""],
            [f"Tashkilot: {legal.org_name}", ""],
            [f"STIR: {legal.stir}  MFY: {legal.mfy}", ""],
            [f"Manzil: {legal.legal_address}", ""],
            [f"Direktor: {legal.director_name}", ""],
            [f"Tel/Email: {legal.phone} / {legal.email}", ""],
            [f"Hisob: {legal.account_number}  Bank: {legal.bank_name}", ""],
            ["Imzo: _______________  Muhr: (o'rni)", ""],
        ]

    max_rows = max(len(client_block), len(executor_block))
    while len(client_block) < max_rows:
        client_block.append(["", ""])
    while len(executor_block) < max_rows:
        executor_block.append(["", ""])

    req_rows = [[client_block[i][0], executor_block[i][0]] for i in range(max_rows)]
    req_tbl = Table(
        [[p(c, styles["cell_bold"] if i == 0 else styles["cell"]) for c in row] for i, row in enumerate(req_rows)],
        colWidths=[7.75 * cm, 7.75 * cm],
    )
    req_tbl.setStyle(table_style())
    story.append(req_tbl)

    on_first, on_later = page_callbacks(regular)
    doc.build(story, onFirstPage=on_first, onLaterPages=on_later)


def safe_filename(org_name: str, contract_date: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", org_name, flags=re.UNICODE)
    slug = re.sub(r"[\s_]+", "_", slug.strip()).lower()[:40] or "tashkilot"
    date_part = contract_date.replace("-", "")
    if len(date_part) != 8:
        date_part = datetime.now().strftime("%Y%m%d")
    return f"shartnoma_jy_{slug}_{date_part}.pdf"
