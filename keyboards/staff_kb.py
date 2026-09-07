from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.models import Feedback, SchoolClass, User


class StaffCB(CallbackData, prefix="staff"):
    action: str
    # Keep empty action parameters compatible with aiogram 3.18 and 3.30.
    param: str | None = None


LABELS = {
    "ru": {
        "classes": "🏫 Мои классы", "complaint": "📩 Жалобы", "suggestion": "💡 Предложения",
        "applications": "📋 Заявки классов",
        "announcement": "📣 Объявление классу", "profile": "👤 Мой профиль", "help": "❓ Справка",
        "schedule": "📅 Расписание класса", "stats": "📊 Статистика класса",
        "new": "🟢 Новые", "in_progress": "🟡 В работе", "closed": "🔴 Закрытые",
        "back": "⬅️ Назад", "main": "⬅️ В панель", "reply": "✉️ Ответить",
        "work": "🟡 В работу", "close": "✅ Закрыть", "send": "✅ Отправить", "cancel": "❌ Отмена",
    },
    "uz": {
        "classes": "🏫 Mening sinflarim", "complaint": "📩 Shikoyatlar", "suggestion": "💡 Takliflar",
        "applications": "📋 Sinf arizalari",
        "announcement": "📣 Sinfga e'lon", "profile": "👤 Mening profilim", "help": "❓ Yordam",
        "schedule": "📅 Sinf jadvali", "stats": "📊 Sinf statistikasi",
        "new": "🟢 Yangi", "in_progress": "🟡 Jarayonda", "closed": "🔴 Yopilgan",
        "back": "⬅️ Ortga", "main": "⬅️ Panelga", "reply": "✉️ Javob berish",
        "work": "🟡 Ishga olish", "close": "✅ Yopish", "send": "✅ Yuborish", "cancel": "❌ Bekor qilish",
    },
}


def _labels(lang: str) -> dict[str, str]:
    return LABELS.get(lang, LABELS["ru"])


def get_staff_main_kb(lang: str) -> InlineKeyboardMarkup:
    text = _labels(lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text["classes"], callback_data=StaffCB(action="classes").pack())],
        [InlineKeyboardButton(text=text["applications"], callback_data=StaffCB(action="applications").pack())],
        [
            InlineKeyboardButton(text=text["suggestion"], callback_data=StaffCB(action="feedback_kind", param="suggestion").pack()),
        ],
        [InlineKeyboardButton(text=text["announcement"], callback_data=StaffCB(action="announcement").pack())],
        [
            InlineKeyboardButton(text=text["schedule"], callback_data=StaffCB(action="schedule").pack()),
            InlineKeyboardButton(text=text["stats"], callback_data=StaffCB(action="stats").pack()),
        ],
        [
            InlineKeyboardButton(text=text["profile"], callback_data=StaffCB(action="profile").pack()),
            InlineKeyboardButton(text=text["help"], callback_data=StaffCB(action="help").pack()),
        ],
    ])


