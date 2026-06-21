from __future__ import annotations

import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base, import_model_modules
from app.orm.rag_chunk import RagChunk
from app.services.rag_context_builder import build_context
from app.services.rag_embedding_service import embed_text_sync


PUBLIC_TEXT = "Public traffic advisory for Silk Board Junction and nearby service road."
CONTROL_TEXT = "Control room deployment note for ORR East 1 barricade staging."
ADMIN_TEXT = "Admin after-action learning for ORR East 1 reserve staffing shortfall."


def _build_session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    import_model_modules()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _seed_chunks(session) -> None:
    session.add_all(
        [
            RagChunk(
                source_table="incidents",
                source_id="PUB-1",
                chunk_type="incident",
                chunk_text=PUBLIC_TEXT,
                embedding=embed_text_sync(PUBLIC_TEXT),
                visibility="public",
            ),
            RagChunk(
                source_table="events",
                source_id="CTRL-1",
                chunk_type="recommendation",
                chunk_text=CONTROL_TEXT,
                embedding=embed_text_sync(CONTROL_TEXT),
                visibility="control_room",
            ),
            RagChunk(
                source_table="post_event_reports",
                source_id="ADMIN-1",
                chunk_type="post_event_report",
                chunk_text=ADMIN_TEXT,
                embedding=embed_text_sync(ADMIN_TEXT),
                visibility="admin",
            ),
        ]
    )
    session.commit()


def test_build_context_limits_guest_to_public_chunks():
    session_factory = _build_session_factory()

    with session_factory() as session:
        _seed_chunks(session)
        texts, sources = asyncio.run(build_context(session, "What is happening near Silk Board service road?", "guest"))

    rendered = " ".join(texts)
    source_ids = {source["source_id"] for source in sources}

    assert "PUB-1" in source_ids
    assert "CTRL-1" not in source_ids
    assert "ADMIN-1" not in source_ids
    assert "Public traffic advisory" in rendered
    assert "deployment note" not in rendered
    assert "after-action learning" not in rendered


def test_build_context_allows_control_room_to_see_control_chunks():
    session_factory = _build_session_factory()

    with session_factory() as session:
        _seed_chunks(session)
        texts, sources = asyncio.run(build_context(session, "Show the ORR East 1 barricade staging plan", "control_room"))

    rendered = " ".join(texts)
    source_ids = {source["source_id"] for source in sources}

    assert "PUB-1" in source_ids
    assert "CTRL-1" in source_ids
    assert "ADMIN-1" not in source_ids
    assert "deployment note" in rendered
    assert "after-action learning" not in rendered


def test_build_context_allows_admin_to_see_admin_chunks():
    session_factory = _build_session_factory()

    with session_factory() as session:
        _seed_chunks(session)
        texts, sources = asyncio.run(build_context(session, "What did the after-action review say about reserve staffing?", "admin"))

    rendered = " ".join(texts)
    source_ids = {source["source_id"] for source in sources}

    assert {"PUB-1", "CTRL-1", "ADMIN-1"}.issubset(source_ids)
    assert "after-action learning" in rendered
