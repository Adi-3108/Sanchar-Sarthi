from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.base import Base, import_model_modules
from app.db.session import SessionLocal, engine
from app.services.event_dna_service import rebuild_event_dna_records

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
    parser = argparse.ArgumentParser(description="Rebuild Event DNA records and similar-event memory.")
    parser.add_argument("--event-id", help="Optional event ID to rebuild a single Event DNA record.")
    parser.add_argument("--limit-similar", type=int, default=5, help="Maximum similar events to persist per event.")
    args = parser.parse_args()

    ensure_schema()

    with SessionLocal() as session:
        try:
            report = rebuild_event_dna_records(
                session,
                event_id=args.event_id,
                limit_similar=args.limit_similar,
                refresh_supporting_data=True,
            )
        except ValueError as exc:
            print(f"[rebuild-event-dna] {exc}")
            return 1

    print(
        f"[rebuild-event-dna] processed={report.events_processed} created={report.dna_created} "
        f"updated={report.dna_updated} scope='{args.event_id or 'all'}' limit_similar={args.limit_similar}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
