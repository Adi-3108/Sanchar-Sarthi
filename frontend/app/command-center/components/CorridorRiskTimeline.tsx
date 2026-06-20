'use client';

import { useCorridorRiskTimeline } from '@/lib/hooks/useCorridorRiskTimeline';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  type ChartData,
  type ChartOptions,
  type TooltipItem
} from 'chart.js';
import { TrendingUp, AlertCircle } from 'lucide-react';
import { ApiError } from '@/lib/api';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

interface CorridorRiskTimelineProps {
  corridor: string;
  days?: number;
}

const dayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function errorMessage(error: unknown, corridor: string): string {
  if (error instanceof ApiError && error.status === 404) {
    return `No dataset-backed risk timeline is available for ${corridor} yet.`;
  }
  return `Failed to load risk timeline for ${corridor}.`;
}

export default function CorridorRiskTimeline({ corridor, days = 7 }: CorridorRiskTimelineProps) {
  const { data, isLoading, error } = useCorridorRiskTimeline(corridor, days);

  if (isLoading) {
    return (
      <div className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-6 shadow-panel">
        <div className="flex items-center gap-2 text-muted">
          <TrendingUp className="w-5 h-5 animate-pulse" />
          <span>Loading risk timeline...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-[24px] border border-danger/40 bg-danger/10 p-6 shadow-panel">
        <div className="flex items-center gap-2 text-danger">
          <AlertCircle className="w-5 h-5" />
          <span>{errorMessage(error, corridor)}</span>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const chartData: ChartData<'line'> = {
    labels: data.hourly_risk_scores.map((point) => `${dayLabels[point.day_of_week]} ${point.hour}:00`),
    datasets: [
      {
        label: 'Risk Score',
        data: data.hourly_risk_scores.map((point) => point.risk_score),
        borderColor: 'rgb(56, 189, 248)',
        backgroundColor: 'rgba(56, 189, 248, 0.1)',
        tension: 0.3,
        pointRadius: 1.5,
        pointHoverRadius: 4
      }
    ]
  };

  const chartOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      title: {
        display: false
      },
      tooltip: {
        callbacks: {
          afterLabel: (context: TooltipItem<'line'>) => {
            const point = data.hourly_risk_scores[context.dataIndex];
            return `Events: ${point.event_count}`;
          }
        }
      }
    },
    scales: {
      x: {
        ticks: {
          maxRotation: 0,
          autoSkip: true,
          maxTicksLimit: 14
        }
      },
      y: {
        beginAtZero: true,
        suggestedMax: 100,
        title: { display: true, text: 'Risk Score' }
      }
    }
  };

  return (
    <div className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-6 shadow-panel h-full flex flex-col">
      <div className="mb-4">
        <h3 className="text-2xl font-semibold flex items-center gap-2">
          <TrendingUp className="w-6 h-6 text-sky-400" />
          Corridor Risk Timeline
        </h3>
        <p className="text-sm leading-7 text-muted mt-1">
          Dataset-backed hourly risk patterns for {corridor}, anchored to the latest available corridor history.
        </p>
      </div>

      <div className="flex-grow relative min-h-[300px]">
        <Line data={chartData} options={chartOptions} />
      </div>

      <div className="mt-6 grid grid-cols-3 gap-4 text-sm">
        <div className="rounded-2xl border border-line/70 bg-bg/60 p-4">
          <div className="text-[11px] uppercase tracking-[0.22em] text-accentSoft">Avg Risk</div>
          <div className="text-xl font-bold text-copy mt-1">{data.average_risk_score}</div>
        </div>
        <div className="rounded-2xl border border-danger/40 bg-danger/10 p-4">
          <div className="text-[11px] uppercase tracking-[0.22em] text-danger/80">Peak Risk Hours</div>
          <div className="text-xl font-bold text-danger mt-1">
            {data.peak_risk_hours.length > 0 ? data.peak_risk_hours.map((hour) => `${hour}:00`).join(', ') : 'n/a'}
          </div>
        </div>
        <div className="rounded-2xl border border-line/70 bg-bg/60 p-4">
          <div className="text-[11px] uppercase tracking-[0.22em] text-accentSoft">Data Points</div>
          <div className="text-xl font-bold text-sky-400 mt-1">{data.hourly_risk_scores.length}</div>
        </div>
      </div>
    </div>
  );
}

