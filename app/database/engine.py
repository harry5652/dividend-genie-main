from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from app.config import config

engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

class Base(DeclarativeBase):
    pass