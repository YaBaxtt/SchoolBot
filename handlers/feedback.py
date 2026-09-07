import logging
from html import escape
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import ADMIN_IDS, FEEDBACK_GROUP_ID
from database import create_feedback, get_user_by_tg_id, get_user_feedback_by_id, get_user_feedbacks
from filters import RegisteredUserFilter
from keyboards import (
    get_confirm_feedback_kb, get_feedback_cancel_kb, get_feedback_warning_kb,
    get_main_menu_kb, get_my_feedback_detail_kb, get_my_feedbacks_kb,
)
from keyboards.admin_kb import get_feedback_group_kb
from locales.texts import TEXTS
from states import FeedbackState

router = Router()
router.message.filter(RegisteredUserFilter())
router.callback_query.filter(RegisteredUserFilter())
logger = logging.getLogger(__name__)
COMPLAINT_BUTTONS = {texts["btn_complaint"] for texts in TEXTS.values()}
SUGGESTION_BUTTONS = {texts["btn_suggestion"] for texts in TEXTS.values()}
MY_FEEDBACKS_BUTTONS = {texts["btn_my_feedbacks"] for texts in TEXTS.values()}
CANCEL_BUTTONS = {texts["btn_cancel"] for texts in TEXTS.values()}


# --- Старт сценария обращений ---

@router.message(F.text.in_(COMPLAINT_BUTTONS))
async def start_complaint(message: Message, state: FSMContext) -> None:
    user = await get_user_by_tg_id(message.from_user.id)
    lang = user.language if user else "ru"

    await state.clear()
    await state.update_data(type="complaint")
    await state.set_state(FeedbackState.warning)
    await message.answer(
        TEXTS[lang]["complaint_warning"],
        reply_markup=get_feedback_warning_kb("complaint", lang),
        parse_mode="HTML",
    )


@router.message(F.text.in_(SUGGESTION_BUTTONS))
async def start_suggestion(message: Message, state: FSMContext) -> None:
    user = await get_user_by_tg_id(message.from_user.id)
    lang = user.language if user else "ru"

    await state.clear()
    await state.update_data(type="suggestion")
    await state.set_state(FeedbackState.warning)
    await message.answer(
        TEXTS[lang]["suggestion_warning"],
        reply_markup=get_feedback_warning_kb("suggestion", lang),
        parse_mode="HTML",
    )


