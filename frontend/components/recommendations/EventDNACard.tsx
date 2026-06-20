"use client";

import type { EventDnaResponse } from "@/lib/api";

export type EventDNACardProps = {
  eventDna: EventDnaResponse | null | undefined;
  className?: string;
};

function formatRiskValue(value: unknown): string {
  if (typeof value === "number") {
    if (value >= 0 && value <= 1) {
      return `${Math.round(value * 100)}%`;
    }
    return String(Math.round(value * 100) / 100);
  }
  if (typeof value === "string") {
    return value.replaceAll("_", " ");
  }
  return "n/a";
}

export function EventDNACard({ eventDna, className }: EventDNACardProps) {
  if (!eventDna) {
    return (
      <section
        className={`rounded-[28px] border border-dashed border-slate-700/80 bg-slate-950/60 p-6 text-sm text-slate-400 ${
          className ?? ""
        }`}
      >
        Event DNA is not available yet.
      </section>
    );
  }

  const indicatorEntries = Object.entries(eventDna.risk_indicators_json ?? {}).slice(0, 8);

  return (
    <section
      className={`rounded-[28px] border border-slate-800/80 bg-slate-950/85 p-6 shadow-[0_18px_40px_rgba(2,6,23,0.35)] ${
        className ?? ""
      }`}
    >
      <div className="flex flex-col gap-3">
        <div className="max-w-3xl">
          <p className="text-[11px] uppercase tracking-[0.24em] text-sky-300/80">Event DNA</p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-100">Operational fingerprint</h2>
          <p className="mt-3 text-sm leading-7 text-slate-300">{eventDna.dna_summary}</p>
        </div>
        <div className="self-start rounded-2xl border border-sky-400/25 bg-sky-500/10 px-4 py-3 text-xs text-sky-100">
          <p className="uppercase tracking-[0.2em] text-sky-300/80">Similar memory</p>
          <p className="mt-2 text-lg font-semibold">{eventDna.similar_event_ids_json.length} matches</p>
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <article className="rounded-3xl border border-slate-800/70 bg-slate-900/70 p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Time context</p>
          <p className="mt-2 text-sm leading-7 text-slate-200">{eventDna.time_context}</p>
        </article>
        <article className="rounded-3xl border border-slate-800/70 bg-slate-900/70 p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Location context</p>
          <p className="mt-2 text-sm leading-7 text-slate-200">{eventDna.location_context}</p>
        </article>
        <article className="rounded-3xl border border-slate-800/70 bg-slate-900/70 p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Cause context</p>
          <p className="mt-2 text-sm leading-7 text-slate-200">{eventDna.cause_context}</p>
        </article>
        <article className="rounded-3xl border border-slate-800/70 bg-slate-900/70 p-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Historical pattern</p>
          <p className="mt-2 text-sm leading-7 text-slate-200">{eventDna.historical_pattern}</p>
        </article>
      </div>

      <div className="mt-6 rounded-3xl border border-slate-800/70 bg-slate-900/70 p-4">
        <div className="flex items-center justify-between gap-4">
          <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">Risk indicators</p>
          <p className="text-xs text-slate-500">Dataset-backed structured signals</p>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {indicatorEntries.map(([label, value]) => (
            <div key={label} className="rounded-2xl border border-slate-800/80 bg-slate-950/70 p-3">
              <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">
                {label.replaceAll("_", " ")}
              </p>
              <p className="mt-2 text-base font-semibold text-slate-100">{formatRiskValue(value)}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default EventDNACard;
