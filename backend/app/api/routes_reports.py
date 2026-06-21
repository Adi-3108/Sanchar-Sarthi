from __future__ import annotations

import time
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import AuthContext, load_auth_context, verify_firebase_token
from app.db.session import get_db
from app.orm.system_audit_log import SystemAuditLog
from app.schemas.reports import CitizenReportCreate, CitizenReportResponse
from app.services.citizen_report_service import build_report_response, create_citizen_report
from app.api.routes_translation import get_translation_service
from app.services.translation_service import TranslationService
from app.services.rag_indexer_service import index_citizen_report_record, index_event_record

router = APIRouter(prefix="/api/reports", tags=["reports"])

REPORT_RATE_LIMIT = 10
REPORT_RATE_WINDOW_SECONDS = 60.0
_REPORT_RATE_BUCKETS: dict[str, list[float]] = {}


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


def _coerce_uuid(value: str | None) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(value)
    except (TypeError, ValueError):
        return None


def resolve_report_auth_context(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> AuthContext | None:
    if not authorization:
        return None
    token_payload = verify_firebase_token(authorization=authorization)
    return load_auth_context(db, token_payload)


def _authorize_report_source(
    payload: CitizenReportCreate,
    auth: AuthContext | None,
) -> JSONResponse | None:
    if payload.report_source == "citizen":
        return None
    if auth is None:
        return error_response(
            401,
            "FIREBASE_AUTH_REQUIRED",
            "Firebase authentication is required for this report source.",
            {"report_source": payload.report_source},
        )
    if payload.report_source == "field_officer" and auth.role != "police_officer":
        return error_response(
            403,
            "OFFICER_ROLE_REQUIRED",
            "Field officer reports require a registered police officer account.",
            {"role": auth.role},
        )
    if payload.report_source in {"control_room", "demo"} and auth.role not in {"admin", "control_room"}:
        return error_response(
            403,
            "CONTROL_ROOM_ROLE_REQUIRED",
            "Control-room reports require an admin or control-room account.",
            {"role": auth.role},
        )
    return None


def _rate_limit_key(request: Request, payload: CitizenReportCreate) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{payload.report_source}:{host}"


def _check_public_rate_limit(request: Request, payload: CitizenReportCreate) -> JSONResponse | None:
    if payload.report_source != "citizen":
        return None

    now = time.monotonic()
    key = _rate_limit_key(request, payload)
    bucket = [
        timestamp
        for timestamp in _REPORT_RATE_BUCKETS.get(key, [])
        if now - timestamp < REPORT_RATE_WINDOW_SECONDS
    ]
    if len(bucket) >= REPORT_RATE_LIMIT:
        _REPORT_RATE_BUCKETS[key] = bucket
        return error_response(
            429,
            "REPORT_RATE_LIMITED",
            "Too many public reports from this client. Please wait before submitting again.",
            {"limit": REPORT_RATE_LIMIT, "window_seconds": int(REPORT_RATE_WINDOW_SECONDS)},
        )
    bucket.append(now)
    _REPORT_RATE_BUCKETS[key] = bucket
    return None


def _record_report_audit_log(
    db: Session,
    *,
    auth: AuthContext | None,
    payload: CitizenReportCreate,
    report_id: str,
    metadata: dict[str, object],
) -> None:
    db.add(
        SystemAuditLog(
            actor_user_id=_coerce_uuid(auth.user_account_id if auth is not None else None),
            actor_role=auth.role if auth is not None else "public",
            action="citizen_report_submit",
            resource_type="citizen_reports",
            resource_id=report_id,
            metadata_json={
                "report_source": payload.report_source,
                "report_type": payload.report_type,
                "severity": payload.severity,
                "matched_event_id": metadata.get("matched_event_id"),
                "new_alert_level": metadata.get("new_alert_level"),
                "report_confidence": metadata.get("report_confidence"),
                "match_method": metadata.get("match_method"),
                "nearby_duplicate_count": metadata.get("nearby_duplicate_count"),
            },
        )
    )


@router.post("/congestion", response_model=CitizenReportResponse)
def submit_congestion_report(
    payload: CitizenReportCreate,
    request: Request,
    auth: AuthContext | None = Depends(resolve_report_auth_context),
    db: Session = Depends(get_db),
    translation_service: TranslationService = Depends(get_translation_service),
):
    auth_error = _authorize_report_source(payload, auth)
    if auth_error is not None:
        return auth_error

    rate_limit_error = _check_public_rate_limit(request, payload)
    if rate_limit_error is not None:
        return rate_limit_error

    try:
        report, metadata = create_citizen_report(
            db,
            payload,
            translation_service=translation_service,
            commit=False
        )
        response_payload = build_report_response(report)
        audit_metadata = {
            **metadata,
            "matched_event_id": response_payload.get("matched_event_id"),
            "new_alert_level": response_payload.get("new_alert_level"),
            "report_confidence": response_payload.get("report_confidence"),
        }
        _record_report_audit_log(
            db,
            auth=auth,
            payload=payload,
            report_id=str(report.id),
            metadata=audit_metadata,
        )
        db.commit()
        db.refresh(report)
        try:
            index_citizen_report_record(db, str(report.id), commit=False)
            matched_event_id = response_payload.get("matched_event_id") or response_payload.get("event_id")
            if matched_event_id:
                index_event_record(db, str(matched_event_id), commit=False)
            db.commit()
        except Exception:
            db.rollback()
    except ValueError as exc:
        db.rollback()
        return error_response(404, "EVENT_NOT_FOUND", str(exc), {"event_id": payload.event_id})
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for report submission.")

    return CitizenReportResponse.model_validate(build_report_response(report))



