"""Admin CMS for the content already modelled in the project.

The handlers are intentionally small FSMs: each save happens once, at the
last step, and every callback is acknowledged.  They use the existing tables
instead of introducing a parallel content system.
"""

from datetime import datetime
from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database import requests as db
from filters.roles import ADMIN_ROLES, RoleFilter
from keyboards.admin_kb import (
    AdminCB,
    get_content_detail_kb,
    get_content_edit_fields_kb,
    get_content_list_kb,
    get_content_menu_kb,
    get_lesson_detail_kb,
    get_schedule_classes_kb,
    get_schedule_days_admin_kb,
    get_schedule_lessons_kb,
)
from states import AchievementCreateState, ContentEditState, EventCreateState, LessonCreateState, PollCreateState


admin_content_router = Router()
admin_content_router.callback_query.filter(RoleFilter(ADMIN_ROLES))
admin_content_router.message.filter(RoleFilter(ADMIN_ROLES))

_CONTENT_TITLES = {
    "events": "🎯 <b>Мероприятия</b>\n\nСоздавайте, публикуйте и скрывайте школьные мероприятия.",
    "achievements": "🏆 <b>Достижения</b>\n\nПубликуйте достижения учеников, команд и школы.",
    "polls": "📊 <b>Опросы</b>\n\nСоздавайте опросы и открывайте или закрывайте голосование.",
}
_SKIP_KB = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="⏭ Пропустить", callback_data=AdminCB(action="content_skip").pack()),
    InlineKeyboardButton(text="❌ Отмена", callback_data=AdminCB(action="content_cancel").pack()),
]])
_CANCEL_KB = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="❌ Отмена", callback_data=AdminCB(action="content_cancel").pack()),
]])


def _parse_date(value: str):
    try:
        return datetime.strptime(value.strip(), "%d.%m.%Y").date()
    except (TypeError, ValueError):
        return None


def _parse_time(value: str):
    if not value or value.strip() in {"-", "—"}:
        return None
    try:
        return datetime.strptime(value.strip(), "%H:%M").time()
    except ValueError:
        return False


def _optional(value: str | None) -> str | None:
    cleaned = (value or "").strip()
    return cleaned if cleaned and cleaned not in {"-", "—"} else None


def _event_target_kb(classes) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="🌐 Для всех классов", callback_data=AdminCB(action="event_target", param="all").pack())]]
    rows += [[InlineKeyboardButton(
        text=f"🏫 {school_class.display_name}", callback_data=AdminCB(action="event_target", param=str(school_class.id)).pack()
    )] for school_class in classes]
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data=AdminCB(action="content_cancel").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _content_item(kind: str, item_id: int):
    if kind == "events":
        return await db.get_event_for_admin(item_id)
    if kind == "achievements":
        return await db.get_achievement_for_admin(item_id)
    if kind == "polls":
        return await db.get_poll_for_admin(item_id)
    return None


async def _show_content_menu(call: CallbackQuery, kind: str, *, clear_state: FSMContext | None = None) -> None:
    if kind not in _CONTENT_TITLES:
        await call.answer("Раздел не найден.", show_alert=True)
        return
    if clear_state:
        await clear_state.clear()
    await call.message.edit_text(_CONTENT_TITLES[kind], reply_markup=get_content_menu_kb(kind), parse_mode="HTML")
    await call.answer()


async def _show_content_list(call: CallbackQuery, kind: str) -> None:
    if kind == "events":
        items = await db.get_events_for_admin()
    elif kind == "achievements":
        items = await db.get_achievements_for_admin()
    elif kind == "polls":
        items = await db.get_polls_for_admin()
    else:
        await call.answer("Раздел не найден.", show_alert=True)
        return
    label = {"events": "мероприятий", "achievements": "достижений", "polls": "опросов"}[kind]
    text = f"📋 <b>Список {label}</b>\n\nВыберите запись:" if items else f"📋 <b>Список {label}</b>\n\nПока ничего нет."
    await call.message.edit_text(text, reply_markup=get_content_list_kb(kind, items), parse_mode="HTML")
    await call.answer()


