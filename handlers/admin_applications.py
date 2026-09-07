import logging
from html import escape

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import CallbackQuery
from config import REGISTRATION_REVIEW_CHAT_ID

from database import requests as db
from filters.roles import ADMIN_ROLES, RoleFilter
from keyboards.admin_kb import (
    AdminCB,
    get_applications_list_kb,
    get_back_to_admin_kb,
    get_registration_request_actions_kb,
)
from keyboards.main_kb import get_main_menu_kb
from locales.texts import TEXTS

admin_applications_router = Router()
admin_applications_router.callback_query.filter(RoleFilter(ADMIN_ROLES))
logger = logging.getLogger(__name__)
PER_PAGE = 8


async def show_applications(call: CallbackQuery, page: int = 1) -> None:
    requested_page = max(page, 1)
    users, total_pages = await db.get_pending_users_paginated(requested_page, PER_PAGE)
    page = min(requested_page, total_pages)
    if page != requested_page:
        users, total_pages = await db.get_pending_users_paginated(page, PER_PAGE)
    text = "📝 <b>Заявки на регистрацию</b>\n\nВыберите заявку:"
    if not users:
        text = "📝 <b>Заявки на регистрацию</b>\n\nНовых заявок нет."
    await call.message.edit_text(
        text, reply_markup=get_applications_list_kb(users, page, total_pages), parse_mode="HTML"
    )
    await call.answer()


@admin_applications_router.callback_query(AdminCB.filter(F.action == "applications"))
async def cb_applications(call: CallbackQuery) -> None:
    await show_applications(call)


@admin_applications_router.callback_query(AdminCB.filter(F.action == "applications_page"))
async def cb_applications_page(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        page = int(callback_data.param)
    except ValueError:
        await call.answer("Некорректная страница.", show_alert=True)
        return
    await show_applications(call, page)


@admin_applications_router.callback_query(AdminCB.filter(F.action == "application_view"))
async def cb_application_view(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        telegram_id = int(callback_data.param)
    except ValueError:
        await call.answer("Некорректная заявка.", show_alert=True)
        return
    user = await db.get_user_by_tg_id(telegram_id)
    if not user or user.status != "pending":
        await call.answer("Заявка уже обработана или не найдена.", show_alert=True)
        return
    text = (
        "📝 <b>Новая заявка</b>\n\n"
        f"Имя: {escape(user.first_name)}\n"
        f"Фамилия: {escape(user.last_name)}\n"
        f"Класс: {escape(user.class_name)}\n"
        f"User Code: <code>{escape(user.user_code or '—')}</code>"
    )
    await call.message.edit_text(
        text, reply_markup=get_registration_request_actions_kb(user.telegram_id), parse_mode="HTML"
    )
    await call.answer()


@admin_applications_router.callback_query(AdminCB.filter(F.action.in_({"application_accept", "application_reject"})))
async def cb_application_decision(call: CallbackQuery, callback_data: AdminCB, bot: Bot) -> None:
    try:
        telegram_id = int(callback_data.param)
    except ValueError:
        await call.answer("Некорректная заявка.", show_alert=True)
        return
    user = await db.get_user_by_tg_id(telegram_id)
    if not user or user.status != "pending":
        await call.answer("Заявка уже обработана или не найдена.", show_alert=True)
        return

    is_accepted = callback_data.action == "application_accept"
    reviewer = await db.get_user_by_tg_id(call.from_user.id)
    if not reviewer:
        await call.answer("Профиль сотрудника не найден.", show_alert=True)
        return
    user = await db.review_registration_request(telegram_id, reviewer.id, is_accepted)
    if not user:
        await call.answer("Заявка уже обработана.", show_alert=True)
        return
    lang_texts = TEXTS.get(user.language, TEXTS["ru"])
    try:
        if is_accepted:
            await bot.send_message(
                telegram_id,
                lang_texts["registration_approved"],
                reply_markup=get_main_menu_kb(user.language),
            )
        else:
            await bot.send_message(telegram_id, lang_texts["registration_rejected"])
    except TelegramForbiddenError:
        logger.info("Registration decision notification blocked by %s", telegram_id)
    except TelegramBadRequest as error:
        logger.warning("Registration decision notification failed for %s: %s", telegram_id, error)

    if REGISTRATION_REVIEW_CHAT_ID is not None and call.message.chat.id == REGISTRATION_REVIEW_CHAT_ID:
        reviewed_at = user.registration_reviewed_at.strftime("%d.%m.%Y %H:%M") if user.registration_reviewed_at else "—"
        result = (
            f"{'✅ ПРИНЯТО' if is_accepted else '❌ ОТКЛОНЕНО'}\n"
            f"Кем: {escape(reviewer.first_name)} {escape(reviewer.last_name)}\nКогда: {reviewed_at}"
        )
        await call.message.edit_text(result, parse_mode="HTML")
    else:
        result = "✅ Заявка принята. Пользователь получил доступ к School Bot." if is_accepted else "❌ Заявка отклонена."
        await call.message.edit_text(result, reply_markup=get_back_to_admin_kb())
    await call.answer()
