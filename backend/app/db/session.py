from collections.abc import Generator
from typing import Any, cast

try:
    from sqlalchemy.orm import Session
except ModuleNotFoundError:  # pragma: no cover - exercised before dependency install
    Session = Any


def get_db() -> Generator[Session, None, None]:
    raise RuntimeError("Database sessions are introduced in Phase 2.")
    yield cast(Session, None)
