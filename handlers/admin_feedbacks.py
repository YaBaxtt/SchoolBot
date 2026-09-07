import logging
from html import escape

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import requests as db
from filters.roles import ADMIN_ROLES, RoleFilter
from permissions import can_view_complaints
from keyboards.admin_kb import (
    AdminCB,
    get_back_to_admin_kb,
    get_feedback_detail_kb,
    get_feedback_filter_kb,
    get_feedback_list_kb,
    get_reply_confirm_kb,
)
from states.feedback import AdminReplyState

admin_feedbacks_router = Router()
admin_feedbacks_router.callback_query.filter(RoleFilter(ADMIN_ROLES))
admin_feedbacks_router.message.filter(RoleFilter(ADMIN_ROLES))

logger = logging.getLogger(__name__)
SECTIONS = {
    "complaints": ("complaint", "📩 <b>Жалобы</b>"),
    "suggestions": ("suggestion", "💡 <b>Предложения</b>"),
}
STATUS_LABELS = {"new": "🟢 Новые", "in_progress": "🟡 В работе", "closed": "🔴 Закрытые"}
COMPLAINTS_DENIED = "Доступ к жалобам разрешён только SuperAdmin."


async def _can_access_complaints(call: CallbackQuery) -> bool:
    """Complaint data is intentionally restricted to SuperAdmin accounts."""
    actor = await db.get_user_by_tg_id(call.from_user.id)
    if can_view_complaints(actor):
        return True
    await call.answer(COMPLAINTS_DENIED, show_alert=True)
    return False


async def _get_accessible_feedback(call: CallbackQuery, feedback_id: int):
    feedback = await db.get_feedback_by_id(feedback_id)
    if not feedback:
        await call.answer("Обращение не найдено.", show_alert=True)
        return None
    if feedback.type == "complaint" and not await _can_access_complaints(call):
        return None
    return feedback


@admin_feedbacks_router.callback_query(AdminCB.filter(F.action.in_(set(SECTIONS))))
async def cb_feedback_main(call: CallbackQuery, callback_data: AdminCB, state: FSMContext) -> None:
    await state.clear()
    if callback_data.action == "complaints" and not await _can_access_complaints(call):
        return
    db_type, title = SECTIONS[callback_data.action]
    items = await db.get_recent_feedbacks(db_type, limit=10)
    text = f"{title}\n\nВыберите категорию:"
    if items:
        text += f"\n\nПоследних обращений: {len(items)}"
    await call.message.edit_text(
        text, reply_markup=get_feedback_filter_kb(callback_data.action), parse_mode="HTML"
    )
    await call.answer()


@admin_feedbacks_router.callback_query(AdminCB.filter(F.action.in_({"complaints_status", "suggestions_status"})))
async def cb_feedback_by_status(call: CallbackQuery, callback_data: AdminCB) -> None:
    section = callback_data.action.removesuffix("_status")
    status = callback_data.param
    if section not in SECTIONS or status not in STATUS_LABELS:
        await call.answer("Некорректный фильтр.", show_alert=True)
        return
    if section == "complaints" and not await _can_access_complaints(call):
        return
    db_type, title = SECTIONS[section]
    items = await db.get_feedbacks_by_status(db_type, status, limit=20)
    text = f"{title}\n\n{STATUS_LABELS[status]}"
    if not items:
        text += "\n\nВ этой категории записей нет."
    else:
        text += "\n\nВыберите обращение:"
    await call.message.edit_text(
        text, reply_markup=get_feedback_list_kb(items, section), parse_mode="HTML"
    )
    await call.answer()


def _feedback_title(feedback_type: str) -> str:
    return "📩 <b>Жалоба</b>" if feedback_type == "complaint" else "💡 <b>Предложение</b>"


async def show_feedback_card(call: CallbackQuery, feedback_id: int) -> None:
    feedback = await _get_accessible_feedback(call, feedback_id)
    if not feedback:
        return
    author = feedback.user
    class_name = escape(author.class_name) if author else "—"
    date = feedback.created_at.strftime("%d.%m.%Y %H:%M") if feedback.created_at else "—"
    status = STATUS_LABELS.get(feedback.status, feedback.status)
    text = (
        f"{_feedback_title(feedback.type)} #{feedback.id}\n\n"
        f"Класс: {class_name}\n"
        f"Дата: {date}\n"
        f"Статус: {status}\n\n"
        f"<b>Текст:</b>\n{escape(feedback.text)}"
    )
    await call.message.edit_text(text, reply_markup=get_feedback_detail_kb(feedback), parse_mode="HTML")
    await call.answer()


