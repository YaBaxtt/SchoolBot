from aiogram.fsm.state import State, StatesGroup


class StaffReplyState(StatesGroup):
    waiting_for_text = State()
    waiting_for_confirm = State()


class StaffAnnouncementState(StatesGroup):
    waiting_for_text = State()
    waiting_for_confirm = State()
