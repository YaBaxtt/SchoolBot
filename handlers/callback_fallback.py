"""Final callback handler: stale or forbidden buttons must never spin forever."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from database import get_user_by_tg_id
from locales.texts import TEXTS

callback_fallback_router = Router()
logger = logging.getLogger(__name__)


@callback_fallback_router.callback_query()
async def handle_unmatched_callback(callback: CallbackQuery) -> None:
    user = await get_user_by_tg_id(callback.from_user.id)
    lang = user.language if user and user.language in TEXTS else "ru"
    is_protected_action = (callback.data or "").startswith(("admin:", "staff:"))
    if is_protected_action:
        logger.warning("Denied protected callback for Telegram user %s", callback.from_user.id)
    text_key = "access_denied" if is_protected_action else "callback_expired"
    await callback.answer(TEXTS[lang][text_key], show_alert=True)


@callback_fallback_router.message(Command("admin", "staff", "moderator"))
async def handle_denied_privileged_command(message: Message) -> None:
    """Give students a clear refusal when no protected router accepted a command."""
    user = await get_user_by_tg_id(message.from_user.id)
    lang = user.language if user and user.language in TEXTS else "ru"
    await message.answer(TEXTS[lang]["access_denied"])
