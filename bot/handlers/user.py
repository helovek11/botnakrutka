import logging

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from config import Config
from bot.keyboards.inline import main_menu, socials_buttons, back_button
from services.conversation import (
    get_or_create_user,
    get_or_create_active_conversation,
    save_message,
    increment_button_click,
)
from utils.helpers import extract_user_info


def admin_forward_keyboard(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Ответить", callback_data=f"admin:reply:{user_id}"),
    )
    return builder.as_markup()

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, config: Config, session: AsyncSession):
    user_info = extract_user_info(message)
    await get_or_create_user(
        session,
        telegram_id=user_info["telegram_id"],
        username=user_info["username"],
        full_name=user_info["full_name"],
    )

    await message.answer(
        config.WELCOME_TEXT,
        parse_mode="Markdown",
        reply_markup=main_menu(config),
    )


@router.callback_query(F.data == "menu:back")
async def back_to_menu(callback: CallbackQuery, config: Config):
    await callback.message.edit_text(
        config.WELCOME_TEXT,
        parse_mode="Markdown",
        reply_markup=main_menu(config),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:price")
async def show_price(callback: CallbackQuery, config: Config, session: AsyncSession):
    await increment_button_click(session, "price")

    if config.PRICE_PHOTO:
        await callback.message.answer_photo(
            photo=config.PRICE_PHOTO,
            caption=config.PRICE_TEXT,
            parse_mode="Markdown",
            reply_markup=back_button(),
        )
    else:
        await callback.message.edit_text(
            config.PRICE_TEXT,
            parse_mode="Markdown",
            reply_markup=back_button(),
        )
    await callback.answer()


@router.callback_query(F.data == "menu:reviews")
async def show_reviews(callback: CallbackQuery, config: Config, session: AsyncSession):
    await increment_button_click(session, "reviews")

    text = config.REVIEWS_TEXT.format(link=config.REVIEWS_LINK)
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=back_button(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:socials")
async def show_socials(callback: CallbackQuery, config: Config, session: AsyncSession):
    await increment_button_click(session, "socials")

    await callback.message.edit_text(
        "📱 **Наши соцсети**\n\nВыберите платформу:",
        parse_mode="Markdown",
        reply_markup=socials_buttons(config),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:support")
async def start_support(
    callback: CallbackQuery, config: Config, session: AsyncSession
):
    await increment_button_click(session, "support")

    user_info = extract_user_info(callback.message)
    await get_or_create_user(
        session,
        telegram_id=user_info["telegram_id"],
        username=user_info["username"],
        full_name=user_info["full_name"],
    )
    await get_or_create_active_conversation(session, user_info["telegram_id"])

    await callback.message.edit_text(
        "💬 **Напишите ваше сообщение**\n\n"
        "Опишите ваш вопрос или проблему, и наш специалист "
        "свяжется с вами в ближайшее время.\n\n"
        "Вы можете отправлять текст, фото, видео и документы.",
        parse_mode="Markdown",
        reply_markup=back_button(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:admin_info")
async def admin_info(callback: CallbackQuery, config: Config, session: AsyncSession):
    await increment_button_click(session, "admin_info")

    text = (
        "👤 **Администрация**\n\n"
        "По вопросам сотрудничества и другим важным вопросам "
        "вы можете написать администратору напрямую.\n\n"
        "Для этого нажмите кнопку ниже, и ваше сообщение будет "
        "перенаправлено администратору."
    )
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=back_button(),
    )
    await callback.answer()


@router.message(F.text | F.photo | F.video | F.voice | F.document | F.audio)
async def forward_user_message(
    message: Message, config: Config, session: AsyncSession
):
    if message.from_user.id in config.ADMIN_IDS:
        return

    user_info = extract_user_info(message)
    user = await get_or_create_user(
        session,
        telegram_id=user_info["telegram_id"],
        username=user_info["username"],
        full_name=user_info["full_name"],
    )
    conv = await get_or_create_active_conversation(session, user.telegram_id)

    media_type = None
    file_id = None
    if message.photo:
        media_type = "photo"
        file_id = message.photo[-1].file_id
    elif message.video:
        media_type = "video"
        file_id = message.video.file_id
    elif message.voice:
        media_type = "voice"
        file_id = message.voice.file_id
    elif message.document:
        media_type = "document"
        file_id = message.document.file_id
    elif message.audio:
        media_type = "audio"
        file_id = message.audio.file_id

    await save_message(
        session,
        conversation_id=conv.id,
        from_user_id=user.telegram_id,
        text=message.text or message.caption,
        media_type=media_type,
        file_id=file_id,
        telegram_message_id=message.message_id,
    )

    await message.answer(
        "✅ **Ваше сообщение отправлено!**\n\n"
        "Мы свяжемся с вами в ближайшее время.",
        parse_mode="Markdown",
    )

    for admin_id in config.ADMIN_IDS:
        try:
            user_display = (
                f"@{user.username}" if user.username
                else user.full_name or f"ID {user.telegram_id}"
            )
            caption = (
                f"💬 **Новое сообщение от {user_display}**\n"
                f"Диалог: `{conv.id[:8]}...`\n\n"
                f"{message.text or message.caption or ''}"
            )

            kwargs = {
                "caption": caption,
                "parse_mode": "Markdown",
                "reply_markup": admin_forward_keyboard(user.telegram_id),
            }

            if media_type == "photo" and file_id:
                sent = await message.bot.send_photo(
                    chat_id=admin_id, photo=file_id, **kwargs
                )
            elif media_type == "video" and file_id:
                sent = await message.bot.send_video(
                    chat_id=admin_id, video=file_id, **kwargs
                )
            elif media_type == "voice" and file_id:
                sent = await message.bot.send_voice(
                    chat_id=admin_id, voice=file_id, **kwargs
                )
            elif media_type == "document" and file_id:
                sent = await message.bot.send_document(
                    chat_id=admin_id, document=file_id, **kwargs
                )
            elif media_type == "audio" and file_id:
                sent = await message.bot.send_audio(
                    chat_id=admin_id, audio=file_id, **kwargs
                )
            else:
                sent = await message.bot.send_message(
                    chat_id=admin_id,
                    text=caption,
                    parse_mode="Markdown",
                    reply_markup=admin_forward_keyboard(user.telegram_id),
                )

            await save_message(
                session,
                conversation_id=conv.id,
                from_user_id=user.telegram_id,
                text=message.text or message.caption,
                is_from_admin=False,
                media_type=media_type,
                file_id=file_id,
                telegram_message_id=sent.message_id,
            )
        except Exception as e:
            logger.error(f"Failed to forward to admin {admin_id}: {e}")
