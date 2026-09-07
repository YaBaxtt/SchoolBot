import asyncio
import logging
from aiogram import Bot, Dispatcher

from database import init_db
from config import BOT_TOKEN, REGISTRATION_REVIEW_CHAT_ID  # Лучше хранить токен в config.py
from middlewares.user import UserMiddleware

# Импортируем роутеры пользователей
from handlers import (
    registration_router,
    user_management_router,
    user_news_router,
    profile_router,
    feedback_router,
    admin_applications_router,
    admin_classes_router,
    admin_class_changes_router,
    admin_content_router,
    staff_router,
    student_core_router,
    games_router,
    callback_fallback_router,
)

# Импортируем роутеры админ-панели
from handlers.admin_main import admin_main_router
from handlers.admin_users import admin_users_router
from handlers.admin_news import admin_news_router
from handlers.admin_feedbacks import admin_feedbacks_router
from handlers.admin_broadcast import admin_broadcast_router
from handlers.admin_stats import admin_stats_router


def register_admin_routers(dp: Dispatcher) -> None:
    """Регистрация всех роутеров администратора."""
    dp.include_router(admin_main_router)
    dp.include_router(admin_users_router)
    dp.include_router(admin_news_router)
    dp.include_router(admin_feedbacks_router)
    dp.include_router(admin_broadcast_router)
    dp.include_router(admin_stats_router)
    dp.include_router(admin_applications_router)
    dp.include_router(admin_classes_router)
    dp.include_router(admin_class_changes_router)
    dp.include_router(admin_content_router)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logging.info("Registration review group configured: %s", bool(REGISTRATION_REVIEW_CHAT_ID))

    # Инициализация базы данных
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    # Must be registered before routers: current_user is then available for
    # both message and callback filters/handlers.
    dp.update.outer_middleware(UserMiddleware())

    # 1. Подключаем базовые роутеры пользователей
    dp.include_router(registration_router)
    dp.include_router(user_management_router)
    dp.include_router(user_news_router)
    dp.include_router(profile_router)
    dp.include_router(feedback_router)
    dp.include_router(student_core_router)
    dp.include_router(games_router)
    dp.include_router(staff_router)

    # 2. Подключаем админ-панель
    register_admin_routers(dp)
    # Must remain last: it acknowledges stale or unauthorized inline buttons.
    dp.include_router(callback_fallback_router)

    # Запуск бота
    # Keep queued updates during a restart; registration requests must not be
    # silently discarded just because the polling process was restarted.
    await bot.delete_webhook(drop_pending_updates=False)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
