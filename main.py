import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from config import Config
from db.database import init_db, close_db

# Bot handlers
from bot.handlers import user, admin, callbacks
from bot.middlewares.antispam import AntiSpamMiddleware
from bot.middlewares.logging import LoggingMiddleware

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def main():
    config = Config()
    logger.info("Starting SupportBot...")

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp["config"] = config

    await init_db(config)

    dp.include_router(user.router)
    dp.include_router(admin.router)
    dp.include_router(callbacks.router)

    user.router.message.middleware(AntiSpamMiddleware())
    user.router.callback_query.middleware(AntiSpamMiddleware())
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())

    logger.info("Bot is polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
