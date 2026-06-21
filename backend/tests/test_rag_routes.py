from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import routes_rag
from app.core.security import AuthContext
from app.db.base import Base, import_model_modules
from app.orm.rag_chunk import RagChunk


class _IndexReport:
    def __init__(self, records_indexed: int, chunks_upserted: int, chunk_types: dict[str, int]):
        self.records_indexed = records_indexed
        self.chunks_upserted = chunks_upserted
        self.chunk_types = chunk_types


async def _fake_build_context(_db, question: str, role: str, event_id: str | None = None):
    focus = event_id or "GLOBAL"
    return (
        [f"[event:{focus}] context for {question} under role {role}"],
        [{"chunk_type": "event", "source_id": focus, "similarity": 0.91}],
    )


async def _fake_stream_llm_response(_context_chunks, _history, question: str, _role: str):
    yield "Answer: "
    yield question


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


def _parse_sse_payloads(body: str) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []
    for block in body.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        data_lines = []
        for line in block.splitlines():
            if line.startswith("data:"):
                data_lines.append(line[5:].strip())
        if data_lines:
            payloads.append(json.loads("\n".join(data_lines)))
    return payloads


def _admin_auth() -> AuthContext:
    return AuthContext(
        firebase_uid="test-admin",
        email="admin@example.com",
        role="admin",
        user_account_id="admin-user-1",
    )


def _build_client(session_factory):
    app = FastAPI()
    app.include_router(routes_rag.router)

    def override_get_db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[routes_rag.get_db] = override_get_db
    app.dependency_overrides[routes_rag.require_rag_admin_access] = _admin_auth
    return TestClient(app)


def test_rag_chat_streams_tokens_and_persists_history(monkeypatch):
    session_factory = _build_session_factory()
    client = _build_client(session_factory)
    routes_rag._SESSION_STORE.clear()

    monkeypatch.setattr(routes_rag, "build_context", _fake_build_context)
    monkeypatch.setattr(routes_rag, "stream_llm_response", _fake_stream_llm_response)

    response = client.post(
        "/api/rag/chat",
        json={"question": "How bad is ORR East 1?", "event_id": "EVENT-1"},
    )

    assert response.status_code == 200
    events = _parse_sse_payloads(response.text)
    token_events = [event for event in events if event["type"] == "token"]
    done_event = next(event for event in events if event["type"] == "done")

    assert token_events == [
        {"type": "token", "content": "Answer: "},
        {"type": "token", "content": "How bad is ORR East 1?"},
    ]
    assert done_event["session_id"]
    assert done_event["sources"] == [{"chunk_type": "event", "source_id": "EVENT-1", "similarity": 0.91}]

    history_response = client.get(f"/api/rag/history/{done_event['session_id']}")
    assert history_response.status_code == 200
    history_payload = history_response.json()
    assert history_payload["role"] == "guest"
    assert [message["role"] for message in history_payload["messages"]] == ["user", "assistant"]
    assert history_payload["messages"][1]["content"] == "Answer: How bad is ORR East 1?"


def test_rag_history_delete_removes_owned_session(monkeypatch):
    session_factory = _build_session_factory()
    client = _build_client(session_factory)
    routes_rag._SESSION_STORE.clear()

    monkeypatch.setattr(routes_rag, "build_context", _fake_build_context)
    monkeypatch.setattr(routes_rag, "stream_llm_response", _fake_stream_llm_response)

    response = client.post("/api/rag/chat", json={"question": "Status check?"})
    done_event = next(event for event in _parse_sse_payloads(response.text) if event["type"] == "done")
    session_id = str(done_event["session_id"])

    delete_response = client.delete(f"/api/rag/history/{session_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"status": "deleted", "session_id": session_id}

    missing_response = client.get(f"/api/rag/history/{session_id}")
    assert missing_response.status_code == 404


def test_rag_admin_index_routes_return_expected_payloads(monkeypatch):
    session_factory = _build_session_factory()
    client = _build_client(session_factory)
    routes_rag._SESSION_STORE.clear()

    monkeypatch.setattr(
        routes_rag,
        "get_rag_index_status",
        lambda _db: {
            "enabled": True,
            "llm_provider": "deepseek",
            "embedding_provider": "gemini",
            "chunk_count": 12,
            "by_visibility": {"public": 2, "control_room": 8, "admin": 2},
            "by_type": {"event": 4, "recommendation": 3},
            "latest_updated_at": datetime(2026, 6, 22, 9, 30, tzinfo=timezone.utc).isoformat(),
        },
    )
    monkeypatch.setattr(
        routes_rag,
        "rebuild_rag_index",
        lambda _db, commit=True: _IndexReport(6, 14, {"event": 4, "recommendation": 3}),
    )
    monkeypatch.setattr(
        routes_rag,
        "index_event_record",
        lambda _db, event_id, commit=True: _IndexReport(1, 4, {"event": 1, "event_dna": 1, "recommendation": 1, "live_update": 1}),
    )

    status_response = client.get("/api/rag/index/status")
    assert status_response.status_code == 200
    assert status_response.json()["chunk_count"] == 12
    assert status_response.json()["by_visibility"]["control_room"] == 8

    rebuild_response = client.post("/api/rag/index/rebuild")
    assert rebuild_response.status_code == 200
    assert rebuild_response.json() == {
        "status": "success",
        "records_indexed": 6,
        "chunks_upserted": 14,
        "chunk_types": {"event": 4, "recommendation": 3},
        "event_id": None,
    }

    event_response = client.post("/api/rag/index/event/DEMO_EVENT_WATERLOGGING_HSR")
    assert event_response.status_code == 200
    assert event_response.json() == {
        "status": "success",
        "records_indexed": 1,
        "chunks_upserted": 4,
        "chunk_types": {"event": 1, "event_dna": 1, "recommendation": 1, "live_update": 1},
        "event_id": "DEMO_EVENT_WATERLOGGING_HSR",
    }
