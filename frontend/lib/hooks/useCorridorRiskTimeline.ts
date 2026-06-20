import { useQuery } from '@tanstack/react-query';
import { apiGet } from '../api';

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
    queryFn: () => {
      return apiGet<CorridorRiskTimelineResponse>(
        `/api/analytics/corridor-risk-timeline?corridor=${encodeURIComponent(corridor)}&days=${days}`
      );
    },
    enabled: !!corridor,
    staleTime: 10 * 60 * 1000
  });
}

