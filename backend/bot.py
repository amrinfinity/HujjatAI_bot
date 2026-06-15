"""
Hujjat AI Telegram bot — Web App orqali shartnoma yaratish.
Ishga tushirish: cd backend && python bot.py
"""

import logging
import sys

from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    Update,
    WebAppInfo,
)
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from config import Config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    "👋 <b>Hujjat AI</b> ga xush kelibsiz!\n\n"
    "Bu yerda professional shartnomalar va hujjatlarni "
    "<b>10 soniyada</b> PDF formatida yaratishingiz mumkin:\n\n"
    "💼 Freelance shartnoma\n"
    "🤝 Jismoniy–yuridik shartnoma\n"
    "🏢 Yuridik–yuridik shartnoma\n"
    "🏠 Uy ijara shartnomasi\n"
    "✅ Xizmat ko'rsatish akti\n\n"
    "Boshlash uchun quyidagi tugmani bosing 👇"
)

HELP_TEXT = (
    "<b>Hujjat AI — Yordam</b>\n\n"
    "/start — Bosh menyu va Web App ochish\n"
    "/help — Ushbu yordam\n\n"
    "Web App ichida kerakli hujjat turini tanlang, "
    "formani to'ldiring va PDF yuklab oling.\n\n"
    "Savollar: @HujjatAI_Bot"
)


def webapp_url() -> str:
    base = (Config.WEBAPP_URL or Config.FRONTEND_URL).rstrip("/")
    if not base.endswith(".html"):
        base = f"{base}/index.html"
    return base


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text="📄 Hujjat yaratish",
            web_app=WebAppInfo(url=webapp_url()),
        )],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(
        WELCOME_TEXT,
        parse_mode="HTML",
        reply_markup=main_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(HELP_TEXT, parse_mode="HTML")


async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(
        "Buyruqni tanlang yoki Web App orqali davom eting 👇",
        reply_markup=main_keyboard(),
    )


async def post_init(application: Application) -> None:
    url = webapp_url()
    await application.bot.set_my_commands([
        BotCommand("start", "Bosh menyu"),
        BotCommand("help", "Yordam"),
    ])
    await application.bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(text="Hujjat AI", web_app=WebAppInfo(url=url)),
    )
    logger.info("Web App URL: %s", url)
    if url.startswith("http://"):
        logger.warning(
            "Telegram Web App HTTPS talab qiladi. "
            "Production uchun WEBAPP_URL ni https manzilga o'rnating."
        )


def validate_config() -> None:
    token = Config.BOT_TOKEN
    if not token or token == "your_bot_token_here":
        print("XATO: .env faylida BOT_TOKEN to'ldirilmagan.")
        print("BotFather dan token oling va .env ga qo'ying.")
        sys.exit(1)


def main() -> None:
    validate_config()
    application = (
        Application.builder()
        .token(Config.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))

    logger.info("Hujjat AI bot ishga tushmoqda...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
