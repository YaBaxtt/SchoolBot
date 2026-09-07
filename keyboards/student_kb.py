from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.models import Achievement, Poll, PollOption, SchoolEvent
from locales.texts import TEXTS


class StudentCB(CallbackData, prefix="student"):
    action: str
    param: str | None = None


WEEKDAYS = {
    "ru": ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб"),
    "uz": ("Du", "Se", "Ch", "Pa", "Ju", "Sh"),
}


def schedule_days_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=label, callback_data=StudentCB(action="schedule_day", param=str(day)).pack())
        for day, label in enumerate(WEEKDAYS.get(lang, WEEKDAYS["ru"]))
    ]])


def requests_kb(lang: str) -> InlineKeyboardMarkup:
    text = TEXTS.get(lang, TEXTS["ru"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text["btn_complaint"], callback_data=StudentCB(action="request", param="complaint").pack())],
        [InlineKeyboardButton(text=text["btn_suggestion"], callback_data=StudentCB(action="request", param="suggestion").pack())],
        [InlineKeyboardButton(text=text["btn_question"], callback_data=StudentCB(action="request", param="question").pack())],
        [InlineKeyboardButton(text=text["btn_my_feedbacks"], callback_data=StudentCB(action="request", param="mine").pack())],
    ])


def event_list_kb(events: list[SchoolEvent], lang: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        text=f"{event.event_date.strftime('%d.%m')} • {event.title_ru if lang == 'ru' or not event.title_uz else event.title_uz}",
        callback_data=StudentCB(action="event", param=str(event.id)).pack(),
    )] for event in events]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def achievements_kb(items: list[Achievement], lang: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        text=f"{item.achievement_date.strftime('%d.%m')} • {item.title_ru if lang == 'ru' or not item.title_uz else item.title_uz}",
        callback_data=StudentCB(action="achievement", param=str(item.id)).pack(),
    )] for item in items]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def polls_kb(polls: list[Poll], lang: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        text=poll.question_ru if lang == "ru" or not poll.question_uz else poll.question_uz,
        callback_data=StudentCB(action="poll", param=str(poll.id)).pack(),
    )] for poll in polls]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def poll_options_kb(poll_id: int, options: list[PollOption], lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=option.text_ru if lang == "ru" or not option.text_uz else option.text_uz,
            callback_data=StudentCB(action="vote", param=f"{poll_id}|{option.id}").pack(),
        )
    ] for option in options])