@router.callback_query(FeedbackState.warning, F.data == "feedback_warning_continue")
async def continue_feedback_after_warning(callback: CallbackQuery, state: FSMContext) -> None:
    user = await get_user_by_tg_id(callback.from_user.id)
    lang = user.language if user else "ru"
    feedback_type = (await state.get_data()).get("type")
    if feedback_type not in {"complaint", "suggestion", "question"}:
        await state.clear()
        await callback.answer(TEXTS[lang]["callback_expired"], show_alert=True)
        return
    await state.set_state(FeedbackState.text)
    prompt_key = "ask_complaint" if feedback_type == "complaint" else "ask_suggestion" if feedback_type == "suggestion" else "ask_question"
    await callback.message.edit_text(TEXTS[lang]["feedback_warning_accepted"])
    await callback.message.answer(
        TEXTS[lang][prompt_key], reply_markup=get_feedback_cancel_kb(lang), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(FeedbackState.warning, F.data == "feedback_warning_cancel")
async def cancel_feedback_warning(callback: CallbackQuery, state: FSMContext) -> None:
    user = await get_user_by_tg_id(callback.from_user.id)
    lang = user.language if user else "ru"
    await state.clear()
    await callback.message.edit_text(TEXTS[lang]["feedback_cancelled"])
    await callback.message.answer(TEXTS[lang]["main_menu"], reply_markup=get_main_menu_kb(lang))
    await callback.answer()


@router.message(FeedbackState.warning)
async def feedback_warning_waiting(message: Message) -> None:
    user = await get_user_by_tg_id(message.from_user.id)
    lang = user.language if user else "ru"
    await message.answer(TEXTS[lang]["feedback_warning_waiting"])


@router.message(F.text.in_(MY_FEEDBACKS_BUTTONS))
async def show_my_feedbacks(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = await get_user_by_tg_id(message.from_user.id)
    if not user:
        return
    lang = user.language or "ru"
    feedbacks = await get_user_feedbacks(user.id)
    text = TEXTS[lang]["my_feedbacks_title"] if feedbacks else TEXTS[lang]["no_my_feedbacks"]
    await message.answer(text, reply_markup=get_my_feedbacks_kb(feedbacks, lang), parse_mode="HTML")


@router.callback_query(F.data == "my_feedbacks_back")
async def show_my_feedbacks_from_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return
    lang = user.language or "ru"
    feedbacks = await get_user_feedbacks(user.id)
    text = TEXTS[lang]["my_feedbacks_title"] if feedbacks else TEXTS[lang]["no_my_feedbacks"]
    await callback.message.edit_text(text, reply_markup=get_my_feedbacks_kb(feedbacks, lang), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("my_feedback_"))
async def show_my_feedback_detail(callback: CallbackQuery) -> None:
    try:
        feedback_id = int((callback.data or "").removeprefix("my_feedback_"))
    except ValueError:
        await callback.answer("Некорректное обращение.", show_alert=True)
        return
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return
    lang = user.language or "ru"
    feedback = await get_user_feedback_by_id(user.id, feedback_id)
    if not feedback:
        await callback.answer(TEXTS[lang]["callback_expired"], show_alert=True)
        return
    feedback_type = TEXTS[lang].get(f"type_{feedback.type}", feedback.type)
    status = TEXTS[lang].get(f"status_{feedback.status}", feedback.status)
    date = feedback.created_at.strftime("%d.%m.%Y %H:%M") if feedback.created_at else "—"
    text = TEXTS[lang]["my_feedback_detail"].format(
        type=feedback_type,
        id=feedback.id,
        date=date,
        status=status,
        text=escape(feedback.text),
    )
    await callback.message.edit_text(text, reply_markup=get_my_feedback_detail_kb(lang), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "my_feedbacks_main_menu")
async def my_feedbacks_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user = await get_user_by_tg_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return
    lang = user.language or "ru"
    await callback.message.edit_text(TEXTS[lang]["menu_returned"])
    await callback.message.answer(TEXTS[lang]["main_menu"], reply_markup=get_main_menu_kb(lang))
    await callback.answer()


# --- Шаг 1: Ввод текста ---

@router.message(FeedbackState.text, F.text.in_(CANCEL_BUTTONS))
async def cancel_feedback_from_text(message: Message, state: FSMContext) -> None:
    user = await get_user_by_tg_id(message.from_user.id)
    lang = user.language if user else "ru"
    lang_texts = TEXTS.get(lang, TEXTS["ru"])

    await state.clear()
    await message.answer(
        lang_texts["feedback_cancelled"], reply_markup=get_main_menu_kb(lang)
    )


@router.message(FeedbackState.text)
async def process_feedback_text(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    user = await get_user_by_tg_id(message.from_user.id)
    lang = user.language if user else "ru"
    lang_texts = TEXTS.get(lang, TEXTS["ru"])

    if not text:
        await message.answer(lang_texts["value_required"])
        return

    await state.update_data(text=text)

    confirm_msg = lang_texts["confirm_feedback"].format(text=escape(text))
    await message.answer(
        confirm_msg,
        reply_markup=get_confirm_feedback_kb(lang),
        parse_mode="HTML"
    )
    await state.set_state(FeedbackState.confirm)


# --- Шаг 2: Подтверждение отправки ---

@router.callback_query(FeedbackState.confirm, F.data == "feedback_confirm_yes")
async def process_feedback_confirm_yes(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    user = await get_user_by_tg_id(callback.from_user.id)
    lang = user.language if user else "ru"
    lang_texts = TEXTS.get(lang, TEXTS["ru"])

    fb_type = data.get("type", "complaint")
    fb_text = data.get("text", "")

    # Сохраняем в базу данных
    feedback = await create_feedback(
        user_db_id=user.id,
        fb_type=fb_type,
        text=fb_text
    )

    await state.clear()
    await callback.message.edit_text(lang_texts["feedback_sent"])
    await callback.message.answer(
        lang_texts["main_menu"], reply_markup=get_main_menu_kb(lang)
    )
    await callback.answer()

    # Формируем текст уведомления администраторам
    type_str = lang_texts.get(f"type_{fb_type}", fb_type)
    date_str = feedback.created_at.strftime("%d.%m.%Y %H:%M")

    admin_msg = lang_texts["admin_feedback_notification"].format(
        type=type_str,
        first_name=escape(user.first_name),
        last_name=escape(user.last_name),
        class_name=escape(user.class_name),
        date=date_str,
        text=escape(fb_text)
    )

    # Кнопка «Ответить» с передачей ID обратной связи
    reply_kb = get_feedback_group_kb(feedback)

    # Отправляем уведомления администраторам
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id, 
                text=admin_msg, 
                reply_markup=reply_kb, 
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Не удалось отправить уведомление админу {admin_id}: {e}")

    if FEEDBACK_GROUP_ID is not None and FEEDBACK_GROUP_ID not in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=FEEDBACK_GROUP_ID,
                text=admin_msg,
                reply_markup=reply_kb,
                parse_mode="HTML",
            )
        except Exception as error:
            logger.warning("Не удалось отправить обращение в группу администрации: %s", error)


@router.callback_query(FeedbackState.confirm, F.data == "feedback_confirm_no")
async def process_feedback_confirm_no(callback: CallbackQuery, state: FSMContext) -> None:
    user = await get_user_by_tg_id(callback.from_user.id)
    lang = user.language if user else "ru"

    await state.clear()
    await callback.message.edit_text(TEXTS[lang]["feedback_cancelled"])
    await callback.message.answer(
        TEXTS[lang]["main_menu"], reply_markup=get_main_menu_kb(lang)
    )
    await callback.answer()


@router.message(FeedbackState.confirm, F.text.in_(CANCEL_BUTTONS))
async def cancel_feedback_from_confirmation(message: Message, state: FSMContext) -> None:
    user = await get_user_by_tg_id(message.from_user.id)
    lang = user.language if user else "ru"
    lang_texts = TEXTS.get(lang, TEXTS["ru"])

    await state.clear()
    await message.answer(
        lang_texts["feedback_cancelled"], reply_markup=get_main_menu_kb(lang)
    )


@router.message(FeedbackState.confirm)
async def feedback_waiting_for_confirmation(message: Message) -> None:
    user = await get_user_by_tg_id(message.from_user.id)
    lang = user.language if user else "ru"
    await message.answer(TEXTS.get(lang, TEXTS["ru"])["feedback_waiting_confirmation"])
