import React, { useState, useCallback } from 'react';
import SearchBar from './components/SearchBar/SearchBar.jsx';
import SearchResults from './components/SearchResults/SearchResults.jsx';
import FolderManager from './components/FolderManager/FolderManager.jsx';
import IndexingPanel from './components/IndexingPanel/IndexingPanel.jsx';
import ExtractionPanel from './components/ExtractionPanel/ExtractionPanel.jsx';
import TaggingPanel from './components/TaggingPanel/TaggingPanel.jsx';
import HomeDashboard from './components/HomeDashboard/HomeDashboard.jsx';
import { useEngineStatus } from './hooks/useEngineStatus.js';
import { searchFiles } from './services/api.js';
import './styles/App.css';

/**
 * DeepFind — Main App Component
 *
 * Step 4: Connected to FastAPI backend via useEngineStatus hook.
 * Step 8: Search wired up — filename/path/extension search.
 * Step 10: Added search mode selector (All / Name·Path / Content) and FTS5 content search.
 */
function App() {
  const { status, version } = useEngineStatus();

  // ── Search State ─────────────────────────────────────────
  const [searchState, setSearchState]   = useState('idle');   // idle | loading | results | empty | error
  const [searchQuery,  setSearchQuery]  = useState('');
  const [searchMode,   setSearchMode]   = useState('all');    // all | metadata | content
  const [searchResults, setResults]     = useState([]);
  const [searchTotal,  setTotal]        = useState(0);
  const [searchError,  setError]        = useState(null);
  const [noContentWarning,  setNoContentWarning]   = useState(false);
  const [hasExtractedContent, setHasExtractedContent] = useState(true);
  const [loadingMore, setLoadingMore]   = useState(false);
  const LIMIT = 50;
  
  const searchRequestId = React.useRef(0);

  const handleSearch = useCallback(async (query, mode = 'all') => {
    setSearchQuery(query);
    setSearchMode(mode);
    setSearchState('loading');
    setError(null);
    setNoContentWarning(false);

    const currentReqId = ++searchRequestId.current;

    try {
      const data = await searchFiles(query, { limit: LIMIT, offset: 0, searchType: mode });
      
      // Ignore if a newer search was started
      if (currentReqId !== searchRequestId.current) return;
      
      setResults(data.results || []);
      setTotal(data.total || 0);
      setHasExtractedContent(data.has_extracted_content ?? true);
      setNoContentWarning(data.no_content_warning ?? false);
      setSearchState((data.results || []).length === 0 ? 'empty' : 'results');
    } catch (err) {
      if (currentReqId !== searchRequestId.current) return;
      
      setError(err.message || 'Backend unreachable');
      setResults([]);
      setTotal(0);
      setSearchState('error');
    }
  }, []);

  const handleLoadMore = useCallback(async () => {
    if (loadingMore || searchResults.length >= searchTotal) return;
    
    setLoadingMore(true);
    const currentReqId = ++searchRequestId.current;
    
    try {
      const data = await searchFiles(searchQuery, { 
        limit: LIMIT, 
        offset: searchResults.length, 
        searchType: searchMode 
      });
      
      if (currentReqId !== searchRequestId.current) return;
      
      setResults(prev => {
        // Avoid duplicates by tracking IDs
        const existingIds = new Set(prev.map(r => r.id));
        const newResults = (data.results || []).filter(r => !existingIds.has(r.id));
        return [...prev, ...newResults];
      });
      setTotal(data.total || 0);
    } catch (err) {
      if (currentReqId !== searchRequestId.current) return;
      alert(`Load more failed: ${err.message || 'Backend unreachable'}`);
    } finally {
      if (currentReqId === searchRequestId.current) {
        setLoadingMore(false);
      }
    }
  }, [loadingMore, searchResults, searchTotal, searchQuery, searchMode]);

  const handleClear = useCallback(() => {
    setSearchState('idle');
    setSearchQuery('');
    setSearchMode('all');
    setResults([]);
    setTotal(0);
    setError(null);
    setNoContentWarning(false);
  }, []);

  const engineOnline = status === 'online';

  return (
    <div className="app-shell">
      {/* Ambient background glow orbs */}
      <div className="glow-orb glow-orb--left"  aria-hidden="true" />
      <div className="glow-orb glow-orb--right" aria-hidden="true" />

      {/* Dot grid background pattern */}
      <div className="bg-grid" aria-hidden="true" />

      {/* ── Main Content ─────────────────────────────────── */}
      <main className="main-content" role="main">

        {/* ── Hero: Logo + Title ── */}
        <header className="hero-header">
          <div className="logo-mark" aria-hidden="true">
            <svg width="36" height="36" viewBox="0 0 40 40" fill="none">
              <circle cx="20" cy="20" r="19" stroke="url(#logoGrad)" strokeWidth="2" />
              <circle cx="18" cy="18" r="8" stroke="url(#logoGrad)" strokeWidth="2" />
              <line x1="24" y1="24" x2="32" y2="32" stroke="url(#logoGrad)" strokeWidth="2.5" strokeLinecap="round" />
              <defs>
                <linearGradient id="logoGrad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#6366f1" />
                  <stop offset="1" stopColor="#8b5cf6" />
                </linearGradient>
              </defs>
            </svg>
          </div>

          <h1 className="app-title">
            Deep<span className="text-gradient">Find</span>
          </h1>
          <p className="app-subtitle">Local-first AI file search</p>
        </header>

        {/* ── Search Section ── */}
        <section className="search-section" aria-label="Search">
          <SearchBar
            onSearch={handleSearch}
            onClear={handleClear}
            loading={searchState === 'loading'}
            hasResults={searchState === 'results' || searchState === 'empty' || searchState === 'error'}
            engineOnline={engineOnline}
          />

          {/* Live engine status badge */}
          <EngineStatusBadge status={status} version={version} />
        </section>

        {/* ── Search Results (shown when not idle) ── */}
        {searchState !== 'idle' && (
          <SearchResults
            state={searchState}
            results={searchResults}
            total={searchTotal}
            query={searchQuery}
            searchMode={searchMode}
            limit={LIMIT}
            error={searchError}
            noContentWarning={noContentWarning}
            hasExtractedContent={hasExtractedContent}
            onLoadMore={handleLoadMore}
            loadingMore={loadingMore}
          />
        )}

        {/* ── Home Dashboard (shown when idle) ── */}
        {searchState === 'idle' && (
          <HomeDashboard onSearchClick={handleSearch} />
        )}

        {/* ── Folder Manager (hidden during search) ── */}
        {searchState === 'idle' && (
          <FolderManager engineStatus={status} />
        )}

        {/* ── Indexing Panel (hidden during search) ── */}
        {searchState === 'idle' && (
          <IndexingPanel engineStatus={status} />
        )}

        {/* ── Extraction Panel (hidden during search) ── */}
        {searchState === 'idle' && (
          <ExtractionPanel engineStatus={status} />
        )}

        {/* ── Tagging Panel (hidden during search) ── */}
        {searchState === 'idle' && (
          <TaggingPanel engineStatus={status} />
        )}

      </main>

      {/* ── Footer ── */}
      <footer className="app-footer">
        <span className="footer-badge">
          <span className="footer-dot" aria-hidden="true" />
          Local-first · No cloud · No uploads
        </span>
        <span className="footer-version">v0.1.0-dev · Step 11</span>
      </footer>
    </div>
  );
}

