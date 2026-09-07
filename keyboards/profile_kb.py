from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from locales.texts import TEXTS
from database.models import SchoolClass


def get_profile_main_kb(lang: str = "ru", public_profile_enabled: bool = False) -> InlineKeyboardMarkup:
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=lang_texts["btn_edit_language"],
                    callback_data="edit_field_language"
                )
            ],
            [
                InlineKeyboardButton(
                    text=lang_texts["btn_change_class_request"],
                    callback_data="class_change_start"
                )
            ],
            [
                InlineKeyboardButton(
                    text=lang_texts["btn_public_profile_disable"] if public_profile_enabled else lang_texts["btn_public_profile_enable"],
                    callback_data="profile_public_toggle"
                )
            ],
            [
                InlineKeyboardButton(
                    text=lang_texts["btn_back_to_menu"],
                    callback_data="profile_main_menu"
                )
            ],
        ]
    )


def get_edit_fields_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=lang_texts["btn_edit_first_name"],
                    callback_data="edit_field_first_name"
                ),
                InlineKeyboardButton(
                    text=lang_texts["btn_edit_last_name"],
                    callback_data="edit_field_last_name"
                )
            ],
            [
                InlineKeyboardButton(
                    text=lang_texts["btn_edit_class"],
                    callback_data="edit_field_class_name"
                ),
                InlineKeyboardButton(
                    text=lang_texts["btn_edit_language"],
                    callback_data="edit_field_language"
                )
            ],
            [
                InlineKeyboardButton(
                    text=lang_texts["btn_cancel_edit"],
                    callback_data="edit_field_back"
                )
            ]
        ]
    )


def get_edit_language_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Русский 🇷🇺", callback_data="change_lang_ru"),
                InlineKeyboardButton(text="O'zbekcha 🇺🇿", callback_data="change_lang_uz")
            ],
            [
                InlineKeyboardButton(
                    text=lang_texts["btn_cancel_edit"],
                    callback_data="edit_field_back"
                )
            ],
        ]
    )


def get_class_change_grades_kb(grades: list[int], lang: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=str(grade), callback_data=f"class_change_grade_{grade}")
        for grade in grades
    ]
    rows = [buttons[index:index + 3] for index in range(0, len(buttons), 3)]
    rows.append([InlineKeyboardButton(text=TEXTS.get(lang, TEXTS["ru"])["btn_cancel_edit"], callback_data="class_change_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_class_change_classes_kb(classes: list[SchoolClass], lang: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        text=f"🏫 {school_class.display_name}", callback_data=f"class_change_select_{school_class.id}"
    )] for school_class in classes]
    rows.append([InlineKeyboardButton(text=TEXTS.get(lang, TEXTS["ru"])["btn_cancel_edit"], callback_data="class_change_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_class_change_reason_kb(lang: str) -> InlineKeyboardMarkup:
    text = TEXTS.get(lang, TEXTS["ru"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text["class_change_skip_reason"], callback_data="class_change_skip_reason")],
        [InlineKeyboardButton(text=text["btn_cancel_edit"], callback_data="class_change_cancel")],
    ])


def get_class_change_confirm_kb(lang: str) -> InlineKeyboardMarkup:
    text = TEXTS.get(lang, TEXTS["ru"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text["class_change_submit"], callback_data="class_change_submit")],
        [InlineKeyboardButton(text=text["btn_cancel_edit"], callback_data="class_change_cancel")],
    ])


def get_edit_cancel_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=lang_texts["btn_cancel_edit"],
                    callback_data="edit_field_back"
                )
            ]
        ]
    )


def get_profile_class_grades_kb(grades: list[int], lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = [InlineKeyboardButton(text=str(grade), callback_data=f"profile_class_grade_{grade}") for grade in grades]
    rows = [buttons[index:index + 3] for index in range(0, len(buttons), 3)]
    rows.append([InlineKeyboardButton(text=TEXTS.get(lang, TEXTS["ru"])["btn_cancel_edit"], callback_data="edit_field_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_profile_classes_kb(classes: list[SchoolClass], lang: str = "ru") -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        text=f"🏫 {school_class.display_name}", callback_data=f"profile_class_select_{school_class.id}"
    )] for school_class in classes]
    rows.append([InlineKeyboardButton(text=TEXTS.get(lang, TEXTS["ru"])["btn_cancel_edit"], callback_data="edit_field_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
