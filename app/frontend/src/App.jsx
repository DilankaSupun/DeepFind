import React, { useState, useEffect } from 'react';
import NavigationRail from './components/shell/NavigationRail.jsx';
import PageHeader from './components/shell/PageHeader.jsx';
import ErrorBoundary from './components/ErrorBoundary/ErrorBoundary.jsx';

import SearchWorkspace from './components/search/SearchWorkspace.jsx';
import LibraryPage from './components/library/LibraryPage.jsx';
import ActivityPage from './components/activity/ActivityPage.jsx';
import SystemPage from './components/system/SystemPage.jsx';
import SettingsPage from './components/settings/SettingsPage.jsx';

import { useEngineStatus } from './hooks/useEngineStatus.js';

function App() {
  const { status, version } = useEngineStatus();
  
  // Navigation State
  const [activePage, setActivePage] = useState('search');
  const [navCollapsed, setNavCollapsed] = useState(window.innerWidth <= 1050);

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth <= 1050) setNavCollapsed(true);
      else setNavCollapsed(false);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div className="app-shell">
      <NavigationRail 
        activePage={activePage} 
        onChangePage={setActivePage} 
        isCollapsed={navCollapsed}
        onToggleCollapse={() => setNavCollapsed(!navCollapsed)}
        engineStatus={status}
      />

      <main className="main-view" role="main">
        {activePage === 'search' && <SearchWorkspace engineStatus={status} />}
        {activePage === 'library' && <LibraryPage status={status} />}
        {activePage === 'activity' && <ActivityPage />}
        {activePage === 'system' && <SystemPage />}
        {activePage === 'settings' && <SettingsPage />}
      </main>
    </div>
  );
}

export default App;
