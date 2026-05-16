import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS: List[int] = field(
        default_factory=lambda: [
            int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
        ]
    )
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/supportbot",
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    MAINTENANCE_MODE: bool = os.getenv("MAINTENANCE_MODE", "false").lower() == "true"

    PRICE_TEXT: str = os.getenv(
        "PRICE_TEXT",
        "📋 **Прайс-лист**\n\n"
        "1. Услуга A — 1000₽\n"
        "2. Услуга B — 2500₽\n"
        "3. Услуга C — 5000₽\n\n"
        "Для уточнения деталей напишите в поддержку.",
    )
    PRICE_PHOTO: str | None = os.getenv("PRICE_PHOTO", None)

    SOCIALS: dict = field(
        default_factory=lambda: {
            "YouTube": os.getenv("SOCIAL_YOUTUBE", "https://youtube.com/@channel"),
            "Instagram": os.getenv("SOCIAL_INSTAGRAM", "https://instagram.com/username"),
            "Telegram": os.getenv("SOCIAL_TELEGRAM", "https://t.me/username"),
        }
    )

    REVIEWS_LINK: str = os.getenv(
        "REVIEWS_LINK", "https://t.me/reviews_channel"
    )
    REVIEWS_TEXT: str = os.getenv(
        "REVIEWS_TEXT",
        "⭐ **Отзывы наших клиентов**\n\n"
        "Читайте отзывы в нашем Telegram-канале:\n"
        "{link}\n\n"
        "Оставляйте свои отзывы и предложения!",
    )

    WELCOME_TEXT: str = os.getenv(
        "WELCOME_TEXT",
        "👋 **Добро пожаловать в SupportBot!**\n\n"
        "Я — виртуальный помощник нашей компании. "
        "С помощью меня вы можете:\n"
        "• Узнать актуальный прайс 📋\n"
        "• Прочитать отзывы ⭐\n"
        "• Связаться с поддержкой 💬\n"
        "• Найти наши соцсети 📱\n\n"
        "Выберите нужный пункт в меню ниже:",
    )

    SUPPORT_GROUP_ID: int | None = (
        int(os.getenv("SUPPORT_GROUP_ID")) if os.getenv("SUPPORT_GROUP_ID") else None
    )

    RATE_LIMIT: int = int(os.getenv("RATE_LIMIT", "5"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "10"))
