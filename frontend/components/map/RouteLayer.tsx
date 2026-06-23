"use client";

import type { LngLat, ProjectedPoint } from "@/lib/map-provider";

export type RouteOverlay = {
  id: string;
  label: string;
  polyline: LngLat[];
  kind: "diversion" | "emergency" | "logistics";
};

export type RouteLayerProps = {
  routes: RouteOverlay[];
  project: (coordinate: LngLat) => ProjectedPoint | null;
};

function routeColor(kind: RouteOverlay["kind"]): string {
  if (kind === "emergency") {
    return "#f87171";
  }
  if (kind === "logistics") {
    return "#60a5fa";
  }
  return "#fbbf24";
}

function pointsForRoute(route: RouteOverlay, project: (coordinate: LngLat) => ProjectedPoint | null): string | null {
  const points = route.polyline
    .map((coordinate) => project(coordinate))
    .filter((point): point is ProjectedPoint => Boolean(point))
    .map((point) => `${point.x},${point.y}`);
  return points.length >= 2 ? points.join(" ") : null;
}

export function RouteLayer({ routes, project }: RouteLayerProps) {
  return (
    <svg className="pointer-events-none absolute inset-0 z-10 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
      {routes.map((route) => {
        const points = pointsForRoute(route, project);
        if (!points) {
          return null;
        }

        return (
          <g key={route.id}>
            <polyline
              points={points}
              fill="none"
              stroke="rgba(2,6,23,0.72)"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2.8"
            />
            <polyline
              points={points}
              fill="none"
              stroke={routeColor(route.kind)}
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="1.4"
            />
          </g>
        );
      })}
    </svg>
  );
}

export default RouteLayer;
