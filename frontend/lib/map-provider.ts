import { getMapConfig as fetchMapConfig } from "@/lib/api";
import type { MapConfigResponse, MapProvider } from "@/lib/api";

export type { MapProvider };

export type MapConfig = MapConfigResponse;

export type LngLat = [number, number];

export type OperationalFeatureProperties = {
  layerType: "hotspot" | "event" | "report" | "barricade" | "diversion" | "conflict";
  label: string;
  severity: "Low" | "Medium" | "High" | "Critical";
  reasonCodes: string[];
};

export type OperationalPointFeature = {
  id: string;
  coordinate: LngLat;
  properties: OperationalFeatureProperties;
};

export type ProjectedPoint = {
  x: number;
  y: number;
};

export type MapBounds = {
  west: number;
  south: number;
  east: number;
  north: number;
};

export const BENGALURU_BOUNDS: MapBounds = {
  west: 77.42,
  south: 12.84,
  east: 77.78,
  north: 13.12
};

export async function getMapConfig(): Promise<MapConfig> {
  return fetchMapConfig();
}

export function osmStyle() {
  return {
    version: 8,
    sources: {
      osm: {
        type: "raster",
        tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
        tileSize: 256,
        attribution: "OpenStreetMap contributors"
      }
    },
    layers: [{ id: "osm", type: "raster", source: "osm" }]
  } as const;
}

export function projectLngLat(
  coordinate: LngLat,
  bounds: MapBounds = BENGALURU_BOUNDS
): ProjectedPoint | null {
  const [longitude, latitude] = coordinate;
  if (
    longitude < bounds.west ||
    longitude > bounds.east ||
    latitude < bounds.south ||
    latitude > bounds.north
  ) {
    return null;
  }

  const x = ((longitude - bounds.west) / (bounds.east - bounds.west)) * 100;
  const y = ((bounds.north - latitude) / (bounds.north - bounds.south)) * 100;
  return { x, y };
}

export function severityFromScore(score: number): OperationalFeatureProperties["severity"] {
  if (score >= 0.75 || score >= 75) {
    return "Critical";
  }
  if (score >= 0.5 || score >= 50) {
    return "High";
  }
  if (score >= 0.25 || score >= 25) {
    return "Medium";
  }
  return "Low";
}

export function fallbackReasonLabel(reason?: string | null): string {
  if (!reason) {
    return "primary provider active";
  }
  return reason.replaceAll("_", " ");
}
