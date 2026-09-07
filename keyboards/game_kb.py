from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from locales.texts import TEXTS


class GameCB(CallbackData, prefix="game"):
    action: str
    param: str | None = None


def _text(lang: str) -> dict[str, str]:
    return TEXTS.get(lang, TEXTS["ru"])


def games_home_kb(lang: str) -> InlineKeyboardMarkup:
    text = _text(lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text["game_memory"], callback_data=GameCB(action="memory_intro").pack())],
        [InlineKeyboardButton(text=text["game_logic"], callback_data=GameCB(action="logic_intro").pack())],
        [InlineKeyboardButton(text=text["game_stats"], callback_data=GameCB(action="stats").pack())],
        [InlineKeyboardButton(text=text["btn_back_to_menu"], callback_data=GameCB(action="main_menu").pack())],
    ])


def game_intro_kb(game_type: str, lang: str) -> InlineKeyboardMarkup:
    text = _text(lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text["game_play"], callback_data=GameCB(action=f"{game_type}_start").pack())],
        [InlineKeyboardButton(text=text["game_back"], callback_data=GameCB(action="home").pack())],
    ])


def memory_grid_kb(grid: list[int], selected: set[int]) -> InlineKeyboardMarkup:
    buttons = []
    for value in grid:
        if value in selected:
            buttons.append(InlineKeyboardButton(text="✓", callback_data=GameCB(action="memory_selected").pack()))
        else:
            buttons.append(
                InlineKeyboardButton(text=str(value), callback_data=GameCB(action="memory_pick", param=str(value)).pack())
            )
    return InlineKeyboardMarkup(inline_keyboard=[buttons[index:index + 3] for index in range(0, 9, 3)])


def memory_finished_kb(lang: str, game_type: str = "memory") -> InlineKeyboardMarkup:
    text = _text(lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text["game_retry"], callback_data=GameCB(action=f"{game_type}_start").pack())],
        [InlineKeyboardButton(text=text["game_stats"], callback_data=GameCB(action="stats").pack())],
        [InlineKeyboardButton(text=text["game_back"], callback_data=GameCB(action="home").pack())],
    ])


def logic_options_kb(options: list[int]) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=str(value), callback_data=GameCB(action="logic_answer", param=str(value)).pack())
        for value in options
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons[:2], buttons[2:]])


def logic_next_kb(lang: str) -> InlineKeyboardMarkup:
    text = _text(lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text["logic_next"], callback_data=GameCB(action="logic_next").pack())],
        [InlineKeyboardButton(text=text["game_back"], callback_data=GameCB(action="home").pack())],
    ])


def game_stats_kb(lang: str) -> InlineKeyboardMarkup:
    text = _text(lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"🔥 {text['game_memory']}", callback_data=GameCB(action="leaderboard", param="memory|week").pack()),
            InlineKeyboardButton(text=f"🏆 {text['game_memory']}", callback_data=GameCB(action="leaderboard", param="memory|all").pack()),
        ],
        [
            InlineKeyboardButton(text=f"🔥 {text['game_logic']}", callback_data=GameCB(action="leaderboard", param="logic|week").pack()),
            InlineKeyboardButton(text=f"🏆 {text['game_logic']}", callback_data=GameCB(action="leaderboard", param="logic|all").pack()),
        ],
        [InlineKeyboardButton(text=text["game_back"], callback_data=GameCB(action="home").pack())],
    ])


def leaderboard_kb(lang: str) -> InlineKeyboardMarkup:
    text = _text(lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text["game_back"], callback_data=GameCB(action="stats").pack())],
    ])
