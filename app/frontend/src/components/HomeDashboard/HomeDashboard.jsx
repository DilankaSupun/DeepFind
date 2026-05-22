import React, { useState, useEffect } from 'react';
import {
  getSearchHistory,
  clearSearchHistory,
  getRecentModifiedFiles,
  getRecentIndexedFiles,
  getDashboardSummary,
  isAbortError
} from '../../services/api';
import WatcherPanel from '../WatcherPanel/WatcherPanel';
import './HomeDashboard.css';

function HomeDashboard({ onSearchClick }) {
  const [history, setHistory] = useState([]);
  const [recentModified, setRecentModified] = useState([]);
  const [recentIndexed, setRecentIndexed] = useState([]);
  const [summary, setSummary] = useState(null);
  const [isOffline, setIsOffline] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [histRes, modRes, indRes, sumRes] = await Promise.all([
          getSearchHistory(10),
          getRecentModifiedFiles(10),
          getRecentIndexedFiles(10),
          getDashboardSummary()
        ]);
        
        setHistory(histRes.searches || []);
        setRecentModified(modRes.files || []);
        setRecentIndexed(indRes.files || []);
        setSummary(sumRes.summary || null);
        setIsOffline(false);
      } catch (error) {
        if (isAbortError(error)) return;
        console.error("Dashboard failed to load:", error);
        setIsOffline(true);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleClearHistory = async () => {
    try {
      await clearSearchHistory();
      setHistory([]);
    } catch (err) {
      console.error("Failed to clear history", err);
    }
  };

  const handleOpenFile = async (e, path) => {
    e.stopPropagation();
    if (!window.deepfind?.openFile) return alert('Desktop API not available. Please run inside the Electron app.');
    const res = await window.deepfind.openFile(path);
    if (!res.success) alert(`File could not be opened.\n${res.error}`);
  };

  const handleOpenFolder = async (e, path) => {
    e.stopPropagation();
    if (!window.deepfind?.showInFolder) return alert('Desktop API not available. Please run inside the Electron app.');
    const res = await window.deepfind.showInFolder(path);
    if (!res.success) alert(`Unable to open folder.\n${res.error}`);
  };

  const renderFileRow = (f, showIndexedTime = false) => {
    const displayTime = showIndexedTime ? f.last_indexed_at : f.modified_at;
    const timeStr = displayTime ? new Date(displayTime).toLocaleString() : 'Unknown';
    const isMissing = f.status === 'missing';
    
    return (
      <div className={`home-dashboard-file-row ${isMissing ? 'missing-file' : ''}`} key={f.id} title={isMissing ? 'File is missing' : ''}>
        <div className="file-icon-col">
          <span className="file-ext-badge">{f.extension || 'file'}</span>
        </div>
        <div className="file-info-col">
          <div className="file-name">{f.name} {isMissing && <span className="missing-badge">(Missing)</span>}</div>
          <div className="file-path">{f.path}</div>
        </div>
        <div className="file-meta-col">
          <div className="file-time">{timeStr}</div>
          {f.tags && <div className="file-tag-mini">{f.tags.split(',')[0]}</div>}
        </div>
        <div className="file-actions-col">
          <button 
            className="row-action-btn" 
            disabled={isMissing}
            onClick={(e) => handleOpenFile(e, f.path)}
            title={isMissing ? "File is missing" : "Open File"}
          >
            Open
          </button>
          <button 
            className="row-action-btn" 
            onClick={(e) => handleOpenFolder(e, f.path)}
            title="Open Folder"
          >
            Folder
          </button>
        </div>
      </div>
    );
  };

  if (loading) {
    return <div className="home-dashboard-loading">Loading dashboard...</div>;
  }

  if (isOffline) {
    return (
      <div className="home-dashboard-offline">
        <h2>Engine offline. Recent activity unavailable.</h2>
        <p>Ensure the Python backend is running.</p>
      </div>
    );
  }

  const noFiles = summary && summary.total_files === 0;

  if (noFiles) {
    return (
      <div className="home-dashboard-empty">
        <h2>No indexed files yet. Run indexing first.</h2>
      </div>
    );
  }

  return (
    <div className="home-dashboard">
      {summary && (
        <div className="dashboard-summary-cards">
          <div className="summary-card">
            <h3>{summary.total_files}</h3>
            <span>Total Indexed</span>
          </div>
          <div className="summary-card">
            <h3>{summary.content_extracted}</h3>
            <span>Content Extracted</span>
          </div>
          <div className="summary-card">
            <h3>{summary.files_with_tags}</h3>
            <span>Files with Tags</span>
          </div>
          <div className="summary-card">
            <h3>{summary.recent_searches}</h3>
            <span>Total Searches</span>
          </div>
        </div>
      )}

      <div className="dashboard-grid">
        <div className="dashboard-column">
          <div className="dashboard-section-header">
            <h2>Recent Searches</h2>
            {history.length > 0 && (
              <button className="clear-history-btn" onClick={handleClearHistory}>
                Clear History
              </button>
            )}
          </div>
          <div className="dashboard-card history-card">
            {history.length === 0 ? (
              <div className="empty-state">No recent searches yet.</div>
            ) : (
              <ul className="history-list">
                {history.map((h) => (
                  <li key={h.id} onClick={() => onSearchClick && onSearchClick(h.query)}>
                    <span className="history-query">{h.query}</span>
                    <span className="history-meta">{h.result_count} results &bull; {new Date(h.searched_at).toLocaleDateString()}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="dashboard-column">
          <div className="dashboard-section-header">
            <h2>Recently Modified Files</h2>
          </div>
          <div className="dashboard-card files-card">
            {recentModified.length === 0 ? (
              <div className="empty-state">No files found.</div>
            ) : (
              <div className="file-list">
                {recentModified.map(f => renderFileRow(f, false))}
              </div>
            )}
          </div>
        </div>

        <div className="dashboard-column">
          <div className="dashboard-section-header">
            <h2>Recently Indexed Files</h2>
          </div>
          <div className="dashboard-card files-card">
            {recentIndexed.length === 0 ? (
              <div className="empty-state">No files found.</div>
            ) : (
              <div className="file-list">
                {recentIndexed.map(f => renderFileRow(f, true))}
              </div>
            )}
          </div>
        </div>

        {/* Watcher Panel Row */}
        <div className="dashboard-column" style={{ gridColumn: '1 / -1' }}>
          <WatcherPanel />
        </div>
      </div>
    </div>
  );
}

export default HomeDashboard;
