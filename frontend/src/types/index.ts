export interface Provider {
  id: string;
  name: string;
  base_url?: string;
  auth_env_var?: string;
  is_active: boolean;
  notes?: string;
}

export interface Model {
  id: string;
  provider_id: string;
  model_id_external: string;
  display_name: string;
  description?: string;
  is_active: boolean;
  rate_limit_rpm?: number;
  rate_limit_tpm?: number;
}

export interface CapabilityCategory {
  id: string;
  name: string;
  slug: string;
  description?: string;
}

export interface Dataset {
  id: string;
  name: string;
  description?: string;
  category_id: string;
  task_type: 'closed' | 'open';
  source_url?: string;
  license_info?: string;
  version_tag?: string;
}

export interface BenchmarkRun {
  id: string;
  name: string;
  description?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  judge_provider?: string;
  judge_model_id?: string;
  judge_model_version?: string;
  config_json?: any;
  total_cells?: number;
  succeeded_cells?: number;
  failed_cells?: number;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface RunProgress {
  run_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  total_cells: number;
  succeeded_cells: number;
  failed_cells: number;
  cells: Array<{
    id: string;
    model_id: string;
    task_id: string;
    status: 'pending' | 'running' | 'succeeded' | 'failed';
    latency_ms?: number;
    error_message?: string;
  }>;
}

export interface EvaluationScore {
  id: string;
  metric_name: string;
  score?: number;
  score_metadata?: any;
  scorer_version: string;
  judge_model_version?: string;
}

export interface RunResult {
  id: string;
  run_id: string;
  model_id: string;
  model_name?: string;
  task_id: string;
  task_prompt?: string;
  task_reference_answer?: string;
  category_name?: string;
  category_slug?: string;
  status: string;
  response_text?: string;
  input_tokens?: number;
  output_tokens?: number;
  latency_ms?: number;
  error_message?: string;
  quality_score?: number;
  groundedness_score?: number;
  hallucination_rate?: number;
  claims?: Array<{ claim: string; verdict: string }>;
  has_hallucination?: boolean;
}

export interface BaselineModel {
  id: string;
  display_name: string;
  version_tag: string;
  captured_date: string;
  notes?: string;
  source_url?: string;
  is_placeholder: boolean;
}

export interface ModelSummary {
  model_id: string;
  model_display_name: string;
  model_external_id: string;
  total_tasks: number;
  succeeded_tasks: number;
  failed_tasks: number;
  avg_metrics: Record<string, number>;
  tier_breakdown: Record<string, any>;
  positioning_summary: any;
}

export interface ComparisonPayload {
  run_id: string;
  run_name: string;
  run_status: string;
  judge_model: string;
  judge_model_version?: string;
  models: ModelSummary[];
  config?: any;
}
