export interface ValidationIssue {
  category: string;
  severity: string;
  message: string;
  layer: string;
  field: string;
  related_layers: string[];
  repairable: boolean;
  repair_target: string;
}

export interface ValidationReport {
  valid: boolean;
  issues: ValidationIssue[];
  error_count: number;
  warning_count: number;
}

export interface StageResult {
  stage: string;
  status: string;
  duration_ms?: number;
  output?: Record<string, unknown>;
}

export interface RuntimeArtifacts {
  sqlite_schema: string;
  sqlalchemy_models: string;
  fastapi_routes: string;
  react_form_configs: string;
}

export interface PipelineState {
  prompt: string;
  intent?: Record<string, unknown>;
  architecture?: Record<string, unknown>;
  database?: Record<string, unknown>;
  api?: Record<string, unknown>;
  ui?: Record<string, unknown>;
  auth?: Record<string, unknown>;
  validation?: ValidationReport;
  runtime?: RuntimeArtifacts;
  stages: StageResult[];
  repair_actions: Record<string, unknown>[];
  logs: { stage: string; level: string; message: string }[];
}

export interface GenerateResponse {
  success: boolean;
  state: PipelineState;
  error?: Record<string, unknown>;
  metrics?: Record<string, unknown>;
}

export interface MetricsResponse {
  total_runs: number;
  successful_runs: number;
  success_rate: number;
  total_retries: number;
  total_validation_failures: number;
  total_repairs: number;
  average_latency_ms: number;
  estimated_token_cost: number;
  recent_runs: Record<string, unknown>[];
}
