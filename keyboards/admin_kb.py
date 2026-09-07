from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from database.models import Feedback, SchoolClass, User


class AdminCB(CallbackData, prefix="admin"):
    action: str
    # aiogram 3.18 unpacks the empty final segment in ``admin:users:`` as
    # None.  ``str = ''`` rejects that value before the handler can run,
    # causing the protected callback to fall through to access-denied.
    param: str | None = None


def get_admin_main_kb(can_view_complaints: bool = False) -> InlineKeyboardMarkup:
    """Build an admin menu without exposing SuperAdmin-only complaints."""
    rows = [
            [
                InlineKeyboardButton(text="👥 Пользователи", callback_data=AdminCB(action="users").pack()),
                InlineKeyboardButton(text="📝 Заявки", callback_data=AdminCB(action="applications").pack())
            ],
            [
                InlineKeyboardButton(text="🏫 Классы", callback_data=AdminCB(action="classes").pack()),
                InlineKeyboardButton(text="🔄 Смена класса", callback_data=AdminCB(action="class_changes").pack()),
            ],
            [
                InlineKeyboardButton(text="📰 Новости", callback_data=AdminCB(action="news").pack()),
                InlineKeyboardButton(text="📅 Расписание", callback_data=AdminCB(action="schedule").pack()),
            ],
            [
                InlineKeyboardButton(text="🎯 Мероприятия", callback_data=AdminCB(action="events").pack()),
                InlineKeyboardButton(text="🏆 Достижения", callback_data=AdminCB(action="achievements").pack()),
            ],
            [
                InlineKeyboardButton(text="📊 Опросы", callback_data=AdminCB(action="polls").pack()),
            ],
            [
                InlineKeyboardButton(text="💡 Предложения", callback_data=AdminCB(action="suggestions").pack()),
                InlineKeyboardButton(text="📨 Рассылка", callback_data=AdminCB(action="broadcast").pack())
            ],
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data=AdminCB(action="stats").pack()),
                InlineKeyboardButton(text="⚙️ Настройки", callback_data=AdminCB(action="settings").pack()),
            ],
            [
                InlineKeyboardButton(text="❓ Справка", callback_data=AdminCB(action="help").pack())
            ]
    ]
    if can_view_complaints:
        rows.insert(1, [InlineKeyboardButton(text="📩 Жалобы", callback_data=AdminCB(action="complaints").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_back_to_admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data=AdminCB(action="main").pack())]
        ]
    )


def get_news_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Создать новость", callback_data=AdminCB(action="news_create").pack()),
                InlineKeyboardButton(text="📋 Список новостей", callback_data=AdminCB(action="news_list").pack())
            ],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCB(action="main").pack())]
        ]
    )


def get_news_publish_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Опубликовать", callback_data=AdminCB(action="news_publish").pack()),
                InlineKeyboardButton(text="❌ Отмена", callback_data=AdminCB(action="news_cancel").pack()),
            ]
        ]
    )


def get_settings_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏫 Управление классами", callback_data=AdminCB(action="classes").pack())],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCB(action="main").pack())],
        ]
    )


def get_classes_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить класс", callback_data=AdminCB(action="class_add").pack())],
            [InlineKeyboardButton(text="📋 Все классы", callback_data=AdminCB(action="classes_list").pack())],
            [InlineKeyboardButton(text="🗑 Управление классами", callback_data=AdminCB(action="classes_manage").pack())],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCB(action="settings").pack())],
        ]
    )


def get_grade_choice_kb(action: str) -> InlineKeyboardMarkup:
    grades = list(range(11, 0, -1))
    buttons = [
        InlineKeyboardButton(text=str(grade), callback_data=AdminCB(action=action, param=str(grade)).pack())
        for grade in grades
    ]
    rows = [buttons[index:index + 3] for index in range(0, len(buttons), 3)]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCB(action="classes").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_class_create_confirm_kb(grade: int, letter: str) -> InlineKeyboardMarkup:
    param = f"{grade}|{letter}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Создать", callback_data=AdminCB(action="class_create_confirm", param=param).pack()
                ),
                InlineKeyboardButton(
                    text="❌ Отмена", callback_data=AdminCB(action="class_create_cancel").pack()
                ),
            ]
        ]
    )


