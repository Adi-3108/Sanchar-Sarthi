"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import ConflictLayer, { type ConflictOverlay } from "@/components/map/ConflictLayer";
import EventLayer, { type MapEventPoint } from "@/components/map/EventLayer";
import HotspotLayer from "@/components/map/HotspotLayer";
import MapCanvas from "@/components/map/MapCanvas";
import ReportLayer, { type MapReportPoint } from "@/components/map/ReportLayer";
import RouteLayer, { type RouteOverlay } from "@/components/map/RouteLayer";
import {
  getHotspots,
  getMapConfig,
  getMapRoute,
  type HotspotResponseItem,
  type MapConfigResponse,
  type MapRouteResponse
} from "@/lib/api";
import { projectLngLat, severityFromScore, type LngLat } from "@/lib/map-provider";

const demoRoute = {
  origin: [77.5946, 12.9716] as LngLat,
  destination: [77.685, 12.9308] as LngLat
};

function eventPointsFromHotspots(hotspots: HotspotResponseItem[]): MapEventPoint[] {
  return hotspots.slice(0, 5).map((hotspot) => ({
    id: hotspot.location_cluster_id,
    coordinate: [hotspot.centroid_longitude, hotspot.centroid_latitude],
    label: hotspot.cluster_top_event_cause ?? hotspot.location_cluster_id,
    severity: severityFromScore(hotspot.cluster_risk_score),
    detail: `${hotspot.cluster_event_count} historical events`
  }));
}

function reportPointsFromHotspots(hotspots: HotspotResponseItem[]): MapReportPoint[] {
  return hotspots.slice(0, 4).map((hotspot, index) => ({
    id: `report-${hotspot.location_cluster_id}`,
    coordinate: [
      hotspot.centroid_longitude + (index % 2 === 0 ? 0.006 : -0.006),
      hotspot.centroid_latitude + (index % 2 === 0 ? -0.004 : 0.004)
    ],
    label: hotspot.cluster_top_event_cause ?? "Citizen report",
    confidence: Math.min(0.95, 0.55 + hotspot.cluster_risk_score * 0.35),
    source: index % 2 === 0 ? "citizen" : "field officer"
  }));
}

function conflictOverlaysFromHotspots(hotspots: HotspotResponseItem[]): ConflictOverlay[] {
  if (hotspots.length < 2) {
    return [];
  }
  return hotspots.slice(0, 2).map((hotspot, index) => {
    const next = hotspots[index + 1] ?? hotspots[0];
    return {
      id: `conflict-${hotspot.location_cluster_id}-${next.location_cluster_id}`,
      eventIds: [hotspot.location_cluster_id, next.location_cluster_id],
      coordinates: [
        [hotspot.centroid_longitude, hotspot.centroid_latitude],
        [next.centroid_longitude, next.centroid_latitude]
      ],
      conflictLevel: hotspot.cluster_risk_score >= 0.75 ? "critical" : "high",
      conflictScore: Math.round(Math.max(hotspot.cluster_risk_score, next.cluster_risk_score) * 100)
    };
  });
}

function routeOverlayFromResponse(route?: MapRouteResponse): RouteOverlay[] {
  if (!route) {
    return [
      {
        id: "demo-route",
        label: "Demo diversion route",
        kind: "diversion",
        polyline: [demoRoute.origin, [77.63, 12.96], demoRoute.destination],
        fallbackReason: "manual_demo"
      }
    ];
  }
  return [
    {
      id: "provider-route",
      label: route.provider === "mapmyindia" ? "MapmyIndia route" : "Fallback route",
      kind: "diversion",
      polyline: route.polyline,
      fallbackReason: route.fallbackReason
    }
  ];
}

function providerStatus(config?: MapConfigResponse): string {
  if (!config) {
    return "Checking provider";
  }
  if (config.activeProvider === "mapmyindia") {
    return "MapmyIndia primary";
  }
  return `OSM fallback: ${config.fallbackReason?.replaceAll("_", " ") ?? "active"}`;
}

