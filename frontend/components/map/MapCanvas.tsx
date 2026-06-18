"use client";

import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import { fallbackReasonLabel, projectLngLat, type LngLat, type MapConfig, type ProjectedPoint } from "@/lib/map-provider";
import { ensureMapmyIndiaSdk, type MapmyIndiaLoadState } from "@/lib/map/mapmyindia-provider";

export type MapCanvasProps = {
  config: MapConfig;
  children: (project: (coordinate: LngLat) => ProjectedPoint | null) => ReactNode;
  className?: string;
};

function providerBadge(config: MapConfig, sdkState: MapmyIndiaLoadState): string {
  if (config.activeProvider === "osm") {
    return `OSM fallback: ${fallbackReasonLabel(config.fallbackReason)}`;
  }
  if (sdkState.status === "loaded") {
    return "MapmyIndia / Mappls primary";
  }
  if (sdkState.status === "failed") {
    return "OSM fallback: SDK load failed";
  }
  return "OSM fallback: browser map key missing";
}

export function MapCanvas({ config, children, className }: MapCanvasProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<{ remove?: () => void } | null>(null);
  const [sdkState, setSdkState] = useState<MapmyIndiaLoadState>(
    config.activeProvider === "mapmyindia"
      ? { status: "disabled", reason: "missing_browser_key" }
      : { status: "disabled", reason: "missing_browser_key" }
  );

  useEffect(() => {
    let cancelled = false;
    if (config.activeProvider !== "mapmyindia") {
      return;
    }

    ensureMapmyIndiaSdk().then((state) => {
      if (!cancelled) {
        setSdkState(state);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [config.activeProvider]);

  const activeProvider = config.activeProvider === "mapmyindia" && sdkState.status === "loaded" ? "mapmyindia" : "osm";
  const project = useMemo(() => (coordinate: LngLat) => projectLngLat(coordinate), []);

  useEffect(() => {
    if (activeProvider !== "mapmyindia" || !mapContainerRef.current || !window.mappls?.Map) {
      return;
    }

    mapInstanceRef.current?.remove?.();
    mapInstanceRef.current = new window.mappls.Map(mapContainerRef.current, {
      center: [config.defaultCenter[1], config.defaultCenter[0]],
      zoom: config.defaultZoom,
      zoomControl: false,
      geolocation: false,
      clickableIcons: false
    });

    return () => {
      mapInstanceRef.current?.remove?.();
      mapInstanceRef.current = null;
    };
  }, [activeProvider, config.defaultCenter, config.defaultZoom]);

  return (
    <section
      className={`relative min-h-[560px] overflow-hidden rounded-[28px] border border-line/80 bg-bg shadow-panel ${
        className ?? ""
      }`}
    >
      <div className="absolute inset-0 bg-[linear-gradient(135deg,#102234_0%,#0b1724_45%,#07111c_100%)]" />
      <div
        ref={mapContainerRef}
        className={`absolute inset-0 transition-opacity duration-500 ${
          activeProvider === "mapmyindia" ? "opacity-100" : "opacity-0"
        }`}
      />
      <div className="absolute inset-0 opacity-80">
        <div className="absolute inset-0 bg-[linear-gradient(transparent_0,transparent_calc(100%-1px),rgba(148,163,184,0.12)_100%),linear-gradient(90deg,transparent_0,transparent_calc(100%-1px),rgba(148,163,184,0.12)_100%)] bg-[length:52px_52px]" />
        <div className="absolute left-[8%] top-[20%] h-[2px] w-[78%] rotate-[-10deg] rounded-full bg-cyan-300/20" />
        <div className="absolute left-[18%] top-[65%] h-[2px] w-[68%] rotate-[7deg] rounded-full bg-amber-300/20" />
        <div className="absolute left-[46%] top-[10%] h-[78%] w-[2px] rotate-[8deg] rounded-full bg-sky-300/20" />
        <div className="absolute left-[2%] top-[72%] h-[2px] w-[92%] rotate-[-2deg] rounded-full bg-slate-200/10" />
      </div>

      <div className="absolute left-5 top-5 z-20 flex max-w-[calc(100%-2.5rem)] flex-wrap gap-2">
        <span className="rounded-full border border-slate-700/80 bg-slate-950/85 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-slate-200">
          {providerBadge(config, sdkState)}
        </span>
        <span className="rounded-full border border-slate-700/80 bg-slate-950/85 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-slate-300">
          Budget: INR {config.creditsBudgetInr}
        </span>
        <span className="rounded-full border border-slate-700/80 bg-slate-950/85 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-slate-300">
          {activeProvider === "mapmyindia" ? "Primary base map" : "Local overlay mode"}
        </span>
      </div>

      <div className="absolute inset-0 z-10">{children(project)}</div>

      <div className="absolute bottom-4 left-5 z-20 max-w-xl rounded-2xl border border-slate-700/80 bg-slate-950/85 px-4 py-3 text-xs leading-6 text-slate-300">
        {config.fallbackNote}
      </div>
    </section>
  );
}

export default MapCanvas;
