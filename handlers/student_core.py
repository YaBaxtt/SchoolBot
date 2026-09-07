from datetime import date
from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import requests as db
from filters import RegisteredUserFilter
from keyboards.feedback_kb import get_feedback_warning_kb, get_my_feedbacks_kb
from keyboards.main_kb import get_feedback_cancel_kb
from keyboards.student_kb import (
    StudentCB,
    WEEKDAYS,
    achievements_kb,
    event_list_kb,
    poll_options_kb,
    polls_kb,
    requests_kb,
    schedule_days_kb,
)
from locales.texts import TEXTS
from states import FeedbackState


student_core_router = Router()
student_core_router.message.filter(RegisteredUserFilter())
student_core_router.callback_query.filter(RegisteredUserFilter())

SCHEDULE_BUTTONS = {items["btn_schedule"] for items in TEXTS.values()}
EVENT_BUTTONS = {items["btn_events"] for items in TEXTS.values()}
ACHIEVEMENT_BUTTONS = {items["btn_achievements"] for items in TEXTS.values()}
REQUEST_BUTTONS = {items["btn_requests"] for items in TEXTS.values()}
POLL_BUTTONS = {items["btn_polls"] for items in TEXTS.values()}
MY_CLASS_BUTTONS = {items["btn_my_class"] for items in TEXTS.values()}


def _lang(user) -> str:
    return user.language if user.language in TEXTS else "ru"


async def _user_and_class(telegram_id: int):
    user = await db.get_user_by_tg_id(telegram_id)
    school_class = await db.get_class_by_display_name(user.class_name) if user else None
    return user, school_class


def _lessons_text(lessons, lang: str) -> str:
    if not lessons:
        return TEXTS[lang]["schedule_empty"]
    rows = []
    for lesson in lessons:
        start = lesson.start_time.strftime("%H:%M") if lesson.start_time else "—"
        extra = ""
        if lesson.room:
            extra += f" · {escape(lesson.room)}"
        if lesson.teacher_name:
            extra += f" · {escape(lesson.teacher_name)}"
        rows.append(f"{lesson.lesson_number}. {start} — {escape(lesson.subject)}{extra}")
    return "\n".join(rows)


async def _show_schedule(target: Message | CallbackQuery, telegram_id: int, weekday: int | None = None) -> None:
    user, school_class = await _user_and_class(telegram_id)
    if not user or not school_class:
        if isinstance(target, CallbackQuery):
            await target.answer(TEXTS["ru"]["class_choice_invalid"], show_alert=True)
        return
    lang = _lang(user)
    if weekday is None:
        text = TEXTS[lang]["schedule_title"].format(class_name=escape(school_class.display_name))
        markup = schedule_days_kb(lang)
    else:
        lessons = await db.get_lessons_for_class_day(school_class.id, weekday)
        day = WEEKDAYS[lang][weekday]
        text = TEXTS[lang]["schedule_day"].format(
            day=day, class_name=escape(school_class.display_name), lessons=_lessons_text(lessons, lang)
        )
        markup = schedule_days_kb(lang)
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
        await target.answer()
    else:
        await target.answer(text, reply_markup=markup, parse_mode="HTML")


@student_core_router.message(F.text.in_(SCHEDULE_BUTTONS))
@student_core_router.message(Command("schedule"))
async def schedule(message: Message) -> None:
    await _show_schedule(message, message.from_user.id)


@student_core_router.callback_query(StudentCB.filter(F.action == "schedule_day"))
async def schedule_day(call: CallbackQuery, callback_data: StudentCB) -> None:
    try:
        weekday = int(callback_data.param or "")
    except ValueError:
        await call.answer("Некорректный день.", show_alert=True)
        return
    if weekday not in range(6):
        await call.answer("Некорректный день.", show_alert=True)
        return
    await _show_schedule(call, call.from_user.id, weekday)


async def _show_events(target: Message | CallbackQuery, telegram_id: int) -> None:
    user, school_class = await _user_and_class(telegram_id)
    if not user or not school_class:
        return
    lang = _lang(user)
    events = await db.get_events_for_class(school_class.id)
    text = TEXTS[lang]["events_title"] + ("\n\n" + TEXTS[lang]["events_empty"] if not events else "")
    markup = event_list_kb(events, lang) if events else None
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
        await target.answer()
    else:
        await target.answer(text, reply_markup=markup, parse_mode="HTML")


