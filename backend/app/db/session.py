from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from app.core.database import get_engine
from app.db.base import import_model_modules

import_model_modules()

engine = get_engine()
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
