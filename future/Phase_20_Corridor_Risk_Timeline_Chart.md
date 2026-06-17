# PHASE 20 — Corridor Risk Timeline Chart

## Phase Overview

Create a visual line chart showing hourly risk scores across a week for selected corridors (ORR, Tumkur Road, etc.) — a "risk calendar" derived purely from historical event data. This provides judges and operators with an at-a-glance view of when and where congestion risk is highest.

This phase is part of EventFlow AI, a predictive traffic command twin for Bengaluru event-driven congestion. The project uses ASTraM historical event data, FastAPI, Next.js, Supabase PostgreSQL free tier, explainable AI/rule-based planning, MapmyIndia/Mappls primary integration using available 1000 INR credits, OpenStreetMap fallback, and only free/open-source APIs or services.

---

## Why This Phase Exists

- **Problem being solved:** Traffic operators and judges need a temporal view of corridor risk patterns to understand "when is this road most dangerous?"
- **User need addressed:** Judges will ask "show me the risk pattern over time" — this phase answers with a visual, data-backed timeline chart.
- **Business requirement satisfied:** Demonstrates data visualization innovation, judge-friendly UX, and actionable intelligence for Flipkart Gridlock 2.0 evaluation.
- **Why now:** This phase builds on completed risk scoring and corridor classification phases, adding temporal analytics that support proactive planning.
- **How it contributes:** It strengthens EventFlow AI as a visual intelligence system by showing risk trends across time, enabling pattern recognition and resource pre-positioning.

---

## Original Intent Preservation

### Original Problem

Bengaluru event-driven congestion needs data-backed planning for impact, manpower, barricading, diversions, live escalation, and post-event learning. Understanding temporal risk patterns enables proactive deployment.

### User Pain Point

Traffic response teams lack visibility into when specific corridors are most vulnerable. Users need a "risk calendar" that shows hourly/daily patterns for strategic planning.

### Product Goal

Deliver this capability: Compute hourly risk scores per corridor from historical events, expose via API endpoint, and render as interactive line chart in command center dashboard.

### Architecture Goal

Maintain backend-owned business logic, frontend-only rendering/API consumption, database persistence through Supabase PostgreSQL, and map provider independence.

### Security Goal

Protect sensitive ASTraM fields, avoid frontend database credentials, enforce three-level access, validate all inputs, rate-limit risky endpoints.

### Scalability Goal

Keep aggregation query fast (<2 seconds) using database indexes and efficient grouping. Cache results for frequently requested corridors.

### Performance Goal

API endpoint must respond under 2 seconds. Chart rendering must not slow page load beyond existing 5-second target.

---

## Expected Outcome

After completion:

- **New functionality:** Display hourly risk score timeline for selected corridors across a 7-day period.
- **New APIs:** GET /api/analytics/corridor-risk-timeline?corridor={name}&days={7}
- **New workflows:** Operators select a corridor and view risk patterns by hour and day. Judges see visual proof of data-driven risk assessment.
- **New capabilities:** Temporal risk analytics, corridor comparison, peak hour identification
- **New infrastructure:** backend/app/api/routes_analytics_corridor.py; frontend/app/command-center/components/CorridorRiskTimeline.tsx; frontend/lib/hooks/useCorridorRiskTimeline.ts
- **New data models:** No new tables required; uses existing events and risk_scores

---

## Full Implementation Requirements

Implementation agents must create executable production-ready source files for every path listed in this phase.

Required implementation standards:

- Complete imports, classes, interfaces, functions, DTOs, models, controllers, services, repositories, middleware, tests, and configuration must be written by the implementation agent.
- No paid APIs may be introduced.
- No placeholder or TODO code may be committed.
- All code must be directly executable in the repository.
- All outputs must preserve EventFlow AI's dataset-honest wording: Dataset-backed, Predicted, Estimated, Recommended, Simulated, or Future integration.

### Exact Repository Paths For This Phase

- backend/app/api/routes_analytics_corridor.py
- backend/app/schemas/corridor_analytics.py
- backend/app/services/corridor_risk_service.py
- frontend/app/command-center/components/CorridorRiskTimeline.tsx
- frontend/lib/hooks/useCorridorRiskTimeline.ts

---

## Implementation Code Snippets

