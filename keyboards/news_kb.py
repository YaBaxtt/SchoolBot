from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.models import News
from locales.texts import TEXTS


def get_news_list_kb(news_list: list[News], page: int, total_count: int, per_page: int = 5, lang: str = "ru") -> InlineKeyboardMarkup:
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    keyboard = []

    for item in news_list:
        keyboard.append([
            InlineKeyboardButton(
                text=f"📌 {item.title}",
                callback_data=f"view_news_{item.id}_{page}"
            )
        ])

    nav_row = []
    if page > 0:
        nav_row.append(
            InlineKeyboardButton(
                text=lang_texts["btn_prev_page"],
                callback_data=f"news_page_{page - 1}"
            )
        )
    if (page + 1) * per_page < total_count:
        nav_row.append(
            InlineKeyboardButton(
                text=lang_texts["btn_next_page"],
                callback_data=f"news_page_{page + 1}"
            )
        )

    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([
        InlineKeyboardButton(
            text=lang_texts["btn_back_to_menu"],
            callback_data="news_main_menu"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_to_news_kb(page: int = 0, lang: str = "ru") -> InlineKeyboardMarkup:
    lang_texts = TEXTS.get(lang, TEXTS["ru"])
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=lang_texts["btn_back_to_list"],
                    callback_data=f"news_page_{page}"
                )
            ],
            [
                InlineKeyboardButton(
                    text=lang_texts["btn_back_to_menu"],
                    callback_data="news_main_menu"
                )
            ],
        ]
    )
