from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import get_active_class_grades, get_active_classes_by_grade, get_class_by_id, get_user_by_tg_id, update_user_profile
from database import requests as db
from filters import RegisteredUserFilter
from keyboards import (
    get_edit_cancel_kb,
    get_edit_fields_kb,
    get_edit_language_kb,
    get_class_change_classes_kb,
    get_class_change_confirm_kb,
    get_class_change_grades_kb,
    get_class_change_reason_kb,
    get_profile_class_grades_kb,
    get_profile_classes_kb,
    get_main_menu_kb,
    get_profile_main_kb,
)
from locales.texts import TEXTS
from states import ClassChangeState, EditProfileState

router = Router()
router.message.filter(RegisteredUserFilter())
router.callback_query.filter(RegisteredUserFilter())
PROFILE_BUTTONS = {texts["btn_profile"] for texts in TEXTS.values()}


# Вспомогательная функция для построения текста профиля
def render_profile_text(user) -> str:
    lang = user.language or "ru"
    lang_texts = TEXTS.get(lang, TEXTS["ru"])

    lang_display = (
        lang_texts["lang_name_ru"] if user.language == "ru" else lang_texts["lang_name_uz"]
    )
    date_str = user.created_at.strftime("%d.%m.%Y")

    return lang_texts["profile_card"].format(
        first_name=escape(user.first_name),
        last_name=escape(user.last_name),
        class_name=escape(user.class_name),
        language=lang_display,
        role=lang_texts.get(f"role_{user.role}", user.role),
        created_at=date_str,
        user_code=escape(user.user_code or "—"),
    )


# --- Нажатие кнопки в главном меню ---

@router.message(F.text.in_(PROFILE_BUTTONS))
@router.message(Command("profile"))
async def show_profile(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = await get_user_by_tg_id(message.from_user.id)
    if not user:
        return

    # Telegram usernames can change.  Keep the current public username only
    # for the student's optional leaderboard link; it is never shown by
    # default.
    username = (message.from_user.username or "").lstrip("@") or None
    if username != user.telegram_username:
        await update_user_profile(user.telegram_id, telegram_username=username)
        user = await get_user_by_tg_id(user.telegram_id)

    lang = user.language or "ru"
    text = render_profile_text(user)
    kb = get_profile_main_kb(lang, bool(user.public_profile_enabled))

    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "profile_main_menu")
async def return_to_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return

    lang = user.language or "ru"
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    await callback.message.edit_text(lang_texts["menu_returned"])
    await callback.message.answer(
        lang_texts["main_menu"], reply_markup=get_main_menu_kb(lang)
    )
    await callback.answer()


@router.callback_query(F.data == "profile_public_toggle")
async def toggle_public_profile(callback: CallbackQuery) -> None:
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return
    enabled = not bool(user.public_profile_enabled)
    await update_user_profile(user.telegram_id, public_profile_enabled=enabled)
    user = await get_user_by_tg_id(user.telegram_id)
    lang = user.language or "ru"
    await callback.message.edit_text(
        render_profile_text(user), reply_markup=get_profile_main_kb(lang, enabled), parse_mode="HTML"
    )
    await callback.answer(TEXTS[lang]["public_profile_enabled" if enabled else "public_profile_disabled"], show_alert=True)


# --- Меню редактирования ---

@router.callback_query(F.data == "edit_profile_open")
async def open_edit_menu(callback: CallbackQuery) -> None:
    user = await get_user_by_tg_id(callback.from_user.id)
    lang = user.language if user else "ru"
    lang_texts = TEXTS.get(lang, TEXTS["ru"])

    await callback.message.edit_text(
        lang_texts["edit_menu_title"],
        reply_markup=get_edit_fields_kb(lang),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "edit_field_back")
