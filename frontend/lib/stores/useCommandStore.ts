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

function sameLayers(left: CommandLayer[], right: CommandLayer[]): boolean {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

function setState(next: Partial<CommandState>) {
  const merged = { ...state, ...next };
  if (
    state.selectedEventId === merged.selectedEventId &&
    state.language === merged.language &&
    sameLayers(state.activeLayers, merged.activeLayers)
  ) {
    return;
  }

  state = merged;
  currentSnapshot = buildSnapshot();
  emit();
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

const actions: Pick<CommandStore, "setSelectedEventId" | "toggleLayer" | "setLanguage"> = {
  setSelectedEventId: (eventId) => {
    if (state.selectedEventId === eventId) {
      return;
    }
    setState({ selectedEventId: eventId });
  },
  toggleLayer: (layer) => {
    const activeLayers = state.activeLayers.includes(layer)
      ? state.activeLayers.filter((item) => item !== layer)
      : [...state.activeLayers, layer];
    setState({ activeLayers });
  },
  setLanguage: (language) => {
    if (state.language === language) {
      return;
    }
    setState({ language });
  }
};

function buildSnapshot(): CommandStore {
  return {
    ...state,
    ...actions
  };
}

currentSnapshot = buildSnapshot();

function snapshot(): CommandStore {
  return currentSnapshot;
}

export function useCommandStore(): CommandStore {
  return useSyncExternalStore(subscribe, snapshot, snapshot);
}
