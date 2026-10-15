import React, { useState } from 'react';
import { Sidebar, type NavTab } from './components/Sidebar';
import { NewRunPage } from './pages/NewRunPage';
import { ResultsPage } from './pages/ResultsPage';
import { ResponsesPage } from './pages/ResponsesPage';
import { HistoryPage } from './pages/HistoryPage';
import { SettingsPage } from './pages/SettingsPage';
import type { BenchmarkRun } from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('new-run');
  const [activeRunId, setActiveRunId] = useState<string | undefined>(undefined);
  const [activeModelId, setActiveModelId] = useState<string | undefined>(undefined);

  const handleRunStarted = (run: BenchmarkRun) => {
    setActiveRunId(run.id);
  };

  const handleNavigateToResults = (runId: string) => {
    setActiveRunId(runId);
    setCurrentTab('results');
  };

  const handleNavigateToResponses = (runId: string, modelId?: string) => {
    setActiveRunId(runId);
    setActiveModelId(modelId);
    setCurrentTab('responses');
  };

  return (
    <>
      <Sidebar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
      />

      {currentTab === 'new-run' && (
        <NewRunPage
          onRunStarted={handleRunStarted}
          onNavigateToResults={handleNavigateToResults}
        />
      )}

      {currentTab === 'results' && (
        <ResultsPage
          runId={activeRunId}
          onSelectRun={(id) => setActiveRunId(id)}
          onNavigateToResponses={handleNavigateToResponses}
        />
      )}

      {currentTab === 'responses' && (
        <ResponsesPage
          initialRunId={activeRunId}
          initialModelId={activeModelId}
        />
      )}

      {currentTab === 'history' && (
        <HistoryPage
          onSelectRun={handleNavigateToResults}
          onNavigateToNewRun={() => setCurrentTab('new-run')}
        />
      )}

      {currentTab === 'settings' && <SettingsPage />}
    </>
  );
};

export default App;