def get_class_creation_cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data=AdminCB(action="class_create_cancel").pack())]
        ]
    )


def get_classes_list_kb(classes: list[SchoolClass], back_action: str = "classes") -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{'🟢' if school_class.is_active else '🔴'} {school_class.display_name}",
                callback_data=AdminCB(action="class_view", param=str(school_class.id)).pack(),
            )
        ]
        for school_class in classes
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCB(action=back_action).pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_class_detail_kb(school_class: SchoolClass) -> InlineKeyboardMarkup:
    toggle_text = "🔴 Отключить класс" if school_class.is_active else "🟢 Включить класс"
    curator_action = "class_curator_change" if getattr(school_class, "curator_user_id", None) else "class_curator_assign"
    curator_text = "✏️ Сменить классного руководителя" if getattr(school_class, "curator_user_id", None) else "👨‍🏫 Назначить классного руководителя"
    rows = [
        [
            InlineKeyboardButton(
                text=curator_text,
                callback_data=AdminCB(action=curator_action, param=str(school_class.id)).pack(),
            )
        ]
    ]
    if getattr(school_class, "curator_user_id", None):
        rows.append([
            InlineKeyboardButton(
                text="🧹 Снять классного руководителя",
                callback_data=AdminCB(action="class_curator_remove", param=str(school_class.id)).pack(),
            )
        ])
    rows.extend([
        [
            InlineKeyboardButton(
                text=toggle_text,
                callback_data=AdminCB(action="class_toggle", param=str(school_class.id)).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text="🗑 Удалить",
                callback_data=AdminCB(action="class_delete", param=str(school_class.id)).pack(),
            )
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCB(action="classes_manage").pack())],
    ])
    return InlineKeyboardMarkup(
        inline_keyboard=rows
    )


def get_class_curator_confirm_kb(action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=AdminCB(action=action).pack()),
        InlineKeyboardButton(text="❌ Отмена", callback_data=AdminCB(action="class_curator_cancel").pack()),
    ]])


def get_class_delete_confirm_kb(school_class: SchoolClass) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить",
                    callback_data=AdminCB(action="class_delete_confirm", param=str(school_class.id)).pack(),
                ),
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=AdminCB(action="class_delete_cancel", param=str(school_class.id)).pack(),
                ),
            ]
        ]
    )


def get_class_change_requests_kb(requests) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        text=f"🔄 {request.user.first_name} {request.user.last_name}: {request.old_class_name} → {request.target_class.display_name}",
        callback_data=AdminCB(action="class_change_view", param=str(request.id)).pack(),
    )] for request in requests]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCB(action="main").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_class_change_decision_kb(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="✅ Одобрить", callback_data=AdminCB(action="class_change_decision", param=f"{request_id}|approve").pack()
        ),
        InlineKeyboardButton(
            text="❌ Отклонить", callback_data=AdminCB(action="class_change_decision", param=f"{request_id}|reject").pack()
        ),
    ], [InlineKeyboardButton(text="⬅️ К заявкам", callback_data=AdminCB(action="class_changes").pack())]])


def get_content_menu_kb(kind: str) -> InlineKeyboardMarkup:
    labels = {
        "events": ("➕ Добавить мероприятие", "📋 Список мероприятий"),
        "achievements": ("➕ Добавить достижение", "📋 Список достижений"),
        "polls": ("➕ Создать опрос", "📋 Список опросов"),
    }
    add_label, list_label = labels[kind]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=add_label, callback_data=AdminCB(action="content_create", param=kind).pack())],
        [InlineKeyboardButton(text=list_label, callback_data=AdminCB(action="content_list", param=kind).pack())],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCB(action="main").pack())],
    ])


