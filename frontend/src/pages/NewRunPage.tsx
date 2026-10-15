import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import type { Model, Provider, Dataset, BenchmarkRun, RunProgress } from '../types';

interface NewRunPageProps {
  onRunStarted: (run: BenchmarkRun) => void;
  onNavigateToResults: (runId: string) => void;
}

export const NewRunPage: React.FC<NewRunPageProps> = ({ onRunStarted, onNavigateToResults }) => {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [configuredProviders, setConfiguredProviders] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  // Form State
  const [selectedModelIds, setSelectedModelIds] = useState<string[]>([]);
  const [selectedDatasetIds, setSelectedDatasetIds] = useState<string[]>([]);
  const [runName, setRunName] = useState('Cloudflare & Gemini vs Industry Baselines');
  const [temperature, setTemperature] = useState(0.2);
  const [maxTokens, setMaxTokens] = useState(1024);
  const [baselineVersion, setBaselineVersion] = useState('v2026.09 — captured 20 Sep 2026');
  const [claimCheck, setClaimCheck] = useState(true);
  const [taskMixMode, setTaskMixMode] = useState<'standard' | 'quick'>('standard');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Custom Dataset Upload state
  const [categories, setCategories] = useState<{ id: string; name: string; slug: string }[]>([]);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadName, setUploadName] = useState('');
  const [uploadCategory, setUploadCategory] = useState('');
  const [uploadDescription, setUploadDescription] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  // Live active run tracking
  const [activeRun, setActiveRun] = useState<BenchmarkRun | null>(null);
  const [progress, setProgress] = useState<RunProgress | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [provList, modList, dsList, confList, runsList, catList] = await Promise.all([
          api.getProviders(),
          api.getModels(),
          api.getDatasets(),
          api.getConfiguredProviders().catch(() => ({ configured_providers: [] })),
          api.getRuns().catch(() => []),
          api.getCategories().catch(() => []),
        ]);
        setProviders(provList);
        setModels(modList);
        setDatasets(dsList);
        setConfiguredProviders(confList.configured_providers || []);
        setCategories(catList);
        if (catList.length > 0) {
          setUploadCategory(catList[0].id);
        }

        // Pre-select first 2 models by default
        if (modList.length > 0) {
          setSelectedModelIds(modList.slice(0, 2).map((m) => m.id));
        }
        // Pre-select all datasets
        if (dsList.length > 0) {
          setSelectedDatasetIds(dsList.map((d) => d.id));
        }

        // Auto-attach active or latest run
        if (runsList.length > 0) {
          const ongoing = runsList.find((r) => r.status === 'running' || r.status === 'pending');
          const targetRun = ongoing || runsList[0];
          setActiveRun(targetRun);
          api.getRunProgress(targetRun.id).then(setProgress).catch(() => {});
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load platform configuration');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Poll progress if a run is active
  useEffect(() => {
    if (!activeRun) return;
    if (activeRun.status === 'completed' || activeRun.status === 'failed') return;

    const interval = setInterval(async () => {
      try {
        const prog = await api.getRunProgress(activeRun.id);
        setProgress(prog);
        setActiveRun((prev) => (prev ? { ...prev, status: prog.status } : null));
      } catch (e) {
        console.error('Error polling run progress:', e);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [activeRun?.id, activeRun?.status]);

  const toggleModel = (id: string) => {
    setSelectedModelIds((prev) =>
      prev.includes(id) ? prev.filter((mId) => mId !== id) : [...prev, id]
    );
  };

  const toggleDataset = (id: string) => {
    setSelectedDatasetIds((prev) =>
      prev.includes(id) ? prev.filter((dId) => dId !== id) : [...prev, id]
    );
  };

  const selectAllModels = () => {
    setSelectedModelIds(models.map((m) => m.id));
  };

  const deselectAllModels = () => {
    setSelectedModelIds([]);
  };

  const selectAllDatasets = () => {
    setSelectedDatasetIds(datasets.map((d) => d.id));
  };

  const deselectAllDatasets = () => {
    setSelectedDatasetIds([]);
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      setUploadError('Please select a JSON or CSV benchmark dataset file.');
      return;
    }
    if (!uploadName.trim()) {
      setUploadError('Please specify a benchmark dataset name.');
      return;
    }
    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('name', uploadName.trim());
    formData.append('category_id', uploadCategory || (categories[0]?.id ?? 'coding'));
    if (uploadDescription.trim()) {
      formData.append('description', uploadDescription.trim());
    }

    try {
      const res = await api.uploadDataset(formData);
      setUploadSuccess(res.message || 'Dataset uploaded and validated successfully!');
      const updatedDs = await api.getDatasets();
      setDatasets(updatedDs);
      if (res.id) {
        setSelectedDatasetIds((prev) => [...prev, res.id]);
      }
      setTimeout(() => {
        setShowUploadModal(false);
        setUploadName('');
        setUploadDescription('');
        setUploadFile(null);
        setUploadSuccess(null);
      }, 1500);
    } catch (err: any) {
      setUploadError(err.message || 'Dataset upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedModelIds.length === 0) {
      setError('Please select at least one candidate model to test.');
      return;
    }
    if (selectedDatasetIds.length === 0) {
      setError('Please select at least one evaluation dataset suite.');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const newRun = await api.createRun({
        name: runName,
        model_ids: selectedModelIds,
        dataset_ids: selectedDatasetIds,
        temperature,
        max_tokens: maxTokens,
        task_mix_mode: taskMixMode,
      });
      setActiveRun(newRun);
      onRunStarted(newRun);
      api.getRunProgress(newRun.id).then(setProgress).catch(() => {});
    } catch (err: any) {
      setError(err.message || 'Failed to launch benchmark run');
    } finally {
      setSubmitting(false);
    }
  };

  const tasksPerDataset = taskMixMode === 'quick' ? 2 : 10;
  const totalCalculatedCells = selectedModelIds.length * selectedDatasetIds.length * tasksPerDataset;
  const succeeded = progress?.succeeded_cells ?? 0;
  const failed = progress?.failed_cells ?? 0;
  const totalCells = progress?.total_cells && progress.total_cells > 0 ? progress.total_cells : (totalCalculatedCells || 1);
  const completed = succeeded + failed;
  const progressPercent = Math.min(100, Math.round((completed / totalCells) * 100));

  return (
    <main>
      <div className="page-head">
        <div>
          <h1>Start a benchmark run</h1>
          <p className="muted">
            Configure candidate models and datasets. Meridian will execute each prompt, measure quality and hallucination, and position models against industry baselines.
          </p>
        </div>
      </div>

      {error && (
        <div className="callout" style={{ borderColor: 'var(--t-weak)', background: 'var(--t-weak-bg)', color: 'var(--t-weak)', marginBottom: 20 }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="grid-2">
        <div className="stack">
          {/* Models selection */}
          <section className="panel">
            <div className="panel-head">
              <h2>Models to test ({selectedModelIds.length}/{models.length})</h2>
              <div className="btn-row" style={{ gap: 6 }}>
                <button type="button" className="btn small" onClick={selectAllModels} style={{ padding: '2px 8px', fontSize: 11 }}>
                  Select all
                </button>
                <button type="button" className="btn small" onClick={deselectAllModels} style={{ padding: '2px 8px', fontSize: 11 }}>
                  Clear
                </button>
              </div>
            </div>
            {loading ? (
              <p className="muted small">Loading registered models...</p>
            ) : (
              <div className="choices">
                {models.map((m) => {
                  const provider = providers.find((p) => p.id === m.provider_id);
                  const isConfigured = configuredProviders.some((cp) =>
                    provider?.name.toLowerCase().includes(cp)
                  );
                  return (
                    <label key={m.id} className="choice">
                      <input
                        type="checkbox"
                        checked={selectedModelIds.includes(m.id)}
                        onChange={() => toggleModel(m.id)}
                      />
                      <div>
                        <b>{m.display_name}</b>
                        <span>
                          {provider?.name || 'External'} · {isConfigured ? 'Key active' : 'Default config'}
                        </span>
                      </div>
                    </label>
                  );
                })}
              </div>
            )}
          </section>

          {/* Datasets selection */}
          <section className="panel">
            <div className="panel-head">
              <h2>Benchmark Datasets ({selectedDatasetIds.length}/{datasets.length})</h2>
              <div className="btn-row" style={{ gap: 6 }}>
                <button
                  type="button"
                  className="btn small"
                  onClick={() => setShowUploadModal(!showUploadModal)}
                  style={{
                    padding: '2px 8px',
                    fontSize: 11,
                    background: showUploadModal ? 'var(--accent)' : 'var(--accent-soft)',
                    color: showUploadModal ? '#fff' : 'var(--accent)',
                    borderColor: 'var(--accent)',
                  }}
                >
                  {showUploadModal ? 'Close Uploader' : '+ Upload Custom Dataset'}
                </button>
                <button type="button" className="btn small" onClick={selectAllDatasets} style={{ padding: '2px 8px', fontSize: 11 }}>
                  Select all
                </button>
                <button type="button" className="btn small" onClick={deselectAllDatasets} style={{ padding: '2px 8px', fontSize: 11 }}>
                  Clear
                </button>
              </div>
            </div>

            {showUploadModal && (
              <form
                onSubmit={handleUploadSubmit}
                style={{
                  background: 'var(--bg)',
                  border: '1px solid var(--line)',
                  borderRadius: 6,
                  padding: 14,
                  marginBottom: 14,
                }}
              >
                <h3 style={{ margin: '0 0 8px 0', fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Upload Custom Dataset (CSV or JSON)
                </h3>
                <p className="small muted" style={{ margin: '0 0 12px 0' }}>
                  Supports CSV or JSON schemas with required <span className="mono">prompt</span>, and optional <span className="mono">reference_answer</span>, <span className="mono">context</span>, and <span className="mono">system_prompt</span> (FR-2.2, FR-2.3).
                </p>

                {uploadError && (
                  <div className="callout" style={{ borderColor: 'var(--t-weak)', background: 'var(--t-weak-bg)', marginBottom: 10, padding: 8, fontSize: 12 }}>
                    {uploadError}
                  </div>
                )}
                {uploadSuccess && (
                  <div className="callout" style={{ borderColor: 'var(--t-strong)', background: 'var(--t-strong-bg)', marginBottom: 10, padding: 8, fontSize: 12 }}>
                    {uploadSuccess}
                  </div>
                )}

                <div className="row-2" style={{ marginBottom: 10 }}>
                  <div className="field">
                    <label style={{ fontSize: 12 }}>Dataset Name</label>
                    <input
                      type="text"
                      placeholder="e.g. Enterprise Legal QA v1"
                      value={uploadName}
                      onChange={(e) => setUploadName(e.target.value)}
                      required
                      style={{ fontSize: 12 }}
                    />
                  </div>
                  <div className="field">
                    <label style={{ fontSize: 12 }}>Capability Category</label>
                    <select
                      value={uploadCategory}
                      onChange={(e) => setUploadCategory(e.target.value)}
                      style={{ fontSize: 12 }}
                    >
                      {categories.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="field" style={{ marginBottom: 10 }}>
                  <label style={{ fontSize: 12 }}>Dataset Description (Optional)</label>
                  <input
                    type="text"
                    placeholder="Brief description of the benchmark suite"
                    value={uploadDescription}
                    onChange={(e) => setUploadDescription(e.target.value)}
                    style={{ fontSize: 12 }}
                  />
                </div>

                <div className="field" style={{ marginBottom: 12 }}>
                  <label style={{ fontSize: 12 }}>File (.json or .csv)</label>
                  <input
                    type="file"
                    accept=".json,.csv"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setUploadFile(e.target.files[0]);
                        if (!uploadName) {
                          setUploadName(e.target.files[0].name.replace(/\.[^/.]+$/, ''));
                        }
                      }
                    }}
                    style={{ fontSize: 12 }}
                  />
                </div>

                <div className="btn-row" style={{ gap: 8 }}>
                  <button className="btn primary small" type="submit" disabled={uploading}>
                    {uploading ? 'Validating & Uploading...' : 'Upload & Validate'}
                  </button>
                  <button className="btn small" type="button" onClick={() => setShowUploadModal(false)}>
                    Cancel
                  </button>
                </div>
              </form>
            )}

            <div className="choices">

              {datasets.map((d) => (
                <label key={d.id} className="choice">
                  <input
                    type="checkbox"
                    checked={selectedDatasetIds.includes(d.id)}
                    onChange={() => toggleDataset(d.id)}
                  />
                  <div>
                    <b>{d.name}</b>
                    <span>{d.task_type.toUpperCase()} · 10 tasks</span>
                  </div>
                </label>
              ))}
            </div>
          </section>

          {/* Dataset Mode */}
          <section className="panel">
            <div className="panel-head">
              <h2>Task Mix</h2>
              <span className="hint">{taskMixMode === 'standard' ? '10 tasks per dataset' : '2 tasks per dataset'}</span>
            </div>
            <div className="choices">
              <label className="choice">
                <input
                  type="radio"
                  name="d_mode"
                  checked={taskMixMode === 'standard'}
                  onChange={() => setTaskMixMode('standard')}
                />
                <div>
                  <b>Standard suite</b>
                  <span>All tasks across selected datasets (10 tasks/set)</span>
                </div>
              </label>
              <label className="choice">
                <input
                  type="radio"
                  name="d_mode"
                  checked={taskMixMode === 'quick'}
                  onChange={() => setTaskMixMode('quick')}
                />
                <div>
                  <b>Quick evaluation</b>
                  <span>Fast test with 2 tasks per dataset</span>
                </div>
              </label>
            </div>
          </section>
        </div>

        <div className="stack">
          {/* Run Settings */}
          <section className="panel">
            <div className="panel-head">
              <h2>Run configuration</h2>
            </div>

            <div className="field">
              <label htmlFor="name">Run name</label>
              <input
                id="name"
                type="text"
                value={runName}
                onChange={(e) => setRunName(e.target.value)}
                required
              />
            </div>

            <div className="row-2">
              <div className="field">
                <label htmlFor="temp">Temperature</label>
                <input
                  id="temp"
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                />
              </div>
              <div className="field">
                <label htmlFor="maxtok">Max output tokens</label>
                <input
                  id="maxtok"
                  type="number"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                />
              </div>
            </div>

            <div className="field">
              <label htmlFor="base">Compare against baseline set</label>
              <select
                id="base"
                value={baselineVersion}
                onChange={(e) => setBaselineVersion(e.target.value)}
              >
                <option>v2026.09 — captured 20 Sep 2026</option>
                <option>v2026.06 — captured 18 Jun 2026</option>
              </select>
              <span className="hint">Tiers are computed relative to this version's score distribution.</span>
            </div>

            <fieldset>
              <label className="legend" style={{ display: 'block', marginBottom: 8 }}>
                Evaluation Modules
              </label>
              <label className="choice" style={{ display: 'block', marginBottom: 8 }}>
                <input
                  type="checkbox"
                  checked={claimCheck}
                  onChange={(e) => setClaimCheck(e.target.checked)}
                />
                <div>
                  <b>Claim-level hallucination verification</b>
                  <span>Extracts atomic claims and validates against reference passages</span>
                </div>
              </label>
            </fieldset>

            <div className="callout" style={{ marginBottom: 16 }}>
              Estimated workload: <b>≈ {totalCalculatedCells} requests</b> across {selectedModelIds.length} models.
            </div>

            <div className="btn-row">
              <button className="btn primary" type="submit" disabled={submitting}>
                {submitting ? 'Starting run...' : 'Start benchmark run'}
              </button>
              <button
                className="btn"
                type="button"
                onClick={() => {
                  setSelectedModelIds(models.slice(0, 2).map((m) => m.id));
                  setRunName('Cloudflare & Gemini vs Industry Baselines');
                }}
              >
                Reset
              </button>
            </div>
          </section>

          {/* Live Progress Monitoring */}
          {activeRun && (
            <section className="panel" style={{ borderLeft: '4px solid var(--accent)' }}>
              <div className="panel-head">
                <div>
                  <h2>Live Progress: {activeRun.name}</h2>
                  <span className="small muted">Run ID: {activeRun.id.slice(0, 8)}...</span>
                </div>
                <span
                  className={`status ${
                    activeRun.status === 'completed'
                      ? 'ok'
                      : activeRun.status === 'failed'
                      ? 'fail'
                      : activeRun.status === 'running'
                      ? 'run'
                      : 'wait'
                  }`}
                >
                  {activeRun.status.toUpperCase()}
                </span>
              </div>
              <p className="small muted" style={{ marginBottom: 14 }}>
                Matrix execution underway. Tasks are throttled per provider rate limits.
              </p>

              {progress ? (
                <>
                  <div className="key-line">
                    <span>Overall Cells Completed</span>
                    <span className="small num">
                      {completed} / {progress.total_cells || totalCalculatedCells} ({progressPercent}%)
                    </span>
                  </div>
                  <div className="progress" style={{ margin: '6px 0 14px' }}>
                    <i style={{ width: `${progressPercent}%` }} />
                  </div>

                  {/* Live counters breakdown */}
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(4, 1fr)',
                      gap: 8,
                      marginBottom: 16,
                      fontSize: '0.82rem',
                    }}
                  >
                    <div style={{ padding: '6px 10px', background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: 6, textAlign: 'center' }}>
                      <span className="muted" style={{ display: 'block', fontSize: '0.72rem' }}>SUCCEEDED</span>
                      <b style={{ color: 'var(--t-strong)', fontSize: '1rem' }}>{succeeded}</b>
                    </div>
                    <div style={{ padding: '6px 10px', background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: 6, textAlign: 'center' }}>
                      <span className="muted" style={{ display: 'block', fontSize: '0.72rem' }}>RUNNING</span>
                      <b style={{ color: 'var(--accent)', fontSize: '1rem' }}>{(progress as any).running ?? 0}</b>
                    </div>
                    <div style={{ padding: '6px 10px', background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: 6, textAlign: 'center' }}>
                      <span className="muted" style={{ display: 'block', fontSize: '0.72rem' }}>PENDING</span>
                      <b style={{ color: 'var(--ink-2)', fontSize: '1rem' }}>{(progress as any).pending ?? 0}</b>
                    </div>
                    <div style={{ padding: '6px 10px', background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: 6, textAlign: 'center' }}>
                      <span className="muted" style={{ display: 'block', fontSize: '0.72rem' }}>FAILED</span>
                      <b style={{ color: failed > 0 ? 'var(--t-weak)' : 'var(--ink-3)', fontSize: '1rem' }}>{failed}</b>
                    </div>
                  </div>

                  {activeRun.status === 'completed' && (
                    <div className="callout" style={{ borderColor: 'var(--t-strong)', background: 'var(--t-strong-bg)', color: 'var(--t-strong)', marginBottom: 14 }}>
                      ✓ Benchmark complete! All candidate outputs and judge scores are compiled and ready.
                    </div>
                  )}

                  <div className="btn-row">
                    <button
                      type="button"
                      className="btn primary"
                      onClick={() => onNavigateToResults(activeRun.id)}
                    >
                      View Live Results Dashboard →
                    </button>
                  </div>
                </>
              ) : (
                <p className="small muted">Initializing work queue...</p>
              )}
            </section>
          )}
        </div>
      </form>
    </main>
  );
};
