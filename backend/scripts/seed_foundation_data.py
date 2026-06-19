from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from alembic import command
from alembic.config import Config

from app.db.session import SessionLocal
from app.services.foundation_seed_service import seed_foundation_data


def main() -> int:
    command.upgrade(Config(str(REPO_ROOT / "alembic.ini")), "head")
    with SessionLocal() as session:
        report = seed_foundation_data(session)
    print(
        "[seed-foundation-data] "
        f"stations={report.stations} users={report.users} incidents={report.incidents} "
        f"votes={report.votes} predictions={report.predictions}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
