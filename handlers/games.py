"""Short educational games with server-side state and one result per attempt."""

import asyncio
from html import escape
from random import sample, shuffle, randint
from time import monotonic

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import requests as db
from filters import RegisteredUserFilter
from keyboards.game_kb import (
    GameCB,
    game_intro_kb,
    game_stats_kb,
    games_home_kb,
    leaderboard_kb,
    logic_next_kb,
    logic_options_kb,
    memory_finished_kb,
    memory_grid_kb,
)
from keyboards.main_kb import get_main_menu_kb
from locales.texts import TEXTS
from states import LogicGameState, MemoryGameState


games_router = Router()
games_router.message.filter(RegisteredUserFilter())
games_router.callback_query.filter(RegisteredUserFilter())

GAME_BUTTONS = {texts["btn_games"] for texts in TEXTS.values()}
MEMORY_SIZES = {1: 3, 2: 4, 3: 5, 4: 6, 5: 7}


def _lang(user) -> str:
    return user.language if user and user.language in TEXTS else "ru"


def _sequence_text(sequence: list[int]) -> str:
    return " → ".join(str(value) for value in sequence)


async def _user(telegram_id: int):
    return await db.get_user_by_tg_id(telegram_id)


async def _show_home(target: Message | CallbackQuery, telegram_id: int, state: FSMContext | None = None) -> None:
    if state:
        await state.clear()
    user = await _user(telegram_id)
    if not user:
        if isinstance(target, CallbackQuery):
            await target.answer()
        return
    lang = _lang(user)
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(TEXTS[lang]["games_home"], reply_markup=games_home_kb(lang), parse_mode="HTML")
        await target.answer()
    else:
        await target.answer(TEXTS[lang]["games_home"], reply_markup=games_home_kb(lang), parse_mode="HTML")


@games_router.message(F.text.in_(GAME_BUTTONS))
@games_router.message(Command("games"))
async def games_home(message: Message, state: FSMContext) -> None:
    await _show_home(message, message.from_user.id, state)


@games_router.callback_query(GameCB.filter(F.action == "home"))
async def games_home_callback(call: CallbackQuery, state: FSMContext) -> None:
    await _show_home(call, call.from_user.id, state)