/* ── Engine Status Badge ─────────────────────────────────── */

/**
 * Displays live backend engine status with three visual states:
 *   checking → grey spinner
 *   online   → green dot + "Engine running · vX.X.X"
 *   offline  → amber dot + "Backend not connected"
 */
function EngineStatusBadge({ status, version }) {
  const config = {
    checking: {
      modifier: 'status-badge--checking',
      dotClass: 'status-dot--checking',
      label: 'Checking engine…',
      detail: null,
    },
    online: {
      modifier: 'status-badge--online',
      dotClass: 'status-dot--online',
      label: 'Engine running',
      detail: version ? `v${version}` : null,
    },
    offline: {
      modifier: 'status-badge--offline',
      dotClass: 'status-dot--offline',
      label: 'Backend not connected',
      detail: 'start engine to enable search',
    },
  };

  const { modifier, dotClass, label, detail } = config[status] ?? config.offline;

  return (
    <div
      className={`status-badge ${modifier}`}
      role="status"
      aria-live="polite"
      aria-label={`Engine status: ${label}`}
    >
      <span className={`status-dot ${dotClass}`} aria-hidden="true" />
      <span className="status-label">{label}</span>
      {detail && (
        <span className="status-detail" aria-hidden="true">· {detail}</span>
      )}
    </div>
  );
}

/* ── Feature Card ────────────────────────────────────────── */
function FeatureCard({ icon, title, description, step, isAI = false, isActive = false }) {
  return (
    <article className={`feature-card ${isAI ? 'feature-card--ai' : ''} ${isActive ? 'feature-card--active' : ''}`}>
      <div className="feature-icon" aria-hidden="true">{icon}</div>
      <div className="feature-body">
        <h3 className="feature-title">{title}</h3>
        <p className="feature-desc">{description}</p>
      </div>
      <span className={`feature-step ${isAI ? 'feature-step--ai' : ''} ${isActive ? 'feature-step--active' : ''}`}>{step}</span>
    </article>
  );
}

/* ── SVG Icons ───────────────────────────────────────────── */
function FilenameIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
    </svg>
  );
}

function ContentIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
      <line x1="8" y1="11" x2="14" y2="11" />
      <line x1="11" y1="8" x2="11" y2="14" />
    </svg>
  );
}

function SemanticIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  );
}

function TagIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z" />
      <line x1="7" y1="7" x2="7.01" y2="7" />
    </svg>
  );
}

export default App;
