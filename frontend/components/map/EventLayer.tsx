"use client";

import type { LngLat, ProjectedPoint } from "@/lib/map-provider";

export type MapEventPoint = {
  id: string;
  coordinate: LngLat;
  label: string;
  severity: "Low" | "Medium" | "High" | "Critical";
  detail?: string;
};

export type EventLayerProps = {
  events: MapEventPoint[];
  project: (coordinate: LngLat) => ProjectedPoint | null;
  onSelectEvent?: (event: MapEventPoint) => void;
};

function severityClass(severity: MapEventPoint["severity"]): string {
  if (severity === "Critical") {
    return "border-red-300 bg-red-400 shadow-[0_0_30px_rgba(248,113,113,0.45)]";
  }
  if (severity === "High") {
    return "border-orange-300 bg-orange-400 shadow-[0_0_24px_rgba(251,146,60,0.35)]";
  }
  if (severity === "Medium") {
    return "border-amber-200 bg-amber-300 shadow-[0_0_20px_rgba(252,211,77,0.3)]";
  }
  return "border-emerald-200 bg-emerald-300 shadow-[0_0_18px_rgba(110,231,183,0.25)]";
}

export function EventLayer({ events, project, onSelectEvent }: EventLayerProps) {
  return (
    <>
      {events.map((event) => {
        const point = project(event.coordinate);
        if (!point) {
          return null;
        }

        return (
          <button
            key={event.id}
            type="button"
            onClick={() => onSelectEvent?.(event)}
            className="group absolute z-20 -translate-x-1/2 -translate-y-1/2"
            style={{ left: `${point.x}%`, top: `${point.y}%` }}
          >
            <span className={`block h-4 w-4 rounded-full border-2 ${severityClass(event.severity)}`} />
            <span className="pointer-events-none absolute left-1/2 top-6 hidden min-w-44 -translate-x-1/2 rounded-2xl border border-slate-700/80 bg-slate-950/95 px-3 py-2 text-left text-xs text-slate-200 shadow-xl group-hover:block">
              <strong className="block text-slate-50">{event.label}</strong>
              <span className="mt-1 block text-slate-400">{event.detail ?? event.severity}</span>
            </span>
          </button>
        );
      })}
    </>
  );
}

export default EventLayer;
