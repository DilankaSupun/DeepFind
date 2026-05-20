import React, { useState, useEffect, useCallback, useRef } from 'react';
import { startExtraction, getExtractStatus, getExtractSummary } from '../../services/api.js';
import './ExtractionPanel.css';

const POLL_MS = 2000; // poll every 2s while running

/**
 * ExtractionPanel — Step 9
 *
 * UI for triggering and monitoring text content extraction.
 * Mirrors IndexingPanel's patterns.
 *
 * Props:
 *   engineStatus — 'online' | 'offline' | 'checking'
 */
function ExtractionPanel({ engineStatus }) {
  const [status,   setStatus]   = useState(null);  // live extraction state
  const [summary,  setSummary]  = useState(null);  // DB summary
  const [starting, setStarting] = useState(false);
  const [error,    setError]    = useState(null);
  const pollRef = useRef(null);

  const isOffline = engineStatus !== 'online';

  // ── Fetch summary ─────────────────────────────────────────────────────────
  const loadSummary = useCallback(async () => {
    if (isOffline) return;
    try { const d = await getExtractSummary(); setSummary(d); } catch { /* silent */ }
  }, [isOffline]);

  // ── Fetch live status ─────────────────────────────────────────────────────
  const fetchStatus = useCallback(async () => {
    try {
      const d = await getExtractStatus();
      setStatus(d);
      if (!d.active) {
        clearInterval(pollRef.current);
        pollRef.current = null;
        loadSummary(); // refresh totals after done
      }
    } catch { /* silent */ }
  }, [loadSummary]);

  // ── Start polling ─────────────────────────────────────────────────────────
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

  // ── Start extraction ──────────────────────────────────────────────────────
  const handleStart = async () => {
    if (starting) return;
    setStarting(true);
    setError(null);
    try {
      await startExtraction();
      await fetchStatus();
      startPolling();
    } catch (e) {
      setError('Failed to start: ' + e.message);
    } finally {
      setStarting(false);
    }
  };

  // ── Derived state ─────────────────────────────────────────────────────────
  const extractStatus = status?.status ?? 'idle';
  const isRunning     = status?.active === true;
  const isCompleted   = extractStatus === 'completed';
  const isError       = extractStatus === 'error';
  const hasActivity   = status && (
    status.files_checked > 0 || status.files_extracted > 0
  );

  return (
    <section className="ep-panel" aria-label="Text content extraction">

      {/* Header */}
      <div className="ep-header">
        <div className="ep-title-row">
          <TextIcon />
          <h2 className="ep-title">Content Extraction</h2>
          {summary?.content_extracted > 0 && (
            <span className="ep-badge ep-badge--green">
              {summary.content_extracted.toLocaleString()} extracted
            </span>
          )}
          {summary?.chunks > 0 && (
            <span className="ep-badge ep-badge--blue">
              {summary.chunks.toLocaleString()} chunks
            </span>
          )}
        </div>

        <button
          className={`ep-start-btn ${isRunning ? 'ep-start-btn--running' : ''}`}
          onClick={handleStart}
          disabled={isRunning || starting || isOffline}
          title={isOffline ? 'Start the engine first' : ''}
          id="extract-text-btn"
        >
          {isRunning ? (
            <><Spinner /> Extracting…</>
          ) : starting ? (
            <><Spinner /> Starting…</>
          ) : (
            <><FileTextIcon /> Extract Text Content</>
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="ep-error" role="alert">
          <AlertIcon />
          <span>{error}</span>
          <button onClick={() => setError(null)} aria-label="Dismiss error">×</button>
        </div>
      )}

      {/* Offline message */}
      {isOffline && (
        <div className="ep-idle-msg">Start the engine to enable text extraction</div>
      )}

      {/* Status bar */}
      {!isOffline && (
        <div className={`ep-status-bar ep-status-bar--${extractStatus}`}>
          <span className="ep-status-dot" />
          <span className="ep-status-label">{STATUS_LABELS[extractStatus] ?? extractStatus}</span>
          {isRunning && status?.current_path && (
            <span className="ep-current-path" title={status.current_path}>
              {truncatePath(status.current_path)}
            </span>
          )}
          {isError && status?.error_message && (
            <span className="ep-error-detail">{status.error_message}</span>
          )}
        </div>
      )}

      {/* Progress stats */}
      {!isOffline && hasActivity && (
        <div className="ep-stats">
          <StatBox label="Checked"   value={status?.files_checked   ?? 0} icon={<ScanIcon />} />
          <StatBox label="Extracted" value={status?.files_extracted ?? 0} icon={<CheckIcon />} accent="green" />
          <StatBox label="Chunks"    value={status?.chunks_created  ?? 0} icon={<ChunkIcon />} accent="blue" />
          <StatBox label="Skipped"   value={status?.files_skipped   ?? 0} icon={<SkipIcon />} />
          {(status?.files_failed ?? 0) > 0 && (
            <StatBox label="Failed"  value={status.files_failed}           icon={<AlertIcon />} accent="red" />
          )}
        </div>
      )}

      {/* Completion summary */}
      {!isOffline && isCompleted && summary && (
        <div className="ep-summary">
          <CheckIcon />
          <span>
            Extraction complete —{' '}
            <strong>{(summary.content_extracted ?? 0).toLocaleString()}</strong> files extracted,{' '}
            <strong>{(summary.chunks ?? 0).toLocaleString()}</strong> text chunks created
            {(summary.extraction_failed ?? 0) > 0 && (
              <>, <strong>{summary.extraction_failed}</strong> failed</>
            )}
          </span>
        </div>
      )}

      {/* Summary from DB (persistent across restarts) */}
      {!isOffline && extractStatus === 'idle' && summary && summary.content_extracted > 0 && (
        <div className="ep-db-summary">
          <DatabaseIcon />
          <span>
            Previously extracted: <strong>{summary.content_extracted.toLocaleString()}</strong> files · {' '}
            <strong>{summary.chunks.toLocaleString()}</strong> chunks
            {summary.metadata_indexed > 0 && (
              <> · <span className="ep-pending">{summary.metadata_indexed.toLocaleString()} pending</span></>
            )}
          </span>
        </div>
      )}

      {/* Idle hint */}
      {!isOffline && extractStatus === 'idle' && !starting && (!summary || summary.content_extracted === 0) && (
        <p className="ep-hint">
          Click <strong>Extract Text Content</strong> to read text from .txt, .md, .pdf, .docx,
          code files, and more. Text is stored locally and used for content search in Step 10.
        </p>
      )}

    </section>
  );
}

