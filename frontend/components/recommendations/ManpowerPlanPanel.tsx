"use client";

import type { RecommendationManpowerResponse } from "@/lib/api";

export type ManpowerPlanPanelProps = {
  manpower: RecommendationManpowerResponse | null | undefined;
  className?: string;
};

export function ManpowerPlanPanel({ manpower, className }: ManpowerPlanPanelProps) {
  if (!manpower) {
    return (
      <section
        className={`rounded-[28px] border border-dashed border-slate-700/80 bg-slate-950/60 p-6 text-sm text-slate-400 ${
          className ?? ""
        }`}
      >
        Manpower recommendation is not available yet.
      </section>
    );
  }

  return (
    <section
      className={`flex flex-col h-full rounded-[28px] border border-slate-800/80 bg-slate-950/85 p-6 shadow-[0_18px_40px_rgba(2,6,23,0.35)] ${
        className ?? ""
      }`}
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-cyan-300/80">Manpower Plan</p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-100">Officer deployment posture</h2>
        </div>
        <p className="text-3xl font-semibold text-slate-100">{manpower.recommended_total_officers}</p>
      </div>

      <div className="mt-6 grid gap-4 grid-cols-2">
        <MetricCard label="Deployment style" value={manpower.deployment_style.replaceAll("_", " ")} />
        <MetricCard label="Reserve officers" value={String(manpower.reserve_officers)} />
        <MetricCard label="Sector count" value={String(manpower.sector_count)} />
        <MetricCard label="Officer gap" value={String(manpower.officer_gap)} />
      </div>

      <div className="mt-6 rounded-3xl border border-slate-800/70 bg-slate-900/70 p-4">
        <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Primary positions</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {manpower.primary_positions.map((position) => (
            <span
              key={position}
              className="rounded-full border border-slate-700/80 bg-slate-950/80 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-slate-300"
            >
              {position}
            </span>
          ))}
        </div>
      </div>

      <p className="mt-auto pt-5 text-sm leading-7 text-slate-300">{manpower.note}</p>
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-4">
      <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-slate-100">{value}</p>
    </article>
  );
}

export default ManpowerPlanPanel;
