import re
import secrets
from datetime import date, datetime, timedelta
from typing import Any, Optional

from sqlalchemy import String, delete, desc, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from database.base import async_session
from database.models import (
    Achievement,
    ClassAnnouncement,
    ClassChangeRequest,
    Feedback,
    GameResult,
    ModeratorClass,
    News,
    Poll,
    PollOption,
    PollVote,
    ScheduleLesson,
    SchoolClass,
    SchoolEvent,
    SchoolSettings,
    User,
)
from permissions import ADMIN_ROLES, ROLE_VALUES, UserRole, normalize_role, normalize_status

_USER_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _make_user_code() -> str:
    return "SCH-" + "".join(secrets.choice(_USER_CODE_ALPHABET) for _ in range(6))


def normalize_user_code(user_code: str) -> str:
    return "".join((user_code or "").split()).upper()

# --- Пользователи ---

async def get_user_by_tg_id(telegram_id: int) -> Optional[User]:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


async def get_all_users() -> list[User]:
    async with async_session() as session:
        result = await session.execute(select(User).order_by(User.id))
        return list(result.scalars().all())


async def get_active_users() -> list[User]:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.status == "active").order_by(User.id)
        )
        return list(result.scalars().all())


async def get_active_users_count() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(User.id)).where(User.status == "active"))
        return int(result.scalar_one() or 0)


async def get_active_users_page(page: int, limit: int = 50) -> list[User]:
    """A bounded recipient batch for broadcasts; never load all pupils at once."""
    async with async_session() as session:
        result = await session.execute(
            select(User)
            .where(User.status == "active")
            .order_by(User.id)
            .offset(max(page - 1, 0) * limit)
            .limit(limit)
        )
        return list(result.scalars().all())


async def get_active_students_by_class(class_name: str) -> list[User]:
    """Recipients for a moderator class announcement."""
    async with async_session() as session:
        result = await session.execute(
            select(User)
            .where(
                User.class_name == class_name,
                User.status == "active",
                User.role == UserRole.STUDENT.value,
            )
            .order_by(User.id)
        )
        return list(result.scalars().all())


async def get_users_count() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(User.id)))
        return result.scalar_one() or 0


async def get_recent_users(limit: int = 5) -> list[User]:
    async with async_session() as session:
        result = await session.execute(
            select(User).order_by(desc(User.id)).limit(limit)
        )
        return list(result.scalars().all())


async def get_users_paginated(page: int = 1, limit: int = 5) -> tuple[list[User], int]:
    offset = (page - 1) * limit
    async with async_session() as session:
        stmt = select(User).order_by(desc(User.id)).offset(offset).limit(limit)
        result = await session.execute(stmt)
        users = list(result.scalars().all())
        
        total_count = await get_users_count()
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
        return users, total_pages


async def get_pending_users_paginated(page: int = 1, limit: int = 5) -> tuple[list[User], int]:
    page = max(page, 1)
    offset = (page - 1) * limit
    async with async_session() as session:
        result = await session.execute(
            select(User)
            .where(User.status == "pending")
            .order_by(desc(User.created_at), desc(User.id))
            .offset(offset)
            .limit(limit)
        )
        users = list(result.scalars().all())
        total = (
            await session.execute(select(func.count(User.id)).where(User.status == "pending"))
        ).scalar_one() or 0
        return users, max((total + limit - 1) // limit, 1)


async def get_pending_users_for_classes(class_names: list[str]) -> list[User]:
    """Pending registrations limited to the supplied school classes."""
    names = [name for name in class_names if name]
    if not names:
        return []
    async with async_session() as session:
        result = await session.execute(
            select(User)
            .where(User.status == "pending", User.class_name.in_(names))
            .order_by(desc(User.created_at), desc(User.id))
        )
        return list(result.scalars().all())


async def add_user(
    telegram_id: int,
    language: str,
    first_name: str,
    last_name: str,
    class_name: str,
    role: str = "student",
    status: str = "active",
    telegram_username: str | None = None,
) -> User:
    role = normalize_role(role)
    if role not in ROLE_VALUES:
        raise ValueError("Unsupported user role")
    status = normalize_status(status)
    if status not in {"active", "pending", "rejected"}:
        raise ValueError("Unsupported user status")
    async with async_session() as session:
        # The database unique constraint is the final collision guard. Retrying
        # also covers two registrations that happen at the same moment.
        for _ in range(10):
            user = User(
                telegram_id=telegram_id,
                language=language,
                first_name=first_name,
                last_name=last_name,
                class_name=class_name,
                user_code=_make_user_code(),
                telegram_username=(telegram_username or "").lstrip("@").strip() or None,
                role=role,
                status=status,
            )
            session.add(user)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                continue
            await session.refresh(user)
            return user
    raise RuntimeError("Could not allocate a unique user code")


async def update_user_profile(telegram_id: int, **kwargs: Any) -> None:
    # User codes are immutable after allocation. This central boundary prevents
    # accidental changes from profile FSMs or future callers.
    kwargs.pop("user_code", None)
    if not kwargs:
        return
    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(**kwargs)
        )
        await session.commit()


