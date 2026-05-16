import time
from collections import defaultdict
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

from config import Config


class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 5, window: int = 10):
        self.limit = limit
        self.window = window
        self.user_messages: dict[int, list[float]] = defaultdict(list)

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        config: Config | None = data.get("config")
        if config:
            actual_limit = config.RATE_LIMIT
            actual_window = config.RATE_LIMIT_WINDOW
        else:
            actual_limit = self.limit
            actual_window = self.window

        user_id = event.from_user.id

        if user_id in (config.ADMIN_IDS if config else []):
            return await handler(event, data)

        now = time.time()
        self.user_messages[user_id] = [
            t for t in self.user_messages[user_id] if now - t < actual_window
        ]

        if len(self.user_messages[user_id]) >= actual_limit:
            await event.answer(
                "⏳ Слишком много сообщений. Пожалуйста, подождите немного.",
                show_alert=True,
            )
            return

        self.user_messages[user_id].append(now)
        return await handler(event, data)
