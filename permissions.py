"""Canonical roles and permissions for the school bot.

The database deliberately stores role values as strings, so this module is the
single boundary that normalizes legacy string values and answers authorization
questions.  Handlers must ask for a permission instead of comparing role text.
"""

from enum import Enum
from typing import Any


class UserRole(str, Enum):
    STUDENT = "student"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class Permission(str, Enum):
    ACCESS_STAFF = "access_staff"
    ACCESS_ADMIN = "access_admin"
    GLOBAL_STAFF_SCOPE = "global_staff_scope"
    MANAGE_USERS = "manage_users"
    MANAGE_CLASSES = "manage_classes"
    MANAGE_NEWS = "manage_news"
    MANAGE_BROADCAST = "manage_broadcast"
    MANAGE_SUGGESTIONS = "manage_suggestions"
    VIEW_COMPLAINTS = "view_complaints"
    MANAGE_ROLES = "manage_roles"
    MANAGE_MODERATOR_ASSIGNMENTS = "manage_moderator_assignments"


ROLE_VALUES = frozenset(role.value for role in UserRole)
ASSIGNABLE_ROLES = frozenset(
    {UserRole.STUDENT.value, UserRole.MODERATOR.value, UserRole.ADMIN.value}
)
STUDENT_ROLES = frozenset({UserRole.STUDENT.value})
MODERATOR_ROLES = frozenset({UserRole.MODERATOR.value})
STAFF_ROLES = frozenset(
    {UserRole.MODERATOR.value, UserRole.ADMIN.value, UserRole.SUPERADMIN.value}
)
ADMIN_ROLES = frozenset({UserRole.ADMIN.value, UserRole.SUPERADMIN.value})
SUPERADMIN_ROLES = frozenset({UserRole.SUPERADMIN.value})


# The policy is intentionally explicit rather than relying on numeric role
# levels: complaints and role management remain SuperAdmin-only.
ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    UserRole.STUDENT.value: frozenset(),
    UserRole.MODERATOR.value: frozenset(
        {
            Permission.ACCESS_STAFF,
            Permission.MANAGE_SUGGESTIONS,
        }
    ),
    UserRole.ADMIN.value: frozenset(
        {
            Permission.ACCESS_STAFF,
            Permission.ACCESS_ADMIN,
            Permission.GLOBAL_STAFF_SCOPE,
            Permission.MANAGE_USERS,
            Permission.MANAGE_CLASSES,
            Permission.MANAGE_NEWS,
            Permission.MANAGE_BROADCAST,
            Permission.MANAGE_SUGGESTIONS,
        }
    ),
    UserRole.SUPERADMIN.value: frozenset(Permission),
}


def normalize_role(value: Any | None) -> str:
    """Return the canonical lowercase role value without granting a fallback."""
    if isinstance(value, UserRole):
        return value.value
    if isinstance(value, Enum):
        value = value.value
    return str(value or "").strip().lower()


def normalize_status(value: Any | None) -> str:
    return str(value or "").strip().lower()


def is_active(user: Any | None) -> bool:
    return user is not None and normalize_status(getattr(user, "status", None)) == "active"


def has_permission(user: Any | None, permission: Permission) -> bool:
    if not is_active(user):
        return False
    return permission in ROLE_PERMISSIONS.get(normalize_role(getattr(user, "role", None)), frozenset())


def can_access_staff(user: Any | None) -> bool:
    return has_permission(user, Permission.ACCESS_STAFF)


def can_access_admin(user: Any | None) -> bool:
    return has_permission(user, Permission.ACCESS_ADMIN)


def has_global_staff_scope(user: Any | None) -> bool:
    """Admins and SuperAdmins may operate staff workflows for every class."""
    return has_permission(user, Permission.GLOBAL_STAFF_SCOPE)


def can_manage_users(user: Any | None) -> bool:
    return has_permission(user, Permission.MANAGE_USERS)


def can_manage_classes(user: Any | None) -> bool:
    return has_permission(user, Permission.MANAGE_CLASSES)


def can_manage_news(user: Any | None) -> bool:
    return has_permission(user, Permission.MANAGE_NEWS)


def can_manage_broadcast(user: Any | None) -> bool:
    return has_permission(user, Permission.MANAGE_BROADCAST)


def can_manage_suggestions(user: Any | None) -> bool:
    return has_permission(user, Permission.MANAGE_SUGGESTIONS)


def can_view_complaints(user: Any | None) -> bool:
    return has_permission(user, Permission.VIEW_COMPLAINTS)


def can_manage_roles(user: Any | None) -> bool:
    return has_permission(user, Permission.MANAGE_ROLES)


def can_manage_moderator_assignments(user: Any | None) -> bool:
    return has_permission(user, Permission.MANAGE_MODERATOR_ASSIGNMENTS)
