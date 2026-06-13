import React, { useState, useEffect } from 'react';
import './BackgroundPipelinePanel.css';

const API_BASE = window.deepfind?.baseUrl || 'http://127.0.0.1:8765';

/**
 * Panel to monitor and control the Background Automation Pipeline.
 * Shows status of Indexing, Extraction, Tagging, and Semantic phases.
 */
export default function BackgroundPipelinePanel() {
  const [pipelineState, setPipelineState] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Poll for status every 1s
  useEffect(() => {
    let intervalId;
    
    const fetchStatus = async () => {
      try {
        const res = await fetch(`${API_BASE}/pipeline/status`);
        if (!res.ok) throw new Error('Failed to fetch pipeline status');
        const data = await res.json();
        setPipelineState(data);
      } catch (err) {
        // Silently fail in polling
        console.error(err);
      }
    };
    
    fetchStatus();
    intervalId = setInterval(fetchStatus, 1000);
    return () => clearInterval(intervalId);
  }, []);

  const handleAction = async (action) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/pipeline/${action}`, { method: 'POST' });
      if (!res.ok) throw new Error(`Failed to ${action} pipeline`);
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAuto = async () => {
    if (!pipelineState) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/pipeline/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ auto_processing_enabled: !pipelineState.auto_processing_enabled })
      });
      if (!res.ok) throw new Error(`Failed to update settings`);
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!pipelineState) {
    return (
      <div className="pipeline-panel">
        <div className="pipeline-header">
          <h3>Automation Pipeline</h3>
          <span className="badge badge-gray">Connecting...</span>
        </div>
      </div>
    );
  }

  const { active, paused, current_stage, auto_processing_enabled, watcher_running, last_error, last_started_at, last_completed_at } = pipelineState;

  // Determine global badge
  let statusBadge = 'badge-gray';
  let statusText = 'Idle';
  if (active) {
    statusBadge = paused ? 'badge-yellow' : 'badge-green';
    statusText = paused ? 'Paused' : 'Running';
  } else if (current_stage === 'error') {
    statusBadge = 'badge-red';
    statusText = 'Error';
  }

  // Helper to format sub-stats
  const renderSubstats = () => {
    if (current_stage === 'idle') return <p className="substat">Pipeline is currently idle.</p>;
    
    if (current_stage === 'indexing') {
      const p = pipelineState.indexing;
      return <p className="substat">Added: {p.files_added} | Updated: {p.files_updated} | Errors: {p.errors}</p>;
    }
    if (current_stage === 'extraction') {
      const p = pipelineState.extraction;
      return <p className="substat">Extracted: {p.files_extracted} | Errors: {p.errors}</p>;
    }
    if (current_stage === 'tagging') {
      const p = pipelineState.tagging;
      return <p className="substat">Tagged: {p.files_tagged} | Errors: {p.errors}</p>;
    }
    if (current_stage === 'semantic') {
      const p = pipelineState.semantic;
      return <p className="substat">Chunks Embedded: {p.chunks_embedded} | Files Covered: {p.files_covered}</p>;
    }
    return <p className="substat">Preparing...</p>;
  };

  return (
    <div className="pipeline-panel">
      <div className="pipeline-header">
        <h3>Background Automation</h3>
        <span className={`badge ${statusBadge}`}>{statusText}</span>
      </div>

      <div className="pipeline-grid">
        <div className="pipeline-col">
          <p className="pipeline-stat">
            <span className="stat-label">Auto Processing:</span> 
            <span className={`stat-value ${auto_processing_enabled ? 'text-green' : 'text-gray'}`}>
              {auto_processing_enabled ? 'ON' : 'OFF'}
            </span>
          </p>
          <p className="pipeline-stat">
            <span className="stat-label">File Watcher:</span> 
            <span className={`stat-value ${watcher_running ? 'text-green' : 'text-gray'}`}>
              {watcher_running ? 'RUNNING' : 'STOPPED'}
            </span>
          </p>
          <p className="pipeline-stat">
            <span className="stat-label">Current Task:</span> 
            <span className="stat-value text-highlight">
              {current_stage.charAt(0).toUpperCase() + current_stage.slice(1)}
            </span>
          </p>
        </div>
      </div>

      <div className="pipeline-substats">
        {renderSubstats()}
      </div>

      {last_error && (
        <div className="pipeline-error">
          <strong>Error:</strong> {last_error}
        </div>
      )}

      <div className="pipeline-note">
        {auto_processing_enabled 
          ? "DeepFind automatically keeps your search index updated when files are added or changed."
          : "Automation is off. New files may not be fully searchable until you run processing manually."}
      </div>

      <div className="pipeline-actions main-actions">
        <button 
          className="btn btn-primary" 
          disabled={loading} 
          onClick={handleToggleAuto}
        >
          {auto_processing_enabled ? 'Turn Off Automation' : 'Turn On Automation'}
        </button>
      </div>

      <div className="advanced-controls-wrapper">
        <button 
          className="btn-text btn-advanced-toggle" 
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          {showAdvanced ? '▼ Hide Advanced Controls' : '▶ Show Advanced Controls'}
        </button>
        
        {showAdvanced && (
          <div className="advanced-controls-panel">
            <div className="pipeline-actions">
              <button 
                className="btn btn-outline" 
                disabled={loading || active} 
                onClick={() => handleAction('start')}
              >
                Run Now
              </button>
              {active && !paused && (
                <button className="btn btn-secondary" disabled={loading} onClick={() => handleAction('pause')}>
                  Pause Current Job
                </button>
              )}
              {active && paused && (
                <button className="btn btn-secondary" disabled={loading} onClick={() => handleAction('resume')}>
                  Resume
                </button>
              )}
              <button 
                className="btn btn-danger" 
                disabled={loading || !active} 
                onClick={() => handleAction('stop')}
              >
                Stop Current Job
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
