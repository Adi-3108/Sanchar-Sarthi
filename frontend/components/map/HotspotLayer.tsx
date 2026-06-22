"use client";

import type { ReactNode } from "react";

import type { HotspotResponseItem } from "@/lib/api";

import type { MapConfig } from "@/lib/map-provider";
import MapCanvas from "./MapCanvas";

type ProjectedPoint = {
  x: number;
  y: number;
};

export type HotspotLayerProps = {
  hotspots: HotspotResponseItem[];
  className?: string;
  emptyState?: ReactNode;
  selectedHotspotId?: string | null;
  onSelectHotspot?: (hotspot: HotspotResponseItem) => void;
  project?: (hotspot: HotspotResponseItem) => ProjectedPoint | null;
  mapConfig?: MapConfig;
};

function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "n/a";
  }
  return `${Math.round(value * 100)}%`;
}

function riskLabel(score: number): "Low" | "Medium" | "High" | "Critical" {
  if (score >= 0.75) {
    return "Critical";
  }
  if (score >= 0.5) {
    return "High";
  }
  if (score >= 0.25) {
    return "Medium";
  }
  return "Low";
}

function riskClassName(score: number): string {
  if (score >= 0.75) {
    return "border-red-400/60 bg-red-500/20 text-red-100";
  }
  if (score >= 0.5) {
    return "border-amber-400/60 bg-amber-500/20 text-amber-100";
  }
  if (score >= 0.25) {
    return "border-yellow-300/60 bg-yellow-400/20 text-yellow-100";
  }
  return "border-emerald-400/60 bg-emerald-500/20 text-emerald-100";
}

function pulseSize(cluster: HotspotResponseItem): number {
  const scoreWeight = Math.max(cluster.cluster_risk_score, 0.15);
  const eventWeight = Math.min(cluster.cluster_event_count, 24) / 24;
  return 22 + scoreWeight * 34 + eventWeight * 16;
}

