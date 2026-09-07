from __future__ import annotations

from types import SimpleNamespace
from unittest import TestCase

from keyboards.admin_kb import (
    AdminCB,
    get_admin_main_kb,
    get_applications_list_kb,
    get_back_to_admin_kb,
    get_broadcast_confirm_kb,
    get_class_create_confirm_kb,
    get_class_curator_confirm_kb,
    get_class_delete_confirm_kb,
    get_class_detail_kb,
    get_classes_list_kb,
    get_classes_menu_kb,
    get_content_detail_kb,
    get_content_edit_fields_kb,
    get_content_list_kb,
    get_content_menu_kb,
    get_feedback_detail_kb,
    get_feedback_filter_kb,
    get_feedback_group_kb,
    get_feedback_list_kb,
    get_grade_choice_kb,
    get_moderator_classes_kb,
    get_news_kb,
    get_news_publish_kb,
    get_registration_request_actions_kb,
    get_reply_confirm_kb,
    get_settings_kb,
    get_lesson_detail_kb,
    get_schedule_classes_kb,
    get_schedule_days_admin_kb,
    get_schedule_lessons_kb,
    get_user_card_kb,
    get_user_change_classes_kb,
    get_user_change_grades_kb,
    get_user_classes_kb,
    get_user_grades_kb,
    get_user_role_kb,
    get_users_list_kb,
)
from keyboards.staff_kb import (
    StaffCB,
    get_staff_announcement_classes_kb,
    get_staff_class_action_kb,
    get_staff_application_card_kb,
    get_staff_applications_kb,
    get_staff_classes_kb,
    get_staff_confirm_kb,
    get_staff_feedback_card_kb,
    get_staff_feedback_list_kb,
    get_staff_feedback_status_kb,
    get_staff_main_kb,
    get_staff_students_kb,
)
from keyboards.feedback_kb import (
    get_confirm_feedback_kb,
    get_feedback_warning_kb,
    get_my_feedback_detail_kb,
    get_my_feedbacks_kb,
)
from keyboards.main_kb import (
    get_help_back_kb,
    get_language_kb,
    get_registration_classes_kb,
    get_registration_grades_kb,
    get_registration_name_confirm_kb,
)
from keyboards.news_kb import get_back_to_news_kb, get_news_list_kb
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
from keyboards.profile_kb import (
    get_edit_cancel_kb,
    get_edit_fields_kb,
    get_edit_language_kb,
    get_profile_class_grades_kb,
    get_profile_classes_kb,
    get_profile_main_kb,
    get_class_change_grades_kb,
    get_class_change_classes_kb,
    get_class_change_reason_kb,
    get_class_change_confirm_kb,
)


SCHOOL_CLASS = SimpleNamespace(id=7, grade=11, letter="А", is_active=True, display_name="11-А")
USER = SimpleNamespace(telegram_id=42, first_name="Test", last_name="User", class_name="11-А")
FEEDBACK = SimpleNamespace(id=3, status="new", type="suggestion", user=USER)


def actions(markups, callback_type):
    return {
        callback_type.unpack(button.callback_data).action
        for markup in markups
        for row in markup.inline_keyboard
        for button in row
        if button.callback_data
    }


def raw_callbacks(markups):
    return {
        button.callback_data
        for markup in markups
        for row in markup.inline_keyboard
        for button in row
        if button.callback_data
    }


# Kept alongside this test as a concise handler inventory.  Any callback that
# a keyboard generates must be present here and have a protected handler.
ADMIN_HANDLER_ACTIONS = {
    "main", "users", "users_grade", "users_class", "user_select", "ignore",
    "user_change_class", "user_class_grade", "user_class_select", "user_change_role",
    "set_role", "moderator_classes", "moderator_class_add", "moderator_class_remove",
    "applications", "applications_page", "application_view", "application_accept", "application_reject",
    "news", "news_list", "news_create", "news_publish", "news_cancel",
    "suggestions", "complaints", "complaints_status", "suggestions_status", "feedback_view",
    "feedback_set_status", "reply_feedback", "reply_send", "reply_cancel",
    "broadcast", "broadcast_confirm", "broadcast_cancel", "stats", "settings", "help",
    "classes", "class_add", "class_add_grade", "class_create_confirm", "class_create_cancel",
    "classes_list", "classes_manage", "class_view", "class_toggle", "class_delete",
    "class_delete_confirm", "class_delete_cancel",
    "class_curator_assign", "class_curator_change", "class_curator_confirm", "class_curator_promote",
    "class_curator_remove", "class_curator_remove_confirm", "class_curator_cancel",
    "class_changes", "class_change_view", "class_change_decision",
    "events", "achievements", "polls", "content_create", "content_list", "content_view",
    "content_edit", "content_edit_field", "content_publish", "content_hide", "content_delete",
    "content_cancel", "content_skip", "event_target", "schedule", "schedule_class", "schedule_day_admin",
    "lesson_create", "lesson_view", "lesson_edit", "lesson_delete",
}

