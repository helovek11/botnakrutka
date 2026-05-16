from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import Config


def main_menu(config: Config) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 Прайс", callback_data="menu:price"),
        InlineKeyboardButton(text="⭐ Отзывы", callback_data="menu:reviews"),
        width=2,
    )
    builder.row(
        InlineKeyboardButton(text="💬 Написать в поддержку", callback_data="menu:support"),
        width=1,
    )
    builder.row(
        InlineKeyboardButton(text="📱 Соцсети", callback_data="menu:socials"),
        InlineKeyboardButton(text="👤 Администрация", callback_data="menu:admin_info"),
        width=2,
    )
    return builder.as_markup()


def socials_buttons(config: Config) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for name, url in config.SOCIALS.items():
        builder.row(InlineKeyboardButton(text=name, url=url))
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="menu:back"),
    )
    return builder.as_markup()


def back_button() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="menu:back"))
    return builder.as_markup()


def admin_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💬 Активные диалоги", callback_data="admin:dialogs"),
        width=1,
    )
    builder.row(
        InlineKeyboardButton(text="⚡ Быстрые ответы", callback_data="admin:quick_replies"),
        width=1,
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats"),
        width=1,
    )
    builder.row(
        InlineKeyboardButton(text="📢 Рассылка", callback_data="admin:broadcast"),
        width=1,
    )
    builder.row(
        InlineKeyboardButton(text="🔙 В главное меню", callback_data="menu:back"),
    )
    return builder.as_markup()


STATUS_EMOJI = {
    "new": "🆕",
    "in_progress": "🔴",
    "waiting_client": "⏳",
    "closed": "⚫",
}


def dialogs_list(dialogs: list[tuple]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for user_id, name, status, msg_count in dialogs:
        emoji = STATUS_EMOJI.get(status, "⚫")
        label = f"{emoji} {name or f'ID {user_id}'} ({msg_count})"
        builder.row(
            InlineKeyboardButton(text=label, callback_data=f"admin:open_dialog:{user_id}"),
        )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="admin:menu"),
    )
    return builder.as_markup()


def dialog_actions(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Ответить", callback_data=f"admin:reply:{user_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🔒 Закрыть диалог", callback_data=f"admin:close:{user_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="📝 Быстрый ответ", callback_data=f"admin:quick:{user_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="« Назад к диалогам", callback_data="admin:dialogs"),
    )
    return builder.as_markup()


def quick_replies_list(replies: list[tuple]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for reply_id, title in replies:
        builder.row(
            InlineKeyboardButton(text=title, callback_data=f"admin:use_quick:{reply_id}"),
        )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="admin:menu"),
    )
    return builder.as_markup()


def cancel_button() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="admin:cancel"))
    return builder.as_markup()
