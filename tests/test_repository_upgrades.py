import tempfile
from pathlib import Path
from unittest import IsolatedAsyncioTestCase

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.base import Base
from database import requests as db


class RepositoryUpgradeTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "school-test.db"
        self.engine = create_async_engine(f"sqlite+aiosqlite:///{database_path.as_posix()}")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.original_session = db.async_session
        db.async_session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    async def asyncTearDown(self) -> None:
        db.async_session = self.original_session
        await self.engine.dispose()
        self.temp_dir.cleanup()

    async def test_class_creation_and_duplicate_protection(self) -> None:
        created = await db.create_school_class(7, "а")
        self.assertEqual(created.display_name, "7-А")
        self.assertEqual((await db.get_class_by_grade_letter(7, "А")).id, created.id)
        with self.assertRaises(IntegrityError):
            await db.create_school_class(7, "А")

    async def test_user_codes_are_generated_searchable_and_immutable(self) -> None:
        user = await db.add_user(telegram_id=71, language="ru", first_name="Test", last_name="User", class_name="7-А")
        self.assertRegex(user.user_code or "", r"^SCH-[A-Z2-9]{6}$")
        found = await db.get_user_by_code((user.user_code or "").lower())
        self.assertEqual(found.id, user.id)
        await db.update_user_profile(user.telegram_id, user_code="SCH-AAAAAA", first_name="Updated")
        refreshed = await db.get_user_by_tg_id(user.telegram_id)
        self.assertEqual(refreshed.user_code, user.user_code)
        self.assertEqual(refreshed.first_name, "Updated")

    async def test_curator_is_included_in_staff_class_scope(self) -> None:
        school_class = await db.create_school_class(7, "Б")
        curator = await db.add_user(
            telegram_id=72, language="ru", first_name="Class", last_name="Teacher",
            class_name="7-Б", role="moderator",
        )
        self.assertTrue(await db.set_class_curator(school_class.id, curator.id))
        self.assertEqual([item.id for item in await db.get_curator_classes(curator.id)], [school_class.id])
        self.assertTrue(await db.is_class_curator(curator.id, school_class.id))
        self.assertTrue(await db.is_moderator_assigned_to_class(curator.id, school_class.id))

    async def test_class_change_keeps_current_class_until_atomic_review(self) -> None:
        old_class = await db.create_school_class(7, "В")
        target_class = await db.create_school_class(8, "В")
        student = await db.add_user(73, "ru", "Student", "One", old_class.display_name)
        reviewer = await db.add_user(74, "ru", "Admin", "One", target_class.display_name, role="admin")
        request = await db.create_class_change_request(student.id, target_class.id, "Moving")
        self.assertIsNotNone(request)
        self.assertEqual((await db.get_user_by_tg_id(student.telegram_id)).class_name, old_class.display_name)
        self.assertIsNone(await db.create_class_change_request(student.id, target_class.id, None))
        reviewed = await db.review_class_change_request(request.id, reviewer.id, True)
        self.assertEqual(reviewed.status, "approved")
        self.assertEqual((await db.get_user_by_tg_id(student.telegram_id)).class_name, target_class.display_name)
        self.assertIsNone(await db.review_class_change_request(request.id, reviewer.id, True))
