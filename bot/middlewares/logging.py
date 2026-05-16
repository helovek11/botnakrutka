import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        user = event.from_user
        if isinstance(event, Message):
            logger.info(
                "Message from %s (%d): %s",
                user.full_name or user.username or "unknown",
                user.id,
                event.text or "[non-text]",
            )
        elif isinstance(event, CallbackQuery):
            logger.info(
                "Callback from %s (%d): %s",
                user.full_name or user.username or "unknown",
                user.id,
                event.data,
            )
        return await handler(event, data)
