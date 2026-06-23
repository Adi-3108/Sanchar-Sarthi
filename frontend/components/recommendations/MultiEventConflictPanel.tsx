"use client";

import type { MultiEventAnalysisResponse } from "@/lib/api";

export type MultiEventConflictPanelProps = {
  analysis?: MultiEventAnalysisResponse | null;
  className?: string;
};

function riskTone(level?: string): string {
  const normalized = level?.trim().toLowerCase();
  if (normalized === "critical") {
    return "border-rose-200 bg-rose-50 text-rose-800";
  }
  if (normalized === "high") {
    return "border-orange-200 bg-orange-50 text-orange-800";
  }
  if (normalized === "medium") {
    return "border-amber-200 bg-amber-50 text-amber-800";
  }
  return "border-emerald-200 bg-emerald-50 text-emerald-800";
}

function formatMode(value?: string): string {
  return value ? value.replaceAll("_", " ") : "normal monitoring";
}

export function MultiEventConflictPanel({ analysis, className }: MultiEventConflictPanelProps) {
  if (!analysis) {
    return (
      <section
        className={`rounded-3xl border-2 border-dashed border-slate-200 bg-slate-50 p-12 text-center text-sm font-medium text-slate-500 shadow-sm ${
          className ?? ""
        }`}
      >
        <svg className="mx-auto mb-3 h-10 w-10 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        No multi-event coordination analysis has been generated yet.
      </section>
    );
  }

  return (
    <section
      className={`rounded-3xl border border-slate-200 bg-white/80 p-6 shadow-sm backdrop-blur-sm ${
        className ?? ""
      }`}
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] font-semibold text-blue-600">Multi Event Coordination</p>
          <h2 className="mt-2 text-2xl font-bold text-slate-900">Simultaneous event conflict analysis</h2>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600">{analysis.honesty_note}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span
            className={`rounded-full border px-3 py-1 text-[11px] font-bold uppercase tracking-[0.18em] ${riskTone(
              analysis.combined_risk
            )}`}
          >
            {analysis.combined_risk}
          </span>
          <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.18em] text-slate-700">
            {formatMode(analysis.coordination_mode)}
          </span>
        </div>
      </div>

      <dl className="mt-6 grid gap-3 text-sm text-slate-600 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-200 bg-slate-50/50 p-4">
          <dt className="text-[11px] font-bold uppercase tracking-widest text-slate-500">Conflict detected</dt>
          <dd className="mt-2 text-base font-semibold text-slate-900">
            {analysis.conflict_detected ? "Yes" : "No"}
          </dd>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50/50 p-4">
          <dt className="text-[11px] font-bold uppercase tracking-widest text-slate-500">High conflicts</dt>
          <dd className="mt-2 text-base font-semibold text-slate-900">{analysis.high_conflict_count}</dd>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50/50 p-4">
          <dt className="text-[11px] font-bold uppercase tracking-widest text-slate-500">Officer demand</dt>
          <dd className="mt-2 text-base font-semibold text-slate-900">{analysis.total_manpower_demand}</dd>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50/50 p-4">
          <dt className="text-[11px] font-bold uppercase tracking-widest text-slate-500">Officer gap</dt>
          <dd className="mt-2 text-base font-semibold text-slate-900">{analysis.officer_gap}</dd>
        </div>
      </dl>

      {analysis.conflict_signals.length > 0 ? (
        <div className="mt-5 flex flex-wrap gap-2">
          {analysis.conflict_signals.map((signal) => (
            <span
              key={signal}
              className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-600"
            >
              {signal}
            </span>
          ))}
        </div>
      ) : null}

      <div className="mt-6 grid gap-4 lg:grid-cols-[0.85fr_1.15fr]">
        <article className="rounded-3xl border border-slate-200 bg-slate-50/80 p-5 shadow-sm">
          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Coordination plan</p>
          <ul className="mt-4 space-y-3 text-sm leading-relaxed text-slate-700">
            {analysis.coordination_plan.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <div className="grid gap-3">
          {analysis.conflicts.length === 0 ? (
            <article className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-5 text-sm font-medium text-slate-500">
              No pairwise conflicts were found between the selected events.
            </article>
          ) : (
            analysis.conflicts.map((conflict) => (
              <article
                key={conflict.event_ids.join("-")}
                className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Event pair</p>
                    <h3 className="mt-2 text-lg font-bold text-slate-900">
                      {conflict.event_ids.join(" + ")}
                    </h3>
                    <p className="mt-2 text-sm leading-relaxed text-slate-600">
                      {conflict.distance_km} km apart with {conflict.overlap_minutes} minutes overlap.
                    </p>
                  </div>
                  <span
                    className={`rounded-full border px-3 py-1 text-[11px] font-bold uppercase tracking-[0.18em] ${riskTone(
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
                        className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-600"
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
