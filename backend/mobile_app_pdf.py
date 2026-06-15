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
from schemas import MobileAppContractData


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


def project_types_text(types: list[str]) -> str:
    return ", ".join(types)


def payment_methods_text(methods: list[str]) -> str:
    return ", ".join(methods)


def ip_items(data: MobileAppContractData) -> list[str]:
    items = []
    if data.ip_code_after_payment:
        items.append(
            f"Ijrochi tomonidan yaratilgan barcha kod, arxitektura, dizayn, baza va hujjatlar "
            f"intellektual mulk huquqlari Buyurtmachiga faqat 100% to'lov "
            f"({format_money(data.total_amount, data.currency)}) amalga oshirilgandan keyin o'tadi."
        )
    if data.ip_rights_until_payment:
        items.append("To'lovgacha barcha huquqlar Ijrochida saqlanadi.")
    if data.ip_github:
        items.append("GitHub repository topshiriladi.")
    if data.ip_source_code:
        items.append("To'liq source code topshiriladi.")
    if data.ip_database:
        items.append("Database migratsiyalari/strukturasi topshiriladi.")
    if data.ip_readme:
        items.append("README (qurish va ishga tushirish yo'riqnomasi) topshiriladi.")
    return items


def make_styles(regular: str, bold: str):
    return {
        "title": ParagraphStyle(
            "Title", fontName=bold, fontSize=14, leading=18, alignment=1, spaceAfter=6,
        ),
        "meta": ParagraphStyle(
            "Meta", fontName=regular, fontSize=10, leading=14, alignment=2, spaceAfter=12,
        ),
        "section": ParagraphStyle(
            "Section", fontName=bold, fontSize=11, leading=15, spaceBefore=10, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body", fontName=regular, fontSize=10, leading=14, spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "Bullet", fontName=regular, fontSize=10, leading=14, leftIndent=12, spaceAfter=3,
        ),
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


def create_mobile_app_pdf(data: MobileAppContractData, filepath: Path) -> None:
    regular, bold = register_fonts()
    styles = make_styles(regular, bold)

    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,
    )

    story = []
    story.append(p("MOBIL ILOVA ISHLAB CHIQISH BO'YICHA SHARTNOMA", styles["title"]))
    story.append(p(
        f"No {data.contract_number}<br/>"
        f"Sana: {format_contract_date(data.contract_date)} yil<br/>"
        f"Joy: {data.contract_place}",
        styles["meta"],
    ))

    # 1. Tomonlar
    story.append(p("1. SHARTNOMA TOMONLARI", styles["section"]))
    story.append(p(
        f"Ushbu shartnoma bir tomondan Buyurtmachi: <b>{data.client.full_name}</b> "
        f"(keyingi o'rinlarda \"Buyurtmachi\" deb ataladi) va ikkinchi tomondan "
        f"Ijrochi: <b>{data.executor.full_name}</b> (keyingi o'rinlarda \"Ijrochi\" deb ataladi) "
        f"o'rtasida tuzildi.",
        styles["body"],
    ))

    parties_rows = [
        ["Ma'lumot", "Buyurtmachi", "Ijrochi"],
        ["F.I.Sh.", data.client.full_name, data.executor.full_name],
        ["Tug'ilgan sana", format_date(data.client.birth_date), format_date(data.executor.birth_date)],
        ["Pasport/ID", data.client.passport, data.executor.passport],
        ["JSHSHIR", data.client.pinfl, data.executor.pinfl],
        ["Manzil", data.client.address, data.executor.address],
        ["Tel/Email", f"{data.client.phone} / {data.client.email}", f"{data.executor.phone} / {data.executor.email}"],
        ["Hisob raqami", data.client.bank_details or "—", data.executor.bank_details or "—"],
    ]

    tbl = Table(
        [[p(c, styles["cell_bold"] if r == 0 else styles["cell"]) for c in row] for r, row in enumerate(parties_rows)],
        colWidths=[3.5 * cm, 6 * cm, 6 * cm],
        repeatRows=1,
    )
    tbl.setStyle(table_style())
    story.append(tbl)

    # 2. Predmet
    story.append(p("2. SHARTNOMA PREDMETI", styles["section"]))
    story.append(p(
        f"Ijrochi Buyurtmachining Texnik topshirig'i (Ilova No1) asosida "
        f"\"{data.project_name}\" ({project_types_text(data.project_types)}) "
        f"loyihasini ishlab chiqish, test qilish va ishga tushirishga tayyor holatda topshiradi.",
        styles["body"],
    ))
    story.append(p(data.project_description, styles["body"]))
    if data.technical_spec:
        story.append(p(f"Texnik topshiriq: {data.technical_spec}", styles["body"]))

    # 3. Muddat
    story.append(p("3. ISH MUDDATI", styles["section"]))
    story.append(p(
        f"Ijrochi ishlar {format_date(data.start_date)} dan {format_date(data.end_date)} gacha, "
        f"jami {data.duration_days} kun ichida yakunlaydi. Shartnoma imzolangandan va avans "
        f"to'lovi kelib tushgandan keyin ishlar boshlanadi. Buyurtmachi tomonidan materiallar, "
        f"dizayn, API yoki tasdiqlar kechiktirilganda, muddat shu kunlarga cho'ziladi.",
        styles["body"],
    ))

    # 4. To'lov
    story.append(p("4. TO'LOV SHARTLARI VA SHARTNOMA SUMMASI", styles["section"]))
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
            "Shartnoma imzolangandan keyin 3 ish kuni ichida. Ishlar faqat shu to'lovdan keyin boshlanadi.",
        ],
        [
            "Yakunlovchi to'lov",
            f"{data.final_percent:g}%",
            format_money(data.final_amount, data.currency),
            "Ish qabul qilingan va \"Akt\" imzolangandan keyin 10 ish kuni ichida.",
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
        f"Kechiktirilgan to'lov uchun har kun {data.penalty_percent:g}% neustoyka hisoblanadi.",
        styles["body"],
    ))

    # 5. Ulush
    story.append(p("5. ULUSH (SHARE MODEL)", styles["section"]))
    story.append(p(
        f"Agar ilova kelajakda uchinchi shaxsga sotilsa yoki litsenziyalansa, Ijrochi "
        f"sotuv/litsenziyalashdan tushgan sof foydadan {data.share_percent:g}% miqdorida ulush olish "
        f"huquqiga ega. Ulush faqat real tushum asosida hisoblanadi. "
        f"Ulush huquqi ilovaning sotilishidan keyin {data.share_years} yil davomida amal qiladi. "
        f"Hisobot davri: {data.report_period}. To'lov sanasi: {data.share_payment_date}.",
        styles["body"],
    ))

    # 6. Qo'llab-quvvatlash
    story.append(p("6. QO'LLAB-QUVVATLASH VA YANGILASHLAR", styles["section"]))
    story.append(p(
        f"Ilova topshirilgandan so'ng {data.warranty_months} oy davomida Ijrochi "
        f"{data.free_updates} marta bepul yangilash/tuzatish kiritadi. Bu o'zgartirishlar quyidagilar "
        f"bilan cheklanadi: TZda belgilangan funksional doirasidagi xatolarni (baglar) tuzatish; "
        f"kichik interfeys/mantiq tuzatishlari; server/API integratsiyasidagi kichik moslashtirishlar. "
        f"Yangi modullar, dizayn o'zgarishlari va server ko'chirishlar alohida to'lov asosida amalga oshiriladi. "
        f"Texnik muammolarga javob berish muddati: {data.response_days} ish kuni.",
        styles["body"],
    ))

    # 7. IP
    story.append(p("7. INTELLEKTUAL MULK HUQUQLARI", styles["section"]))
    for item in ip_items(data):
        story.append(p(f"• {item}", styles["bullet"]))
    story.append(p(
        "Ijrochi o'z uslubi, umumiy bibliotekalari va nomaxsus kod fragmentlarini "
        "boshqa loyihalarda ishlatish huquqini saqlab qoladi.",
        styles["body"],
    ))

    # 8. NDA
    story.append(p("8. MAXFIYLIK (NDA)", styles["section"]))
    if data.nda_required:
        story.append(p(
            "Taraflar quyidagilarni maxfiy saqlashga majbur: Ijrochi — ilova g'oyasi, biznes model, "
            "moliyaviy ma'lumotlar, foydalanuvchilar bazasi, API kalitlari; Buyurtmachi — Ijrochining "
            "arxivtura yechimlari, ichki instrumentlari, kod tuzilishi, xavfsizlik protokollari. "
            f"Maxfiylik muddati: shartnoma tugaganidan so'ng {data.nda_years} yil. "
            "Maxfiylik buzilganida, javobgar tomon isbotlangan real zararni qoplaydi.",
            styles["body"],
        ))
    else:
        story.append(p("Maxfiylik shartnomasi (NDA) talab qilinmaydi.", styles["body"]))

    # 9. Kod va repozitoriy
    story.append(p("9. KOD VA REPOZITORIY BOSHQARUVI", styles["section"]))
    story.append(p(
        "Ishlab chiqish davrida barcha kod Ijrochining maxfiy (Private) repozitoriyasida yuritiladi. "
        "Buyurtmachi ish jarayonida faqat Read-Only huquqi bilan kuzatuv olib borishi mumkin. "
        "To'liq access (Write/Manage) faqat yakunlovchi to'lov to'langandan keyin beriladi. "
        "Repozitoriy, branchlar, commit tarixi va konfiguratsiya fayllari qat'iy maxfiy hisoblanadi. "
        "Ish tugaganda Ijrochi quyidagilarni topshiradi: to'liq source code, database migratsiyalari, "
        "backend/API kodlari, README va muhit o'zgaruvchilari.",
        styles["body"],
    ))

    # 10. Qabul qilish
    story.append(p("10. ISHNI QABUL QILISH TARTIBI", styles["section"]))
    story.append(p(
        f"Ijrochi ishni tayyor deb e'lon qilgach, Buyurtmachi {data.acceptance_days} ish kuni ichida "
        f"tekshiruv o'tkazadi. Kamchiliklar faqat TZ doirasidagi mos kelmasliklar bo'lishi kerak. "
        f"Kamchiliklarni tuzatish muddati: {data.fix_days} kun. "
        f"Agar Buyurtmachi {data.acceptance_days} kun ichida yozma rad etmasa, ish avtomatik qabul qilingan "
        f"deb hisoblanadi. To'liq qabul qilingandan so'ng \"Ishni qabul qilish akti\" imzolanadi.",
        styles["body"],
    ))

    # 11. Javobgarlik
    story.append(p("11. JAVOBGARLIK VA CHEKLOVLAR", styles["section"]))
    story.append(p(
        f"Ijrochining moliyaviy javobgarligi shartnoma umumiy summasi — "
        f"{format_money(data.total_amount, data.currency)} dan oshmaydi. "
        "Bevosita bo'lmagan, ko'rsatilmagan foyda yoki biznes to'xtash zarari undirilmaydi. "
        "Buyurtmachi to'lovni 15 kundan ko'p kechiktirsa, Ijrochi ishni to'xtatish va shartnomani "
        "bir tomonlama bekor qilish huquqiga ega.",
        styles["body"],
    ))

    # 12. Fors-major
    story.append(p("12. FORS-MAJOR", styles["section"]))
    story.append(p(
        "Tabiiy ofatlar, urush, davlat cheklovlari, global hosting/internet uzilishlari, "
        "qonunchilik o'zgarishlari yuzaga kelganda taraflar majburiyatlarini bajarmaganligi uchun "
        "javobgar emas. Fors-major 30 kundan oshsa, taraflar shartnomani yozma ogohlantirish bilan "
        "bekor qilish huquqiga ega.",
        styles["body"],
    ))

    # 13. Bahslar
    story.append(p("13. BAHSLARNI HAL QILISH", styles["section"]))
    story.append(p(
        "Taraflar o'rtasidagi barcha nizolar avval yozma muzokaralar yo'li bilan hal qilinadi. "
        "Kelishuv bo'lmasa, bahslar Ijrochi ro'yxatdan o'tgan joyidagi sudlar tomonidan ko'rib chiqiladi. "
        "O'zbekiston Respublikasi qonunchiligi qo'llaniladi.",
        styles["body"],
    ))

    # 14. Bekor qilish
    story.append(p("14. SHARTNOMANI BEKOR QILISH", styles["section"]))
    story.append(p(
        "Shartnoma taraflarning o'zaro yozma kelishuvi yoki ushbu shartnomada ko'rsatilgan "
        "qo'pol buzilishlar yuzaga kelganda bekor qilinishi mumkin. Bekor qilinganda Ijrochi "
        "bajarilgan bosqichlar uchun mutanosib to'lov olish huquqini saqlab qoladi.",
        styles["body"],
    ))

    # 15. Yakun qoidalar
    story.append(p("15. YAKUN QOIDALAR", styles["section"]))
    story.append(p(
        "Shartnoma ikki nusxada, bir xil yuridik kuch bilan tuziladi. Imzolangan kundan kuchga kiradi. "
        "Har qanday o'zgartirish faqat yozma ko'rinishda amalga oshiriladi. "
        "Ilovalar shartnomaning ajralmas qismi hisoblanadi.",
        styles["body"],
    ))
    if data.electronic_signature:
        story.append(p("Elektron imzo orqali imzolash qo'llab-quvvatlanadi.", styles["body"]))

    # 16. Rekvizitlar
    story.append(p("16. TOMONLAR REKVIZITLARI", styles["section"]))
    req_rows = [
        ["BUYURTMACHI", "IJROCHI"],
        ["F.I.Sh.: " + data.client.full_name, "F.I.Sh.: " + data.executor.full_name],
        ["Pasport/ID: " + data.client.passport, "Pasport/ID: " + data.executor.passport],
        ["JSHSHIR: " + data.client.pinfl, "JSHSHIR: " + data.executor.pinfl],
        ["Manzil: " + data.client.address, "Manzil: " + data.executor.address],
        [
            f"Tel/Email: {data.client.phone} / {data.client.email}",
            f"Tel/Email: {data.executor.phone} / {data.executor.email}",
        ],
        [
            "Hisob raqami: " + (data.client.bank_details or "_______________"),
            "Hisob raqami: " + (data.executor.bank_details or "_______________"),
        ],
        ["Imzo: _______________", "Imzo: _______________"],
        ["Sana: _______________", "Sana: _______________"],
    ]
    req_tbl = Table(
        [[p(c, styles["cell_bold"] if r == 0 else styles["cell"]) for c in row] for r, row in enumerate(req_rows)],
        colWidths=[7.75 * cm, 7.75 * cm],
    )
    req_tbl.setStyle(table_style())
    story.append(req_tbl)

    on_first, on_later = page_callbacks(regular)
    doc.build(story, onFirstPage=on_first, onLaterPages=on_later)


def safe_filename(project_name: str, contract_date: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", project_name, flags=re.UNICODE)
    slug = re.sub(r"[\s_]+", "_", slug.strip()).lower()[:40] or "loyiha"
    date_part = contract_date.replace("-", "")
    if len(date_part) != 8:
        date_part = datetime.now().strftime("%Y%m%d")
    return f"shartnoma_{slug}_{date_part}.pdf"
