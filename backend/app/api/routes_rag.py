from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import AuthContext, load_auth_context, require_role, verify_firebase_token
from app.db.session import get_db
from app.services.rag_context_builder import build_context
from app.services.rag_indexer_service import get_rag_index_status, index_event_record, rebuild_rag_index
from app.services.rag_llm_service import stream_llm_response

router = APIRouter(prefix="/api/rag", tags=["rag"])

MAX_HISTORY_TURNS = 6
SESSION_TTL_SECONDS = 3600


class RagChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1200)
    session_id: str | None = Field(default=None, max_length=128)
    event_id: str | None = Field(default=None, max_length=128)


class RagSourceResponse(BaseModel):
    chunk_type: str
    source_id: str
    similarity: float


class RagHistoryMessageResponse(BaseModel):
    role: str
    content: str
    created_at: str
    sources: list[RagSourceResponse] = Field(default_factory=list)


class RagHistoryResponse(BaseModel):
    session_id: str
    role: str
    expires_at: str
    messages: list[RagHistoryMessageResponse] = Field(default_factory=list)


class RagIndexStatusResponse(BaseModel):
    enabled: bool
    llm_provider: str
    embedding_provider: str
    chunk_count: int
    by_visibility: dict[str, int] = Field(default_factory=dict)
    by_type: dict[str, int] = Field(default_factory=dict)
    latest_updated_at: str | None = None


class RagIndexRefreshResponse(BaseModel):
    status: str
    records_indexed: int
    chunks_upserted: int
    chunk_types: dict[str, int] = Field(default_factory=dict)
    event_id: str | None = None


@dataclass
class SessionTurn:
    question: str
    answer: str
    created_at: datetime
    sources: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ChatSession:
    session_id: str
    owner_key: str
    role: str
    turns: list[SessionTurn] = field(default_factory=list)
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(seconds=SESSION_TTL_SECONDS))


_SESSION_STORE: dict[str, ChatSession] = {}
_SESSION_LOCK = asyncio.Lock()


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict[str, object] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
    )


