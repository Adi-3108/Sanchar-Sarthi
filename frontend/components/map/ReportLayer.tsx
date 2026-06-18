"use client";

import type { LngLat, ProjectedPoint } from "@/lib/map-provider";

export type MapReportPoint = {
  id: string;
  coordinate: LngLat;
  label: string;
  confidence: number;
  source: string;
};

export type ReportLayerProps = {
  reports: MapReportPoint[];
  project: (coordinate: LngLat) => ProjectedPoint | null;
};

export function ReportLayer({ reports, project }: ReportLayerProps) {
  return (
    <>
      {reports.map((report) => {
        const point = project(report.coordinate);
        if (!point) {
          return null;
        }

        return (
          <div
            key={report.id}
            className="group absolute z-20 -translate-x-1/2 -translate-y-1/2"
            style={{ left: `${point.x}%`, top: `${point.y}%` }}
          >
            <span className="block h-3 w-3 rounded-sm border border-cyan-100 bg-cyan-300 shadow-[0_0_18px_rgba(103,232,249,0.4)]" />
            <span className="pointer-events-none absolute left-1/2 top-5 hidden min-w-44 -translate-x-1/2 rounded-2xl border border-slate-700/80 bg-slate-950/95 px-3 py-2 text-left text-xs text-slate-200 shadow-xl group-hover:block">
              <strong className="block text-slate-50">{report.label}</strong>
              <span className="mt-1 block text-slate-400">
                {report.source} report, {Math.round(report.confidence * 100)} confidence
              </span>
            </span>
          </div>
        );
      })}
    </>
  );
}

export default ReportLayer;
