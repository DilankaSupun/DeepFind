import React, { useState, useEffect, useCallback } from 'react';
import {
  getAllFolders, discoverFolders, initializeDefaults,
  addFolder, toggleFolder, removeFolder,
} from '../../services/api.js';
import './FolderManager.css';

function FolderManager({ engineStatus }) {
  const [folders,      setFolders]      = useState([]);
  const [discovery,    setDiscovery]    = useState(null);
  const [loading,      setLoading]      = useState(true);
  const [initializing, setInitializing] = useState(false);
  const [toggling,     setToggling]     = useState(null);
  const [adding,       setAdding]       = useState(false);
  const [removing,     setRemoving]     = useState(null);
  const [error,        setError]        = useState(null);

  const isOffline = engineStatus !== 'online';

  const loadFolders = useCallback(async () => {
    if (isOffline) { setLoading(false); return; }
    try {
      const data = await getAllFolders();
      setFolders(data.folders ?? []);
      setError(null);
    } catch { setError('Could not load folders.'); }
    finally   { setLoading(false); }
  }, [isOffline]);

  const loadDiscovery = useCallback(async () => {
    if (isOffline) return;
    try { const d = await discoverFolders(); setDiscovery(d); } catch { /* silent */ }
  }, [isOffline]);

  useEffect(() => { loadFolders(); }, [loadFolders]);

  useEffect(() => {
    if (!loading && folders.length === 0 && !isOffline) loadDiscovery();
  }, [loading, folders.length, isOffline, loadDiscovery]);

  const handleSetupDefaults = async () => {
    setInitializing(true); setError(null);
    try { await initializeDefaults(); await loadFolders(); }
    catch (e) { setError('Setup failed: ' + e.message); }
    finally   { setInitializing(false); }
  };

  const handleToggle = async (folder) => {
    if (toggling) return;
    setToggling(folder.id);
    try {
      const data = await toggleFolder(folder.id);
      setFolders(prev => prev.map(f => f.id === folder.id ? data.folder : f));
    } catch (e) { setError('Toggle failed: ' + e.message); }
    finally     { setToggling(null); }
  };

  const handleAddFolder = async () => {
    if (!window.deepfind?.selectFolder) {
      setError('Folder picker only works in the Electron app.'); return;
    }
    setAdding(true); setError(null);
    try {
      const path = await window.deepfind.selectFolder();
      if (!path) return;
      await addFolder(path, 'manual');
      await loadFolders();
    } catch (e) { setError('Failed to add: ' + e.message); }
    finally     { setAdding(false); }
  };

  const handleRemove = async (folder) => {
    setRemoving(folder.id);
    try { await removeFolder(folder.id); setFolders(prev => prev.filter(f => f.id !== folder.id)); }
    catch (e) { setError('Remove failed: ' + e.message); }
    finally   { setRemoving(null); }
  };

  const commonFolders = folders.filter(f => f.source_type === 'auto_common_folder');
  const drives        = folders.filter(f => f.source_type === 'auto_drive');
  const custom        = folders.filter(f => f.source_type === 'manual' || !f.source_type);
  const activeCount   = folders.filter(f => f.is_active).length;
  const isInitialized = folders.length > 0;

  return (
    <section className="folder-manager" aria-label="Indexing sources">
      <div className="folder-manager__header">
        <div className="folder-manager__title-row">
          <FolderIcon />
          <h2 className="folder-manager__title">Indexing Sources</h2>
          {isInitialized && (
            <span className="folder-manager__count">{activeCount}/{folders.length} active</span>
          )}
        </div>
        {isInitialized && (
          <button className="fm-btn fm-btn--ghost" onClick={handleAddFolder} disabled={adding || isOffline}>
            {adding ? <Spinner /> : <PlusIcon />} {adding ? 'Selecting…' : 'Add Custom'}
          </button>
        )}
      </div>

      {error && (
        <div className="folder-manager__error" role="alert">
          <AlertIcon /><span>{error}</span>
          <button className="folder-manager__error-close" onClick={() => setError(null)}>×</button>
        </div>
      )}

      {isOffline ? (
        <div className="folder-manager__offline"><CloudOffIcon /> Start the engine to manage indexing sources</div>
      ) : loading ? (
        <div className="folder-manager__loading"><Spinner /> Loading sources…</div>
      ) : !isInitialized ? (
        <SetupPrompt
          discovery={discovery} initializing={initializing} adding={adding}
          onSetup={handleSetupDefaults} onAddManual={handleAddFolder}
        />
      ) : (
        <div className="source-groups">
          {commonFolders.length > 0 && (
            <SourceGroup title="Common Folders" subtitle="Your personal folders"
              folders={commonFolders} toggling={toggling} removing={removing}
              onToggle={handleToggle} onRemove={handleRemove} />
          )}
          {drives.length > 0 && (
            <SourceGroup title="Local Drives" subtitle="Full drives — large, inactive by default"
              folders={drives} toggling={toggling} removing={removing}
              onToggle={handleToggle} onRemove={handleRemove} isDriveGroup />
          )}
          {custom.length > 0 && (
            <SourceGroup title="Custom Folders" subtitle="Manually added"
              folders={custom} toggling={toggling} removing={removing}
              onToggle={handleToggle} onRemove={handleRemove} />
          )}
        </div>
      )}
    </section>
  );
}

