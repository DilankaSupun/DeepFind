import React, { useState, useEffect } from 'react';
import { buildSemanticIndex, getSemanticStatus, getSemanticSummary } from '../../services/api';
import './SemanticPanel.css';

function BrainIcon() {
  return (
    <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 2C8.686 2 6 4.686 6 8c0 1.071.277 2.077.766 2.946L5 15l2 2 3.553-1.776A5.96 5.96 0 0012 18c3.314 0 6-2.686 6-6S15.314 2 12 2z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 10h.01M15 10h.01M12 14v.01" />
    </svg>
  );
}

function BuildIcon() {
  return (
    <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  );
}

export default function SemanticPanel({ engineStatus }) {
  const [summary, setSummary] = useState(null);
  const [statusData, setStatusData] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState(null);

  const fetchSummary = async () => {
    if (engineStatus !== 'online') return;
    try {
      const data = await getSemanticSummary();
      setSummary(data);
    } catch (err) {
      console.error("Failed to fetch semantic summary:", err);
    }
  };

  const pollStatus = async () => {
    if (engineStatus !== 'online') return;
    try {
      const data = await getSemanticStatus();
      setStatusData(data);
      if (data.active) {
        setIsRunning(true);
      } else {
        if (isRunning) {
          setIsRunning(false);
          fetchSummary();
        }
      }
    } catch (err) {
      console.error("Failed to poll semantic status:", err);
    }
  };

  useEffect(() => {
    fetchSummary();
    const interval = setInterval(() => {
      pollStatus();
    }, 1500);
    return () => clearInterval(interval);
  }, [engineStatus, isRunning]);

  const handleBuild = async () => {
    try {
      setError(null);
      await buildSemanticIndex();
      setIsRunning(true);
    } catch (err) {
      setError(err.message);
    }
  };

  const isOffline = engineStatus !== 'online';

  return (
    <section className="semantic-panel" aria-labelledby="semantic-heading">
      <header className="semantic-header">
        <div className="semantic-header-title">
          <BrainIcon />
          <h2 id="semantic-heading">Semantic Search</h2>
        </div>
        
        <button 
          className={`semantic-build-btn ${isRunning ? 'running' : ''}`}
          onClick={handleBuild}
          disabled={isOffline || isRunning}
        >
          {isRunning ? (
            <>
              <span className="spinner-icon"></span>
              Building...
            </>
          ) : (
            <>
              <BuildIcon />
              Build Semantic Index
            </>
          )}
        </button>
      </header>
      
      {error && <div className="semantic-error">{error}</div>}

      <div className="semantic-body">
        {isRunning && statusData ? (
          <div className="semantic-progress">
            <p className="semantic-progress-title">Building Local Semantic Index...</p>
            <p className="semantic-progress-subtitle">First run may take a few minutes to download the AI model locally.</p>
            <div className="semantic-stats-grid">
              <div className="stat-card">
                <div className="stat-value">{statusData.chunks_embedded}</div>
                <div className="stat-label">Chunks Embedded</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{statusData.files_covered}</div>
                <div className="stat-label">Files Covered</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{statusData.errors}</div>
                <div className="stat-label">Errors</div>
              </div>
            </div>
          </div>
        ) : (
          <div className="semantic-summary">
            <div className="semantic-stats-grid">
              <div className="stat-card">
                <div className="stat-value">{summary?.vectors?.toLocaleString() || 0}</div>
                <div className="stat-label">Vectors in FAISS</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{summary?.files_covered?.toLocaleString() || 0}</div>
                <div className="stat-label">Files Embedded</div>
              </div>
              <div className="stat-card">
                <div className="stat-value model-name">{summary?.model || 'all-MiniLM-L6-v2'}</div>
                <div className="stat-label">Local Model</div>
              </div>
            </div>
          </div>
        )}
      </div>

      <footer className="semantic-footer">
        Semantic search runs locally on your machine. File content and queries are <strong>never uploaded</strong>.
      </footer>
    </section>
  );
}
