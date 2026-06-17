from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import AuthContext, require_role
from app.db.session import get_db
from app.orm.system_audit_log import SystemAuditLog
from app.services.data_cleaning_service import (
    IngestionReport,
    ingest_astram_csv_bytes,
    ingest_astram_csv_file,
)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class DatasetLoadResponse(BaseModel):
    status: str
    rows_loaded: int
    columns_detected: int
    invalid_rows: int
    message: str | None = None


router = APIRouter(prefix="/api/datasets", tags=["datasets"])


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


def require_admin_or_control_room(
    auth: AuthContext = Depends(require_role("admin", "control_room")),
) -> AuthContext:
    return auth


def _coerce_uuid(value: str | None) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(value)
    except (ValueError, TypeError):
        return None


def _record_dataset_audit_log(
    db: Session,
    auth: AuthContext,
    *,
    action: str,
    resource_id: str,
    report: IngestionReport,
) -> None:
    db.add(
        SystemAuditLog(
            actor_user_id=_coerce_uuid(auth.user_account_id),
            actor_role=auth.role,
            action=action,
            resource_type="dataset",
            resource_id=resource_id,
            metadata_json={
                "rows_processed": report.rows_processed,
                "rows_upserted": report.rows_upserted,
                "invalid_rows": report.invalid_rows,
                "columns_detected": report.columns_detected,
                "sample_errors": report.sample_errors,
            },
        )
    )
    db.commit()


def _success_payload(report: IngestionReport, *, message: str | None = None) -> DatasetLoadResponse:
    return DatasetLoadResponse(
        status="success",
        rows_loaded=report.rows_upserted,
        columns_detected=report.columns_detected,
        invalid_rows=report.invalid_rows,
        message=message,
    )


@router.post("/load-demo", response_model=DatasetLoadResponse)
def load_demo_dataset(
    auth: AuthContext = Depends(require_admin_or_control_room),
    db: Session = Depends(get_db),
):
    dataset_path = get_settings().resolved_raw_data_path
    if not dataset_path.exists():
        return error_response(
            404,
            "DATASET_NOT_FOUND",
            "Configured demo dataset was not found.",
            {"path": str(dataset_path)},
        )

    try:
        report = ingest_astram_csv_file(db, dataset_path)
        _record_dataset_audit_log(
            db,
            auth,
            action="dataset_load_demo",
            resource_id=dataset_path.name,
            report=report,
        )
    except ValueError as exc:
        db.rollback()
        return error_response(400, "VALIDATION_ERROR", str(exc))
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for dataset loading.")

    return _success_payload(report, message="Demo dataset loaded.")


@router.post("/upload", response_model=DatasetLoadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    auth: AuthContext = Depends(require_admin_or_control_room),
    db: Session = Depends(get_db),
):
    filename = file.filename or "uploaded.csv"
    if Path(filename).suffix.lower() != ".csv":
        return error_response(
            400,
            "VALIDATION_ERROR",
            "Only CSV uploads are supported.",
            {"filename": filename},
        )

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        return error_response(
            400,
            "VALIDATION_ERROR",
            "Uploaded CSV exceeds the 10 MB MVP limit.",
            {"filename": filename, "size_bytes": len(content)},
        )

    try:
        report = ingest_astram_csv_bytes(db, content)
        _record_dataset_audit_log(
            db,
            auth,
            action="dataset_upload",
            resource_id=filename,
            report=report,
        )
    except ValueError as exc:
        db.rollback()
        return error_response(400, "VALIDATION_ERROR", str(exc))
    except SQLAlchemyError:
        db.rollback()
        return error_response(503, "DATABASE_UNAVAILABLE", "Database is unavailable for dataset upload.")

    return _success_payload(report)
