from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


class Person(Base):
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    primary_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    primary_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    city_raw: Mapped[str | None] = mapped_column(String(120), nullable=True)
    city_canonical: Mapped[str | None] = mapped_column(String(120), index=True, nullable=True)
    experience_years: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    current_ctc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    applied_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    gig_rate_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gig_rate_period: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gig_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cb_verified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    projects_completed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    emails = relationship("PersonEmail", cascade="all, delete-orphan", back_populates="person")
    phones = relationship("PersonPhone", cascade="all, delete-orphan", back_populates="person")
    skills = relationship("PersonSkill", cascade="all, delete-orphan", back_populates="person")
    source_records = relationship("SourceRecord", cascade="all, delete-orphan", back_populates="person")
    audio_submissions = relationship("AudioSubmission", back_populates="person")


Index("ix_people_name_city", Person.normalized_name, Person.city_canonical)


class PersonEmail(Base):
    __tablename__ = "person_emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    person = relationship("Person", back_populates="emails")


class PersonPhone(Base):
    __tablename__ = "person_phones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    phone_e164: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    person = relationship("Person", back_populates="phones")


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)


class PersonSkill(Base):
    __tablename__ = "person_skills"
    __table_args__ = (UniqueConstraint("person_id", "skill_id", name="uq_person_skill"),)

    person_id: Mapped[int] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)

    person = relationship("Person", back_populates="skills")
    skill = relationship("Skill")


class SourceRecord(Base):
    __tablename__ = "source_records"
    __table_args__ = (UniqueConstraint("source_name", "source_row_number", name="uq_source_row"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    source_name: Mapped[str] = mapped_column(String(80), nullable=False)
    source_row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    match_strategy: Mapped[str] = mapped_column(String(80), nullable=False)
    issue_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    person = relationship("Person", back_populates="source_records")


class AudioSubmission(Base):
    __tablename__ = "audio_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int | None] = mapped_column(ForeignKey("people.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    phone_e164: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    sample_rate_khz: Mapped[float | None] = mapped_column(Float, nullable=True)
    sample_rate_hz: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bitrate_kbps: Mapped[float | None] = mapped_column(Float, nullable=True)
    loudness_db: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_estimate: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    noise_estimate: Mapped[str | None] = mapped_column(String(80), nullable=True)
    analysis_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    person = relationship("Person", back_populates="audio_submissions")
