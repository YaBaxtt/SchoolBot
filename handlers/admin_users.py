from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery

from database import requests as db
from filters.roles import ADMIN_ROLES, RoleFilter, normalize_role
from permissions import ASSIGNABLE_ROLES, UserRole, can_manage_moderator_assignments, can_manage_roles
from keyboards.admin_kb import (
    AdminCB,
    get_user_card_kb,
    get_user_change_classes_kb,
    get_user_change_grades_kb,
    get_user_classes_kb,
    get_user_grades_kb,
    get_moderator_classes_kb,
    get_user_role_kb,
    get_users_list_kb,
)

admin_users_router = Router()
admin_users_router.callback_query.filter(RoleFilter(ADMIN_ROLES))


@admin_users_router.callback_query(AdminCB.filter(F.action == "ignore"))
async def cb_admin_users_ignore(call: CallbackQuery) -> None:
    await call.answer()


@admin_users_router.callback_query(AdminCB.filter(F.action == "users"))
async def cb_admin_users(call: CallbackQuery) -> None:
    grades = await db.get_user_grades()
    text = "👥 <b>Пользователи</b>\n\nВыберите параллель:"
    if not grades:
        text = "👥 <b>Пользователи</b>\n\nПользователей и классов пока нет."
    await call.message.edit_text(text, reply_markup=get_user_grades_kb(grades), parse_mode="HTML")
    await call.answer()


