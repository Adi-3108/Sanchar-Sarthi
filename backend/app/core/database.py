from __future__ import annotations

from functools import lru_cache
from typing import Any

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings


def _build_connect_args(database_url: str) -> dict[str, Any]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}

    if database_url.startswith("postgresql"):
        return {"connect_timeout": 2}

    return {}


def _configure_sqlite(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def build_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_settings().database_url
    engine = create_engine(
        url,
        pool_pre_ping=True,
        future=True,
        connect_args=_build_connect_args(url),
    )
    _configure_sqlite(engine)
    return engine


@lru_cache
def get_engine() -> Engine:
    return build_engine()


def get_database_status(engine: Engine | None = None) -> tuple[str, str | None]:
    active_engine = engine or get_engine()
    try:
        with active_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return "connected", None
    except SQLAlchemyError as exc:
        return "unavailable", exc.__class__.__name__
