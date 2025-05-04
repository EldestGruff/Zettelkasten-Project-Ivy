# backend/app/api/deps.py
from typing import Generator, Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal

def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that yields a SQLAlchemy session.
    Ensures the session is closed after the request is finished.
    """
    db = None
    try:
        db = SessionLocal()
        yield db
    finally:
        if db is not None:
            db.close() # Ensures session is closed even if errors occur

# Type Alias for dependency injection clarity (optional but nice)
DbSession = Annotated[Session, Depends(get_db)]