async def _show_content_item(call: CallbackQuery, kind: str, item_id: int) -> None:
    item = await _content_item(kind, item_id)
    if not item:
        await call.answer("Запись удалена или не найдена.", show_alert=True)
        return
    if kind == "events":
        published = bool(item.is_published)
        status = "опубликовано" if published else "черновик"
        date_text = item.event_date.strftime("%d.%m.%Y")
        time_text = f" {item.event_time.strftime('%H:%M')}" if item.event_time else ""
        audience = "все классы" if item.target_class_id is None else f"класс #{item.target_class_id}"
        text = (
            f"🎯 <b>{escape(item.title_ru)}</b>\n\n{escape(item.description_ru)}\n\n"
            f"📅 {date_text}{time_text}\n📍 {escape(item.location_ru or '—')}\n"
            f"👥 {audience}\nСтатус: <b>{status}</b>"
        )
    elif kind == "achievements":
        published = bool(item.is_published)
        status = "опубликовано" if published else "черновик"
        text = (
            f"🏆 <b>{escape(item.title_ru)}</b>\n\n{escape(item.description_ru)}\n\n"
            f"📅 {item.achievement_date.strftime('%d.%m.%Y')}\n"
            f"👤 {escape(item.student_name or '—')}\n🏷 {escape(item.category or '—')}\nСтатус: <b>{status}</b>"
        )
    else:
        published = bool(item.is_active)
        options = await db.get_poll_options(item.id)
        results = await db.get_poll_results(item.id)
        counts = {option.id: count for option, count in results}
        rows = "\n".join(f"• {escape(option.text_ru)} — {counts.get(option.id, 0)}" for option in options) or "—"
        text = f"📊 <b>{escape(item.question_ru)}</b>\n\n{rows}\n\nСтатус: <b>{'открыт' if published else 'закрыт'}</b>"
    await call.message.edit_text(text, reply_markup=get_content_detail_kb(kind, item.id, published), parse_mode="HTML")
    await call.answer()


@admin_content_router.callback_query(AdminCB.filter(F.action.in_({"events", "achievements", "polls"})))
async def content_home(call: CallbackQuery, callback_data: AdminCB, state: FSMContext) -> None:
    await _show_content_menu(call, callback_data.action, clear_state=state)


@admin_content_router.callback_query(AdminCB.filter(F.action == "content_list"))
async def content_list(call: CallbackQuery, callback_data: AdminCB) -> None:
    await _show_content_list(call, callback_data.param or "")


