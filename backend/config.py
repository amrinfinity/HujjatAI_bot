import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


class Config:
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "8000"))
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5500")
    WEBAPP_URL = os.getenv("WEBAPP_URL", "")

    @classmethod
    def cors_origins(cls) -> list[str]:
        origins = {
            cls.FRONTEND_URL,
            "http://localhost:5500",
            "http://127.0.0.1:5500",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "https://hujjat-ai-bot.vercel.app",
        }
        for url in (cls.WEBAPP_URL, cls.FRONTEND_URL):
            if url:
                parsed = urlparse(url)
                if parsed.scheme and parsed.netloc:
                    origins.add(f"{parsed.scheme}://{parsed.netloc}")
        extra = os.getenv("CORS_EXTRA_ORIGINS", "")
        for origin in extra.split(","):
            origin = origin.strip()
            if origin:
                origins.add(origin)
        return [origin for origin in origins if origin]
