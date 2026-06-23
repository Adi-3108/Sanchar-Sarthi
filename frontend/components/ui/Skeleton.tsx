/**
 * Reusable skeleton loader primitives for all pages.
 * Usage: <Skeleton.Line />, <Skeleton.Card />, <Skeleton.MetricGrid count={4} />, etc.
 */

function Line({ width = "w-full", height = "h-4", className = "" }: { width?: string; height?: string; className?: string }) {
  return <div className={`animate-pulse rounded bg-line/50 ${height} ${width} ${className}`} />;
}

function Block({ height = "h-24", className = "" }: { height?: string; className?: string }) {
  return <div className={`animate-pulse rounded-2xl bg-line/30 w-full ${height} ${className}`} />;
}

function MetricCard({ className = "" }: { className?: string }) {
  return (
    <div className={`rounded-[24px] border border-line/70 bg-panel/85 p-5 shadow-panel animate-pulse ${className}`}>
      <div className="h-3 w-20 rounded bg-line/50" />
      <div className="mt-3 h-7 w-16 rounded bg-line/60" />
      <div className="mt-3 h-3 w-28 rounded bg-line/40" />
    </div>
  );
}

function MetricGrid({ count = 4, className = "" }: { count?: number; className?: string }) {
  return (
    <>
      {[...Array(count)].map((_, i) => (
        <MetricCard key={i} className={className} />
      ))}
    </>
  );
}

function Card({ rows = 3, className = "" }: { rows?: number; className?: string }) {
  return (
    <div className={`rounded-[24px] border border-line/70 bg-panel/85 p-6 shadow-panel animate-pulse space-y-4 ${className}`}>
      <div className="h-3 w-24 rounded bg-line/50" />
      <div className="h-6 w-48 rounded bg-line/60" />
      <div className="space-y-3 pt-2">
        {[...Array(rows)].map((_, i) => (
          <div key={i} className={`h-4 rounded bg-line/40 ${i % 2 === 0 ? "w-full" : "w-3/4"}`} />
        ))}
      </div>
    </div>
  );
}

function DataGrid({ count = 8, cols = 2, className = "" }: { count?: number; cols?: number; className?: string }) {
  const colClass = cols === 2 ? "grid-cols-2" : cols === 3 ? "grid-cols-3" : cols === 4 ? "grid-cols-4" : "grid-cols-2";
  return (
    <div className={`grid ${colClass} gap-4 animate-pulse ${className}`}>
      {[...Array(count)].map((_, i) => (
        <div key={i} className="flex items-center gap-2">
          <div className="h-4 w-24 rounded bg-line/50" />
          <div className="h-4 w-10 rounded bg-accent/20" />
        </div>
      ))}
    </div>
  );
}