@student_core_router.message(F.text.in_(EVENT_BUTTONS))
@student_core_router.message(Command("events"))
async def events(message: Message) -> None:
    await _show_events(message, message.from_user.id)


@student_core_router.callback_query(StudentCB.filter(F.action == "event"))
async def event_detail(call: CallbackQuery, callback_data: StudentCB) -> None:
    try:
        event_id = int(callback_data.param or "")
    except ValueError:
        await call.answer("Некорректное мероприятие.", show_alert=True)
        return
    user, school_class = await _user_and_class(call.from_user.id)
    event = await db.get_event_by_id_for_class(event_id, school_class.id) if school_class else None
    if not user or not event:
        await call.answer(TEXTS["ru"]["callback_expired"], show_alert=True)
        return
    lang = _lang(user)
    title = event.title_ru if lang == "ru" or not event.title_uz else event.title_uz
    description = event.description_ru if lang == "ru" or not event.description_uz else event.description_uz
    location = event.location_ru if lang == "ru" or not event.location_uz else event.location_uz
    when = event.event_date.strftime("%d.%m.%Y") + (f" {event.event_time.strftime('%H:%M')}" if event.event_time else "")
    text = f"🎯 <b>{escape(title)}</b>\n\n📅 {when}" + (f"\n📍 {escape(location)}" if location else "") + f"\n\n{escape(description)}"
    await call.message.edit_text(text, parse_mode="HTML")
    await call.answer()


async def _show_achievements(target: Message | CallbackQuery, telegram_id: int) -> None:
    user = await db.get_user_by_tg_id(telegram_id)
    if not user:
        return
    lang = _lang(user)
    items = await db.get_published_achievements()
    text = TEXTS[lang]["achievements_title"] + ("\n\n" + TEXTS[lang]["achievements_empty"] if not items else "")
    markup = achievements_kb(items, lang) if items else None
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
        await target.answer()
    else:
        await target.answer(text, reply_markup=markup, parse_mode="HTML")


@student_core_router.message(F.text.in_(ACHIEVEMENT_BUTTONS))
@student_core_router.message(Command("achievements"))
async def achievements(message: Message) -> None:
    await _show_achievements(message, message.from_user.id)


@student_core_router.callback_query(StudentCB.filter(F.action == "achievement"))
async def achievement_detail(call: CallbackQuery, callback_data: StudentCB) -> None:
    try:
        item = await db.get_achievement_by_id(int(callback_data.param or ""))
    except ValueError:
        item = None
    if not item:
        await call.answer(TEXTS["ru"]["callback_expired"], show_alert=True)
        return
    user = await db.get_user_by_tg_id(call.from_user.id)
    lang = _lang(user)
    title = item.title_ru if lang == "ru" or not item.title_uz else item.title_uz
    description = item.description_ru if lang == "ru" or not item.description_uz else item.description_uz
    text = f"🏆 <b>{escape(title)}</b>\n\n📅 {item.achievement_date.strftime('%d.%m.%Y')}\n\n{escape(description)}"
    await call.message.edit_text(text, parse_mode="HTML")
    await call.answer()


async def _show_polls(target: Message | CallbackQuery, telegram_id: int) -> None:
    user = await db.get_user_by_tg_id(telegram_id)
    if not user:
        return
    lang = _lang(user)
    polls = await db.get_active_polls()
    text = TEXTS[lang]["polls_title"] + ("\n\n" + TEXTS[lang]["polls_empty"] if not polls else "")
    markup = polls_kb(polls, lang) if polls else None
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
        await target.answer()
    else:
        await target.answer(text, reply_markup=markup, parse_mode="HTML")


@student_core_router.message(F.text.in_(POLL_BUTTONS))
@student_core_router.message(Command("polls"))
async def polls(message: Message) -> None:
    await _show_polls(message, message.from_user.id)