export default function MapIntelligencePage() {
  const [selectedHotspotId, setSelectedHotspotId] = useState<string | null>(null);

  const configQuery = useQuery({
    queryKey: ["map-config"],
    queryFn: getMapConfig,
    retry: 1,
    refetchOnWindowFocus: false
  });

  const hotspotsQuery = useQuery({
    queryKey: ["hotspots", "map-intelligence"],
    queryFn: () => getHotspots({}),
    retry: 1,
    refetchOnWindowFocus: false
  });

  const routeMutation = useMutation({
    mutationFn: () =>
      getMapRoute({
        origin: demoRoute.origin,
        destination: demoRoute.destination,
        mode: "driving",
        purpose: "diversion_plan"
      })
  });

  const hotspots = hotspotsQuery.data?.hotspots ?? [];
  const eventPoints = useMemo(() => eventPointsFromHotspots(hotspots), [hotspots]);
  const reportPoints = useMemo(() => reportPointsFromHotspots(hotspots), [hotspots]);
  const conflictOverlays = useMemo(() => conflictOverlaysFromHotspots(hotspots), [hotspots]);
  const routeOverlays = useMemo(() => routeOverlayFromResponse(routeMutation.data), [routeMutation.data]);
  const config = configQuery.data;

  return (
    <main className="shell-grid min-h-screen px-6 py-8 text-copy md:px-10">
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        <section className="rounded-[28px] border border-line/80 bg-panel/90 p-7 shadow-panel">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm uppercase tracking-[0.32em] text-accentSoft">Map Intelligence</p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight md:text-5xl">
                Operational map for hotspots, reports, routes, and conflicts.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-muted">
                Primary geospatial layer is MapmyIndia / Mappls with INR 1000 credit guardrails.
                The same overlays remain usable in OSM fallback mode.
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:items-end">
              <Link
                href="/command-center"
                className="rounded-full border border-line/80 px-4 py-2 text-sm text-muted transition hover:border-accent/60 hover:text-copy"
              >
                Back to command center
              </Link>
              <button
                type="button"
                onClick={() => routeMutation.mutate()}
                className="rounded-full border border-accent/50 bg-accent/15 px-4 py-2 text-sm text-copy transition hover:border-accent hover:bg-accent/25"
              >
                Refresh demo route
              </button>
            </div>
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-[1fr_0.35fr]">
          <div>
            {configQuery.isLoading ? (
              <div className="min-h-[560px] rounded-[28px] border border-line/80 bg-panel/70 p-8 text-sm text-muted shadow-panel">
                Loading map provider configuration...
              </div>
            ) : configQuery.isError || !config ? (
              <div className="min-h-[560px] rounded-[28px] border border-danger/30 bg-danger/10 p-8 text-sm text-danger shadow-panel">
                Map configuration is unavailable. Non-map recommendation panels can still work.
              </div>
            ) : (
              <MapCanvas config={config}>
                {(project) => (
                  <>
                    <RouteLayer routes={routeOverlays} project={project} />
                    <ConflictLayer conflicts={conflictOverlays} project={project} />
                    <EventLayer events={eventPoints} project={project} />
                    <ReportLayer reports={reportPoints} project={project} />
                  </>
                )}
              </MapCanvas>
            )}
          </div>

          <aside className="space-y-5">
            <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel">
              <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Provider</p>
              <h2 className="mt-2 text-2xl font-semibold">{providerStatus(config)}</h2>
              <div className="mt-4 space-y-2 text-sm leading-7 text-muted">
                <p>Map key available: {config?.mapKeyAvailable ? "yes" : "no"}</p>
                <p>Budget guard: {config?.budgetGuardEnabled ? "enabled" : "disabled"}</p>
                <p>Credit budget: INR {config?.creditsBudgetInr ?? 1000}</p>
              </div>
            </article>

            <article className="rounded-[24px] border border-line/70 bg-panel/85 p-5 shadow-panel">
              <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Route status</p>
              <h2 className="mt-2 text-2xl font-semibold">
                {routeMutation.isPending
                  ? "Refreshing"
                  : routeMutation.data
                    ? routeMutation.data.provider
                    : "Local demo route"}
              </h2>
              <p className="mt-3 text-sm leading-7 text-muted">
                {routeMutation.isError
                  ? "Protected route generation needs an internal Firebase session. The map keeps the local demo overlay visible."
                  : routeMutation.data?.honestyNote ??
                    "Route refresh uses the protected backend adapter; local overlay remains available without provider calls."}
              </p>
            </article>

            <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel">
              <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Overlays</p>
              <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-2xl border border-line/60 bg-bg/60 p-3">
                  <dt className="text-muted">Hotspots</dt>
                  <dd className="mt-1 text-xl font-semibold">{hotspots.length}</dd>
                </div>
                <div className="rounded-2xl border border-line/60 bg-bg/60 p-3">
                  <dt className="text-muted">Reports</dt>
                  <dd className="mt-1 text-xl font-semibold">{reportPoints.length}</dd>
                </div>
                <div className="rounded-2xl border border-line/60 bg-bg/60 p-3">
                  <dt className="text-muted">Events</dt>
                  <dd className="mt-1 text-xl font-semibold">{eventPoints.length}</dd>
                </div>
                <div className="rounded-2xl border border-line/60 bg-bg/60 p-3">
                  <dt className="text-muted">Conflicts</dt>
                  <dd className="mt-1 text-xl font-semibold">{conflictOverlays.length}</dd>
                </div>
              </dl>
            </article>

            {hotspotsQuery.isError ? (
              <article className="rounded-[24px] border border-warn/30 bg-warn/10 p-5 text-sm leading-7 text-warn shadow-panel">
                Hotspot overlays require internal analytics access. Sign in with Firebase to load dataset-backed hotspots.
              </article>
            ) : null}
          </aside>
        </section>

        <HotspotLayer
          hotspots={hotspots}
          selectedHotspotId={selectedHotspotId}
          onSelectHotspot={(hotspot) => setSelectedHotspotId(hotspot.location_cluster_id)}
          project={(hotspot) => {
            return projectLngLat([hotspot.centroid_longitude, hotspot.centroid_latitude]);
          }}
          emptyState="No hotspot overlays are available yet."
        />
      </div>
    </main>
  );
}
