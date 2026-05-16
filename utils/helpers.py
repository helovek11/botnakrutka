from aiogram.types import Message


def extract_user_info(message: Message) -> dict:
    user = message.from_user
    return {
        "telegram_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
    }


def format_dialog_history(messages: list, current_user_id: int) -> str:
    lines = []
    for msg in messages:
        sender = "👤 Клиент" if msg.from_user_id == current_user_id else "🛠 Админ"
        time_str = msg.created_at.strftime("%d.%m %H:%M") if msg.created_at else ""
        text_preview = (msg.text or f"[{msg.media_type}]")[:200]
        lines.append(f"{time_str} {sender}: {text_preview}")
    return "\n".join(lines) if lines else "Нет сообщений"


def format_stats(stats) -> str:
    lines = ["📊 **Статистика кнопок**\n"]
    for stat in stats:
        lines.append(
            f"• {stat.button_name}: {stat.clicks_count} нажатий"
        )
    return "\n".join(lines)
