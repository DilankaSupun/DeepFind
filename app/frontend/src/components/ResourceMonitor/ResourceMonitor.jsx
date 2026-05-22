import React, { useState, useEffect } from 'react';
import { getSystemResources, isAbortError } from '../../services/api';
import './ResourceMonitor.css';

function ResourceMonitor() {
  const [resources, setResources] = useState(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    
    async function fetchResources() {
      try {
        const data = await getSystemResources();
        if (mounted) {
          setResources(data);
          setError(false);
          setLoading(false);
        }
      } catch (err) {
        if (isAbortError(err)) return;
        if (mounted) {
          console.error("Failed to fetch system resources:", err);
          setError(true);
          setLoading(false);
        }
      }
    }

    fetchResources();
    
    // Refresh every 5 seconds
    const interval = setInterval(fetchResources, 5000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  if (loading && !resources) {
    return (
      <div className="panel-card resource-monitor">
        <h2 className="panel-card__title">Storage & Performance</h2>
        <div className="resource-monitor__loading">Loading live metrics...</div>
      </div>
    );
  }

  if (error || !resources) {
    return (
      <div className="panel-card resource-monitor resource-monitor--error">
        <h2 className="panel-card__title">Storage & Performance</h2>
        <div className="resource-monitor__offline">
          <p>System metrics unavailable.</p>
          <p className="resource-monitor__subtext">Ensure the DeepFind backend is running.</p>
        </div>
      </div>
    );
  }

  const storage = resources?.storage ?? {};
  const runtime = resources?.runtime ?? {};

  return (
    <div className="panel-card resource-monitor">
      <h2 className="panel-card__title">Storage & Performance</h2>
      
      <div className="resource-monitor__grid">
        <div className="resource-monitor__section">
          <h3 className="resource-monitor__section-title">Storage used by DeepFind:</h3>
          <ul className="resource-monitor__list">
            <li>
              <span className="rm-label">App data:</span>
              <span className="rm-value">{storage?.data_folder?.size_human ?? 'Not available'}</span>
            </li>
            <li>
              <span className="rm-label">Database:</span>
              <span className="rm-value">{storage?.sqlite_db?.size_human ?? 'Not available'}</span>
            </li>
            <li>
              <span className="rm-label">Semantic index:</span>
              <span className="rm-value">{storage?.faiss_index?.size_human ?? 'Not created yet'}</span>
            </li>
            <li>
              <span className="rm-label">Model cache:</span>
              <span className="rm-value">{storage?.model_cache?.size_human ?? 'Not tracked'}</span>
            </li>
          </ul>
        </div>

        <div className="resource-monitor__section">
          <h3 className="resource-monitor__section-title">Runtime usage:</h3>
          <ul className="resource-monitor__list">
            <li>
              <span className="rm-label">Backend RAM:</span>
              <span className="rm-value">{runtime?.process_memory?.rss_human ?? 'Not available'}</span>
            </li>
            <li>
              <span className="rm-label">Backend CPU:</span>
              <span className="rm-value">{runtime?.cpu_percent !== undefined ? `${runtime.cpu_percent}%` : 'Not available'}</span>
            </li>
          </ul>
          <p className="resource-monitor__approx-note">Approximate live backend process usage</p>
        </div>
      </div>

      <div className="resource-monitor__footer">
        Only DeepFind-created data is counted. Your original files are not included.
      </div>
    </div>
  );
}

export default ResourceMonitor;
