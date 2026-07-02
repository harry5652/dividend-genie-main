"""
Database engine and session factory.
"""
import logging
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import config

logger = logging.getLogger(__name__)

engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {},
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def _migrate() -> None:
    """Add new columns to existing tables when they are missing."""
    is_sqlite = "sqlite" in config.DATABASE_URL
    migrations = [
        ("command_logs", "response_time_ms", "INTEGER"),
        ("command_logs", "success", "BOOLEAN"),
        ("portfolio", "avg_price", "FLOAT"),
    ]

    with engine.connect() as conn:
        for table, column, col_type in migrations:
            try:
                if is_sqlite:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                else:
                    conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type}")
                    )
                conn.commit()
                logger.info("Migration applied: %s.%s (%s)", table, column, col_type)
            except Exception as exc:
                conn.rollback()
                msg = str(exc).lower()
                if any(kw in msg for kw in ("already exists", "duplicate column", "dupcolumn")):
                    logger.debug("Column %s.%s already exists, skipping.", table, column)
                else:
                    logger.error(
                        "Migration failed for %s.%s: %s", table, column, exc, exc_info=True
                    )
                    raise

        try:
            conn.execute(text("UPDATE portfolio SET avg_price = 0 WHERE avg_price IS NULL"))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            msg = str(exc).lower()
            if "no such column" not in msg and "no such table" not in msg:
                raise


def init_db() -> None:
    """Create all tables if they do not exist yet, then apply lightweight migrations."""
    from app.models.user import User, CommandLog
    from app.models.portfolio import Portfolio

    Base.metadata.create_all(bind=engine)
    _migrate()


@contextmanager
def get_db():
    """Context-manager style session. Use with `with get_db() as db:`."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
