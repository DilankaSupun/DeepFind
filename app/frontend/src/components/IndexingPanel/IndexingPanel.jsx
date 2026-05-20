import React, { useState, useEffect, useCallback, useRef } from 'react';
import { startIndexing, getIndexStatus, getIndexSummary } from '../../services/api.js';
import './IndexingPanel.css';

const POLL_MS = 2000; // poll every 2s while running

function IndexingPanel({ engineStatus }) {
  const [status,    setStatus]  = useState(null);   // live scan state
  const [summary,   setSummary] = useState(null);   // DB summary
  const [starting,  setStarting] = useState(false);
  const [error,     setError]   = useState(null);
  const pollRef = useRef(null);

  const isOffline = engineStatus !== 'online';

  // ── Fetch summary ────────────────────────────────────────────────────────
  const loadSummary = useCallback(async () => {
    if (isOffline) return;
    try { const d = await getIndexSummary(); setSummary(d); } catch { /* silent */ }
  }, [isOffline]);

  // ── Fetch live status ────────────────────────────────────────────────────
  const fetchStatus = useCallback(async () => {
    try {
      const d = await getIndexStatus();
      setStatus(d);
      if (!d.active) {
        clearInterval(pollRef.current);
        pollRef.current = null;
        loadSummary(); // refresh totals after scan
      }
    } catch { /* silent */ }
  }, [loadSummary]);

  // ── Start polling ────────────────────────────────────────────────────────
  const startPolling = useCallback(() => {
    if (pollRef.current) return;
    pollRef.current = setInterval(fetchStatus, POLL_MS);
  }, [fetchStatus]);

  // On mount: load initial status + summary
  useEffect(() => {
    if (isOffline) return;
    fetchStatus();
    loadSummary();
    return () => clearInterval(pollRef.current);
  }, [isOffline, fetchStatus, loadSummary]);

  // Auto-poll if status comes back as running on mount
  useEffect(() => {
    if (status?.active) startPolling();
  }, [status?.active, startPolling]);

  // ── Start indexing ───────────────────────────────────────────────────────
  const handleStart = async () => {
    if (starting) return;
    setStarting(true);
    setError(null);
    try {
      await startIndexing();
      await fetchStatus();
      startPolling();
    } catch (e) {
      setError('Failed to start: ' + e.message);
    } finally {
      setStarting(false);
    }
  };

  // ── Derived state ────────────────────────────────────────────────────────
  const scanStatus  = status?.status ?? 'idle';
  const isRunning   = status?.active === true;
  const isCompleted = scanStatus === 'completed';
  const isError     = scanStatus === 'error';
  const hasScanned  = status && status.files_scanned > 0;

  return (
    <section className="indexing-panel" aria-label="File indexing">

      {/* Header */}
      <div className="indexing-panel__header">
        <div className="indexing-panel__title-row">
          <ScanIcon />
          <h2 className="indexing-panel__title">File Index</h2>
          {summary?.total_files > 0 && (
            <span className="indexing-panel__total">
              {summary.total_files.toLocaleString()} files
            </span>
          )}
        </div>

        <button
          className={`ip-start-btn ${isRunning ? 'ip-start-btn--running' : ''}`}
          onClick={handleStart}
          disabled={isRunning || starting || isOffline}
          title={isOffline ? 'Start the engine first' : ''}
        >
          {isRunning ? (
            <><Spinner /> Scanning…</>
          ) : starting ? (
            <><Spinner /> Starting…</>
          ) : (
            <><PlayIcon /> Start Indexing</>
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="ip-error" role="alert">
          <AlertIcon /><span>{error}</span>
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      {/* Offline */}
      {isOffline && (
        <div className="ip-idle-msg">Start the engine to begin indexing</div>
      )}

      {/* Status bar */}
      {!isOffline && (
        <div className={`ip-status-bar ip-status-bar--${scanStatus}`}>
          <span className="ip-status-dot" />
          <span className="ip-status-label">{STATUS_LABELS[scanStatus] ?? scanStatus}</span>
          {isRunning && status?.current_path && (
            <span className="ip-current-path" title={status.current_path}>
              {truncatePath(status.current_path)}
            </span>
          )}
        </div>
      )}

      {/* Progress grid */}
      {!isOffline && (hasScanned || isCompleted) && (
        <div className="ip-stats">
          <StatBox label="Scanned" value={status?.files_scanned ?? 0} icon={<FolderIcon />} />
          <StatBox label="Added"   value={status?.files_added   ?? 0} icon={<PlusCircleIcon />} accent="green" />
          <StatBox label="Updated" value={status?.files_updated ?? 0} icon={<RefreshIcon />}    accent="blue" />
          <StatBox label="Skipped" value={status?.files_skipped ?? 0} icon={<SkipIcon />} />
          {(status?.errors ?? 0) > 0 && (
            <StatBox label="Errors" value={status.errors} icon={<AlertIcon />} accent="red" />
          )}
        </div>
      )}

      {/* Summary after completion */}
      {!isOffline && isCompleted && summary && (
        <div className="ip-summary">
          <CheckIcon />
          <span>
            Index complete —{' '}
            <strong>{(summary.metadata_indexed ?? 0).toLocaleString()}</strong> files indexed
            {summary.missing > 0 && <>, <strong>{summary.missing}</strong> missing</>}
          </span>
        </div>
      )}

      {/* Idle hint */}
      {!isOffline && scanStatus === 'idle' && !starting && (
        <p className="ip-hint">
          Click <strong>Start Indexing</strong> to scan your active folders and build the file index.
        </p>
      )}
    </section>
  );
}

const STATUS_LABELS = {
  idle:      'Idle',
  running:   'Scanning files…',
  completed: 'Completed',
  error:     'Error',
};

function truncatePath(p) {
  if (!p) return '';
  const max = 60;
  return p.length > max ? '…' + p.slice(p.length - max) : p;
}

function StatBox({ label, value, icon, accent }) {
  return (
    <div className={`ip-stat ip-stat--${accent ?? 'default'}`}>
      <span className="ip-stat__icon">{icon}</span>
      <span className="ip-stat__value">{value.toLocaleString()}</span>
      <span className="ip-stat__label">{label}</span>
    </div>
  );
}

/* Icons */
function Spinner()       { return <span className="ip-spinner" aria-hidden="true"/>; }
function ScanIcon()      { return <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><rect x="7" y="7" width="10" height="10" rx="1"/></svg>; }
function PlayIcon()      { return <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>; }
function FolderIcon()    { return <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>; }
function PlusCircleIcon(){ return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>; }
function RefreshIcon()   { return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>; }
function SkipIcon()      { return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>; }
function CheckIcon()     { return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>; }
function AlertIcon()     { return <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>; }

export default IndexingPanel;
