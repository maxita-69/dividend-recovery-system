"""
FastAPI dependencies.
"""
from typing import Generator

from sqlalchemy.orm import Session

from database.database import get_database_session


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session and close it after the request."""
    db = get_database_session()
    try:
        yield db
    finally:
        db.close()
