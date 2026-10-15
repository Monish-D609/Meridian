import React from 'react';

export type NavTab = 'new-run' | 'results' | 'responses' | 'history' | 'settings';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  activeRunName?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab }) => {
  const [theme, setTheme] = React.useState<'light' | 'dark'>(() => {
    try {
      const saved = localStorage.getItem('meridian_theme');
      if (saved === 'dark' || saved === 'light') return saved;
      return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
    } catch {
      return 'light';
    }
  });

  React.useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    document.body.setAttribute('data-theme', theme);
    try {
      localStorage.setItem('meridian_theme', theme);
    } catch {
      // ignore
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  return (
    <aside className="side">
      <div className="brand" onClick={() => onSelectTab('new-run')}>
        <span className="brand-mark" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M3 14V9M7 14V4M11 14V7M15 14V11" stroke="#fff" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </span>
        <span>
          <b>Benchmark Lab</b>
          <span>LLM evaluation</span>
        </span>
      </div>

      <nav className="nav" aria-label="Main">
        <button
          type="button"
          aria-current={currentTab === 'new-run' ? 'page' : undefined}
          onClick={() => onSelectTab('new-run')}
        >
          New run
        </button>
        <button
          type="button"
          aria-current={currentTab === 'results' ? 'page' : undefined}
          onClick={() => onSelectTab('results')}
        >
          Results
        </button>
        <button
          type="button"
          aria-current={currentTab === 'responses' ? 'page' : undefined}
          onClick={() => onSelectTab('responses')}
        >
          Responses
        </button>
        <button
          type="button"
          aria-current={currentTab === 'history' ? 'page' : undefined}
          onClick={() => onSelectTab('history')}
        >
          Run history
        </button>
        <button
          type="button"
          aria-current={currentTab === 'settings' ? 'page' : undefined}
          onClick={() => onSelectTab('settings')}
        >
          Settings
        </button>
      </nav>

      <div className="side-foot">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <span style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Appearance</span>
          <button
            type="button"
            className="btn small"
            onClick={toggleTheme}
            style={{ padding: '2px 8px', fontSize: 11, cursor: 'pointer' }}
          >
            {theme === 'dark' ? '☀ Light' : '☾ Dark'}
          </button>
        </div>
        <b>Baseline set v2026.09</b>
        <br />
        Captured 20 Sep 2026. Every tier is relative to this version.
      </div>
    </aside>
  );
};
