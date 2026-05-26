"use client";

interface PromptInputProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  loading: boolean;
  skipRepair: boolean;
  onSkipRepairChange: (v: boolean) => void;
}

export default function PromptInput({
  value,
  onChange,
  onSubmit,
  loading,
  skipRepair,
  onSkipRepairChange,
}: PromptInputProps) {
  return (
    <div className="rounded-xl border border-surface-border bg-surface-elevated p-5">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Natural Language Input
        </h2>
        <label className="flex items-center gap-2 text-xs text-slate-500">
          <input
            type="checkbox"
            checked={skipRepair}
            onChange={(e) => onSkipRepairChange(e.target.checked)}
          />
          Skip repair
        </label>
      </div>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Describe the application you want to compile..."
        rows={4}
        className="w-full resize-none rounded-lg border border-surface-border bg-surface px-4 py-3 text-sm text-slate-200 focus:border-accent focus:outline-none"
      />
      <button
        type="button"
        onClick={onSubmit}
        disabled={loading || value.trim().length < 10}
        className="mt-4 w-full rounded-lg bg-accent px-4 py-3 text-sm font-semibold text-white disabled:opacity-50"
      >
        {loading ? "Compiling..." : "Compile Application"}
      </button>
    </div>
  );
}
