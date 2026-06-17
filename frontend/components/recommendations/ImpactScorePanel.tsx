"use client";

export type ImpactScorePanelProps = {
  estimatedImpactScore?: number | null;
  impactCategory?: string | null;
  impactRadiusKm?: number | null;
  vehicleImpactFactor?: number | null;
  vehicleImpactNote?: string | null;
  priorityConfidence?: number | null;
  roadClosureProbability?: number | null;
  scoreReasonCodes?: string[];
  className?: string;
};

function categoryTone(category: string | null | undefined): string {
  if (category === "Critical") {
    return "border-red-400/40 bg-red-500/15 text-red-100";
  }
  if (category === "High") {
    return "border-amber-400/40 bg-amber-500/15 text-amber-100";
  }
  if (category === "Medium") {
    return "border-yellow-300/40 bg-yellow-400/15 text-yellow-100";
  }
  return "border-emerald-400/40 bg-emerald-500/15 text-emerald-100";
}

function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "n/a";
  }
  return `${Math.round(value * 100)}%`;
}

function formatNumber(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "n/a";
  }
  return value.toFixed(digits);
}

export function ImpactScorePanel({
  estimatedImpactScore,
  impactCategory,
  impactRadiusKm,
  vehicleImpactFactor,
  vehicleImpactNote,
  priorityConfidence,
  roadClosureProbability,
  scoreReasonCodes = [],
  className
}: ImpactScorePanelProps) {
  if (estimatedImpactScore === null || estimatedImpactScore === undefined) {
    return (
      <section
        className={`rounded-[28px] border border-dashed border-slate-700/80 bg-slate-950/60 p-6 text-sm text-slate-400 ${
          className ?? ""
        }`}
      >
        Estimated impact score is not available yet.
      </section>
    );
  }

  return (
    <section
      className={`rounded-[28px] border border-slate-800/80 bg-slate-950/85 p-6 shadow-[0_18px_40px_rgba(2,6,23,0.35)] ${
        className ?? ""
      }`}
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="max-w-3xl">
          <p className="text-[11px] uppercase tracking-[0.24em] text-fuchsia-300/80">Estimated Impact</p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-100">Operational disruption estimate</h2>
          <p className="mt-3 text-sm leading-7 text-slate-300">
            Dataset-backed impact combines urgency, closure likelihood, hotspot risk, similar-event memory,
            and controlled vehicle-type adjustment.
          </p>
        </div>
        <div
          className={`rounded-full border px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] ${categoryTone(
            impactCategory
          )}`}
        >
          {impactCategory ?? "Unknown"}
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
        <article className="rounded-3xl border border-slate-800/70 bg-slate-900/70 p-5">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Impact score</p>
          <p className="mt-3 text-4xl font-semibold text-slate-100">{formatNumber(estimatedImpactScore)}</p>
          <p className="mt-3 text-sm text-slate-400">
            Estimated radius {formatNumber(impactRadiusKm)} km
          </p>
        </article>

        <div className="grid gap-3 sm:grid-cols-2">
          <MetricCard label="Priority confidence" value={formatPercent(priorityConfidence)} />
          <MetricCard label="Closure likelihood" value={formatPercent(roadClosureProbability)} />
          <MetricCard label="Vehicle impact factor" value={formatNumber(vehicleImpactFactor)} />
          <MetricCard label="Radius estimate" value={`${formatNumber(impactRadiusKm)} km`} />
        </div>
      </div>

      <div className="mt-6 rounded-3xl border border-slate-800/70 bg-slate-900/70 p-4">
        <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Vehicle note</p>
        <p className="mt-2 text-sm leading-7 text-slate-300">
          {vehicleImpactNote ?? "Vehicle impact factor was not available for this scenario."}
        </p>
      </div>

      <div className="mt-6 rounded-3xl border border-slate-800/70 bg-slate-900/70 p-4">
        <div className="flex items-center justify-between gap-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Reason codes</p>
          <p className="text-xs text-slate-500">Dataset-backed scoring signals</p>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {scoreReasonCodes.length > 0 ? (
            scoreReasonCodes.map((reasonCode) => (
              <span
                key={reasonCode}
                className="rounded-full border border-slate-700/80 bg-slate-950/80 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-slate-300"
              >
                {reasonCode.replaceAll("_", " ")}
              </span>
            ))
          ) : (
            <span className="text-sm text-slate-400">No reason codes were available.</span>
          )}
        </div>
      </div>
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

export default ImpactScorePanel;
