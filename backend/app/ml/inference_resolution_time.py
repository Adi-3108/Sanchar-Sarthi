from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.orm.event import Event
from app.orm.event_feature import EventFeature
from app.services.resolution_time_service import predict_resolution_time


def infer_resolution_time(
    event: Event,
    *,
    feature: EventFeature | None = None,
) -> dict[str, object]:
    return predict_resolution_time(event, feature=feature)
