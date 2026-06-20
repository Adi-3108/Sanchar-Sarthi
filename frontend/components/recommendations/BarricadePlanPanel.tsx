"use client";

import type { RecommendationBarricadeResponse } from "@/lib/api";

export type BarricadePlanPanelProps = {
  barricades: RecommendationBarricadeResponse | null | undefined;
  className?: string;
};

export function BarricadePlanPanel({ barricades, className }: BarricadePlanPanelProps) {
  if (!barricades) {
    return (
      <section
        className={`rounded-[28px] border border-dashed border-slate-700/80 bg-slate-950/60 p-6 text-sm text-slate-400 ${
          className ?? ""
        }`}
      >
        Barricade recommendation is not available yet.
      </section>
    );
  }

  return (
    <section
      className={`flex flex-col h-full rounded-[28px] border border-slate-800/80 bg-slate-950/85 p-6 shadow-[0_18px_40px_rgba(2,6,23,0.35)] ${
        className ?? ""
      }`}
    >
      <p className="text-[11px] uppercase tracking-[0.24em] text-amber-300/80">Barricade Plan</p>
      <h2 className="mt-2 text-2xl font-semibold text-slate-100">
        {barricades.barricade_level.replaceAll("_", " ")}
      </h2>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <MetricCard label="Estimated units" value={String(barricades.estimated_units)} />
        <MetricCard label="Coverage radius" value={`${barricades.coverage_radius_km.toFixed(2)} km`} />
      </div>
      <div className="mt-6 flex flex-wrap gap-2">
        {barricades.placement_priority.map((item) => (
          <span
            key={item}
            className="rounded-full border border-slate-700/80 bg-slate-950/80 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-slate-300"
          >
            {item}
          </span>
        ))}
      </div>
      <p className="mt-auto pt-5 text-sm leading-7 text-slate-300">{barricades.note}</p>
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

export default BarricadePlanPanel;
