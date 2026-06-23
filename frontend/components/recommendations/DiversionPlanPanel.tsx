"use client";

import type { RecommendationDiversionResponse } from "@/lib/api";

export type DiversionPlanPanelProps = {
  diversions: RecommendationDiversionResponse | null | undefined;
  className?: string;
};

export function DiversionPlanPanel({ diversions, className }: DiversionPlanPanelProps) {
  if (!diversions) {
    return (
      <section
        className={`rounded-[28px] border border-dashed border-slate-200 bg-white p-6 text-sm text-slate-500 ${
          className ?? ""
        }`}
      >
        Diversion recommendation is not available yet.
      </section>
    );
  }

  return (
    <section
      className={`flex flex-col h-full rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm ${
        className ?? ""
      }`}
    >
      <p className="text-[11px] uppercase tracking-[0.24em] text-emerald-300/80">Diversion Plan</p>
      <h2 className="mt-2 text-2xl font-semibold text-slate-900">{diversions.strategy.replaceAll("_", " ")}</h2>
      <p className="mt-3 text-sm leading-7 text-slate-600">{diversions.note}</p>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <MetricCard label="Corridor to protect" value={diversions.corridor_to_protect ?? "n/a"} />
        <MetricCard label="Diversion scope" value={diversions.diversion_scope} />
      </div>

      <div className="mt-6 rounded-3xl border border-slate-200 bg-white p-4">
        <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Upstream focus points</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {diversions.upstream_focus_points.map((point) => (
            <span
              key={point}
              className="rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-slate-600"
            >
              {point}
            </span>
          ))}
        </div>
      </div>

      <p className="mt-auto pt-5 text-sm leading-7 text-slate-600">{diversions.heavy_vehicle_advisory}</p>
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4">
      <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-2 text-base font-semibold text-slate-900">{value}</p>
    </article>
  );
}

export default DiversionPlanPanel;