async def resolve_optional_auth_context(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> AuthContext | None:
    if not authorization:
        return None
    token_payload = verify_firebase_token(authorization=authorization)
    return load_auth_context(db, token_payload)


def require_rag_admin_access(
    auth: AuthContext = Depends(require_role("admin")),
) -> AuthContext:
    return auth


def _owner_key(auth: AuthContext | None) -> str:
    if auth is None:
        return "public"
    return f"user:{auth.user_account_id}"


def _role_for_session(auth: AuthContext | None) -> str:
    return auth.role if auth is not None else "guest"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_expiry() -> datetime:
    return _utc_now() + timedelta(seconds=SESSION_TTL_SECONDS)


def _cleanup_expired_sessions() -> None:
    now = _utc_now()
    expired_ids = [session_id for session_id, session in _SESSION_STORE.items() if session.expires_at <= now]
    for session_id in expired_ids:
        _SESSION_STORE.pop(session_id, None)


async def _resolve_chat_session(
    requested_session_id: str | None,
    auth: AuthContext | None,
) -> ChatSession:
    owner_key = _owner_key(auth)
    role = _role_for_session(auth)
    async with _SESSION_LOCK:
        _cleanup_expired_sessions()
        if requested_session_id:
            session = _SESSION_STORE.get(requested_session_id)
            if session is not None and session.owner_key == owner_key:
                session.role = role
                session.expires_at = _new_expiry()
                return session
        session_id = requested_session_id if requested_session_id and requested_session_id not in _SESSION_STORE else str(uuid4())
        session = ChatSession(session_id=session_id, owner_key=owner_key, role=role, expires_at=_new_expiry())
        _SESSION_STORE[session_id] = session
        return session


async def _append_turn(
    session_id: str,
    auth: AuthContext | None,
    question: str,
    answer: str,
    sources: list[dict[str, Any]],
) -> None:
    owner_key = _owner_key(auth)
    async with _SESSION_LOCK:
        session = _SESSION_STORE.get(session_id)
        if session is None or session.owner_key != owner_key:
            session = ChatSession(session_id=session_id, owner_key=owner_key, role=_role_for_session(auth))
            _SESSION_STORE[session_id] = session
        session.role = _role_for_session(auth)
        session.expires_at = _new_expiry()
        session.turns.append(
            SessionTurn(
                question=question,
                answer=answer,
                created_at=_utc_now(),
                sources=sources,
            )
        )
        session.turns = session.turns[-MAX_HISTORY_TURNS:]


async def _get_owned_session_or_404(session_id: str, auth: AuthContext | None) -> ChatSession:
    owner_key = _owner_key(auth)
    async with _SESSION_LOCK:
        _cleanup_expired_sessions()
        session = _SESSION_STORE.get(session_id)
        if session is None or session.owner_key != owner_key:
            raise HTTPException(status_code=404, detail={"code": "RAG_SESSION_NOT_FOUND"})
        session.expires_at = _new_expiry()
        return session


def _history_messages(session: ChatSession) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for turn in session.turns[-MAX_HISTORY_TURNS:]:
        messages.append({"role": "user", "content": turn.question})
        messages.append({"role": "assistant", "content": turn.answer})
    return messages


def _history_response(session: ChatSession) -> RagHistoryResponse:
    messages: list[RagHistoryMessageResponse] = []
    for turn in session.turns:
        created_at = turn.created_at.isoformat()
        messages.append(
            RagHistoryMessageResponse(
                role="user",
                content=turn.question,
                created_at=created_at,
                sources=[],
            )
        )
        messages.append(
            RagHistoryMessageResponse(
                role="assistant",
                content=turn.answer,
                created_at=created_at,
                sources=[RagSourceResponse.model_validate(source) for source in turn.sources],
            )
        )
    return RagHistoryResponse(
        session_id=session.session_id,
        role=session.role,
        expires_at=session.expires_at.isoformat(),
        messages=messages,
    )


def _sse_event(payload: dict[str, Any]) -> bytes:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")


@router.post("/chat")
async def chat_with_rag(
    payload: RagChatRequest,
    auth: AuthContext | None = Depends(resolve_optional_auth_context),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    if not settings.rag_enabled:
        return error_response(503, "RAG_DISABLED", "RAG chat is currently disabled.")

    session = await _resolve_chat_session(payload.session_id, auth)
    history = _history_messages(session)

    try:
        context_chunks, sources = await build_context(
            db,
            payload.question,
            _role_for_session(auth),
            event_id=payload.event_id,
        )
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for RAG retrieval.")

    async def event_stream():
        answer_parts: list[str] = []
        try:
            async for token in stream_llm_response(context_chunks, history, payload.question, _role_for_session(auth)):
                answer_parts.append(token)
                yield _sse_event({"type": "token", "content": token})
            answer_text = "".join(answer_parts).strip()
            await _append_turn(session.session_id, auth, payload.question, answer_text, sources)
            yield _sse_event({"type": "done", "sources": sources, "session_id": session.session_id})
        except Exception as exc:
            yield _sse_event({"type": "error", "message": str(exc) or "RAG chat failed."})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/history/{session_id}", response_model=RagHistoryResponse)
async def get_rag_history(
    session_id: str,
    auth: AuthContext | None = Depends(resolve_optional_auth_context),
):
    session = await _get_owned_session_or_404(session_id, auth)
    return _history_response(session)


@router.delete("/history/{session_id}")
async def delete_rag_history(
    session_id: str,
    auth: AuthContext | None = Depends(resolve_optional_auth_context),
):
    session = await _get_owned_session_or_404(session_id, auth)
    async with _SESSION_LOCK:
        _SESSION_STORE.pop(session.session_id, None)
    return {"status": "deleted", "session_id": session.session_id}


@router.post("/index/rebuild", response_model=RagIndexRefreshResponse)
def rebuild_rag_index_route(
    _auth: AuthContext = Depends(require_rag_admin_access),
    db: Session = Depends(get_db),
):
    try:
        report = rebuild_rag_index(db, commit=True)
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for RAG index rebuild.")

    return RagIndexRefreshResponse(
        status="success",
        records_indexed=report.records_indexed,
        chunks_upserted=report.chunks_upserted,
        chunk_types=report.chunk_types,
    )


@router.post("/index/event/{event_id}", response_model=RagIndexRefreshResponse)
def rebuild_rag_index_for_event_route(
    event_id: str,
    _auth: AuthContext = Depends(require_rag_admin_access),
    db: Session = Depends(get_db),
):
    try:
        report = index_event_record(db, event_id, commit=True)
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for event RAG indexing.")

    return RagIndexRefreshResponse(
        status="success",
        records_indexed=report.records_indexed,
        chunks_upserted=report.chunks_upserted,
        chunk_types=report.chunk_types,
        event_id=event_id,
    )


@router.get("/index/status", response_model=RagIndexStatusResponse)
def rag_index_status(
    _auth: AuthContext = Depends(require_rag_admin_access),
    db: Session = Depends(get_db),
):
    try:
        status_payload = get_rag_index_status(db)
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for RAG index status.")
    return RagIndexStatusResponse.model_validate(status_payload)
