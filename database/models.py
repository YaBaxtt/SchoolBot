from datetime import date, datetime, time
from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(2), nullable=False, default="ru")
    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    last_name: Mapped[str] = mapped_column(String(64), nullable=False)
    class_name: Mapped[str] = mapped_column(String(16), nullable=False)
    # A non-secret, staff-facing identifier. It is allocated once and never
    # reused as the Telegram id in administrator workflows.
    user_code: Mapped[str | None] = mapped_column(String(16), unique=True, nullable=True, index=True)
    public_profile_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    telegram_username: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="student")  # student, moderator, admin, superadmin
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active", server_default="active")
    registration_reviewed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    registration_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    news: Mapped[list["News"]] = relationship(back_populates="author")
    feedbacks: Mapped[list["Feedback"]] = relationship(back_populates="user")
    moderator_class_links: Mapped[list["ModeratorClass"]] = relationship(
        back_populates="moderator", cascade="all, delete-orphan"
    )
    curated_classes: Mapped[list["SchoolClass"]] = relationship(
        back_populates="curator", foreign_keys="SchoolClass.curator_user_id"
    )
    game_results: Mapped[list["GameResult"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    class_change_requests: Mapped[list["ClassChangeRequest"]] = relationship(
        back_populates="user", foreign_keys="ClassChangeRequest.user_id", cascade="all, delete-orphan"
    )


class SchoolClass(Base):
    __tablename__ = "school_classes"
    __table_args__ = (UniqueConstraint("grade", "letter", name="uq_school_classes_grade_letter"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    grade: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    letter: Mapped[str] = mapped_column(String(8), nullable=False)
    curator_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    moderator_links: Mapped[list["ModeratorClass"]] = relationship(
        back_populates="school_class", cascade="all, delete-orphan"
    )
    curator: Mapped["User | None"] = relationship(
        back_populates="curated_classes", foreign_keys=[curator_user_id]
    )

    @property
    def display_name(self) -> str:
        return f"{self.grade}-{self.letter}"


class News(Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Legacy title/content remain the Russian fallback for existing news.
    title_uz: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    author: Mapped["User"] = relationship(back_populates="news")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="new")

    user: Mapped["User"] = relationship(back_populates="feedbacks")


class ModeratorClass(Base):
    """Normalized list of school classes assigned to a moderator."""

    __tablename__ = "moderator_classes"
    __table_args__ = (
        UniqueConstraint("moderator_id", "school_class_id", name="uq_moderator_classes_assignment"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    moderator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    school_class_id: Mapped[int] = mapped_column(
        ForeignKey("school_classes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    moderator: Mapped["User"] = relationship(back_populates="moderator_class_links")
    school_class: Mapped["SchoolClass"] = relationship(back_populates="moderator_links")


class ClassChangeRequest(Base):
    """A student request; the student's actual class changes only on review."""

    __tablename__ = "class_change_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    old_class_name: Mapped[str] = mapped_column(String(16), nullable=False)
    target_class_id: Mapped[int] = mapped_column(
        ForeignKey("school_classes.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending", index=True)
    reviewed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    user: Mapped["User"] = relationship(back_populates="class_change_requests", foreign_keys=[user_id])
    target_class: Mapped["SchoolClass"] = relationship(foreign_keys=[target_class_id])
    reviewer: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by_id])


class GameResult(Base):
    """One persisted record for one completed game attempt, never per click."""

    __tablename__ = "game_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    game_type: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    user: Mapped["User"] = relationship(back_populates="game_results")


class SchoolSettings(Base):
    """One optional, editable settings record (id=1)."""

    __tablename__ = "school_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    school_name_ru: Mapped[str | None] = mapped_column(String(255), nullable=True)
    school_name_uz: Mapped[str | None] = mapped_column(String(255), nullable=True)
    short_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    address_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    address_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    official_channel_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    logo_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    welcome_photo_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    support_username: Mapped[str | None] = mapped_column(String(128), nullable=True)
    leaderboard_prize_text_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    leaderboard_prize_text_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    show_prize_message: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class ScheduleLesson(Base):
    __tablename__ = "schedule_lessons"
    __table_args__ = (
        UniqueConstraint("school_class_id", "weekday", "lesson_number", name="uq_schedule_lesson_slot"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    school_class_id: Mapped[int] = mapped_column(ForeignKey("school_classes.id", ondelete="CASCADE"), nullable=False, index=True)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # Monday=0
    lesson_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    room: Mapped[str | None] = mapped_column(String(64), nullable=True)
    teacher_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")


class SchoolEvent(Base):
    __tablename__ = "school_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    title_uz: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description_ru: Mapped[str] = mapped_column(Text, nullable=False)
    description_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    event_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    location_ru: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_uz: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_class_id: Mapped[int | None] = mapped_column(ForeignKey("school_classes.id", ondelete="SET NULL"), nullable=True, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=func.now())


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    title_uz: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description_ru: Mapped[str] = mapped_column(Text, nullable=False)
    description_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    achievement_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    student_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    school_class_id: Mapped[int | None] = mapped_column(ForeignKey("school_classes.id", ondelete="SET NULL"), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, onupdate=func.now())


class Poll(Base):
    __tablename__ = "polls"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_ru: Mapped[str] = mapped_column(Text, nullable=False)
    question_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    allow_results: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PollOption(Base):
    __tablename__ = "poll_options"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    poll_id: Mapped[int] = mapped_column(ForeignKey("polls.id", ondelete="CASCADE"), nullable=False, index=True)
    text_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    text_uz: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class PollVote(Base):
    __tablename__ = "poll_votes"
    __table_args__ = (UniqueConstraint("poll_id", "user_id", name="uq_poll_vote_per_user"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    poll_id: Mapped[int] = mapped_column(ForeignKey("polls.id", ondelete="CASCADE"), nullable=False, index=True)
    option_id: Mapped[int] = mapped_column(ForeignKey("poll_options.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ClassAnnouncement(Base):
    __tablename__ = "class_announcements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    school_class_id: Mapped[int] = mapped_column(ForeignKey("school_classes.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
