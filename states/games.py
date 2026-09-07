from aiogram.fsm.state import State, StatesGroup


class MemoryGameState(StatesGroup):
    answering = State()


class LogicGameState(StatesGroup):
    answering = State()
    between_questions = State()
