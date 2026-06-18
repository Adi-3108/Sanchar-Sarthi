"use client";

import type { MultiEventAnalysisResponse } from "@/lib/api";

export type MultiEventConflictPanelProps = {
  analysis?: MultiEventAnalysisResponse | null;
  className?: string;
};

function riskTone(level?: string): string {
  const normalized = level?.trim().toLowerCase();
  if (normalized === "critical") {
    return "border-red-400/50 bg-red-500/15 text-red-100";
  }
  if (normalized === "high") {
    return "border-orange-400/50 bg-orange-500/15 text-orange-100";
  }
  if (normalized === "medium") {
    return "border-amber-400/50 bg-amber-500/15 text-amber-100";
  }
  return "border-emerald-400/50 bg-emerald-500/15 text-emerald-100";
}

function formatMode(value?: string): string {
  return value ? value.replaceAll("_", " ") : "normal monitoring";
}

export function MultiEventConflictPanel({ analysis, className }: MultiEventConflictPanelProps) {
  if (!analysis) {
    return (
      <section
        className={`rounded-[28px] border border-dashed border-slate-700/80 bg-slate-950/60 p-6 text-sm text-slate-400 ${
          className ?? ""
        }`}
      >
        No multi-event coordination analysis has been generated yet.
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
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-cyan-300/80">Multi Event Coordination</p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-100">Simultaneous event conflict analysis</h2>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400">{analysis.honesty_note}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span
            className={`rounded-full border px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] ${riskTone(
              analysis.combined_risk
            )}`}
          >
            {analysis.combined_risk}
          </span>
          <span className="rounded-full border border-slate-700/80 bg-slate-950/80 px-3 py-1 text-xs uppercase tracking-[0.18em] text-slate-300">
            {formatMode(analysis.coordination_mode)}
          </span>
        </div>
      </div>

      <dl className="mt-6 grid gap-3 text-xs text-slate-300 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-3">
          <dt className="text-slate-500">Conflict detected</dt>
          <dd className="mt-2 text-sm font-semibold text-slate-100">
            {analysis.conflict_detected ? "Yes" : "No"}
          </dd>
        </div>
        <div className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-3">
          <dt className="text-slate-500">High conflicts</dt>
          <dd className="mt-2 text-sm font-semibold text-slate-100">{analysis.high_conflict_count}</dd>
        </div>
        <div className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-3">
          <dt className="text-slate-500">Officer demand</dt>
          <dd className="mt-2 text-sm font-semibold text-slate-100">{analysis.total_manpower_demand}</dd>
        </div>
        <div className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-3">
          <dt className="text-slate-500">Officer gap</dt>
          <dd className="mt-2 text-sm font-semibold text-slate-100">{analysis.officer_gap}</dd>
        </div>
      </dl>

      {analysis.conflict_signals.length > 0 ? (
        <div className="mt-5 flex flex-wrap gap-2">
          {analysis.conflict_signals.map((signal) => (
            <span
              key={signal}
              className="rounded-full border border-slate-700/80 bg-slate-950/80 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-slate-300"
            >
              {signal}
            </span>
          ))}
        </div>
      ) : null}

      <div className="mt-6 grid gap-4 lg:grid-cols-[0.85fr_1.15fr]">
        <article className="rounded-3xl border border-slate-800/80 bg-slate-900/75 p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Coordination plan</p>
          <ul className="mt-4 space-y-3 text-sm leading-7 text-slate-300">
            {analysis.coordination_plan.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <div className="grid gap-3">
          {analysis.conflicts.length === 0 ? (
            <article className="rounded-3xl border border-dashed border-slate-700/80 bg-slate-900/60 p-4 text-sm text-slate-400">
              No pairwise conflicts were found between the selected events.
            </article>
          ) : (
            analysis.conflicts.map((conflict) => (
              <article
                key={conflict.event_ids.join("-")}
                className="rounded-3xl border border-slate-800/80 bg-slate-900/75 p-4"
              >
                <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Event pair</p>
                    <h3 className="mt-2 text-lg font-semibold text-slate-100">
                      {conflict.event_ids.join(" + ")}
                    </h3>
                    <p className="mt-2 text-sm leading-7 text-slate-300">
                      {conflict.distance_km} km apart with {conflict.overlap_minutes} minutes overlap.
                    </p>
                  </div>
                  <span
                    className={`rounded-full border px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] ${riskTone(
                      conflict.conflict_level
                    )}`}
                  >
                    {conflict.conflict_score} score
                  </span>
                </div>
                {conflict.reason_labels.length > 0 ? (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {conflict.reason_labels.map((reason) => (
                      <span
                        key={`${conflict.event_ids.join("-")}-${reason}`}
                        className="rounded-full border border-slate-700/80 bg-slate-950/80 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-slate-300"
                      >
                        {reason}
                      </span>
                    ))}
                  </div>
                ) : null}
              </article>
            ))
          )}
        </div>
      </div>
    </section>
  );
}

export default MultiEventConflictPanel;
