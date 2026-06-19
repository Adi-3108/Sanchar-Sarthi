"use client";

import { useSyncExternalStore } from "react";

export type AccessLevel = "admin" | "control_room" | "police_officer" | "citizen" | "public_citizen";

type FirebaseSessionInput = {
  accessLevel: AccessLevel;
  firebaseIdToken: string;
  firebaseUid: string;
  email?: string | null;
  officerId?: string;
  policeStation?: string;
  assignedCorridors?: string[];
  assignedZones?: string[];
};

type SessionState = {
  accessLevel: AccessLevel;
  firebaseIdToken?: string;
  firebaseUid?: string;
  email?: string | null;
  officerId?: string;
  policeStation?: string;
  assignedCorridors?: string[];
  assignedZones?: string[];
};

type SessionStore = SessionState & {
  setFirebaseSession: (input: FirebaseSessionInput) => void;
  clearSession: () => void;
};

const publicState: SessionState = {
  accessLevel: "public_citizen"
};

const STORAGE_KEY = "gridlock_session";

function loadState(): SessionState {
  if (typeof window !== "undefined") {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored) return JSON.parse(stored);
    } catch (err) {}
  }
  return publicState;
}

let state: SessionState = loadState();
let currentSnapshot: SessionStore;
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((listener) => listener());
}

function setState(next: SessionState) {
  state = next;
  if (typeof window !== "undefined") {
    try {
      if (next.accessLevel === "public_citizen") {
        window.localStorage.removeItem(STORAGE_KEY);
      } else {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      }
    } catch (err) {}
  }
  currentSnapshot = buildSnapshot();
  emit();
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function buildSnapshot(): SessionStore {
  return {
    ...state,
    setFirebaseSession: (input) => setState(input),
    clearSession: () => setState(publicState)
  };
}

currentSnapshot = buildSnapshot();

function snapshot(): SessionStore {
  return currentSnapshot;
}

export function useSessionStore(): SessionStore {
  return useSyncExternalStore(subscribe, snapshot, snapshot);
}
