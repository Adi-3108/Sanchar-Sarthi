"use client";

import { useEffect, useId, useMemo, useRef, useState, type ReactNode } from "react";

import { projectLngLat, type LngLat, type MapConfig, type ProjectedPoint } from "@/lib/map-provider";
import { ensureMapmyIndiaSdk, type MapmyIndiaLoadState } from "@/lib/map/mapmyindia-provider";

export type MapCanvasProps = {
  config: MapConfig;
  children: (project: (coordinate: LngLat) => ProjectedPoint | null) => ReactNode;
  className?: string;
};

function providerBadge(sdkState: MapmyIndiaLoadState): string {
  if (sdkState.status === "loaded") {
    return "MapmyIndia / Mappls primary";
  }
  if (sdkState.status === "failed") {
    return "Mappls SDK load failed";
  }
  return "Mappls browser key missing";
}

export function MapCanvas({ config, children, className }: MapCanvasProps) {
  const mapId = useId().replace(/:/g, "");
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<{ remove?: () => void; invalidateSize?: () => void } | null>(null);
  const [sdkState, setSdkState] = useState<MapmyIndiaLoadState>({ status: "disabled", reason: "missing_browser_key" });

  useEffect(() => {
    let cancelled = false;
    ensureMapmyIndiaSdk().then((state) => {
      if (!cancelled) {
        setSdkState(state);
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const mapplsReady = sdkState.status === "loaded";
  const project = useMemo(() => (coordinate: LngLat) => projectLngLat(coordinate), []);

  useEffect(() => {
    if (!mapplsReady || !mapContainerRef.current || !window.mappls?.Map) {
      return;
    }

    mapInstanceRef.current?.remove?.();
    const map = new window.mappls.Map(`mappls-container-${mapId}`, {
      center: [config.defaultCenter[1], config.defaultCenter[0]],
      zoom: config.defaultZoom,
      zoomControl: false,
      geolocation: false,
      clickableIcons: false,
      theme: "standardNight"
    }) as { remove?: () => void; invalidateSize?: () => void };
    mapInstanceRef.current = map;

    let resizeObserver: ResizeObserver | null = null;
    if (mapContainerRef.current) {
      resizeObserver = new ResizeObserver(() => {
        if (map && typeof map.invalidateSize === "function") {
          map.invalidateSize();
        } else {
          window.dispatchEvent(new Event("resize"));
        }
      });
      resizeObserver.observe(mapContainerRef.current);
    }

    return () => {
      resizeObserver?.disconnect();
      mapInstanceRef.current?.remove?.();
      mapInstanceRef.current = null;
    };
  }, [mapplsReady, config.defaultCenter, config.defaultZoom, mapId]);

  return (
    <section
      className={`relative min-h-[560px] overflow-hidden rounded-[28px] border border-line/80 bg-bg shadow-panel ${
        className ?? ""
      }`}
    >
      <div className="absolute inset-0 bg-[linear-gradient(135deg,#102234_0%,#0b1724_45%,#07111c_100%)]" />
      <div className={`absolute inset-0 h-full w-full transition-opacity duration-500 ${mapplsReady ? "opacity-100" : "opacity-0"}`}>
        <div
          id={`mappls-container-${mapId}`}
          ref={mapContainerRef}
          style={{ width: "100%", height: "100%", position: "absolute", inset: 0 }}
        />
      </div>
      <div className={`absolute inset-0 pointer-events-none transition-opacity duration-500 ${mapplsReady ? "opacity-0" : "opacity-80"}`}>
        <div className="absolute inset-0 bg-[linear-gradient(transparent_0,transparent_calc(100%-1px),rgba(148,163,184,0.12)_100%),linear-gradient(90deg,transparent_0,transparent_calc(100%-1px),rgba(148,163,184,0.12)_100%)] bg-[length:52px_52px]" />
        <div className="absolute left-[8%] top-[20%] h-[2px] w-[78%] rotate-[-10deg] rounded-full bg-cyan-300/20" />
        <div className="absolute left-[18%] top-[65%] h-[2px] w-[68%] rotate-[7deg] rounded-full bg-amber-300/20" />
        <div className="absolute left-[46%] top-[10%] h-[78%] w-[2px] rotate-[8deg] rounded-full bg-sky-300/20" />
        <div className="absolute left-[2%] top-[72%] h-[2px] w-[92%] rotate-[-2deg] rounded-full bg-slate-200/10" />
      </div>

      <div className="absolute left-5 top-5 z-20 flex max-w-[calc(100%-2.5rem)] flex-wrap gap-2">
        <span className="rounded-full border border-slate-700/80 bg-slate-950/85 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-slate-200">
          {providerBadge(sdkState)}
        </span>
        <span className="rounded-full border border-slate-700/80 bg-slate-950/85 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-slate-300">
          {mapplsReady ? "Primary base map" : "Mappls unavailable"}
        </span>
      </div>

      <div className="absolute inset-0 z-10">{children(project)}</div>

      <div className="absolute bottom-4 left-5 z-20 max-w-xl rounded-2xl border border-slate-700/80 bg-slate-950/85 px-4 py-3 text-xs leading-6 text-slate-300">
        Sanchar Sarthi
      </div>
    </section>
  );
}

export default MapCanvas;