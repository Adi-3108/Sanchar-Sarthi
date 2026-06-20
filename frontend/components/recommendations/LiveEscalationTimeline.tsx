"use client";

import type { LiveEventUpdateRecordResponse } from "@/lib/api";

export type LiveEscalationTimelineProps = {
  updates: LiveEventUpdateRecordResponse[];
  className?: string;
};

function alertTone(level?: string | null): string {
  const normalized = level?.trim().toLowerCase();
  if (normalized === "critical") {
    return "border-red-400/50 bg-red-500/15 text-red-100";
  }
  if (normalized === "warning") {
    return "border-amber-400/50 bg-amber-500/15 text-amber-100";
  }
  return "border-emerald-400/50 bg-emerald-500/15 text-emerald-100";
}

function formatTimestamp(value?: string | null): string {
  if (!value) {
    return "Just recorded";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Just recorded";
  }
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(parsed);
}

function activeSignals(update: LiveEventUpdateRecordResponse): string[] {
  const signals: string[] = [];
  if (update.road_closure_active) {
    signals.push("Road closure active");
  }
  if (update.officer_shortage) {
    signals.push("Officer shortage");
  }
  if (update.crowd_increase) {
    signals.push("Crowd increase");
  }
  if (update.rain_waterlogging) {
    signals.push("Rain or waterlogging");
  }
  if (update.new_nearby_incident) {
    signals.push("Nearby incident");
  }
  return signals;
}

export function LiveEscalationTimeline({ updates, className }: LiveEscalationTimelineProps) {
  if (updates.length === 0) {
    return (
      <section
        className={`rounded-[28px] border border-dashed border-slate-700/80 bg-slate-950/60 p-6 text-sm text-slate-400 ${
          className ?? ""
        }`}
      >
        No live escalation updates have been recorded for this event yet.
      </section>
    );
  }

  return (
    <section
      className={`rounded-[28px] border border-slate-800/80 bg-slate-950/85 p-6 shadow-[0_18px_40px_rgba(2,6,23,0.35)] ${
        className ?? ""
      }`}
    >
      <div className="flex flex-col gap-2">
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-fuchsia-300/80">Live Escalation Timeline</p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-100">Field updates and adaptive actions</h2>
        </div>
        <p className="text-sm text-slate-400">
          Dataset-backed escalation guidance that keeps the command plan adaptive.
        </p>
      </div>

      <div className="mt-6 grid gap-4">
        {updates.map((update) => {
          const signals = activeSignals(update);
          return (
            <article
              key={update.id}
              className="rounded-3xl border border-slate-800/80 bg-slate-900/75 p-4"
            >
              <div className="flex flex-col gap-4">
                <div className="max-w-3xl">
                  <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">
                    {update.update_source.replaceAll("_", " ")}
                  </p>
                  <h3 className="mt-2 text-lg font-semibold text-slate-100">
                    {update.current_congestion_level} congestion update
                  </h3>
                  <p className="mt-2 text-sm leading-7 text-slate-300">
                    {update.field_update ?? "No additional free-text field update was recorded."}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={`rounded-full border px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] ${alertTone(
                      update.alert_level
                    )}`}
                  >
                    {update.alert_level ?? "Stable"}
                  </span>
                  <span className="rounded-full border border-slate-700/80 bg-slate-950/80 px-3 py-1 text-xs uppercase tracking-[0.18em] text-slate-300">
                    {formatTimestamp(update.created_at)}
                  </span>
                </div>
              </div>

              {signals.length > 0 ? (
                <div className="mt-4 flex flex-wrap gap-2">
                  {signals.map((signal) => (
                    <span
                      key={`${update.id}-${signal}`}
                      className="rounded-full border border-slate-700/80 bg-slate-950/80 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-slate-300"
                    >
                      {signal}
                    </span>
                  ))}
                </div>
              ) : null}

              <dl className="mt-4 grid gap-3 text-xs text-slate-300 grid-cols-3">
                <div className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-3">
                  <dt className="text-slate-500">Exp.</dt>
                  <dd className="mt-2 text-sm font-semibold text-slate-100">{update.expected_impact_score}</dd>
                </div>
                <div className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-3">
                  <dt className="text-slate-500">Cur.</dt>
                  <dd className="mt-2 text-sm font-semibold text-slate-100">{update.current_impact_score}</dd>
                </div>
                <div className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-3">
                  <dt className="text-slate-500">Dev.</dt>
                  <dd className="mt-2 text-sm font-semibold text-slate-100">
                    {update.impact_deviation >= 0 ? "+" : ""}
                    {update.impact_deviation}
                  </dd>
                </div>
                <div className="col-span-3 rounded-2xl border border-slate-800/80 bg-slate-950/70 p-3">
                  <dt className="text-slate-500">Recommended action</dt>
                  <dd className="mt-2 text-sm font-semibold text-slate-100">
                    {update.adaptive_action ?? "Monitor situation"}
                  </dd>
                </div>
              </dl>
            </article>
          );
        })}
      </div>
    </section>
  );
}

export default LiveEscalationTimeline;
