import React from 'react';
import PageHeader from '../shell/PageHeader.jsx';
import WatcherPanel from '../WatcherPanel/WatcherPanel.jsx';
import BackgroundPipelinePanel from '../BackgroundPipelinePanel/BackgroundPipelinePanel.jsx';
import ErrorBoundary from '../ErrorBoundary/ErrorBoundary.jsx';

export default function ActivityPage() {
  return (
    <>
      <PageHeader 
        title="Background activity" 
        description="See how DeepFind keeps your local search index updated." 
      />
      <div className="page-content page-content-constrained" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--df-space-6)', paddingTop: 'var(--df-space-4)' }}>
        
        <div style={{ background: 'var(--df-bg-surface-1)', border: '1px solid var(--df-border-default)', borderRadius: 'var(--df-radius-card)', padding: 'var(--df-space-5)' }}>
          <WatcherPanel />
        </div>

        <div style={{ background: 'var(--df-bg-surface-1)', border: '1px solid var(--df-border-default)', borderRadius: 'var(--df-radius-card)', padding: 'var(--df-space-5)' }}>
          <ErrorBoundary>
            <BackgroundPipelinePanel />
          </ErrorBoundary>
        </div>

      </div>
    </>
  );
}
