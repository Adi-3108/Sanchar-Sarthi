import { useSyncExternalStore } from "react";

type UIState = {
  sidebarOpen: boolean;
};

type UIActions = {
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
};

type UIStore = UIState & UIActions;

let state: UIState = {
  sidebarOpen: true,
};

let cachedSnapshot: UIStore | null = null;

const listeners = new Set<() => void>();

function emit() {
  cachedSnapshot = null; // Invalidate cache so next snapshot() call returns new state
  for (const listener of listeners) {
    listener();
  }
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

const actions: UIActions = {
  toggleSidebar: () => {
    state = { ...state, sidebarOpen: !state.sidebarOpen };
    emit();
  },
  setSidebarOpen: (open: boolean) => {
    if (state.sidebarOpen === open) return;
    state = { ...state, sidebarOpen: open };
    emit();
  },
};

function snapshot(): UIStore {
  if (!cachedSnapshot) {
    cachedSnapshot = { ...state, ...actions };
  }
  return cachedSnapshot;
}

export function useUIStore(): UIStore {
  return useSyncExternalStore(subscribe, snapshot, snapshot);
}
