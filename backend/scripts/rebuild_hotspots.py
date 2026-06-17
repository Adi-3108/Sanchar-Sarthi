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
from app.services.hotspot_service import rebuild_hotspots

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
    parser = argparse.ArgumentParser(description="Rebuild dataset-backed hotspot clusters.")
    parser.add_argument("--eps-km", type=float, default=0.7, help="DBSCAN neighborhood radius in kilometers.")
    parser.add_argument("--min-samples", type=int, default=3, help="Minimum neighboring events required to form a cluster.")
    args = parser.parse_args()

    ensure_schema()

    with SessionLocal() as session:
        try:
            report = rebuild_hotspots(
                session,
                eps_km=args.eps_km,
                min_samples=args.min_samples,
            )
        except ValueError as exc:
            print(f"[rebuild-hotspots] {exc}")
            return 1

    print(
        f"[rebuild-hotspots] clusters={report.clusters_created} clustered_events={report.clustered_events} "
        f"noise_events={report.noise_events} feature_updates={report.event_features_updated} "
        f"eps_km={args.eps_km} min_samples={args.min_samples}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