STAFF_HANDLER_ACTIONS = {
    "main", "ignore", "classes", "applications", "application_view", "application_accept",
    "application_reject", "class_students", "student", "feedback_kind", "feedback_status",
    "feedback", "feedback_status_set", "feedback_reply", "reply_send", "reply_cancel",
    "announcement", "announcement_class", "announcement_send", "announcement_cancel", "profile", "help",
    "schedule", "stats", "class_schedule", "class_stats",
}

GAME_HANDLER_ACTIONS = {
    "home", "main_menu", "memory_intro", "logic_intro", "memory_start", "memory_selected", "memory_pick",
    "logic_start", "logic_answer", "logic_next", "stats", "leaderboard",
}

USER_CALLBACKS = {
    "lang_ru", "lang_uz", "reg_name_confirm", "reg_name_edit", "reg_grade_11", "reg_class_7",
    "reg_classes_back", "help_main_menu", "edit_profile_open", "profile_main_menu", "edit_field_first_name",
    "edit_field_last_name", "edit_field_class_name", "edit_field_language", "edit_field_back", "change_lang_ru",
    "change_lang_uz", "profile_class_grade_11", "profile_class_select_7", "class_change_start", "class_change_grade_11",
    "class_change_select_7", "class_change_skip_reason", "class_change_submit", "class_change_cancel", "profile_public_toggle", "feedback_confirm_yes",
    "feedback_confirm_no", "feedback_warning_continue", "feedback_warning_cancel", "my_feedback_3",
    "my_feedbacks_back", "my_feedbacks_main_menu", "view_news_3_0", "news_page_0", "news_main_menu",
}


