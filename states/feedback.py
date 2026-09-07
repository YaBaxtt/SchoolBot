from aiogram.fsm.state import State, StatesGroup


class FeedbackState(StatesGroup):
    type = State()
    warning = State()
    text = State()
    confirm = State()


class AdminReplyState(StatesGroup):
    waiting_for_reply = State()
    waiting_for_confirm = State()


class BroadcastState(StatesGroup):
    waiting_for_text = State()
    waiting_for_confirm = State()


class AddSchoolClassState(StatesGroup):
    waiting_for_letter = State()
    waiting_for_confirm = State()


class ClassCuratorState(StatesGroup):
    waiting_for_user_code = State()
    waiting_for_candidate_confirm = State()
    waiting_for_promotion_confirm = State()
    waiting_for_remove_confirm = State()
