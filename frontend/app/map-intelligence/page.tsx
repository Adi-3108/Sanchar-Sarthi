"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import AuthPanel from "@/components/auth/AuthPanel";
import ConflictLayer, { type ConflictOverlay } from "@/components/map/ConflictLayer";
import EventLayer, { type MapEventPoint } from "@/components/map/EventLayer";
import HotspotLayer from "@/components/map/HotspotLayer";
import MapCanvas from "@/components/map/MapCanvas";
import ReportLayer, { type MapReportPoint } from "@/components/map/ReportLayer";
import RouteLayer, { type RouteOverlay } from "@/components/map/RouteLayer";
import MultiEventConflictPanel from "@/components/recommendations/MultiEventConflictPanel";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  analyzeMultiEvent,
  geocodeMapAddress,
  getHotspots,
  getMapConfig,
  getMapRoute,
  type HotspotResponseItem,
  type MapConfigResponse,
  type MapGeocodeResponse,
  type MapRouteResponse,
  type MultiEventAnalysisResponse
} from "@/lib/api";
import { useFirebaseAuthState } from "@/lib/auth";
import { projectLngLat, severityFromScore, type LngLat } from "@/lib/map-provider";
import { useLanguage } from "@/components/LanguageContext";
import { t } from "@/lib/i18n";

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

function geocodeEventPoints(result?: MapGeocodeResponse): MapEventPoint[] {
  return (result?.candidates ?? []).map((candidate, index) => ({
    id: `geocode-${index}`,
    coordinate: candidate.coordinate,
    label: candidate.label,
    severity: "Medium",
    detail: candidate.confidence
  }));
}

function reportPointsFromHotspots(hotspots: HotspotResponseItem[]): MapReportPoint[] {
  return hotspots.slice(0, 4).map((hotspot, index) => ({
    id: `report-${hotspot.location_cluster_id}`,
    coordinate: [
      hotspot.centroid_longitude + (index % 2 === 0 ? 0.006 : -0.006),
      hotspot.centroid_latitude + (index % 2 === 0 ? -0.004 : 0.004)
    ],
    label: hotspot.cluster_top_event_cause ?? "Representative report",
    confidence: Math.min(0.95, 0.55 + hotspot.cluster_risk_score * 0.35),
    source: "representative demo"
  }));
}

function conflictOverlaysFromAnalysis(analysis?: MultiEventAnalysisResponse): ConflictOverlay[] {
  const features = Array.isArray((analysis?.map_overlay as { features?: unknown[] } | undefined)?.features)
    ? ((analysis?.map_overlay as { features: unknown[] }).features)
    : [];

  return features
    .map((feature, index) => {
      if (!feature || typeof feature !== "object") {
        return null;
      }
      const geometry = (feature as { geometry?: unknown }).geometry;
      const properties = (feature as { properties?: unknown }).properties;
      if (!geometry || typeof geometry !== "object" || !properties || typeof properties !== "object") {
        return null;
      }
      const coordinates = (geometry as { coordinates?: unknown }).coordinates;
      if (!Array.isArray(coordinates) || coordinates.length < 2) {
        return null;
      }
      const left = coordinates[0];
      const right = coordinates[1];
      if (
        !Array.isArray(left) ||
        !Array.isArray(right) ||
        typeof left[0] !== "number" ||
        typeof left[1] !== "number" ||
        typeof right[0] !== "number" ||
        typeof right[1] !== "number"
      ) {
        return null;
      }
      const props = properties as Record<string, unknown>;
      const eventIds = Array.isArray(props.event_ids)
        ? props.event_ids.filter((value): value is string => typeof value === "string")
        : [`pair-${index}`];
      return {
        id: `conflict-${eventIds.join("-")}-${index}`,
        eventIds,
        coordinates: [
          [left[0], left[1]] as LngLat,
          [right[0], right[1]] as LngLat
        ],
        conflictLevel: typeof props.conflict_level === "string" ? props.conflict_level : "medium",
        conflictScore: typeof props.conflict_score === "number" ? props.conflict_score : 0
      } satisfies ConflictOverlay;
    })
    .filter((value): value is ConflictOverlay => Boolean(value));
}

