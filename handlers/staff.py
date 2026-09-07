import logging
from html import escape

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import requests as db
from filters.roles import STAFF_ROLES, RoleFilter, normalize_role
from permissions import UserRole, has_global_staff_scope
from keyboards.staff_kb import (
    StaffCB,
    get_staff_application_card_kb,
    get_staff_applications_kb,
    get_staff_announcement_classes_kb,
    get_staff_class_action_kb,
    get_staff_classes_kb,
    get_staff_cancel_kb,
    get_staff_confirm_kb,
    get_staff_feedback_card_kb,
    get_staff_feedback_list_kb,
    get_staff_feedback_status_kb,
    get_staff_main_kb,
    get_staff_students_kb,
)
from keyboards.main_kb import get_main_menu_kb
from locales.texts import TEXTS
from states.staff import StaffAnnouncementState, StaffReplyState

staff_router = Router()
staff_router.message.filter(RoleFilter(STAFF_ROLES))
staff_router.callback_query.filter(RoleFilter(STAFF_ROLES))

logger = logging.getLogger(__name__)
STATUS_LABELS = {
    "ru": {"new": "🟢 Новое", "in_progress": "🟡 В работе", "closed": "🔴 Закрыто"},
    "uz": {"new": "🟢 Yangi", "in_progress": "🟡 Jarayonda", "closed": "🔴 Yopilgan"},
}
TYPE_LABELS = {
    "ru": {"complaint": "📩 Жалобы", "suggestion": "💡 Предложения"},
    "uz": {"complaint": "📩 Shikoyatlar", "suggestion": "💡 Takliflar"},
}
FEEDBACK_CARD_TITLES = {
    "ru": {"complaint": "📩 <b>Жалоба</b>", "suggestion": "💡 <b>Предложение</b>"},
    "uz": {"complaint": "📩 <b>Shikoyat</b>", "suggestion": "💡 <b>Taklif</b>"},
}


def _lang(user) -> str:
    return user.language if user and user.language in {"ru", "uz"} else "ru"


async def _actor(telegram_id: int):
    return await db.get_user_by_tg_id(telegram_id)


def _main_text(user) -> str:
    lang = _lang(user)
    if has_global_staff_scope(user):
        return (
            "👨‍🏫 <b>Панель сотрудника</b>\n\nРаботайте с классами всей школы."
            if lang == "ru"
            else "👨‍🏫 <b>Xodim paneli</b>\n\nMaktabning barcha sinflari bilan ishlang."
        )
    return (
        "👨‍🏫 <b>Панель сотрудника</b>\n\n"
        "Работайте только с закреплёнными классами."
        if lang == "ru"
        else "👨‍🏫 <b>Xodim paneli</b>\n\nFaqat biriktirilgan sinflar bilan ishlang."
    )


async def show_staff_main(message: Message | CallbackQuery, user) -> None:
    lang = _lang(user)
    if isinstance(message, CallbackQuery):
        await message.message.edit_text(_main_text(user), reply_markup=get_staff_main_kb(lang), parse_mode="HTML")
    else:
        await message.answer(_main_text(user), reply_markup=get_staff_main_kb(lang), parse_mode="HTML")


async def _staff_classes(actor, active_only: bool = False):
    """Return assigned classes for a Moderator, all classes for elevated staff."""
    if has_global_staff_scope(actor):
        return await db.get_school_classes(active_only=active_only)
    return await db.get_moderator_classes(actor.id, active_only=active_only)


async def _can_access_staff_class(actor, class_id: int, active_only: bool = False) -> bool:
    if not actor:
        return False
    if has_global_staff_scope(actor):
        school_class = await db.get_class_by_id(class_id)
        return school_class is not None and (school_class.is_active or not active_only)
    return await db.is_moderator_assigned_to_class(actor.id, class_id, active_only=active_only)


async def _staff_pending_applications(actor):
    classes = await _staff_classes(actor)
    return await db.get_pending_users_for_classes([item.display_name for item in classes])


async def _staff_feedback(actor, feedback_id: int):
    if has_global_staff_scope(actor):
        return await db.get_feedback_by_id(feedback_id)
    return await db.get_feedback_for_moderator(actor.id, feedback_id)


async def _staff_feedbacks_by_status(actor, feedback_type: str, status: str):
    if has_global_staff_scope(actor):
        return await db.get_feedbacks_by_status(feedback_type, status, limit=20)
    return await db.get_feedbacks_for_moderator(actor.id, feedback_type, status)


