"use client";

import { useSyncExternalStore } from "react";

type VoteState = {
  votedIncidents: Record<string, "true" | "false">;
};

type VoteStore = VoteState & {
  setVote: (incidentId: string, voteValue: "true" | "false") => void;
};

const STORAGE_KEY = "eventflow.votes";

function getPersisted(): VoteState {
  if (typeof window === "undefined" || !window.localStorage) {
    return { votedIncidents: {} };
  }
  try {
    const data = window.localStorage.getItem(STORAGE_KEY);
    if (data) {
      return { votedIncidents: JSON.parse(data) };
    }
  } catch (e) {}
  return { votedIncidents: {} };
}

let state: VoteState = getPersisted();
let currentSnapshot: VoteStore;
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((l) => l());
}

const actions = {
  setVote: (incidentId: string, voteValue: "true" | "false") => {
    state = {
      votedIncidents: {
        ...state.votedIncidents,
        [incidentId]: voteValue
      }
    };
    if (typeof window !== "undefined" && window.localStorage) {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state.votedIncidents));
    }
    currentSnapshot = { ...state, ...actions };
    emit();
  }
};

currentSnapshot = { ...state, ...actions };

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function useVoteStore() {
  return useSyncExternalStore(subscribe, () => currentSnapshot, () => currentSnapshot);
}
