import re
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

from pdf_fonts import register_fonts
from pdf_footer import page_callbacks
from schemas import LegalLegalContractData, LegalPartyFull


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
    formatted = f"{amount:,.0f}".replace(",", " ")
    if currency == "USD":
        return f"${formatted}"
    if currency == "EUR":
        return f"€{formatted}"
    return f"{formatted} so'm"


def party_display_name(party: LegalPartyFull) -> str:
    return f"{party.org_name} {party.org_form}"


def ip_owner_text(data: LegalLegalContractData) -> str:
    mapping = {
        "party_first": f"Birinchi tomonga ({party_display_name(data.party_first)})",
        "party_second": f"Ikkinchi tomonga ({party_display_name(data.party_second)})",
        "joint": "Taraflarga qo'shma mulkdorlik huquqi bilan",
    }
    return mapping.get(data.ip_owner, data.ip_owner)


def payment_type_text(payment_type: str) -> str:
    return {
        "one_time": "Bir martalik to'lov",
        "staged": "Bosqichma-bosqich to'lov",
        "monthly": "Oylik to'lov (abonement)",
    }.get(payment_type, payment_type)


def make_styles(regular: str, bold: str):
    return {
        "title": ParagraphStyle("Title", fontName=bold, fontSize=14, leading=18, alignment=1, spaceAfter=8),
        "meta": ParagraphStyle("Meta", fontName=regular, fontSize=10, leading=14, alignment=2, spaceAfter=12),
        "section": ParagraphStyle("Section", fontName=bold, fontSize=11, leading=15, spaceBefore=10, spaceAfter=6),
        "body": ParagraphStyle("Body", fontName=regular, fontSize=10, leading=14, spaceAfter=4),
        "bullet": ParagraphStyle("Bullet", fontName=regular, fontSize=10, leading=14, leftIndent=12, spaceAfter=3),
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


def party_comparison_rows(p1: LegalPartyFull, p2: LegalPartyFull):
    return [
        ["Ma'lumot", "BIRINCHI TOMON", "IKKINCHI TOMON"],
        ["Tashkilot:", party_display_name(p1), party_display_name(p2)],
        ["STIR:", p1.stir, p2.stir],
        ["MFY:", p1.mfy, p2.mfy],
        ["Hisob raqami:", p1.account_number, p2.account_number],
        ["Bank:", p1.bank_name, p2.bank_name],
        ["MFO:", p1.mfo, p2.mfo],
        ["Manzil:", p1.legal_address, p2.legal_address],
        ["Direktor:", f"{p1.director_name} ({p1.director_position})", f"{p2.director_name} ({p2.director_position})"],
        ["Tel/Email:", f"{p1.phone} / {p1.email}", f"{p2.phone} / {p2.email}"],
    ]


def create_legal_legal_pdf(data: LegalLegalContractData, filepath: Path) -> None:
    regular, bold = register_fonts()
    styles = make_styles(regular, bold)
    p1, p2 = data.party_first, data.party_second

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
        f"Ushbu shartnoma bir tomondan <b>{party_display_name(p1)}</b> va ikkinchi tomondan "
        f"<b>{party_display_name(p2)}</b> o'rtasida tuzildi.",
        styles["body"],
    ))
    rows = party_comparison_rows(p1, p2)
    tbl = Table(
        [[p(c, styles["cell_bold"] if r == 0 else styles["cell"]) for c in row] for r, row in enumerate(rows)],
        colWidths=[3.5 * cm, 6 * cm, 6 * cm],
        repeatRows=1,
    )
    tbl.setStyle(table_style())
    story.append(tbl)

    # 2. Predmet
    story.append(p("2. SHARTNOMA PREDMETI", styles["section"]))
    story.append(p(
        f"Ikkinchi tomon Birinchi tomonga \"{data.service_type}\" xizmatini ko'rsatish majburiyatini oladi.",
        styles["body"],
    ))
    story.append(p(data.service_description, styles["body"]))
    story.append(p(f"Ish hajmi: {data.work_scope}", styles["body"]))
    if data.has_technical_spec:
        story.append(p("Texnik topshiriq shartnoma ilovasi sifatida taqdim etiladi.", styles["body"]))

    # 3. Muddat
    story.append(p("3. ISH MUDDATI", styles["section"]))
    story.append(p(
        f"Shartnoma {format_date(data.effective_date)} sanasidan kuchga kiradi. "
        f"Ishlar {format_date(data.start_date)} dan {format_date(data.end_date)} gacha, "
        f"jami {data.duration_days} kun ichida bajariladi. Shartnoma muddati: {data.contract_term}.",
        styles["body"],
    ))

    # 4. To'lov
    story.append(p("4. TO'LOV SHARTLARI VA SUMMASI", styles["section"]))
    story.append(p(
        f"Shartnoma umumiy summasi: {format_money(data.total_amount, data.currency)}. "
        f"To'lov turi: {payment_type_text(data.payment_type)}.",
        styles["body"],
    ))
    pay_rows = [["Bosqich", "Foiz", "Summa", "Sharti"]]
    for stage in data.payment_stages:
        pay_rows.append([
            stage.name,
            f"{stage.percent:g}%",
            format_money(stage.amount, data.currency),
            stage.condition,
        ])
    pay_tbl = Table(
        [[p(c, styles["cell_bold"] if r == 0 else styles["cell"]) for c in row] for r, row in enumerate(pay_rows)],
        colWidths=[2.5 * cm, 1.5 * cm, 3 * cm, 8.5 * cm],
        repeatRows=1,
    )
    pay_tbl.setStyle(table_style())
    story.append(pay_tbl)
    story.append(p(
        f"To'lov usuli: {', '.join(data.payment_methods)}. "
        f"Kechiktirilgan to'lov uchun har kun {data.penalty_percent:g}% penya hisoblanadi, "
        f"maksimal muddati {data.penalty_max_days} kun.",
        styles["body"],
    ))

    # 5. Sifat
    story.append(p("5. SIFAT VA QABUL QILISH", styles["section"]))
    story.append(p(
        f"Sifat standarti: {data.quality_standard}. "
        f"Buyurtmachi {data.acceptance_days} ish kuni ichida tekshiruv o'tkazadi. "
        f"Kamchiliklarni tuzatish muddati: {data.fix_days} kun.",
        styles["body"],
    ))
    if data.acceptance_act_required:
        story.append(p("Ish qabul qilingandan so'ng tomonlar \"Qabul qilish akti\"ni imzolaydi.", styles["body"]))

    # 6. Kafolat
    story.append(p("6. KAFOLAT VA JAVOBGARLIK", styles["section"]))
    story.append(p(
        f"Kafolat muddati: {data.warranty_months} oy. Bepul tuzatishlar soni: {data.free_fixes}. "
        f"Moliyaviy javobgarlik chegarasi: {data.liability_limit}.",
        styles["body"],
    ))
    if data.insurance_required:
        story.append(p("Taraflar sug'urta polisini rasmiylashtirish majburiyatini oladi.", styles["body"]))

    # 7. NDA
    story.append(p("7. MAXFIYLIK (NDA)", styles["section"]))
    if data.nda_required:
        story.append(p(
            f"Taraflar shartnoma doirasidagi ma'lumotlarni maxfiy saqlashga majbur. "
            f"Maxfiylik muddati: {data.nda_years} yil.",
            styles["body"],
        ))
    else:
        story.append(p("Maxfiylik shartnomasi (NDA) talab qilinmaydi.", styles["body"]))

    # 8. IP
    story.append(p("8. INTELLEKTUAL MULK", styles["section"]))
    story.append(p(f"Intellektual mulk huquqlari: {ip_owner_text(data)}.", styles["body"]))
    if data.repository_transfer:
        story.append(p("Kod va repozitoriy topshiriladi.", styles["body"]))
    else:
        story.append(p("Kod va repozitoriy topshirilmaydi.", styles["body"]))

    # 9. Fors-major
    story.append(p("9. FORS-MAJOR", styles["section"]))
    story.append(p(
        "Tabiiy ofatlar, urush, davlat cheklovlari va boshqa fors-major holatlar yuzaga kelganda "
        "taraflar majburiyatlarini bajarmaganligi uchun javobgar emas.",
        styles["body"],
    ))

    # 10. Bahslar
    story.append(p("10. BAHSLARNI HAL QILISH", styles["section"]))
    story.append(p(
        "Nizolar avval yozma muzokaralar yo'li bilan hal qilinadi. Kelishuv bo'lmasa, "
        "bahslar O'zbekiston Respublikasi qonunchiligiga muvofiq sud tartibida ko'rib chiqiladi.",
        styles["body"],
    ))

    # 11. Bekor qilish
    story.append(p("11. SHARTNOMANI BEKOR QILISH", styles["section"]))
    story.append(p(
        "Shartnoma taraflarning o'zaro yozma kelishuvi yoki qo'pol buzilishlar "
        "yuzaga kelganda bekor qilinishi mumkin.",
        styles["body"],
    ))

    # 12. Yakun qoidalar
    story.append(p("12. YAKUN QOIDALAR", styles["section"]))
    story.append(p(
        f"Shartnoma {data.copies_count} nusxada, bir xil yuridik kuch bilan tuziladi. "
        "Imzolangan kundan kuchga kiradi. Har qanday o'zgartirish faqat yozma kelishuv bilan amalga oshiriladi.",
        styles["body"],
    ))
    if data.electronic_signature:
        story.append(p("Elektron imzo orqali imzolash qo'llab-quvvatlanadi.", styles["body"]))

    # 13. Rekvizitlar
    story.append(p("13. TOMONLAR REKVIZITLARI", styles["section"]))

    def req_block(party: LegalPartyFull, title: str):
        lines = [
            title,
            f"Tashkilot: {party_display_name(party)}",
            f"STIR: {party.stir}  MFY: {party.mfy}",
            f"Manzil: {party.legal_address}",
            f"Direktor: {party.director_name}",
            f"Tel/Email: {party.phone} / {party.email}",
            f"Hisob: {party.account_number}  Bank: {party.bank_name}  MFO: {party.mfo}",
            "Imzo: _______________  Muhr: (o'rni)",
        ]
        return lines

    b1 = req_block(p1, "BIRINCHI TOMON")
    b2 = req_block(p2, "IKKINCHI TOMON")
    max_len = max(len(b1), len(b2))
    while len(b1) < max_len:
        b1.append("")
    while len(b2) < max_len:
        b2.append("")

    req_tbl = Table(
        [[p(b1[i], styles["cell_bold"] if i == 0 else styles["cell"]),
          p(b2[i], styles["cell_bold"] if i == 0 else styles["cell"])] for i in range(max_len)],
        colWidths=[7.75 * cm, 7.75 * cm],
    )
    req_tbl.setStyle(table_style())
    story.append(req_tbl)

    on_first, on_later = page_callbacks(regular)
    doc.build(story, onFirstPage=on_first, onLaterPages=on_later)


def safe_filename(party1: str, party2: str, contract_date: str) -> str:
    def slug(name: str) -> str:
        s = re.sub(r"[^\w\s-]", "", name, flags=re.UNICODE)
        s = re.sub(r"[\s_]+", "_", s.strip()).lower()[:25]
        return s or "tomon"

    date_part = contract_date.replace("-", "")
    if len(date_part) != 8:
        date_part = datetime.now().strftime("%Y%m%d")
    return f"shartnoma_yy_{slug(party1)}_{slug(party2)}_{date_part}.pdf"
