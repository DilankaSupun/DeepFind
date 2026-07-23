import React from 'react';

const MODES = [
  { value: 'all', label: 'All' },
  { value: 'metadata', label: 'Name / path' },
  { value: 'content', label: 'Content' },
  { value: 'semantic', label: 'Semantic' }
];

export default function SearchModeSelector({ mode, onChange, disabled }) {
  return (
    <div className={`search-mode-selector ${disabled ? 'is-disabled' : ''}`} role="group" aria-label="Search modes">
      {MODES.map(m => (
        <button
          key={m.value}
          className={`mode-segment ${mode === m.value ? 'is-active' : ''}`}
          onClick={() => onChange(m.value)}
          disabled={disabled}
          aria-pressed={mode === m.value}
        >
          {m.label}
        </button>
      ))}
    </div>
  );
}
