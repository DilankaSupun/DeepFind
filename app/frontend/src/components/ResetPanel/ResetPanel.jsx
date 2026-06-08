import React, { useState, useEffect } from 'react';
import { getResetPreview, clearSearchIndex, resetAppData, isAbortError } from '../../services/api';
import './ResetPanel.css';

function ResetPanel({ onResetSuccess }) {
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState(null); // null, 'index', 'app-data'
  const [confirmText, setConfirmText] = useState('');
  const [successMsg, setSuccessMsg] = useState(null);

  const loadPreview = async () => {
    try {
      const data = await getResetPreview();
      setPreview(data.index);
    } catch (err) {
      if (!isAbortError(err)) {
        console.error("Failed to load reset preview:", err);
      }
    }
  };

  useEffect(() => {
    loadPreview();
  }, []);

  const handleClearIndex = async () => {
    if (!window.confirm("This will clear DeepFind's search index, extracted text, tags, semantic vectors, and search history. Your original files will not be deleted. Indexed folders will be kept. Continue?")) {
      return;
    }

    setLoading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await clearSearchIndex();
      if (res.status === 'error') throw new Error(res.message);
      
      setSuccessMsg(res.message || "Search index cleared successfully.");
      if (onResetSuccess) onResetSuccess();
      loadPreview();
      setMode(null);
      
      // Auto-hide success message after 5 seconds
      setTimeout(() => setSuccessMsg(null), 5000);
    } catch (err) {
      if (!isAbortError(err)) {
        setError(err.message || 'Failed to clear search index.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResetAppData = async () => {
    if (confirmText !== 'RESET') {
      alert('Please type RESET to confirm.');
      return;
    }

    if (!window.confirm("This will reset DeepFind to a newly installed state by deleting all local index data and folder selections. Your original files will not be deleted. Continue?")) {
      return;
    }

    setLoading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await resetAppData();
      if (res.status === 'error') throw new Error(res.message);
      
      setSuccessMsg(res.message || "App data reset successfully.");
      setConfirmText('');
      if (onResetSuccess) onResetSuccess();
      loadPreview();
      setMode(null);
      
      // Auto-hide success message after 5 seconds
      setTimeout(() => setSuccessMsg(null), 5000);
    } catch (err) {
      if (!isAbortError(err)) {
        setError(err.message || 'Failed to reset app data.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="settings-panel reset-panel">
      <div className="panel-header">
        <div className="header-title">
          <h2>Danger Zone</h2>
          <span className="badge danger-badge">Caution</span>
        </div>
        <p className="panel-description">
          Reset local databases and indexes. Your original files will never be modified or deleted.
        </p>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {successMsg && <div className="success-banner" style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#10b981', padding: '1rem', borderRadius: '8px', border: '1px solid #10b981', marginBottom: '1rem' }}>{successMsg}</div>}

      <div className="reset-options">
        <div className="reset-card">
          <div className="reset-card-info">
            <h3>Clear Search Index</h3>
            <p>
              Deletes indexed file records, extracted text, tags, search history, and semantic index.
              Your selected folders are kept. Your original files are not deleted.
            </p>
          </div>
          <button 
            className="btn btn-warning" 
            onClick={() => setMode('index')}
            disabled={loading}
          >
            Clear Index
          </button>
        </div>

        <div className="reset-card">
          <div className="reset-card-info">
            <h3>Reset App Data</h3>
            <p>
              Deletes all DeepFind local data and returns the app to a newly installed state.
              Your original files are not deleted.
            </p>
          </div>
          <button 
            className="btn btn-danger" 
            onClick={() => setMode('app-data')}
            disabled={loading}
          >
            Reset App Data
          </button>
        </div>
      </div>

      {mode === 'index' && (
        <div className="reset-confirmation-modal">
          <div className="modal-content">
            <h3>Confirm Clear Search Index</h3>
            <p>Are you sure you want to clear the search index?</p>
            {preview && (
              <ul className="preview-list">
                <li>{preview.files} files will be removed from index</li>
                <li>{preview.chunks} text chunks will be deleted</li>
                <li>Search history ({preview.search_history} entries) will be cleared</li>
                <li>FAISS Index ({preview.faiss_index_size_human}) will be deleted</li>
              </ul>
            )}
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setMode(null)}>Cancel</button>
              <button className="btn btn-warning" onClick={handleClearIndex} disabled={loading}>
                {loading ? 'Clearing...' : 'Confirm Clear Index'}
              </button>
            </div>
          </div>
        </div>
      )}

      {mode === 'app-data' && (
        <div className="reset-confirmation-modal">
          <div className="modal-content">
            <h3>Confirm Reset App Data</h3>
            <p className="danger-text">This will permanently delete all DeepFind internal data and configurations.</p>
            {preview && (
              <ul className="preview-list">
                <li>{preview.folders} indexed folders will be removed</li>
                <li>{preview.files} files will be removed from index</li>
                <li>{preview.chunks} text chunks will be deleted</li>
                <li>Database ({preview.database_size_human}) will be reset</li>
              </ul>
            )}
            <div className="confirm-input-group">
              <label>Type <strong>RESET</strong> to confirm:</label>
              <input 
                type="text" 
                value={confirmText} 
                onChange={(e) => setConfirmText(e.target.value)} 
                placeholder="RESET"
              />
            </div>
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setMode(null)}>Cancel</button>
              <button 
                className="btn btn-danger" 
                onClick={handleResetAppData} 
                disabled={loading || confirmText !== 'RESET'}
              >
                {loading ? 'Resetting...' : 'Confirm Full Reset'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ResetPanel;
