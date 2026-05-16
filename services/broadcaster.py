import asyncio
import logging

from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User

logger = logging.getLogger(__name__)


async def broadcast_message(
    bot: Bot,
    session: AsyncSession,
    text: str,
    parse_mode: str = "HTML",
) -> tuple[int, int]:
    result = await session.execute(
        select(User.telegram_id).where(User.is_blocked == False)
    )
    user_ids = result.scalars().all()

    success = 0
    failed = 0

    for user_id in user_ids:
        try:
            await bot.send_message(chat_id=user_id, text=text, parse_mode=parse_mode)
            success += 1
        except Exception as e:
            logger.warning(f"Failed to send to {user_id}: {e}")
            failed += 1

        await asyncio.sleep(0.05)

    return success, failed