@admin_users_router.callback_query(AdminCB.filter(F.action == "users_grade"))
async def cb_users_grade(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        grade = int(callback_data.param)
    except ValueError:
        await call.answer("Некорректная параллель.", show_alert=True)
        return
    classes = await db.get_user_class_summaries(grade)
    grade_title = "Без параллели" if grade == 0 else f"{grade} класс"
    text = f"🎓 <b>{grade_title}</b>\n\nВыберите класс:"
    if not classes:
        text = f"🎓 <b>{grade_title}</b>\n\nКлассы пока не настроены."
    await call.message.edit_text(text, reply_markup=get_user_classes_kb(classes, grade), parse_mode="HTML")
    await call.answer()


@admin_users_router.callback_query(AdminCB.filter(F.action == "users_class"))
async def cb_users_class(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        class_name, page_raw = callback_data.param.rsplit("|", 1)
        requested_page = int(page_raw)
    except (TypeError, ValueError):
        await call.answer("Некорректный класс.", show_alert=True)
        return
    users, total_pages = await db.get_users_by_class_paginated(class_name, requested_page)
    page = min(max(requested_page, 1), total_pages)
    if page != requested_page:
        users, total_pages = await db.get_users_by_class_paginated(class_name, page)
    text = f"🏫 <b>{escape(class_name)}</b>\n\nВыберите ученика:"
    if not users:
        text = f"🏫 <b>{escape(class_name)}</b>\n\nВ этом классе пока нет учеников."
    await call.message.edit_text(
        text,
        reply_markup=get_users_list_kb(users, class_name, page, total_pages),
        parse_mode="HTML",
    )
    await call.answer()


def _status_name(status: str) -> str:
    return {"active": "✅ Active", "pending": "⏳ Ожидает подтверждения", "rejected": "❌ Отклонена"}.get(status, status)


def _role_name(role: str) -> str:
    return {"student": "Student", "admin": "Admin", "superadmin": "SuperAdmin", "moderator": "Moderator"}.get(role, role)


async def show_user_card(call: CallbackQuery, telegram_id: int) -> None:
    user = await db.get_user_by_tg_id(telegram_id)
    actor = await db.get_user_by_tg_id(call.from_user.id)
    if not user:
        await call.answer("Пользователь не найден.", show_alert=True)
        return
    date = user.created_at.strftime("%d.%m.%Y") if user.created_at else "—"
    language = "Русский" if user.language == "ru" else "O'zbekcha"
    text = (
        "👤 <b>Карточка пользователя</b>\n\n"
        f"Имя: {escape(user.first_name)}\n"
        f"Фамилия: {escape(user.last_name)}\n"
        f"Класс: {escape(user.class_name)}\n"
        f"Язык: {language}\n"
        f"Роль: {_role_name(user.role)}\n"
        f"Статус: {_status_name(user.status)}\n"
        f"Дата регистрации: {date}\n"
        f"User Code: <code>{escape(user.user_code or '—')}</code>"
    )
    await call.message.edit_text(
        text,
        reply_markup=get_user_card_kb(
            user.telegram_id,
            user.class_name,
            user.role,
            can_manage_roles=can_manage_roles(actor),
            can_manage_moderator_assignments=can_manage_moderator_assignments(actor),
        ),
        parse_mode="HTML",
    )
    await call.answer()


@admin_users_router.callback_query(AdminCB.filter(F.action == "user_select"))
async def cb_user_select(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        telegram_id = int(callback_data.param)
    except ValueError:
        await call.answer("Некорректный пользователь.", show_alert=True)
        return
    await show_user_card(call, telegram_id)


@admin_users_router.callback_query(AdminCB.filter(F.action == "user_change_class"))
async def cb_user_change_class(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        telegram_id = int(callback_data.param)
    except ValueError:
        await call.answer("Некорректный пользователь.", show_alert=True)
        return
    grades = await db.get_active_class_grades()
    if not grades:
        await call.answer("Нет активных классов для перевода.", show_alert=True)
        return
    await call.message.edit_text(
        "🎓 <b>Изменение класса</b>\n\nВыберите параллель:",
        reply_markup=get_user_change_grades_kb(telegram_id, grades),
        parse_mode="HTML",
    )
    await call.answer()


@admin_users_router.callback_query(AdminCB.filter(F.action == "user_class_grade"))
async def cb_user_class_grade(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        telegram_id_raw, grade_raw = callback_data.param.split("|", 1)
        telegram_id, grade = int(telegram_id_raw), int(grade_raw)
    except (AttributeError, ValueError):
        await call.answer("Некорректные данные.", show_alert=True)
        return
    classes = await db.get_active_classes_by_grade(grade)
    if not classes:
        await call.answer("В этой параллели нет активных классов.", show_alert=True)
        return
    await call.message.edit_text(
        f"🏫 <b>{grade} класс</b>\n\nВыберите класс:",
        reply_markup=get_user_change_classes_kb(telegram_id, classes),
        parse_mode="HTML",
    )
    await call.answer()


@admin_users_router.callback_query(AdminCB.filter(F.action == "user_class_select"))
async def cb_user_class_select(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        telegram_id_raw, class_id_raw = callback_data.param.split("|", 1)
        telegram_id, class_id = int(telegram_id_raw), int(class_id_raw)
    except (AttributeError, ValueError):
        await call.answer("Некорректные данные.", show_alert=True)
        return
    user = await db.get_user_by_tg_id(telegram_id)
    school_class = await db.get_class_by_id(class_id)
    if not user or not school_class or not school_class.is_active:
        await call.answer("Пользователь или класс не найден.", show_alert=True)
        return
    old_class = user.class_name
    actor = await db.get_user_by_tg_id(call.from_user.id)
    await db.update_user_profile(telegram_id, class_name=school_class.display_name)
    await call.message.edit_text(
        f"✅ Класс пользователя изменён:\n{escape(old_class)} → <b>{escape(school_class.display_name)}</b>",
        reply_markup=get_user_card_kb(
            telegram_id,
            school_class.display_name,
            user.role,
            can_manage_roles=can_manage_roles(actor),
            can_manage_moderator_assignments=can_manage_moderator_assignments(actor),
        ),
        parse_mode="HTML",
    )
    await call.answer()


@admin_users_router.callback_query(AdminCB.filter(F.action == "user_change_role"))
async def cb_user_change_role(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        telegram_id = int(callback_data.param)
    except ValueError:
        await call.answer("Некорректный пользователь.", show_alert=True)
        return
    actor = await db.get_user_by_tg_id(call.from_user.id)
    user = await db.get_user_by_tg_id(telegram_id)
    if not user:
        await call.answer("Пользователь не найден.", show_alert=True)
        return
    if not can_manage_roles(actor):
        await call.answer("Управление ролями доступно только SuperAdmin.", show_alert=True)
        return
    await call.message.edit_text(
        "🛡 <b>Изменение роли</b>\n\nВыберите новую роль:",
        reply_markup=get_user_role_kb(telegram_id, user.role),
        parse_mode="HTML",
    )
    await call.answer()


@admin_users_router.callback_query(AdminCB.filter(F.action == "set_role"))
async def cb_set_role(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        telegram_id_raw, new_role = callback_data.param.split("|", 1)
        telegram_id = int(telegram_id_raw)
    except (AttributeError, ValueError):
        await call.answer("Ошибка данных роли.", show_alert=True)
        return
    actor = await db.get_user_by_tg_id(call.from_user.id)
    target = await db.get_user_by_tg_id(telegram_id)
    if not actor or not target or new_role not in ASSIGNABLE_ROLES:
        await call.answer("Невозможно изменить роль.", show_alert=True)
        return
    if not can_manage_roles(actor):
        await call.answer("Управление ролями доступно только SuperAdmin.", show_alert=True)
        return
    if normalize_role(target.role) == UserRole.SUPERADMIN.value:
        await call.answer("Нельзя изменять роль SuperAdmin через эту кнопку.", show_alert=True)
        return
    await db.update_user_role(telegram_id, new_role)
    await show_user_card(call, telegram_id)


async def _show_moderator_classes(call: CallbackQuery, moderator_tg_id: int) -> None:
    moderator = await db.get_user_by_tg_id(moderator_tg_id)
    if not moderator or normalize_role(moderator.role) != UserRole.MODERATOR.value:
        await call.answer("Пользователь больше не является Moderator.", show_alert=True)
        return
    classes = await db.get_school_classes()
    assigned = await db.get_moderator_classes(moderator.id)
    assigned_ids = {school_class.id for school_class in assigned}
    listed = ", ".join(escape(school_class.display_name) for school_class in assigned) or "не назначены"
    text = (
        f"👨‍🏫 <b>Классы модератора</b>\n\n"
        f"{escape(moderator.first_name)} {escape(moderator.last_name)}\n"
        f"Закреплено: {listed}\n\n"
        "Нажмите класс, чтобы добавить или убрать закрепление."
    )
    await call.message.edit_text(
        text,
        reply_markup=get_moderator_classes_kb(moderator_tg_id, classes, assigned_ids),
        parse_mode="HTML",
    )
    await call.answer()


@admin_users_router.callback_query(AdminCB.filter(F.action == "moderator_classes"))
async def cb_moderator_classes(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        moderator_tg_id = int(callback_data.param)
    except ValueError:
        await call.answer("Некорректный пользователь.", show_alert=True)
        return
    actor = await db.get_user_by_tg_id(call.from_user.id)
    if not can_manage_moderator_assignments(actor):
        await call.answer("Управление закреплениями доступно только SuperAdmin.", show_alert=True)
        return
    await _show_moderator_classes(call, moderator_tg_id)


async def _change_moderator_class(call: CallbackQuery, raw_param: str, add: bool) -> None:
    try:
        moderator_tg_raw, class_id_raw = raw_param.split("|", 1)
        moderator_tg_id, class_id = int(moderator_tg_raw), int(class_id_raw)
    except (AttributeError, ValueError):
        await call.answer("Некорректные данные.", show_alert=True)
        return
    actor = await db.get_user_by_tg_id(call.from_user.id)
    if not can_manage_moderator_assignments(actor):
        await call.answer("Управление закреплениями доступно только SuperAdmin.", show_alert=True)
        return
    moderator = await db.get_user_by_tg_id(moderator_tg_id)
    school_class = await db.get_class_by_id(class_id)
    if not moderator or normalize_role(moderator.role) != UserRole.MODERATOR.value or not school_class:
        await call.answer("Модератор или класс не найден.", show_alert=True)
        return
    if add:
        await db.assign_moderator_class(moderator.id, class_id)
    else:
        await db.remove_moderator_class(moderator.id, class_id)
    await _show_moderator_classes(call, moderator_tg_id)


@admin_users_router.callback_query(AdminCB.filter(F.action == "moderator_class_add"))
async def cb_moderator_class_add(call: CallbackQuery, callback_data: AdminCB) -> None:
    await _change_moderator_class(call, callback_data.param, add=True)


@admin_users_router.callback_query(AdminCB.filter(F.action == "moderator_class_remove"))
async def cb_moderator_class_remove(call: CallbackQuery, callback_data: AdminCB) -> None:
    await _change_moderator_class(call, callback_data.param, add=False)