async def back_to_profile(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return

    lang = user.language or "ru"
    text = render_profile_text(user)
    kb = get_profile_main_kb(lang, bool(user.public_profile_enabled))

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


# --- Выбор конкретного поля для изменения ---

@router.callback_query(F.data == "edit_field_first_name")
async def start_edit_first_name(callback: CallbackQuery, state: FSMContext) -> None:
    user = await get_user_by_tg_id(callback.from_user.id)
    lang = user.language if user else "ru"

    await callback.message.edit_text(
        TEXTS[lang]["ask_new_first_name"], reply_markup=get_edit_cancel_kb(lang)
    )
    await state.set_state(EditProfileState.first_name)
    await callback.answer()


@router.callback_query(F.data == "edit_field_last_name")
async def start_edit_last_name(callback: CallbackQuery, state: FSMContext) -> None:
    user = await get_user_by_tg_id(callback.from_user.id)
    lang = user.language if user else "ru"

    await callback.message.edit_text(
        TEXTS[lang]["ask_new_last_name"], reply_markup=get_edit_cancel_kb(lang)
    )
    await state.set_state(EditProfileState.last_name)
    await callback.answer()


@router.callback_query(F.data == "edit_field_class_name")
async def start_edit_class_name(callback: CallbackQuery, state: FSMContext) -> None:
    # Legacy profile cards may still contain this callback. It now enters the
    # same approval flow as the current profile instead of changing a class.
    await start_class_change(callback, state)


@router.callback_query(F.data == "class_change_start")
async def start_class_change(callback: CallbackQuery, state: FSMContext) -> None:
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return
    lang = user.language or "ru"
    grades = await get_active_class_grades()
    await state.clear()
    if not grades:
        await callback.message.edit_text(TEXTS[lang]["no_school_classes"], reply_markup=get_edit_cancel_kb(lang))
        await callback.answer()
        return
    await state.set_state(ClassChangeState.grade)
    await callback.message.edit_text(
        TEXTS[lang]["class_change_title"], reply_markup=get_class_change_grades_kb(grades, lang), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(ClassChangeState.grade, F.data.startswith("class_change_grade_"))
async def class_change_select_grade(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        grade = int((callback.data or "").removeprefix("class_change_grade_"))
    except ValueError:
        await callback.answer(TEXTS["ru"]["callback_expired"], show_alert=True)
        return
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return
    lang = user.language or "ru"
    classes = await get_active_classes_by_grade(grade)
    if not classes:
        await callback.answer(TEXTS[lang]["class_choice_invalid"], show_alert=True)
        return
    await state.update_data(class_change_grade=grade)
    await state.set_state(ClassChangeState.target_class)
    await callback.message.edit_text(
        TEXTS[lang]["class_change_choose_class"], reply_markup=get_class_change_classes_kb(classes, lang), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(ClassChangeState.target_class, F.data.startswith("class_change_select_"))
async def class_change_select_target(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        class_id = int((callback.data or "").removeprefix("class_change_select_"))
    except ValueError:
        await callback.answer(TEXTS["ru"]["callback_expired"], show_alert=True)
        return
    user = await get_user_by_tg_id(callback.from_user.id)
    school_class = await get_class_by_id(class_id)
    if not user or not school_class or not school_class.is_active:
        await callback.answer(TEXTS[(user.language if user else "ru")]["class_choice_invalid"], show_alert=True)
        return
    lang = user.language or "ru"
    if user.class_name == school_class.display_name:
        await callback.answer(TEXTS[lang]["class_change_same"], show_alert=True)
        return
    await state.update_data(class_change_target_id=class_id)
    await state.set_state(ClassChangeState.reason)
    await callback.message.edit_text(
        TEXTS[lang]["class_change_reason"], reply_markup=get_class_change_reason_kb(lang), parse_mode="HTML"
    )
    await callback.answer()


async def _show_class_change_confirmation(message: Message | CallbackQuery, state: FSMContext, user, reason: str | None) -> None:
    data = await state.get_data()
    target_id = data.get("class_change_target_id")
    school_class = await get_class_by_id(target_id) if isinstance(target_id, int) else None
    lang = user.language or "ru"
    if not school_class or not school_class.is_active:
        await state.clear()
        if isinstance(message, CallbackQuery):
            await message.answer(TEXTS[lang]["class_choice_invalid"], show_alert=True)
        else:
            await message.answer(TEXTS[lang]["class_choice_invalid"])
        return
    await state.update_data(class_change_reason=(reason or "").strip() or None)
    await state.set_state(ClassChangeState.confirm)
    text = TEXTS[lang]["class_change_confirm"].format(
        old_class=escape(user.class_name),
        new_class=escape(school_class.display_name),
        reason=escape((reason or "").strip()) or "—",
    )
    if isinstance(message, CallbackQuery):
        await message.message.edit_text(text, reply_markup=get_class_change_confirm_kb(lang), parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=get_class_change_confirm_kb(lang), parse_mode="HTML")


@router.callback_query(ClassChangeState.reason, F.data == "class_change_skip_reason")
async def class_change_skip_reason(callback: CallbackQuery, state: FSMContext) -> None:
    user = await get_user_by_tg_id(callback.from_user.id)
    if user:
        await _show_class_change_confirmation(callback, state, user, None)
    await callback.answer()


@router.message(ClassChangeState.reason)
async def class_change_reason(message: Message, state: FSMContext) -> None:
    user = await get_user_by_tg_id(message.from_user.id)
    if not user:
        return
    await _show_class_change_confirmation(message, state, user, message.text)


@router.callback_query(ClassChangeState.confirm, F.data == "class_change_submit")
async def class_change_submit(callback: CallbackQuery, state: FSMContext) -> None:
    user = await get_user_by_tg_id(callback.from_user.id)
    data = await state.get_data()
    if not user or not isinstance(data.get("class_change_target_id"), int):
        await state.clear()
        await callback.answer(TEXTS[(user.language if user else "ru")]["callback_expired"], show_alert=True)
        return
    lang = user.language or "ru"
    try:
        request = await db.create_class_change_request(
            user.id, data["class_change_target_id"], data.get("class_change_reason")
        )
    except ValueError:
        await state.clear()
        await callback.answer(TEXTS[lang]["class_change_same"], show_alert=True)
        return
    await state.clear()
    if request is None:
        await callback.message.edit_text(TEXTS[lang]["class_change_pending"], reply_markup=get_profile_main_kb(lang, bool(user.public_profile_enabled)))
    else:
        await callback.message.edit_text(TEXTS[lang]["class_change_submitted"], reply_markup=get_profile_main_kb(lang, bool(user.public_profile_enabled)))
    await callback.answer()


@router.callback_query(F.data == "class_change_cancel")
async def class_change_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return
    lang = user.language or "ru"
    await callback.message.edit_text(render_profile_text(user), reply_markup=get_profile_main_kb(lang, bool(user.public_profile_enabled)), parse_mode="HTML")
    await callback.answer()


@router.callback_query(EditProfileState.class_grade, F.data.startswith("profile_class_grade_"))
async def profile_select_class_grade(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        grade = int(callback.data.removeprefix("profile_class_grade_"))
    except ValueError:
        await callback.answer("Некорректный класс.", show_alert=True)
        return
    user = await get_user_by_tg_id(callback.from_user.id)
    lang = user.language if user else "ru"
    classes = await get_active_classes_by_grade(grade)
    if not classes:
        await callback.answer(TEXTS[lang]["class_choice_invalid"], show_alert=True)
        return
    await state.update_data(profile_class_grade=grade)
    await state.set_state(EditProfileState.class_name)
    await callback.message.edit_text(
        TEXTS[lang]["ask_class_from_list"], reply_markup=get_profile_classes_kb(classes, lang), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(EditProfileState.class_name, F.data.startswith("profile_class_select_"))
async def profile_select_class(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        class_id = int(callback.data.removeprefix("profile_class_select_"))
    except ValueError:
        await callback.answer("Некорректный класс.", show_alert=True)
        return
    user = await get_user_by_tg_id(callback.from_user.id)
    lang = user.language if user else "ru"
    await state.clear()
    # Never honour a pre-upgrade direct-class callback. The current profile
    # provides the reviewed request path above instead.
    await callback.message.edit_text(TEXTS[lang]["class_change_use_request"], reply_markup=get_profile_main_kb(lang, bool(user.public_profile_enabled)))
    await callback.answer()


@router.callback_query(F.data == "edit_field_language")
async def start_edit_language(callback: CallbackQuery, state: FSMContext) -> None:
    user = await get_user_by_tg_id(callback.from_user.id)
    lang = user.language if user else "ru"

    await callback.message.edit_text(
        TEXTS[lang]["ask_new_language"],
        reply_markup=get_edit_language_kb(lang)
    )
    await state.set_state(EditProfileState.language)
    await callback.answer()


# --- FSM Хэндлеры ввода новых значений ---

@router.message(EditProfileState.first_name)
async def process_new_first_name(message: Message, state: FSMContext) -> None:
    new_val = (message.text or "").strip()
    user = await get_user_by_tg_id(message.from_user.id)
    lang = user.language if user else "ru"
    if not new_val:
        await message.answer(TEXTS[lang]["value_required"])
        return

    await update_user_profile(message.from_user.id, first_name=new_val)
    await state.clear()

    user = await get_user_by_tg_id(message.from_user.id)
    lang = user.language or "ru"
    lang_texts = TEXTS.get(lang, TEXTS["ru"])

    await message.answer(lang_texts["profile_updated"])
    text = render_profile_text(user)
    await message.answer(text, reply_markup=get_profile_main_kb(lang, bool(user.public_profile_enabled)), parse_mode="HTML")


@router.message(EditProfileState.last_name)
async def process_new_last_name(message: Message, state: FSMContext) -> None:
    new_val = (message.text or "").strip()
    user = await get_user_by_tg_id(message.from_user.id)
    lang = user.language if user else "ru"
    if not new_val:
        await message.answer(TEXTS[lang]["value_required"])
        return

    await update_user_profile(message.from_user.id, last_name=new_val)
    await state.clear()

    user = await get_user_by_tg_id(message.from_user.id)
    lang = user.language or "ru"
    lang_texts = TEXTS.get(lang, TEXTS["ru"])

    await message.answer(lang_texts["profile_updated"])
    text = render_profile_text(user)
    await message.answer(text, reply_markup=get_profile_main_kb(lang, bool(user.public_profile_enabled)), parse_mode="HTML")


@router.message(EditProfileState.class_name)
async def process_new_class_name(message: Message, state: FSMContext) -> None:
    user = await get_user_by_tg_id(message.from_user.id)
    lang = user.language if user else "ru"
    data = await state.get_data()
    grade = data.get("profile_class_grade")
    classes = await get_active_classes_by_grade(grade) if isinstance(grade, int) else []
    await message.answer(
        TEXTS[lang]["ask_class_from_list"], reply_markup=get_profile_classes_kb(classes, lang)
    )


@router.callback_query(EditProfileState.language, F.data.startswith("change_lang_"))
async def process_new_language(callback: CallbackQuery, state: FSMContext) -> None:
    new_lang = callback.data.split("_")[2]
    await update_user_profile(callback.from_user.id, language=new_lang)
    await state.clear()

    user = await get_user_by_tg_id(callback.from_user.id)
    lang_texts = TEXTS.get(new_lang, TEXTS["ru"])

    # Обновляем главное меню бота в соответствии с новым языком
    await callback.message.answer(
        lang_texts["profile_updated"],
        reply_markup=get_main_menu_kb(new_lang)
    )

    text = render_profile_text(user)
    await callback.message.answer(text, reply_markup=get_profile_main_kb(new_lang, bool(user.public_profile_enabled)), parse_mode="HTML")
    await callback.answer()
