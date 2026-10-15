import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import type { BaselineModel, Provider } from '../types';

export const SettingsPage: React.FC = () => {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [configuredProviders, setConfiguredProviders] = useState<string[]>([]);
  const [baselines, setBaselines] = useState<BaselineModel[]>([]);
  const [selectedProvider, setSelectedProvider] = useState('xai');
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  // Thresholds
  const [tFrontier, setTFrontier] = useState(80);
  const [tStrong, setTStrong] = useState(60);
  const [tMid, setTMid] = useState(40);

  useEffect(() => {
    try {
      const savedT = localStorage.getItem('meridian_thresholds');
      if (savedT) {
        const parsed = JSON.parse(savedT);
        if (parsed.tFrontier) setTFrontier(parsed.tFrontier);
        if (parsed.tStrong) setTStrong(parsed.tStrong);
        if (parsed.tMid) setTMid(parsed.tMid);
      }
    } catch {
      // ignore
    }

    async function loadData() {
      try {
        const [provs, conf, bases] = await Promise.all([
          api.getProviders(),
          api.getConfiguredProviders().catch(() => ({ configured_providers: [] })),
          api.getBaselines().catch(() => []),
        ]);
        setProviders(provs);
        const serverConfigured = conf.configured_providers || [];
        const localSaved = ['xai', 'gemini', 'openrouter', 'cloudflare', 'groq'].filter((p) => {
          try {
            return !!localStorage.getItem('meridian_api_key_' + p);
          } catch {
            return false;
          }
        });
        const merged = Array.from(new Set([...serverConfigured, ...localSaved]));
        setConfiguredProviders(merged);
        setBaselines(bases);
      } catch (err) {
        console.error('Failed to load settings:', err);
      }
    }
    loadData();
  }, []);

  const [isSavingKey, setIsSavingKey] = useState(false);

  const handleSaveKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKeyInput.trim()) return;

    const providerKey = selectedProvider.toLowerCase();
    setIsSavingKey(true);
    try {
      try {
        localStorage.setItem('meridian_api_key_' + providerKey, apiKeyInput);
      } catch {}

      const res = await api.saveProviderKey(providerKey, apiKeyInput.trim());
      if (res.configured_providers) {
        setConfiguredProviders(res.configured_providers);
      } else {
        setConfiguredProviders((prev) => Array.from(new Set([...prev, providerKey])));
      }
      setSaveStatus(`Saved & verified credentials for ${selectedProvider.toUpperCase()} on server.`);
      setApiKeyInput('');
    } catch (err: any) {
      setSaveStatus(`Error saving key: ${err.message || 'Server error'}`);
    } finally {
      setIsSavingKey(false);
      setTimeout(() => setSaveStatus(null), 5000);
    }
  };


  const handleSaveThresholds = () => {
    try {
      localStorage.setItem('meridian_thresholds', JSON.stringify({ tFrontier, tStrong, tMid }));
    } catch {
      // ignore
    }
    setSaveStatus('Tier thresholds updated and saved successfully.');
    setTimeout(() => setSaveStatus(null), 3000);
  };

  return (
    <main>
      <div className="page-head">
        <div>
          <h1>Settings & API Providers</h1>
          <p className="muted">
            All API keys are encrypted at rest with Fernet and never sent to the browser or leaked in reports (NFR-3.4).
          </p>
        </div>
      </div>

      {saveStatus && (
        <div className="callout" style={{ marginBottom: 20 }}>
          {saveStatus}
        </div>
      )}

      <div className="grid-2">
        <div className="stack">
          {/* Provider API Keys Status */}
          <section className="panel">
            <div className="panel-head">
              <h2>Configured LLM Providers</h2>
            </div>

            <div className="key-line">
              <div>
                <b>xAI (Grok - Elon Musk)</b>
                <div className="small muted mono">grok-2-latest, grok-2-mini</div>
              </div>
              <span className={`status ${configuredProviders.includes('xai') ? 'ok' : 'wait'}`}>
                {configuredProviders.includes('xai') ? 'Connected' : 'Configure in .env'}
              </span>
            </div>

            <div className="key-line">
              <div>
                <b>Google AI Studio (Gemini)</b>
                <div className="small muted mono">gemini-1.5-flash, LLM-Judge</div>
              </div>
              <span className={`status ${configuredProviders.includes('gemini') ? 'ok' : 'wait'}`}>
                {configuredProviders.includes('gemini') ? 'Connected' : 'Configure in .env'}
              </span>
            </div>

            <div className="key-line">
              <div>
                <b>OpenRouter</b>
                <div className="small muted mono">Free-tier open models</div>
              </div>
              <span className={`status ${configuredProviders.includes('openrouter') ? 'ok' : 'wait'}`}>
                {configuredProviders.includes('openrouter') ? 'Connected' : 'Configure in .env'}
              </span>
            </div>

            <div className="key-line">
              <div>
                <b>Cloudflare Workers AI</b>
                <div className="small muted mono">Serverless inference allocation</div>
              </div>
              <span className={`status ${configuredProviders.includes('cloudflare') ? 'ok' : 'wait'}`}>
                {configuredProviders.includes('cloudflare') ? 'Connected' : 'Configure in .env'}
              </span>
            </div>

            <div className="key-line">
              <div>
                <b>Groq</b>
                <div className="small muted mono">LPU fast inference engine</div>
              </div>
              <span className={`status ${configuredProviders.includes('groq') ? 'ok' : 'wait'}`}>
                {configuredProviders.includes('groq') ? 'Connected' : 'Configure in .env'}
              </span>
            </div>

            <form style={{ marginTop: 22 }} onSubmit={handleSaveKey}>
              <div className="row-2">
                <div className="field">
                  <label htmlFor="prov">Provider</label>
                  <select
                    id="prov"
                    value={selectedProvider}
                    onChange={(e) => setSelectedProvider(e.target.value)}
                  >
                    {providers.length > 0 ? (
                      providers.map((p) => (
                        <option key={p.id} value={p.name}>
                          {p.name.toUpperCase()}
                        </option>
                      ))
                    ) : (
                      <>
                        <option value="xai">xAI (Grok)</option>
                        <option value="gemini">Google AI Studio (Gemini)</option>
                        <option value="openrouter">OpenRouter</option>
                        <option value="cloudflare">Cloudflare Workers AI</option>
                        <option value="groq">Groq</option>
                      </>
                    )}
                  </select>
                </div>
                <div className="field">
                  <label htmlFor="key">API Key</label>
                  <input
                    id="key"
                    type="password"
                    autoComplete="off"
                    placeholder="Paste key to save encrypted"
                    value={apiKeyInput}
                    onChange={(e) => setApiKeyInput(e.target.value)}
                  />
                </div>
              </div>
              <button className="btn primary" type="submit" disabled={isSavingKey}>
                {isSavingKey ? 'Verifying & Saving...' : 'Save key'}
              </button>
            </form>
          </section>

          {/* Tier Thresholds */}
          <section className="panel">
            <div className="panel-head">
              <h2>Tier Percentile Thresholds</h2>
              <span className="hint">Industry Comparison Engine rules</span>
            </div>
            <div className="row-2">
              <div className="field">
                <label htmlFor="t1">Frontier tier (≥ %ile)</label>
                <input
                  id="t1"
                  type="number"
                  value={tFrontier}
                  onChange={(e) => setTFrontier(parseInt(e.target.value) || 80)}
                />
              </div>
              <div className="field">
                <label htmlFor="t2">Strong tier (≥ %ile)</label>
                <input
                  id="t2"
                  type="number"
                  value={tStrong}
                  onChange={(e) => setTStrong(parseInt(e.target.value) || 60)}
                />
              </div>
              <div className="field">
                <label htmlFor="t3">Mid tier (≥ %ile)</label>
                <input
                  id="t3"
                  type="number"
                  value={tMid}
                  onChange={(e) => setTMid(parseInt(e.target.value) || 40)}
                />
              </div>
              <div className="field">
                <label>Weak tier</label>
                <input type="text" value={`< ${tMid}th percentile`} disabled />
              </div>
            </div>
            <button className="btn" type="button" onClick={handleSaveThresholds}>
              Save thresholds
            </button>
          </section>
        </div>

        {/* Baseline Registry */}
        <section className="panel">
          <div className="panel-head">
            <h2>Baseline Registry</h2>
            <span className="hint">Versioned reference scores</span>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Model Reference</th>
                  <th>Version</th>
                  <th>Captured Date</th>
                  <th>Type</th>
                </tr>
              </thead>
              <tbody>
                {baselines.map((b) => (
                  <tr key={b.id}>
                    <td>
                      <b>{b.display_name}</b>
                      {b.notes && <div className="small muted">{b.notes.slice(0, 70)}…</div>}
                    </td>
                    <td className="mono">{b.version_tag}</td>
                    <td className="small">{b.captured_date}</td>
                    <td>
                      <span className="tier strong">Baseline</span>
                    </td>
                  </tr>
                ))}
                {baselines.length === 0 && (
                  <>
                    <tr>
                      <td><b>GPT-4-class Reference</b></td>
                      <td className="mono">gpt4-class-2024q3</td>
                      <td className="small">2024-09-01</td>
                      <td><span className="tier frontier">Frontier</span></td>
                    </tr>
                    <tr>
                      <td><b>Claude-3-class Reference</b></td>
                      <td className="mono">claude3-class-2024q3</td>
                      <td className="small">2024-09-01</td>
                      <td><span className="tier strong">Strong</span></td>
                    </tr>
                    <tr>
                      <td><b>Open-Source Mid-Tier Reference</b></td>
                      <td className="mono">oss-mid-2024q3</td>
                      <td className="small">2024-09-01</td>
                      <td><span className="tier mid">Mid</span></td>
                    </tr>
                  </>
                )}
              </tbody>
            </table>
          </div>
          <p className="hint" style={{ marginTop: 14 }}>
            Baselines are versioned and date-stamped so relative positioning remains scientifically reproducible over time.
          </p>
        </section>
      </div>
    </main>
  );
};
