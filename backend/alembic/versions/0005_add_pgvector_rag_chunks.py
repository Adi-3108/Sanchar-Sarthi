"""Add pgvector-backed rag_chunks table.

Revision ID: 0005_add_pgvector_rag_chunks
Revises: 0004_foundation_incidents
Create Date: 2026-06-22 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_add_pgvector_rag_chunks"
down_revision = "0004_foundation_incidents"
branch_labels = None
depends_on = None

VECTOR_DIMENSIONS = 768


def _dialect_name() -> str:
    return op.get_bind().dialect.name


def _uuid_type() -> sa.types.TypeEngine:
    return postgresql.UUID(as_uuid=True) if _dialect_name() == "postgresql" else sa.String(length=36)


def _embedding_type() -> sa.types.TypeEngine:
    if _dialect_name() == "postgresql":
        return sa.Text()
    return sa.JSON()


def _uuid_default() -> sa.TextClause | None:
    return sa.text("gen_random_uuid()") if _dialect_name() == "postgresql" else None


def upgrade() -> None:
    if _dialect_name() == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "rag_chunks",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False, server_default=_uuid_default()),
        sa.Column("source_table", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("chunk_type", sa.String(length=64), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("embedding", _embedding_type(), nullable=False),
        sa.Column("visibility", sa.String(length=32), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("source_table", "source_id", "chunk_type", name="uq_rag_chunks_source"),
    )
    op.create_index("idx_rag_chunks_type_visibility", "rag_chunks", ["chunk_type", "visibility"])
    op.create_index("idx_rag_chunks_source", "rag_chunks", ["source_table", "source_id"])

    if _dialect_name() == "postgresql":
        op.execute(
            f"""
            ALTER TABLE rag_chunks
            ALTER COLUMN embedding TYPE vector({VECTOR_DIMENSIONS})
            USING embedding::vector({VECTOR_DIMENSIONS})
            """
        )
        op.execute(
            """
            CREATE INDEX idx_rag_chunks_embedding
            ON rag_chunks USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
            """
        )


def downgrade() -> None:
    if _dialect_name() == "postgresql":
        op.execute("DROP INDEX IF EXISTS idx_rag_chunks_embedding")
    op.drop_index("idx_rag_chunks_source", table_name="rag_chunks")
    op.drop_index("idx_rag_chunks_type_visibility", table_name="rag_chunks")
    op.drop_table("rag_chunks")
