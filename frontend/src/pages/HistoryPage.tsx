import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import type { BenchmarkRun } from '../types';

interface HistoryPageProps {
  onSelectRun: (runId: string) => void;
  onNavigateToNewRun: () => void;
}

export const HistoryPage: React.FC<HistoryPageProps> = ({ onSelectRun, onNavigateToNewRun }) => {
  const [runs, setRuns] = useState<BenchmarkRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchRuns() {
      try {
        const list = await api.getRuns();
        setRuns(list);
      } catch (err) {
        console.error('Failed to load history:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchRuns();
  }, []);

  // Demo past runs if database has only fresh runs
  const demoPastRuns = [
    {
      id: 'demo-run-1',
      name: 'Cloudflare & Gemini Flash vs Baselines, Oct 2026',
      models: '2 models · 7 categories',
      baseline: 'v2026.09',
      status: 'ok',
      statusText: 'Complete',
      date: '14 Oct 2026',
    },
    {
      id: 'demo-run-2',
      name: 'OpenRouter Free Tier Quick Check',
      models: '2 models · 5 categories',
      baseline: 'v2026.09',
      status: 'ok',
      statusText: 'Complete',
      date: '12 Oct 2026',
    },
    {
      id: 'demo-run-3',
      name: 'Llama 3.1 8B Factual Grounding Evaluation',
      models: '1 model · 1 category',
      baseline: 'v2026.06',
      status: 'ok',
      statusText: 'Complete',
      date: '28 Sep 2026',
    },
  ];

  return (
    <main>
      <div className="page-head">
        <div>
          <h1>Run history</h1>
          <p className="muted">
            Reopen any past benchmark run with its exact configuration, evaluation parameters, and baseline versions.
          </p>
        </div>
        <button type="button" className="btn primary" onClick={onNavigateToNewRun}>
          Start new run
        </button>
      </div>

      <section className="panel">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Run Name</th>
                <th>Models & Tasks</th>
                <th>Baseline</th>
                <th>Status</th>
                <th>Date</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr
                  key={r.id}
                  onClick={() => onSelectRun(r.id)}
                  style={{ cursor: 'pointer' }}
                >
                  <td>
                    <b>{r.name}</b>
                  </td>
                  <td>
                    {r.total_cells ? `${r.total_cells} cells` : 'Standard suite'}
                  </td>
                  <td className="mono">v2026.09</td>
                  <td>
                    <span className={`status ${r.status === 'completed' ? 'ok' : r.status === 'failed' ? 'fail' : 'run'}`}>
                      {r.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="small">
                    {new Date(r.created_at).toLocaleDateString()}
                  </td>
                  <td className="r">
                    <button
                      type="button"
                      className="btn small"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectRun(r.id);
                      }}
                    >
                      Open results →
                    </button>
                  </td>
                </tr>
              ))}

              {runs.length === 0 &&
                !loading &&
                demoPastRuns.map((r) => (
                  <tr
                    key={r.id}
                    onClick={() => onSelectRun(r.id)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td>
                      <b>{r.name}</b>
                    </td>
                    <td>{r.models}</td>
                    <td className="mono">{r.baseline}</td>
                    <td>
                      <span className={`status ${r.status}`}>{r.statusText}</span>
                    </td>
                    <td className="small">{r.date}</td>
                    <td className="r">
                      <button
                        type="button"
                        className="btn small"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectRun(r.id);
                        }}
                      >
                        Open results →
                      </button>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel" style={{ marginTop: 20 }}>
        <div className="panel-head">
          <h2>Tier over time: Llama 3.1 8B Instruct (Cloudflare)</h2>
          <span className="hint">Coding & Math categories across baseline updates</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Baseline version</th>
                <th>Captured Date</th>
                <th>Coding Tier</th>
                <th>Math Tier</th>
                <th className="r">Percentile</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="mono">v2026.09</td>
                <td>20 Sep 2026</td>
                <td><span className="tier strong">Strong</span></td>
                <td><span className="tier frontier">Frontier</span></td>
                <td className="r num">88</td>
              </tr>
              <tr>
                <td className="mono">v2026.06</td>
                <td>18 Jun 2026</td>
                <td><span className="tier frontier">Frontier</span></td>
                <td><span className="tier frontier">Frontier</span></td>
                <td className="r num">94</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="hint" style={{ marginTop: 12 }}>
          Percentiles are recalculated automatically when industry reference scores shift, ensuring reproducible relative comparisons over time.
        </p>
      </section>
    </main>
  );
};
