from aiogram.fsm.state import State, StatesGroup


class RegistrationState(StatesGroup):
    language = State()
    first_name = State()
    last_name = State()
    confirm_name = State()
    grade = State()
    class_name = State()
