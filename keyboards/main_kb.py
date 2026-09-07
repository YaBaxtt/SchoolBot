from database.models import SchoolClass
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from locales.texts import TEXTS


def get_language_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru"),
                InlineKeyboardButton(text="O'zbekcha 🇺🇿", callback_data="lang_uz")
            ]
        ]
    )


def get_main_menu_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=lang_texts["btn_news"])],
            [
                KeyboardButton(text=lang_texts["btn_schedule"]),
            ],
            [
                KeyboardButton(text=lang_texts["btn_events"]),
                KeyboardButton(text=lang_texts["btn_achievements"]),
            ],
            [
                KeyboardButton(text=lang_texts["btn_games"]),
                KeyboardButton(text=lang_texts["btn_polls"]),
            ],
            [
                KeyboardButton(text=lang_texts["btn_requests"]),
                KeyboardButton(text=lang_texts["btn_profile"]),
            ],
            [KeyboardButton(text=lang_texts["btn_help"])],
        ],
        resize_keyboard=True
    )


def get_feedback_cancel_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=lang_texts["btn_cancel"])]] ,
        resize_keyboard=True,
    )


def get_help_back_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=lang_texts["btn_back_to_menu"], callback_data="help_main_menu")
        ]]
    )


def get_registration_grades_kb(grades: list[int], lang: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=str(grade), callback_data=f"reg_grade_{grade}")
        for grade in grades
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[buttons[index:index + 3] for index in range(0, len(buttons), 3)]
    )


def get_registration_name_confirm_kb(lang: str) -> InlineKeyboardMarkup:
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=lang_texts["btn_confirm_name"], callback_data="reg_name_confirm"),
            InlineKeyboardButton(text=lang_texts["btn_edit_name"], callback_data="reg_name_edit"),
        ]]
    )


def get_registration_classes_kb(
    classes: list[SchoolClass], grade: int, lang: str
) -> InlineKeyboardMarkup:
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    rows = [
        [
            InlineKeyboardButton(
                text=f"🏫 {school_class.display_name}",
                callback_data=f"reg_class_{school_class.id}",
            )
        ]
        for school_class in classes
    ]
    rows.append([
        InlineKeyboardButton(
            text=lang_texts["btn_back"], callback_data="reg_classes_back"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)
