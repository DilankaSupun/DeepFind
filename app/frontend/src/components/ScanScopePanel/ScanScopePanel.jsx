import React, { useState, useEffect, useCallback } from 'react';
import {
  getScanScopeStatus,
  initializeScanScope,
  addExcludedPath,
  removeExcludedPath,
  reloadScanScope,
} from '../../services/api.js';
import './ScanScopePanel.css';

function ScanScopePanel({ engineStatus }) {
  const [scope, setScope] = useState(null);
  const [loading, setLoading] = useState(true);
  const [initializing, setInitializing] = useState(false);
  const [adding, setAdding] = useState(false);
  const [removing, setRemoving] = useState(null);
  const [error, setError] = useState(null);

  const isOffline = engineStatus !== 'online';

  const loadScope = useCallback(async () => {
    if (isOffline) { setLoading(false); return; }
    try {
      const data = await getScanScopeStatus();
      setScope(data);
      setError(null);
    } catch { setError('Could not load scan scope.'); }
    finally { setLoading(false); }
  }, [isOffline]);

  useEffect(() => { loadScope(); }, [loadScope]);

  const handleInitialize = async () => {
    setInitializing(true); setError(null);
    try {
      await initializeScanScope();
      await loadScope();
    } catch (e) { setError('Setup failed: ' + e.message); }
    finally { setInitializing(false); }
  };

  const handleAddExclusion = async () => {
    if (!window.deepfind?.selectFolder) return setError('Electron required.');
    setAdding(true); setError(null);
    try {
      const path = await window.deepfind.selectFolder();
      if (!path) return;
      await addExcludedPath(path);
      await reloadScanScope();
      await loadScope();
    } catch (e) { setError('Failed to add exclusion: ' + e.message); }
    finally { setAdding(false); }
  };

  const handleRemoveExclusion = async (id) => {
    setRemoving(id); setError(null);
    try {
      await removeExcludedPath(id);
      await reloadScanScope();
      await loadScope();
    } catch (e) { setError('Failed to remove exclusion: ' + e.message); }
    finally { setRemoving(null); }
  };

  if (isOffline) {
    return (
      <section className="scan-scope-panel">
        <div className="scan-scope__offline"><CloudOffIcon /> Start the engine to manage scan scope</div>
      </section>
    );
  }

  if (loading) {
    return (
      <section className="scan-scope-panel">
        <div className="scan-scope__loading"><Spinner /> Loading scan scope…</div>
      </section>
    );
  }

  const needsInit = scope && scope.scan_roots?.length === 0;

  return (
    <section className="scan-scope-panel" aria-label="Search Coverage">
      <div className="scan-scope__header">
        <div className="scan-scope__title-row">
          <ScanIcon />
          <h2 className="scan-scope__title">Search Coverage</h2>
        </div>
        <div className="scan-scope__status">
          <span className={`status-indicator ${scope?.automatic_scan ? 'status-indicator--active' : ''}`} />
          Automatic scanning: {scope?.automatic_scan ? 'Enabled' : 'Disabled'}
        </div>
      </div>

      {error && (
        <div className="scan-scope__error" role="alert">
          <AlertIcon /><span>{error}</span>
          <button className="scan-scope__error-close" onClick={() => setError(null)}>×</button>
        </div>
      )}

      {needsInit ? (
        <div className="scan-scope__init">
          <p>DeepFind is ready to automatically discover your local files.</p>
          <button className="ss-btn ss-btn--primary" onClick={handleInitialize} disabled={initializing}>
            {initializing ? <><Spinner /> Initializing…</> : 'Setup Default Scope'}
          </button>
        </div>
      ) : (
        <div className="scan-scope__content">
          <p className="scan-scope__description">
            DeepFind automatically scans your local files and keeps the index updated in the background. Add exclusions only for folders, files, or drives you do not want DeepFind to scan.
          </p>

          <div className="scan-scope__section">
            <h3 className="scan-scope__section-title">
              Scanned Locations
              <span className="scan-scope__section-subtitle">These locations are included in indexing, extraction, tagging, semantic indexing, and automatic watcher updates. Excluded locations are skipped everywhere.</span>
            </h3>
            <ul className="ss-list">
              {scope?.scan_roots?.map(root => (
                <li key={root.id} className="ss-item">
                  {root.source_type === 'auto_drive' ? <DriveIcon /> : <FolderFilledIcon />}
                  {root.folder_path} <span className="ss-badge">Scanning</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="scan-scope__section">
            <h3 className="scan-scope__section-title">
              Excluded Locations
              <span className="scan-scope__section-subtitle">Anything listed here is skipped by indexing, extraction, tagging, semantic indexing, watcher updates, and search results.</span>
            </h3>
            <ul className="ss-list">
              {scope?.user_exclusions?.map(excl => (
                <li key={excl.id} className="ss-item ss-item--excluded">
                  <FolderFilledIcon /> {excl.path} <span className="ss-badge ss-badge--user">Skipped</span>
                  <button className="ss-item__remove" onClick={() => handleRemoveExclusion(excl.id)} disabled={removing === excl.id}>
                    {removing === excl.id ? <Spinner size={12} /> : <TrashIcon />}
                  </button>
                </li>
              ))}
              {(!scope?.user_exclusions || scope.user_exclusions.length === 0) && (
                <li className="ss-item ss-item--empty">No user exclusions added.</li>
              )}
            </ul>
            <div className="scan-scope__actions">
              <button className="ss-btn ss-btn--ghost" onClick={handleAddExclusion} disabled={adding}>
                <PlusIcon /> Add Exclusion
              </button>
            </div>
          </div>

          {scope?.system_exclusions?.length > 0 && (
            <div className="scan-scope__section">
              <details className="scan-scope__details">
                <summary className="scan-scope__section-title">
                  System Exclusions ({scope.system_exclusions.length}) 
                  <span className="scan-scope__section-subtitle">System folders are skipped automatically for safety and performance.</span>
                </summary>
                <ul className="ss-list ss-list--system">
                  {scope.system_exclusions.map(excl => (
                    <li key={excl.id} className="ss-item ss-item--system">
                      <FolderFilledIcon /> {excl.path} <span className="ss-badge ss-badge--system">System</span>
                    </li>
                  ))}
                </ul>
              </details>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function Spinner({ size = 12 }) { return <span className="ss-spinner" style={{ width: size, height: size }} aria-hidden="true" />; }
function ScanIcon() { return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><rect x="7" y="7" width="10" height="10" rx="1"/></svg>; }
function FolderFilledIcon() { return <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>; }
function DriveIcon() { return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>; }
function PlusIcon() { return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>; }
function TrashIcon() { return <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/></svg>; }
function AlertIcon() { return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>; }
function CloudOffIcon() { return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><line x1="2" y1="2" x2="22" y2="22"/><path d="M5.782 5.782A7 7 0 0 0 9 19h8.5a4.5 4.5 0 0 0 1.307-.193"/><path d="M21.532 16.5A4.5 4.5 0 0 0 17.5 10h-1.79A7.008 7.008 0 0 0 10 5.07"/></svg>; }

export default ScanScopePanel;