def get_staff_applications_kb(users: list[User], lang: str) -> InlineKeyboardMarkup:
    text = _labels(lang)
    rows = [[InlineKeyboardButton(
        text=f"👤 {user.first_name} {user.last_name} — {user.class_name}",
        callback_data=StaffCB(action="application_view", param=str(user.telegram_id)).pack(),
    )] for user in users]
    rows.append([InlineKeyboardButton(text=text["main"], callback_data=StaffCB(action="main").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_staff_application_card_kb(user: User, lang: str) -> InlineKeyboardMarkup:
    text = _labels(lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять" if lang == "ru" else "✅ Qabul qilish", callback_data=StaffCB(action="application_accept", param=str(user.telegram_id)).pack()),
            InlineKeyboardButton(text="❌ Отклонить" if lang == "ru" else "❌ Rad etish", callback_data=StaffCB(action="application_reject", param=str(user.telegram_id)).pack()),
        ],
        [InlineKeyboardButton(text=text["back"], callback_data=StaffCB(action="applications").pack())],
    ])


def get_staff_classes_kb(classes: list[SchoolClass], counts: dict[int, int], lang: str) -> InlineKeyboardMarkup:
    text = _labels(lang)
    rows = [[InlineKeyboardButton(
        text=f"🏫 {school_class.display_name} — {counts.get(school_class.id, 0)}",
        callback_data=StaffCB(action="class_students", param=f"{school_class.id}|1").pack(),
    )] for school_class in classes]
    rows.append([InlineKeyboardButton(text=text["main"], callback_data=StaffCB(action="main").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_staff_students_kb(
    users: list[User], class_id: int, page: int, total_pages: int, lang: str
) -> InlineKeyboardMarkup:
    text = _labels(lang)
    rows = [[InlineKeyboardButton(
        text=f"👤 {user.first_name} {user.last_name}",
        callback_data=StaffCB(action="student", param=f"{user.telegram_id}|{class_id}|{page}").pack(),
    )] for user in users]
    navigation: list[InlineKeyboardButton] = []
    if page > 1:
        navigation.append(InlineKeyboardButton(
            text="⬅️", callback_data=StaffCB(action="class_students", param=f"{class_id}|{page - 1}").pack()
        ))
    navigation.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data=StaffCB(action="ignore").pack()))
    if page < total_pages:
        navigation.append(InlineKeyboardButton(
            text="➡️", callback_data=StaffCB(action="class_students", param=f"{class_id}|{page + 1}").pack()
        ))
    rows.append(navigation)
    rows.append([InlineKeyboardButton(text=text["back"], callback_data=StaffCB(action="classes").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_staff_feedback_status_kb(feedback_type: str, lang: str) -> InlineKeyboardMarkup:
    text = _labels(lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=text["new"], callback_data=StaffCB(action="feedback_status", param=f"{feedback_type}|new").pack()),
            InlineKeyboardButton(text=text["in_progress"], callback_data=StaffCB(action="feedback_status", param=f"{feedback_type}|in_progress").pack()),
        ],
        [InlineKeyboardButton(text=text["closed"], callback_data=StaffCB(action="feedback_status", param=f"{feedback_type}|closed").pack())],
        [InlineKeyboardButton(text=text["main"], callback_data=StaffCB(action="main").pack())],
    ])


def get_staff_feedback_list_kb(feedbacks: list[Feedback], feedback_type: str, lang: str) -> InlineKeyboardMarkup:
    text = _labels(lang)
    rows = [[InlineKeyboardButton(
        text=f"#{feedback.id} — {feedback.user.class_name if feedback.user else '—'}",
        callback_data=StaffCB(action="feedback", param=str(feedback.id)).pack(),
    )] for feedback in feedbacks]
    rows.append([InlineKeyboardButton(
        text=text["back"], callback_data=StaffCB(action="feedback_kind", param=feedback_type).pack()
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_staff_feedback_card_kb(feedback: Feedback, lang: str) -> InlineKeyboardMarkup:
    text = _labels(lang)
    rows: list[list[InlineKeyboardButton]] = []
    if feedback.status == "new":
        rows.append([InlineKeyboardButton(text=text["work"], callback_data=StaffCB(action="feedback_status_set", param=f"{feedback.id}|in_progress").pack())])
    if feedback.status != "closed":
        rows.append([InlineKeyboardButton(text=text["close"], callback_data=StaffCB(action="feedback_status_set", param=f"{feedback.id}|closed").pack())])
    rows.append([InlineKeyboardButton(text=text["reply"], callback_data=StaffCB(action="feedback_reply", param=str(feedback.id)).pack())])
    rows.append([InlineKeyboardButton(text=text["back"], callback_data=StaffCB(action="feedback_kind", param=feedback.type).pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_staff_announcement_classes_kb(classes: list[SchoolClass], lang: str) -> InlineKeyboardMarkup:
    text = _labels(lang)
    rows = [[InlineKeyboardButton(
        text=f"🏫 {school_class.display_name}", callback_data=StaffCB(action="announcement_class", param=str(school_class.id)).pack()
    )] for school_class in classes]
    rows.append([InlineKeyboardButton(text=text["main"], callback_data=StaffCB(action="main").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_staff_class_action_kb(classes: list[SchoolClass], action: str, lang: str) -> InlineKeyboardMarkup:
    text = _labels(lang)
    rows = [[InlineKeyboardButton(
        text=f"🏫 {school_class.display_name}", callback_data=StaffCB(action=action, param=str(school_class.id)).pack()
    )] for school_class in classes]
    rows.append([InlineKeyboardButton(text=text["main"], callback_data=StaffCB(action="main").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_staff_confirm_kb(kind: str, lang: str) -> InlineKeyboardMarkup:
    text = _labels(lang)
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=text["send"], callback_data=StaffCB(action=f"{kind}_send").pack()),
        InlineKeyboardButton(text=text["cancel"], callback_data=StaffCB(action=f"{kind}_cancel").pack()),
    ]])


def get_staff_cancel_kb(kind: str, lang: str) -> InlineKeyboardMarkup:
    text = _labels(lang)
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=text["cancel"], callback_data=StaffCB(action=f"{kind}_cancel").pack())
    ]])