### `backend/app/api/routes_analytics_corridor.py`
```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.corridor_analytics import CorridorRiskTimelineResponse
from app.services.corridor_risk_service import CorridorRiskService

router = APIRouter(prefix='/api/analytics', tags=['analytics'])

@router.get('/corridor-risk-timeline', response_model=CorridorRiskTimelineResponse)
def get_corridor_risk_timeline(
    corridor: str = Query(..., description='Corridor name (e.g., ORR, Tumkur Road)'),
    days: int = Query(default=7, ge=1, le=30, description='Number of days to analyze'),
    db: Session = Depends(get_db)
) -> CorridorRiskTimelineResponse:
    service = CorridorRiskService(db)
    return service.get_risk_timeline(corridor, days)
```

### `backend/app/schemas/corridor_analytics.py`
```python
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
```

### `backend/app/services/corridor_risk_service.py`
```python
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.orm.events import Event
from app.schemas.corridor_analytics import CorridorRiskTimelineResponse, HourlyRiskPoint

class CorridorRiskService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_risk_timeline(self, corridor: str, days: int) -> CorridorRiskTimelineResponse:
        # Query historical events for the corridor
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Aggregate events by hour and day of week
        query = (
            self.db.query(
                func.extract('hour', Event.start_datetime).label('hour'),
                func.extract('dow', Event.start_datetime).label('day_of_week'),
                func.avg(Event.computed_risk_score).label('avg_risk'),
                func.count(Event.id).label('event_count')
            )
            .filter(Event.corridor.ilike(f'%{corridor}%'))
            .filter(Event.start_datetime >= start_date)
            .filter(Event.start_datetime <= end_date)
            .filter(Event.computed_risk_score.isnot(None))
            .group_by('hour', 'day_of_week')
            .order_by('day_of_week', 'hour')
        )
        
        results = query.all()
        
        # Build hourly risk points
        hourly_scores = []
        total_risk = 0.0
        risk_by_hour = {}
        
        for row in results:
            hour = int(row.hour)
            dow = int(row.day_of_week)
            risk = float(row.avg_risk)
            count = int(row.event_count)
            
            # Generate timestamp for visualization (using current week as reference)
            base_date = end_date - timedelta(days=end_date.weekday())
            timestamp = (base_date + timedelta(days=dow, hours=hour)).isoformat()
            
            hourly_scores.append(HourlyRiskPoint(
                timestamp=timestamp,
                hour=hour,
                day_of_week=dow,
                risk_score=round(risk, 2),
                event_count=count
            ))
            
            total_risk += risk
            risk_by_hour[hour] = risk_by_hour.get(hour, 0) + risk
        
        # Identify peak risk hours (top 3)
        sorted_hours = sorted(risk_by_hour.items(), key=lambda x: x[1], reverse=True)
        peak_hours = [h for h, _ in sorted_hours[:3]]
        
        avg_risk = round(total_risk / len(results), 2) if results else 0.0
        
        return CorridorRiskTimelineResponse(
            corridor=corridor,
            days_analyzed=days,
            hourly_risk_scores=hourly_scores,
            peak_risk_hours=peak_hours,
            average_risk_score=avg_risk
        )
```

