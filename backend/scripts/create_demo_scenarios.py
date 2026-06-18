from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.base import Base, import_model_modules
from app.db.session import SessionLocal, engine
from app.services.demo_scenario_service import seed_demo_scenarios, serialize_demo_seed_report

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
    ensure_schema()

    with SessionLocal() as session:
        report = seed_demo_scenarios(session, commit=True)

    payload = serialize_demo_seed_report(report)
    print("[create-demo-scenarios] deterministic judge walkthrough data refreshed")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
