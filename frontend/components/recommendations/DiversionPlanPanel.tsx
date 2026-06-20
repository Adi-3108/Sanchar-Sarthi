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
        className={`rounded-[28px] border border-dashed border-slate-700/80 bg-slate-950/60 p-6 text-sm text-slate-400 ${
          className ?? ""
        }`}
      >
        Diversion recommendation is not available yet.
      </section>
    );
  }

  return (
    <section
      className={`flex flex-col h-full rounded-[28px] border border-slate-800/80 bg-slate-950/85 p-6 shadow-[0_18px_40px_rgba(2,6,23,0.35)] ${
        className ?? ""
      }`}
    >
      <p className="text-[11px] uppercase tracking-[0.24em] text-emerald-300/80">Diversion Plan</p>
      <h2 className="mt-2 text-2xl font-semibold text-slate-100">{diversions.strategy.replaceAll("_", " ")}</h2>
      <p className="mt-3 text-sm leading-7 text-slate-300">{diversions.note}</p>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <MetricCard label="Corridor to protect" value={diversions.corridor_to_protect ?? "n/a"} />
        <MetricCard label="Diversion scope" value={diversions.diversion_scope} />
      </div>

      <div className="mt-6 rounded-3xl border border-slate-800/70 bg-slate-900/70 p-4">
        <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Upstream focus points</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {diversions.upstream_focus_points.map((point) => (
            <span
              key={point}
              className="rounded-full border border-slate-700/80 bg-slate-950/80 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-slate-300"
            >
              {point}
            </span>
          ))}
        </div>
      </div>

      <p className="mt-auto pt-5 text-sm leading-7 text-slate-300">{diversions.heavy_vehicle_advisory}</p>
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-4">
      <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-2 text-base font-semibold text-slate-100">{value}</p>
    </article>
  );
}

export default DiversionPlanPanel;