def get_content_list_kb(kind: str, items) -> InlineKeyboardMarkup:
    label_attr = "title_ru" if kind in {"events", "achievements"} else "question_ru"
    rows = []
    for item in items:
        is_visible = item.is_published if kind in {"events", "achievements"} else item.is_active
        rows.append([InlineKeyboardButton(
            text=f"{'🟢' if is_visible else '⚪'} {getattr(item, label_attr)[:52]}",
            callback_data=AdminCB(action="content_view", param=f"{kind}|{item.id}").pack(),
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCB(action=kind).pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_content_detail_kb(kind: str, item_id: int, is_published: bool) -> InlineKeyboardMarkup:
    action = "content_hide" if is_published else "content_publish"
    caption = "🙈 Скрыть / закрыть" if is_published else "✅ Опубликовать / открыть"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить", callback_data=AdminCB(action="content_edit", param=f"{kind}|{item_id}").pack())],
        [InlineKeyboardButton(text=caption, callback_data=AdminCB(action=action, param=f"{kind}|{item_id}").pack())],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=AdminCB(action="content_delete", param=f"{kind}|{item_id}").pack())],
        [InlineKeyboardButton(text="⬅️ К списку", callback_data=AdminCB(action="content_list", param=kind).pack())],
    ])


def get_content_edit_fields_kb(kind: str, item_id: int) -> InlineKeyboardMarkup:
    shared = [
        ("title_ru", "🇷🇺 Заголовок"), ("title_uz", "🇺🇿 Sarlavha"),
        ("description_ru", "🇷🇺 Описание"), ("description_uz", "🇺🇿 Tavsif"),
    ]
    if kind == "events":
        shared += [("event_date", "📅 Дата"), ("location_ru", "📍 Место RU"), ("location_uz", "📍 Joy UZ")]
    elif kind == "achievements":
        shared += [("achievement_date", "📅 Дата"), ("student_name", "👤 Ученик / команда"), ("category", "🏷 Категория")]
    elif kind == "polls":
        shared = [("question_ru", "🇷🇺 Вопрос"), ("question_uz", "🇺🇿 Savol")]
    rows = [[InlineKeyboardButton(
        text=caption, callback_data=AdminCB(action="content_edit_field", param=f"{kind}|{item_id}|{field}").pack()
    )] for field, caption in shared]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCB(action="content_view", param=f"{kind}|{item_id}").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_schedule_classes_kb(classes) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        text=f"🏫 {school_class.display_name}", callback_data=AdminCB(action="schedule_class", param=str(school_class.id)).pack()
    )] for school_class in classes]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCB(action="main").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_schedule_days_admin_kb(class_id: int) -> InlineKeyboardMarkup:
    labels = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб")
    rows = [[InlineKeyboardButton(
        text=label, callback_data=AdminCB(action="schedule_day_admin", param=f"{class_id}|{day}").pack()
    ) for day, label in enumerate(labels[:3])], [InlineKeyboardButton(
        text=label, callback_data=AdminCB(action="schedule_day_admin", param=f"{class_id}|{day}").pack()
    ) for day, label in enumerate(labels[3:], start=3)]]
    rows.append([InlineKeyboardButton(text="⬅️ К классам", callback_data=AdminCB(action="schedule").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_schedule_lessons_kb(class_id: int, weekday: int, lessons) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        text=f"{lesson.lesson_number}. {lesson.subject}",
        callback_data=AdminCB(action="lesson_view", param=f"{class_id}|{weekday}|{lesson.id}").pack(),
    )] for lesson in lessons]
    rows.append([InlineKeyboardButton(
        text="➕ Добавить урок", callback_data=AdminCB(action="lesson_create", param=f"{class_id}|{weekday}").pack()
    )])
    rows.append([InlineKeyboardButton(
        text="⬅️ К дням", callback_data=AdminCB(action="schedule_class", param=str(class_id)).pack()
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_lesson_detail_kb(class_id: int, weekday: int, lesson_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить предмет", callback_data=AdminCB(action="lesson_edit", param=f"{class_id}|{weekday}|{lesson_id}|subject").pack())],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=AdminCB(action="lesson_delete", param=f"{class_id}|{weekday}|{lesson_id}").pack())],
        [InlineKeyboardButton(text="⬅️ К урокам", callback_data=AdminCB(action="schedule_day_admin", param=f"{class_id}|{weekday}").pack())],
    ])


def get_feedback_filter_kb(fb_type: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🟢 Новые", callback_data=AdminCB(action=f"{fb_type}_status", param="new").pack()),
                InlineKeyboardButton(text="🟡 В работе", callback_data=AdminCB(action=f"{fb_type}_status", param="in_progress").pack()),
                InlineKeyboardButton(text="🔴 Закрытые", callback_data=AdminCB(action=f"{fb_type}_status", param="closed").pack())
            ],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCB(action="main").pack())]
        ]
    )


