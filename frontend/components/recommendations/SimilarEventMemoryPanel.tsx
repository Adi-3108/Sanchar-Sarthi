"use client";

import type { SimilarEventResponse } from "@/lib/api";

export type SimilarEventMemoryPanelProps = {
  similarEvents: SimilarEventResponse[];
  className?: string;
};

function similarityTone(similarity: number): string {
  if (similarity >= 0.8) {
    return "border-red-400/50 bg-red-500/15 text-red-100";
  }
  if (similarity >= 0.65) {
    return "border-amber-400/50 bg-amber-500/15 text-amber-100";
  }
  if (similarity >= 0.5) {
    return "border-yellow-300/50 bg-yellow-400/15 text-yellow-100";
  }
  return "border-emerald-400/50 bg-emerald-500/15 text-emerald-100";
}

export function SimilarEventMemoryPanel({
  similarEvents,
  className
}: SimilarEventMemoryPanelProps) {
  if (similarEvents.length === 0) {
    return (
      <section
        className={`rounded-[28px] border border-dashed border-slate-700/80 bg-slate-950/60 p-6 text-sm text-slate-400 ${
          className ?? ""
        }`}
      >
        No similar historical events were available for this memory panel.
      </section>
    );
  }

  return (
    <section
      className={`rounded-[28px] border border-slate-800/80 bg-slate-950/85 p-6 shadow-[0_18px_40px_rgba(2,6,23,0.35)] ${
        className ?? ""
      }`}
    >
      <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-amber-300/80">
            Similar Event Memory
          </p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-100">Historical operational matches</h2>
        </div>
        <p className="text-sm text-slate-400">
          Ranked by structured-field alignment and operational fingerprint similarity.
        </p>
      </div>

      <div className="mt-6 grid gap-4">
        {similarEvents.map((match) => (
          <article
            key={match.event_id}
            className="rounded-3xl border border-slate-800/80 bg-slate-900/75 p-4"
          >
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Historical event</p>
                <h3 className="mt-2 text-lg font-semibold text-slate-100">{match.event_id}</h3>
                <p className="mt-2 text-sm leading-7 text-slate-300">
                  {(match.event_cause_clean ?? "unknown cause").replaceAll("_", " ")} in{" "}
                  {match.corridor ?? "unknown corridor"} near {match.police_station ?? "unknown station"}.
                </p>
              </div>
              <div
                className={`rounded-full border px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] ${similarityTone(
                  match.similarity
                )}`}
              >
                {Math.round(match.similarity * 100)} similarity
              </div>
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              {match.matched_signals.map((signal) => (
                <span
                  key={`${match.event_id}-${signal}`}
                  className="rounded-full border border-slate-700/80 bg-slate-950/80 px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-slate-300"
                >
                  {signal}
                </span>
              ))}
            </div>

            <dl className="mt-4 grid gap-3 text-xs text-slate-300 sm:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-3">
                <dt className="text-slate-500">Priority</dt>
                <dd className="mt-2 text-sm font-semibold text-slate-100">{match.priority ?? "unknown"}</dd>
              </div>
              <div className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-3">
                <dt className="text-slate-500">Road closure</dt>
                <dd className="mt-2 text-sm font-semibold text-slate-100">
                  {match.requires_road_closure ? "Required" : "Not required"}
                </dd>
              </div>
              <div className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-3">
                <dt className="text-slate-500">Corridor closure rate</dt>
                <dd className="mt-2 text-sm font-semibold text-slate-100">
                  {match.historical_corridor_closure_rate !== null &&
                  match.historical_corridor_closure_rate !== undefined
                    ? `${Math.round(match.historical_corridor_closure_rate * 100)}%`
                    : "n/a"}
                </dd>
              </div>
              <div className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-3">
                <dt className="text-slate-500">Cluster closure rate</dt>
                <dd className="mt-2 text-sm font-semibold text-slate-100">
                  {match.historical_cluster_closure_rate !== null &&
                  match.historical_cluster_closure_rate !== undefined
                    ? `${Math.round(match.historical_cluster_closure_rate * 100)}%`
                    : "n/a"}
                </dd>
              </div>
            </dl>
          </article>
        ))}
      </div>
    </section>
  );
}

export default SimilarEventMemoryPanel;
