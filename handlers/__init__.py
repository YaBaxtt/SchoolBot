from handlers.admin_broadcast import admin_broadcast_router
from handlers.admin_applications import admin_applications_router
from handlers.admin_classes import admin_classes_router
from handlers.admin_class_changes import admin_class_changes_router
from handlers.admin_content import admin_content_router
from handlers.admin_feedbacks import admin_feedbacks_router
from handlers.admin_main import admin_main_router
from handlers.admin_news import admin_news_router
from handlers.admin_stats import admin_stats_router
from handlers.admin_users import admin_users_router
from handlers.feedback import router as feedback_router
from handlers.profile import router as profile_router
from handlers.registration import router as registration_router
from handlers.user_management import router as user_management_router
from handlers.user_news import router as user_news_router
from handlers.staff import staff_router
from handlers.student_core import student_core_router
from handlers.games import games_router
from handlers.callback_fallback import callback_fallback_router

__all__ = [
    "registration_router",
    "user_news_router",
    "admin_main_router",
    "admin_users_router",
    "admin_news_router",
    "profile_router",
    "feedback_router",
    "admin_feedbacks_router",
    "admin_broadcast_router",
    "admin_applications_router",
    "admin_classes_router",
    "admin_class_changes_router",
    "admin_content_router",
    "admin_stats_router",
    "user_management_router",
    "staff_router",
    "student_core_router",
    "games_router",
    "callback_fallback_router",
]