async def _get_accessible_pending_application(actor, telegram_id: int):
    """Return a pending application only when it belongs to the actor's class."""
    applicant = await db.get_user_by_tg_id(telegram_id)
    if not applicant or applicant.status != "pending" or normalize_role(applicant.role) != UserRole.STUDENT.value:
        return None
    classes = await _staff_classes(actor)
    return applicant if any(item.display_name == applicant.class_name for item in classes) else None


def _staff_lessons_text(lessons, lang: str) -> str:
    if not lessons:
        return "На сегодня уроков пока нет." if lang == "ru" else "Bugun uchun darslar hali kiritilmagan."
    return "\n".join(
        f"{lesson.lesson_number}. {lesson.start_time.strftime('%H:%M') if lesson.start_time else '—'} — "
        f"{escape(lesson.subject)}" + (f" · {escape(lesson.room)}" if lesson.room else "")
        for lesson in lessons
    )


@staff_router.message(Command("staff", "moderator"))
async def cmd_staff(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = await _actor(message.from_user.id)
    if user:
        await show_staff_main(message, user)


@staff_router.callback_query(StaffCB.filter(F.action == "main"))
async def cb_staff_main(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user = await _actor(call.from_user.id)
    if user:
        await show_staff_main(call, user)
    await call.answer()


@staff_router.callback_query(StaffCB.filter(F.action == "ignore"))
async def cb_staff_ignore(call: CallbackQuery) -> None:
    await call.answer()


@staff_router.callback_query(StaffCB.filter(F.action == "classes"))
async def cb_staff_classes(call: CallbackQuery) -> None:
    user = await _actor(call.from_user.id)
    if not user:
        await call.answer()
        return
    lang = _lang(user)
    classes = await _staff_classes(user)
    counts = {school_class.id: await db.get_students_count_by_class(school_class.display_name) for school_class in classes}
    text = "🏫 <b>Мои классы</b>\n\nВыберите класс:" if lang == "ru" else "🏫 <b>Mening sinflarim</b>\n\nSinfni tanlang:"
    if not classes:
        text = "🏫 <b>Мои классы</b>\n\nКлассы пока не закреплены." if lang == "ru" else "🏫 <b>Mening sinflarim</b>\n\nHali sinflar biriktirilmagan."
    await call.message.edit_text(text, reply_markup=get_staff_classes_kb(classes, counts, lang), parse_mode="HTML")
    await call.answer()


@staff_router.callback_query(StaffCB.filter(F.action.in_({"schedule", "stats"})))
async def cb_staff_choose_class_action(call: CallbackQuery, callback_data: StaffCB) -> None:
    actor = await _actor(call.from_user.id)
    if not actor:
        await call.answer()
        return
    lang = _lang(actor)
    classes = await _staff_classes(actor, active_only=True)
    action = "class_schedule" if callback_data.action == "schedule" else "class_stats"
    title = "📅 <b>Расписание класса</b>\n\nВыберите класс:" if callback_data.action == "schedule" else "📊 <b>Статистика класса</b>\n\nВыберите класс:"
    if lang == "uz":
        title = "📅 <b>Sinf jadvali</b>\n\nSinfni tanlang:" if callback_data.action == "schedule" else "📊 <b>Sinf statistikasi</b>\n\nSinfni tanlang:"
    if not classes:
        title = "Sizga sinflar biriktirilmagan." if lang == "ru" else "Sizga sinflar biriktirilmagan."
    await call.message.edit_text(title, reply_markup=get_staff_class_action_kb(classes, action, lang), parse_mode="HTML")
    await call.answer()


@staff_router.callback_query(StaffCB.filter(F.action == "class_schedule"))
async def cb_staff_class_schedule(call: CallbackQuery, callback_data: StaffCB) -> None:
    try:
        class_id = int(callback_data.param or "")
    except ValueError:
        await call.answer("Некорректный класс.", show_alert=True)
        return
    actor = await _actor(call.from_user.id)
    if not actor or not await _can_access_staff_class(actor, class_id, active_only=True):
        await call.answer("Доступ к классу запрещён.", show_alert=True)
        return
    school_class = await db.get_class_by_id(class_id)
    lang = _lang(actor)
    from datetime import date
    lessons = await db.get_lessons_for_class_day(class_id, date.today().weekday())
    heading = "📅 <b>Расписание на сегодня</b>" if lang == "ru" else "📅 <b>Bugungi dars jadvali</b>"
    await call.message.edit_text(
        f"{heading}\n🏫 {school_class.display_name}\n\n{_staff_lessons_text(lessons, lang)}",
        reply_markup=get_staff_class_action_kb([school_class], "class_schedule", lang), parse_mode="HTML",
    )
    await call.answer()


@staff_router.callback_query(StaffCB.filter(F.action == "class_stats"))
async def cb_staff_class_stats(call: CallbackQuery, callback_data: StaffCB) -> None:
    try:
        class_id = int(callback_data.param or "")
    except ValueError:
        await call.answer("Некорректный класс.", show_alert=True)
        return
    actor = await _actor(call.from_user.id)
    if not actor or not await _can_access_staff_class(actor, class_id, active_only=True):
        await call.answer("Доступ к классу запрещён.", show_alert=True)
        return
    school_class = await db.get_class_by_id(class_id)
    lang = _lang(actor)
    students = await db.get_students_count_by_class(school_class.display_name)
    pending = len(await db.get_pending_users_for_classes([school_class.display_name]))
    text = (
        f"📊 <b>Статистика {school_class.display_name}</b>\n\nАктивных учеников: <b>{students}</b>\nЗаявок на рассмотрении: <b>{pending}</b>"
        if lang == "ru" else
        f"📊 <b>{school_class.display_name} statistikasi</b>\n\nFaol o'quvchilar: <b>{students}</b>\nKo'rib chiqilayotgan arizalar: <b>{pending}</b>"
    )
    await call.message.edit_text(text, reply_markup=get_staff_class_action_kb([school_class], "class_stats", lang), parse_mode="HTML")
    await call.answer()


@staff_router.callback_query(StaffCB.filter(F.action == "applications"))
async def cb_staff_applications(call: CallbackQuery) -> None:
    actor = await _actor(call.from_user.id)
    if not actor:
        await call.answer()
        return
    lang = _lang(actor)
    applicants = await _staff_pending_applications(actor)
    if applicants:
        text = "📋 <b>Заявки классов</b>\n\nВыберите заявку:" if lang == "ru" else "📋 <b>Sinf arizalari</b>\n\nArizani tanlang:"
    else:
        text = "📋 <b>Заявки классов</b>\n\nНовых заявок нет." if lang == "ru" else "📋 <b>Sinf arizalari</b>\n\nYangi arizalar yo'q."
    await call.message.edit_text(text, reply_markup=get_staff_applications_kb(applicants, lang), parse_mode="HTML")
    await call.answer()


@staff_router.callback_query(StaffCB.filter(F.action == "application_view"))
async def cb_staff_application_view(call: CallbackQuery, callback_data: StaffCB) -> None:
    try:
        telegram_id = int(callback_data.param)
    except ValueError:
        await call.answer("Некорректная заявка.", show_alert=True)
        return
    actor = await _actor(call.from_user.id)
    applicant = await _get_accessible_pending_application(actor, telegram_id) if actor else None
    if not applicant:
        await call.answer("Заявка недоступна или уже обработана.", show_alert=True)
        return
    lang = _lang(actor)
    language = "Русский" if applicant.language == "ru" else "O'zbek"
    text = (
        "📋 <b>Заявка ученика</b>\n\n"
        f"Имя: {escape(applicant.first_name)}\nФамилия: {escape(applicant.last_name)}\n"
        f"Класс: {escape(applicant.class_name)}\nЯзык: {language}"
        if lang == "ru" else
        "📋 <b>O'quvchi arizasi</b>\n\n"
        f"Ism: {escape(applicant.first_name)}\nFamiliya: {escape(applicant.last_name)}\n"
        f"Sinf: {escape(applicant.class_name)}\nTil: {language}"
    )
    await call.message.edit_text(text, reply_markup=get_staff_application_card_kb(applicant, lang), parse_mode="HTML")
    await call.answer()


@staff_router.callback_query(StaffCB.filter(F.action.in_({"application_accept", "application_reject"})))
async def cb_staff_application_decision(call: CallbackQuery, callback_data: StaffCB, bot: Bot) -> None:
    try:
        telegram_id = int(callback_data.param)
    except ValueError:
        await call.answer("Некорректная заявка.", show_alert=True)
        return
    actor = await _actor(call.from_user.id)
    applicant = await _get_accessible_pending_application(actor, telegram_id) if actor else None
    if not applicant:
        await call.answer("Заявка недоступна или уже обработана.", show_alert=True)
        return
    accepted = callback_data.action == "application_accept"
    applicant = await db.review_registration_request(telegram_id, actor.id, accepted)
    if not applicant:
        await call.answer("Заявка уже обработана.", show_alert=True)
        return
    applicant_texts = TEXTS.get(applicant.language, TEXTS["ru"])
    try:
        if accepted:
            await bot.send_message(
                telegram_id, applicant_texts["registration_approved"],
                reply_markup=get_main_menu_kb(applicant.language),
            )
        else:
            await bot.send_message(telegram_id, applicant_texts["registration_rejected"])
    except (TelegramForbiddenError, TelegramBadRequest) as error:
        logger.warning("Could not notify class applicant %s: %s", telegram_id, type(error).__name__)
    except Exception:
        logger.exception("Unexpected applicant notification failure for %s", telegram_id)
    lang = _lang(actor)
    result = "✅ Заявка принята." if accepted and lang == "ru" else (
        "❌ Заявка отклонена." if lang == "ru" else ("✅ Ariza qabul qilindi." if accepted else "❌ Ariza rad etildi.")
    )
    remaining = await _staff_pending_applications(actor)
    await call.message.edit_text(result, reply_markup=get_staff_applications_kb(remaining, lang))
    await call.answer()


@staff_router.callback_query(StaffCB.filter(F.action == "class_students"))
async def cb_staff_class_students(call: CallbackQuery, callback_data: StaffCB) -> None:
    try:
        class_id_raw, requested_page_raw = callback_data.param.split("|", 1)
        class_id, requested_page = int(class_id_raw), int(requested_page_raw)
    except (AttributeError, ValueError):
        await call.answer("Некорректный класс.", show_alert=True)
        return
    user = await _actor(call.from_user.id)
    if not await _can_access_staff_class(user, class_id):
        logger.warning("Staff user %s attempted unavailable class %s", call.from_user.id, class_id)
        await call.answer("Доступ к классу запрещён.", show_alert=True)
        return
    school_class = await db.get_class_by_id(class_id)
    if not school_class:
        await call.answer("Класс не найден.", show_alert=True)
        return
    students, total_pages = await db.get_students_by_class_paginated(school_class.display_name, requested_page)
    page = min(max(requested_page, 1), total_pages)
    if page != requested_page:
        students, total_pages = await db.get_students_by_class_paginated(school_class.display_name, page)
    lang = _lang(user)
    title = "Ученики" if lang == "ru" else "O'quvchilar"
    empty = "В этом классе пока нет активных учеников." if lang == "ru" else "Bu sinfda hali faol o'quvchilar yo'q."
    text = f"🏫 <b>{escape(school_class.display_name)}</b>\n\n<b>{title}:</b>"
    if not students:
        text += f"\n\n{empty}"
    await call.message.edit_text(text, reply_markup=get_staff_students_kb(students, class_id, page, total_pages, lang), parse_mode="HTML")
    await call.answer()


@staff_router.callback_query(StaffCB.filter(F.action == "student"))
async def cb_staff_student(call: CallbackQuery, callback_data: StaffCB) -> None:
    try:
        tg_id_raw, class_id_raw, page_raw = callback_data.param.split("|", 2)
        telegram_id, class_id, page = int(tg_id_raw), int(class_id_raw), int(page_raw)
    except (AttributeError, ValueError):
        await call.answer("Некорректный пользователь.", show_alert=True)
        return
    actor = await _actor(call.from_user.id)
    school_class = await db.get_class_by_id(class_id)
    student = await db.get_user_by_tg_id(telegram_id)
    if (
        not actor or not school_class or not student
        or not await _can_access_staff_class(actor, class_id)
        or student.class_name != school_class.display_name
        or normalize_role(student.role) != UserRole.STUDENT.value
    ):
        logger.warning("Staff user %s attempted unavailable student %s", call.from_user.id, telegram_id)
        await call.answer("Доступ к карточке запрещён.", show_alert=True)
        return
    lang = _lang(actor)
    date = student.created_at.strftime("%d.%m.%Y") if student.created_at else "—"
    student_language = "Русский" if student.language == "ru" else "O'zbek"
    student_status = {
        "active": "Активен" if lang == "ru" else "Faol",
        "pending": "Ожидает" if lang == "ru" else "Kutilmoqda",
        "rejected": "Отклонён" if lang == "ru" else "Rad etilgan",
    }.get(student.status, student.status)
    text = (
        "👤 <b>Карточка ученика</b>\n\n"
        f"Имя: {escape(student.first_name)}\nФамилия: {escape(student.last_name)}\n"
        f"Класс: {escape(student.class_name)}\nКод: <code>{escape(student.user_code or '—')}</code>\nЯзык: {student_language}\nСтатус: {student_status}\nВ боте с: {date}\n\n<i>Только просмотр.</i>"
        if lang == "ru" else
        "👤 <b>O'quvchi kartasi</b>\n\n"
        f"Ism: {escape(student.first_name)}\nFamiliya: {escape(student.last_name)}\n"
        f"Sinf: {escape(student.class_name)}\nKod: <code>{escape(student.user_code or '—')}</code>\nTil: {student_language}\nHolat: {student_status}\nBotda: {date}\n\n<i>Faqat ko'rish uchun.</i>"
    )
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    back = "⬅️ Ortga" if lang == "uz" else "⬅️ Назад"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=back, callback_data=StaffCB(action="class_students", param=f"{class_id}|{page}").pack())
    ]])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@staff_router.callback_query(StaffCB.filter(F.action == "feedback_kind"))
