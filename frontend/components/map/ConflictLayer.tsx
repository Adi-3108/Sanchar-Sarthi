"use client";

import type { LngLat, ProjectedPoint } from "@/lib/map-provider";

export type ConflictOverlay = {
  id: string;
  eventIds: string[];
  coordinates: [LngLat, LngLat];
  conflictLevel: string;
  conflictScore: number;
};

export type ConflictLayerProps = {
  conflicts: ConflictOverlay[];
  project: (coordinate: LngLat) => ProjectedPoint | null;
};

function conflictColor(level: string): string {
  const normalized = level.toLowerCase();
  if (normalized === "critical") {
    return "#ef4444";
  }
  if (normalized === "high") {
    return "#f97316";
  }
  if (normalized === "medium") {
    return "#f59e0b";
  }
  return "#22c55e";
}

export function ConflictLayer({ conflicts, project }: ConflictLayerProps) {
  return (
    <svg className="pointer-events-none absolute inset-0 z-10 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
      {conflicts.map((conflict) => {
        const left = project(conflict.coordinates[0]);
        const right = project(conflict.coordinates[1]);
        if (!left || !right) {
          return null;
        }
        const color = conflictColor(conflict.conflictLevel);

        return (
          <g key={conflict.id}>
            <line
              x1={left.x}
              y1={left.y}
              x2={right.x}
              y2={right.y}
              stroke="rgba(2,6,23,0.85)"
              strokeLinecap="round"
              strokeWidth="3"
            />
            <line
              x1={left.x}
              y1={left.y}
              x2={right.x}
              y2={right.y}
              stroke={color}
              strokeDasharray="3 2"
              strokeLinecap="round"
              strokeWidth="1.4"
            />
            <circle cx={(left.x + right.x) / 2} cy={(left.y + right.y) / 2} r="1.4" fill={color} />
          </g>
        );
      })}
    </svg>
  );
}

export default ConflictLayer;
