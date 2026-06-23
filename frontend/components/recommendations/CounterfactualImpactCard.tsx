"use client";

export type CounterfactualImpactCardProps = {
  baselineRiskScore?: number | null;
  eventImpactScore?: number | null;
  additionalEventDelta?: number | null;
  honestyNote?: string | null;
  className?: string;
};

function formatNumber(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "n/a";
  }
  return value.toFixed(digits);
}

function deltaTone(delta: number | null | undefined): string {
  if (delta === null || delta === undefined) {
    return "text-slate-700";
  }
  if (delta >= 25) {
    return "text-red-200";
  }
  if (delta >= 10) {
    return "text-amber-200";
  }
  return "text-emerald-700";
}

export function CounterfactualImpactCard({
  baselineRiskScore,
  eventImpactScore,
  additionalEventDelta,
  honestyNote,
  className
}: CounterfactualImpactCardProps) {
  if (baselineRiskScore === null || baselineRiskScore === undefined) {
    return (
      <section
        className={`rounded-[28px] border border-dashed border-slate-200 bg-white p-6 text-sm text-slate-500 ${
          className ?? ""
        }`}
      >
        Counterfactual comparison is not available yet.
      </section>
    );
  }

  return (
    <section
      className={`flex flex-col h-full rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm ${
        className ?? ""
      }`}
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-blue-600">Counterfactual</p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-900">Baseline vs event-adjusted impact</h2>
        </div>
        <p className={`text-3xl font-semibold ${deltaTone(additionalEventDelta)}`}>
          +{formatNumber(additionalEventDelta)}
        </p>
      </div>

      <div className="mt-6 grid gap-4 grid-cols-2">
        <MetricCard label="Baseline risk" value={formatNumber(baselineRiskScore)} />
        <MetricCard label="Event-adjusted score" value={formatNumber(eventImpactScore)} />
        <MetricCard label="Additional delta" value={formatNumber(additionalEventDelta)} />
      </div>

      <div className="mt-auto pt-6">
        <div className="rounded-3xl border border-slate-200 bg-white p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Honesty note</p>
        <p className="mt-2 text-sm leading-7 text-slate-600">
          {honestyNote ?? "Delta is a relative operational estimate, not measured vehicle delay."}
        </p>
        </div>
      </div>
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4">
      <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
    </article>
  );
}

export default CounterfactualImpactCard;
