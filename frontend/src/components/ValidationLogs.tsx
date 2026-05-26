"use client";

import type { ValidationReport } from "@/types";

export default function ValidationLogs({ report }: { report?: ValidationReport }) {
  if (!report) {
    return (
      <div className="rounded-xl border border-surface-border bg-surface-elevated p-5">
        <h2 className="text-sm font-semibold uppercase text-slate-400">Validation</h2>
        <p className="mt-2 text-sm text-slate-600">Run compile to see results</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-surface-border bg-surface-elevated p-5">
      <div className="mb-3 flex justify-between">
        <h2 className="text-sm font-semibold uppercase text-slate-400">Validation</h2>
        <span className={`text-xs ${report.valid ? "text-success" : "text-error"}`}>
          {report.valid ? "PASSED" : `${report.error_count} errors`}
        </span>
      </div>
      <div className="max-h-48 space-y-2 overflow-y-auto">
        {report.issues.map((issue, i) => (
          <div key={i} className="rounded border border-surface-border px-3 py-2 text-xs text-slate-400">
            <span className="text-slate-600">[{issue.layer}] </span>
            {issue.message}
          </div>
        ))}
        {report.issues.length === 0 && <p className="text-sm text-success">All checks passed</p>}
      </div>
    </div>
  );
}
