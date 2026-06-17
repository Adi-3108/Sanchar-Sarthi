"use client";

import { useQuery } from "@tanstack/react-query";

import { apiGet, type HealthResponse } from "@/lib/api";

const commandCards = [
  {
    title: "Predict",
    description: "Historical ASTraM intelligence, explainable risk scoring, and phase-safe API health."
  },
  {
    title: "Plan",
    description: "Command-center workflows will layer manpower, barricade, diversion, and map intelligence next."
  },
  {
    title: "Learn",
    description: "Post-event feedback loops remain planned for later phases without breaking this base shell."
  }
];

export default function CommandCenterPage() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["health"],
    queryFn: () => apiGet<HealthResponse>("/api/health"),
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
                EventFlow AI
              </p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight md:text-5xl">
                Predictive traffic command twin for event-driven congestion.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-muted md:text-lg">
                Phase 1 establishes the backend shell, health contract, and command-center
                entrypoint for the full Predict - Plan - Monitor - Adapt - Learn workflow.
              </p>
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
                Phase 1
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
                  <p>Priority model: {data.models.priority}</p>
                  <p>Road closure model: {data.models.road_closure}</p>
                  <p>Resolution time model: {data.models.resolution_time}</p>
                  <p>Firebase: {data.auth.firebase}</p>
                </div>
              )}
            </div>
          </article>

          <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-6 shadow-panel">
            <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Phase map</p>
            <h2 className="mt-2 text-2xl font-semibold">What this unlocks next</h2>
            <ul className="mt-5 space-y-3 text-sm leading-7 text-muted">
              <li>Phase 2: PostgreSQL sessions, ORM models, and migrations.</li>
              <li>Phase 3: ASTraM ingestion, masking, and text normalization.</li>
              <li>Phase 14+: MapmyIndia primary rendering with OSM fallback.</li>
            </ul>
          </article>
        </section>
      </div>
    </main>
  );
}
