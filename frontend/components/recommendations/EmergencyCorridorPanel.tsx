"use client";

import type { RecommendationEmergencyCorridorResponse } from "@/lib/api";

export type EmergencyCorridorPanelProps = {
  emergencyCorridor: RecommendationEmergencyCorridorResponse | null | undefined;
  className?: string;
};

export function EmergencyCorridorPanel({
  emergencyCorridor,
  className
}: EmergencyCorridorPanelProps) {
  if (!emergencyCorridor) {
    return (
      <section
        className={`rounded-[28px] border border-dashed border-slate-200 bg-white p-6 text-sm text-slate-500 ${
          className ?? ""
        }`}
      >
        Emergency corridor advisory is not active for this recommendation.
      </section>
    );
  }

  return (
    <section
      className={`flex flex-col h-full rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm ${
        className ?? ""
      }`}
    >
      <p className="text-[11px] uppercase tracking-[0.24em] text-rose-300/80">Emergency Corridor</p>
      <h2 className="mt-2 text-2xl font-semibold text-slate-900">
        {emergencyCorridor.priority.replaceAll("_", " ")}
      </h2>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <MetricCard label="Protected corridor" value={emergencyCorridor.protected_corridor ?? "n/a"} />
        <MetricCard label="Activation trigger" value={emergencyCorridor.activation_trigger} />
      </div>
      <p className="mt-5 text-sm leading-7 text-slate-600">{emergencyCorridor.lane_policy}</p>
      <p className="mt-auto pt-4 text-sm leading-7 text-slate-500">{emergencyCorridor.authentication_note}</p>
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

export default EmergencyCorridorPanel;
