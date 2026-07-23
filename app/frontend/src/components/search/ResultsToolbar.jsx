import React from 'react';

export default function ResultsToolbar({ count, query, showing }) {
  return (
    <div className="results-toolbar">
      <div className="results-toolbar-left">
        <strong>{count.toLocaleString()} results</strong>
        {query && <span>for "{query}"</span>}
      </div>
      <div className="results-toolbar-right">
        <span>Showing {showing}</span>
      </div>
    </div>
  );
}
