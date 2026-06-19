"use client";

import { useSyncExternalStore } from "react";

export type AccessLevel = "admin" | "control_room" | "police_officer" | "public_citizen";

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

const STORAGE_KEY = "eventflow.firebase-session";
const publicState: SessionState = {
  accessLevel: "public_citizen"
};

type PersistedSessionState = Omit<SessionState, "firebaseIdToken">;

function canUseStorage(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function safeString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim().length > 0 ? value : undefined;
}

function safeStringArray(value: unknown): string[] | undefined {
  if (!Array.isArray(value)) {
    return undefined;
  }

  const items = value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
  return items.length ? items : undefined;
}

function normalizePersistedState(value: unknown): PersistedSessionState | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const candidate = value as Record<string, unknown>;
  const accessLevel = candidate.accessLevel;
  if (
    accessLevel !== "admin" &&
    accessLevel !== "control_room" &&
    accessLevel !== "police_officer" &&
    accessLevel !== "public_citizen"
  ) {
    return null;
  }

  return {
    accessLevel,
    firebaseUid: safeString(candidate.firebaseUid),
    email: typeof candidate.email === "string" || candidate.email === null ? candidate.email : undefined,
    officerId: safeString(candidate.officerId),
    policeStation: safeString(candidate.policeStation),
    assignedCorridors: safeStringArray(candidate.assignedCorridors),
    assignedZones: safeStringArray(candidate.assignedZones)
  };
}

function readPersistedState(): SessionState {
  if (!canUseStorage()) {
    return publicState;
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return publicState;
    }

    const parsed = normalizePersistedState(JSON.parse(raw));
    return parsed ? { ...publicState, ...parsed } : publicState;
  } catch {
    return publicState;
  }
}

function persistState(next: SessionState) {
  if (!canUseStorage()) {
    return;
  }

  if (next.accessLevel === "public_citizen" && !next.firebaseUid && !next.email) {
    window.localStorage.removeItem(STORAGE_KEY);
    return;
  }

  const persisted: PersistedSessionState = {
    accessLevel: next.accessLevel,
    firebaseUid: next.firebaseUid,
    email: next.email,
    officerId: next.officerId,
    policeStation: next.policeStation,
    assignedCorridors: next.assignedCorridors,
    assignedZones: next.assignedZones
  };

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(persisted));
}

function sameStringArray(left?: string[], right?: string[]): boolean {
  if (!left && !right) {
    return true;
  }
  if (!left || !right || left.length !== right.length) {
    return false;
  }
  return left.every((value, index) => value === right[index]);
}

function sameState(left: SessionState, right: SessionState): boolean {
  return (
    left.accessLevel === right.accessLevel &&
    left.firebaseIdToken === right.firebaseIdToken &&
    left.firebaseUid === right.firebaseUid &&
    left.email === right.email &&
    left.officerId === right.officerId &&
    left.policeStation === right.policeStation &&
    sameStringArray(left.assignedCorridors, right.assignedCorridors) &&
    sameStringArray(left.assignedZones, right.assignedZones)
  );
}

let state: SessionState = readPersistedState();
let currentSnapshot: SessionStore;
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((listener) => listener());
}

function setState(next: SessionState) {
  if (sameState(state, next)) {
    return;
  }

  state = next;
  persistState(state);
  currentSnapshot = buildSnapshot();
  emit();
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

const actions: Pick<SessionStore, "setFirebaseSession" | "clearSession"> = {
  setFirebaseSession: (input) => {
    const sameUser = state.firebaseUid === input.firebaseUid;
    setState({
      accessLevel: input.accessLevel,
      firebaseIdToken: input.firebaseIdToken,
      firebaseUid: input.firebaseUid,
      email: input.email ?? null,
      officerId: input.officerId ?? (sameUser && input.accessLevel === "police_officer" ? state.officerId : undefined),
      policeStation:
        input.policeStation ?? (sameUser && input.accessLevel === "police_officer" ? state.policeStation : undefined),
      assignedCorridors:
        input.assignedCorridors ??
        (sameUser && input.accessLevel === "police_officer" ? state.assignedCorridors : undefined),
      assignedZones:
        input.assignedZones ?? (sameUser && input.accessLevel === "police_officer" ? state.assignedZones : undefined)
    });
  },
  clearSession: () => setState(publicState)
};

function buildSnapshot(): SessionStore {
  return {
    ...state,
    ...actions
  };
}

currentSnapshot = buildSnapshot();

function snapshot(): SessionStore {
  return currentSnapshot;
}

export function useSessionStore(): SessionStore {
  return useSyncExternalStore(subscribe, snapshot, snapshot);
}