function routeOverlayFromResponse(route?: MapRouteResponse): RouteOverlay[] {
  if (!route) {
    return [
      {
        id: "demo-route",
        label: "Demo diversion route",
        kind: "diversion",
        polyline: [demoRoute.origin, [77.63, 12.96], demoRoute.destination]
      }
    ];
  }
  return [
    {
      id: "provider-route",
      label: "MapmyIndia route",
      kind: "diversion",
      polyline: route.polyline
    }
  ];
}

function providerStatus(config?: MapConfigResponse): string {
  if (!config) {
    return "Checking provider";
  }
  return config.mapKeyAvailable ? "MapmyIndia / Mappls ready" : "MapmyIndia / Mappls key missing";
}

function defaultEventIdsFromHotspots(hotspots: HotspotResponseItem[]): string[] {
  const uniqueEventIds: string[] = [];
  for (const hotspot of hotspots) {
    const members = hotspot.cluster_profile.member_event_ids;
    if (!Array.isArray(members)) {
      continue;
    }
    for (const member of members) {
      if (typeof member !== "string" || uniqueEventIds.includes(member)) {
        continue;
      }
      uniqueEventIds.push(member);
      if (uniqueEventIds.length >= 2) {
        return uniqueEventIds;
      }
    }
  }
  return uniqueEventIds;
}

