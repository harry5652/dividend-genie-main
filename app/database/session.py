from sqlalchemy.orm import scoped_session, sessionmaker
from app.database.db import engine

SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False)
)


def get_session():
    return SessionLocal()