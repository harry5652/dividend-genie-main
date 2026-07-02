"""
Database engine and session factory (Production-ready).
PostgreSQL + SQLAlchemy setup.
"""
import logging
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import config

logger = logging.getLogger(__name__)

# =========================
# Engine (PostgreSQL only)
# =========================
engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

# =========================
# Session Factory
# =========================
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# =========================
# Base Model
# =========================
class Base(DeclarativeBase):
    pass


# =========================
# DB Initialization
# =========================
def init_db() -> None:
    """
    Create tables if they do not exist.
    NOTE: In production, Alembic will replace this later.
    """
    import app.models.user  # noqa: F401
    import app.models.portfolio  # noqa: F401

    Base.metadata.create_all(bind=engine)

    logger.info("Database initialized successfully.")


# =========================
# FIXED SESSION CONTEXT MANAGER
# =========================
@contextmanager
def get_db():
    """
    Usage:
        with get_db() as db:
            ...
    """
    db = SessionLocal()   # ✅ FIX: create session

    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
