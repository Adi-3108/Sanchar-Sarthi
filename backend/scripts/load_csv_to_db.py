from __future__ import annotations

import argparse
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
    parser = argparse.ArgumentParser(description="Load an ASTraM CSV file into the events table.")
    parser.add_argument("csv_path", nargs="?", help="Path to the ASTraM CSV file.")
    args = parser.parse_args()

    settings = get_settings()
    csv_path = Path(args.csv_path) if args.csv_path else settings.resolved_raw_data_path
    if not csv_path.exists():
        print(f"[dataset-load] CSV not found: {csv_path}")
        return 1

    ensure_schema()

    with SessionLocal() as session:
        report = ingest_astram_csv_file(session, csv_path)

    print(
        f"[dataset-load] processed={report.rows_processed} upserted={report.rows_upserted} "
        f"invalid={report.invalid_rows} columns={report.columns_detected}"
    )
    if report.sample_errors:
        print(f"[dataset-load] sample_errors={report.sample_errors}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
