import calendar
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
from schemas import RentalContractData


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
    return f"{formatted} so'm"


def rental_end_date(start: str, period: str) -> str:
    months_map = {"6 oy": 6, "1 yil": 12, "2 yil": 24, "3 yil": 36}
    months = months_map.get(period, 12)
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            dt = datetime.strptime(start, fmt)
            break
        except ValueError:
            dt = None
    if not dt:
        return period
    total_months = dt.month - 1 + months
    year = dt.year + total_months // 12
    month = total_months % 12 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return datetime(year, month, day).strftime("%d.%m.%Y")


def utilities_text(data: RentalContractData) -> str:
    parts = []
    mapping = {
        "landlord": "Ijaraga beruvchi",
        "tenant": "Ijaraga oluvchi",
        "partial": "Qisman",
    }
    for key in data.utilities_paid_by:
        parts.append(mapping.get(key, key))
    text = ", ".join(parts)
    if data.utilities_note:
        text += f" ({data.utilities_note})"
    return text


def make_styles(regular: str, bold: str):
    return {
        "title": ParagraphStyle("Title", fontName=bold, fontSize=14, leading=18, alignment=1, spaceAfter=8),
        "meta": ParagraphStyle("Meta", fontName=regular, fontSize=10, leading=14, alignment=2, spaceAfter=12),
        "section": ParagraphStyle("Section", fontName=bold, fontSize=11, leading=15, spaceBefore=10, spaceAfter=6),
        "body": ParagraphStyle("Body", fontName=regular, fontSize=10, leading=14, spaceAfter=4),
        "bullet": ParagraphStyle("Bullet", fontName=regular, fontSize=10, leading=14, leftIndent=12, spaceAfter=3),
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
    return Paragraph(str(text).replace("\n", "<br/>"), style)


def create_rental_pdf(data: RentalContractData, filepath: Path) -> None:
    regular, bold = register_fonts()
    styles = make_styles(regular, bold)
    ll, tn = data.landlord, data.tenant
    start = format_date(data.contract_date)
    end = rental_end_date(data.contract_date, data.rental_period)
    appliances = ", ".join(data.appliances) if data.appliances else "—"
    if data.other_appliances:
        appliances += f", {data.other_appliances}"

    doc = SimpleDocTemplate(
        str(filepath), pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm, topMargin=2 * cm, bottomMargin=2.5 * cm,
    )

    story = []
    story.append(p("UY-IJOVA SHARTNOMASI", styles["title"]))
    story.append(p(
        f"No {data.contract_number}<br/>"
        f"Sana: {format_contract_date(data.contract_date)} yil<br/>"
        f"Joy: {data.contract_place}",
        styles["meta"],
    ))

    # 1. Tomonlar
    story.append(p("1. SHARTNOMA TOMONLARI", styles["section"]))
    rows = [
        ["Ma'lumot", "IJARAGA BERUVCHI", "IJARAGA OLUVCHI"],
        ["F.I.Sh.:", ll.full_name, tn.full_name],
        ["Tug'ilgan sana:", format_date(ll.birth_date), format_date(tn.birth_date)],
        ["Pasport:", ll.passport, tn.passport],
        ["JSHSHIR:", ll.pinfl, tn.pinfl],
        ["Manzil:", ll.address, tn.address],
        ["Tel/Email:", f"{ll.phone} / {ll.email}", f"{tn.phone} / {tn.email}"],
        ["Mulk hujjati / Ish joyi:", ll.property_document or "—", tn.workplace or "—"],
    ]
    tbl = Table(
        [[p(c, styles["cell_bold"] if r == 0 else styles["cell"]) for c in row] for r, row in enumerate(rows)],
        colWidths=[3.5 * cm, 6 * cm, 6 * cm], repeatRows=1,
    )
    tbl.setStyle(table_style())
    story.append(tbl)

    # 2. Predmet
    story.append(p("2. SHARTNOMA PREDMETI", styles["section"]))
    story.append(p(f"Ijara ob'ekti manzili: {data.property_address}", styles["body"]))
    story.append(p(
        f"Uy turi: {data.property_type}. Umumiy maydoni: {data.total_area:g} m². "
        f"Xonalar soni: {data.rooms_count}. Qavat: {data.floor}.",
        styles["body"],
    ))
    furnished_text = "Ha" if data.furnished else "Yo'q"
    story.append(p(
        f"Mebellangan: {furnished_text}. Texnika: {appliances}.",
        styles["body"],
    ))

    # 3. Muddat
    story.append(p("3. IJARA MUDDATI", styles["section"]))
    story.append(p(
        f"Boshlanish sanasi: {start}. Tugash sanasi: {end}. Umumiy muddat: {data.rental_period}.",
        styles["body"],
    ))

    # 4. To'lov
    story.append(p("4. TO'LOV SHARTLARI", styles["section"]))
    pay_rows = [
        ["Ko'rsatkich", "Miqdor"],
        ["Oylik ijara haqi", format_money(data.monthly_rent, data.currency)],
        ["Garov puli", format_money(data.deposit, data.currency)],
        ["To'lov kuni", data.payment_day],
        ["To'lov usuli", ", ".join(data.payment_methods)],
        ["Kommunal to'lovlar", utilities_text(data)],
        ["Kechiktirilgan to'lov penya", f"{data.penalty_percent:g}% har kun"],
    ]
    pay_tbl = Table(
        [[p(c, styles["cell_bold"] if r == 0 else styles["cell"]) for c in row] for r, row in enumerate(pay_rows)],
        colWidths=[6 * cm, 9.5 * cm], repeatRows=1,
    )
    pay_tbl.setStyle(table_style())
    story.append(pay_tbl)

    # 5. Huquq va majburiyatlar
    story.append(p("5. TOMONLARNING HUQUQ VA MAJBURIYATLARI", styles["section"]))
    story.append(p("Ijaraga beruvchining majburiyatlari:", styles["body"]))
    for item in [
        "Ijara ob'ektini yaxshi holatda topshirish",
        "Kommunal to'lovlarni (agar kelishilgan bo'lsa) amalga oshirish",
        f"Tuzatishlar: {data.repairs_by} tomonidan amalga oshiriladi",
    ]:
        story.append(p(f"• {item}", styles["bullet"]))
    story.append(p("Ijaraga oluvchining majburiyatlari:", styles["body"]))
    for item in [
        "O'z vaqtida ijara haqini to'lash",
        "Mulkni asrab-avaylash va ehtiyotkorlik bilan foydalanish",
        "Kommunal to'lovlarni (agar kelishilgan bo'lsa) to'lash",
        "Qo'shnilar bilan tinch yashash",
    ]:
        story.append(p(f"• {item}", styles["bullet"]))

    # 6. Qo'shimcha
    story.append(p("6. QO'SHIMCHA SHARTLAR", styles["section"]))
    story.append(p(f"Uy hayvonlari: {data.pets_allowed}.", styles["body"]))
    story.append(p(f"Mehmonlar qolishi: {data.guests_policy}.", styles["body"]))
    story.append(p(f"Chekish: {data.smoking_policy}.", styles["body"]))
    story.append(p(f"Tuzatishlar: {data.repairs_by}.", styles["body"]))
    if data.max_repair_amount:
        story.append(p(
            f"Maksimal tuzatish summasi: {format_money(data.max_repair_amount, data.currency)}.",
            styles["body"],
        ))

    # 7. Kafolat
    story.append(p("7. KAFOLAT VA JAVOBGARLIK", styles["section"]))
    story.append(p(f"Garov qaytarish shartlari: {data.deposit_return_terms}", styles["body"]))
    story.append(p(f"Oldindan ogohlantirish muddati: {data.notice_days} kun.", styles["body"]))
    if data.early_termination_penalty:
        story.append(p(
            f"Muddatidan oldin bekor qilish jarimasi: "
            f"{format_money(data.early_termination_penalty, data.currency)}.",
            styles["body"],
        ))
    story.append(p(f"Mulkka zarar yetkazilganda: {data.damage_liability}", styles["body"]))

    # 8-10
    story.append(p("8. FORS-MAJOR", styles["section"]))
    story.append(p(
        "Tabiiy ofatlar, urush va boshqa fors-major holatlar yuzaga kelganda taraflar "
        "majburiylarni bajarmaganlik uchun javobgar emas.", styles["body"],
    ))
    story.append(p("9. BAHSLARNI HAL QILISH", styles["section"]))
    story.append(p(
        "Nizolar avval muzokaralar yo'li bilan hal qilinadi. Kelishuv bo'lmasa, "
        "O'zbekiston Respublikasi qonunchiligiga muvofiq sud tartibida ko'rib chiqiladi.",
        styles["body"],
    ))
    story.append(p("10. YAKUN QOIDALAR", styles["section"]))
    story.append(p(
        "Shartnoma ikki nusxada tuziladi. Imzolangan kundan kuchga kiradi. "
        "O'zgarishlar faqat yozma kelishuv bilan amalga oshiriladi.",
        styles["body"],
    ))
    if data.electronic_signature:
        story.append(p("Elektron imzo qo'llab-quvvatlanadi.", styles["body"]))

    # 11. Imzolar
    story.append(p("11. TOMONLAR REKVIZITLARI VA IMZOLAR", styles["section"]))
    sig_rows = [
        ["IJARAGA BERUVCHI", "IJARAGA OLUVCHI"],
        [f"F.I.Sh.: {ll.full_name}", f"F.I.Sh.: {tn.full_name}"],
        [f"Pasport: {ll.passport}", f"Pasport: {tn.passport}"],
        [f"Manzil: {ll.address}", f"Manzil: {tn.address}"],
        [f"Tel: {ll.phone}", f"Tel: {tn.phone}"],
        ["Imzo: _______________", "Imzo: _______________"],
        ["Sana: _______________", "Sana: _______________"],
    ]
    sig_tbl = Table(
        [[p(c, styles["cell_bold"] if r == 0 else styles["cell"]) for c in row] for r, row in enumerate(sig_rows)],
        colWidths=[7.75 * cm, 7.75 * cm],
    )
    sig_tbl.setStyle(table_style())
    story.append(sig_tbl)

    if data.witnesses_required:
        story.append(p("Guvohlar:", styles["body"]))
        for i in range(1, data.witnesses_count + 1):
            story.append(p(
                f"{i}-guvoh: F.I.Sh. _______________  Pasport: _______________  Imzo: _______________",
                styles["bullet"],
            ))

    on_first, on_later = page_callbacks(regular)
    doc.build(story, onFirstPage=on_first, onLaterPages=on_later)


def safe_filename(tenant_name: str, contract_date: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", tenant_name, flags=re.UNICODE)
    slug = re.sub(r"[\s_]+", "_", slug.strip()).lower()[:30] or "ijarachi"
    date_part = contract_date.replace("-", "")
    if len(date_part) != 8:
        date_part = datetime.now().strftime("%Y%m%d")
    return f"uy_ijara_{slug}_{date_part}.pdf"
