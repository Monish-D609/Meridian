import type {
  Provider,
  Model,
  Dataset,
  BenchmarkRun,
  RunProgress,
  RunResult,
  EvaluationScore,
  BaselineModel,
  ComparisonPayload,
} from '../types';

const API_BASE = '/api/v1';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const err = await res.json();
      if (err.detail) errorDetail = err.detail;
    } catch {}
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // Providers & Models
  getProviders: () => request<Provider[]>('/providers'),
  getConfiguredProviders: () => request<{ configured_providers: string[] }>('/providers/configured/list'),
  getModels: (providerId?: string) =>
    request<Model[]>(`/models${providerId ? `?provider_id=${providerId}` : ''}`),

  // Datasets
  getDatasets: () => request<Dataset[]>('/datasets'),
  getCategories: () =>
    request<{ id: string; name: string; slug: string; description?: string }[]>('/categories'),
  uploadDataset: async (formData: FormData): Promise<any> => {
    const res = await fetch(`${API_BASE}/datasets/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      let errorDetail = `Upload failed with status ${res.status}`;
      try {
        const err = await res.json();
        if (err.detail) errorDetail = err.detail;
      } catch {}
      throw new Error(errorDetail);
    }
    return res.json();
  },
  createCustomDataset: (payload: {
    name: string;
    category_id: string;
    description?: string;
    task_type?: string;
    tasks: { prompt: string; reference_answer?: string; context?: string; system_prompt?: string }[];
  }) =>
    request<any>('/datasets/custom', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Provider Keys
  saveProviderKey: (provider_name: string, api_key: string, extra?: Record<string, string>) =>
    request<{ status: string; provider: string; message: string; configured_providers: string[] }>(
      '/providers/key',
      {
        method: 'POST',
        body: JSON.stringify({ provider_name, api_key, extra }),
      }
    ),

  // Baselines
  getBaselines: () => request<BaselineModel[]>('/baselines'),

  // Runs
  getRuns: () => request<BenchmarkRun[]>('/runs'),
  getRun: (id: string) => request<BenchmarkRun>(`/runs/${id}`),
  getRunProgress: (id: string) => request<RunProgress>(`/runs/${id}/progress`),
  createRun: (data: {
    name: string;
    model_ids: string[];
    dataset_ids: string[];
    description?: string;
    max_tokens?: number;
    temperature?: number;
    task_mix_mode?: 'standard' | 'quick';
  }) =>
    request<BenchmarkRun>('/runs', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Results & Comparison
  getRunResults: (runId: string, modelId?: string) =>
    request<RunResult[]>(`/runs/${runId}/results${modelId ? `?model_id=${modelId}` : ''}`),
  getRunComparison: (runId: string) => request<ComparisonPayload>(`/runs/${runId}/comparison`),
  getCapabilityProfiles: (runId: string) => request<any>(`/runs/${runId}/capability-profiles`),
  getResultScores: (runResultId: string) => request<EvaluationScore[]>(`/results/${runResultId}/scores`),

  // Reports
  getCsvReportUrl: (runId: string) => `/api/v1/runs/${runId}/report/csv`,
  getPdfReportUrl: (runId: string) => `/api/v1/runs/${runId}/report/pdf`,
};
