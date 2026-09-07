import logging
from collections.abc import Collection
from typing import Any, Union
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from database.requests import get_user_by_tg_id
from permissions import (
    ADMIN_ROLES,
    MODERATOR_ROLES,
    STAFF_ROLES,
    SUPERADMIN_ROLES,
    is_active,
    normalize_role,
)

logger = logging.getLogger(__name__)

class RoleFilter(BaseFilter):
    """
    Фильтр проверки ролей пользователя.
    Принимает список ролей (например: 'admin', 'superadmin') или одну роль.
    """
    def __init__(self, allowed_roles: Union[str, Collection[str]]) -> None:
        if isinstance(allowed_roles, str):
            allowed_roles = [allowed_roles]
        else:
            allowed_roles = list(allowed_roles)
        self.allowed_roles = {normalize_role(role) for role in allowed_roles}

    async def __call__(
        self, event: Union[Message, CallbackQuery], current_user: Any | None = None
    ) -> bool:
        # UserMiddleware supplies the same object to messages and callbacks.
        # The database fallback keeps this filter usable in isolated tests.
        user = current_user or await get_user_by_tg_id(event.from_user.id)
        if not user:
            return False
        # Existing installations may contain manually edited values with
        # surrounding whitespace or another letter case.  They are compared
        # against the same canonical RBAC values without granting a new role.
        role = normalize_role(user.role)
        allowed = is_active(user) and role in self.allowed_roles
        if not allowed:
            # A callback can be checked by several protected routers in turn.
            # The final fallback logs a single actionable denial instead.
            logger.debug("Permission denied for Telegram user %s", event.from_user.id)
        return allowed


class RegisteredUserFilter(BaseFilter):
    """Allows the student-facing routers to handle updates only for registered users."""

    async def __call__(
        self, event: Union[Message, CallbackQuery], current_user: Any | None = None
    ) -> bool:
        user = current_user or await get_user_by_tg_id(event.from_user.id)
        return is_active(user)


class IsSuperAdmin(RoleFilter):
    def __init__(self) -> None:
        super().__init__(SUPERADMIN_ROLES)


class IsAdmin(RoleFilter):
    def __init__(self) -> None:
        super().__init__(ADMIN_ROLES)


class IsModerator(RoleFilter):
    def __init__(self) -> None:
        super().__init__(MODERATOR_ROLES)
