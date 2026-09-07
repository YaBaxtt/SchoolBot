from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from locales.texts import TEXTS
from database.models import Feedback


def get_confirm_feedback_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=lang_texts["btn_confirm_yes"],
                    callback_data="feedback_confirm_yes"
                ),
                InlineKeyboardButton(
                    text=lang_texts["btn_confirm_no"],
                    callback_data="feedback_confirm_no"
                )
            ]
        ]
    )


def get_feedback_warning_kb(feedback_type: str, lang: str = "ru") -> InlineKeyboardMarkup:
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    continue_key = "btn_complaint_continue" if feedback_type == "complaint" else "btn_suggestion_continue"
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=lang_texts[continue_key], callback_data="feedback_warning_continue"),
            InlineKeyboardButton(text=lang_texts["btn_cancel"], callback_data="feedback_warning_cancel"),
        ]]
    )


def get_my_feedbacks_kb(feedbacks: list[Feedback], lang: str = "ru") -> InlineKeyboardMarkup:
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    rows = [[InlineKeyboardButton(
        text=lang_texts["my_feedback_item"].format(
            type=lang_texts.get(f"type_{feedback.type}", feedback.type),
            id=feedback.id,
            status=lang_texts.get(f"status_{feedback.status}", feedback.status),
        ),
        callback_data=f"my_feedback_{feedback.id}",
    )] for feedback in feedbacks]
    rows.append([InlineKeyboardButton(text=lang_texts["btn_back_to_menu"], callback_data="my_feedbacks_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_my_feedback_detail_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=lang_texts["btn_back_to_feedbacks"], callback_data="my_feedbacks_back")],
        [InlineKeyboardButton(text=lang_texts["btn_back_to_menu"], callback_data="my_feedbacks_main_menu")],
    ])
