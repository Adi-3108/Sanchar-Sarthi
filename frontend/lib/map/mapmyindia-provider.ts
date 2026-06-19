"use client";

declare global {
  interface Window {
    mappls?: {
      Map?: new (
        target: string | HTMLElement,
        options: Record<string, unknown>
      ) => { remove?: () => void };
    };
  }
}

export type MapmyIndiaLoadState =
  | { status: "disabled"; reason: "missing_browser_key" }
  | { status: "loaded" }
  | { status: "failed"; reason: "sdk_load_failed" };

let sdkLoadPromise: Promise<void> | null = null;

export function browserMapmyIndiaKey(): string | null {
  const key = process.env.NEXT_PUBLIC_MAPMYINDIA_MAP_KEY?.trim();
  if (!key || key === "replace_with_browser_allowed_key") {
    return null;
  }
  return key;
}

export function loadMapmyIndiaScript(mapKey: string): Promise<void> {
  if (typeof document === "undefined") {
    return Promise.resolve();
  }

  const existing = document.querySelector('[data-mapmyindia-sdk="true"]');
  if (existing) {
    return sdkLoadPromise ?? Promise.resolve();
  }

  sdkLoadPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.dataset.mapmyindiaSdk = "true";
    script.src = `https://sdk.mappls.com/map/sdk/web?v=3.0&layer=vector&access_token=${mapKey}`;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("MapmyIndia SDK failed to load"));
    document.head.appendChild(script);
  });

  return sdkLoadPromise;
}

export async function ensureMapmyIndiaSdk(): Promise<MapmyIndiaLoadState> {
  const key = browserMapmyIndiaKey();
  if (!key) {
    return { status: "disabled", reason: "missing_browser_key" };
  }

  try {
    await loadMapmyIndiaScript(key);
    return { status: "loaded" };
  } catch {
    return { status: "failed", reason: "sdk_load_failed" };
  }
}
