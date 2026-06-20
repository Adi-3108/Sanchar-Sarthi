"use client";

import type { RecommendationLogisticsImpactResponse } from "@/lib/api";

export type FlipkartLogisticsImpactPanelProps = {
  logisticsImpact: RecommendationLogisticsImpactResponse | null | undefined;
  className?: string;
};

export function FlipkartLogisticsImpactPanel({
  logisticsImpact,
  className
}: FlipkartLogisticsImpactPanelProps) {
  if (!logisticsImpact) {
    return (
      <section
        className={`rounded-[28px] border border-dashed border-slate-700/80 bg-slate-950/60 p-6 text-sm text-slate-400 ${
          className ?? ""
        }`}
      >
        Flipkart logistics impact is not included in this recommendation.
      </section>
    );
  }

  return (
    <section
      className={`flex flex-col h-full rounded-[28px] border border-slate-800/80 bg-slate-950/85 p-6 shadow-[0_18px_40px_rgba(2,6,23,0.35)] ${
        className ?? ""
      }`}
    >
      <p className="text-[11px] uppercase tracking-[0.24em] text-fuchsia-300/80">Logistics Impact</p>
      <h2 className="mt-2 text-2xl font-semibold text-slate-100">
        {logisticsImpact.impact_level.replaceAll("_", " ")}
      </h2>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <MetricCard
          label="Risk window"
          value={`${logisticsImpact.delivery_risk_window_minutes} min`}
        />
        <MetricCard
          label="Affected radius"
          value={`${logisticsImpact.affected_radius_km.toFixed(2)} km`}
        />
      </div>
      <p className="mt-5 text-sm leading-7 text-slate-300">{logisticsImpact.dispatch_recommendation}</p>
      <p className="mt-auto pt-4 text-sm leading-7 text-slate-400">{logisticsImpact.warehouse_note}</p>
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

export default FlipkartLogisticsImpactPanel;
