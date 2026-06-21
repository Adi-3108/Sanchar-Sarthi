from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, TypeDecorator

from app.db.base import UUIDPrimaryKeyMixin, Base

try:  # pragma: no cover - exercised when pgvector is installed
    from pgvector.sqlalchemy import Vector as PgVector
except ModuleNotFoundError:  # pragma: no cover - local fallback path
    PgVector = None

VECTOR_DIMENSIONS = 768


class RagVectorType(TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and PgVector is not None:
            return dialect.type_descriptor(PgVector(VECTOR_DIMENSIONS))
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.JSONB(astext_type=Text()))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Any, dialect):
        if value is None:
            return None
        return list(value)

    def process_result_value(self, value: Any, dialect):
        if value is None:
            return None
        if isinstance(value, list):
            return [float(item) for item in value]
        if isinstance(value, tuple):
            return [float(item) for item in value]
        if isinstance(value, str):
            stripped = value.strip().strip("[]")
            if not stripped:
                return []
            return [float(item.strip()) for item in stripped.split(",") if item.strip()]
        return list(value)


class RagChunk(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "rag_chunks"
    __table_args__ = (
        UniqueConstraint(
            "source_table",
            "source_id",
            "chunk_type",
            name="uq_rag_chunks_source",
        ),
        Index("idx_rag_chunks_type_visibility", "chunk_type", "visibility"),
        Index("idx_rag_chunks_source", "source_table", "source_id"),
    )

    source_table: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    chunk_type: Mapped[str] = mapped_column(String(64), nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(RagVectorType(), nullable=False)
    visibility: Mapped[str] = mapped_column(String(32), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
