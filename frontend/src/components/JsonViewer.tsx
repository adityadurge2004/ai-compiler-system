"use client";

import { useState } from "react";

const TABS = ["intent", "architecture", "database", "api", "ui", "auth"] as const;

export default function JsonViewer({
  data,
}: {
  data: Partial<Record<(typeof TABS)[number], Record<string, unknown>>>;
}) {
  const [active, setActive] = useState<(typeof TABS)[number]>("intent");

  return (
    <div className="rounded-xl border border-surface-border bg-surface-elevated p-5">
      <h2 className="mb-3 text-sm font-semibold uppercase text-slate-400">Generated Schemas</h2>
      <div className="mb-3 flex flex-wrap gap-1">
        {TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActive(tab)}
            className={`rounded px-2 py-1 text-xs ${active === tab ? "bg-accent text-white" : "text-slate-500"}`}
          >
            {tab}
          </button>
        ))}
      </div>
      <pre className="max-h-80 overflow-auto rounded border border-surface-border bg-surface p-4 font-mono text-xs text-slate-300">
        {data[active] ? JSON.stringify(data[active], null, 2) : "// No data"}
      </pre>
    </div>
  );
}