@games_router.callback_query(GameCB.filter(F.action == "main_menu"))
async def games_main_menu(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user = await _user(call.from_user.id)
    if user:
        lang = _lang(user)
        await call.message.edit_text(TEXTS[lang]["menu_returned"])
        await call.message.answer(TEXTS[lang]["main_menu"], reply_markup=get_main_menu_kb(lang))
    await call.answer()


@games_router.callback_query(GameCB.filter(F.action.in_({"memory_intro", "logic_intro"})))
async def game_intro(call: CallbackQuery, callback_data: GameCB, state: FSMContext) -> None:
    await state.clear()
    user = await _user(call.from_user.id)
    if not user:
        await call.answer()
        return
    lang = _lang(user)
    game_type = "memory" if callback_data.action == "memory_intro" else "logic"
    key = "memory_intro" if game_type == "memory" else "logic_intro"
    await call.message.edit_text(TEXTS[lang][key], reply_markup=game_intro_kb(game_type, lang), parse_mode="HTML")
    await call.answer()


async def _present_memory_round(call: CallbackQuery, state: FSMContext, lang: str, level: int, score: int, start_time: float) -> None:
    size = MEMORY_SIZES[level]
    sequence = sample(list(range(-9, 41)), size)
    grid = list(sequence)
    for value in sample([item for item in range(-9, 41) if item not in sequence], 9 - size):
        grid.append(value)
    shuffle(grid)
    await state.set_state(MemoryGameState.answering)
    await state.set_data({
        "game": "memory", "sequence": sequence, "grid": grid, "selected": [], "expected": 0,
        "level": level, "score": score, "start_time": start_time,
    })
    # The countdown and reveal reuse one message, so the game does not flood
    # the chat. Callback acknowledgement happens before this controlled wait.
    for number in (3, 2, 1):
        await call.message.edit_text(
            TEXTS[lang]["memory_level"].format(level=level) + f"\n\n{number}", parse_mode="HTML"
        )
        await asyncio.sleep(1)
    await call.message.edit_text(
        TEXTS[lang]["memory_numbers"].format(level=level, sequence=_sequence_text(sequence)), parse_mode="HTML"
    )
    await asyncio.sleep(max(3, 6 - level))
    await call.message.edit_text(
        TEXTS[lang]["memory_answer"].format(level=level),
        reply_markup=memory_grid_kb(grid, set()),
        parse_mode="HTML",
    )


@games_router.callback_query(GameCB.filter(F.action == "memory_start"))
async def memory_start(call: CallbackQuery, state: FSMContext) -> None:
    user = await _user(call.from_user.id)
    if not user:
        await call.answer()
        return
    await call.answer()
    await _present_memory_round(call, state, _lang(user), level=1, score=0, start_time=monotonic())


async def _finish_memory(call: CallbackQuery, state: FSMContext, user, *, completed_level: int, score: int, failed_sequence: list[int] | None = None) -> None:
    data = await state.get_data()
    duration_ms = int((monotonic() - float(data.get("start_time", monotonic()))) * 1000)
    await state.clear()
    await db.create_game_result(user.id, "memory", score, completed_level, score, duration_ms)
    lang = _lang(user)
    if failed_sequence is not None:
        text = TEXTS[lang]["memory_error"].format(sequence=_sequence_text(failed_sequence), score=score)
    else:
        text = TEXTS[lang]["memory_complete"].format(level=completed_level, score=score)
    await call.message.edit_text(text, reply_markup=memory_finished_kb(lang), parse_mode="HTML")


@games_router.callback_query(GameCB.filter(F.action == "memory_selected"))
async def memory_selected(call: CallbackQuery) -> None:
    await call.answer()


@games_router.callback_query(GameCB.filter(F.action == "memory_pick"))
async def memory_pick(call: CallbackQuery, callback_data: GameCB, state: FSMContext) -> None:
    user = await _user(call.from_user.id)
    data = await state.get_data()
    if not user or await state.get_state() != MemoryGameState.answering.state:
        await call.answer(TEXTS[_lang(user)]["callback_expired"] if user else "", show_alert=True)
        return
    try:
        value = int(callback_data.param or "")
    except ValueError:
        await call.answer(TEXTS[_lang(user)]["callback_expired"], show_alert=True)
        return
    sequence = data.get("sequence", [])
    selected = list(data.get("selected", []))
    expected = int(data.get("expected", 0))
    if value in selected:
        await call.answer()
        return
    if expected >= len(sequence) or value != sequence[expected]:
        await call.answer()
        await _finish_memory(
            call, state, user, completed_level=max(int(data.get("level", 1)) - 1, 0),
            score=int(data.get("score", 0)), failed_sequence=sequence,
        )
        return
    selected.append(value)
    score = int(data.get("score", 0)) + 1
    level = int(data.get("level", 1))
    await call.answer()
    if len(selected) == len(sequence):
        if level == max(MEMORY_SIZES):
            await _finish_memory(call, state, user, completed_level=level, score=score)
            return
        await call.message.edit_text(TEXTS[_lang(user)]["memory_level_complete"].format(level=level), parse_mode="HTML")
        await asyncio.sleep(1)
        await _present_memory_round(call, state, _lang(user), level=level + 1, score=score, start_time=float(data["start_time"]))
        return
    await state.update_data(selected=selected, expected=expected + 1, score=score)
    await call.message.edit_text(
        TEXTS[_lang(user)]["memory_next_number"].format(level=level),
        reply_markup=memory_grid_kb(list(data["grid"]), set(selected)),
        parse_mode="HTML",
    )


def _logic_question(round_number: int, lang: str) -> dict[str, object]:
    """Generate from explicit rules only, never from an ambiguous random row."""
    if round_number == 1:
        start, step = randint(1, 8), randint(2, 4)
        values = [start + step * index for index in range(4)]
        correct, explanation = values[-1] + step, TEXTS[lang]["logic_rule_add"].format(value=step)
    elif round_number == 2:
        start, step = randint(2, 10), sample((5, 10, 15), 1)[0]
        values = [start + step * index for index in range(4)]
        correct, explanation = values[-1] + step, TEXTS[lang]["logic_rule_add"].format(value=step)
    elif round_number == 3:
        start, factor = randint(1, 3), 2
        values = [start * factor**index for index in range(4)]
        correct, explanation = values[-1] * factor, TEXTS[lang]["logic_rule_multiply"].format(value=factor)
    elif round_number == 4:
        start = randint(1, 9)
        values = [start, start + 3, start + 2, start + 5, start + 4]
        correct, explanation = start + 7, TEXTS[lang]["logic_rule_alternate"]
    else:
        first, second = randint(1, 7), randint(8, 16)
        values = [first, second, first + 1, second + 2, first + 2]
        correct, explanation = second + 4, TEXTS[lang]["logic_rule_interleaved"]
    options = {correct}
    offsets = (-8, -6, -4, -3, -2, 2, 3, 4, 6, 8)
    while len(options) < 4:
        candidate = correct + sample(offsets, 1)[0]
        if candidate != correct:
            options.add(candidate)
    options = list(options)
    shuffle(options)
    return {"values": values, "correct": correct, "explanation": explanation, "options": options}


async def _show_logic_question(call: CallbackQuery, state: FSMContext, lang: str, round_number: int, correct_answers: int, start_time: float) -> None:
    question = _logic_question(round_number, lang)
    await state.set_state(LogicGameState.answering)
    await state.set_data({
        "game": "logic", "round": round_number, "correct_answers": correct_answers,
        "start_time": start_time, "question": question,
    })
    await call.message.edit_text(
        TEXTS[lang]["logic_question"].format(round=round_number, sequence=_sequence_text(question["values"])),
        reply_markup=logic_options_kb(question["options"]), parse_mode="HTML",
    )


@games_router.callback_query(GameCB.filter(F.action == "logic_start"))
async def logic_start(call: CallbackQuery, state: FSMContext) -> None:
    user = await _user(call.from_user.id)
    if not user:
        await call.answer()
        return
    await call.answer()
    await _show_logic_question(call, state, _lang(user), 1, 0, monotonic())


async def _finish_logic(call: CallbackQuery, state: FSMContext, user, correct_answers: int) -> None:
    data = await state.get_data()
    duration_ms = int((monotonic() - float(data.get("start_time", monotonic()))) * 1000)
    # A small, capped speed bonus rewards fluency without making the timer the task.
    speed_bonus = min(5, max(0, 20 - duration_ms // 1000))
    score = correct_answers * 10 + speed_bonus
    await state.clear()
    await db.create_game_result(user.id, "logic", score, 5, correct_answers, duration_ms)
    lang = _lang(user)
    await call.message.edit_text(
        TEXTS[lang]["logic_complete"].format(correct=correct_answers, score=score),
        reply_markup=memory_finished_kb(lang, "logic"), parse_mode="HTML",
    )


@games_router.callback_query(GameCB.filter(F.action == "logic_answer"))
async def logic_answer(call: CallbackQuery, callback_data: GameCB, state: FSMContext) -> None:
    user = await _user(call.from_user.id)
    data = await state.get_data()
    if not user or await state.get_state() != LogicGameState.answering.state:
        await call.answer(TEXTS[_lang(user)]["callback_expired"] if user else "", show_alert=True)
        return
    try:
        answer = int(callback_data.param or "")
    except ValueError:
        await call.answer(TEXTS[_lang(user)]["callback_expired"], show_alert=True)
        return
    question = data.get("question") or {}
    correct = int(question.get("correct", -10_000))
    round_number = int(data.get("round", 1))
    correct_answers = int(data.get("correct_answers", 0)) + int(answer == correct)
    lang = _lang(user)
    await call.answer()
    if round_number == 5:
        await _finish_logic(call, state, user, correct_answers)
        return
    await state.set_state(LogicGameState.between_questions)
    await state.update_data(correct_answers=correct_answers)
    message_key = "logic_correct" if answer == correct else "logic_wrong"
    await call.message.edit_text(
        TEXTS[lang][message_key].format(
            correct=correct, explanation=escape(str(question.get("explanation", "")))
        ),
        reply_markup=logic_next_kb(lang), parse_mode="HTML",
    )


@games_router.callback_query(GameCB.filter(F.action == "logic_next"))
async def logic_next(call: CallbackQuery, state: FSMContext) -> None:
    user = await _user(call.from_user.id)
    data = await state.get_data()
    if not user or await state.get_state() != LogicGameState.between_questions.state:
        await call.answer(TEXTS[_lang(user)]["callback_expired"] if user else "", show_alert=True)
        return
    await call.answer()
    await _show_logic_question(
        call, state, _lang(user), int(data["round"]) + 1, int(data["correct_answers"]), float(data["start_time"])
    )


@games_router.callback_query(GameCB.filter(F.action == "stats"))
async def game_stats(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user = await _user(call.from_user.id)
    if not user:
        await call.answer()
        return
    stats = await db.get_game_stats_for_user(user.id)
    memory, logic = stats.get("memory", {}), stats.get("logic", {})
    lang = _lang(user)
    await call.message.edit_text(
        TEXTS[lang]["game_personal_stats"].format(
            memory_level=memory.get("best_level", 0), memory_score=memory.get("best_score", 0), memory_games=memory.get("games", 0),
            logic_score=logic.get("best_score", 0), logic_correct=logic.get("best_correct", 0), logic_games=logic.get("games", 0),
        ),
        reply_markup=game_stats_kb(lang), parse_mode="HTML",
    )
    await call.answer()


@games_router.callback_query(GameCB.filter(F.action == "leaderboard"))
async def game_leaderboard(call: CallbackQuery, callback_data: GameCB) -> None:
    user = await _user(call.from_user.id)
    try:
        game_type, period = (callback_data.param or "").split("|", 1)
    except ValueError:
        game_type = period = ""
    if not user or game_type not in {"memory", "logic"} or period not in {"week", "all"}:
        await call.answer(TEXTS[_lang(user)]["callback_expired"] if user else "", show_alert=True)
        return
    results = await db.get_game_leaderboard(game_type, weekly=period == "week")
    lang = _lang(user)
    if results:
        rank_marks = ("🥇", "🥈", "🥉")
        def participant_name(result) -> str:
            full_name = f"{escape(result.user.first_name)} {escape(result.user.last_name)}"
            username = (result.user.telegram_username or "").lstrip("@")
            if result.user.public_profile_enabled and username.replace("_", "").isalnum():
                return f'<a href="https://t.me/{username}">{full_name}</a>'
            return full_name
        rows = "\n".join(
            f"{rank_marks[index - 1] if index <= 3 else f'{index}.'} {participant_name(result)} · "
            f"{escape(result.user.class_name)} — <b>{result.score}</b>"
            for index, result in enumerate(results, 1)
        )
    else:
        rows = TEXTS[lang]["game_leaderboard_empty"]
    settings = await db.get_school_settings()
    prize_text = ""
    if settings and settings.show_prize_message:
        prize_text = settings.leaderboard_prize_text_ru if lang == "ru" else settings.leaderboard_prize_text_uz
        prize_text = prize_text or TEXTS[lang]["leaderboard_prize_default"]
    title = f"{TEXTS[lang][f'game_{game_type}']} — {TEXTS[lang][f'leaderboard_{period}']}"
    await call.message.edit_text(
        TEXTS[lang]["game_leaderboard"].format(title=title, rows=rows) + (f"\n\n{prize_text}" if prize_text else ""),
        reply_markup=leaderboard_kb(lang), parse_mode="HTML",
    )
    await call.answer()
