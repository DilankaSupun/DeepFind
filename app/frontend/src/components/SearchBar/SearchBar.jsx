import React, { useState, useRef } from 'react';
import './SearchBar.css';

/**
 * SearchBar — Step 10: Added search mode selector.
 *
 * Props:
 *   onSearch(query, mode) — called when user submits
 *   onClear()             — called when X is clicked
 *   loading               — bool, show spinner on button
 *   hasResults            — bool, show clear state
 *   engineOnline          — bool, disable when offline
 */
function SearchBar({ onSearch, onClear, loading = false, hasResults = false, engineOnline = true }) {
  const [value,    setValue]    = useState('');
  const [mode,     setMode]     = useState('all'); // 'all' | 'metadata' | 'content'
  const inputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    const q = value.trim();
    if (!q || loading) return;
    onSearch?.(q, mode);
  };

  const handleClear = () => {
    setValue('');
    onClear?.();
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') handleClear();
  };

  const placeholder = engineOnline
    ? mode === 'content'
      ? 'Search inside file contents…'
      : mode === 'metadata'
      ? 'Search by filename, extension, or path…'
      : 'Search files by name, content, or path…'
    : 'Start the engine to enable search';

  return (
    <form className="searchbar-form" onSubmit={handleSubmit} role="search">

      {/* Mode selector pills */}
      <div className="searchbar-modes" role="group" aria-label="Search mode">
        {MODES.map((m) => (
          <button
            key={m.value}
            type="button"
            className={`searchbar-mode-btn ${mode === m.value ? 'searchbar-mode-btn--active' : ''}`}
            onClick={() => setMode(m.value)}
            disabled={!engineOnline || loading}
            aria-pressed={mode === m.value}
            id={`search-mode-${m.value}`}
          >
            <span className="mode-icon" aria-hidden="true">{m.icon}</span>
            {m.label}
          </button>
        ))}
      </div>

      <div className={`searchbar-wrapper ${loading ? 'searchbar-wrapper--loading' : ''}`}>

        {/* Search / spinner icon */}
        <span className="searchbar-icon" aria-hidden="true">
          {loading ? (
            <span className="searchbar-spinner" />
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          )}
        </span>

        {/* Input */}
        <input
          ref={inputRef}
          id="main-search-input"
          className="searchbar-input"
          type="text"
          placeholder={placeholder}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          autoComplete="off"
          spellCheck={false}
          disabled={!engineOnline || loading}
        />

        {/* Clear button */}
        {(value || hasResults) && (
          <button
            type="button"
            className="searchbar-clear"
            onClick={handleClear}
            aria-label="Clear search"
            tabIndex={0}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        )}

        {/* Submit button */}
        <button
          type="submit"
          className="searchbar-submit"
          aria-label="Search"
          disabled={!engineOnline || loading || !value.trim()}
          title={!engineOnline ? 'Start the engine first' : ''}
        >
          {loading ? 'Searching…' : 'Search'}
        </button>
      </div>

      <p className="searchbar-hint">
        Press <kbd>Enter</kbd> to search ·{' '}
        {mode === 'content'
          ? <>Try: <em>payment</em>, <em>database</em>, <em>function</em></>
          : mode === 'metadata'
          ? <>Try: <em>pdf</em>, <em>cv</em>, <em>.docx</em>, <em>screenshot</em></>
          : <>Try: <em>payment</em>, <em>pdf</em>, <em>cv</em>, <em>database</em></>}
      </p>
    </form>
  );
}

/* ── Mode definitions ─────────────────────────────────────── */

const MODES = [
  {
    value: 'all',
    label: 'All',
    icon: (
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
    ),
  },
  {
    value: 'metadata',
    label: 'Name / Path',
    icon: (
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
      </svg>
    ),
  },
  {
    value: 'content',
    label: 'Content',
    icon: (
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <line x1="8" y1="6" x2="21" y2="6" /><line x1="8" y1="12" x2="21" y2="12" /><line x1="8" y1="18" x2="21" y2="18" />
        <line x1="3" y1="6" x2="3.01" y2="6" /><line x1="3" y1="12" x2="3.01" y2="12" /><line x1="3" y1="18" x2="3.01" y2="18" />
      </svg>
    ),
  },
];

export default SearchBar;