def get_broadcast_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data=AdminCB(action="broadcast_confirm").pack()),
                InlineKeyboardButton(text="❌ Отмена", callback_data=AdminCB(action="broadcast_cancel").pack())
            ]
        ]
    )


def get_user_grades_kb(grades: list[int]) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text="Без класса" if grade == 0 else f"{grade} класс",
            callback_data=AdminCB(action="users_grade", param=str(grade)).pack()
        )
        for grade in grades
    ]
    rows = [buttons[index:index + 2] for index in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton(text="⬅️ Назад в меню", callback_data=AdminCB(action="main").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_user_classes_kb(classes: list[tuple[str, int]], grade: int) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"🏫 {class_name} — {count} учен.",
                callback_data=AdminCB(action="users_class", param=f"{class_name}|1").pack(),
            )
        ]
        for class_name, count in classes
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCB(action="users").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_users_list_kb(
    users: list[User], class_name: str, page: int, total_pages: int
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"👤 {user.first_name} {user.last_name}",
                callback_data=AdminCB(action="user_select", param=str(user.telegram_id)).pack(),
            )
        ]
        for user in users
    ]
    navigation = []
    if page > 1:
        navigation.append(
            InlineKeyboardButton(
                text="⬅️", callback_data=AdminCB(action="users_class", param=f"{class_name}|{page - 1}").pack()
            )
        )
    navigation.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data=AdminCB(action="ignore").pack()))
    if page < total_pages:
        navigation.append(
            InlineKeyboardButton(
                text="➡️", callback_data=AdminCB(action="users_class", param=f"{class_name}|{page + 1}").pack()
            )
        )
    rows.append(navigation)
    rows.append([InlineKeyboardButton(text="⬅️ К параллелям", callback_data=AdminCB(action="users").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_feedback_list_kb(feedbacks: list[Feedback], section: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"#{feedback.id} — {feedback.user.class_name if feedback.user else 'без класса'}",
                callback_data=AdminCB(action="feedback_view", param=str(feedback.id)).pack(),
            )
        ]
        for feedback in feedbacks
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCB(action=section).pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_user_change_grades_kb(user_id: int, grades: list[int]) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            text=str(grade), callback_data=AdminCB(action="user_class_grade", param=f"{user_id}|{grade}").pack()
        )
        for grade in grades
    ]
    rows = [buttons[index:index + 3] for index in range(0, len(buttons), 3)]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCB(action="user_select", param=str(user_id)).pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_user_change_classes_kb(user_id: int, classes: list[SchoolClass]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"🏫 {school_class.display_name}",
                callback_data=AdminCB(action="user_class_select", param=f"{user_id}|{school_class.id}").pack(),
            )
        ]
        for school_class in classes
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCB(action="user_change_class", param=str(user_id)).pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_reply_feedback_kb(feedback_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✉ Ответить", 
                    callback_data=AdminCB(action="reply_feedback", param=str(feedback_id)).pack()
                )
            ]
        ]
    )


def get_reply_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data=AdminCB(action="reply_send").pack()),
                InlineKeyboardButton(text="❌ Отмена", callback_data=AdminCB(action="reply_cancel").pack()),
            ]
        ]
    )


