from pydantic import BaseModel

class HourlyRiskPoint(BaseModel):
    timestamp: str
    hour: int
    day_of_week: int
    risk_score: float
    event_count: int

class CorridorRiskTimelineResponse(BaseModel):
    corridor: str
    days_analyzed: int
    hourly_risk_scores: list[HourlyRiskPoint]
    peak_risk_hours: list[int]
    average_risk_score: float
