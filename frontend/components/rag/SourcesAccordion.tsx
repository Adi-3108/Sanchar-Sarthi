"use client";

import type { RagSource } from "@/lib/ragApi";

function prettyLabel(value: string): string {
  return value
    .split(/[_-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function SourcesAccordion({ sources }: { sources: RagSource[] }) {
  if (!sources.length) {
    return null;
  }

  return (
    <details className="mt-3 rounded-2xl border border-slate-700/80 bg-slate-950/40 px-4 py-3 text-left text-sm text-slate-300">
      <summary className="cursor-pointer list-none font-medium text-sky-200">
        Grounding sources ({sources.length})
      </summary>
      <div className="mt-3 space-y-2">
        {sources.map((source) => (
          <div key={`${source.chunk_type}:${source.source_id}`} className="rounded-xl border border-slate-800 bg-slate-900/70 px-3 py-2">
            <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.22em] text-slate-400">
              <span>{prettyLabel(source.chunk_type)}</span>
              <span className="rounded-full border border-slate-700 px-2 py-1 tracking-[0.18em] text-slate-300">
                {source.source_id}
              </span>
            </div>
            <p className="mt-2 text-xs text-slate-400">Similarity {Math.round(source.similarity * 100)}%</p>
          </div>
        ))}
      </div>
    </details>
  );
}
