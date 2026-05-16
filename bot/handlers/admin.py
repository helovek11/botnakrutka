import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import Config
from bot.filters import IsAdminFilter
from bot.keyboards.inline import (
    admin_menu,
    dialogs_list,
    dialog_actions,
    quick_replies_list,
    cancel_button,
)
from bot.states import BroadcastStates, QuickReplyStates
from db.models import QuickReply, Conversation
from services.conversation import (
    get_or_create_user,
    get_or_create_active_conversation,
    get_active_dialogs,
    get_conversation_messages,
    close_conversation,
    update_conversation_status,
    save_message,
    find_message_by_forward,
    get_button_stats,
)
from services.broadcaster import broadcast_message
from utils.helpers import format_dialog_history, format_stats, extract_user_info

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(IsAdminFilter())
router.callback_query.filter(IsAdminFilter())


@router.message(Command("admin"))
async def admin_panel(message: Message):
    await message.answer(
        "🔧 **Админ-панель**\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=admin_menu(),
    )


@router.callback_query(F.data == "admin:menu")
async def admin_menu_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔧 **Админ-панель**\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=admin_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:dialogs")
async def list_dialogs(callback: CallbackQuery, session: AsyncSession):
    dialogs = await get_active_dialogs(session)

    if not dialogs:
        await callback.message.edit_text(
            "📭 **Нет активных диалогов**",
            parse_mode="Markdown",
            reply_markup=admin_menu(),
        )
        await callback.answer()
        return

    text = f"💬 **Активные диалоги** ({len(dialogs)}):\n\n"
    await callback.message.edit_text(
        text, parse_mode="Markdown",
        reply_markup=dialogs_list(dialogs),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:open_dialog:"))
async def open_dialog(callback: CallbackQuery, session: AsyncSession):
    user_id = int(callback.data.split(":")[-1])
    messages = await get_conversation_messages(session, user_id)
    history = format_dialog_history(messages, user_id)

    text = f"💬 **Диалог с пользователем ID {user_id}**\n\n```\n{history}\n```"
    await callback.message.edit_text(
        text[:4000],
        parse_mode="Markdown",
        reply_markup=dialog_actions(user_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:reply:"))
async def start_reply(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[-1])
    await callback.message.answer(
        f"✏️ Ответьте пользователю **ID {user_id}**\n\n"
        "Просто ответьте на любое его сообщение в этом чате "
        "(через Reply в Telegram), и бот доставит ответ.",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:close:"))
async def close_dialog_handler(callback: CallbackQuery, session: AsyncSession):
    user_id = int(callback.data.split(":")[-1])
    conv = await get_or_create_active_conversation(session, user_id)
    await close_conversation(session, conv.id)

    await callback.message.edit_text(
        f"✅ **Диалог с пользователем ID {user_id} закрыт**",
        parse_mode="Markdown",
        reply_markup=admin_menu(),
    )

    try:
        await callback.bot.send_message(
            chat_id=user_id,
            text="✅ **Ваш диалог закрыт.**\n\n"
                 "Если у вас появятся новые вопросы, "
                 "просто напишите нам!",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Failed to notify user {user_id}: {e}")

    await callback.answer()


@router.callback_query(F.data == "admin:stats")
async def show_stats(callback: CallbackQuery, session: AsyncSession):
    stats = await get_button_stats(session)
    text = format_stats(stats) if stats else "📊 **Статистика**\n\nПока нет данных."
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=admin_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:quick_replies")
async def list_quick_replies(callback: CallbackQuery, session: AsyncSession):
    result = await session.execute(
        QuickReply.__table__.select().order_by(QuickReply.title)
    )
    replies = result.all()

    if not replies:
        text = "⚡ **Нет быстрых ответов**"
        await callback.message.edit_text(
            text, parse_mode="Markdown",
        )
        await callback.answer()
        return

    kb = quick_replies_list([(r.id, r.title) for r in replies])
    await callback.message.edit_text(
        "⚡ **Быстрые ответы**\n\nВыберите шаблон:",
        parse_mode="Markdown",
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:use_quick:"))
async def use_quick_reply(callback: CallbackQuery, session: AsyncSession):
    reply_id = int(callback.data.split(":")[-1])
    result = await session.get(QuickReply, reply_id)
    if not result:
        await callback.answer("Шаблон не найден", show_alert=True)
        return

    await callback.message.answer(
        f"📝 **Шаблон:** {result.title}\n\n{result.text}",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "admin:broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastStates.waiting_for_text)
    await callback.message.answer(
        "📢 **Введите текст для рассылки:**\n\n"
        "Поддерживается HTML-разметка.\n"
        "Отправьте /cancel для отмены.",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(BroadcastStates.waiting_for_text, F.text)
async def broadcast_text_received(message: Message, state: FSMContext):
    await state.update_data(broadcast_text=message.text)
    await state.set_state(BroadcastStates.confirm)
    preview = message.text[:200] + ("..." if len(message.text) > 200 else "")
    await message.answer(
        f"📢 **Предварительный просмотр:**\n\n{preview}\n\n"
        f"Отправить всем пользователям?\n"
        f"Напишите \"да\" для подтверждения или \"нет\" для отмены.",
        parse_mode="Markdown",
    )


@router.message(BroadcastStates.waiting_for_text)
async def broadcast_text_received_non_text(message: Message):
    await message.answer("Пожалуйста, отправьте текстовое сообщение.")


@router.message(BroadcastStates.waiting_for_text, Command("cancel"))
@router.message(BroadcastStates.confirm, Command("cancel"))
async def cancel_broadcast(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🚫 Рассылка отменена.")


@router.message(BroadcastStates.confirm, F.text)
async def broadcast_confirm(
    message: Message, state: FSMContext, config: Config, session: AsyncSession
):
    if message.text.lower() in ["да", "yes", "отправить", "send"]:
        data = await state.get_data()
        text = data.get("broadcast_text", "")
        await message.answer("📢 **Рассылка запущена...**", parse_mode="Markdown")
        success, failed = await broadcast_message(
            bot=message.bot,
            session=session,
            text=text,
        )
        await message.answer(
            f"✅ **Рассылка завершена!**\n\n"
            f"• Успешно: {success}\n"
            f"• Ошибок: {failed}",
            parse_mode="Markdown",
            reply_markup=admin_menu(),
        )
    else:
        await message.answer("🚫 Рассылка отменена.", reply_markup=admin_menu())
    await state.clear()


@router.message(F.reply_to_message)
async def admin_reply_via_reply(
    message: Message, config: Config, session: AsyncSession, state: FSMContext
):
    current_state = await state.get_state()
    if current_state is not None:
        return

    replied = message.reply_to_message
    if not replied:
        return

    msg_record = await find_message_by_forward(
        session,
        forward_message_id=replied.message_id,
        forward_chat_id=message.chat.id,
    )
    if not msg_record:
        return

    conv = await session.get(Conversation, msg_record.conversation_id)
    if conv is None:
        return

    user_id = conv.user_id

    user_info = extract_user_info(message)
    admin_user = await get_or_create_user(
        session,
        telegram_id=user_info["telegram_id"],
        username=user_info["username"],
        full_name=user_info["full_name"],
    )

    text_content = message.text or message.caption or ""
    admin_display = (
        f"@{admin_user.username}" if admin_user.username
        else admin_user.full_name or "Администратор"
    )
    text_to_user = (
        f"✉️ **Ответ от {admin_display}:**\n\n{text_content}"
    )

    media_type = None
    file_id = None
    try:
        if message.photo:
            media_type = "photo"
            file_id = message.photo[-1].file_id
            sent = await message.bot.send_photo(
                chat_id=user_id, photo=file_id,
                caption=text_to_user, parse_mode="Markdown",
            )
        elif message.video:
            media_type = "video"
            file_id = message.video.file_id
            sent = await message.bot.send_video(
                chat_id=user_id, video=file_id,
                caption=text_to_user, parse_mode="Markdown",
            )
        elif message.document:
            media_type = "document"
            file_id = message.document.file_id
            sent = await message.bot.send_document(
                chat_id=user_id, document=file_id,
                caption=text_to_user, parse_mode="Markdown",
            )
        elif message.voice:
            media_type = "voice"
            file_id = message.voice.file_id
            sent = await message.bot.send_voice(
                chat_id=user_id, voice=file_id,
                caption=text_to_user, parse_mode="Markdown",
            )
        else:
            sent = await message.bot.send_message(
                chat_id=user_id,
                text=text_to_user,
                parse_mode="Markdown",
            )

        await save_message(
            session,
            conversation_id=conv.id,
            from_user_id=admin_user.telegram_id,
            text=text_content,
            is_from_admin=True,
            media_type=media_type,
            file_id=file_id,
            telegram_message_id=sent.message_id,
        )

        await update_conversation_status(session, conv.id, "waiting_client")

        await message.reply(
            "✅ **Ответ отправлен!**",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Failed to send reply to {user_id}: {e}")
        await message.reply(
            f"❌ **Ошибка:** {e}",
            parse_mode="Markdown",
        )


@router.callback_query(F.data == "admin:cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🔧 **Админ-панель**\n\nДействие отменено.",
        parse_mode="Markdown",
        reply_markup=admin_menu(),
    )
    await callback.answer()
