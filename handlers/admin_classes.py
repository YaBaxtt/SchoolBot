import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import IntegrityError

from database import requests as db
from filters.roles import ADMIN_ROLES, RoleFilter
from permissions import UserRole, can_access_staff, can_manage_classes, normalize_role
from keyboards.admin_kb import (
    AdminCB,
    get_class_curator_confirm_kb,
    get_class_create_confirm_kb,
    get_class_creation_cancel_kb,
    get_class_delete_confirm_kb,
    get_class_detail_kb,
    get_classes_list_kb,
    get_classes_menu_kb,
    get_grade_choice_kb,
)
from states import AddSchoolClassState, ClassCuratorState

admin_classes_router = Router()
admin_classes_router.callback_query.filter(RoleFilter(ADMIN_ROLES))
admin_classes_router.message.filter(RoleFilter(ADMIN_ROLES))

logger = logging.getLogger(__name__)


async def show_classes_menu(message: Message | CallbackQuery) -> None:
    text = (
        "🏫 <b>Классы школы</b>\n\n"
        "Добавляйте только реальные классы школы и отключайте классы, которые больше не принимают учеников."
    )
    if isinstance(message, CallbackQuery):
        await message.message.edit_text(text, reply_markup=get_classes_menu_kb(), parse_mode="HTML")
        await message.answer()
    else:
        await message.answer(text, reply_markup=get_classes_menu_kb(), parse_mode="HTML")


