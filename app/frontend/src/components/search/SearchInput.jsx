import React, { useRef, useEffect } from 'react';
import { Search20Regular, Dismiss20Regular } from '@fluentui/react-icons';

export default function SearchInput({ value, onChange, onSearch, onClear, loading, disabled }) {
  const inputRef = useRef(null);

  useEffect(() => {
    const handleGlobalKeyDown = (e) => {
      // Ctrl+L to focus
      if (e.ctrlKey && e.key === 'l') {
        e.preventDefault();
        inputRef.current?.focus();
        inputRef.current?.select();
      }
      // '/' to focus if not in input
      if (e.key === '/' && document.activeElement !== inputRef.current && document.activeElement?.tagName !== 'INPUT') {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, []);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      onSearch();
    }
    if (e.key === 'Escape') {
      e.preventDefault();
      onClear();
      inputRef.current?.blur();
    }
  };

  return (
    <div className={`search-input-wrapper ${loading ? 'is-loading' : ''} ${disabled ? 'is-disabled' : ''}`}>
      <div className="search-input-icon">
        {loading ? <div className="spinner-small" /> : <Search20Regular />}
      </div>
      
      <input
        ref={inputRef}
        type="text"
        className="search-input-field"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Search files by name, content, or path..."
        disabled={disabled}
        spellCheck={false}
        autoComplete="off"
      />
      
      {value && (
        <button className="search-input-clear" onClick={onClear} aria-label="Clear search">
          <Dismiss20Regular />
        </button>
      )}
      
      <button 
        className="search-input-btn" 
        onClick={onSearch} 
        disabled={disabled || !value.trim() || loading}
      >
        Search
      </button>
    </div>
  );
}
