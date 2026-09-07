from aiogram.fsm.state import State, StatesGroup

class CreateNewsState(StatesGroup):
    waiting_for_title = State()
    waiting_for_content = State()
    waiting_for_confirm = State()
