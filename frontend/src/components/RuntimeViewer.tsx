"use client";

import { useState } from "react";
import type { RuntimeArtifacts } from "@/types";

const KEYS = [
  { key: "sqlite_schema" as const, label: "SQLite" },
  { key: "sqlalchemy_models" as const, label: "SQLAlchemy" },
  { key: "fastapi_routes" as const, label: "FastAPI" },
  { key: "react_form_configs" as const, label: "React" },
];

export default function RuntimeViewer({ runtime }: { runtime?: RuntimeArtifacts }) {
  const [active, setActive] = useState<keyof RuntimeArtifacts>("sqlite_schema");

  if (!runtime) {
    return (
      <div className="rounded-xl border border-surface-border bg-surface-elevated p-5">
        <h2 className="text-sm font-semibold uppercase text-slate-400">Runtime Artifacts</h2>
        <p className="mt-2 text-sm text-slate-600">Generated after pipeline completes</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-surface-border bg-surface-elevated p-5">
      <h2 className="mb-3 text-sm font-semibold uppercase text-slate-400">Runtime Artifacts</h2>
      <div className="mb-3 flex gap-1">
        {KEYS.map((k) => (
          <button
            key={k.key}
            type="button"
            onClick={() => setActive(k.key)}
            className={`rounded px-2 py-1 text-xs ${active === k.key ? "bg-success/20 text-success" : "text-slate-500"}`}
          >
            {k.label}
          </button>
        ))}
      </div>
      <pre className="max-h-96 overflow-auto rounded border border-surface-border bg-surface p-4 font-mono text-xs text-emerald-300/90">
        {runtime[active] || "// empty"}
      </pre>
    </div>
  );
}
