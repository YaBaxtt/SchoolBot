from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, patch

from aiogram import Bot, F, Dispatcher, Router
from aiogram.types import CallbackQuery, Update, User
from filters.roles import ADMIN_ROLES, RoleFilter
from middlewares.user import UserMiddleware
from permissions import (
    Permission,
    UserRole,
    has_global_staff_scope,
    has_permission,
    normalize_role,
)


def user(role: str, status: str = "active") -> SimpleNamespace:
    return SimpleNamespace(role=role, status=status)


class PermissionTests(TestCase):
    def test_role_normalization_handles_legacy_string_values(self) -> None:
        self.assertEqual(normalize_role(" ADMIN "), UserRole.ADMIN.value)
        self.assertEqual(normalize_role(UserRole.SUPERADMIN), UserRole.SUPERADMIN.value)
        self.assertEqual(normalize_role(None), "")

    def test_explicit_permission_matrix(self) -> None:
        self.assertFalse(has_permission(user("student"), Permission.ACCESS_STAFF))
        self.assertTrue(has_permission(user("moderator"), Permission.ACCESS_STAFF))
        self.assertFalse(has_permission(user("moderator"), Permission.ACCESS_ADMIN))
        self.assertTrue(has_permission(user("admin"), Permission.ACCESS_ADMIN))
        self.assertFalse(has_permission(user("admin"), Permission.VIEW_COMPLAINTS))
        self.assertTrue(has_permission(user("superadmin"), Permission.VIEW_COMPLAINTS))
        self.assertFalse(has_permission(user("admin", "pending"), Permission.ACCESS_ADMIN))

    def test_global_staff_scope_is_reserved_for_elevated_staff(self) -> None:
        self.assertFalse(has_global_staff_scope(user("moderator")))
        self.assertTrue(has_global_staff_scope(user("admin")))
        self.assertTrue(has_global_staff_scope(user("superadmin")))


class MiddlewareAndFilterTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        # Dispatcher construction can legitimately take longer than unittest's
        # debug-mode 100 ms callback warning on a Windows file system.
        asyncio.get_running_loop().slow_callback_duration = 1.0

    async def test_middleware_injects_current_user_for_callback_events(self) -> None:
        current_user = user("admin")
        middleware = UserMiddleware()
        data = {"event_from_user": SimpleNamespace(id=42)}

        async def handler(event, injected_data):
            return injected_data["current_user"]

        with patch("middlewares.user.get_user_by_tg_id", AsyncMock(return_value=current_user)):
            injected = await middleware(handler, object(), data)

        self.assertIs(injected, current_user)

    async def test_dispatcher_injects_current_user_into_callback_handler(self) -> None:
        dispatcher = Dispatcher()
        dispatcher.update.outer_middleware(UserMiddleware())
        router = Router()
        seen: list[object] = []

        @router.callback_query(F.data == "probe")
        async def callback_handler(callback: CallbackQuery, current_user) -> None:
            seen.append(current_user)

        dispatcher.include_router(router)
        update = Update(
            update_id=1,
            callback_query=CallbackQuery(
                id="probe-id",
                from_user=User(id=42, is_bot=False, first_name="Test"),
                chat_instance="probe",
                data="probe",
            ),
        )
        bot = Bot(token="123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi")
        current_user = user("admin")
        try:
            with patch("middlewares.user.get_user_by_tg_id", AsyncMock(return_value=current_user)):
                await dispatcher.feed_update(bot, update)
        finally:
            await bot.session.close()

        self.assertEqual(seen, [current_user])

    async def test_role_filter_uses_injected_user_for_callbacks(self) -> None:
        role_filter = RoleFilter(ADMIN_ROLES)
        callback = SimpleNamespace(from_user=SimpleNamespace(id=42))
        self.assertTrue(await role_filter(callback, current_user=user(" ADMIN ")))
        self.assertFalse(await role_filter(callback, current_user=user("moderator")))
