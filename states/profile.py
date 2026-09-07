from aiogram.fsm.state import State, StatesGroup


class EditProfileState(StatesGroup):
    first_name = State()
    last_name = State()
    class_grade = State()
    class_name = State()
    language = State()


class ClassChangeState(StatesGroup):
    grade = State()
    target_class = State()
    reason = State()
    confirm = State()