async def cb_staff_feedback_kind(call: CallbackQuery, callback_data: StaffCB) -> None:
    feedback_type = callback_data.param
    if feedback_type != "suggestion":
        await call.answer("Сотрудникам доступны только предложения своих классов.", show_alert=True)
        return
    user = await _actor(call.from_user.id)
    if not user:
        await call.answer()
        return
    lang = _lang(user)
    intro = "Выберите статус:" if lang == "ru" else "Holatni tanlang:"
    await call.message.edit_text(f"{TYPE_LABELS[lang][feedback_type]}\n\n{intro}", reply_markup=get_staff_feedback_status_kb(feedback_type, lang), parse_mode="HTML")
    await call.answer()


@staff_router.callback_query(StaffCB.filter(F.action == "feedback_status"))
async def cb_staff_feedback_status(call: CallbackQuery, callback_data: StaffCB) -> None:
    try:
        feedback_type, status = callback_data.param.split("|", 1)
    except (AttributeError, ValueError):
        await call.answer("Некорректный фильтр.", show_alert=True)
        return
    if feedback_type != "suggestion" or status not in {"new", "in_progress", "closed"}:
        await call.answer("Некорректный фильтр.", show_alert=True)
        return
    user = await _actor(call.from_user.id)
    if not user:
        await call.answer()
        return
    lang = _lang(user)
    feedbacks = await _staff_feedbacks_by_status(user, feedback_type, status)
    empty = "В этой категории обращений нет." if lang == "ru" else "Bu bo'limda murojaatlar yo'q."
    prompt = "Выберите обращение:" if feedbacks and lang == "ru" else ("Murojaatni tanlang:" if feedbacks else empty)
    await call.message.edit_text(
        f"{TYPE_LABELS[lang][feedback_type]}\n\n{STATUS_LABELS[lang][status]}\n\n{prompt}",
        reply_markup=get_staff_feedback_list_kb(feedbacks, feedback_type, lang), parse_mode="HTML",
    )
    await call.answer()


