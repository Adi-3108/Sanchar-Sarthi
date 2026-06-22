"use client";

import type { ActionConfidenceLedgerItemResponse } from "@/lib/api";

export type ActionConfidenceLedgerProps = {
  items: ActionConfidenceLedgerItemResponse[];
  className?: string;
};

export function ActionConfidenceLedger({ items, className }: ActionConfidenceLedgerProps) {
  if (items.length === 0) {
    return (
      <section
        className={`rounded-[28px] border border-dashed border-slate-200 bg-white p-6 text-sm text-slate-500 ${
          className ?? ""
        }`}
      >
        No confidence ledger entries were available.
      </section>
    );
  }

  return (
    <section
      className={`flex flex-col h-full rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm ${
        className ?? ""
      }`}
    >
      <p className="text-[11px] uppercase tracking-[0.24em] text-sky-300/80">Action Confidence Ledger</p>
      <h2 className="mt-2 text-2xl font-semibold text-slate-900">Why this plan should be trusted carefully</h2>
      <div className="mt-6 grid gap-4">
        {items.map((item) => (
          <article
            key={`${item.input}-${item.source ?? "source"}`}
            className="rounded-3xl border border-slate-200 bg-white p-4"
          >
            <div className="flex flex-col gap-3">
              <div>
                <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">{item.input}</p>
                <p className="mt-2 text-sm leading-7 text-slate-600">{item.note ?? "No note provided."}</p>
              </div>
              <div className="self-start rounded-full border border-slate-200 bg-white px-3 py-1 text-xs uppercase tracking-[0.18em] text-slate-700">
                {Math.round(item.confidence * 100)} confidence
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export default ActionConfidenceLedger;