@admin_feedbacks_router.callback_query(AdminCB.filter(F.action == "feedback_view"))
async def cb_feedback_view(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        feedback_id = int(callback_data.param)
    except ValueError:
        await call.answer("Некорректное обращение.", show_alert=True)
        return
    await show_feedback_card(call, feedback_id)


@admin_feedbacks_router.callback_query(AdminCB.filter(F.action == "feedback_set_status"))
async def cb_feedback_set_status(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        feedback_id_raw, status = callback_data.param.split("|", 1)
        feedback_id = int(feedback_id_raw)
    except (AttributeError, ValueError):
        await call.answer("Некорректные данные.", show_alert=True)
        return
    if status not in {"in_progress", "closed"}:
        await call.answer("Некорректный статус.", show_alert=True)
        return
    if not await _get_accessible_feedback(call, feedback_id):
        return
    if not await db.update_feedback_status(feedback_id, status):
        await call.answer("Обращение не найдено.", show_alert=True)
        return
    await show_feedback_card(call, feedback_id)


@admin_feedbacks_router.callback_query(AdminCB.filter(F.action == "reply_feedback"))
async def cb_start_reply(call: CallbackQuery, callback_data: AdminCB, state: FSMContext) -> None:
    try:
        feedback_id = int(callback_data.param)
    except ValueError:
        await call.answer("Некорректное обращение.", show_alert=True)
        return
    feedback = await _get_accessible_feedback(call, feedback_id)
    if not feedback or not feedback.user:
        await call.answer("Обращение не найдено.", show_alert=True)
        return
    await state.clear()
    await state.update_data(reply_feedback_id=feedback_id, user_tg_id=feedback.user.telegram_id)
    await state.set_state(AdminReplyState.waiting_for_reply)
    await call.message.edit_text(
        f"✉️ <b>Ответ на обращение №{feedback_id}</b>\n\nВведите текст ответа:", parse_mode="HTML"
    )
    await call.answer()


@admin_feedbacks_router.message(AdminReplyState.waiting_for_reply)
async def process_reply_text(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("⚠️ Ответ не может быть пустым.")
        return
    await state.update_data(reply_text=text)
    await state.set_state(AdminReplyState.waiting_for_confirm)
    await message.answer(
        f"👀 <b>Предпросмотр ответа</b>\n\n{escape(text)}\n\nОтправить ученику?",
        reply_markup=get_reply_confirm_kb(),
        parse_mode="HTML",
    )


@admin_feedbacks_router.callback_query(
    AdminReplyState.waiting_for_confirm, AdminCB.filter(F.action == "reply_cancel")
)
async def cb_cancel_reply(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text("❌ Ответ отменён.", reply_markup=get_back_to_admin_kb())
    await call.answer()


@admin_feedbacks_router.callback_query(AdminReplyState.waiting_for_confirm, AdminCB.filter(F.action == "reply_send"))
async def cb_send_reply(call: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    feedback_id = data.get("reply_feedback_id")
    user_tg_id = data.get("user_tg_id")
    reply_text = data.get("reply_text")
    if not feedback_id or not user_tg_id or not reply_text:
        await state.clear()
        await call.message.edit_text("⚠️ Не удалось найти данные ответа.", reply_markup=get_back_to_admin_kb())
        await call.answer()
        return
    feedback = await _get_accessible_feedback(call, feedback_id)
    if not feedback:
        await state.clear()
        return
    if not feedback.user or feedback.user.telegram_id != user_tg_id:
        await state.clear()
        await call.message.edit_text("⚠️ Доступ к обращению закрыт.", reply_markup=get_back_to_admin_kb())
        await call.answer()
        return
    try:
        await bot.send_message(
            user_tg_id,
            "📨 <b>Ответ администрации</b>\n\n"
            f"По вашему обращению #{feedback_id}:\n\n{escape(reply_text)}",
            parse_mode="HTML",
        )
    except TelegramForbiddenError:
        await call.message.edit_text("⚠️ Пользователь заблокировал бота. Ответ не отправлен.", reply_markup=get_back_to_admin_kb())
        await call.answer()
        await state.clear()
        return
    except TelegramBadRequest as error:
        logger.warning("Unable to send feedback reply %s: %s", feedback_id, error)
        await call.message.edit_text("⚠️ Не удалось отправить ответ пользователю.", reply_markup=get_back_to_admin_kb())
        await call.answer()
        await state.clear()
        return
    except Exception:
        logger.exception("Unexpected feedback reply failure for %s", feedback_id)
        await call.message.edit_text("⚠️ Произошла ошибка при отправке ответа.", reply_markup=get_back_to_admin_kb())
        await call.answer()
        await state.clear()
        return
    await db.update_feedback_status(feedback_id, "closed")
    await state.clear()
    await call.message.edit_text("✅ Ответ отправлен пользователю, обращение закрыто.", reply_markup=get_back_to_admin_kb())
    await call.answer()
