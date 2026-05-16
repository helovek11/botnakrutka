from datetime import datetime, timezone

from sqlalchemy import select, func, update, or_
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Conversation, Message, User, ButtonStats

ACTIVE_STATUSES = ("new", "in_progress", "waiting_client")


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    full_name: str | None = None,
) -> User:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
        )
        session.add(user)
    else:
        if username != user.username or full_name != user.full_name:
            user.username = username
            user.full_name = full_name
        user.last_activity = datetime.now(timezone.utc)

    await session.commit()
    return user


async def get_or_create_active_conversation(
    session: AsyncSession, user_id: int
) -> Conversation:
    result = await session.execute(
        select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.status.in_(ACTIVE_STATUSES),
        )
    )
    conv = result.scalar_one_or_none()

    if conv is None:
        conv = Conversation(user_id=user_id, status="new")
        session.add(conv)
        await session.commit()

    return conv


async def update_conversation_status(
    session: AsyncSession, conversation_id: str, status: str
) -> None:
    await session.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(status=status, updated_at=datetime.now(timezone.utc))
    )
    await session.commit()


async def close_conversation(session: AsyncSession, conversation_id: str) -> None:
    await update_conversation_status(session, conversation_id, "closed")


async def save_message(
    session: AsyncSession,
    conversation_id: str,
    from_user_id: int,
    text: str | None = None,
    is_from_admin: bool = False,
    media_type: str | None = None,
    file_id: str | None = None,
    telegram_message_id: int | None = None,
    forward_message_id: int | None = None,
    forward_chat_id: int | None = None,
) -> Message:
    msg = Message(
        conversation_id=conversation_id,
        from_user_id=from_user_id,
        text=text,
        is_from_admin=is_from_admin,
        media_type=media_type,
        file_id=file_id,
        telegram_message_id=telegram_message_id,
        forward_message_id=forward_message_id,
        forward_chat_id=forward_chat_id,
    )
    session.add(msg)
    await session.commit()
    return msg


async def update_message_forward(
    session: AsyncSession,
    message_id: str,
    forward_message_id: int,
    forward_chat_id: int,
) -> None:
    await session.execute(
        update(Message)
        .where(Message.id == message_id)
        .values(
            forward_message_id=forward_message_id,
            forward_chat_id=forward_chat_id,
        )
    )
    await session.commit()


async def find_message_by_forward(
    session: AsyncSession, forward_message_id: int, forward_chat_id: int
) -> Message | None:
    result = await session.execute(
        select(Message).where(
            Message.forward_message_id == forward_message_id,
            Message.forward_chat_id == forward_chat_id,
        )
    )
    return result.scalar_one_or_none()


async def get_active_dialogs(session: AsyncSession) -> list[tuple]:
    stmt = (
        select(
            User.telegram_id,
            User.full_name,
            Conversation.status,
            func.count(Message.id).label("msg_count"),
        )
        .join(Conversation, User.telegram_id == Conversation.user_id)
        .join(Message, Message.conversation_id == Conversation.id)
        .where(Conversation.status.in_(ACTIVE_STATUSES))
        .group_by(User.telegram_id, User.full_name, Conversation.status)
        .order_by(func.max(Message.created_at).desc())
    )
    result = await session.execute(stmt)
    return result.all()


async def get_conversation_messages(
    session: AsyncSession, user_id: int
) -> list[Message]:
    conv = await get_or_create_active_conversation(session, user_id)
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at)
    )
    return result.scalars().all()


async def increment_button_click(session: AsyncSession, button_name: str) -> None:
    result = await session.execute(
        select(ButtonStats).where(ButtonStats.button_name == button_name)
    )
    stat = result.scalar_one_or_none()

    if stat is None:
        stat = ButtonStats(
            button_name=button_name,
            clicks_count=1,
            last_clicked=datetime.now(timezone.utc),
        )
        session.add(stat)
    else:
        stat.clicks_count += 1
        stat.last_clicked = datetime.now(timezone.utc)

    await session.commit()


async def get_button_stats(session: AsyncSession) -> list[ButtonStats]:
    result = await session.execute(
        select(ButtonStats).order_by(ButtonStats.clicks_count.desc())
    )
    return result.scalars().all()
