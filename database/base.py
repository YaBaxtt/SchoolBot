from pathlib import Path
import secrets

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Resolve the database next to the project, not relative to the terminal from
# which ``bot.py`` was launched.  Otherwise two launch directories can create
# two different ``school_bot.db`` files and produce contradictory RBAC checks.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "school_bot.db"
DB_URL = f"sqlite+aiosqlite:///{DB_PATH.as_posix()}"

engine = create_async_engine(DB_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


_USER_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _new_user_code(used_codes: set[str]) -> str:
    """Create a short non-sequential code not used by the existing database."""
    while True:
        code = "SCH-" + "".join(secrets.choice(_USER_CODE_ALPHABET) for _ in range(6))
        if code not in used_codes:
            used_codes.add(code)
            return code


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # ``create_all`` creates new tables but does not add columns to an
        # existing SQLite table. Existing users remain active after upgrade.
        columns = (await conn.execute(text("PRAGMA table_info(users)"))).mappings().all()
        if "status" not in {column["name"] for column in columns}:
            await conn.execute(
                text("ALTER TABLE users ADD COLUMN status VARCHAR(16) NOT NULL DEFAULT 'active'")
            )
        user_columns = {column["name"] for column in columns}
        if "user_code" not in user_columns:
            await conn.execute(text("ALTER TABLE users ADD COLUMN user_code VARCHAR(16)"))
        if "public_profile_enabled" not in user_columns:
            await conn.execute(
                text("ALTER TABLE users ADD COLUMN public_profile_enabled BOOLEAN NOT NULL DEFAULT 0")
            )
        if "registration_reviewed_by_id" not in user_columns:
            await conn.execute(text("ALTER TABLE users ADD COLUMN registration_reviewed_by_id INTEGER"))
        if "registration_reviewed_at" not in user_columns:
            await conn.execute(text("ALTER TABLE users ADD COLUMN registration_reviewed_at DATETIME"))
        if "telegram_username" not in user_columns:
            await conn.execute(text("ALTER TABLE users ADD COLUMN telegram_username VARCHAR(64)"))
        # The unique index preserves the generated-code invariant while still
        # allowing legacy rows to be backfilled during this same transaction.
        await conn.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_user_code ON users (user_code)")
        )
        # A pupil may keep historical approved/rejected requests, but never
        # two pending class-transfer requests.  The partial unique index makes
        # a double click safe even when two callback updates race.
        await conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_class_change_one_pending "
            "ON class_change_requests (user_id) WHERE status = 'pending'"
        ))
        class_columns = (await conn.execute(text("PRAGMA table_info(school_classes)"))).mappings().all()
        if "curator_user_id" not in {column["name"] for column in class_columns}:
            await conn.execute(text("ALTER TABLE school_classes ADD COLUMN curator_user_id INTEGER"))

        missing_codes = (
            await conn.execute(text("SELECT id FROM users WHERE user_code IS NULL OR trim(user_code) = ''"))
        ).mappings().all()
        existing_codes = {
            str(row["user_code"]).upper()
            for row in (await conn.execute(text("SELECT user_code FROM users WHERE user_code IS NOT NULL"))).mappings()
            if str(row["user_code"]).strip()
        }
        for row in missing_codes:
            await conn.execute(
                text("UPDATE users SET user_code = :user_code WHERE id = :id"),
                {"user_code": _new_user_code(existing_codes), "id": row["id"]},
            )
        # Existing databases may have roles edited as ADMIN or " admin ".
        # Normalize in place; no user, table, or database is recreated.
        await conn.execute(text("UPDATE users SET role = lower(trim(role)), status = lower(trim(status))"))
        news_columns = (await conn.execute(text("PRAGMA table_info(news)"))).mappings().all()
        existing_news_columns = {column["name"] for column in news_columns}
        # SQLite does not support Alembic in this legacy project.  These
        # additive upgrades preserve every existing news row.
        for name, definition in {
            "title_uz": "VARCHAR(255)",
            "content_uz": "TEXT",
            "photo_file_id": "VARCHAR(255)",
            "is_published": "BOOLEAN NOT NULL DEFAULT 1",
            "is_pinned": "BOOLEAN NOT NULL DEFAULT 0",
            "published_at": "DATETIME",
            "updated_at": "DATETIME",
        }.items():
            if name not in existing_news_columns:
                await conn.execute(text(f"ALTER TABLE news ADD COLUMN {name} {definition}"))
        settings_columns = (await conn.execute(text("PRAGMA table_info(school_settings)"))).mappings().all()
        existing_settings_columns = {column["name"] for column in settings_columns}
        for name, definition in {
            "leaderboard_prize_text_ru": "TEXT",
            "leaderboard_prize_text_uz": "TEXT",
            "show_prize_message": "BOOLEAN NOT NULL DEFAULT 0",
        }.items():
            if name not in existing_settings_columns:
                await conn.execute(text(f"ALTER TABLE school_settings ADD COLUMN {name} {definition}"))
