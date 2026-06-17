from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings
from app.db.base import Base, import_model_modules
from app.db.session import SessionLocal, engine
from app.services.data_cleaning_service import ingest_astram_csv_file

try:
    from alembic import command
    from alembic.config import Config
except (ImportError, ModuleNotFoundError):  # pragma: no cover - depends on local interpreter packages
    command = None
    Config = None


def ensure_schema() -> None:
    if command is not None and Config is not None:
        alembic_config = Config(str(REPO_ROOT / "alembic.ini"))
        command.upgrade(alembic_config, "head")
        return

    import_model_modules()
    Base.metadata.create_all(bind=engine)


def main() -> int:
    settings = get_settings()
    dataset_path = settings.resolved_raw_data_path
    if not dataset_path.exists():
        print(f"[seed-demo-data] demo dataset not found: {dataset_path}")
        return 1

    ensure_schema()

    with SessionLocal() as session:
        report = ingest_astram_csv_file(session, dataset_path)

    print(
        f"[seed-demo-data] loaded={report.rows_upserted} invalid={report.invalid_rows} "
        f"columns={report.columns_detected} source='{dataset_path.name}'"
    )
    if report.sample_errors:
        print(f"[seed-demo-data] sample_errors={report.sample_errors}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
