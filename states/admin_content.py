from aiogram.fsm.state import State, StatesGroup


class EventCreateState(StatesGroup):
    title_ru = State()
    title_uz = State()
    description_ru = State()
    description_uz = State()
    event_date = State()
    event_time = State()
    location_ru = State()
    location_uz = State()
    target_class = State()
    photo = State()


class AchievementCreateState(StatesGroup):
    title_ru = State()
    title_uz = State()
    description_ru = State()
    description_uz = State()
    achievement_date = State()
    student_name = State()
    category = State()
    photo = State()


class LessonCreateState(StatesGroup):
    number = State()
    subject = State()
    start_time = State()
    room = State()
    teacher_name = State()


class PollCreateState(StatesGroup):
    question_ru = State()
    question_uz = State()
    options = State()


class ContentEditState(StatesGroup):
    value = State()
