import Link from "next/link";

import { ReportForm } from "@/components/reports/ReportForm";

export default function ReportsPage() {
  return (
    <main className="shell-grid min-h-screen px-6 py-8 text-copy md:px-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <nav className="flex items-center justify-between text-sm text-slate-400">
          <Link href="/command-center" className="transition hover:text-cyan-200">
            Command center
          </Link>
          <Link href="/model-insights" className="transition hover:text-cyan-200">
            Model insights
          </Link>
        </nav>
        <ReportForm />
      </div>
    </main>
  );
}

