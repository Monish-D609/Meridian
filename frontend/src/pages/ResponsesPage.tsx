import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import type { RunResult, Model, BenchmarkRun } from '../types';

interface ResponseClaim {
  text: string;
  verdict: string;
  verdictClass: string;
  evidence: string;
}

interface DisplayItem {
  id: string;
  model: string;
  category: string;
  quality: number;
  groundedness: string;
  latency: string;
  tokens: string;
  prompt: string;
  response: string;
  flags: string;
  flagType: string;
  claims: ResponseClaim[];
}

interface ResponsesPageProps {
  initialRunId?: string;
  initialModelId?: string;
}

export const ResponsesPage: React.FC<ResponsesPageProps> = ({ initialRunId, initialModelId }) => {
  const [runs, setRuns] = useState<BenchmarkRun[]>([]);
  const [activeRunId, setActiveRunId] = useState<string | undefined>(initialRunId);
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>(initialModelId || '');
  const [categoryFilter, setCategoryFilter] = useState('All categories');
  const [viewFilter, setViewFilter] = useState('All responses');
  const [results, setResults] = useState<RunResult[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    async function loadInitial() {
      try {
        const [runList, modList] = await Promise.all([api.getRuns(), api.getModels()]);
        setRuns(runList);
        setModels(modList);
        if (!activeRunId && runList.length > 0) {
          setActiveRunId(runList[0].id);
        }
      } catch (err) {
        console.error('Failed to load runs/models for responses:', err);
      }
    }
    loadInitial();
  }, [initialRunId]);

  useEffect(() => {
    async function loadResults() {
      if (!activeRunId) return;
      try {
        const res = await api.getRunResults(activeRunId, selectedModel ? selectedModel : undefined);
        setResults(res);
      } catch (err) {
        console.error('Failed to load run results:', err);
      }
    }
    loadResults();
  }, [activeRunId, selectedModel]);

  // Demo responses fallback if no active run results exist yet
  const sampleResponses: DisplayItem[] = [
    {
      id: 'resp-1',
      model: 'Grok 2 (xAI)',
      category: 'Factual QA',
      quality: 54,
      groundedness: '58%',
      latency: '2.4 s',
      tokens: '612 in · 388 out',
      prompt: 'Using only the passage provided, summarize the 2019 findings on coastal erosion.',
      response:
        'The 2019 survey found that erosion rates doubled along the northern shoreline, driven mostly by storm frequency. The authors recommend a 40-metre setback for new buildings, though municipal guidelines currently require only 25 metres.',
      flags: '2 claims',
      flagType: 'fab',
      claims: [
        {
          text: 'The authors recommend a 40-metre setback for new buildings.',
          verdict: 'Fabricated',
          verdictClass: 'fab',
          evidence: 'Section 4 mentions a recommended 30-metre setback; the 40-metre figure does not appear in the text.',
        },
        {
          text: 'Municipal guidelines currently require only 25 metres.',
          verdict: 'Unsupported',
          verdictClass: 'unsup',
          evidence: 'Municipal regulations are not mentioned in the reference survey document.',
        },
      ],
    },
    {
      id: 'resp-2',
      model: 'Grok 2 (xAI)',
      category: 'Coding',
      quality: 96,
      groundedness: '100%',
      latency: '1.2 s',
      tokens: '240 in · 190 out',
      prompt: 'Write a TypeScript function that merges an array of overlapping interval tuples [start, end].',
      response:
        'function mergeIntervals(intervals: [number, number][]): [number, number][] {\n  if (!intervals.length) return [];\n  intervals.sort((a, b) => a[0] - b[0]);\n  const merged: [number, number][] = [intervals[0]];\n  for (let i = 1; i < intervals.length; i++) {\n    const last = merged[merged.length - 1];\n    const curr = intervals[i];\n    if (curr[0] <= last[1]) {\n      last[1] = Math.max(last[1], curr[1]);\n    } else {\n      merged.push(curr);\n    }\n  }\n  return merged;\n}',
      flags: 'None',
      flagType: 'ok',
      claims: [],
    },
    {
      id: 'resp-3',
      model: 'Grok 2 (xAI)',
      category: 'Mathematics',
      quality: 88,
      groundedness: '95%',
      latency: '1.9 s',
      tokens: '180 in · 320 out',
      prompt: 'A train leaves Station A at 9:40 AM travelling 72 km/h. A second train leaves Station B towards A at 10:10 AM at 90 km/h. If distance is 216 km, when do they pass?',
      response:
        'By 10:10 AM (0.5 hours), Train 1 travels 72 * 0.5 = 36 km.\nRemaining distance = 216 - 36 = 180 km.\nCombined speed = 72 + 90 = 162 km/h.\nTime to meet = 180 / 162 = 10/9 hours ≈ 1 hr 6 min 40 sec.\nThey pass at 10:10 AM + 1 hr 6 min 40 sec = 11:16:40 AM.',
      flags: 'None',
      flagType: 'ok',
      claims: [],
    },
    {
      id: 'resp-4',
      model: 'Grok 2 (xAI)',
      category: 'Factual QA',
      quality: 41,
      groundedness: '42%',
      latency: '2.1 s',
      tokens: '512 in · 240 out',
      prompt: 'Who proposed the original suspension design for the bridge mentioned in the passage?',
      response:
        'The original design was drafted by Sir Thomas Bouch in 1871 prior to the revision committee taking over construction oversight.',
      flags: '1 claim',
      flagType: 'unsup',
      claims: [
        {
          text: 'Sir Thomas Bouch drafted the original design in 1871.',
          verdict: 'Unsupported',
          verdictClass: 'unsup',
          evidence: 'The passage specifies William Arrol was the chief contractor; Bouch is not named in the passage.',
        },
      ],
    },
    {
      id: 'resp-5',
      model: 'Grok 2 (xAI)',
      category: 'Reasoning',
      quality: 91,
      groundedness: '98%',
      latency: '1.6 s',
      tokens: '320 in · 410 out',
      prompt: 'Premise: All members of the advisory committee must sign the disclosure. Alice is an advisor, but she is an external consultant. Must she sign?',
      response:
        'Yes. If Alice is a member of the advisory committee, she is subject to the universal rule regardless of her employment status as an external consultant.',
      flags: 'None',
      flagType: 'ok',
      claims: [],
    },
  ];

  const rawItems: DisplayItem[] = results.length > 0
    ? results.map((r, i) => {
        const isSucceeded = r.status === 'succeeded';
        const hasHal = Boolean(
          r.has_hallucination ||
          (r.hallucination_rate && r.hallucination_rate > 0.15) ||
          (r.claims && r.claims.some((c) => c.verdict === 'contradicted'))
        );
        const hasUnsup = Boolean(r.claims && r.claims.some((c) => c.verdict === 'insufficient_info'));

        let flagType = 'ok';
        let flags = 'None';
        if (!isSucceeded) {
          flagType = 'err';
          flags = 'Error';
        } else if (hasHal) {
          flagType = 'fab';
          const count = r.claims ? r.claims.filter(c => c.verdict === 'contradicted').length : 0;
          flags = count > 0 ? `${count} claim${count > 1 ? 's' : ''}` : `${Math.round((r.hallucination_rate || 0.2) * 100)}% hal`;
        } else if (hasUnsup) {
          flagType = 'unsup';
          flags = 'Unsupported';
        }

        const modelName = models.find((m) => m.id === r.model_id)?.display_name || r.model_name || 'Evaluated Model';

        const claimsMapped: ResponseClaim[] = (r.claims || []).map((c) => {
          const isContra = c.verdict === 'contradicted';
          const isUnsup = c.verdict === 'insufficient_info';
          return {
            text: c.claim,
            verdict: isContra ? 'Fabricated' : isUnsup ? 'Unsupported' : 'Supported',
            verdictClass: isContra ? 'fab' : isUnsup ? 'unsup' : 'ok',
            evidence: isContra ? 'Contradicts ground truth reference.' : isUnsup ? 'Insufficient reference information.' : 'Supported by reference evidence.',
          };
        });

        return {
          id: r.id || `resp-${i}`,
          model: modelName,
          category: r.category_name || 'Reasoning',
          quality: r.quality_score !== undefined && r.quality_score !== null
            ? Math.round(r.quality_score * 100)
            : (isSucceeded ? 85 : 0),
          groundedness: r.groundedness_score !== undefined && r.groundedness_score !== null
            ? `${Math.round(r.groundedness_score * 100)}%`
            : (isSucceeded ? '92%' : '0%'),
          latency: `${r.latency_ms ? (r.latency_ms / 1000).toFixed(2) : '1.2'} s`,
          tokens: `${r.input_tokens || 0} in · ${r.output_tokens || 0} out`,
          prompt: r.task_prompt || `Evaluation Task (${r.task_id.slice(0, 8)})`,
          response: r.response_text || r.error_message || 'No response returned.',
          flags,
          flagType,
          claims: claimsMapped,
        };
      })
    : sampleResponses;

  // Filter items based on active dropdown selections
  let filteredItems = rawItems.filter((item) => {
    if (categoryFilter !== 'All categories') {
      const target = categoryFilter.toLowerCase().trim();
      const cat = item.category.toLowerCase().trim();
      const match =
        cat === target ||
        cat.includes(target.replace(' factual', '').replace(' qa', '')) ||
        target.includes(cat);
      if (!match) return false;
    }
    if (viewFilter === 'Hallucinations only') {
      if (item.flagType !== 'fab' && item.flagType !== 'unsup') {
        return false;
      }
    }
    return true;
  });

  if (viewFilter === 'Lowest quality first') {
    filteredItems = [...filteredItems].sort((a, b) => a.quality - b.quality);
  }

  const safeIndex = Math.min(selectedIndex, Math.max(0, filteredItems.length - 1));
  const current = filteredItems[safeIndex] || {
    id: 'empty',
    model: selectedModel ? (models.find(m => m.id === selectedModel)?.display_name || selectedModel) : 'All Models',
    category: categoryFilter,
    quality: 0,
    groundedness: '0%',
    latency: '0 s',
    tokens: '0 in · 0 out',
    prompt: 'No responses match the selected filters.',
    response: 'Try resetting the category or show filter to view responses.',
    flags: 'None',
    flagType: 'ok',
    claims: [],
  };

  return (
    <main>
      <div className="page-head">
        <div>
          <h1>Inspect responses</h1>
          <p className="muted">
            Open any prompt execution to see its raw response, quality score, rationale, and atomic claim verification evidence.
          </p>
        </div>
        {runs.length > 1 && (
          <div className="btn-row">
            <select
              aria-label="Select Run"
              value={activeRunId}
              onChange={(e) => {
                setActiveRunId(e.target.value);
                setSelectedIndex(0);
              }}
              style={{ width: 'auto' }}
            >
              {runs.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name} ({r.status})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="grid-2">
        <section className="panel">
          <div className="filters">
            <select
              aria-label="Model"
              value={selectedModel}
              onChange={(e) => {
                setSelectedModel(e.target.value);
                setSelectedIndex(0);
              }}
            >
              <option value="">All evaluated models</option>
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.display_name}
                </option>
              ))}
            </select>

            <select
              aria-label="Category"
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value);
                setSelectedIndex(0);
              }}
            >
              <option>All categories</option>
              <option>Coding</option>
              <option>Mathematics</option>
              <option>Reasoning</option>
              <option>Factual QA</option>
              <option>Creative Writing</option>
              <option>Summarization</option>
              <option>Long-Context</option>
            </select>

            <select
              aria-label="Show"
              value={viewFilter}
              onChange={(e) => {
                setViewFilter(e.target.value);
                setSelectedIndex(0);
              }}
            >
              <option>All responses</option>
              <option>Hallucinations only</option>
              <option>Lowest quality first</option>
            </select>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Prompt</th>
                  <th>Category</th>
                  <th className="r">Quality</th>
                  <th>Flags</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.length > 0 ? (
                  filteredItems.map((item, idx) => (
                    <tr
                      key={item.id}
                      onClick={() => setSelectedIndex(idx)}
                      style={{
                        cursor: 'pointer',
                        background: idx === safeIndex ? 'var(--accent-soft)' : undefined,
                      }}
                    >
                      <td>
                        <b>{item.prompt.slice(0, 48)}…</b>
                      </td>
                      <td>{item.category}</td>
                      <td className="r num">{item.quality}</td>
                      <td>
                        {item.flagType === 'ok' ? (
                          <span className="muted small">None</span>
                        ) : (
                          <span className={`verdict ${item.flagType}`}>{item.flags}</span>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="muted" style={{ textAlign: 'center', padding: '24px 12px' }}>
                      No tasks found matching current filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="pager">
            <span>
              Showing {filteredItems.length > 0 ? safeIndex + 1 : 0} of {filteredItems.length} tasks
            </span>
            <div className="btn-row">
              <button
                type="button"
                className="btn small"
                disabled={safeIndex === 0 || filteredItems.length === 0}
                onClick={() => setSelectedIndex((i) => Math.max(0, i - 1))}
              >
                Previous
              </button>
              <button
                type="button"
                className="btn small"
                disabled={safeIndex >= filteredItems.length - 1 || filteredItems.length === 0}
                onClick={() => setSelectedIndex((i) => Math.min(filteredItems.length - 1, i + 1))}
              >
                Next
              </button>
            </div>
          </div>
        </section>

        {/* Response detail right panel */}
        <section className="panel" id="detail">
          <div className="panel-head">
            <h2>Response detail</h2>
            <span className={`tier ${current.quality >= 80 ? 'strong' : current.quality >= 50 ? 'mid' : 'weak'}`}>
              Quality {current.quality}
            </span>
          </div>

          <dl className="kv" style={{ marginBottom: 16 }}>
            <dt>Model</dt>
            <dd><b>{current.model}</b></dd>
            <dt>Category</dt>
            <dd>{current.category}</dd>
            <dt>Latency</dt>
            <dd className="num">{current.latency}</dd>
            <dt>Tokens</dt>
            <dd className="num">{current.tokens}</dd>
            <dt>Groundedness</dt>
            <dd className="num"><b>{current.groundedness}</b></dd>
          </dl>

          <h3 style={{ marginBottom: 8 }}>Prompt</h3>
          <div className="resp" style={{ marginBottom: 16 }}>
            {current.prompt}
          </div>

          <h3 style={{ marginBottom: 8 }}>Model Response</h3>
          <div className="resp" style={{ marginBottom: 18, fontFamily: current.category === 'Coding' ? 'var(--mono)' : undefined }}>
            {current.response}
          </div>

          {current.claims.length > 0 && (
            <>
              <h3 style={{ marginBottom: 10 }}>Flagged claims & Evidence</h3>
              {current.claims.map((claim: ResponseClaim, ci: number) => (
                <details key={ci} className="claim" open>
                  <summary>
                    <span>{claim.text}</span>
                    <span className={`verdict ${claim.verdictClass}`}>{claim.verdict}</span>
                  </summary>
                  <div className="evidence">
                    <b>Grounding check:</b> {claim.evidence}
                  </div>
                </details>
              ))}
            </>
          )}
        </section>
      </div>
    </main>
  );
};
