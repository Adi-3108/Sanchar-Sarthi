"use client";

import { useSyncExternalStore } from "react";

export type CommandLayer =
  | "events"
  | "hotspots"
  | "recommendations"
  | "reports"
  | "conflicts"
  | "routes";
export type CommandLanguage = "en" | "kn" | "hi";

type CommandState = {
  selectedEventId?: string;
  activeLayers: CommandLayer[];
  language: CommandLanguage;
};

type CommandStore = CommandState & {
  setSelectedEventId: (eventId?: string) => void;
  toggleLayer: (layer: CommandLayer) => void;
  setLanguage: (language: CommandLanguage) => void;
};

let state: CommandState = {
  selectedEventId: undefined,
  activeLayers: ["events", "hotspots", "recommendations", "reports", "conflicts", "routes"],
  language: "en"
};
let currentSnapshot: CommandStore;

const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((listener) => listener());
}

function setState(next: Partial<CommandState>) {
  state = { ...state, ...next };
  currentSnapshot = buildSnapshot();
  emit();
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function buildSnapshot(): CommandStore {
  return {
    ...state,
    setSelectedEventId: (eventId) => setState({ selectedEventId: eventId }),
    toggleLayer: (layer) =>
      setState({
        activeLayers: state.activeLayers.includes(layer)
          ? state.activeLayers.filter((item) => item !== layer)
          : [...state.activeLayers, layer]
      }),
    setLanguage: (language) => setState({ language })
  };
}

currentSnapshot = buildSnapshot();

function snapshot(): CommandStore {
  return currentSnapshot;
}

export function useCommandStore(): CommandStore {
  return useSyncExternalStore(subscribe, snapshot, snapshot);
}
