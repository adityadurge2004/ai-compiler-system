"use client";

export default function RepairLogs({
  actions,
  logs,
}: {
  actions: Record<string, unknown>[];
  logs: { stage: string; level: string; message: string }[];
}) {
  const repairLogs = logs.filter((l) => l.stage === "repair");

  return (
    <div className="rounded-xl border border-surface-border bg-surface-elevated p-5">
      <h2 className="mb-3 text-sm font-semibold uppercase text-slate-400">Repair Engine</h2>
      {actions.length === 0 && repairLogs.length === 0 ? (
        <p className="text-sm text-slate-600">No repair actions</p>
      ) : (
        <div className="max-h-40 space-y-2 overflow-y-auto text-xs text-slate-400">
          {actions.map((a, i) => (
            <div key={i} className="rounded border border-accent/20 px-3 py-2">
              {(a.layer as string) || "layer"}: {(a.status as string) || "done"}
            </div>
          ))}
          {repairLogs.map((l, i) => (
            <div key={i}>{l.message}</div>
          ))}
        </div>
      )}
    </div>
  );
}
