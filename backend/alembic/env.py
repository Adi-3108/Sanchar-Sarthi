from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import resolve_database_url
from app.core.database import build_engine
from app.db.base import Base, import_model_modules

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

import_model_modules()
target_metadata = Base.metadata


def get_database_url() -> str:
    configured_url = config.get_main_option("sqlalchemy.url")
    return resolve_database_url(
        configured_url if configured_url and configured_url != "sqlite:///./eventflow_local.db" else None
    )


def run_migrations_offline() -> None:
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = build_engine(get_database_url())

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=connection.dialect.name == "sqlite",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