def get_feedback_detail_kb(feedback: Feedback) -> InlineKeyboardMarkup:
    rows = []
    if feedback.status == "new":
        rows.append([
            InlineKeyboardButton(
                text="🟡 В работу",
                callback_data=AdminCB(action="feedback_set_status", param=f"{feedback.id}|in_progress").pack(),
            )
        ])
    if feedback.status != "closed":
        rows.append([
            InlineKeyboardButton(
                text="✅ Закрыть",
                callback_data=AdminCB(action="feedback_set_status", param=f"{feedback.id}|closed").pack(),
            )
        ])
    rows.append([
        InlineKeyboardButton(
            text="✉️ Ответить", callback_data=AdminCB(action="reply_feedback", param=str(feedback.id)).pack()
        )
    ])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCB(action="main").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_applications_list_kb(users: list[User], page: int, total_pages: int) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"📝 {user.first_name} {user.last_name} — {user.class_name}",
                callback_data=AdminCB(action="application_view", param=str(user.telegram_id)).pack(),
            )
        ]
        for user in users
    ]
    navigation = []
    if page > 1:
        navigation.append(
            InlineKeyboardButton(text="⬅️", callback_data=AdminCB(action="applications_page", param=str(page - 1)).pack())
        )
    navigation.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data=AdminCB(action="ignore").pack()))
    if page < total_pages:
        navigation.append(
            InlineKeyboardButton(text="➡️", callback_data=AdminCB(action="applications_page", param=str(page + 1)).pack())
        )
    rows.append(navigation)
    rows.append([InlineKeyboardButton(text="⬅️ Назад в меню", callback_data=AdminCB(action="main").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_registration_request_actions_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять", callback_data=AdminCB(action="application_accept", param=str(user_id)).pack()
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить", callback_data=AdminCB(action="application_reject", param=str(user_id)).pack()
                ),
            ],
            [InlineKeyboardButton(
                text="👤 Профиль",
                callback_data=AdminCB(action="application_view", param=str(user_id)).pack(),
            )],
        ]
    )


# Stage 3 overrides keep existing admin callbacks while adding the Moderator role.
def get_user_card_kb(
    user_id: int,
    class_name: str,
    role: str = "",
    *,
    can_manage_roles: bool = False,
    can_manage_moderator_assignments: bool = False,
) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🎓 Изменить класс", callback_data=AdminCB(action="user_change_class", param=str(user_id)).pack())],
    ]
    if can_manage_roles:
        rows.append([InlineKeyboardButton(
            text="🛡 Изменить роль", callback_data=AdminCB(action="user_change_role", param=str(user_id)).pack()
        )])
    if role == "moderator" and can_manage_moderator_assignments:
        rows.append([InlineKeyboardButton(
            text="🏫 Управление классами", callback_data=AdminCB(action="moderator_classes", param=str(user_id)).pack()
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCB(action="users_class", param=f"{class_name}|1").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_user_role_kb(user_id: int, current_role: str) -> InlineKeyboardMarkup:
    roles = [("🎓 Ученик", "student"), ("👨‍🏫 Модератор", "moderator"), ("🛡 Администратор", "admin")]
    rows = [[InlineKeyboardButton(
        text=f"✅ {label}" if role == current_role else label,
        callback_data=AdminCB(action="set_role", param=f"{user_id}|{role}").pack(),
    )] for label, role in roles]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCB(action="user_select", param=str(user_id)).pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_moderator_classes_kb(
    moderator_id: int, classes: list[SchoolClass], assigned_ids: set[int]
) -> InlineKeyboardMarkup:
    rows = []
    for school_class in classes:
        assigned = school_class.id in assigned_ids
        action = "moderator_class_remove" if assigned else "moderator_class_add"
        rows.append([InlineKeyboardButton(
            text=f"{'✅' if assigned else '➕'} {school_class.display_name}",
            callback_data=AdminCB(action=action, param=f"{moderator_id}|{school_class.id}").pack(),
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=AdminCB(action="user_select", param=str(moderator_id)).pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_feedback_group_kb(feedback: Feedback) -> InlineKeyboardMarkup:
    """Compact operational controls for an administration feedback group."""
    rows = []
    if feedback.status == "new":
        rows.append([InlineKeyboardButton(
            text="🟡 В работу", callback_data=AdminCB(action="feedback_set_status", param=f"{feedback.id}|in_progress").pack()
        )])
    if feedback.status != "closed":
        rows.append([InlineKeyboardButton(
            text="✅ Закрыть", callback_data=AdminCB(action="feedback_set_status", param=f"{feedback.id}|closed").pack()
        )])
    rows.append([InlineKeyboardButton(
        text="✉️ Ответить", callback_data=AdminCB(action="reply_feedback", param=str(feedback.id)).pack()
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)