function parseEventIds(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function MapIntelligencePage() {
  const { user, ready: authReady } = useFirebaseAuthState();
  const { language } = useLanguage();
  const [selectedHotspotId, setSelectedHotspotId] = useState<string | null>(null);
  const [eventIdsInput, setEventIdsInput] = useState("");
  const [availableOfficers, setAvailableOfficers] = useState("18");
  const [geocodeQuery, setGeocodeQuery] = useState("MG Road, Bengaluru");

  const configQuery = useQuery({
    queryKey: ["map-config"],
    queryFn: getMapConfig,
    retry: 1,
    refetchOnWindowFocus: false
  });

  const hotspotsQuery = useQuery({
    queryKey: ["hotspots", "map-intelligence"],
    queryFn: () => getHotspots({}),
    enabled: authReady && Boolean(user),
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

  const multiEventMutation = useMutation({
    mutationFn: () =>
      analyzeMultiEvent({
        event_ids: parseEventIds(eventIdsInput),
        available_officers: Number(availableOfficers)
      })
  });

  const geocodeMutation = useMutation({
    mutationFn: () =>
      geocodeMapAddress({
        query: geocodeQuery,
        purpose: "map_intelligence_search"
      })
  });

  const hotspots = hotspotsQuery.data?.hotspots ?? [];

  useEffect(() => {
    if (eventIdsInput.trim()) {
      return;
    }
    const defaults = defaultEventIdsFromHotspots(hotspots);
    if (defaults.length >= 2) {
      setEventIdsInput(defaults.join(", "));
    }
  }, [eventIdsInput, hotspots]);

  const eventPoints = useMemo(
    () => [...eventPointsFromHotspots(hotspots), ...geocodeEventPoints(geocodeMutation.data)],
    [geocodeMutation.data, hotspots]
  );
  const reportPoints = useMemo(() => reportPointsFromHotspots(hotspots), [hotspots]);
  const conflictOverlays = useMemo(
    () => conflictOverlaysFromAnalysis(multiEventMutation.data),
    [multiEventMutation.data]
  );
  const routeOverlays = useMemo(() => routeOverlayFromResponse(routeMutation.data), [routeMutation.data]);
  const config = configQuery.data;
  const selectedHotspot = hotspots.find((hotspot) => hotspot.location_cluster_id === selectedHotspotId) ?? null;

  return (
    <main className="shell-grid min-h-screen px-6 py-8 text-copy md:px-10">
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        <section className="rounded-[28px] border border-line/80 bg-panel/90 p-7 shadow-panel">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm uppercase tracking-[0.32em] text-accentSoft">{t(language, "mapIntelligence")}</p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight md:text-5xl">
                Operational map for hotspots, reports, routes, and conflicts.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-muted">
                Primary geospatial layer is MapmyIndia / Mappls.
                Conflict overlays now come from the real multi-event analysis API, while representative report markers remain a safe demo overlay until a dedicated map feed is added.
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
                disabled={!user || routeMutation.isPending}
                className="rounded-full border border-accent/50 bg-accent/15 px-4 py-2 text-sm text-copy transition hover:border-accent hover:bg-accent/25 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {routeMutation.isPending ? "Refreshing route" : "Refresh demo route"}
              </button>
            </div>
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-[1fr_0.38fr]">
          <div>
            {configQuery.isLoading ? (
              <Skeleton.MapPanel className="min-h-[560px]" />
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
            <AuthPanel
              preferredRole="control_room"
              title="Map access sign-in"
              note="Hotspots, routing, geocode, and multi-event coordination are protected internal tools even though the map shell itself can still load."
            />

            <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel">
              <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Provider</p>
              {configQuery.isLoading ? <Skeleton.Line width="w-52" height="h-8" className="mt-2" /> : <h2 className="mt-2 text-2xl font-semibold">{providerStatus(config)}</h2>}
              <div className="mt-4 space-y-2 text-sm leading-7 text-muted">
                <p>Map key available: {config?.mapKeyAvailable ? "yes" : "no"}</p>

                <p>Routing status: {routeMutation.data?.provider ?? "Mappls route not loaded"}</p>
              </div>
            </article>

            <article className="rounded-[24px] border border-line/70 bg-panel/85 p-5 shadow-panel">
              <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Geocode search</p>
              <label className="mt-4 block text-sm text-muted">
                <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-accentSoft">Address query</span>
                <input
                  value={geocodeQuery}
                  onChange={(event) => setGeocodeQuery(event.target.value)}
                  className="w-full rounded-2xl border border-line bg-bg/80 px-4 py-3 text-copy outline-none transition focus:border-accent"
                />
              </label>
              <button
                type="button"
                onClick={() => geocodeMutation.mutate()}
                disabled={!user || geocodeMutation.isPending || geocodeQuery.trim().length < 3}
                className="mt-4 rounded-2xl border border-accent/50 bg-accent px-4 py-3 text-sm font-semibold text-bg transition hover:bg-accentSoft disabled:cursor-not-allowed disabled:opacity-60"
              >
                {geocodeMutation.isPending ? "Searching" : "Search address"}
              </button>
              <p className="mt-3 text-sm leading-7 text-muted">
                {geocodeMutation.data?.honestyNote ??
                  "Search results will appear as map markers when provider geocoding is available."}
              </p>
              {geocodeMutation.data?.candidates.length ? (
                <div className="mt-4 grid gap-3">
                  {geocodeMutation.data.candidates.map((candidate) => (
                    <div key={`${candidate.label}-${candidate.coordinate.join(",")}`} className="rounded-2xl border border-line/70 bg-bg/60 p-4 text-sm text-copy">
                      <p className="font-semibold">{candidate.label}</p>
                      <p className="mt-1 text-muted">
                        {candidate.coordinate[1].toFixed(5)}, {candidate.coordinate[0].toFixed(5)} - {candidate.confidence}
                      </p>
                    </div>
                  ))}
                </div>
              ) : null}
            </article>

            <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel">
              <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Overlay counts</p>
              <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                {hotspotsQuery.isLoading ? (
                  <Skeleton.MetricGrid count={4} />
                ) : (
                  <>
                    <div className="rounded-2xl border border-line/60 bg-bg/60 p-3"><p className="text-muted">Hotspots</p><p className="mt-1 text-xl font-semibold">{hotspots.length}</p></div>
                    <div className="rounded-2xl border border-line/60 bg-bg/60 p-3"><p className="text-muted">Reports</p><p className="mt-1 text-xl font-semibold">{reportPoints.length}</p></div>
                    <div className="rounded-2xl border border-line/60 bg-bg/60 p-3"><p className="text-muted">Search markers</p><p className="mt-1 text-xl font-semibold">{geocodeMutation.data?.candidates.length ?? 0}</p></div>
                    <div className="rounded-2xl border border-line/60 bg-bg/60 p-3"><p className="text-muted">Conflicts</p><p className="mt-1 text-xl font-semibold">{conflictOverlays.length}</p></div>
                  </>
                )}
              </div>
            </article>

            {selectedHotspot ? (
              <article className="rounded-[24px] border border-line/70 bg-panel/85 p-5 shadow-panel">
                <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Selected hotspot</p>
                <h2 className="mt-2 text-2xl font-semibold">{selectedHotspot.location_cluster_id}</h2>
                <p className="mt-3 text-sm leading-7 text-muted">
                  {selectedHotspot.cluster_top_event_cause ?? "Unknown cause"} with {selectedHotspot.cluster_event_count} historical events and {Math.round(selectedHotspot.cluster_risk_score * 100)} risk score.
                </p>
              </article>
            ) : null}

            {authReady && !user ? (
              <article className="rounded-[24px] border border-warn/30 bg-warn/10 p-5 text-sm leading-7 text-warn shadow-panel">
                Sign in with Firebase to load protected hotspot analytics, geocode lookups, and multi-event coordination.
              </article>
            ) : null}
          </aside>
        </section>

        <section className="grid gap-5 lg:grid-cols-[0.42fr_0.58fr]">
          <article className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel">
            <p className="text-xs uppercase tracking-[0.24em] text-accentSoft">Multi-event analysis</p>
            <label className="mt-4 block text-sm text-muted">
              <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-accentSoft">Event IDs</span>
              <input
                value={eventIdsInput}
                onChange={(event) => setEventIdsInput(event.target.value)}
                placeholder="FKID000001, FKID000002"
                className="w-full rounded-2xl border border-line bg-bg/80 px-4 py-3 text-copy outline-none transition focus:border-accent"
              />
            </label>
            <label className="mt-4 block text-sm text-muted">
              <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-accentSoft">Available officers</span>
              <input
                value={availableOfficers}
                onChange={(event) => setAvailableOfficers(event.target.value)}
                className="w-full rounded-2xl border border-line bg-bg/80 px-4 py-3 text-copy outline-none transition focus:border-accent"
              />
            </label>
            <button
              type="button"
              onClick={() => multiEventMutation.mutate()}
              disabled={!user || multiEventMutation.isPending || parseEventIds(eventIdsInput).length < 2}
              className="mt-4 rounded-2xl border border-accent/50 bg-accent px-4 py-3 text-sm font-semibold text-bg transition hover:bg-accentSoft disabled:cursor-not-allowed disabled:opacity-60"
            >
              {multiEventMutation.isPending ? "Analyzing" : "Run analysis"}
            </button>
            <p className="mt-3 text-sm leading-7 text-muted">
              This feeds the conflict layer from the real multi-event backend analysis instead of a synthetic overlay.
            </p>
          </article>

          {multiEventMutation.isPending ? <Skeleton.Card rows={5} /> : <MultiEventConflictPanel analysis={multiEventMutation.data} />}
        </section>

        <HotspotLayer
          hotspots={hotspots}
          selectedHotspotId={selectedHotspotId}
          onSelectHotspot={(hotspot) => setSelectedHotspotId(hotspot.location_cluster_id)}
          mapConfig={config}
          project={(hotspot) => projectLngLat([hotspot.centroid_longitude, hotspot.centroid_latitude])}
          emptyState={
            authReady && user
              ? "No hotspot overlays are available yet."
              : "Sign in to load protected hotspot overlays."
          }
        />
      </div>
    </main>
  );
}
