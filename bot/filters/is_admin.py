from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from config import Config


class IsAdminFilter(BaseFilter):
    async def __call__(
        self, event: Message | CallbackQuery, config: Config = None
    ) -> bool:
        if config is None:
            return False
        return event.from_user.id in config.ADMIN_IDS
