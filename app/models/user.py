from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)

    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))

    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    portfolio = relationship(
        "Portfolio",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    command_logs = relationship(
        "CommandLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class CommandLog(Base):
    __tablename__ = "command_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    command = Column(String(50), nullable=False, index=True)
    args = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    response_time_ms = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=True)

    user = relationship("User", back_populates="command_logs")
