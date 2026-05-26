"use client";

import { useCallback, useEffect, useState } from "react";
import { checkHealth, generate, repair } from "@/lib/api";
import type { GenerateResponse } from "@/types";
import PromptInput from "@/components/PromptInput";
import PipelineVisualizer from "@/components/PipelineVisualizer";
import ValidationLogs from "@/components/ValidationLogs";
import RepairLogs from "@/components/RepairLogs";
import JsonViewer from "@/components/JsonViewer";
import RuntimeViewer from "@/components/RuntimeViewer";

export default function Dashboard() {
  const [prompt, setPrompt] = useState(
    "Build a CRM with login, dashboard, role-based access, contacts management, and Stripe payments."
  );
  const [skipRepair, setSkipRepair] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<string>("checking...");

  useEffect(() => {
    checkHealth()
      .then((h) => setHealth(h.openai_configured ? "OpenAI ready" : "Demo mode"))
      .catch(() => setHealth("Backend offline"));
  }, []);

  const handleCompile = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await generate(prompt, skipRepair);
      setResult(res);
      if (res.error) {
        setError(String((res.error as { message?: string }).message || "Compilation failed"));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed — is the backend running on port 8000?");
    } finally {
      setLoading(false);
    }
  }, [prompt, skipRepair]);

  const handleRepair = useCallback(async () => {
    if (!result?.state) return;
    setLoading(true);
    try {
      setResult(await repair(result.state));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Repair failed");
    } finally {
      setLoading(false);
    }
  }, [result]);

  const state = result?.state;

  return (
    <div className="min-h-screen">
      <header className="border-b border-surface-border px-6 py-4">
        <h1 className="text-xl font-bold text-white">AI Compiler System</h1>
        <p className="text-xs text-slate-500">Status: {health}</p>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
        {error && (
          <div className="mb-4 rounded-lg border border-error/30 bg-error/10 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-6">
            <PromptInput
              value={prompt}
              onChange={setPrompt}
              onSubmit={handleCompile}
              loading={loading}
              skipRepair={skipRepair}
              onSkipRepairChange={setSkipRepair}
            />
            <PipelineVisualizer stages={state?.stages || []} loading={loading} />
            {state?.validation && !state.validation.valid && (
              <button
                type="button"
                onClick={handleRepair}
                disabled={loading}
                className="w-full rounded-lg border border-warning/50 py-2 text-sm text-warning"
              >
                Run Targeted Repair
              </button>
            )}
          </div>

          <div className="space-y-6 lg:col-span-2">
            <div className="grid gap-6 md:grid-cols-2">
              <ValidationLogs report={state?.validation} />
              <RepairLogs actions={state?.repair_actions || []} logs={state?.logs || []} />
            </div>
            <JsonViewer
              data={{
                intent: state?.intent,
                architecture: state?.architecture,
                database: state?.database,
                api: state?.api,
                ui: state?.ui,
                auth: state?.auth,
              }}
            />
            <RuntimeViewer runtime={state?.runtime} />
          </div>
        </div>
      </main>
    </div>
  );
}
