"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { getHealth, type HealthResponse } from "@/lib/api";

const commandCards = [
  {
    title: "Predict",
    description: "Historical ASTraM intelligence, derived features, hotspot detection, Event DNA, prediction signals, and estimated impact scoring."
  },
  {
    title: "Plan",
    description: "Command-center workflows now include weather-aware manpower, barricade, diversion, emergency corridor, and logistics recommendation planning."
  },
  {
    title: "Adapt",
    description: "Citizen reports, live escalation, and multi-event coordination now push the prototype toward a real monitor-and-adapt operational loop."
  }
];

export default function CommandCenterPage() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    retry: 1,
    refetchOnWindowFocus: false
  });

  return (
    <main className="shell-grid min-h-screen px-6 py-8 text-copy md:px-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-8">
        <section className="overflow-hidden rounded-[28px] border border-line/80 bg-panel/90 p-8 shadow-panel">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm uppercase tracking-[0.32em] text-accentSoft">
                Sanchar Sarthi
              </p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight md:text-5xl">
                Predictive traffic command twin for event-driven congestion.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-muted md:text-lg">
                Phases 1 through 16 now cover the backend shell, typed health contract,
                database connectivity, ASTraM ingestion, derived feature engineering,
                dataset-backed hotspot analytics, Event DNA, prediction services, and
                estimated impact scoring plus recommendation orchestration with weather-aware
                planning, multilingual citizen reporting, live operational escalation,
                multi-event coordination, MapmyIndia-first operational map intelligence,
                and post-event learning reports for the full Predict - Plan - Monitor -
                Adapt - Learn workflow.
              </p>
              <div className="mt-5 flex flex-wrap gap-3">
                <Link
                  href="/model-insights"
                  className="rounded-full border border-accent/40 bg-accent/10 px-4 py-2 text-sm text-copy transition hover:border-accent hover:bg-accent/20"
                >
                  Open model insights
                </Link>
                <Link
                  href="/reports"
                  className="rounded-full border border-cyan-300/40 bg-cyan-300/10 px-4 py-2 text-sm text-copy transition hover:border-cyan-200 hover:bg-cyan-300/20"
                >
                  Submit report
                </Link>
                <Link
                  href="/map-intelligence"
                  className="rounded-full border border-amber-300/40 bg-amber-300/10 px-4 py-2 text-sm text-copy transition hover:border-amber-200 hover:bg-amber-300/20"
                >
                  Open map intelligence
                </Link>
                <Link
                  href="/post-event-learning"
                  className="rounded-full border border-emerald-300/40 bg-emerald-300/10 px-4 py-2 text-sm text-copy transition hover:border-emerald-200 hover:bg-emerald-300/20"
                >
                  Open post-event learning
                </Link>
              </div>
            </div>
            <div className="rounded-3xl border border-accent/30 bg-accent/10 px-5 py-4">
              <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">
                System State
              </p>
              <p className="mt-2 text-2xl font-semibold text-copy">
                {isLoading ? "Checking" : isError ? "Attention needed" : "Operational shell ready"}
              </p>
            </div>
          </div>
        </section>

        <section className="grid gap-5 md:grid-cols-3">
          {commandCards.map((card) => (
            <article
              key={card.title}
              className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-6 shadow-panel"
            >
              <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">{card.title}</p>
              <h2 className="mt-3 text-2xl font-semibold text-copy">{card.title}</h2>
              <p className="mt-3 text-sm leading-7 text-muted">{card.description}</p>
            </article>
          ))}
        </section>

        <section className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
          <article className="rounded-[24px] border border-line/70 bg-panel/85 p-6 shadow-panel">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">
                  Backend health
                </p>
                <h2 className="mt-2 text-2xl font-semibold">Typed `/api/health` contract</h2>
              </div>
              <span className="rounded-full border border-line px-3 py-1 text-xs uppercase tracking-[0.18em] text-muted">
                Phase 2
              </span>
            </div>

            <div className="mt-6 rounded-3xl border border-line/70 bg-bg/60 p-5 font-mono text-sm leading-7 text-copy">
              {isLoading && <p>Loading backend heartbeat...</p>}
              {isError && (
                <div className="space-y-2 text-danger">
                  <p>Backend health request failed.</p>
                  <p className="text-xs text-muted">{error instanceof Error ? error.message : "Unknown error"}</p>
                </div>
              )}
              {data && (
                <div className="space-y-2">
                  <p>Status: {data.status}</p>
                  <p>Service: {data.service}</p>
                  <p>Environment: {data.environment}</p>
                  <p>Database: {data.database}</p>
                  {data.database_detail ? <p>Database detail: {data.database_detail}</p> : null}
                  <p>Priority model: {data.models.priority}</p>
                  <p>Road closure model: {data.models.road_closure}</p>
                  <p>Resolution time model: {data.models.resolution_time}</p>
                  <p>Firebase: {data.auth.firebase}</p>
                  <p>Phase 16: post-event learning loop ready</p>
                </div>
              )}
            </div>
          </article>

          <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-6 shadow-panel">
            <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Phase map</p>
            <h2 className="mt-2 text-2xl font-semibold">What this unlocks next</h2>
            <ul className="mt-5 space-y-3 text-sm leading-7 text-muted">
              <li>Phase 4: derived time, duration, and historical risk features.</li>
              <li>Phase 5: dataset-backed hotspot clustering and analytics endpoints.</li>
              <li>Phase 6: Event DNA summaries and similar-event retrieval.</li>
              <li>Phase 7: prediction diagnostics, road-closure scoring, and resolution-time estimates.</li>
              <li>Phase 8: counterfactual impact scoring and simulation-ready impact fields.</li>
              <li>Phase 9: operational recommendation planning across manpower, barricades, diversions, and logistics impact.</li>
              <li>Phase 10: weather-aware impact, barricade, and diversion adjustment for simulation and event-plan workflows.</li>
              <li>Phase 11: citizen and field reporting with multilingual normalization and confidence scoring.</li>
              <li>Phase 12: live escalation updates that compare expected vs current impact and suggest adaptive actions.</li>
              <li>Phase 13: simultaneous event conflict detection across time, space, diversions, and manpower.</li>
              <li>Phase 14: MapmyIndia-first map intelligence with route/geocode adapters, budget guardrails, and OSM fallback.</li>
              <li>Phase 15: role-aware dashboards, Firebase-protected portals, and connected event workflow pages.</li>
              <li>Phase 16: post-event learning reports and future-playbook generation for the closing loop.</li>
            </ul>
          </article>
        </section>
      </div>
    </main>
  );
}
