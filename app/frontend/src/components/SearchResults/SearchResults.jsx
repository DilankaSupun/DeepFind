import React from 'react';
import './SearchResults.css';

/**
 * SearchResults — Step 10
 *
 * Renders ranked search result cards with match type badges and content snippets.
 * Handles: loading, empty, no-content-warning, error, and results states.
 *
 * Props:
 *   state               — 'idle' | 'loading' | 'results' | 'empty' | 'error'
 *   results             — array of result objects from /search
 *   total               — total matches found
 *   query               — the search query string
 *   searchMode          — 'all' | 'metadata' | 'content'
 *   limit               — the applied limit (default 50)
 *   error               — error message string if state === 'error'
 *   noContentWarning    — bool: content searched but no extracted files exist
 *   hasExtractedContent — bool: at least some files have been extracted
 */
/**
 * Safely renders snippet text with [[HL]]...[[/HL]] markers.
 * Splits text by the markers and wraps highlighted terms in <mark>.
 * React natively escapes all strings, preventing XSS injection.
 */
function renderHighlightedText(text) {
  if (!text) return null;
  const parts = text.split(/\[\[HL\]\](.*?)\[\[\/HL\]\]/g);
  return parts.map((part, index) => {
    // Because of the capture group, odd indices are the matched terms
    if (index % 2 === 1) {
      return <mark key={index} className="highlighted-term">{part}</mark>;
    }
    return <span key={index}>{part}</span>;
  });
}

function SearchResults({
  state, results = [], total = 0, query = '',
  searchMode = 'all', limit = 50, error = null,
  noContentWarning = false, hasExtractedContent = true,
  noIndex = false,
  onLoadMore, loadingMore = false
}) {
  
  // Debug log for Step 13 fix removed

  if (state === 'idle') return null;

  if (state === 'loading') {
    return (
      <section className="sr-section" aria-live="polite" aria-label="Search results">
        <div className="sr-loading">
          <span className="sr-spinner" aria-hidden="true" />
          <span>Searching{searchMode === 'content' ? ' file contents' : ' indexed files'}…</span>
        </div>
      </section>
    );
  }

  if (state === 'error') {
    return (
      <section className="sr-section" aria-live="polite" aria-label="Search error">
        <div className="sr-error">
          <ErrorIcon />
          <div className="sr-error__body">
            <p className="sr-error__title">Engine offline</p>
            <p className="sr-error__detail">
              {error || 'Cannot reach the backend. Start the engine and try again.'}
            </p>
          </div>
        </div>
      </section>
    );
  }

  if (state === 'empty') {
    // Special: tried content search but nothing extracted yet
    if (noContentWarning) {
      return (
        <section className="sr-section" aria-live="polite" aria-label="No extracted content">
          <div className="sr-empty">
            <ExtractIcon />
            <p className="sr-empty__title">No content-indexed files yet</p>
            <p className="sr-empty__detail">
              Run <strong>Content Extraction</strong> first to enable full-text content search.
              Files must have extracted text before they can be searched by content.
            </p>
          </div>
        </section>
      );
    }
    
    if (searchMode === 'semantic' && noIndex) {
      return (
        <section className="sr-section" aria-live="polite" aria-label="No semantic index">
          <div className="sr-empty">
            <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 2C8.686 2 6 4.686 6 8c0 1.071.277 2.077.766 2.946L5 15l2 2 3.553-1.776A5.96 5.96 0 0012 18c3.314 0 6-2.686 6-6S15.314 2 12 2z" />
            </svg>
            <p className="sr-empty__title">Semantic search is not ready yet</p>
            <p className="sr-empty__detail">
              Build the Semantic Index from the Home Dashboard first.
            </p>
          </div>
        </section>
      );
    }

    const contentEmptyMsg = searchMode === 'content'
      ? 'No content matches found.'
      : 'No indexed files match';

    return (
      <section className="sr-section" aria-live="polite" aria-label="No results">
        <div className="sr-empty">
          <EmptyIcon />
          <p className="sr-empty__title">{searchMode === 'semantic' ? 'No semantic matches found' : contentEmptyMsg}</p>
          <p className="sr-empty__detail">
            {searchMode === 'semantic'
              ? <>No files semantically match <em>"{query}"</em>. Try a different concept.</>
              : searchMode === 'content'
              ? <>No file content matches <em>"{query}"</em>. Try a shorter or different word.</>
              : <>No indexed files match <em>"{query}"</em>. Try a different term or run indexing.</>
            }
          </p>
        </div>
      </section>
    );
  }

  // state === 'results'
  const showingAll = results.length >= total;

  return (
    <section className="sr-section" aria-live="polite" aria-label={`Search results for ${query}`}>

      {/* Results header */}
      <div className="sr-header">
        <span className="sr-header__count">
          <strong>{total.toLocaleString()}</strong> file{total !== 1 ? 's' : ''} found
        </span>
        <span className="sr-header__query">for <em>"{query}"</em></span>
        {searchMode !== 'all' && (
          <span className={`sr-mode-badge sr-mode-badge--${searchMode}`}>
            {searchMode === 'content' ? 'Content search' 
              : searchMode === 'semantic' ? 'Semantic search' 
              : 'Name / Path'}
          </span>
        )}
        {!showingAll && (
          <span className="sr-header__limit">Showing first {limit}</span>
        )}
      </div>

      {/* No-content warning banner (some results but extracted is 0) */}
      {searchMode === 'all' && !hasExtractedContent && (
        <div className="sr-no-content-banner">
          <ExtractIcon />
          <span>
            Content search is inactive — run <strong>Content Extraction</strong> to also search inside files.
          </span>
        </div>
      )}

      {/* Result cards */}
      <ul className="sr-list" role="list">
        {results.map((file) => (
          <ResultCard key={file.id} file={file} />
        ))}
      </ul>

      {/* Footer: load-more placeholder */}
      {!showingAll && (
        <div className="sr-load-more">
          <span className="sr-load-more__text">
            Showing {results.length} of {total.toLocaleString()} results
          </span>
          <button 
            className="sr-load-more__btn" 
            onClick={onLoadMore}
            disabled={loadingMore}
          >
            {loadingMore ? "Loading..." : "Load more"}
          </button>
        </div>
      )}

    </section>
  );
}