function SetupPrompt({ discovery, initializing, adding, onSetup, onAddManual }) {
  const cc = discovery?.common_folders?.length ?? 0;
  const dc = discovery?.drives?.length ?? 0;
  return (
    <div className="setup-prompt">
      <div className="setup-prompt__icon"><ScanIcon /></div>
      <div className="setup-prompt__text">
        <p className="setup-prompt__title">Set up your indexing sources</p>
        <p className="setup-prompt__desc">
          DeepFind detected <strong>{cc} common folder{cc !== 1 ? 's' : ''}</strong>
          {dc > 0 && <> and <strong>{dc} drive{dc !== 1 ? 's' : ''}</strong></>} on this computer.
          Set them up to prepare for indexing.
        </p>
      </div>
      {discovery && (
        <div className="setup-prompt__preview">
          {discovery.common_folders?.map(f => (
            <span key={f.path} className={`preview-chip ${f.is_active_default ? 'preview-chip--active' : 'preview-chip--inactive'}`}>
              {f.is_active_default ? '✓' : '○'} {f.name}
            </span>
          ))}
          {discovery.drives?.map(f => (
            <span key={f.path} className="preview-chip preview-chip--inactive">○ {f.name}</span>
          ))}
        </div>
      )}
      <div className="setup-prompt__buttons">
        <button className="fm-btn fm-btn--primary" onClick={onSetup} disabled={initializing}>
          {initializing ? <><Spinner /> Setting up…</> : <><CheckIcon /> Setup Defaults</>}
        </button>
        <button className="fm-btn fm-btn--ghost" onClick={onAddManual} disabled={adding}>
          {adding ? <><Spinner /> Selecting…</> : <><PlusIcon /> Add Custom Folder</>}
        </button>
      </div>
    </div>
  );
}

function SourceGroup({ title, subtitle, folders, toggling, removing, onToggle, onRemove, isDriveGroup }) {
  return (
    <div className="source-group">
      <div className="source-group__header">
        <span className="source-group__title">{title}</span>
        <span className="source-group__subtitle">{subtitle}</span>
      </div>
      <ul className="folder-list" role="list">
        {folders.map(f => (
          <FolderRow key={f.id} folder={f}
            isToggling={toggling === f.id} isRemoving={removing === f.id}
            onToggle={() => onToggle(f)} onRemove={() => onRemove(f)}
            isDrive={isDriveGroup} />
        ))}
      </ul>
    </div>
  );
}

function FolderRow({ folder, isToggling, isRemoving, onToggle, onRemove, isDrive }) {
  const isActive = Boolean(folder.is_active);
  const segments = folder.folder_path?.replace(/\\/g, '/').split('/').filter(Boolean);
  const name = segments?.pop() ?? folder.folder_path;

  return (
    <li className={`folder-row ${!isActive ? 'folder-row--inactive' : ''} ${isRemoving ? 'folder-row--removing' : ''}`}>
      <div className={`folder-row__icon ${isDrive ? 'folder-row__icon--drive' : ''}`}>
        {isDrive ? <DriveIcon /> : <FolderFilledIcon />}
      </div>
      <div className="folder-row__info">
        <span className="folder-row__name">{name}</span>
        <span className="folder-row__path" title={folder.folder_path}>{folder.folder_path}</span>
      </div>
      <span className={`folder-row__badge ${isActive ? 'folder-row__badge--active' : 'folder-row__badge--inactive'}`}>
        {isActive ? 'Active' : 'Inactive'}
      </span>
      <label className="toggle-switch" title={isActive ? 'Disable' : 'Enable'}>
        <input type="checkbox" checked={isActive} onChange={onToggle} disabled={isToggling} />
        <span className={`toggle-slider ${isToggling ? 'toggle-slider--busy' : ''}`} />
      </label>
      <button className="folder-row__remove" onClick={onRemove} disabled={isRemoving || isToggling}
        aria-label={`Remove ${name}`} title="Remove">
        {isRemoving ? <Spinner size={10} /> : <TrashIcon />}
      </button>
    </li>
  );
}

function Spinner({ size = 12 }) {
  return <span className="fm-spinner" style={{ width: size, height: size }} aria-hidden="true" />;
}
function FolderIcon()      { return <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" /></svg>; }
function FolderFilledIcon(){ return <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>; }
function DriveIcon()       { return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>; }
function PlusIcon()        { return <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>; }
function TrashIcon()       { return <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/></svg>; }
function CheckIcon()       { return <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>; }
function AlertIcon()       { return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>; }
function ScanIcon()        { return <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><rect x="7" y="7" width="10" height="10" rx="1"/></svg>; }
function CloudOffIcon()    { return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><line x1="2" y1="2" x2="22" y2="22"/><path d="M5.782 5.782A7 7 0 0 0 9 19h8.5a4.5 4.5 0 0 0 1.307-.193"/><path d="M21.532 16.5A4.5 4.5 0 0 0 17.5 10h-1.79A7.008 7.008 0 0 0 10 5.07"/></svg>; }

export default FolderManager;
