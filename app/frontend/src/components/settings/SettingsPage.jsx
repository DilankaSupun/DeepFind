import React from 'react';
import PageHeader from '../shell/PageHeader.jsx';
import ResetPanel from '../ResetPanel/ResetPanel.jsx';
import ErrorBoundary from '../ErrorBoundary/ErrorBoundary.jsx';

export default function SettingsPage() {
  const handleClear = () => {
    // Optionally trigger a refresh or notification
    console.log('Index cleared from Settings');
  };

  return (
    <>
      <PageHeader 
        title="Settings" 
        description="Control automation, exclusions, and application data." 
      />
      <div className="page-content page-content-constrained" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--df-space-6)', paddingTop: 'var(--df-space-4)' }}>
        
        <div style={{ background: 'var(--df-bg-surface-1)', border: '1px solid var(--df-border-default)', borderRadius: 'var(--df-radius-card)', padding: 'var(--df-space-5)' }}>
          <h2 style={{ fontSize: 'var(--df-type-section-title)', fontWeight: 600, margin: '0 0 var(--df-space-4) 0' }}>About DeepFind</h2>
          <div style={{ fontSize: 'var(--df-type-body)', color: 'var(--df-text-secondary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <p><strong style={{ color: 'var(--df-text-primary)' }}>DeepFind</strong> version 0.1.0</p>
            <p>Local-first · No cloud uploads</p>
          </div>
        </div>

        <div style={{ background: 'rgba(239, 115, 125, 0.05)', border: '1px solid var(--df-danger-subtle)', borderRadius: 'var(--df-radius-card)', padding: 'var(--df-space-5)' }}>
          <h2 style={{ fontSize: 'var(--df-type-section-title)', fontWeight: 600, color: 'var(--df-danger)', margin: '0 0 var(--df-space-4) 0' }}>Danger Zone</h2>
          <ErrorBoundary>
            <ResetPanel onResetSuccess={handleClear} />
          </ErrorBoundary>
        </div>

      </div>
    </>
  );
}