/* ── File Icon SVG helper ────────────────────────────────── */
function FileIcon({ extRaw, color }) {
  // A clean, simple file icon
  return (
    <div className="file-icon-box" style={{ '--icon-color': color }}>
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
      </svg>
      <span className="file-icon-ext">{extRaw.substring(0, 4)}</span>
    </div>
  );
}

/* ── ResultCard ───────────────────────────────────────────── */

function ResultCard({ file }) {
  const extRaw  = (file.extension || '').toLowerCase().replace('.', '');
  const color   = EXT_COLORS[extRaw] || EXT_COLORS.default;
  const score   = Math.round((file.score || 0) * 100);
  const matchType = file.match_type || 'metadata';
  
  // Format Date & Size
  const sizeKb = Math.round(file.size / 1024);
  const dateStr = file.modified_at ? new Date(file.modified_at * 1000).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' }) : 'Unknown date';
  
  // Parse tags
  const tagsStr = file.tags || '';
  const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(Boolean) : [];
  const displayTags = tags.slice(0, 3);
  const extraTags = tags.length > 3 ? tags.length - 3 : 0;

  const isMissing = file.status === 'missing';

  const handleOpenFile = async () => {
    if (!window.deepfind?.openFile) return alert('Desktop API not available. Please run inside the Electron app.');
    const res = await window.deepfind.openFile(file.path);
    if (!res.success) alert(`File could not be opened.\n${res.error}`);
  };

  const handleOpenFolder = async () => {
    if (!window.deepfind?.showInFolder) return alert('Desktop API not available. Please run inside the Electron app.');
    const res = await window.deepfind.showInFolder(file.path);
    if (!res.success) alert(`Unable to open folder.\n${res.error}`);
  };

  return (
    <li className={`result-card result-card--${matchType} ${isMissing ? 'result-card--missing' : ''}`} role="listitem">
      
      {/* Top Row: Icon, Filename, Match Badge, Actions */}
      <div className="result-card__header">
        <FileIcon extRaw={extRaw} color={color} />
        
        <div className="result-card__titles">
          <h3 className="result-card__name" title={file.name}>
            {file.name}
          </h3>
          <p className="result-card__path" title={file.path}>
            {file.path}
          </p>
        </div>

        <div className="result-card__badges">
          {file.match_type === 'exact_name' && <span className="minimal-badge badge-exact">Exact Match</span>}
          {file.match_type === 'content'    && <span className="minimal-badge badge-content">Content Match</span>}
          {file.match_type === 'semantic'   && <span className="minimal-badge badge-semantic">Semantic</span>}
        </div>

        <div className="result-card__actions">
          <button className="action-icon-btn" onClick={handleOpenFolder} title="Show in folder" aria-label="Show in folder">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
            </svg>
          </button>
          <button className="action-icon-btn" onClick={handleOpenFile} title="Open file" aria-label="Open file">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
              <polyline points="15 3 21 3 21 9"></polyline>
              <line x1="10" y1="14" x2="21" y2="3"></line>
            </svg>
          </button>
        </div>
      </div>

      {/* Main body (Snippet) */}
      <div className="result-card__body">
        {/* Snippet Preview */}
        {(file.match_type === 'content' || file.match_type === 'semantic' || file.snippet) && (
          <p className="result-card__snippet" dir="auto">
            {renderHighlightedText(file.snippet)}
          </p>
        )}

        {/* Tags */}
        {tags.length > 0 && (
          <div className="result-card__tags">
            {displayTags.map(tag => <span key={tag} className="tag-pill">{tag}</span>)}
            {extraTags > 0 && <span className="tag-pill tag-pill--more">+{extraTags}</span>}
          </div>
        )}
      </div>

      {/* Footer Metadata */}
      <div className="result-card__footer">
        {sizeKb} KB · {dateStr} · {file.match_type === 'exact_name' ? 'Exact name' : file.match_type === 'content' ? 'Phrase in content' : file.match_type === 'semantic' ? 'Semantic meaning' : 'Name/Path match'}
        {isMissing && <span className="missing-alert"> · Missing File</span>}
      </div>

    </li>
  );
}