@admin_content_router.callback_query(AdminCB.filter(F.action == "content_view"))
async def content_view(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        kind, raw_id = (callback_data.param or "").split("|", 1)
        item_id = int(raw_id)
    except (TypeError, ValueError):
        await call.answer("Некорректная запись.", show_alert=True)
        return
    await _show_content_item(call, kind, item_id)


@admin_content_router.callback_query(AdminCB.filter(F.action.in_({"content_publish", "content_hide", "content_delete"})))
async def content_change_status(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        kind, raw_id = (callback_data.param or "").split("|", 1)
        item_id = int(raw_id)
    except (TypeError, ValueError):
        await call.answer("Некорректная запись.", show_alert=True)
        return
    if kind not in _CONTENT_TITLES:
        await call.answer("Раздел не найден.", show_alert=True)
        return
    if callback_data.action == "content_delete":
        changed = await ({"events": db.delete_school_event, "achievements": db.delete_achievement, "polls": db.delete_poll}[kind])(item_id)
        if not changed:
            await call.answer("Запись уже удалена.", show_alert=True)
            return
        if kind == "events":
            items = await db.get_events_for_admin()
        elif kind == "achievements":
            items = await db.get_achievements_for_admin()
        else:
            items = await db.get_polls_for_admin()
        label = {"events": "мероприятий", "achievements": "достижений", "polls": "опросов"}[kind]
        text = f"📋 <b>Список {label}</b>\n\nВыберите запись:" if items else f"📋 <b>Список {label}</b>\n\nПока ничего нет."
        await call.message.edit_text(text, reply_markup=get_content_list_kb(kind, items), parse_mode="HTML")
        await call.answer("Запись удалена.")
        return
    visible = callback_data.action == "content_publish"
    changed = await ({
        "events": lambda: db.update_school_event(item_id, is_published=visible),
        "achievements": lambda: db.update_achievement(item_id, is_published=visible),
        "polls": lambda: db.update_poll(item_id, is_active=visible),
    }[kind])()
    if not changed:
        await call.answer("Запись уже недоступна.", show_alert=True)
        return
    await _show_content_item(call, kind, item_id)


@admin_content_router.callback_query(AdminCB.filter(F.action == "content_edit"))
async def content_edit(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        kind, raw_id = (callback_data.param or "").split("|", 1)
        item_id = int(raw_id)
    except (TypeError, ValueError):
        await call.answer("Некорректная запись.", show_alert=True)
        return
    if not await _content_item(kind, item_id):
        await call.answer("Запись не найдена.", show_alert=True)
        return
    await call.message.edit_text("✏️ <b>Изменение записи</b>\n\nВыберите поле:", reply_markup=get_content_edit_fields_kb(kind, item_id), parse_mode="HTML")
    await call.answer()


@admin_content_router.callback_query(AdminCB.filter(F.action == "content_edit_field"))
async def content_edit_field(call: CallbackQuery, callback_data: AdminCB, state: FSMContext) -> None:
    try:
        kind, raw_id, field = (callback_data.param or "").split("|", 2)
        item_id = int(raw_id)
    except (TypeError, ValueError):
        await call.answer("Некорректное поле.", show_alert=True)
        return
    allowed = {
        "events": {"title_ru", "title_uz", "description_ru", "description_uz", "event_date", "location_ru", "location_uz"},
        "achievements": {"title_ru", "title_uz", "description_ru", "description_uz", "achievement_date", "student_name", "category"},
        "polls": {"question_ru", "question_uz"},
    }
    if field not in allowed.get(kind, set()) or not await _content_item(kind, item_id):
        await call.answer("Поле недоступно.", show_alert=True)
        return
    await state.clear()
    await state.update_data(content_kind=kind, content_item_id=item_id, content_field=field)
    await state.set_state(ContentEditState.value)
    hint = " в формате ДД.ММ.ГГГГ" if field.endswith("date") else " (для очистки отправьте -)"
    await call.message.edit_text(f"✏️ Введите новое значение{hint}:", reply_markup=_CANCEL_KB)
    await call.answer()


@admin_content_router.message(ContentEditState.value)
async def content_edit_value(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    kind, item_id, field = data.get("content_kind"), data.get("content_item_id"), data.get("content_field")
    value = (message.text or "").strip()
    if not isinstance(item_id, int) or not value:
        await message.answer("⚠️ Введите непустое значение.", reply_markup=_CANCEL_KB)
        return
    if kind == "lesson" and field == "subject":
        changed = await db.update_schedule_lesson(item_id, subject=value)
        await state.clear()
        await message.answer("✅ Предмет изменён." if changed else "⚠️ Урок уже недоступен.")
        return
    if kind not in _CONTENT_TITLES:
        await message.answer("⚠️ Этот экран уже устарел.", reply_markup=_CANCEL_KB)
        return
    if field.endswith("date"):
        parsed = _parse_date(value)
        if not parsed:
            await message.answer("⚠️ Используйте дату в формате ДД.ММ.ГГГГ.", reply_markup=_CANCEL_KB)
            return
        value = parsed
    elif field in {"title_uz", "description_uz", "location_ru", "location_uz", "student_name", "category", "question_uz"}:
        value = _optional(value)
    updater = {"events": db.update_school_event, "achievements": db.update_achievement, "polls": db.update_poll}[kind]
    changed = await updater(item_id, **{field: value})
    await state.clear()
    if changed:
        await message.answer("✅ Изменения сохранены.")
    else:
        await message.answer("⚠️ Запись уже недоступна.")


@admin_content_router.callback_query(AdminCB.filter(F.action == "content_cancel"))
async def content_cancel(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text("❌ Действие отменено.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⬅️ В админ-панель", callback_data=AdminCB(action="main").pack())
    ]]))
    await call.answer()


# ---- Events ----

@admin_content_router.callback_query(AdminCB.filter(F.action == "content_create"), F.data.contains("events"))
async def event_create_start(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(EventCreateState.title_ru)
    await call.message.edit_text("🎯 <b>Новое мероприятие</b>\n\nВведите заголовок на русском:", reply_markup=_CANCEL_KB, parse_mode="HTML")
    await call.answer()


@admin_content_router.message(EventCreateState.title_ru)
async def event_title_ru(message: Message, state: FSMContext) -> None:
    title = _optional(message.text)
    if not title:
        await message.answer("⚠️ Заголовок обязателен.", reply_markup=_CANCEL_KB)
        return
    await state.update_data(title_ru=title)
    await state.set_state(EventCreateState.title_uz)
    await message.answer("Введите заголовок на узбекском или пропустите:", reply_markup=_SKIP_KB)


@admin_content_router.message(EventCreateState.title_uz)
async def event_title_uz(message: Message, state: FSMContext) -> None:
    await state.update_data(title_uz=_optional(message.text))
    await state.set_state(EventCreateState.description_ru)
    await message.answer("Введите описание на русском:", reply_markup=_CANCEL_KB)


@admin_content_router.message(EventCreateState.description_ru)
async def event_description_ru(message: Message, state: FSMContext) -> None:
    value = _optional(message.text)
    if not value:
        await message.answer("⚠️ Описание обязательно.", reply_markup=_CANCEL_KB)
        return
    await state.update_data(description_ru=value)
    await state.set_state(EventCreateState.description_uz)
    await message.answer("Введите описание на узбекском или пропустите:", reply_markup=_SKIP_KB)


@admin_content_router.message(EventCreateState.description_uz)
async def event_description_uz(message: Message, state: FSMContext) -> None:
    await state.update_data(description_uz=_optional(message.text))
    await state.set_state(EventCreateState.event_date)
    await message.answer("Введите дату в формате ДД.ММ.ГГГГ:", reply_markup=_CANCEL_KB)


@admin_content_router.message(EventCreateState.event_date)
async def event_date(message: Message, state: FSMContext) -> None:
    value = _parse_date(message.text or "")
    if not value:
        await message.answer("⚠️ Используйте дату в формате ДД.ММ.ГГГГ.", reply_markup=_CANCEL_KB)
        return
    await state.update_data(event_date=value)
    await state.set_state(EventCreateState.event_time)
    await message.answer("Введите время ЧЧ:ММ или пропустите:", reply_markup=_SKIP_KB)


@admin_content_router.message(EventCreateState.event_time)
async def event_time(message: Message, state: FSMContext) -> None:
    value = _parse_time(message.text or "")
    if value is False:
        await message.answer("⚠️ Используйте время ЧЧ:ММ.", reply_markup=_SKIP_KB)
        return
    await state.update_data(event_time=value)
    await state.set_state(EventCreateState.location_ru)
    await message.answer("Введите место на русском или пропустите:", reply_markup=_SKIP_KB)


@admin_content_router.message(EventCreateState.location_ru)
async def event_location_ru(message: Message, state: FSMContext) -> None:
    await state.update_data(location_ru=_optional(message.text))
    await state.set_state(EventCreateState.location_uz)
    await message.answer("Введите место на узбекском или пропустите:", reply_markup=_SKIP_KB)


@admin_content_router.message(EventCreateState.location_uz)
async def event_location_uz(message: Message, state: FSMContext) -> None:
    await state.update_data(location_uz=_optional(message.text))
    await state.set_state(EventCreateState.target_class)
    await message.answer("Выберите аудиторию мероприятия:", reply_markup=_event_target_kb(await db.get_school_classes(active_only=True)))


@admin_content_router.callback_query(EventCreateState.target_class, AdminCB.filter(F.action == "event_target"))
async def event_target(call: CallbackQuery, state: FSMContext, callback_data: AdminCB) -> None:
    raw = callback_data.param or ""
    if raw == "all":
        class_id = None
    else:
        try:
            class_id = int(raw)
        except ValueError:
            await call.answer("Некорректный класс.", show_alert=True)
            return
        if not await db.get_class_by_id(class_id):
            await call.answer("Класс не найден.", show_alert=True)
            return
    await state.update_data(target_class_id=class_id)
    await state.set_state(EventCreateState.photo)
    await call.message.edit_text("Отправьте фото мероприятия или пропустите:", reply_markup=_SKIP_KB)
    await call.answer()


@admin_content_router.message(EventCreateState.photo)
async def event_photo(message: Message, state: FSMContext) -> None:
    if message.photo:
        photo_file_id = message.photo[-1].file_id
    elif _optional(message.text) is None:
        photo_file_id = None
    else:
        await message.answer("⚠️ Отправьте фото или нажмите «Пропустить».", reply_markup=_SKIP_KB)
        return
    data = await state.get_data()
    await db.create_school_event(
        title_ru=data["title_ru"], title_uz=data.get("title_uz"),
        description_ru=data["description_ru"], description_uz=data.get("description_uz"),
        event_date=data["event_date"], event_time=data.get("event_time"),
        location_ru=data.get("location_ru"), location_uz=data.get("location_uz"),
        target_class_id=data.get("target_class_id"), photo_file_id=photo_file_id,
    )
    await state.clear()
    await message.answer("✅ Мероприятие сохранено как черновик. Откройте список, чтобы опубликовать его.")


# ---- Achievements ----

@admin_content_router.callback_query(AdminCB.filter(F.action == "content_create"), F.data.contains("achievements"))
async def achievement_create_start(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AchievementCreateState.title_ru)
    await call.message.edit_text("🏆 <b>Новое достижение</b>\n\nВведите заголовок на русском:", reply_markup=_CANCEL_KB, parse_mode="HTML")
    await call.answer()


@admin_content_router.message(AchievementCreateState.title_ru)
async def achievement_title_ru(message: Message, state: FSMContext) -> None:
    value = _optional(message.text)
    if not value:
        await message.answer("⚠️ Заголовок обязателен.", reply_markup=_CANCEL_KB)
        return
    await state.update_data(title_ru=value)
    await state.set_state(AchievementCreateState.title_uz)
    await message.answer("Введите заголовок на узбекском или пропустите:", reply_markup=_SKIP_KB)


@admin_content_router.message(AchievementCreateState.title_uz)
async def achievement_title_uz(message: Message, state: FSMContext) -> None:
    await state.update_data(title_uz=_optional(message.text))
    await state.set_state(AchievementCreateState.description_ru)
    await message.answer("Введите описание на русском:", reply_markup=_CANCEL_KB)


@admin_content_router.message(AchievementCreateState.description_ru)
async def achievement_description_ru(message: Message, state: FSMContext) -> None:
    value = _optional(message.text)
    if not value:
        await message.answer("⚠️ Описание обязательно.", reply_markup=_CANCEL_KB)
        return
    await state.update_data(description_ru=value)
    await state.set_state(AchievementCreateState.description_uz)
    await message.answer("Введите описание на узбекском или пропустите:", reply_markup=_SKIP_KB)


@admin_content_router.message(AchievementCreateState.description_uz)
async def achievement_description_uz(message: Message, state: FSMContext) -> None:
    await state.update_data(description_uz=_optional(message.text))
    await state.set_state(AchievementCreateState.achievement_date)
    await message.answer("Введите дату в формате ДД.ММ.ГГГГ:", reply_markup=_CANCEL_KB)


@admin_content_router.message(AchievementCreateState.achievement_date)
async def achievement_date(message: Message, state: FSMContext) -> None:
    value = _parse_date(message.text or "")
    if not value:
        await message.answer("⚠️ Используйте дату в формате ДД.ММ.ГГГГ.", reply_markup=_CANCEL_KB)
        return
    await state.update_data(achievement_date=value)
    await state.set_state(AchievementCreateState.student_name)
    await message.answer("Введите имя ученика/команды или пропустите:", reply_markup=_SKIP_KB)


@admin_content_router.message(AchievementCreateState.student_name)
async def achievement_student_name(message: Message, state: FSMContext) -> None:
    await state.update_data(student_name=_optional(message.text))
    await state.set_state(AchievementCreateState.category)
    await message.answer("Введите категорию или пропустите:", reply_markup=_SKIP_KB)


@admin_content_router.message(AchievementCreateState.category)
async def achievement_category(message: Message, state: FSMContext) -> None:
    await state.update_data(category=_optional(message.text))
    await state.set_state(AchievementCreateState.photo)
    await message.answer("Отправьте фото или пропустите:", reply_markup=_SKIP_KB)


@admin_content_router.message(AchievementCreateState.photo)
async def achievement_photo(message: Message, state: FSMContext) -> None:
    if message.photo:
        photo_file_id = message.photo[-1].file_id
    elif _optional(message.text) is None:
        photo_file_id = None
    else:
        await message.answer("⚠️ Отправьте фото или нажмите «Пропустить».", reply_markup=_SKIP_KB)
        return
    data = await state.get_data()
    await db.create_achievement(
        title_ru=data["title_ru"], title_uz=data.get("title_uz"),
        description_ru=data["description_ru"], description_uz=data.get("description_uz"),
        achievement_date=data["achievement_date"], student_name=data.get("student_name"),
        category=data.get("category"), photo_file_id=photo_file_id,
    )
    await state.clear()
    await message.answer("✅ Достижение сохранено как черновик. Откройте список, чтобы опубликовать его.")


# ---- Polls ----

@admin_content_router.callback_query(AdminCB.filter(F.action == "content_create"), F.data.contains("polls"))
async def poll_create_start(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(PollCreateState.question_ru)
    await call.message.edit_text("📊 <b>Новый опрос</b>\n\nВведите вопрос на русском:", reply_markup=_CANCEL_KB, parse_mode="HTML")
    await call.answer()


@admin_content_router.message(PollCreateState.question_ru)
async def poll_question_ru(message: Message, state: FSMContext) -> None:
    value = _optional(message.text)
    if not value:
        await message.answer("⚠️ Вопрос обязателен.", reply_markup=_CANCEL_KB)
        return
    await state.update_data(question_ru=value)
    await state.set_state(PollCreateState.question_uz)
    await message.answer("Введите вопрос на узбекском или пропустите:", reply_markup=_SKIP_KB)


@admin_content_router.message(PollCreateState.question_uz)
async def poll_question_uz(message: Message, state: FSMContext) -> None:
    await state.update_data(question_uz=_optional(message.text))
    await state.set_state(PollCreateState.options)
    await message.answer("Введите минимум два варианта: каждый с новой строки. Для UZ-перевода используйте «RU | UZ».", reply_markup=_CANCEL_KB)


@admin_content_router.message(PollCreateState.options)
async def poll_options(message: Message, state: FSMContext) -> None:
    options = []
    for line in (message.text or "").splitlines():
        ru, separator, uz = line.partition("|")
        ru = ru.strip()
        if ru:
            options.append((ru, _optional(uz) if separator else None))
    if len(options) < 2:
        await message.answer("⚠️ Укажите минимум два непустых варианта.", reply_markup=_CANCEL_KB)
        return
    data = await state.get_data()
    await db.create_poll(data["question_ru"], data.get("question_uz"), options)
    await state.clear()
    await message.answer("✅ Опрос сохранён закрытым. Откройте его из списка, когда будете готовы к голосованию.")


# ---- Schedule ----

@admin_content_router.callback_query(AdminCB.filter(F.action == "schedule"))
async def schedule_home(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    classes = await db.get_school_classes(active_only=True)
    text = "📅 <b>Расписание</b>\n\nВыберите класс:" if classes else "📅 <b>Расписание</b>\n\nСначала создайте активный класс."
    await call.message.edit_text(text, reply_markup=get_schedule_classes_kb(classes), parse_mode="HTML")
    await call.answer()


@admin_content_router.callback_query(AdminCB.filter(F.action == "schedule_class"))
async def schedule_class(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        class_id = int(callback_data.param or "")
    except ValueError:
        await call.answer("Некорректный класс.", show_alert=True)
        return
    school_class = await db.get_class_by_id(class_id)
    if not school_class:
        await call.answer("Класс не найден.", show_alert=True)
        return
    await call.message.edit_text(f"📅 <b>{escape(school_class.display_name)}</b>\n\nВыберите день:", reply_markup=get_schedule_days_admin_kb(class_id), parse_mode="HTML")
    await call.answer()


async def _show_schedule_day(call: CallbackQuery, class_id: int, weekday: int) -> None:
    school_class = await db.get_class_by_id(class_id)
    if not school_class or weekday not in range(6):
        await call.answer("Расписание устарело.", show_alert=True)
        return
    lessons = await db.get_lessons_for_admin(class_id, weekday)
    names = ("Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота")
    text = f"📅 <b>{escape(school_class.display_name)} — {names[weekday]}</b>\n\nВыберите урок или добавьте новый:"
    await call.message.edit_text(text, reply_markup=get_schedule_lessons_kb(class_id, weekday, lessons), parse_mode="HTML")
    await call.answer()


@admin_content_router.callback_query(AdminCB.filter(F.action == "schedule_day_admin"))
async def schedule_day(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        raw_class, raw_day = (callback_data.param or "").split("|", 1)
        class_id, weekday = int(raw_class), int(raw_day)
    except (TypeError, ValueError):
        await call.answer("Некорректный день.", show_alert=True)
        return
    await _show_schedule_day(call, class_id, weekday)


@admin_content_router.callback_query(AdminCB.filter(F.action == "lesson_create"))
async def lesson_create_start(call: CallbackQuery, callback_data: AdminCB, state: FSMContext) -> None:
    try:
        raw_class, raw_day = (callback_data.param or "").split("|", 1)
        class_id, weekday = int(raw_class), int(raw_day)
    except (TypeError, ValueError):
        await call.answer("Некорректный урок.", show_alert=True)
        return
    if not await db.get_class_by_id(class_id) or weekday not in range(6):
        await call.answer("Расписание устарело.", show_alert=True)
        return
    await state.clear()
    await state.update_data(lesson_class_id=class_id, lesson_weekday=weekday)
    await state.set_state(LessonCreateState.number)
    await call.message.edit_text("Введите номер урока (1–12):", reply_markup=_CANCEL_KB)
    await call.answer()


@admin_content_router.message(LessonCreateState.number)
async def lesson_number(message: Message, state: FSMContext) -> None:
    try:
        number = int((message.text or "").strip())
    except ValueError:
        number = 0
    if number not in range(1, 13):
        await message.answer("⚠️ Укажите номер от 1 до 12.", reply_markup=_CANCEL_KB)
        return
    await state.update_data(lesson_number=number)
    await state.set_state(LessonCreateState.subject)
    await message.answer("Введите предмет:", reply_markup=_CANCEL_KB)


@admin_content_router.message(LessonCreateState.subject)
async def lesson_subject(message: Message, state: FSMContext) -> None:
    value = _optional(message.text)
    if not value:
        await message.answer("⚠️ Предмет обязателен.", reply_markup=_CANCEL_KB)
        return
    await state.update_data(lesson_subject=value)
    await state.set_state(LessonCreateState.start_time)
    await message.answer("Введите время ЧЧ:ММ или пропустите:", reply_markup=_SKIP_KB)


@admin_content_router.message(LessonCreateState.start_time)
async def lesson_start_time(message: Message, state: FSMContext) -> None:
    value = _parse_time(message.text or "")
    if value is False:
        await message.answer("⚠️ Используйте время ЧЧ:ММ.", reply_markup=_SKIP_KB)
        return
    await state.update_data(lesson_start_time=value)
    await state.set_state(LessonCreateState.room)
    await message.answer("Введите кабинет или пропустите:", reply_markup=_SKIP_KB)


@admin_content_router.message(LessonCreateState.room)
async def lesson_room(message: Message, state: FSMContext) -> None:
    await state.update_data(lesson_room=_optional(message.text))
    await state.set_state(LessonCreateState.teacher_name)
    await message.answer("Введите имя преподавателя или пропустите:", reply_markup=_SKIP_KB)


@admin_content_router.message(LessonCreateState.teacher_name)
async def lesson_teacher(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    try:
        await db.create_schedule_lesson(
            school_class_id=data["lesson_class_id"], weekday=data["lesson_weekday"], lesson_number=data["lesson_number"],
            subject=data["lesson_subject"], start_time=data.get("lesson_start_time"), room=data.get("lesson_room"),
            teacher_name=_optional(message.text),
        )
    except ValueError:
        await message.answer("⚠️ В этот номер урока уже есть запись. Откройте его для изменения.")
        return
    await state.clear()
    await message.answer("✅ Урок добавлен.")


@admin_content_router.callback_query(AdminCB.filter(F.action == "lesson_view"))
async def lesson_view(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        raw_class, raw_day, raw_lesson = (callback_data.param or "").split("|", 2)
        class_id, weekday, lesson_id = int(raw_class), int(raw_day), int(raw_lesson)
    except (TypeError, ValueError):
        await call.answer("Некорректный урок.", show_alert=True)
        return
    lesson = await db.get_schedule_lesson(lesson_id)
    if not lesson or lesson.school_class_id != class_id or lesson.weekday != weekday:
        await call.answer("Урок уже удалён.", show_alert=True)
        return
    time_text = lesson.start_time.strftime("%H:%M") if lesson.start_time else "—"
    text = f"📚 <b>{escape(lesson.subject)}</b>\n\n№ {lesson.lesson_number}\n🕒 {time_text}\n🏫 {escape(lesson.room or '—')}\n👨‍🏫 {escape(lesson.teacher_name or '—')}"
    await call.message.edit_text(text, reply_markup=get_lesson_detail_kb(class_id, weekday, lesson_id), parse_mode="HTML")
    await call.answer()


@admin_content_router.callback_query(AdminCB.filter(F.action == "lesson_delete"))
async def lesson_delete(call: CallbackQuery, callback_data: AdminCB) -> None:
    try:
        raw_class, raw_day, raw_lesson = (callback_data.param or "").split("|", 2)
        class_id, weekday, lesson_id = int(raw_class), int(raw_day), int(raw_lesson)
    except (TypeError, ValueError):
        await call.answer("Некорректный урок.", show_alert=True)
        return
    lesson = await db.get_schedule_lesson(lesson_id)
    if not lesson or lesson.school_class_id != class_id or lesson.weekday != weekday:
        await call.answer("Урок уже удалён.", show_alert=True)
        return
    await db.delete_schedule_lesson(lesson_id)
    await _show_schedule_day(call, class_id, weekday)


@admin_content_router.callback_query(AdminCB.filter(F.action == "lesson_edit"))
async def lesson_edit(call: CallbackQuery, callback_data: AdminCB, state: FSMContext) -> None:
    try:
        raw_class, raw_day, raw_lesson, field = (callback_data.param or "").split("|", 3)
        class_id, weekday, lesson_id = int(raw_class), int(raw_day), int(raw_lesson)
    except (TypeError, ValueError):
        await call.answer("Некорректный урок.", show_alert=True)
        return
    lesson = await db.get_schedule_lesson(lesson_id)
    if field != "subject" or not lesson or lesson.school_class_id != class_id or lesson.weekday != weekday:
        await call.answer("Урок уже недоступен.", show_alert=True)
        return
    await state.clear()
    await state.update_data(lesson_edit_id=lesson_id)
    await state.set_state(ContentEditState.value)
    # Reuse the generic value state with a distinct sentinel.
    await state.update_data(content_kind="lesson", content_field="subject", content_item_id=lesson_id)
    await call.message.edit_text("Введите новое название предмета:", reply_markup=_CANCEL_KB)
    await call.answer()


@admin_content_router.callback_query(AdminCB.filter(F.action == "content_skip"))
async def content_skip(call: CallbackQuery, state: FSMContext) -> None:
    current = await state.get_state()
    if current == EventCreateState.title_uz.state:
        await state.update_data(title_uz=None); await state.set_state(EventCreateState.description_ru)
        text, kb = "Введите описание на русском:", _CANCEL_KB
    elif current == EventCreateState.description_uz.state:
        await state.update_data(description_uz=None); await state.set_state(EventCreateState.event_date)
        text, kb = "Введите дату в формате ДД.ММ.ГГГГ:", _CANCEL_KB
    elif current == EventCreateState.event_time.state:
        await state.update_data(event_time=None); await state.set_state(EventCreateState.location_ru)
        text, kb = "Введите место на русском или пропустите:", _SKIP_KB
    elif current == EventCreateState.location_ru.state:
        await state.update_data(location_ru=None); await state.set_state(EventCreateState.location_uz)
        text, kb = "Введите место на узбекском или пропустите:", _SKIP_KB
    elif current == EventCreateState.location_uz.state:
        await state.update_data(location_uz=None); await state.set_state(EventCreateState.target_class)
        text, kb = "Выберите аудиторию мероприятия:", _event_target_kb(await db.get_school_classes(active_only=True))
    elif current == EventCreateState.photo.state:
        data = await state.get_data()
        await db.create_school_event(
            title_ru=data["title_ru"], title_uz=data.get("title_uz"), description_ru=data["description_ru"],
            description_uz=data.get("description_uz"), event_date=data["event_date"], event_time=data.get("event_time"),
            location_ru=data.get("location_ru"), location_uz=data.get("location_uz"), target_class_id=data.get("target_class_id"), photo_file_id=None,
        )
        await state.clear(); await call.message.edit_text("✅ Мероприятие сохранено как черновик."); await call.answer(); return
    elif current == AchievementCreateState.title_uz.state:
        await state.update_data(title_uz=None); await state.set_state(AchievementCreateState.description_ru)
        text, kb = "Введите описание на русском:", _CANCEL_KB
    elif current == AchievementCreateState.description_uz.state:
        await state.update_data(description_uz=None); await state.set_state(AchievementCreateState.achievement_date)
        text, kb = "Введите дату в формате ДД.ММ.ГГГГ:", _CANCEL_KB
    elif current == AchievementCreateState.student_name.state:
        await state.update_data(student_name=None); await state.set_state(AchievementCreateState.category)
        text, kb = "Введите категорию или пропустите:", _SKIP_KB
    elif current == AchievementCreateState.category.state:
        await state.update_data(category=None); await state.set_state(AchievementCreateState.photo)
        text, kb = "Отправьте фото или пропустите:", _SKIP_KB
    elif current == AchievementCreateState.photo.state:
        data = await state.get_data()
        await db.create_achievement(
            title_ru=data["title_ru"], title_uz=data.get("title_uz"), description_ru=data["description_ru"],
            description_uz=data.get("description_uz"), achievement_date=data["achievement_date"],
            student_name=data.get("student_name"), category=data.get("category"), photo_file_id=None,
        )
        await state.clear(); await call.message.edit_text("✅ Достижение сохранено как черновик."); await call.answer(); return
    elif current == PollCreateState.question_uz.state:
        await state.update_data(question_uz=None); await state.set_state(PollCreateState.options)
        text, kb = "Введите минимум два варианта: каждый с новой строки. Для UZ-перевода используйте «RU | UZ».", _CANCEL_KB
    elif current == LessonCreateState.start_time.state:
        await state.update_data(lesson_start_time=None); await state.set_state(LessonCreateState.room)
        text, kb = "Введите кабинет или пропустите:", _SKIP_KB
    elif current == LessonCreateState.room.state:
        await state.update_data(lesson_room=None); await state.set_state(LessonCreateState.teacher_name)
        text, kb = "Введите имя преподавателя или пропустите:", _SKIP_KB
    elif current == LessonCreateState.teacher_name.state:
        data = await state.get_data()
        try:
            await db.create_schedule_lesson(
                school_class_id=data["lesson_class_id"], weekday=data["lesson_weekday"], lesson_number=data["lesson_number"],
                subject=data["lesson_subject"], start_time=data.get("lesson_start_time"), room=data.get("lesson_room"), teacher_name=None,
            )
        except ValueError:
            await call.answer("В этот номер урока уже есть запись.", show_alert=True); return
        await state.clear(); await call.message.edit_text("✅ Урок добавлен."); await call.answer(); return
    else:
        await call.answer("Этот шаг уже устарел.", show_alert=True)
        return
    await call.message.edit_text(text, reply_markup=kb)
    await call.answer()