/* ── Constants ────────────────────────────────────────────── */

const STATUS_LABELS = {
  idle:      'Ready',
  running:   'Extracting text…',
  completed: 'Completed',
  error:     'Error',
};

/* ── Helpers ──────────────────────────────────────────────── */

function truncatePath(p) {
  if (!p) return '';
  const max = 60;
  return p.length > max ? '…' + p.slice(p.length - max) : p;
}

/* ── StatBox ──────────────────────────────────────────────── */

function StatBox({ label, value, icon, accent }) {
  return (
    <div className={`ep-stat ep-stat--${accent ?? 'default'}`}>
      <span className="ep-stat__icon">{icon}</span>
      <span className="ep-stat__value">{value.toLocaleString()}</span>
      <span className="ep-stat__label">{label}</span>
    </div>
  );
}

/* ── SVG Icons ────────────────────────────────────────────── */

function Spinner() { return <span className="ep-spinner" aria-hidden="true" />; }

function TextIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <line x1="10" y1="9" x2="8" y2="9" />
    </svg>
  );
}

function FileTextIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
    </svg>
  );
}

function ScanIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 7V5a2 2 0 0 1 2-2h2" /><path d="M17 3h2a2 2 0 0 1 2 2v2" />
      <path d="M21 17v2a2 2 0 0 1-2 2h-2" /><path d="M7 21H5a2 2 0 0 1-2-2v-2" />
      <rect x="7" y="7" width="10" height="10" rx="1" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

function ChunkIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="8" y1="6" x2="21" y2="6" />
      <line x1="8" y1="12" x2="21" y2="12" />
      <line x1="8" y1="18" x2="21" y2="18" />
      <line x1="3" y1="6" x2="3.01" y2="6" />
      <line x1="3" y1="12" x2="3.01" y2="12" />
      <line x1="3" y1="18" x2="3.01" y2="18" />
    </svg>
  );
}

function SkipIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="5" y1="12" x2="19" y2="12" />
      <polyline points="12 5 19 12 12 19" />
    </svg>
  );
}

function AlertIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  );
}

function DatabaseIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
      <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
    </svg>
  );
}

export default ExtractionPanel;
