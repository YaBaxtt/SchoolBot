import logging

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import REGISTRATION_REVIEW_CHAT_ID
from database import add_user, get_active_class_grades, get_active_classes_by_grade, get_class_by_id, get_user_by_tg_id
from keyboards import (
    get_language_kb,
    get_main_menu_kb,
    get_registration_classes_kb,
    get_registration_grades_kb,
    get_registration_name_confirm_kb,
)
from keyboards.admin_kb import get_registration_request_actions_kb
from locales.texts import TEXTS
from states import RegistrationState

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    user = await get_user_by_tg_id(message.from_user.id)
    
    if user and user.status == "active":
        await state.clear()
        lang_texts = TEXTS.get(user.language, TEXTS["ru"])
        await message.answer(
            "{welcome}\n\n{menu}".format(
                welcome=lang_texts["welcome_back"].format(first_name=user.first_name),
                menu=lang_texts["main_menu"],
            ),
            reply_markup=get_main_menu_kb(user.language)
        )
        return

    if user and user.status == "pending":
        await state.clear()
        lang_texts = TEXTS.get(user.language, TEXTS["ru"])
        await message.answer(lang_texts["registration_pending"])
        return

    if user and user.status == "rejected":
        await state.clear()
        lang_texts = TEXTS.get(user.language, TEXTS["ru"])
        await message.answer(lang_texts["registration_rejected"])
        return

    await state.clear()
    await message.answer(
        TEXTS["ru"]["select_lang"],
        reply_markup=get_language_kb()
    )
    await state.set_state(RegistrationState.language)


@router.callback_query(RegistrationState.language, F.data.startswith("lang_"))
async def process_language(callback: CallbackQuery, state: FSMContext) -> None:
    lang = callback.data.split("_")[1]
    await state.update_data(language=lang)
    
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    await callback.message.edit_text(lang_texts["ask_first_name"])
    await state.set_state(RegistrationState.first_name)
    await callback.answer()


@router.message(RegistrationState.first_name)
async def process_first_name(message: Message, state: FSMContext) -> None:
    first_name = (message.text or "").strip()
    data = await state.get_data()
    lang = data.get("language", "ru")
    if not first_name:
        await message.answer(TEXTS.get(lang, TEXTS["ru"])["value_required"])
        return

    await state.update_data(first_name=first_name)
    
    data = await state.get_data()
    lang = data.get("language", "ru")
    lang_texts = TEXTS.get(lang, TEXTS["ru"])

    await message.answer(lang_texts["ask_last_name"])
    await state.set_state(RegistrationState.last_name)


@router.message(RegistrationState.last_name)
async def process_last_name(message: Message, state: FSMContext) -> None:
    last_name = (message.text or "").strip()
    data = await state.get_data()
    lang = data.get("language", "ru")
    if not last_name:
        await message.answer(TEXTS.get(lang, TEXTS["ru"])["value_required"])
        return

    await state.update_data(last_name=last_name)
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    await message.answer(
        lang_texts["confirm_full_name"].format(
            first_name=data["first_name"], last_name=last_name
        ),
        reply_markup=get_registration_name_confirm_kb(lang),
    )
    await state.set_state(RegistrationState.confirm_name)


@router.callback_query(RegistrationState.confirm_name, F.data == "reg_name_edit")
async def edit_name_before_registration(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("language", "ru")
    await callback.message.edit_text(TEXTS.get(lang, TEXTS["ru"])["ask_first_name"])
    await state.set_state(RegistrationState.first_name)
    await callback.answer()


@router.callback_query(RegistrationState.confirm_name, F.data == "reg_name_confirm")
async def confirm_name_before_registration(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("language", "ru")
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    grades = await get_active_class_grades()
    if not grades:
        logger.warning("Registration paused: no active school classes are configured")
        await state.clear()
        await callback.message.edit_text(lang_texts["no_school_classes"])
        await callback.answer()
        return

    await callback.message.edit_text(
        lang_texts["ask_grade"], reply_markup=get_registration_grades_kb(grades, lang)
    )
    await state.set_state(RegistrationState.grade)
    await callback.answer()


@router.callback_query(RegistrationState.grade, F.data.startswith("reg_grade_"))
async def process_grade(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        grade = int(callback.data.removeprefix("reg_grade_"))
    except ValueError:
        await callback.answer()
        return

    data = await state.get_data()
    lang = data.get("language", "ru")
    classes = await get_active_classes_by_grade(grade)
    if not classes:
        await callback.answer(TEXTS.get(lang, TEXTS["ru"])["class_choice_invalid"], show_alert=True)
        return

    await state.update_data(grade=grade)
    await callback.message.edit_text(
        TEXTS.get(lang, TEXTS["ru"])["ask_class_from_list"],
        reply_markup=get_registration_classes_kb(classes, grade, lang),
    )
    await state.set_state(RegistrationState.class_name)
    await callback.answer()


@router.callback_query(RegistrationState.class_name, F.data == "reg_classes_back")
async def back_to_grades(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("language", "ru")
    grades = await get_active_class_grades()
    if not grades:
        await state.clear()
        await callback.message.edit_text(TEXTS.get(lang, TEXTS["ru"])["no_school_classes"])
        await callback.answer()
        return

    await callback.message.edit_text(
        TEXTS.get(lang, TEXTS["ru"])["ask_grade"],
        reply_markup=get_registration_grades_kb(grades, lang),
    )
    await state.set_state(RegistrationState.grade)
    await callback.answer()


@router.callback_query(RegistrationState.class_name, F.data.startswith("reg_class_"))
async def process_class_selection(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    try:
        class_id = int(callback.data.removeprefix("reg_class_"))
    except ValueError:
        await callback.answer()
        return

    school_class = await get_class_by_id(class_id)
    data = await state.get_data()
    lang = data.get("language", "ru")
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    if not school_class or not school_class.is_active:
        await callback.answer(lang_texts["class_choice_invalid"], show_alert=True)
        return

    existing_user = await get_user_by_tg_id(callback.from_user.id)
    if existing_user:
        await state.clear()
        await callback.message.edit_text(lang_texts["registration_pending"])
        await callback.answer()
        return

    user = await add_user(
        telegram_id=callback.from_user.id,
        language=lang,
        first_name=data["first_name"],
        last_name=data["last_name"],
        class_name=school_class.display_name,
        status="pending",
        telegram_username=callback.from_user.username,
    )
    await state.clear()
    await callback.message.edit_text(lang_texts["registration_submitted"])
    await callback.answer()

    if REGISTRATION_REVIEW_CHAT_ID is not None:
        try:
            await bot.send_message(
                REGISTRATION_REVIEW_CHAT_ID,
                "🆕 <b>Новая заявка</b>\n\n"
                f"👤 ФИО: {user.first_name} {user.last_name}\n"
                f"🏫 Класс: {user.class_name}\n🌐 Язык: {user.language}\n"
                f"🆔 User Code: <code>{user.user_code or '—'}</code>\n"
                f"📅 Дата: {user.created_at.strftime('%d.%m.%Y %H:%M') if user.created_at else '—'}",
                reply_markup=get_registration_request_actions_kb(user.telegram_id),
                parse_mode="HTML",
            )
        except Exception as error:
            logger.warning("Unable to send registration request to the group: %s", error)


@router.message(RegistrationState.class_name)
async def reject_manual_class_input(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("language", "ru")
    grade = data.get("grade")
    classes = await get_active_classes_by_grade(grade) if grade else []
    await message.answer(
        TEXTS.get(lang, TEXTS["ru"])["ask_class_from_list"],
        reply_markup=get_registration_classes_kb(classes, grade, lang) if classes else None,
    )
