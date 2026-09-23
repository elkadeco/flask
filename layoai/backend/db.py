from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from config import settings

def utcnow():
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass

class Brief(Base):
    __tablename__ = "briefs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_user_id: Mapped[str] = mapped_column(String(128), index=True)
    project_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    project_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    locale: Mapped[str] = mapped_column(String(16), default="en")
    status: Mapped[str] = mapped_column(String(32), default="draft")
    answers: Mapped[dict] = mapped_column(JSON, default=dict)
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    submission_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    rooms: Mapped[list["Room"]] = relationship(back_populates="brief", cascade="all, delete-orphan")

class Room(Base):
    __tablename__ = "rooms"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    brief_id: Mapped[str] = mapped_column(ForeignKey("briefs.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    count: Mapped[str | None] = mapped_column(String(32), nullable=True)
    area: Mapped[str | None] = mapped_column(String(32), nullable=True)
    priority: Mapped[str] = mapped_column(String(32), default="Must have")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    brief: Mapped[Brief] = relationship(back_populates="rooms")

engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def init_db():
    Base.metadata.create_all(bind=engine)
