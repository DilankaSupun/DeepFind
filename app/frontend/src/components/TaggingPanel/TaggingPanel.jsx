import React, { useState, useEffect, useRef } from 'react';
import { startTagging, getTagStatus, getTagSummary } from '../../services/api';
import './TaggingPanel.css';

/**
 * TaggingPanel — Step 11
 *
 * Background worker UI for automatic file tagging.
 * Polls status during active tagging, and displays summary stats.
 */
function TaggingPanel({ engineStatus }) {
  // ── State ────────────────────────────────────────────────────────
  const [tagState, setTagState] = useState({
    status: 'idle',
    active: false,
    files_checked: 0,
    files_tagged: 0,
    files_skipped: 0,
    errors: 0,
    current_path: '',
    error_message: '',
  });

  const [summary, setSummary] = useState({
    files_with_tags: 0,
    unique_tags: 0,
    top_tags: [],
  });

  const [loadingAction, setLoadingAction] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const timerRef = useRef(null);

  // ── Poll Status ──────────────────────────────────────────────────
  const checkStatus = async () => {
    if (engineStatus !== 'online') return;
    try {
      const data = await getTagStatus();
      setTagState(data);
      if (data.active) {
        startPolling();
      } else {
        stopPolling();
        if (data.status === 'completed' || data.status === 'error') {
          fetchSummary();
        }
      }
    } catch (err) {
      console.error('Failed to get tagging status:', err);
      stopPolling();
    }
  };

  const fetchSummary = async () => {
    if (engineStatus !== 'online') return;
    try {
      const data = await getTagSummary();
      setSummary(data);
    } catch (err) {
      console.error('Failed to fetch tagging summary:', err);
    }
  };

  const startPolling = () => {
    if (timerRef.current) return;
    timerRef.current = setInterval(checkStatus, 1500);
  };

  const stopPolling = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  // Initial load
  useEffect(() => {
    if (engineStatus === 'online') {
      checkStatus();
      fetchSummary();
    } else {
      stopPolling();
    }
    return stopPolling;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [engineStatus]);

  // ── Actions ──────────────────────────────────────────────────────
  const handleStart = async (force = false) => {
    setLoadingAction(true);
    setErrorMsg(null);
    try {
      const res = await startTagging(force);
      if (res.status === 'already_running') {
        checkStatus();
      } else {
        // Optimistic UI update
        setTagState((prev) => ({
          ...prev,
          status: 'running',
          active: true,
          files_checked: 0,
          files_tagged: 0,
          files_skipped: 0,
          errors: 0,
          error_message: '',
        }));
        startPolling();
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to start tagging');
    } finally {
      setLoadingAction(false);
    }
  };

  // ── Render Helpers ───────────────────────────────────────────────
  const { status, active, files_checked, files_tagged, files_skipped, errors, current_path, error_message } = tagState;
  const isOnline = engineStatus === 'online';
  const disableBtns = !isOnline || active || loadingAction;

  return (
    <section className="tag-panel" aria-label="Auto-Tagging">
      <header className="tag-header">
        <div className="tag-header__title-group">
          <TagIcon />
          <h2>Auto-Tagging</h2>
          <span className="tag-badge">Step 11</span>
        </div>
        <p className="tag-desc">
          Generate lightweight tags from filenames, paths, and extracted content.
        </p>
      </header>

      {errorMsg && (
        <div className="tag-alert tag-alert--error">
          <span className="tag-alert__icon" aria-hidden="true">⚠️</span>
          {errorMsg}
        </div>
      )}

      {status === 'error' && error_message && !active && (
        <div className="tag-alert tag-alert--error">
          <span className="tag-alert__icon" aria-hidden="true">⚠️</span>
          <strong>Tagging failed:</strong> {error_message}
        </div>
      )}

      {status === 'completed' && !active && (
        <div className="tag-alert tag-alert--success">
          <span className="tag-alert__icon" aria-hidden="true">✓</span>
          Tag generation complete.
        </div>
      )}

      <div className="tag-content">
        {/* Left Col: Controls & Live Progress */}
        <div className="tag-col tag-col--main">
          
          <div className="tag-controls">
            <button
              className="tag-btn tag-btn--primary"
              onClick={() => handleStart(false)}
              disabled={disableBtns}
            >
              {active ? 'Tagging in progress…' : 'Generate Tags'}
            </button>
            <button
              className="tag-btn tag-btn--secondary"
              onClick={() => handleStart(true)}
              disabled={disableBtns}
              title="Force regenerate tags for all files"
            >
              Force Re-tag All
            </button>
          </div>

          <div className="tag-progress-box">
            <h3 className="tag-progress-title">
              Live Progress
              {active && <span className="tag-pulse" title="Running" />}
            </h3>

            <div className="tag-stats-grid">
              <div className="tag-stat-item">
                <span className="tag-stat-label">Checked</span>
                <span className="tag-stat-val">{files_checked.toLocaleString()}</span>
              </div>
              <div className="tag-stat-item">
                <span className="tag-stat-label">Tagged</span>
                <span className="tag-stat-val val--success">{files_tagged.toLocaleString()}</span>
              </div>
              <div className="tag-stat-item">
                <span className="tag-stat-label">Skipped</span>
                <span className="tag-stat-val val--muted">{files_skipped.toLocaleString()}</span>
              </div>
              <div className="tag-stat-item">
                <span className="tag-stat-label">Errors</span>
                <span className={`tag-stat-val ${errors > 0 ? 'val--error' : ''}`}>{errors.toLocaleString()}</span>
              </div>
            </div>

            <div className="tag-current-path">
              {active ? (
                <>
                  <span className="tag-path-label">Processing:</span>
                  <span className="tag-path-val" title={current_path}>
                    {current_path || 'Starting…'}
                  </span>
                </>
              ) : (
                <span className="tag-path-idle">Worker idle</span>
              )}
            </div>
          </div>
        </div>

        {/* Right Col: DB Summary */}
        <div className="tag-col tag-col--side">
          <div className="tag-summary-box">
            <h3 className="tag-summary-title">Tag Database</h3>
            
            <div className="tag-db-stats">
              <div className="db-stat">
                <span className="db-stat__val">{summary.files_with_tags.toLocaleString()}</span>
                <span className="db-stat__label">Tagged Files</span>
              </div>
              <div className="db-stat">
                <span className="db-stat__val">{summary.unique_tags.toLocaleString()}</span>
                <span className="db-stat__label">Unique Tags</span>
              </div>
            </div>

            <div className="tag-top-list">
              <span className="top-list-label">Top Tags</span>
              {summary.top_tags.length === 0 ? (
                <div className="top-list-empty">No tags generated yet</div>
              ) : (
                <ul className="top-tags">
                  {summary.top_tags.map(t => (
                    <li key={t.tag} className="top-tag-item">
                      <span className="top-tag-name">{t.tag}</span>
                      <span className="top-tag-count">{t.count}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ── Icons ──────────────────────────────────────────────────────── */

function TagIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="url(#tagGrad)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <defs>
        <linearGradient id="tagGrad" x1="0" y1="0" x2="24" y2="24">
          <stop stopColor="#a855f7" />
          <stop offset="1" stopColor="#ec4899" />
        </linearGradient>
      </defs>
      <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z" />
      <line x1="7" y1="7" x2="7.01" y2="7" />
    </svg>
  );
}

export default TaggingPanel;
