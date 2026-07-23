import React from 'react';
import logoImg from '../../assets/logo.png';
import { 
  Search20Regular, Search20Filled,
  Library20Regular, Library20Filled,
  History20Regular, History20Filled,
  Desktop20Regular, Desktop20Filled,
  Settings20Regular, Settings20Filled,
  PanelLeftExpand20Regular,
  PanelRightExpand20Regular
} from '@fluentui/react-icons';

function NavigationRail({ activePage, onChangePage, isCollapsed, onToggleCollapse, engineStatus }) {
  const isReady = engineStatus === 'online';

  const navItems = [
    { id: 'search', label: 'Search', iconReg: <Search20Regular />, iconFilled: <Search20Filled /> },
    { id: 'library', label: 'Library', iconReg: <Library20Regular />, iconFilled: <Library20Filled /> },
    { id: 'activity', label: 'Activity', iconReg: <History20Regular />, iconFilled: <History20Filled /> },
    { id: 'system', label: 'System', iconReg: <Desktop20Regular />, iconFilled: <Desktop20Filled /> },
    { id: 'settings', label: 'Settings', iconReg: <Settings20Regular />, iconFilled: <Settings20Filled /> },
  ];

  return (
    <nav className={`nav-rail ${isCollapsed ? 'nav-rail--collapsed' : ''}`} aria-label="Main Navigation">
      <div className="nav-top">
        <button 
          className="nav-item" 
          onClick={onToggleCollapse} 
          title={isCollapsed ? "Expand navigation" : "Collapse navigation"}
          style={{ width: '40px', padding: '0 10px', flexShrink: 0 }}
        >
          <div className="nav-icon">
            {isCollapsed ? <PanelRightExpand20Regular /> : <PanelLeftExpand20Regular />}
          </div>
        </button>
        <div className="nav-logo" aria-hidden="true">
          <img src={logoImg} alt="DeepFind" style={{ width: '24px', height: '24px', objectFit: 'contain' }} />
        </div>
        <div className="nav-wordmark">DeepFind</div>
      </div>

      <div className="nav-items">
        {navItems.map((item) => {
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? 'nav-item--active' : ''}`}
              onClick={() => onChangePage(item.id)}
              title={isCollapsed ? item.label : undefined}
            >
              <div className="nav-icon">
                {isActive ? item.iconFilled : item.iconReg}
              </div>
              <span className="nav-label">{item.label}</span>
            </button>
          );
        })}
      </div>

      <div className="nav-bottom">
        <div className="nav-status" title={isReady ? "Engine ready" : "Engine offline"}>
          <div className={`status-dot ${isReady ? 'status-dot--ready' : 'status-dot--error'}`} />
          <span className="nav-status-text">{isReady ? 'Engine ready' : 'Engine offline'}</span>
        </div>
        <div className="nav-version">Local only · v0.1.0</div>
      </div>
    </nav>
  );
}

export default NavigationRail;
