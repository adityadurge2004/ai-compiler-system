import type { GenerateResponse, MetricsResponse, PipelineState, ValidationReport } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

export async function checkHealth(): Promise<{ status: string; openai_configured: boolean }> {
  return fetchApi("/health");
}

export async function generate(prompt: string, skipRepair = false): Promise<GenerateResponse> {
  return fetchApi("/api/generate", {
    method: "POST",
    body: JSON.stringify({ prompt, mode: "fast", skip_repair: skipRepair }),
  });
}

export async function repair(state: PipelineState): Promise<GenerateResponse> {
  return fetchApi("/api/repair", {
    method: "POST",
    body: JSON.stringify({
      prompt: state.prompt,
      intent: state.intent,
      architecture: state.architecture,
      database: state.database,
      api: state.api,
      ui: state.ui,
      auth: state.auth,
      validation_report: state.validation,
    }),
  });
}

export async function getMetrics(): Promise<MetricsResponse> {
  return fetchApi("/api/metrics");
}
