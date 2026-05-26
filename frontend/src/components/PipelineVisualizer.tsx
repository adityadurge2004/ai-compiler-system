"use client";

import type { StageResult } from "@/types";

const STAGES = [
  "intent_extraction",
  "architecture_planning",
  "database_generator",
  "api_generator",
  "ui_generator",
  "auth_generator",
  "validation",
  "repair",
  "runtime_generator",
];

interface Props {
  stages: StageResult[];
  loading: boolean;
}

export default function PipelineVisualizer({ stages, loading }: Props) {
  const completed = new Set(stages.map((s) => s.stage));
  const statusMap = Object.fromEntries(stages.map((s) => [s.stage, s.status]));

  return (
    <div className="rounded-xl border border-surface-border bg-surface-elevated p-5">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
        Pipeline Stages
      </h2>
      <div className="space-y-2">
        {STAGES.map((id, i) => {
          const done = completed.has(id);
          const failed = statusMap[id] === "failed";
          const data = stages.find((s) => s.stage === id);
          return (
            <div key={id} className="flex items-center gap-3">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold ${
                  failed ? "bg-error/20 text-error" : done ? "bg-success/20 text-success" : "bg-surface-border text-slate-600"
                }`}
              >
                {done && !failed ? "✓" : i + 1}
              </div>
              <div className="flex-1 text-sm capitalize text-slate-300">
                {id.replace(/_/g, " ")}
                {data?.duration_ms != null && (
                  <span className="ml-2 text-xs text-slate-600">{data.duration_ms.toFixed(0)}ms</span>
                )}
              </div>
              {loading && !done && i === stages.length && (
                <span className="text-xs text-accent-glow">running...</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