async def show_staff_feedback(call: CallbackQuery, actor, feedback_id: int) -> bool:
    feedback = await _staff_feedback(actor, feedback_id)
    if not feedback or not feedback.user or feedback.type != "suggestion":
        logger.warning("Staff user %s attempted unavailable feedback %s", actor.telegram_id, feedback_id)
        await call.answer("Доступ к обращению запрещён.", show_alert=True)
        return False
    lang = _lang(actor)
    date = feedback.created_at.strftime("%d.%m.%Y %H:%M") if feedback.created_at else "—"
    text = (
        f"{FEEDBACK_CARD_TITLES[lang][feedback.type]} #{feedback.id}\n\n"
        f"{'Класс' if lang == 'ru' else 'Sinf'}: {escape(feedback.user.class_name)}\n"
        f"{'Дата' if lang == 'ru' else 'Sana'}: {date}\n"
        f"{'Статус' if lang == 'ru' else 'Holat'}: {STATUS_LABELS[lang].get(feedback.status, feedback.status)}\n\n"
        f"<b>{'Текст' if lang == 'ru' else 'Matn'}:</b>\n{escape(feedback.text)}"
    )
    await call.message.edit_text(text, reply_markup=get_staff_feedback_card_kb(feedback, lang), parse_mode="HTML")
    await call.answer()
    return True


