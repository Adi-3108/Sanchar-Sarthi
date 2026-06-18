"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import AuthPanel from "@/components/auth/AuthPanel";
import { getHotspots, getSummary, type HotspotResponseItem } from "@/lib/api";
import { useFirebaseAuthState } from "@/lib/auth";
import { useCommandStore } from "@/lib/stores/useCommandStore";

function percent(value?: number | null): string {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "n/a";
  }
  return `${Math.round(value * 100)}%`;
}

export default function ExplorerPage() {
  const router = useRouter();
  const { user, ready: authReady } = useFirebaseAuthState();
  const { setSelectedEventId } = useCommandStore();
  const [eventId, setEventId] = useState("");
  const [clusterType, setClusterType] = useState<"low" | "medium" | "high" | "critical" | "">("");

  const summaryQuery = useQuery({
    queryKey: ["explorer-summary"],
    queryFn: getSummary,
    enabled: authReady && Boolean(user),
    retry: 1,
    refetchOnWindowFocus: false
  });
  const hotspotsQuery = useQuery({
    queryKey: ["explorer-hotspots", clusterType],
    queryFn: () => getHotspots(clusterType ? { clusterType } : {}),
    enabled: authReady && Boolean(user),
    retry: 1,
    refetchOnWindowFocus: false
  });

  function handleOpenEvent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (eventId.trim()) {
      setSelectedEventId(eventId.trim());
      router.push(`/events/${encodeURIComponent(eventId.trim())}`);
    }
  }

  return (
    <main className="shell-grid min-h-screen px-6 py-8 text-copy md:px-10">
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        <section className="rounded-[28px] border border-line/80 bg-panel/90 p-8 shadow-panel">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm uppercase tracking-[0.32em] text-accentSoft">Explorer</p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight md:text-5xl">
                Dataset-backed hotspot and event dossier explorer.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-muted">
                Browse risk clusters, inspect historical patterns, and open a protected event dossier by ID.
              </p>
            </div>
            <nav className="flex flex-wrap gap-3">
              <Link href="/command-center" className="rounded-full border border-line/80 px-4 py-2 text-sm text-muted transition hover:border-accent/60 hover:text-copy">
                Command center
              </Link>
              <Link href="/map-intelligence" className="rounded-full border border-line/80 px-4 py-2 text-sm text-muted transition hover:border-accent/60 hover:text-copy">
                Map intelligence
              </Link>
            </nav>
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-[0.32fr_0.68fr]">
          <aside className="space-y-5">
            <AuthPanel
              preferredRole="control_room"
              title="Internal Firebase sign-in"
              note="Explorer analytics and event dossiers are protected. Sign in with a control-room, admin, or allowed internal account."
            />

            <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel">
              <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Dataset</p>
              <div className="mt-4 grid gap-3">
                <Metric label="Total events" value={String(summaryQuery.data?.total_events ?? "n/a")} />
                <Metric label="Planned" value={String(summaryQuery.data?.planned_events ?? "n/a")} />
                <Metric label="Unplanned" value={String(summaryQuery.data?.unplanned_events ?? "n/a")} />
                <Metric label="Hotspots" value={String(summaryQuery.data?.hotspot_count ?? "n/a")} />
              </div>
            </article>

            <form onSubmit={handleOpenEvent} className="rounded-[24px] border border-line/70 bg-panel/85 p-5 shadow-panel">
              <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Open dossier</p>
              <label className="mt-4 block text-sm text-muted">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-accentSoft">Event ID</span>
                <input
                  value={eventId}
                  onChange={(event) => setEventId(event.target.value)}
                  placeholder="FKID000001"
                  className="w-full rounded-2xl border border-line bg-bg/80 px-4 py-3 text-copy outline-none transition focus:border-accent"
                />
              </label>
              <button type="submit" className="mt-4 rounded-2xl border border-accent/50 bg-accent px-5 py-3 text-sm font-semibold text-bg transition hover:bg-accentSoft">
                Open event
              </button>
            </form>
          </aside>

          <section className="rounded-[24px] border border-line/70 bg-panel/85 p-5 shadow-panel">
            <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Hotspot clusters</p>
                <h2 className="mt-2 text-2xl font-semibold">Risk-ranked operating areas</h2>
              </div>
              <label className="text-sm text-muted">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-accentSoft">Cluster type</span>
                <select
                  value={clusterType}
                  onChange={(event) => setClusterType(event.target.value as typeof clusterType)}
                  className="rounded-2xl border border-line bg-bg/80 px-4 py-3 text-copy outline-none transition focus:border-accent"
                >
                  <option value="">All clusters</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </label>
            </div>

            {!authReady ? <p className="mt-6 text-sm text-muted">Restoring internal session...</p> : null}
            {authReady && !user ? (
              <p className="mt-6 text-sm leading-7 text-muted">Sign in to load protected analytics and hotspot overlays.</p>
            ) : null}
            {hotspotsQuery.isLoading ? <p className="mt-6 text-sm text-muted">Loading hotspot clusters...</p> : null}
            {hotspotsQuery.isError ? (
              <p className="mt-6 text-sm leading-7 text-danger">
                Hotspot explorer needs an internal Firebase session because analytics endpoints are protected.
              </p>
            ) : null}
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {(hotspotsQuery.data?.hotspots ?? []).map((hotspot) => (
                <HotspotCard key={hotspot.location_cluster_id} hotspot={hotspot} />
              ))}
            </div>
            {hotspotsQuery.data?.hotspots.length === 0 && authReady && user ? (
              <p className="mt-6 text-sm text-muted">No hotspots match the selected filter.</p>
            ) : null}
          </section>
        </section>
      </div>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-line/70 bg-bg/60 p-4">
      <p className="text-[11px] uppercase tracking-[0.22em] text-accentSoft">{label}</p>
      <p className="mt-2 text-xl font-semibold text-copy">{value}</p>
    </div>
  );
}

function HotspotCard({ hotspot }: { hotspot: HotspotResponseItem }) {
  return (
    <article className="rounded-2xl border border-line/70 bg-bg/60 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.22em] text-accentSoft">Cluster</p>
          <h3 className="mt-2 text-lg font-semibold">{hotspot.location_cluster_id}</h3>
        </div>
        <span className="rounded-full border border-line px-3 py-1 text-xs uppercase tracking-[0.18em] text-muted">
          {hotspot.cluster_type ?? "mixed"}
        </span>
      </div>
      <dl className="mt-4 grid gap-3 text-sm text-muted">
        <div className="flex justify-between gap-4"><dt>Events</dt><dd className="text-copy">{hotspot.cluster_event_count}</dd></div>
        <div className="flex justify-between gap-4"><dt>Risk</dt><dd className="text-copy">{Math.round(hotspot.cluster_risk_score * 100)}</dd></div>
        <div className="flex justify-between gap-4"><dt>Road closure</dt><dd className="text-copy">{percent(hotspot.cluster_road_closure_rate)}</dd></div>
        <div className="flex justify-between gap-4"><dt>Top cause</dt><dd className="text-right text-copy">{hotspot.cluster_top_event_cause ?? "unknown"}</dd></div>
      </dl>
    </article>
  );
}