### `frontend/app/command-center/components/CorridorRiskTimeline.tsx`
```tsx
'use client';

import { useCorridorRiskTimeline } from '@/lib/hooks/useCorridorRiskTimeline';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import { TrendingUp, AlertCircle } from 'lucide-react';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

interface CorridorRiskTimelineProps {
  corridor: string;
  days?: number;
}

export default function CorridorRiskTimeline({ corridor, days = 7 }: CorridorRiskTimelineProps) {
  const { data, isLoading, error } = useCorridorRiskTimeline(corridor, days);

  if (isLoading) {
    return (
      <div className="border rounded-lg p-6 bg-white shadow-sm">
        <div className="flex items-center gap-2 text-gray-500">
          <TrendingUp className="w-5 h-5 animate-pulse" />
          <span>Loading risk timeline...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="border rounded-lg p-6 bg-red-50 border-red-200">
        <div className="flex items-center gap-2 text-red-600">
          <AlertCircle className="w-5 h-5" />
          <span>Failed to load risk timeline</span>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const chartData = {
    labels: data.hourly_risk_scores.map(point => {
      const date = new Date(point.timestamp);
      return `${['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][point.day_of_week]} ${point.hour}:00`;
    }),
    datasets: [
      {
        label: 'Risk Score',
        data: data.hourly_risk_scores.map(point => point.risk_score),
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.4
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { display: false },
      title: {
        display: true,
        text: `${corridor} - Risk Timeline (${days} days)`
      },
      tooltip: {
        callbacks: {
          afterLabel: (context: any) => {
            const point = data.hourly_risk_scores[context.dataIndex];
            return `Events: ${point.event_count}`;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: { display: true, text: 'Risk Score' }
      }
    }
  };

  return (
    <div className="border rounded-lg p-6 bg-white shadow-sm">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-blue-600" />
          Corridor Risk Timeline
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          Dataset-backed hourly risk patterns for {corridor}
        </p>
      </div>
      
      <Line data={chartData} options={chartOptions} />
      
      <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
        <div className="bg-gray-50 p-3 rounded">
          <div className="text-gray-500">Avg Risk Score</div>
          <div className="text-xl font-bold text-gray-900">{data.average_risk_score}</div>
        </div>
        <div className="bg-red-50 p-3 rounded">
          <div className="text-gray-500">Peak Risk Hours</div>
          <div className="text-xl font-bold text-red-600">
            {data.peak_risk_hours.map(h => `${h}:00`).join(', ')}
          </div>
        </div>
        <div className="bg-blue-50 p-3 rounded">
          <div className="text-gray-500">Data Points</div>
          <div className="text-xl font-bold text-blue-600">{data.hourly_risk_scores.length}</div>
        </div>
      </div>
    </div>
  );
}
```

### `frontend/lib/hooks/useCorridorRiskTimeline.ts`
```ts
import { useQuery } from '@tanstack/react-query';
import { API_BASE_URL } from '../api';

interface HourlyRiskPoint {
  timestamp: string;
  hour: number;
  day_of_week: number;
  risk_score: number;
  event_count: number;
}

interface CorridorRiskTimelineResponse {
  corridor: string;
  days_analyzed: number;
  hourly_risk_scores: HourlyRiskPoint[];
  peak_risk_hours: number[];
  average_risk_score: number;
}

export function useCorridorRiskTimeline(corridor: string, days: number = 7) {
  return useQuery<CorridorRiskTimelineResponse>({
    queryKey: ['corridor-risk-timeline', corridor, days],
    queryFn: async () => {
      const response = await fetch(
        `${API_BASE_URL}/api/analytics/corridor-risk-timeline?corridor=${encodeURIComponent(corridor)}&days=${days}`,
        { cache: 'no-store' }
      );
      if (!response.ok) {
        throw new Error('Failed to fetch corridor risk timeline');
      }
      return response.json();
    },
    enabled: !!corridor,
    staleTime: 10 * 60 * 1000 // 10 minutes
  });
}
```

---

## Database Requirements

- **Database entities affected:** events (read-only), risk_scores (read-only)
- **Migration requirements:** None - uses existing event and risk_score data.
- **SQL statements:** Use SQLAlchemy ORM with aggregation functions (AVG, COUNT, GROUP BY).
- **Indexes:** Ensure indexes exist on events.corridor, events.start_datetime, events.computed_risk_score.
- **Constraints and foreign keys:** None required.
- **Composite indexes:** Create composite index on (corridor, start_datetime) for fast filtering.
- **RLS policies:** Not required in MVP.
- **Triggers/stored procedures/functions:** None required.
- **Materialized views:** Optional future optimization for frequently requested corridors.
- **Rollback migrations:** N/A.
- **Seed data:** Uses existing events data from Phase 17.

---

## API Requirements

- **APIs affected:** GET /api/analytics/corridor-risk-timeline
- **Route definitions:** Register under FastAPI /api/analytics router.
- **Request schemas:** Query parameters: corridor (required), days (optional, default 7).
- **Response schemas:** CorridorRiskTimelineResponse with hourly_risk_scores array.
- **Validation logic:** Validate corridor name non-empty, days between 1-30.
- **Error handling:** Return 404 if corridor has no data, 400 for invalid parameters.
- **Authentication:** Public endpoint with rate limiting (Level 3 access).
- **Authorization:** No special authorization required.
- **Rate limiting:** Apply 50 requests/minute per IP.
- **Audit logging:** Log corridor analytics requests.
- **OpenAPI:** FastAPI exposes schema automatically.

---

## Frontend Requirements

- **Frontend scope:** /command-center integration for CorridorRiskTimeline component
- **Pages/components:** Create CorridorRiskTimeline.tsx component with Chart.js line chart.
- **Hooks:** Use TanStack Query via useCorridorRiskTimeline hook.
- **State management:** No global state needed; corridor selection from parent component.
- **Forms:** N/A, component receives corridor prop.
- **API integrations:** GET /api/analytics/corridor-risk-timeline via hook.
- **Error states:** Show "Failed to load risk timeline" message.
- **Loading states:** Show loading spinner with "Loading risk timeline..." message.
- **Empty states:** Show "No risk data available for this corridor" if empty dataset.
- **Permission handling:** Public component, no auth required.
- **Routing:** Integrate into existing /command-center page as corridor analytics panel.

---

## Infrastructure Requirements

- **Dockerfiles:** No changes required.
- **docker-compose:** No changes required.
- **Kubernetes/Terraform:** Not required for MVP.
- **CI/CD:** No changes required.
- **Environment configuration:** No new environment variables required.
- **Secrets configuration:** N/A.
- **Monitoring configuration:** Monitor /api/analytics/corridor-risk-timeline response time (target <2s).
- **Logging configuration:** Log corridor analytics queries for usage analytics.
- **Alerting configuration:** Alert if response time exceeds 3 seconds or error rate > 5%.

---

## Security Requirements

- **Authentication model:** Public endpoint, rate-limited.
- **Authorization model:** No authorization required for analytics.
- **Threat model:** Protect against excessive queries, SQL injection (via parameterization).
- **Secrets management:** N/A.
- **Audit requirements:** Log corridor name and days parameter for usage tracking.
- **Encryption requirements:** HTTPS in deployed environments.
- **Compliance requirements:** No personal data in response.
- **Security controls:** Rate limiting, input validation, parameterized queries.

---

## Testing Requirements

### Unit Tests

Test CorridorRiskService.get_risk_timeline() with sample corridor data.

### Integration Tests

Test GET /api/analytics/corridor-risk-timeline endpoint with valid/invalid corridors.

### E2E Tests

Verify CorridorRiskTimeline component renders chart correctly in command center.

### Security Tests

Validate rate limiting, SQL injection protection, invalid parameter rejection.

### Performance Tests

Verify endpoint responds under 2 seconds for 7-day query.

### Load Tests

Test 50 concurrent requests for different corridors.

### Contract Tests

Ensure frontend CorridorRiskTimelineResponse matches backend schema.

---

## Cross-Phase References & Dependency Tracking

- **Required previous phases:** Phase 4 (risk scoring), Phase 17 (event data ingestion)
- **Integration method:** Reads events and computed_risk_score, exposes analytics API, integrates into command-center UI.
- **Compatibility requirements:** Do not break existing event schemas or API contracts.
- **Required interfaces:** GET /api/analytics/corridor-risk-timeline
- **Required contracts:** CorridorRiskTimelineResponse schema.
- **Validation process:** Query endpoint with sample corridors, verify chart renders correctly.

---

## Deliverables

- backend/app/api/routes_analytics_corridor.py
- backend/app/schemas/corridor_analytics.py
- backend/app/services/corridor_risk_service.py
- frontend/app/command-center/components/CorridorRiskTimeline.tsx
- frontend/lib/hooks/useCorridorRiskTimeline.ts

---

## Technical Design Summary

Build an analytics endpoint that aggregates historical events by hour and day of week for a selected corridor, computing average risk scores and event counts. Frontend renders results as interactive Chart.js line chart showing temporal risk patterns. Identify peak risk hours for operational planning. Zero additional data collection required — purely derived from existing event history.

---

## Validation Checklist

### Automated Verification

Run pytest for analytics endpoint, frontend build, integration tests.

### Manual Verification

Test chart rendering for ORR, Tumkur Road, and other major corridors in command center UI.

### Integration Verification

Verify corridor selector integrates with timeline chart component.

### Security Verification

Check rate limiting, input validation, no sensitive data exposure.

### Performance Verification

Measure endpoint response time for 7-day and 30-day queries (target <2s).

---

## Validation Commands

```bash
pytest backend/app/api/test_routes_analytics_corridor.py
npm run build
npm run test
```

---

## Completion Criteria

Phase is complete only if:

- Analytics endpoint returns hourly risk scores correctly.
- Chart renders smoothly for all major corridors.
- Response time under 2 seconds for 7-day query.
- Tests pass.
- Security checks pass.
- No paid API dependency is introduced.
- Documentation updated.
