# keyboards/__init__.py

from keyboards.admin_kb import (
    get_admin_main_kb,
    get_back_to_admin_kb,
    get_news_kb,
    get_feedback_filter_kb,
    get_broadcast_confirm_kb,
    AdminCB,
)

# Псевдонимы для совместимости со старыми импортами

from keyboards.feedback_kb import (
    get_confirm_feedback_kb, get_feedback_warning_kb, get_my_feedback_detail_kb, get_my_feedbacks_kb,
)
from keyboards.main_kb import (
    get_feedback_cancel_kb,
    get_help_back_kb,
    get_language_kb,
    get_main_menu_kb,
    get_registration_classes_kb,
    get_registration_grades_kb,
    get_registration_name_confirm_kb,
)
from keyboards.news_kb import get_back_to_news_kb, get_news_list_kb
from keyboards.profile_kb import (
    get_edit_cancel_kb, get_edit_fields_kb, get_edit_language_kb, get_profile_class_grades_kb,
    get_profile_classes_kb, get_profile_main_kb, get_class_change_classes_kb,
    get_class_change_confirm_kb, get_class_change_grades_kb, get_class_change_reason_kb,
)

get_admin_menu_kb = get_admin_main_kb
get_confirm_publish_kb = get_broadcast_confirm_kb
__all__ = [
    "get_language_kb",
    "get_main_menu_kb",
    "get_feedback_cancel_kb",
    "get_help_back_kb",
    "get_registration_grades_kb",
    "get_registration_name_confirm_kb",
    "get_registration_classes_kb",
    "get_news_list_kb",
    "get_back_to_news_kb",
    "get_admin_menu_kb",
    "get_confirm_publish_kb",
    "get_profile_main_kb",
    "get_edit_fields_kb",
    "get_edit_language_kb",
    "get_edit_cancel_kb",
    "get_profile_class_grades_kb",
    "get_profile_classes_kb",
    "get_class_change_grades_kb",
    "get_class_change_classes_kb",
    "get_class_change_reason_kb",
    "get_class_change_confirm_kb",
    "get_confirm_feedback_kb",
    "get_feedback_warning_kb",
    "get_my_feedbacks_kb",
    "get_my_feedback_detail_kb",
]