async def update_user_role(telegram_id: int, new_role: str) -> bool:
    new_role = normalize_role(new_role)
    if new_role not in ROLE_VALUES:
        return False
    async with async_session() as session:
        result = await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(role=new_role)
        )
        await session.commit()
        return result.rowcount > 0


async def get_admin_users() -> list[User]:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.role.in_(ADMIN_ROLES))
        )
        return list(result.scalars().all())


# --- Классы школы ---

def normalize_class_letter(letter: str) -> str:
    return "".join(letter.split()).upper()


async def get_class_by_id(class_id: int) -> Optional[SchoolClass]:
    async with async_session() as session:
        result = await session.execute(select(SchoolClass).where(SchoolClass.id == class_id))
        return result.scalar_one_or_none()


async def set_class_curator(class_id: int, curator_user_id: int | None) -> bool:
    async with async_session() as session:
        result = await session.execute(
            update(SchoolClass)
            .where(SchoolClass.id == class_id)
            .values(curator_user_id=curator_user_id)
        )
        await session.commit()
        return result.rowcount > 0


async def get_curator_classes(curator_user_id: int, active_only: bool = False) -> list[SchoolClass]:
    async with async_session() as session:
        stmt = select(SchoolClass).where(SchoolClass.curator_user_id == curator_user_id)
        if active_only:
            stmt = stmt.where(SchoolClass.is_active.is_(True))
        result = await session.execute(stmt.order_by(desc(SchoolClass.grade), SchoolClass.letter))
        return list(result.scalars().all())


async def is_class_curator(curator_user_id: int, class_id: int, active_only: bool = False) -> bool:
    async with async_session() as session:
        stmt = select(SchoolClass.id).where(
            SchoolClass.id == class_id, SchoolClass.curator_user_id == curator_user_id
        )
        if active_only:
            stmt = stmt.where(SchoolClass.is_active.is_(True))
        return (await session.execute(stmt)).scalar_one_or_none() is not None


async def get_user_by_code(user_code: str) -> Optional[User]:
    """Case-insensitive lookup for the non-secret staff-facing identifier."""
    normalized = normalize_user_code(user_code)
    if not normalized:
        return None
    async with async_session() as session:
        result = await session.execute(
            select(User).where(func.upper(User.user_code) == normalized)
        )
        return result.scalar_one_or_none()


async def get_user_by_id(user_id: int) -> Optional[User]:
    async with async_session() as session:
        return await session.get(User, user_id)


async def get_class_by_display_name(display_name: str) -> Optional[SchoolClass]:
    async with async_session() as session:
        result = await session.execute(
            select(SchoolClass).where(
                (SchoolClass.grade.cast(String) + "-" + SchoolClass.letter) == display_name
            )
        )
        return result.scalar_one_or_none()


async def get_class_by_grade_letter(grade: int, letter: str) -> Optional[SchoolClass]:
    letter = normalize_class_letter(letter)
    async with async_session() as session:
        result = await session.execute(
            select(SchoolClass).where(SchoolClass.grade == grade, SchoolClass.letter == letter)
        )
        return result.scalar_one_or_none()


async def create_school_class(grade: int, letter: str) -> SchoolClass:
    school_class = SchoolClass(grade=grade, letter=normalize_class_letter(letter))
    async with async_session() as session:
        session.add(school_class)
        await session.commit()
        await session.refresh(school_class)
        return school_class


async def get_school_classes(active_only: bool = False) -> list[SchoolClass]:
    async with async_session() as session:
        stmt = select(SchoolClass)
        if active_only:
            stmt = stmt.where(SchoolClass.is_active.is_(True))
        result = await session.execute(stmt.order_by(desc(SchoolClass.grade), SchoolClass.letter))
        return list(result.scalars().all())


async def get_active_class_grades() -> list[int]:
    async with async_session() as session:
        result = await session.execute(
            select(SchoolClass.grade)
            .where(SchoolClass.is_active.is_(True))
            .distinct()
            .order_by(desc(SchoolClass.grade))
        )
        return list(result.scalars().all())


async def get_active_classes_by_grade(grade: int) -> list[SchoolClass]:
    async with async_session() as session:
        result = await session.execute(
            select(SchoolClass)
            .where(SchoolClass.grade == grade, SchoolClass.is_active.is_(True))
            .order_by(SchoolClass.letter)
        )
        return list(result.scalars().all())


async def set_school_class_active(class_id: int, is_active: bool) -> bool:
    async with async_session() as session:
        result = await session.execute(
            update(SchoolClass).where(SchoolClass.id == class_id).values(is_active=is_active)
        )
        await session.commit()
        return result.rowcount > 0


async def get_users_count_by_class(class_name: str) -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.count(User.id)).where(User.class_name == class_name)
        )
        return result.scalar_one() or 0


