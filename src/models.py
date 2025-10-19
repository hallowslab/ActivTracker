# models.py
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # API token fields
    api_token = mapped_column(String, unique=True, nullable=True)
    token_expiry = mapped_column(DateTime, nullable=True)

    actions: Mapped[list["Action"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Action(Base):
    __tablename__ = "actions"

    # Define the composite unique constraint here
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_user_action_name'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    # general notes and metadata
    notes: Mapped[str] = mapped_column(default="", nullable=False)
    properties: Mapped[dict] = mapped_column(JSON, default={})

    user: Mapped["User"] = relationship(back_populates="actions")
    logs: Mapped[list["ActivityLog"]] = relationship(
        back_populates="action", cascade="all, delete-orphan"
    )


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    action_id = Column(Integer, ForeignKey("actions.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
    # delta ▲(ALT+30) most commonly means difference or change
    # Can later be used to track multiple occurences on a single log
    # ActivityLog=DrankWater, Delta=2, Drank 2 cups of water
    delta = mapped_column(Integer, default=1, nullable=False)

    # per-instance info
    notes: Mapped[str] = mapped_column(default="", nullable=False)
    properties: Mapped[dict] = mapped_column(JSON, default={})

    action = relationship("Action", back_populates="logs")
