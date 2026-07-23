import React from 'react';
import { Search20Regular, DocumentSearch20Regular, ErrorCircle20Regular, SpinnerIos20Regular } from '@fluentui/react-icons';

export function SearchEmptyState({ onExampleClick }) {
  return (
    <div className="search-state search-state-empty">
      <div className="search-state-icon">
        <DocumentSearch20Regular />
      </div>
      <h3>Find anything on this computer</h3>
      <p>Search by filename, text inside documents, folder, file type, or meaning.</p>
      
      <div className="search-examples">
        <button className="example-btn" onClick={() => onExampleClick('report.pdf')}>report.pdf</button>
        <button className="example-btn" onClick={() => onExampleClick('files in Downloads')}>files in Downloads</button>
        <button className="example-btn" onClick={() => onExampleClick('payment gateway')}>payment gateway</button>
        <button className="example-btn" onClick={() => onExampleClick('videos from 2025')}>videos from 2025</button>
      </div>
    </div>
  );
}

export function SearchNoResults({ query, mode }) {
  return (
    <div className="search-state search-state-no-results">
      <div className="search-state-icon">
        <Search20Regular />
      </div>
      <h3>No matching files</h3>
      <p>
        {mode === 'semantic' ? `No files semantically match "${query}". Try a different concept.`
        : mode === 'content' ? `No file content matches "${query}". Try a shorter word.`
        : `No indexed files match "${query}". Try fewer words or check spelling.`}
      </p>
    </div>
  );
}

export function SearchErrorState({ error, onRetry }) {
  return (
    <div className="search-state search-state-error">
      <div className="search-state-icon" style={{ color: 'var(--df-danger)' }}>
        <ErrorCircle20Regular />
      </div>
      <h3>Search could not be completed</h3>
      <p>{error || 'The local DeepFind engine did not respond.'}</p>
      <button className="ui-btn ui-btn--secondary" onClick={onRetry} style={{ marginTop: '12px' }}>
        Try again
      </button>
    </div>
  );
}

export function SearchLoadingState() {
  return (
    <div className="search-state search-state-loading">
      <div className="spinner-large" />
      <p>Searching...</p>
    </div>
  );
}
