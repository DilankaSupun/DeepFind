import React from 'react';
import PageHeader from '../shell/PageHeader.jsx';
import ResourceMonitor from '../ResourceMonitor/ResourceMonitor.jsx';
import ErrorBoundary from '../ErrorBoundary/ErrorBoundary.jsx';

export default function SystemPage() {
  return (
    <>
      <PageHeader 
        title="System usage" 
        description="Monitor local storage and processing resources." 
      />
      <div className="page-content page-content-constrained" style={{ paddingTop: 'var(--df-space-4)' }}>
        <div style={{ background: 'var(--df-bg-surface-1)', border: '1px solid var(--df-border-default)', borderRadius: 'var(--df-radius-card)', padding: 'var(--df-space-5)' }}>
          <ErrorBoundary>
            <ResourceMonitor />
          </ErrorBoundary>
        </div>
      </div>
    </>
  );
}
