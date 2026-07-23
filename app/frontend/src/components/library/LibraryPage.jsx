import React, { useState } from 'react';
import PageHeader from '../shell/PageHeader.jsx';
import ScanScopePanel from '../ScanScopePanel/ScanScopePanel.jsx';
import ExtractionPanel from '../ExtractionPanel/ExtractionPanel.jsx';
import TaggingPanel from '../TaggingPanel/TaggingPanel.jsx';
import SemanticPanel from '../SemanticPanel/SemanticPanel.jsx';
import IndexingPanel from '../IndexingPanel/IndexingPanel.jsx';
import './LibraryPage.css';

export default function LibraryPage({ status }) {
  const [maintenanceOpen, setMaintenanceOpen] = useState(false);

  return (
    <>
      <PageHeader 
        title="Search library" 
        description="Manage indexed locations and search-processing data." 
      />
      
      <div className="page-content page-content-constrained library-page">
        
        {/* Section 1: Search Coverage */}
        <div className="library-section">
          <h2 className="library-section-title">Search Coverage</h2>
          <div className="library-card">
            <ScanScopePanel engineStatus={status} hideHeader />
          </div>
        </div>

        {/* Section 2: Maintenance Tools */}
        <div className="library-section">
          <button 
            className="maintenance-toggle-btn" 
            onClick={() => setMaintenanceOpen(!maintenanceOpen)}
            aria-expanded={maintenanceOpen}
          >
            <span className="maintenance-toggle-icon">
              {maintenanceOpen ? '▼' : '▶'}
            </span>
            Maintenance tools
          </button>
          
          {maintenanceOpen && (
            <div className="maintenance-content">
              <p className="maintenance-note">
                DeepFind normally performs these tasks automatically. Manual tools are intended for troubleshooting or forced reprocessing.
              </p>
              <div className="maintenance-panels-grid">
                <div className="library-card">
                  <IndexingPanel engineStatus={status} />
                </div>
                <div className="library-card">
                  <ExtractionPanel engineStatus={status} />
                </div>
                <div className="library-card">
                  <TaggingPanel engineStatus={status} />
                </div>
                <div className="library-card">
                  <SemanticPanel engineStatus={status} />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
