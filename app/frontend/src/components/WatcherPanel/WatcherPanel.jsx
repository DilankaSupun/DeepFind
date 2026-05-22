import React, { useState, useEffect } from 'react';
import { getWatcherStatus, startWatcher, stopWatcher, reloadWatcher, isAbortError } from '../../services/api';
import './WatcherPanel.css';

export default function WatcherPanel() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    let timeoutId = null;

    async function fetchStatus() {
      if (!mounted) return;
      try {
        const data = await getWatcherStatus();
        if (mounted) setStatus(data);
      } catch (err) {
        if (!isAbortError(err)) {
          console.error("Failed to fetch watcher status:", err);
          if (mounted) setStatus(null);
        }
      } finally {
        if (mounted) {
          setLoading(false);
          timeoutId = setTimeout(fetchStatus, 5000); // Poll every 5s
        }
      }
    }

    fetchStatus();

    return () => {
      mounted = false;
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, []);

  const handleStart = async () => {
    setActionLoading(true);
    try {
      await startWatcher();
      const s = await getWatcherStatus();
      setStatus(s);
    } catch (err) {
      alert("Failed to start watcher: " + err.message);
    }
    setActionLoading(false);
  };

  const handleStop = async () => {
    setActionLoading(true);
    try {
      await stopWatcher();
      const s = await getWatcherStatus();
      setStatus(s);
    } catch (err) {
      alert("Failed to stop watcher: " + err.message);
    }
    setActionLoading(false);
  };

  const handleReload = async () => {
    setActionLoading(true);
    try {
      await reloadWatcher();
      const s = await getWatcherStatus();
      setStatus(s);
    } catch (err) {
      alert("Failed to reload watcher: " + err.message);
    }
    setActionLoading(false);
  };

  if (loading && !status) return <div className="watcher-panel-loading">Loading Watcher Status...</div>;

  const isRunning = status?.active;

  return (
    <div className="watcher-panel dashboard-card">
      <div className="watcher-header">
        <div className="watcher-title-row">
          <h3>File System Watcher</h3>
          <span className={`watcher-badge ${isRunning ? 'running' : 'stopped'}`}>
            {isRunning ? 'Running' : 'Stopped'}
          </span>
        </div>
        <p className="watcher-subtitle">Automatically keeps DeepFind updated when files change.</p>
      </div>

      <div className="watcher-stats-grid">
        <div className="stat-box">
          <span className="stat-label">Watched Folders</span>
          <span className="stat-value">{status?.watched_folders || 0}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Processed Events</span>
          <span className="stat-value">{status?.processed_events || 0}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Queued Events</span>
          <span className="stat-value">{status?.queued_events || 0}</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Errors</span>
          <span className="stat-value">{status?.errors || 0}</span>
        </div>
      </div>

      <div className="watcher-times">
        {status?.last_event_at && <div className="watcher-time">Last Event: {status.last_event_at}</div>}
        {status?.last_processed_at && <div className="watcher-time">Last Processed: {status.last_processed_at}</div>}
      </div>

      <div className="watcher-actions">
        {!isRunning ? (
          <button className="primary-btn" onClick={handleStart} disabled={actionLoading}>
            {actionLoading ? 'Starting...' : 'Start Watcher'}
          </button>
        ) : (
          <button className="secondary-btn" onClick={handleStop} disabled={actionLoading}>
            {actionLoading ? 'Stopping...' : 'Stop Watcher'}
          </button>
        )}
        <button className="secondary-btn outline" onClick={handleReload} disabled={actionLoading || !isRunning}>
          Reload Folders
        </button>
      </div>
    </div>
  );
}
