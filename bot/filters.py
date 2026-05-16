from aiogram.filters import BaseFilter
from aiogram.types import Message

from config import Config


class IsAdminFilter(BaseFilter):
    async def __call__(self, message: Message, config: Config = None) -> bool:
        if config is None:
            return False
        return message.from_user.id in config.ADMIN_IDS


class IsNotMaintenance(BaseFilter):
    async def __call__(self, message: Message, config: Config = None) -> bool:
        if config is None:
            return True
        if config.MAINTENANCE_MODE:
            if message.from_user.id in config.ADMIN_IDS:
                return True
            return False
        return True