function HotspotCard({
  hotspot,
  selected,
  onSelect
}: {
  hotspot: HotspotResponseItem;
  selected: boolean;
  onSelect?: (hotspot: HotspotResponseItem) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect?.(hotspot)}
      className={`w-full rounded-3xl border p-4 text-left transition ${
        selected
          ? "border-sky-300/70 bg-slate-900/95 shadow-[0_0_0_1px_rgba(125,211,252,0.25)]"
          : "border-slate-700/70 bg-slate-950/80 hover:border-slate-500/80 hover:bg-slate-900/90"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-slate-400">Hotspot</p>
          <h3 className="mt-2 text-sm font-semibold text-slate-100">{hotspot.location_cluster_id}</h3>
        </div>
        <span
          className={`rounded-full border px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] ${riskClassName(
            hotspot.cluster_risk_score
          )}`}
        >
          {riskLabel(hotspot.cluster_risk_score)}
        </span>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 text-xs text-slate-300">
        <div>
          <p className="text-slate-500">Events</p>
          <p className="mt-1 text-lg font-semibold text-slate-100">{hotspot.cluster_event_count}</p>
        </div>
        <div>
          <p className="text-slate-500">Risk score</p>
          <p className="mt-1 text-lg font-semibold text-slate-100">
            {Math.round(hotspot.cluster_risk_score * 100)}
          </p>
        </div>
      </div>

      <dl className="mt-4 space-y-2 text-xs text-slate-300">
        <div className="flex items-center justify-between gap-4">
          <dt className="text-slate-500">Top cause</dt>
          <dd className="text-right text-slate-100">
            {hotspot.cluster_top_event_cause ?? "unknown"}
          </dd>
        </div>
        <div className="flex items-center justify-between gap-4">
          <dt className="text-slate-500">Road closure</dt>
          <dd className="text-right text-slate-100">
            {formatPercent(hotspot.cluster_road_closure_rate)}
          </dd>
        </div>
        <div className="flex items-center justify-between gap-4">
          <dt className="text-slate-500">Peak hour</dt>
          <dd className="text-right text-slate-100">
            {formatPercent(hotspot.cluster_peak_hour_rate)}
          </dd>
        </div>
      </dl>
    </button>
  );
}

function HotspotOverlayContent({
  hotspots,
  selectedHotspotId,
  onSelectHotspot,
  project
}: Required<Pick<HotspotLayerProps, "hotspots" | "selectedHotspotId" | "project">> &
  Pick<HotspotLayerProps, "onSelectHotspot">) {
  return (
    <>
      {hotspots.map((hotspot) => {
        const projected = project(hotspot);
        if (!projected) {
          return null;
        }

        const size = pulseSize(hotspot);
        const selected = hotspot.location_cluster_id === selectedHotspotId;

        return (
          <button
            key={hotspot.location_cluster_id}
            type="button"
            onClick={() => onSelectHotspot?.(hotspot)}
            className="group absolute -translate-x-1/2 -translate-y-1/2"
            style={{ left: `${projected.x}%`, top: `${projected.y}%` }}
          >
            <span
              className={`absolute left-1/2 top-1/2 rounded-full border transition ${
                selected
                  ? "border-indigo-700 bg-indigo-600/40"
                  : "border-indigo-600/80 bg-indigo-500/30"
              }`}
              style={{
                width: `${size}px`,
                height: `${size}px`,
                transform: "translate(-50%, -50%)"
              }}
            />
            <span
              className={`absolute left-1/2 top-1/2 rounded-full border transition ${
                selected
                  ? "border-indigo-900 bg-indigo-800"
                  : "border-indigo-800 bg-indigo-700"
              }`}
              style={{
                width: "10px",
                height: "10px",
                transform: "translate(-50%, -50%)"
              }}
            />
            <span className="relative z-10 block rounded-full bg-slate-950/90 px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.16em] text-slate-100 shadow-lg opacity-0 transition group-hover:opacity-100">
              {hotspot.location_cluster_id}
            </span>
          </button>
        );
      })}
    </>
  );
}

export function HotspotOverlay({
  hotspots,
  selectedHotspotId,
  onSelectHotspot,
  project,
  mapConfig
}: Required<Pick<HotspotLayerProps, "hotspots" | "selectedHotspotId">> &
  Pick<HotspotLayerProps, "onSelectHotspot" | "project" | "mapConfig">) {
  
  if (mapConfig) {
    return (
      <MapCanvas config={mapConfig} className="min-h-[320px]">
        {(mapProject) => (
          <HotspotOverlayContent
            hotspots={hotspots}
            selectedHotspotId={selectedHotspotId}
            onSelectHotspot={onSelectHotspot}
            project={(hotspot) => mapProject([hotspot.centroid_longitude, hotspot.centroid_latitude])}
          />
        )}
      </MapCanvas>
    );
  }

  if (!project) return null;

  return (
    <div className="relative min-h-[320px] overflow-hidden rounded-[28px] border border-slate-800/80 bg-[radial-gradient(circle_at_top,#172554_0%,#020617_52%,#020617_100%)]">
      <div className="absolute inset-0 bg-[linear-gradient(transparent_0,transparent_calc(100%-1px),rgba(148,163,184,0.1)_100%),linear-gradient(90deg,transparent_0,transparent_calc(100%-1px),rgba(148,163,184,0.1)_100%)] bg-[length:56px_56px]" />
      <HotspotOverlayContent
        hotspots={hotspots}
        selectedHotspotId={selectedHotspotId}
        onSelectHotspot={onSelectHotspot}
        project={project}
      />
    </div>
  );
}

export function HotspotLayer({
  hotspots,
  className,
  emptyState,
  selectedHotspotId = null,
  onSelectHotspot,
  project,
  mapConfig
}: HotspotLayerProps) {
  if (hotspots.length === 0) {
    return (
      <div
        className={`rounded-3xl border-2 border-dashed border-slate-200 bg-slate-50 p-8 text-center text-sm font-medium text-slate-500 shadow-sm ${
          className ?? ""
        }`}
      >
        {emptyState ?? "No dataset-backed hotspots are available yet."}
      </div>
    );
  }

  return (
    <section className={`space-y-5 ${className ?? ""}`}>
      {project || mapConfig ? (
        <HotspotOverlay
          hotspots={hotspots}
          selectedHotspotId={selectedHotspotId}
          onSelectHotspot={onSelectHotspot}
          project={project}
          mapConfig={mapConfig}
        />
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {hotspots.map((hotspot) => (
          <HotspotCard
            key={hotspot.location_cluster_id}
            hotspot={hotspot}
            selected={hotspot.location_cluster_id === selectedHotspotId}
            onSelect={onSelectHotspot}
          />
        ))}
      </div>
    </section>
  );
}

export default HotspotLayer;