@staff_router.callback_query(StaffCB.filter(F.action == "feedback"))
async def cb_staff_feedback(call: CallbackQuery, callback_data: StaffCB) -> None:
    try:
        feedback_id = int(callback_data.param)
    except ValueError:
        await call.answer("Некорректное обращение.", show_alert=True)
        return
    actor = await _actor(call.from_user.id)
    if actor:
        await show_staff_feedback(call, actor, feedback_id)
    else:
        await call.answer()


@staff_router.callback_query(StaffCB.filter(F.action == "feedback_status_set"))
async def cb_staff_set_feedback_status(call: CallbackQuery, callback_data: StaffCB) -> None:
    try:
        feedback_id_raw, status = callback_data.param.split("|", 1)
        feedback_id = int(feedback_id_raw)
    except (AttributeError, ValueError):
        await call.answer("Некорректные данные.", show_alert=True)
        return
    if status not in {"in_progress", "closed"}:
        await call.answer("Некорректный статус.", show_alert=True)
        return
    actor = await _actor(call.from_user.id)
    feedback = await _staff_feedback(actor, feedback_id) if actor else None
    if not feedback or feedback.type != "suggestion":
        await call.answer("Доступ к обращению запрещён.", show_alert=True)
        return
    await db.update_feedback_status(feedback_id, status)
    await show_staff_feedback(call, actor, feedback_id)