async def get_students_count_by_class(class_name: str) -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.count(User.id)).where(
                User.class_name == class_name,
                User.role == UserRole.STUDENT.value,
                User.status == "active",
            )
        )
        return result.scalar_one() or 0


async def delete_school_class_if_empty(class_id: int) -> bool:
    school_class = await get_class_by_id(class_id)
    if not school_class or await get_users_count_by_class(school_class.display_name):
        return False
    async with async_session() as session:
        await session.execute(delete(ModeratorClass).where(ModeratorClass.school_class_id == class_id))
        result = await session.execute(delete(SchoolClass).where(SchoolClass.id == class_id))
        await session.commit()
        return result.rowcount > 0


# --- Закрепления модераторов за классами ---

async def get_moderator_classes(moderator_id: int, active_only: bool = False) -> list[SchoolClass]:
    async with async_session() as session:
        stmt = (
            select(SchoolClass)
            .outerjoin(ModeratorClass, ModeratorClass.school_class_id == SchoolClass.id)
            .where(
                or_(
                    ModeratorClass.moderator_id == moderator_id,
                    SchoolClass.curator_user_id == moderator_id,
                )
            )
            .distinct()
        )
        if active_only:
            stmt = stmt.where(SchoolClass.is_active.is_(True))
        result = await session.execute(stmt.order_by(desc(SchoolClass.grade), SchoolClass.letter))
        return list(result.scalars().all())


async def is_moderator_assigned_to_class(moderator_id: int, class_id: int, active_only: bool = False) -> bool:
    async with async_session() as session:
        stmt = (
            select(SchoolClass.id)
            .outerjoin(ModeratorClass, SchoolClass.id == ModeratorClass.school_class_id)
            .where(
                SchoolClass.id == class_id,
                or_(
                    ModeratorClass.moderator_id == moderator_id,
                    SchoolClass.curator_user_id == moderator_id,
                ),
            )
        )
        if active_only:
            stmt = stmt.where(SchoolClass.is_active.is_(True))
        return (await session.execute(stmt)).scalar_one_or_none() is not None


async def assign_moderator_class(moderator_id: int, class_id: int) -> bool:
    async with async_session() as session:
        exists = await session.execute(
            select(ModeratorClass.id).where(
                ModeratorClass.moderator_id == moderator_id,
                ModeratorClass.school_class_id == class_id,
            )
        )
        if exists.scalar_one_or_none() is not None:
            return False
        session.add(ModeratorClass(moderator_id=moderator_id, school_class_id=class_id))
        await session.commit()
        return True


