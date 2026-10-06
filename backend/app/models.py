from datetime import date, datetime, timezone

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text, TypeDecorator, UniqueConstraint
from sqlalchemy import DateTime as SADateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def now():
    return datetime.now(timezone.utc)


class DateTime(TypeDecorator):
    """Date-heure toujours en UTC avec fuseau (SQLite perd le fuseau, PostgreSQL le garde)."""

    impl = SADateTime(timezone=True)
    cache_ok = True

    def __init__(self, timezone=True):
        super().__init__()

    def process_bind_param(self, value, dialect):
        return value.astimezone(timezone.utc) if value is not None else None

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(default=False)
    # Incrémenté au changement de mot de passe : invalide toutes les sessions existantes.
    session_version: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    subject: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(200))
    notes: Mapped[str] = mapped_column(Text, default="")
    # Révision espacée : prochaine date de révision conseillée et nombre de révisions faites.
    next_review: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    # Identifiant du cours sur Moodle quand il a été importé automatiquement.
    moodle_course_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    files: Mapped[list["CourseFile"]] = relationship(
        back_populates="course", cascade="all, delete-orphan", order_by="CourseFile.id"
    )


class CourseFile(Base):
    __tablename__ = "course_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255))
    size: Mapped[int] = mapped_column(Integer)
    # Pour les fichiers venant de Moodle : URL + date de modification, pour ne pas les retélécharger.
    moodle_key: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

    course: Mapped[Course] = relationship(back_populates="files")


class CalendarSource(Base):
    __tablename__ = "calendar_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    url: Mapped[str] = mapped_column(Text)
    last_sync: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("source_id", "uid"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # NULL = événement ajouté à la main.
    source_id: Mapped[int | None] = mapped_column(
        ForeignKey("calendar_sources.id", ondelete="CASCADE"), nullable=True, index=True
    )
    uid: Mapped[str | None] = mapped_column(String(500), nullable=True)
    title: Mapped[str] = mapped_column(String(300))
    start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    location: Mapped[str] = mapped_column(String(300), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    # "course", "exam" ou "other"
    kind: Mapped[str] = mapped_column(String(20), default="course")


class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    subject: Mapped[str] = mapped_column(String(100))
    label: Mapped[str] = mapped_column(String(200))
    value: Mapped[float] = mapped_column(Float)
    max_value: Mapped[float] = mapped_column(Float, default=20)
    coefficient: Mapped[float] = mapped_column(Float, default=1)
    date: Mapped[date] = mapped_column(Date)


class MoodleAccount(Base):
    __tablename__ = "moodle_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    base_url: Mapped[str] = mapped_column(String(255))
    # Clé chiffrée avec SECRET_KEY : jamais renvoyée au navigateur.
    token_encrypted: Mapped[str] = mapped_column(Text)
    moodle_user_id: Mapped[int] = mapped_column(Integer)
    site_name: Mapped[str] = mapped_column(String(255), default="")
    last_sync: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    syncing: Mapped[bool] = mapped_column(default=False, server_default="false")