@student_core_router.callback_query(StudentCB.filter(F.action == "poll"))
async def poll_detail(call: CallbackQuery, callback_data: StudentCB) -> None:
    try:
        poll = await db.get_active_poll_by_id(int(callback_data.param or ""))
    except ValueError:
        poll = None
    user = await db.get_user_by_tg_id(call.from_user.id)
    if not poll or not user:
        await call.answer(TEXTS["ru"]["callback_expired"], show_alert=True)
        return
    lang = _lang(user)
    question = poll.question_ru if lang == "ru" or not poll.question_uz else poll.question_uz
    await call.message.edit_text(
        f"📊 <b>{escape(question)}</b>",
        reply_markup=poll_options_kb(poll.id, await db.get_poll_options(poll.id), lang),
        parse_mode="HTML",
    )
    await call.answer()


@student_core_router.callback_query(StudentCB.filter(F.action == "vote"))
async def vote(call: CallbackQuery, callback_data: StudentCB) -> None:
    try:
        poll_raw, option_raw = (callback_data.param or "").split("|", 1)
        poll_id, option_id = int(poll_raw), int(option_raw)
    except ValueError:
        await call.answer("Некорректный голос.", show_alert=True)
        return
    user = await db.get_user_by_tg_id(call.from_user.id)
    if not user:
        await call.answer()
        return
    lang = _lang(user)
    accepted = await db.cast_poll_vote(poll_id, option_id, user.id)
    await call.answer(TEXTS[lang]["vote_saved"] if accepted else TEXTS[lang]["vote_unavailable"], show_alert=not accepted)


@student_core_router.message(F.text.in_(REQUEST_BUTTONS))
async def requests_menu(message: Message) -> None:
    user = await db.get_user_by_tg_id(message.from_user.id)
    if user:
        lang = _lang(user)
        await message.answer(TEXTS[lang]["requests_title"], reply_markup=requests_kb(lang), parse_mode="HTML")


@student_core_router.callback_query(StudentCB.filter(F.action == "request"))
async def request_action(call: CallbackQuery, callback_data: StudentCB, state: FSMContext) -> None:
    user = await db.get_user_by_tg_id(call.from_user.id)
    if not user:
        await call.answer()
        return
    lang = _lang(user)
    kind = callback_data.param
    if kind in {"complaint", "suggestion"}:
        await state.clear()
        await state.update_data(type=kind)
        await state.set_state(FeedbackState.warning)
        await call.message.edit_text(
            TEXTS[lang]["complaint_warning"] if kind == "complaint" else TEXTS[lang]["suggestion_warning"],
            reply_markup=get_feedback_warning_kb(kind, lang), parse_mode="HTML",
        )
        await call.answer()
        return
    if kind == "question":
        await state.clear()
        await state.update_data(type=kind)
        await state.set_state(FeedbackState.text)
        await call.message.edit_text(TEXTS[lang]["ask_question"], parse_mode="HTML")
        await call.message.answer(TEXTS[lang]["btn_cancel"], reply_markup=get_feedback_cancel_kb(lang))
        await call.answer()
        return
    if kind == "mine":
        feedbacks = await db.get_user_feedbacks(user.id)
        text = TEXTS[lang]["my_feedbacks_title"] if feedbacks else TEXTS[lang]["no_my_feedbacks"]
        await call.message.edit_text(text, reply_markup=get_my_feedbacks_kb(feedbacks, lang), parse_mode="HTML")
        await call.answer()
        return
    await call.answer(TEXTS[lang]["callback_expired"], show_alert=True)


@student_core_router.message(F.text.in_(MY_CLASS_BUTTONS))
async def my_class(message: Message) -> None:
    user, school_class = await _user_and_class(message.from_user.id)
    if not user or not school_class:
        return
    lang = _lang(user)
    lessons = await db.get_lessons_for_class_day(school_class.id, date.today().weekday())
    announcements = await db.get_recent_class_announcements(school_class.id)
    announcement_text = "\n".join(f"• {escape(item.text[:140])}" for item in announcements) or TEXTS[lang]["no_announcements"]
    await message.answer(
        TEXTS[lang]["my_class_title"].format(
            class_name=escape(school_class.display_name),
            students=await db.get_students_count_by_class(school_class.display_name),
            lessons=_lessons_text(lessons, lang),
            announcements=announcement_text,
        ),
        parse_mode="HTML",
    )