async def remove_moderator_class(moderator_id: int, class_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(
            delete(ModeratorClass).where(
                ModeratorClass.moderator_id == moderator_id,
                ModeratorClass.school_class_id == class_id,
            )
        )
        await session.commit()
        return result.rowcount > 0


# --- Пользователи по классам ---

def _grade_from_class_name(class_name: str) -> Optional[int]:
    match = re.match(r"^\s*(\d+)", class_name)
    return int(match.group(1)) if match else None


async def get_user_grades() -> list[int]:
    school_grades = await get_school_classes()
    async with async_session() as session:
        result = await session.execute(select(User.class_name).distinct())
        user_grades = {_grade_from_class_name(name) for name in result.scalars().all()}
    grades = {school_class.grade for school_class in school_grades}
    grades.update(grade for grade in user_grades if grade is not None)
    if None in user_grades:
        grades.add(0)
    return sorted(grades, reverse=True)


async def get_user_class_summaries(grade: int) -> list[tuple[str, int]]:
    school_classes = await get_school_classes()
    names = {school_class.display_name for school_class in school_classes if school_class.grade == grade}
    async with async_session() as session:
        result = await session.execute(select(User.class_name, func.count(User.id)).group_by(User.class_name))
        all_counts = dict(result.all())
        counts = {
            class_name: count
            for class_name, count in all_counts.items()
            if (_grade_from_class_name(class_name) == grade if grade else _grade_from_class_name(class_name) is None)
        }
    names.update(counts)
    return [(name, counts.get(name, 0)) for name in sorted(names)]


async def get_users_by_class_paginated(
    class_name: str, page: int = 1, limit: int = 8
) -> tuple[list[User], int]:
    page = max(page, 1)
    offset = (page - 1) * limit
    async with async_session() as session:
        result = await session.execute(
            select(User)
            .where(User.class_name == class_name)
            .order_by(User.last_name, User.first_name, User.id)
            .offset(offset)
            .limit(limit)
        )
        users = list(result.scalars().all())
        total = (
            await session.execute(select(func.count(User.id)).where(User.class_name == class_name))
        ).scalar_one() or 0
        return users, max((total + limit - 1) // limit, 1)


async def get_students_by_class_paginated(
    class_name: str, page: int = 1, limit: int = 8
) -> tuple[list[User], int]:
    """Read-only moderator list: only active student accounts."""
    page = max(page, 1)
    offset = (page - 1) * limit
    async with async_session() as session:
        criteria = (
            User.class_name == class_name,
            User.role == UserRole.STUDENT.value,
            User.status == "active",
        )
        result = await session.execute(
            select(User)
            .where(*criteria)
            .order_by(User.last_name, User.first_name, User.id)
            .offset(offset)
            .limit(limit)
        )
        users = list(result.scalars().all())
        total = (await session.execute(select(func.count(User.id)).where(*criteria))).scalar_one() or 0
        return users, max((total + limit - 1) // limit, 1)


# --- Статистика ---

async def get_system_stats() -> dict[str, int]:
    async with async_session() as session:
        total_users = (await session.execute(select(func.count(User.id)))).scalar_one() or 0
        active_users = (await session.execute(select(func.count(User.id)).where(User.status == "active"))).scalar_one() or 0
        pending_users = (await session.execute(select(func.count(User.id)).where(User.status == "pending"))).scalar_one() or 0
        students = (await session.execute(select(func.count(User.id)).where(User.role == UserRole.STUDENT.value))).scalar_one() or 0
        moderators = (await session.execute(select(func.count(User.id)).where(User.role == UserRole.MODERATOR.value))).scalar_one() or 0
        admins = (await session.execute(select(func.count(User.id)).where(User.role.in_(ADMIN_ROLES)))).scalar_one() or 0
        news_count = (await session.execute(select(func.count(News.id)))).scalar_one() or 0
        classes_count = (await session.execute(select(func.count(SchoolClass.id)))).scalar_one() or 0

        async def feedback_count(fb_type: str, status: Optional[str] = None) -> int:
            stmt = select(func.count(Feedback.id)).where(Feedback.type == fb_type)
            if status:
                stmt = stmt.where(Feedback.status == status)
            return (await session.execute(stmt)).scalar_one() or 0

        return {
            "total_users": total_users,
            "active_users": active_users,
            "pending_users": pending_users,
            "students": students,
            "moderators": moderators,
            "admins": admins,
            "classes_count": classes_count,
            "news_count": news_count,
            "complaint_new": await feedback_count("complaint", "new"),
            "complaint_in_progress": await feedback_count("complaint", "in_progress"),
            "complaint_closed": await feedback_count("complaint", "closed"),
            "suggestion_new": await feedback_count("suggestion", "new"),
            "suggestion_in_progress": await feedback_count("suggestion", "in_progress"),
            "suggestion_closed": await feedback_count("suggestion", "closed"),
        }


# --- Новости ---

async def create_news(title: str, content: str, author_db_id: int) -> News:
    async with async_session() as session:
        news_item = News(
            title=title,
            content=content,
            author_id=author_db_id
        )
        session.add(news_item)
        await session.commit()
        await session.refresh(news_item)
        return news_item


async def get_news_list(limit: int = 10, offset: int = 0) -> list[News]:
    async with async_session() as session:
        result = await session.execute(
            select(News)
            .order_by(desc(News.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())


async def get_recent_news(limit: int = 3) -> list[News]:
    async with async_session() as session:
        result = await session.execute(
            select(News)
            .order_by(desc(News.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())


async def get_news_count() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(News.id)))
        return result.scalar_one() or 0


async def get_news_by_id(news_id: int) -> Optional[News]:
    async with async_session() as session:
        result = await session.execute(
            select(News).where(News.id == news_id)
        )
        return result.scalar_one_or_none()


# --- Обращения (Жалобы / Предложения) ---

async def create_feedback(user_db_id: int, fb_type: str, text: str) -> Feedback:
    async with async_session() as session:
        feedback = Feedback(
            user_id=user_db_id,
            type=fb_type,
            text=text,
            status="new"
        )
        session.add(feedback)
        await session.commit()
        await session.refresh(feedback)
        return feedback


async def get_recent_feedbacks(fb_type: str, limit: int = 5) -> list[Feedback]:
    async with async_session() as session:
        result = await session.execute(
            select(Feedback)
            .options(joinedload(Feedback.user))
            .where(Feedback.type == fb_type)
            .order_by(desc(Feedback.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())


async def get_feedbacks_by_status(fb_type: str, status: str, limit: int = 5) -> list[Feedback]:
    async with async_session() as session:
        result = await session.execute(
            select(Feedback)
            .options(joinedload(Feedback.user))
            .where(Feedback.type == fb_type, Feedback.status == status)
            .order_by(desc(Feedback.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())


async def get_published_news(limit: int = 5, offset: int = 0) -> list[News]:
    async with async_session() as session:
        result = await session.execute(
            select(News)
            .where(News.is_published.is_(True))
            .order_by(desc(News.is_pinned), desc(News.published_at), desc(News.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())


async def get_published_news_count() -> int:
    async with async_session() as session:
        return (
            await session.execute(select(func.count(News.id)).where(News.is_published.is_(True)))
        ).scalar_one() or 0


async def get_feedbacks_for_moderator(
    moderator_id: int, fb_type: str, status: str, limit: int = 20
) -> list[Feedback]:
    """Feedback from students in classes actually assigned to the moderator."""
    class_names = [school_class.display_name for school_class in await get_moderator_classes(moderator_id)]
    if not class_names:
        return []
    async with async_session() as session:
        result = await session.execute(
            select(Feedback)
            .join(User, User.id == Feedback.user_id)
            .options(joinedload(Feedback.user))
            .where(
                Feedback.type == fb_type,
                Feedback.status == status,
                User.class_name.in_(class_names),
            )
            .order_by(desc(Feedback.created_at))
            .limit(limit)
        )
        return list(result.scalars().unique().all())


async def get_feedback_for_moderator(moderator_id: int, feedback_id: int) -> Optional[Feedback]:
    feedback = await get_feedback_by_id(feedback_id)
    if not feedback or not feedback.user:
        return None
    classes = await get_moderator_classes(moderator_id)
    return feedback if any(item.display_name == feedback.user.class_name for item in classes) else None


async def get_feedbacks_list(limit: int = 10) -> list[Feedback]:
    async with async_session() as session:
        result = await session.execute(
            select(Feedback)
            .options(joinedload(Feedback.user))
            .order_by(desc(Feedback.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())


async def get_user_feedbacks(user_id: int, limit: int = 20) -> list[Feedback]:
    """Returns only the current student's own appeals, newest first."""
    async with async_session() as session:
        result = await session.execute(
            select(Feedback)
            .where(Feedback.user_id == user_id)
            .order_by(desc(Feedback.created_at), desc(Feedback.id))
            .limit(limit)
        )
        return list(result.scalars().all())


async def get_user_feedback_by_id(user_id: int, feedback_id: int) -> Optional[Feedback]:
    """Prevents a crafted callback from exposing another student's appeal."""
    async with async_session() as session:
        result = await session.execute(
            select(Feedback).where(Feedback.id == feedback_id, Feedback.user_id == user_id)
        )
        return result.scalar_one_or_none()


async def get_feedback_by_id(feedback_id: int) -> Optional[Feedback]:
    async with async_session() as session:
        result = await session.execute(
            select(Feedback)
            .options(joinedload(Feedback.user))
            .where(Feedback.id == feedback_id)
        )
        return result.scalar_one_or_none()


async def update_feedback_status(feedback_id: int, status: str) -> bool:
    async with async_session() as session:
        result = await session.execute(
            update(Feedback)
            .where(Feedback.id == feedback_id)
            .values(status=status)
        )
        await session.commit()
        return result.rowcount > 0


async def update_user_status(telegram_id: int, status: str) -> bool:
    status = normalize_status(status)
    if status not in {"active", "pending", "rejected"}:
        return False
    async with async_session() as session:
        result = await session.execute(
            update(User).where(User.telegram_id == telegram_id).values(status=status)
        )
        await session.commit()
        return result.rowcount > 0


async def review_registration_request(
    telegram_id: int, reviewer_db_id: int, accepted: bool
) -> User | None:
    """Atomically review a pending registration; repeated clicks return None."""
    async with async_session() as session:
        new_status = "active" if accepted else "rejected"
        updated = await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id, User.status == "pending")
            .values(
                status=new_status,
                registration_reviewed_by_id=reviewer_db_id,
                registration_reviewed_at=datetime.now(),
            )
        )
        if updated.rowcount != 1:
            await session.rollback()
            return None
        user = (
            await session.execute(select(User).where(User.telegram_id == telegram_id))
        ).scalar_one()
        await session.commit()
        return user


# --- Student class-change requests ---

async def create_class_change_request(
    user_id: int, target_class_id: int, reason: str | None = None
) -> ClassChangeRequest | None:
    """Create at most one pending request for a student without changing class."""
    async with async_session() as session:
        user = await session.get(User, user_id)
        target_class = await session.get(SchoolClass, target_class_id)
        if not user or not target_class or not target_class.is_active:
            return None
        if user.class_name == target_class.display_name:
            raise ValueError("Target class is already current")
        pending = await session.execute(
            select(ClassChangeRequest.id).where(
                ClassChangeRequest.user_id == user_id,
                ClassChangeRequest.status == "pending",
            )
        )
        if pending.scalar_one_or_none() is not None:
            return None
        request = ClassChangeRequest(
            user_id=user.id,
            old_class_name=user.class_name,
            target_class_id=target_class.id,
            reason=(reason or "").strip() or None,
            status="pending",
        )
        session.add(request)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return None
        await session.refresh(request)
        return request


async def get_pending_class_change_requests(
    page: int = 1, limit: int = 8
) -> tuple[list[ClassChangeRequest], int]:
    page = max(page, 1)
    offset = (page - 1) * limit
    async with async_session() as session:
        statement = (
            select(ClassChangeRequest)
            .options(joinedload(ClassChangeRequest.user), joinedload(ClassChangeRequest.target_class))
            .where(ClassChangeRequest.status == "pending")
            .order_by(desc(ClassChangeRequest.created_at), desc(ClassChangeRequest.id))
        )
        requests = list((await session.execute(statement.offset(offset).limit(limit))).scalars().all())
        total = (
            await session.execute(
                select(func.count(ClassChangeRequest.id)).where(ClassChangeRequest.status == "pending")
            )
        ).scalar_one() or 0
        return requests, max((total + limit - 1) // limit, 1)


async def get_class_change_request(request_id: int) -> ClassChangeRequest | None:
    async with async_session() as session:
        result = await session.execute(
            select(ClassChangeRequest)
            .options(joinedload(ClassChangeRequest.user), joinedload(ClassChangeRequest.target_class))
            .where(ClassChangeRequest.id == request_id)
        )
        return result.scalar_one_or_none()


async def review_class_change_request(
    request_id: int, reviewer_id: int, approved: bool
) -> ClassChangeRequest | None:
    """Conditionally review one pending request and update the user atomically."""
    async with async_session() as session:
        request = (
            await session.execute(
                select(ClassChangeRequest)
                .options(joinedload(ClassChangeRequest.user), joinedload(ClassChangeRequest.target_class))
                .where(ClassChangeRequest.id == request_id, ClassChangeRequest.status == "pending")
            )
        ).scalar_one_or_none()
        if not request or not request.target_class or not request.target_class.is_active:
            return None
        status = "approved" if approved else "rejected"
        updated = await session.execute(
            update(ClassChangeRequest)
            .where(ClassChangeRequest.id == request_id, ClassChangeRequest.status == "pending")
            .values(status=status, reviewed_by_id=reviewer_id, reviewed_at=datetime.now())
        )
        if updated.rowcount != 1:
            await session.rollback()
            return None
        if approved:
            await session.execute(
                update(User)
                .where(User.id == request.user_id)
                .values(class_name=request.target_class.display_name)
            )
        await session.commit()
        request.status = status
        request.reviewed_by_id = reviewer_id
        request.reviewed_at = datetime.now()
        return request


# --- School settings / student core ---

async def get_school_settings() -> SchoolSettings | None:
    async with async_session() as session:
        return await session.get(SchoolSettings, 1)


async def get_lessons_for_class_day(school_class_id: int, weekday: int) -> list[ScheduleLesson]:
    async with async_session() as session:
        result = await session.execute(
            select(ScheduleLesson)
            .where(
                ScheduleLesson.school_class_id == school_class_id,
                ScheduleLesson.weekday == weekday,
                ScheduleLesson.is_active.is_(True),
            )
            .order_by(ScheduleLesson.lesson_number)
        )
        return list(result.scalars().all())


async def get_events_for_class(class_id: int, limit: int = 10, offset: int = 0) -> list[SchoolEvent]:
    async with async_session() as session:
        result = await session.execute(
            select(SchoolEvent)
            .where(
                SchoolEvent.is_published.is_(True),
                SchoolEvent.event_date >= date.today(),
                (SchoolEvent.target_class_id.is_(None)) | (SchoolEvent.target_class_id == class_id),
            )
            .order_by(SchoolEvent.event_date, SchoolEvent.event_time, SchoolEvent.id)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())


async def get_event_by_id_for_class(event_id: int, class_id: int) -> SchoolEvent | None:
    async with async_session() as session:
        result = await session.execute(
            select(SchoolEvent).where(
                SchoolEvent.id == event_id,
                SchoolEvent.is_published.is_(True),
                (SchoolEvent.target_class_id.is_(None)) | (SchoolEvent.target_class_id == class_id),
            )
        )
        return result.scalar_one_or_none()


async def get_published_achievements(limit: int = 10, offset: int = 0) -> list[Achievement]:
    async with async_session() as session:
        result = await session.execute(
            select(Achievement)
            .where(Achievement.is_published.is_(True))
            .order_by(desc(Achievement.achievement_date), desc(Achievement.id))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())


async def get_achievement_by_id(achievement_id: int) -> Achievement | None:
    async with async_session() as session:
        result = await session.execute(
            select(Achievement).where(
                Achievement.id == achievement_id, Achievement.is_published.is_(True)
            )
        )
        return result.scalar_one_or_none()


async def get_active_polls() -> list[Poll]:
    now = datetime.now()
    async with async_session() as session:
        result = await session.execute(
            select(Poll)
            .where(Poll.is_active.is_(True), (Poll.ends_at.is_(None)) | (Poll.ends_at > now))
            .order_by(desc(Poll.created_at), desc(Poll.id))
        )
        return list(result.scalars().all())


async def get_active_poll_by_id(poll_id: int) -> Poll | None:
    now = datetime.now()
    async with async_session() as session:
        result = await session.execute(
            select(Poll).where(
                Poll.id == poll_id,
                Poll.is_active.is_(True),
                (Poll.ends_at.is_(None)) | (Poll.ends_at > now),
            )
        )
        return result.scalar_one_or_none()


async def get_poll_options(poll_id: int) -> list[PollOption]:
    async with async_session() as session:
        result = await session.execute(
            select(PollOption).where(PollOption.poll_id == poll_id).order_by(PollOption.sort_order, PollOption.id)
        )
        return list(result.scalars().all())


async def cast_poll_vote(poll_id: int, option_id: int, user_id: int) -> bool:
    """Atomically accept one valid vote per user; returns False for duplicates/stale data."""
    now = datetime.now()
    async with async_session() as session:
        poll = await session.get(Poll, poll_id)
        option = await session.get(PollOption, option_id)
        if not poll or not poll.is_active or (poll.ends_at and poll.ends_at <= now) or not option or option.poll_id != poll_id:
            return False
        exists = await session.execute(
            select(PollVote.id).where(PollVote.poll_id == poll_id, PollVote.user_id == user_id)
        )
        if exists.scalar_one_or_none() is not None:
            return False
        session.add(PollVote(poll_id=poll_id, option_id=option_id, user_id=user_id))
        await session.commit()
        return True


async def get_poll_results(poll_id: int) -> list[tuple[PollOption, int]]:
    async with async_session() as session:
        result = await session.execute(
            select(PollOption, func.count(PollVote.id))
            .outerjoin(PollVote, PollVote.option_id == PollOption.id)
            .where(PollOption.poll_id == poll_id)
            .group_by(PollOption.id)
            .order_by(PollOption.sort_order, PollOption.id)
        )
        return list(result.all())


# --- Admin content management ---
# These functions deliberately use small, explicit unit-of-work operations.
# They are shared by the admin CMS and never load the whole school database.

async def get_events_for_admin(limit: int = 20, offset: int = 0) -> list[SchoolEvent]:
    async with async_session() as session:
        result = await session.execute(
            select(SchoolEvent)
            .order_by(desc(SchoolEvent.event_date), desc(SchoolEvent.id))
            .offset(max(offset, 0)).limit(limit)
        )
        return list(result.scalars().all())


async def get_event_for_admin(event_id: int) -> SchoolEvent | None:
    async with async_session() as session:
        return await session.get(SchoolEvent, event_id)


async def create_school_event(**values) -> SchoolEvent:
    async with async_session() as session:
        item = SchoolEvent(**values)
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item


async def update_school_event(event_id: int, **values) -> bool:
    if not values:
        return False
    async with async_session() as session:
        result = await session.execute(update(SchoolEvent).where(SchoolEvent.id == event_id).values(**values))
        await session.commit()
        return result.rowcount == 1


async def delete_school_event(event_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(delete(SchoolEvent).where(SchoolEvent.id == event_id))
        await session.commit()
        return result.rowcount == 1


async def get_achievements_for_admin(limit: int = 20, offset: int = 0) -> list[Achievement]:
    async with async_session() as session:
        result = await session.execute(
            select(Achievement)
            .order_by(desc(Achievement.achievement_date), desc(Achievement.id))
            .offset(max(offset, 0)).limit(limit)
        )
        return list(result.scalars().all())


async def get_achievement_for_admin(achievement_id: int) -> Achievement | None:
    async with async_session() as session:
        return await session.get(Achievement, achievement_id)


async def create_achievement(**values) -> Achievement:
    async with async_session() as session:
        item = Achievement(**values)
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item


async def update_achievement(achievement_id: int, **values) -> bool:
    if not values:
        return False
    async with async_session() as session:
        result = await session.execute(update(Achievement).where(Achievement.id == achievement_id).values(**values))
        await session.commit()
        return result.rowcount == 1


async def delete_achievement(achievement_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(delete(Achievement).where(Achievement.id == achievement_id))
        await session.commit()
        return result.rowcount == 1


async def get_lessons_for_admin(school_class_id: int, weekday: int) -> list[ScheduleLesson]:
    async with async_session() as session:
        result = await session.execute(
            select(ScheduleLesson)
            .where(ScheduleLesson.school_class_id == school_class_id, ScheduleLesson.weekday == weekday)
            .order_by(ScheduleLesson.lesson_number, ScheduleLesson.id)
        )
        return list(result.scalars().all())


async def get_schedule_lesson(lesson_id: int) -> ScheduleLesson | None:
    async with async_session() as session:
        return await session.get(ScheduleLesson, lesson_id)


async def create_schedule_lesson(**values) -> ScheduleLesson:
    async with async_session() as session:
        item = ScheduleLesson(**values)
        session.add(item)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise ValueError("lesson_slot_exists")
        await session.refresh(item)
        return item


async def update_schedule_lesson(lesson_id: int, **values) -> bool:
    if not values:
        return False
    async with async_session() as session:
        try:
            result = await session.execute(update(ScheduleLesson).where(ScheduleLesson.id == lesson_id).values(**values))
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise ValueError("lesson_slot_exists")
        return result.rowcount == 1


async def delete_schedule_lesson(lesson_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(delete(ScheduleLesson).where(ScheduleLesson.id == lesson_id))
        await session.commit()
        return result.rowcount == 1


async def get_polls_for_admin(limit: int = 20, offset: int = 0) -> list[Poll]:
    async with async_session() as session:
        result = await session.execute(
            select(Poll).order_by(desc(Poll.created_at), desc(Poll.id)).offset(max(offset, 0)).limit(limit)
        )
        return list(result.scalars().all())


async def get_poll_for_admin(poll_id: int) -> Poll | None:
    async with async_session() as session:
        return await session.get(Poll, poll_id)


async def create_poll(question_ru: str, question_uz: str | None, options: list[tuple[str, str | None]]) -> Poll:
    if len(options) < 2:
        raise ValueError("at_least_two_options")
    async with async_session() as session:
        poll = Poll(question_ru=question_ru, question_uz=question_uz)
        session.add(poll)
        await session.flush()
        session.add_all(
            PollOption(poll_id=poll.id, text_ru=title_ru, text_uz=title_uz, sort_order=index)
            for index, (title_ru, title_uz) in enumerate(options, start=1)
        )
        await session.commit()
        await session.refresh(poll)
        return poll


async def update_poll(poll_id: int, **values) -> bool:
    if not values:
        return False
    async with async_session() as session:
        result = await session.execute(update(Poll).where(Poll.id == poll_id).values(**values))
        await session.commit()
        return result.rowcount == 1


async def delete_poll(poll_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(delete(Poll).where(Poll.id == poll_id))
        await session.commit()
        return result.rowcount == 1


async def get_recent_class_announcements(class_id: int, limit: int = 3) -> list[ClassAnnouncement]:
    async with async_session() as session:
        result = await session.execute(
            select(ClassAnnouncement)
            .where(ClassAnnouncement.school_class_id == class_id)
            .order_by(desc(ClassAnnouncement.created_at), desc(ClassAnnouncement.id))
            .limit(limit)
        )
        return list(result.scalars().all())


async def create_class_announcement(class_id: int, author_id: int, text: str) -> ClassAnnouncement:
    async with async_session() as session:
        announcement = ClassAnnouncement(school_class_id=class_id, author_id=author_id, text=text)
        session.add(announcement)
        await session.commit()
        await session.refresh(announcement)
        return announcement


# --- Educational games ---

async def create_game_result(
    user_id: int,
    game_type: str,
    score: int,
    level: int,
    correct_answers: int,
    duration_ms: int | None,
) -> GameResult:
    async with async_session() as session:
        result = GameResult(
            user_id=user_id,
            game_type=game_type,
            score=max(score, 0),
            level=max(level, 0),
            correct_answers=max(correct_answers, 0),
            duration_ms=max(duration_ms, 0) if duration_ms is not None else None,
        )
        session.add(result)
        await session.commit()
        await session.refresh(result)
        return result


async def get_game_stats_for_user(user_id: int) -> dict[str, dict[str, int]]:
    """Aggregated personal statistics; no game-click data is persisted."""
    async with async_session() as session:
        rows = await session.execute(
            select(
                GameResult.game_type,
                func.count(GameResult.id),
                func.max(GameResult.score),
                func.max(GameResult.level),
                func.max(GameResult.correct_answers),
            )
            .where(GameResult.user_id == user_id)
            .group_by(GameResult.game_type)
        )
        return {
            game_type: {
                "games": int(games),
                "best_score": int(best_score or 0),
                "best_level": int(best_level or 0),
                "best_correct": int(best_correct or 0),
            }
            for game_type, games, best_score, best_level, best_correct in rows.all()
        }


async def get_game_leaderboard(
    game_type: str, limit: int = 10, *, weekly: bool = False
) -> list[GameResult]:
    async with async_session() as session:
        criteria = [GameResult.game_type == game_type]
        if weekly:
            week_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=datetime.now().weekday())
            criteria.append(GameResult.created_at >= week_start)
        # Keep each pupil's best attempt only; a prolific single player cannot
        # occupy every leaderboard position.
        ranked = (
            select(
                GameResult.id.label("result_id"),
                func.row_number().over(
                    partition_by=GameResult.user_id,
                    order_by=(desc(GameResult.score), desc(GameResult.level), GameResult.duration_ms, GameResult.id),
                ).label("position"),
            )
            .where(*criteria)
            .subquery()
        )
        statement = (
            select(GameResult)
            .join(ranked, ranked.c.result_id == GameResult.id)
            .options(joinedload(GameResult.user))
            .where(ranked.c.position == 1)
            .order_by(desc(GameResult.score), desc(GameResult.level), GameResult.duration_ms, GameResult.id)
            .limit(limit)
        )
        rows = await session.execute(statement)
        return list(rows.scalars().all())