/* ── MatchTypeBadge ───────────────────────────────────────── */

function MatchTypeBadge({ type }) {
  const config = {
    exact_name:    { label: 'Exact match',      cls: 'badge--meta' },
    name:          { label: 'Name match',       cls: 'badge--meta' },
    app:           { label: 'App match',        cls: 'badge--meta' },
    folder:        { label: 'Folder match',     cls: 'badge--meta' },
    path:          { label: 'Path match',       cls: 'badge--meta' },
    tag:           { label: 'Tag match',        cls: 'badge--meta' },
    content:       { label: 'Content match',    cls: 'badge--content' },
    semantic:      { label: 'Semantic match',   cls: 'badge--semantic' },
    hybrid:        { label: 'Hybrid match',     cls: 'badge--hybrid' },
    metadata:      { label: 'Name match',       cls: 'badge--meta' }, // fallback
  };
  const { label, cls } = config[type] || config.metadata;
  return (
    <span className={`match-type-badge ${cls}`} aria-label={label}>
      {label}
    </span>
  );
}

/* ── MetaChip ─────────────────────────────────────────────── */

function MetaChip({ icon, label }) {
  return (
    <span className="result-card__meta-chip">
      <span className="meta-chip__icon" aria-hidden="true">{icon}</span>
      {label}
    </span>
  );
}

/* ── Helpers ──────────────────────────────────────────────── */

function formatDate(dateStr) {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  } catch {
    return dateStr;
  }
}

/** Map extensions to accent colours */
const EXT_COLORS = {
  '.pdf':  '#ef4444',
  '.doc':  '#3b82f6', '.docx': '#3b82f6',
  '.xls':  '#22c55e', '.xlsx': '#22c55e',
  '.ppt':  '#f97316', '.pptx': '#f97316',
  '.jpg':  '#ec4899', '.jpeg': '#ec4899', '.png': '#ec4899', '.gif': '#ec4899', '.webp': '#ec4899',
  '.mp4':  '#a855f7', '.mov': '#a855f7', '.avi': '#a855f7', '.mkv': '#a855f7',
  '.mp3':  '#8b5cf6', '.wav': '#8b5cf6', '.flac': '#8b5cf6',
  '.zip':  '#f59e0b', '.rar': '#f59e0b', '.7z': '#f59e0b',
  '.js':   '#facc15', '.ts': '#3b82f6', '.jsx': '#61dafb', '.tsx': '#61dafb',
  '.py':   '#60a5fa',
  '.html': '#f97316', '.css': '#a78bfa',
  '.sql':  '#34d399',
  '.txt':  '#94a3b8',
  '.md':   '#94a3b8',
  default: '#6366f1',
};

/* ── Inline SVG Icons ─────────────────────────────────────── */

function ErrorIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  );
}

function EmptyIcon() {
  return (
    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
      <line x1="8" y1="11" x2="14" y2="11" />
    </svg>
  );
}

function ExtractIcon() {
  return (
    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
    </svg>
  );
}

function SizeIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  );
}

function CalIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  );
}

function OpenFileIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
      <polyline points="15 3 21 3 21 9" />
      <line x1="10" y1="14" x2="21" y2="3" />
    </svg>
  );
}

function FolderIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
    </svg>
  );
}

export default SearchResults;