@admin_classes_router.callback_query(AdminCB.filter(F.action == "classes"))
async def cb_classes(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show_classes_menu(call)


@admin_classes_router.callback_query(AdminCB.filter(F.action == "class_add"))
async def cb_class_add(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text(
        "➕ <b>Добавить класс</b>\n\nВыберите параллель:",
        reply_markup=get_grade_choice_kb("class_add_grade"),
        parse_mode="HTML",
    )
    await call.answer()


@admin_classes_router.callback_query(AdminCB.filter(F.action == "class_add_grade"))
async def cb_class_add_grade(call: CallbackQuery, callback_data: AdminCB, state: FSMContext) -> None:
    try:
        grade = int(callback_data.param)
    except (TypeError, ValueError):
        await call.answer("Некорректная параллель.", show_alert=True)
        return
    if grade not in range(1, 12):
        await call.answer("Некорректная параллель.", show_alert=True)
        return

    await state.update_data(grade=grade)
    await state.set_state(AddSchoolClassState.waiting_for_letter)
    await call.message.edit_text(
        f"🏫 <b>{grade} класс</b>\n\nВведите букву класса. Например: <b>А</b>",
        reply_markup=get_class_creation_cancel_kb(),
        parse_mode="HTML",
    )
    await call.answer()


@admin_classes_router.message(AddSchoolClassState.waiting_for_letter)
async def process_class_letter(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    grade = data.get("grade")
    letter = db.normalize_class_letter(message.text or "")
    if not grade or not letter.isalpha() or len(letter) > 3:
        await message.answer("⚠️ Введите букву класса без цифр и лишних символов.")
        return

    if await db.get_class_by_grade_letter(grade, letter):
        await message.answer(f"⚠️ Класс {grade}-{letter} уже существует.", reply_markup=get_classes_menu_kb())
        return

    await state.update_data(letter=letter)
    await state.set_state(AddSchoolClassState.waiting_for_confirm)
    await message.answer(
        f"🏫 Создать класс <b>{grade}-{letter}</b>?",
        reply_markup=get_class_create_confirm_kb(grade, letter),
        parse_mode="HTML",
    )


@admin_classes_router.callback_query(AdminCB.filter(F.action == "class_create_cancel"))
async def cb_class_create_cancel(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text("❌ Создание класса отменено.", reply_markup=get_classes_menu_kb())
    await call.answer()


@admin_classes_router.callback_query(
    AddSchoolClassState.waiting_for_confirm, AdminCB.filter(F.action == "class_create_confirm")
)
async def cb_class_create_confirm(
    call: CallbackQuery, callback_data: AdminCB, state: FSMContext
) -> None:
    data = await state.get_data()
    try:
        grade_raw, letter_from_button = callback_data.param.split("|", 1)
        grade = int(grade_raw)
    except (AttributeError, ValueError):
        await state.clear()
        await call.answer("Данные создания класса устарели.", show_alert=True)
        return
    letter = db.normalize_class_letter(data.get("letter", ""))
    if data.get("grade") != grade or letter != letter_from_button or grade not in range(1, 12):
        await state.clear()
        await call.answer("Данные создания класса устарели.", show_alert=True)
        return
    if await db.get_class_by_grade_letter(grade, letter):
        await state.clear()
        await call.message.edit_text(
            f"⚠️ Класс {grade}-{letter} уже существует.", reply_markup=get_classes_menu_kb()
        )
        await call.answer()
        return
    try:
        school_class = await db.create_school_class(grade, letter)
    except IntegrityError:
        logger.info("Duplicate school class creation prevented: %s-%s", grade, letter)
        await state.clear()
        await call.message.edit_text(
            f"⚠️ Класс {grade}-{letter} уже существует.", reply_markup=get_classes_menu_kb()
        )
        await call.answer()
        return
    await state.clear()
    await call.message.edit_text(
        f"✅ Класс <b>{school_class.display_name}</b> успешно добавлен.",
        reply_markup=get_classes_menu_kb(),
        parse_mode="HTML",
    )
    await call.answer()


@admin_classes_router.callback_query(AdminCB.filter(F.action.in_({"classes_list", "classes_manage"})))
async def cb_classes_list(call: CallbackQuery, callback_data: AdminCB) -> None:
    classes = await db.get_school_classes()
    title = "📋 <b>Все классы</b>" if callback_data.action == "classes_list" else "🗑 <b>Управление классами</b>"
    if not classes:
        text = f"{title}\n\nКлассы пока не добавлены."
    else:
        text = f"{title}\n\nВыберите класс:"
    await call.message.edit_text(text, reply_markup=get_classes_list_kb(classes), parse_mode="HTML")
    await call.answer()


async def show_class_card(call: CallbackQuery, class_id: int) -> None:
    school_class = await db.get_class_by_id(class_id)
    if not school_class:
        await call.answer("Класс не найден.", show_alert=True)
        return
    users_count = await db.get_users_count_by_class(school_class.display_name)
    status = "🟢 Активен" if school_class.is_active else "🔴 Отключён"
    curator = await db.get_user_by_id(school_class.curator_user_id) if school_class.curator_user_id else None
    curator_text = (
        f"👨‍🏫 Классный руководитель: <b>{escape(curator.first_name)} {escape(curator.last_name)}</b>\n"
        f"🆔 Код: <code>{escape(curator.user_code or '—')}</code>\n"
        if curator else "👨‍🏫 Классный руководитель: не назначен\n"
    )
    await call.message.edit_text(
        f"🏫 <b>{school_class.display_name}</b>\n\n👥 Учеников: <b>{users_count}</b>\n{curator_text}Статус: {status}",
        reply_markup=get_class_detail_kb(school_class),
        parse_mode="HTML",
    )
    await call.answer()


@admin_classes_router.callback_query(AdminCB.filter(F.action == "class_view"))
async def cb_class_view(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        class_id = int(callback_data.param)
    except (TypeError, ValueError):
        await call.answer("Некорректный класс.", show_alert=True)
        return
    await show_class_card(call, class_id)


def _class_id_from_param(param: str | None) -> int | None:
    try:
        return int(param)
    except (TypeError, ValueError):
        return None


async def _curator_actor(telegram_id: int):
    """Fresh permission lookup for every curator-management mutation."""
    actor = await db.get_user_by_tg_id(telegram_id)
    return actor if can_manage_classes(actor) else None


@admin_classes_router.callback_query(AdminCB.filter(F.action.in_({"class_curator_assign", "class_curator_change"})))
async def cb_class_curator_assign(call: CallbackQuery, callback_data: AdminCB, state: FSMContext) -> None:
    class_id = _class_id_from_param(callback_data.param)
    actor = await _curator_actor(call.from_user.id)
    school_class = await db.get_class_by_id(class_id) if class_id else None
    if not actor or not school_class:
        await call.answer("Класс не найден или доступ изменён.", show_alert=True)
        return
    await state.clear()
    await state.update_data(curator_class_id=class_id)
    await state.set_state(ClassCuratorState.waiting_for_user_code)
    existing = await db.get_user_by_id(school_class.curator_user_id) if school_class.curator_user_id else None
    current = (
        f"\nТекущий руководитель: <b>{escape(existing.first_name)} {escape(existing.last_name)}</b>."
        if existing else ""
    )
    await call.message.edit_text(
        f"👨‍🏫 <b>Классный руководитель {school_class.display_name}</b>{current}\n\n"
        "Введите User Code сотрудника, например <code>SCH-7K4M2P</code>.",
        reply_markup=get_class_curator_confirm_kb("class_curator_cancel"),
        parse_mode="HTML",
    )
    await call.answer()


@admin_classes_router.message(ClassCuratorState.waiting_for_user_code)
async def process_curator_user_code(message: Message, state: FSMContext) -> None:
    actor = await _curator_actor(message.from_user.id)
    data = await state.get_data()
    class_id = data.get("curator_class_id")
    school_class = await db.get_class_by_id(class_id) if isinstance(class_id, int) else None
    if not actor or not school_class:
        await state.clear()
        await message.answer("Сессия назначения устарела. Откройте класс заново.")
        return
    candidate = await db.get_user_by_code(message.text or "")
    if not candidate:
        await message.answer("Пользователь с таким кодом не найден. Проверьте код и попробуйте ещё раз.")
        return
    await state.update_data(curator_candidate_id=candidate.id)
    card = (
        f"👤 <b>{escape(candidate.first_name)} {escape(candidate.last_name)}</b>\n"
        f"🆔 <code>{escape(candidate.user_code or '—')}</code>\n"
        f"Роль: <b>{escape(normalize_role(candidate.role))}</b>"
    )
    if can_access_staff(candidate):
        await state.set_state(ClassCuratorState.waiting_for_candidate_confirm)
        await message.answer(
            f"{card}\n\nНазначить классным руководителем <b>{school_class.display_name}</b>?",
            reply_markup=get_class_curator_confirm_kb("class_curator_confirm"),
            parse_mode="HTML",
        )
        return
    if normalize_role(candidate.role) == UserRole.STUDENT.value and normalize_role(actor.role) == UserRole.SUPERADMIN.value:
        await state.set_state(ClassCuratorState.waiting_for_promotion_confirm)
        await message.answer(
            f"{card}\n\nПользователь имеет роль Student. Для назначения нужно изменить роль на Moderator.\n"
            f"Изменить роль и назначить руководителем <b>{school_class.display_name}</b>?",
            reply_markup=get_class_curator_confirm_kb("class_curator_promote"),
            parse_mode="HTML",
        )
        return
    await message.answer(
        "Этого пользователя нельзя назначить: нужен активный сотрудник с ролью Moderator, Admin или SuperAdmin. "
        "Только SuperAdmin может отдельно подтвердить повышение Student до Moderator."
    )


async def _assign_curator_from_state(call: CallbackQuery, state: FSMContext, *, promote: bool) -> None:
    actor = await _curator_actor(call.from_user.id)
    data = await state.get_data()
    class_id, candidate_id = data.get("curator_class_id"), data.get("curator_candidate_id")
    school_class = await db.get_class_by_id(class_id) if isinstance(class_id, int) else None
    candidate = await db.get_user_by_id(candidate_id) if isinstance(candidate_id, int) else None
    if not actor or not school_class or not candidate:
        await state.clear()
        await call.answer("Данные назначения устарели. Откройте класс заново.", show_alert=True)
        return
    if promote:
        if normalize_role(actor.role) != UserRole.SUPERADMIN.value or normalize_role(candidate.role) != UserRole.STUDENT.value:
            await state.clear()
            await call.answer("Повышение больше недоступно.", show_alert=True)
            return
        if not await db.update_user_role(candidate.telegram_id, UserRole.MODERATOR.value):
            await state.clear()
            await call.answer("Не удалось обновить роль пользователя.", show_alert=True)
            return
    else:
        candidate = await db.get_user_by_id(candidate.id)
        if not can_access_staff(candidate):
            await state.clear()
            await call.answer("У сотрудника больше нет нужной роли или активного статуса.", show_alert=True)
            return
    await db.set_class_curator(school_class.id, candidate.id)
    await state.clear()
    await show_class_card(call, school_class.id)


@admin_classes_router.callback_query(
    ClassCuratorState.waiting_for_candidate_confirm, AdminCB.filter(F.action == "class_curator_confirm")
)
async def cb_class_curator_confirm(call: CallbackQuery, state: FSMContext) -> None:
    await _assign_curator_from_state(call, state, promote=False)


@admin_classes_router.callback_query(
    ClassCuratorState.waiting_for_promotion_confirm, AdminCB.filter(F.action == "class_curator_promote")
)
async def cb_class_curator_promote(call: CallbackQuery, state: FSMContext) -> None:
    await _assign_curator_from_state(call, state, promote=True)


@admin_classes_router.callback_query(AdminCB.filter(F.action == "class_curator_remove"))
async def cb_class_curator_remove(call: CallbackQuery, callback_data: AdminCB, state: FSMContext) -> None:
    class_id = _class_id_from_param(callback_data.param)
    actor = await _curator_actor(call.from_user.id)
    school_class = await db.get_class_by_id(class_id) if class_id else None
    curator = await db.get_user_by_id(school_class.curator_user_id) if school_class and school_class.curator_user_id else None
    if not actor or not school_class or not curator:
        await call.answer("Классный руководитель не найден.", show_alert=True)
        return
    await state.clear()
    await state.update_data(curator_class_id=school_class.id)
    await state.set_state(ClassCuratorState.waiting_for_remove_confirm)
    await call.message.edit_text(
        f"Снять <b>{escape(curator.first_name)} {escape(curator.last_name)}</b> с должности классного руководителя "
        f"<b>{school_class.display_name}</b>?",
        reply_markup=get_class_curator_confirm_kb("class_curator_remove_confirm"),
        parse_mode="HTML",
    )
    await call.answer()


@admin_classes_router.callback_query(
    ClassCuratorState.waiting_for_remove_confirm, AdminCB.filter(F.action == "class_curator_remove_confirm")
)
async def cb_class_curator_remove_confirm(call: CallbackQuery, state: FSMContext) -> None:
    actor = await _curator_actor(call.from_user.id)
    class_id = (await state.get_data()).get("curator_class_id")
    school_class = await db.get_class_by_id(class_id) if isinstance(class_id, int) else None
    if not actor or not school_class:
        await state.clear()
        await call.answer("Данные назначения устарели.", show_alert=True)
        return
    await db.set_class_curator(school_class.id, None)
    await state.clear()
    await show_class_card(call, school_class.id)


@admin_classes_router.callback_query(AdminCB.filter(F.action == "class_curator_cancel"))
async def cb_class_curator_cancel(call: CallbackQuery, state: FSMContext) -> None:
    class_id = (await state.get_data()).get("curator_class_id")
    await state.clear()
    if isinstance(class_id, int) and await db.get_class_by_id(class_id):
        await show_class_card(call, class_id)
    else:
        await call.message.edit_text("Действие отменено.", reply_markup=get_classes_menu_kb())
        await call.answer()


@admin_classes_router.callback_query(AdminCB.filter(F.action == "class_toggle"))
async def cb_class_toggle(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        class_id = int(callback_data.param)
    except (TypeError, ValueError):
        await call.answer("Некорректный класс.", show_alert=True)
        return
    school_class = await db.get_class_by_id(class_id)
    if not school_class:
        await call.answer("Класс не найден.", show_alert=True)
        return
    await db.set_school_class_active(class_id, not school_class.is_active)
    await show_class_card(call, class_id)


@admin_classes_router.callback_query(AdminCB.filter(F.action == "class_delete"))
async def cb_class_delete(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        class_id = int(callback_data.param)
    except (TypeError, ValueError):
        await call.answer("Некорректный класс.", show_alert=True)
        return
    school_class = await db.get_class_by_id(class_id)
    if not school_class:
        await call.answer("Класс не найден.", show_alert=True)
        return
    await call.message.edit_text(
        f"⚠️ Удалить класс <b>{school_class.display_name}</b>?\n\n"
        "Если в нём есть ученики, класс будет отключён, а не удалён.",
        reply_markup=get_class_delete_confirm_kb(school_class),
        parse_mode="HTML",
    )
    await call.answer()


@admin_classes_router.callback_query(AdminCB.filter(F.action == "class_delete_cancel"))
async def cb_class_delete_cancel(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        class_id = int(callback_data.param)
    except (TypeError, ValueError):
        await call.answer("Некорректный класс.", show_alert=True)
        return
    await show_class_card(call, class_id)


@admin_classes_router.callback_query(AdminCB.filter(F.action == "class_delete_confirm"))
async def cb_class_delete_confirm(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        class_id = int(callback_data.param)
    except (TypeError, ValueError):
        await call.answer("Некорректный класс.", show_alert=True)
        return
    school_class = await db.get_class_by_id(class_id)
    if not school_class:
        await call.answer("Класс не найден.", show_alert=True)
        return
    users_count = await db.get_users_count_by_class(school_class.display_name)
    if users_count:
        await db.set_school_class_active(class_id, False)
        await call.message.edit_text(
            "⚠️ В классе зарегистрированы ученики.\n"
            "Класс отключён, но данные учеников сохранены.",
            reply_markup=get_classes_menu_kb(),
        )
        await call.answer()
        return

    await db.delete_school_class_if_empty(class_id)
    await call.message.edit_text(
        f"✅ Класс {school_class.display_name} удалён.", reply_markup=get_classes_menu_kb()
    )
    await call.answer()