function HotspotGrid({ count = 4, className = "" }: { count?: number; className?: string }) {
  return (
    <div className={`grid gap-4 md:grid-cols-2 animate-pulse ${className}`}>
      {[...Array(count)].map((_, i) => (
        <div key={i} className="rounded-2xl border border-line/70 bg-bg/60 p-4 space-y-3">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <div className="h-2 w-12 rounded bg-line/50" />
              <div className="h-5 w-28 rounded bg-line/60" />
            </div>
            <div className="h-5 w-16 rounded-full bg-line/40" />
          </div>
          <div className="space-y-2 pt-1">
            {[...Array(4)].map((_, j) => (
              <div key={j} className="flex justify-between">
                <div className="h-3 w-16 rounded bg-line/40" />
                <div className="h-3 w-8 rounded bg-line/50" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function TableRows({ count = 5, className = "" }: { count?: number; className?: string }) {
  return (
    <div className={`space-y-3 animate-pulse ${className}`}>
      {[...Array(count)].map((_, i) => (
        <div key={i} className="rounded-2xl border border-line/70 bg-bg/60 p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-2 flex-1">
              <div className="h-4 w-3/4 rounded bg-line/60" />
              <div className="h-3 w-1/2 rounded bg-line/40" />
            </div>
            <div className="h-8 w-16 rounded-2xl bg-line/30" />
          </div>
        </div>
      ))}
    </div>
  );
}

function IncidentCards({ count = 4, className = "" }: { count?: number; className?: string }) {
  return (
    <div className={`space-y-4 animate-pulse ${className}`}>
      {[...Array(count)].map((_, i) => (
        <div key={i} className="rounded-2xl border border-line/70 bg-bg/60 p-5 space-y-3">
          <div className="flex items-start justify-between">
            <div className="h-5 w-48 rounded bg-line/60 flex-1 mr-4" />
            <div className="h-5 w-16 rounded-full bg-line/40" />
          </div>
          <div className="h-3 w-full rounded bg-line/40" />
          <div className="h-3 w-3/4 rounded bg-line/30" />
          <div className="flex gap-2 pt-1">
            {[...Array(3)].map((_, j) => (
              <div key={j} className="h-8 w-20 rounded-2xl bg-line/30" />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}


function FormPanel({ rows = 6, className = "" }: { rows?: number; className?: string }) {
  return (
    <div className={`rounded-[24px] border border-line/70 bg-panelAlt/90 p-5 shadow-panel animate-pulse ${className}`}>
      <div className="h-3 w-28 rounded bg-line/50" />
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        {[...Array(rows)].map((_, i) => (
          <div key={i} className={i === rows - 1 ? "md:col-span-2" : ""}>
            <div className="mb-2 h-3 w-24 rounded bg-line/40" />
            <div className="h-11 rounded-2xl bg-line/30" />
          </div>
        ))}
      </div>
      <div className="mt-5 h-11 w-36 rounded-2xl bg-accent/20" />
    </div>
  );
}

function MapPanel({ className = "" }: { className?: string }) {
  return (
    <div className={`min-h-[360px] rounded-[28px] border border-line/80 bg-panel/70 p-6 shadow-panel animate-pulse ${className}`}>
      <div className="flex items-center justify-between gap-4">
        <div className="h-4 w-36 rounded bg-line/50" />
        <div className="h-8 w-24 rounded-2xl bg-line/30" />
      </div>
      <div className="mt-5 min-h-[260px] rounded-2xl bg-line/20" />
      <div className="mt-5 grid gap-3 md:grid-cols-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-16 rounded-2xl bg-line/25" />
        ))}
      </div>
    </div>
  );
}

function AuthGate({ className = "" }: { className?: string }) {
  return (
    <div className={`grid gap-6 md:grid-cols-[1fr_380px] ${className}`}>
      <Card rows={4} />
      <Card rows={5} />
    </div>
  );
}

function ScenarioGrid({ count = 2, className = "" }: { count?: number; className?: string }) {
  return (
    <div className={`grid gap-5 lg:grid-cols-2 animate-pulse ${className}`}>
      {[...Array(count)].map((_, i) => (
        <div key={i} className="rounded-[24px] border border-line/70 bg-panelAlt/90 p-6 shadow-panel">
          <div className="h-3 w-28 rounded bg-line/50" />
          <div className="mt-3 h-7 w-52 rounded bg-line/60" />
          <div className="mt-4 h-4 w-full rounded bg-line/40" />
          <div className="mt-2 h-4 w-4/5 rounded bg-line/30" />
          <div className="mt-5 grid gap-4 xl:grid-cols-2">
            <div className="h-28 rounded-2xl bg-line/25" />
            <div className="h-28 rounded-2xl bg-line/25" />
          </div>
        </div>
      ))}
    </div>
  );
}
function ChartPanel({ height = "min-h-[300px]", className = "" }: { height?: string; className?: string }) {
  return (
    <div className={`rounded-[24px] border border-line/70 bg-panelAlt/90 p-6 shadow-panel animate-pulse flex flex-col ${className}`}>
      <div className="mb-4 space-y-2">
        <div className="flex items-center gap-2">
          <div className="h-6 w-6 rounded bg-sky-400/20" />
          <div className="h-6 w-48 rounded bg-line/60" />
        </div>
        <div className="h-4 w-3/4 rounded bg-line/40" />
      </div>
      <div className={`flex-grow relative ${height} bg-line/20 rounded-xl`} />
      <div className="mt-6 grid grid-cols-3 gap-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="rounded-2xl border border-line/70 bg-bg/60 p-4 space-y-2">
            <div className="h-3 w-16 rounded bg-line/60" />
            <div className="h-6 w-12 rounded bg-line/70" />
          </div>
        ))}
      </div>
    </div>
  );
}

function ModelSection({ count = 3, className = "" }: { count?: number; className?: string }) {
  return (
    <div className={`space-y-5 animate-pulse ${className}`}>
      {[...Array(count)].map((_, i) => (
        <div key={i} className="rounded-[24px] border border-line/70 bg-panel/85 p-6 shadow-panel space-y-4">
          <div className="flex items-start justify-between">
            <div className="space-y-2 max-w-lg">
              <div className="h-3 w-24 rounded bg-line/50" />
              <div className="h-6 w-48 rounded bg-line/60" />
              <div className="h-4 w-full rounded bg-line/40" />
            </div>
            <div className="flex gap-2">
              <div className="h-6 w-20 rounded-full bg-line/40" />
              <div className="h-6 w-24 rounded-full bg-line/30" />
            </div>
          </div>
          <div className="grid gap-5 lg:grid-cols-[0.75fr_1.25fr]">
            <div className="rounded-3xl border border-line/70 bg-bg/60 p-5 space-y-3">
              {[...Array(5)].map((_, j) => (
                <div key={j} className="h-3 w-full rounded bg-line/40" />
              ))}
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[...Array(4)].map((_, j) => (
                <div key={j} className="rounded-2xl border border-line/70 bg-bg/60 p-4 space-y-2">
                  <div className="h-3 w-20 rounded bg-line/50" />
                  <div className="h-6 w-16 rounded bg-line/60" />
                </div>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export const Skeleton = {
  Line,
  Block,
  MetricCard,
  MetricGrid,
  Card,
  DataGrid,
  HotspotGrid,
  TableRows,
  IncidentCards,
  ChartPanel,
  ModelSection,
  FormPanel,
  MapPanel,
  AuthGate,
  ScenarioGrid,
};