class CallbackAuditTests(TestCase):
    def test_admin_callback_factory_keeps_class_creation_confirmation(self) -> None:
        packed = AdminCB(action="class_create_confirm", param="7|А").pack()
        parsed = AdminCB.unpack(packed)
        self.assertEqual(parsed.action, "class_create_confirm")
        self.assertEqual(parsed.param, "7|А")

    def test_admin_callback_factory_accepts_menu_callback_without_param(self) -> None:
        # aiogram 3.18 decodes a trailing empty segment as None; this is the
        # regression that previously made protected callbacks hit fallback.
        parsed = AdminCB.unpack(AdminCB(action="class_add").pack())
        self.assertEqual(parsed.action, "class_add")
        self.assertIsNone(parsed.param)
    def test_every_generated_admin_action_has_a_handler(self) -> None:
        markups = [
            get_admin_main_kb(False), get_admin_main_kb(True), get_back_to_admin_kb(), get_news_kb(),
            get_news_publish_kb(), get_settings_kb(), get_classes_menu_kb(),
            get_grade_choice_kb("class_add_grade"), get_class_create_confirm_kb(11, "А"),
            get_class_curator_confirm_kb("class_curator_confirm"), get_class_curator_confirm_kb("class_curator_promote"),
            get_classes_list_kb([SCHOOL_CLASS]), get_class_detail_kb(SCHOOL_CLASS),
            get_class_delete_confirm_kb(SCHOOL_CLASS), get_feedback_filter_kb("complaints"),
            get_feedback_filter_kb("suggestions"), get_broadcast_confirm_kb(), get_user_grades_kb([11]),
            get_user_classes_kb([("11-А", 1)], 11), get_users_list_kb([USER], "11-А", 1, 1),
            get_user_change_grades_kb(USER.telegram_id, [11]), get_user_change_classes_kb(USER.telegram_id, [SCHOOL_CLASS]),
            get_feedback_list_kb([FEEDBACK], "suggestions"), get_reply_confirm_kb(),
            get_feedback_detail_kb(FEEDBACK), get_applications_list_kb([USER], 1, 1),
            get_registration_request_actions_kb(USER.telegram_id),
            get_user_card_kb(USER.telegram_id, USER.class_name, "moderator", can_manage_roles=True, can_manage_moderator_assignments=True),
            get_user_role_kb(USER.telegram_id, "moderator"), get_moderator_classes_kb(USER.telegram_id, [SCHOOL_CLASS], {SCHOOL_CLASS.id}),
            get_feedback_group_kb(FEEDBACK),
            get_content_menu_kb("events"), get_content_menu_kb("achievements"), get_content_menu_kb("polls"),
            get_content_list_kb("events", [SimpleNamespace(id=5, title_ru="Event", is_published=False)]),
            get_content_list_kb("achievements", [SimpleNamespace(id=6, title_ru="Achievement", is_published=True)]),
            get_content_list_kb("polls", [SimpleNamespace(id=7, question_ru="Poll?", is_active=True)]),
            get_content_detail_kb("events", 5, False), get_content_edit_fields_kb("events", 5),
            get_content_edit_fields_kb("achievements", 6), get_content_edit_fields_kb("polls", 7),
            get_schedule_classes_kb([SCHOOL_CLASS]), get_schedule_days_admin_kb(SCHOOL_CLASS.id),
            get_schedule_lessons_kb(SCHOOL_CLASS.id, 0, [SimpleNamespace(id=4, lesson_number=1, subject="Math")]),
            get_lesson_detail_kb(SCHOOL_CLASS.id, 0, 4),
        ]
        self.assertTrue(actions(markups, AdminCB) <= ADMIN_HANDLER_ACTIONS)

    def test_every_generated_staff_action_has_a_handler(self) -> None:
        markups = [
            get_staff_main_kb("ru"), get_staff_applications_kb([USER], "ru"),
            get_staff_application_card_kb(USER, "ru"), get_staff_classes_kb([SCHOOL_CLASS], {7: 1}, "ru"),
            get_staff_students_kb([USER], 7, 1, 1, "ru"), get_staff_feedback_status_kb("suggestion", "ru"),
            get_staff_feedback_list_kb([FEEDBACK], "suggestion", "ru"), get_staff_feedback_card_kb(FEEDBACK, "ru"),
            get_staff_announcement_classes_kb([SCHOOL_CLASS], "ru"), get_staff_confirm_kb("reply", "ru"),
            get_staff_confirm_kb("announcement", "ru"), get_staff_class_action_kb([SCHOOL_CLASS], "class_schedule", "ru"),
            get_staff_class_action_kb([SCHOOL_CLASS], "class_stats", "ru"),
        ]
        self.assertTrue(actions(markups, StaffCB) <= STAFF_HANDLER_ACTIONS)

    def test_every_generated_game_action_has_a_handler(self) -> None:
        markups = [
            games_home_kb("ru"), game_intro_kb("memory", "ru"), game_intro_kb("logic", "ru"),
            memory_grid_kb([1, 2, 3, 4, 5, 6, 7, 8, 9], {1, 2}), memory_finished_kb("ru"),
            memory_finished_kb("ru", "logic"), logic_options_kb([1, 2, 3, 4]), logic_next_kb("ru"),
            game_stats_kb("ru"), leaderboard_kb("ru"),
        ]
        self.assertTrue(actions(markups, GameCB) <= GAME_HANDLER_ACTIONS)

    def test_every_generated_student_callback_has_a_handler(self) -> None:
        news = SimpleNamespace(id=3, title="News")
        markups = [
            get_language_kb(), get_registration_name_confirm_kb("ru"), get_registration_grades_kb([11], "ru"),
            get_registration_classes_kb([SCHOOL_CLASS], 11, "ru"), get_help_back_kb("ru"),
            get_profile_main_kb("ru"), get_edit_fields_kb("ru"), get_edit_cancel_kb("ru"),
            get_edit_language_kb("ru"), get_profile_class_grades_kb([11], "ru"),
            get_profile_classes_kb([SCHOOL_CLASS], "ru"), get_class_change_grades_kb([11], "ru"),
            get_class_change_classes_kb([SCHOOL_CLASS], "ru"), get_class_change_reason_kb("ru"),
            get_class_change_confirm_kb("ru"), get_confirm_feedback_kb("ru"),
            get_feedback_warning_kb("complaint", "ru"), get_my_feedbacks_kb([FEEDBACK], "ru"),
            get_my_feedback_detail_kb("ru"), get_news_list_kb([news], 0, 1, lang="ru"),
            get_back_to_news_kb(0, "ru"),
        ]
        self.assertTrue(raw_callbacks(markups) <= USER_CALLBACKS)
