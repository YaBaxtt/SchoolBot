from html import escape

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery

from database import requests as db
from filters.roles import ADMIN_ROLES, RoleFilter
from keyboards.admin_kb import AdminCB, get_class_change_decision_kb, get_class_change_requests_kb
from locales.texts import TEXTS


admin_class_changes_router = Router()
admin_class_changes_router.callback_query.filter(RoleFilter(ADMIN_ROLES))


async def show_class_change_requests(call: CallbackQuery) -> None:
    requests, _ = await db.get_pending_class_change_requests()
    text = "🔄 <b>Заявки на смену класса</b>\n\nВыберите заявку:" if requests else "🔄 <b>Заявки на смену класса</b>\n\nНовых заявок нет."
    await call.message.edit_text(text, reply_markup=get_class_change_requests_kb(requests), parse_mode="HTML")
    await call.answer()


@admin_class_changes_router.callback_query(AdminCB.filter(F.action == "class_changes"))
async def class_change_list(call: CallbackQuery) -> None:
    await show_class_change_requests(call)


@admin_class_changes_router.callback_query(AdminCB.filter(F.action == "class_change_view"))
async def class_change_view(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        request_id = int(callback_data.param or "")
    except ValueError:
        await call.answer("Некорректная заявка.", show_alert=True)
        return
    request = await db.get_class_change_request(request_id)
    if not request or request.status != "pending" or not request.user or not request.target_class:
        await call.answer("Заявка уже обработана или не найдена.", show_alert=True)
        return
    date = request.created_at.strftime("%d.%m.%Y %H:%M") if request.created_at else "—"
    text = (
        "🔄 <b>Заявка на смену класса</b>\n\n"
        f"👤 {escape(request.user.first_name)} {escape(request.user.last_name)}\n"
        f"🏫 {escape(request.old_class_name)} → <b>{escape(request.target_class.display_name)}</b>\n"
        f"🆔 <code>{escape(request.user.user_code or '—')}</code>\n"
        f"📅 {date}\n\nПричина:\n{escape(request.reason or '—')}"
    )
    await call.message.edit_text(text, reply_markup=get_class_change_decision_kb(request.id), parse_mode="HTML")
    await call.answer()


@admin_class_changes_router.callback_query(AdminCB.filter(F.action == "class_change_decision"))
async def class_change_decision(call: CallbackQuery, callback_data: AdminCB, bot: Bot) -> None:
    try:
        request_raw, decision = (callback_data.param or "").split("|", 1)
        request_id = int(request_raw)
    except ValueError:
        await call.answer("Некорректная заявка.", show_alert=True)
        return
    if decision not in {"approve", "reject"}:
        await call.answer("Некорректное решение.", show_alert=True)
        return
    reviewer = await db.get_user_by_tg_id(call.from_user.id)
    if not reviewer:
        await call.answer("Профиль сотрудника не найден.", show_alert=True)
        return
    request = await db.review_class_change_request(request_id, reviewer.id, decision == "approve")
    if not request or not request.user or not request.target_class:
        await call.answer("Заявка уже обработана или недоступна.", show_alert=True)
        return
    user_texts = TEXTS.get(request.user.language, TEXTS["ru"])
    if decision == "approve":
        notification = (
            f"✅ Ваша заявка одобрена. Новый класс: {request.target_class.display_name}."
            if request.user.language == "ru" else
            f"✅ So'rovingiz tasdiqlandi. Yangi sinf: {request.target_class.display_name}."
        )
        outcome = "✅ Заявка одобрена. Класс пользователя обновлён."
    else:
        notification = "❌ Заявка на смену класса отклонена." if request.user.language == "ru" else "❌ Sinfni almashtirish so'rovi rad etildi."
        outcome = "❌ Заявка отклонена."
    try:
        await bot.send_message(request.user.telegram_id, notification)
    except Exception:
        # The review is already committed; notification failure must not undo it.
        pass
    await call.message.edit_text(outcome, parse_mode="HTML")
    await call.answer()
