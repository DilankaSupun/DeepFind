import React, { useState, useCallback, useRef } from 'react';
import logoImg from '../../assets/logo.png';
import SearchInput from './SearchInput.jsx';
import SearchModeSelector from './SearchModeSelector.jsx';
import ResultsToolbar from './ResultsToolbar.jsx';
import ResultRow from './ResultRow.jsx';
import ResultDetailsPane from './ResultDetailsPane.jsx';
import { SearchEmptyState, SearchNoResults, SearchErrorState, SearchLoadingState } from './SearchStates.jsx';
import { searchFiles } from '../../services/api.js';
import './SearchWorkspace.css';

export default function SearchWorkspace({ engineStatus }) {
  const engineOnline = engineStatus === 'online';

  const [searchState, setSearchState]   = useState('idle'); // idle, loading, results, empty, error
  const [searchQuery,  setSearchQuery]  = useState('');
  const [searchMode,   setSearchMode]   = useState('all');
  const [results, setResults]           = useState([]);
  const [total, setTotal]               = useState(0);
  const [error, setError]               = useState(null);
  
  const [selectedResultId, setSelectedResultId] = useState(null);
  const searchRequestId = useRef(0);
  const LIMIT = 50;

  const handleSearch = useCallback(async (query, mode = searchMode) => {
    setSearchQuery(query);
    setSearchMode(mode);
    setSearchState('loading');
    setError(null);
    setSelectedResultId(null);

    const currentReqId = ++searchRequestId.current;

    try {
      const data = await searchFiles(query, { limit: LIMIT, offset: 0, searchType: mode });
      if (currentReqId !== searchRequestId.current) return;
      
      setResults(data.results || []);
      setTotal(data.total || 0);
      setSearchState((data.results || []).length === 0 ? 'empty' : 'results');
      
      // Auto-select first result if any
      if (data.results?.length > 0) {
        setSelectedResultId(data.results[0].id);
      }
    } catch (err) {
      if (currentReqId !== searchRequestId.current) return;
      setError(err.message || 'Backend unreachable');
      setResults([]);
      setTotal(0);
      setSearchState('error');
    }
  }, [searchMode]);

  const handleClear = useCallback(() => {
    setSearchState('idle');
    setSearchQuery('');
    setResults([]);
    setTotal(0);
    setError(null);
    setSelectedResultId(null);
  }, []);

  const selectedResult = results.find(r => r.id === selectedResultId);

  return (
    <div className="search-workspace">
      
      {/* ── Search Header (Sticky Area) ── */}
      <div className="search-header-sticky">
        {searchState === 'idle' ? (
          <div className="search-intro">
            <div className="search-intro-logo">
              <img src={logoImg} alt="DeepFind" style={{ width: '64px', height: '64px', objectFit: 'contain' }} />
            </div>
            <h2>Find anything on this computer</h2>
            <p>Search by name, text, location, type, or meaning</p>
            <div className="search-intro-inputs">
              <SearchInput 
                value={searchQuery} 
                onChange={setSearchQuery} 
                onSearch={() => handleSearch(searchQuery)} 
                onClear={handleClear}
                loading={searchState === 'loading'}
                disabled={!engineOnline}
              />
              <SearchModeSelector mode={searchMode} onChange={(m) => { setSearchMode(m); if(searchQuery) handleSearch(searchQuery, m); }} disabled={!engineOnline} />
            </div>
          </div>
        ) : (
          <div className="search-compact-header">
            <div className="search-compact-row">
              <SearchInput 
                value={searchQuery} 
                onChange={setSearchQuery} 
                onSearch={() => handleSearch(searchQuery)} 
                onClear={handleClear}
                loading={searchState === 'loading'}
                disabled={!engineOnline}
              />
            </div>
            <div className="search-compact-row">
              <SearchModeSelector mode={searchMode} onChange={(m) => { setSearchMode(m); handleSearch(searchQuery, m); }} disabled={!engineOnline} />
              <div className="search-compact-status">
                <div className={`status-dot ${engineOnline ? 'status-dot--ready' : 'status-dot--error'}`} />
                <span>{engineOnline ? 'Engine ready' : 'Engine offline'}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Search Content Area ── */}
      <div className="search-content">
        {searchState === 'idle' && <SearchEmptyState onExampleClick={(q) => handleSearch(q, 'all')} />}
        {searchState === 'loading' && <SearchLoadingState />}
        {searchState === 'error' && <SearchErrorState error={error} onRetry={() => handleSearch(searchQuery)} />}
        {searchState === 'empty' && <SearchNoResults query={searchQuery} mode={searchMode} />}
        
        {searchState === 'results' && (
          <div className="search-results-grid">
            
            {/* List Column */}
            <div className="search-list-column">
              <ResultsToolbar count={total} query={searchQuery} showing={results.length} />
              <div className="search-list" role="list">
                {results.map(file => (
                  <ResultRow 
                    key={file.id} 
                    file={file} 
                    isSelected={selectedResultId === file.id}
                    onSelect={() => setSelectedResultId(file.id)}
                  />
                ))}
              </div>
            </div>

            {/* Details Pane Column */}
            <div className="search-details-column">
              {selectedResult ? (
                <ResultDetailsPane file={selectedResult} />
              ) : (
                <div className="search-details-empty">
                  Select a result to see details
                </div>
              )}
            </div>

          </div>
        )}
      </div>
    </div>
  );
}