@staff_router.callback_query(StaffCB.filter(F.action == "feedback_reply"))
async def cb_staff_reply_start(call: CallbackQuery, callback_data: StaffCB, state: FSMContext) -> None:
    try:
        feedback_id = int(callback_data.param)
    except ValueError:
        await call.answer("Некорректное обращение.", show_alert=True)
        return
    actor = await _actor(call.from_user.id)
    feedback = await _staff_feedback(actor, feedback_id) if actor else None
    if not feedback or not feedback.user or feedback.type != "suggestion":
        await call.answer("Доступ к обращению запрещён.", show_alert=True)
        return
    lang = _lang(actor)
    await state.clear()
    await state.update_data(feedback_id=feedback.id, recipient_id=feedback.user.telegram_id, language=lang)
    await state.set_state(StaffReplyState.waiting_for_text)
    prompt = f"✉️ <b>Ответ на обращение №{feedback.id}</b>\n\nВведите текст ответа:" if lang == "ru" else f"✉️ <b>#{feedback.id} murojaatiga javob</b>\n\nJavob matnini kiriting:"
    await call.message.edit_text(prompt, reply_markup=get_staff_cancel_kb("reply", lang), parse_mode="HTML")
    await call.answer()


@staff_router.message(StaffReplyState.waiting_for_text)
async def staff_reply_text(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    data = await state.get_data()
    lang = data.get("language", "ru")
    if not text:
        await message.answer("⚠️ Ответ не может быть пустым." if lang == "ru" else "⚠️ Javob bo'sh bo'lishi mumkin emas.")
        return
    await state.update_data(text=text)
    await state.set_state(StaffReplyState.waiting_for_confirm)
    preview = "<b>Предпросмотр:</b>" if lang == "ru" else "<b>Ko'rib chiqish:</b>"
    await message.answer(f"{preview}\n\n{escape(text)}", reply_markup=get_staff_confirm_kb("reply", lang), parse_mode="HTML")


@staff_router.callback_query(StaffCB.filter(F.action == "reply_cancel"))
async def cb_staff_reply_cancel(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    actor = await _actor(call.from_user.id)
    if actor:
        await show_staff_main(call, actor)
    await call.answer()


@staff_router.callback_query(StaffCB.filter(F.action == "reply_send"))
async def cb_staff_reply_send(call: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    feedback_id = data.get("feedback_id")
    recipient_id = data.get("recipient_id")
    reply_text = data.get("text")
    actor = await _actor(call.from_user.id)
    if not actor or not isinstance(feedback_id, int) or not isinstance(recipient_id, int) or not reply_text:
        await state.clear()
        await call.answer("Сессия ответа устарела.", show_alert=True)
        return
    feedback = await _staff_feedback(actor, feedback_id)
    if (
        not feedback
        or not feedback.user
        or feedback.type != "suggestion"
        or feedback.user.telegram_id != recipient_id
    ):
        await state.clear()
        await call.answer("Доступ к обращению запрещён.", show_alert=True)
        return
    lang = _lang(actor)
    content = (
        f"📨 <b>Ответ школы</b>\n\nПо вашему обращению #{feedback_id}\n\n<b>Ответ:</b>\n{escape(reply_text)}"
        if lang == "ru" else f"📨 <b>Maktab javobi</b>\n\n#{feedback_id} murojaatingiz bo'yicha\n\n<b>Javob:</b>\n{escape(reply_text)}"
    )
    try:
        await bot.send_message(recipient_id, content, parse_mode="HTML")
    except (TelegramForbiddenError, TelegramBadRequest) as exc:
        logger.warning("Could not deliver feedback reply %s: %s", feedback_id, type(exc).__name__)
        await call.message.answer("⚠️ Не удалось доставить сообщение пользователю." if lang == "ru" else "⚠️ Foydalanuvchiga xabar yetkazilmadi.")
    else:
        await call.message.answer("✅ Ответ отправлен." if lang == "ru" else "✅ Javob yuborildi.")
    await state.clear()
    await show_staff_main(call, actor)
    await call.answer()


@staff_router.callback_query(StaffCB.filter(F.action == "announcement"))
async def cb_staff_announcement(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    actor = await _actor(call.from_user.id)
    if not actor:
        await call.answer()
        return
    lang = _lang(actor)
    classes = await _staff_classes(actor, active_only=True)
    text = "📣 <b>Объявление классу</b>\n\nВыберите класс:" if lang == "ru" else "📣 <b>Sinfga e'lon</b>\n\nSinfni tanlang:"
    if not classes:
        text = "📣 <b>Объявление классу</b>\n\nНет активных закреплённых классов." if lang == "ru" else "📣 <b>Sinfga e'lon</b>\n\nFaol biriktirilgan sinflar yo'q."
    await call.message.edit_text(text, reply_markup=get_staff_announcement_classes_kb(classes, lang), parse_mode="HTML")
    await call.answer()


@staff_router.callback_query(StaffCB.filter(F.action == "announcement_class"))
async def cb_staff_announcement_class(call: CallbackQuery, callback_data: StaffCB, state: FSMContext) -> None:
    try:
        class_id = int(callback_data.param)
    except ValueError:
        await call.answer("Некорректный класс.", show_alert=True)
        return
    actor = await _actor(call.from_user.id)
    school_class = await db.get_class_by_id(class_id)
    if not actor or not school_class or not await _can_access_staff_class(actor, class_id, active_only=True):
        await call.answer("Доступ к классу запрещён.", show_alert=True)
        return
    lang = _lang(actor)
    await state.update_data(announcement_class_id=class_id, language=lang)
    await state.set_state(StaffAnnouncementState.waiting_for_text)
    prompt = f"📣 <b>{escape(school_class.display_name)}</b>\n\nВведите текст объявления:" if lang == "ru" else f"📣 <b>{escape(school_class.display_name)}</b>\n\nE'lon matnini kiriting:"
    await call.message.edit_text(
        prompt, reply_markup=get_staff_cancel_kb("announcement", lang), parse_mode="HTML"
    )
    await call.answer()


@staff_router.message(StaffAnnouncementState.waiting_for_text)
async def staff_announcement_text(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    data = await state.get_data()
    lang = data.get("language", "ru")
    if not text:
        await message.answer("⚠️ Текст объявления не может быть пустым." if lang == "ru" else "⚠️ E'lon matni bo'sh bo'lishi mumkin emas.")
        return
    await state.update_data(announcement_text=text)
    await state.set_state(StaffAnnouncementState.waiting_for_confirm)
    prefix = "📣 <b>Предпросмотр объявления</b>" if lang == "ru" else "📣 <b>E'lonni ko'rib chiqish</b>"
    await message.answer(f"{prefix}\n\n{escape(text)}", reply_markup=get_staff_confirm_kb("announcement", lang), parse_mode="HTML")


@staff_router.callback_query(StaffCB.filter(F.action == "announcement_cancel"))
async def cb_staff_announcement_cancel(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    actor = await _actor(call.from_user.id)
    if actor:
        await show_staff_main(call, actor)
    await call.answer()


@staff_router.callback_query(StaffCB.filter(F.action == "announcement_send"))
async def cb_staff_announcement_send(call: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    class_id = data.get("announcement_class_id")
    announcement_text = data.get("announcement_text")
    actor = await _actor(call.from_user.id)
    if not actor or not isinstance(class_id, int) or not announcement_text:
        await state.clear()
        await call.answer("Сессия объявления устарела.", show_alert=True)
        return
    school_class = await db.get_class_by_id(class_id)
    if not school_class or not await _can_access_staff_class(actor, class_id, active_only=True):
        await state.clear()
        await call.answer("Доступ к классу запрещён.", show_alert=True)
        return
    # Persist the announcement before delivery so students can read it later
    # in “My class”, even if their Telegram delivery was missed.
    await db.create_class_announcement(class_id, actor.id, announcement_text)
    sent = failed = 0
    announcement_header = "Объявление класса" if _lang(actor) == "ru" else "Sinf e'loni"
    for student in await db.get_active_students_by_class(school_class.display_name):
        try:
            await bot.send_message(
                student.telegram_id,
                f"📣 <b>{announcement_header}</b>\n\n{escape(announcement_text)}",
                parse_mode="HTML",
            )
        except (TelegramForbiddenError, TelegramBadRequest) as exc:
            failed += 1
            logger.warning("Could not deliver class announcement to %s: %s", student.telegram_id, type(exc).__name__)
        else:
            sent += 1
    await state.clear()
    lang = _lang(actor)
    result = f"✅ Объявление отправлено.\n\nПолучили: {sent}\nОшибок: {failed}" if lang == "ru" else f"✅ E'lon yuborildi.\n\nQabul qildi: {sent}\nXatolar: {failed}"
    await call.message.answer(result)
    await show_staff_main(call, actor)
    await call.answer()


@staff_router.callback_query(StaffCB.filter(F.action == "profile"))
async def cb_staff_profile(call: CallbackQuery) -> None:
    actor = await _actor(call.from_user.id)
    if not actor:
        await call.answer()
        return
    lang = _lang(actor)
    classes = await _staff_classes(actor)
    class_list = ", ".join(escape(item.display_name) for item in classes) or ("не назначены" if lang == "ru" else "biriktirilmagan")
    language = "Русский" if actor.language == "ru" else "O'zbek"
    role_label = {
        "moderator": "Сотрудник школы" if lang == "ru" else "Maktab xodimi",
        "admin": "Администратор" if lang == "ru" else "Administrator",
        "superadmin": "SuperAdmin",
    }.get(normalize_role(actor.role), actor.role)
    text = (
        "👨‍🏫 <b>Профиль сотрудника</b>\n\n"
        f"Имя: {escape(actor.first_name)} {escape(actor.last_name)}\nРоль: {role_label}\nЯзык: {language}\nЗакреплённые классы: {class_list}"
        if lang == "ru" else
        "👨‍🏫 <b>Xodim profili</b>\n\n"
        f"Ism: {escape(actor.first_name)} {escape(actor.last_name)}\nRol: {role_label}\nTil: {language}\nBiriktirilgan sinflar: {class_list}"
    )
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⬅️ Назад" if lang == "ru" else "⬅️ Ortga", callback_data=StaffCB(action="main").pack())
    ]])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@staff_router.callback_query(StaffCB.filter(F.action == "help"))
async def cb_staff_help(call: CallbackQuery) -> None:
    actor = await _actor(call.from_user.id)
    if not actor:
        await call.answer()
        return
    lang = _lang(actor)
    text = (
        "❓ <b>Справка сотрудника</b>\n\n🏫 «Мои классы» — просмотр закреплённых классов и учеников.\n📋 «Заявки классов» — подтверждение учеников своего класса.\n💡 «Предложения» — работа только с предложениями закреплённых классов.\n📣 Объявления получают только активные ученики выбранного класса."
        if lang == "ru" else
        "❓ <b>Xodim yordami</b>\n\n🏫 «Mening sinflarim» — biriktirilgan sinflar va o'quvchilar.\n📋 «Sinf arizalari» — o'z sinfidagi o'quvchilar arizalari.\n💡 «Takliflar» — faqat biriktirilgan sinflar takliflari.\n📣 E'lon faqat tanlangan sinfning faol o'quvchilariga yuboriladi."
    )
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⬅️ Назад" if lang == "ru" else "⬅️ Ortga", callback_data=StaffCB(action="main").pack())
    ]])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()
