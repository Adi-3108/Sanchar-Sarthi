from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.corridor_analytics import CorridorRiskTimelineResponse
from app.services.corridor_risk_service import CorridorRiskService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/corridor-risk-timeline", response_model=CorridorRiskTimelineResponse)
def get_corridor_risk_timeline(
    corridor: str = Query(..., description="Corridor name (e.g., ORR, Tumkur Road)"),
    days: int = Query(default=7, ge=1, le=30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
) -> CorridorRiskTimelineResponse:
    corridor_name = corridor.strip()
    if not corridor_name:
        raise HTTPException(status_code=400, detail="Corridor name must not be blank.")

    service = CorridorRiskService(db)
    try:
        return service.get_risk_timeline(corridor_name, days)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Database is unavailable for corridor analytics.") from exc

