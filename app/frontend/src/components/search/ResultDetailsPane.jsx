import React from 'react';
import { Open20Regular, FolderOpen20Regular, Document20Regular, Folder20Regular, DocumentText20Regular, DocumentPdf20Regular, Code20Regular, Image20Regular, Video20Regular, Copy20Regular } from '@fluentui/react-icons';

function getFileIcon(extension, isDir) {
  if (isDir) return <Folder20Regular style={{ color: '#efc461', width: 48, height: 48 }} />;
  const ext = (extension || '').toLowerCase();
  switch(ext) {
    case 'pdf': return <DocumentPdf20Regular style={{ color: '#ef737d', width: 48, height: 48 }} />;
    case 'txt': case 'md': case 'csv': case 'log': return <DocumentText20Regular style={{ color: '#60a5fa', width: 48, height: 48 }} />;
    case 'js': case 'jsx': case 'py': case 'json': case 'html': case 'css': return <Code20Regular style={{ color: '#8278f8', width: 48, height: 48 }} />;
    case 'jpg': case 'jpeg': case 'png': case 'gif': case 'svg': return <Image20Regular style={{ color: '#5ecdb3', width: 48, height: 48 }} />;
    case 'mp4': case 'mkv': case 'avi': return <Video20Regular style={{ color: '#8278f8', width: 48, height: 48 }} />;
    default: return <Document20Regular style={{ color: 'var(--df-text-tertiary)', width: 48, height: 48 }} />;
  }
}

function renderHighlightedText(text) {
  if (!text) return null;
  const parts = text.split(/\[\[HL\]\](.*?)\[\[\/HL\]\]/g);
  return parts.map((part, index) => {
    if (index % 2 === 1) return <mark key={index}>{part}</mark>;
    return <span key={index}>{part}</span>;
  });
}

export default function ResultDetailsPane({ file }) {
  const sizeKb = file.size ? Math.round(file.size / 1024) : 0;
  const dateStr = file.modified_at ? new Date(file.modified_at).toLocaleString() : 'Unknown date';

  const handleOpen = () => {
    if (window.deepfind?.openFile) window.deepfind.openFile(file.path);
  };

  const handleOpenFolder = () => {
    if (window.deepfind?.showInFolder) window.deepfind.showInFolder(file.path);
  };

  const handleCopyPath = () => {
    navigator.clipboard.writeText(file.path);
  };

  return (
    <div className="result-details-pane">
      <div className="details-header">
        <div className="details-icon-large">
          {getFileIcon(file.extension, file.type === 'directory')}
        </div>
        <h3 className="details-filename" title={file.name}>{file.name}</h3>
        <p className="details-match-reason">
          {file.match_type === 'exact_name' ? 'Exact filename match'
          : file.match_type === 'name' ? 'Filename matched'
          : file.match_type === 'content' ? 'Exact phrase found in content'
          : file.match_type === 'semantic' ? 'Related by meaning'
          : file.match_type === 'path' ? 'Folder matched'
          : 'Matched search'}
        </p>
      </div>

      <div className="details-actions">
        <button className="ui-btn ui-btn--primary details-action-btn" onClick={handleOpen}>
          <Open20Regular /> Open
        </button>
        <button className="ui-btn ui-btn--secondary details-action-btn" onClick={handleOpenFolder}>
          <FolderOpen20Regular /> Show in folder
        </button>
      </div>

      <div className="details-section">
        <div className="details-label">Location</div>
        <div className="details-path-box">
          <span className="details-path-text" title={file.path}>{file.path}</span>
          <button className="copy-path-btn" onClick={handleCopyPath} title="Copy path" aria-label="Copy path">
            <Copy20Regular />
          </button>
        </div>
      </div>

      {(file.match_type === 'content' || file.match_type === 'semantic') && file.snippet && (
        <div className="details-section">
          <div className="details-label">
            {file.match_type === 'semantic' ? 'Semantic Preview' : 'Content Preview'}
          </div>
          <div className="details-snippet-box">
            {renderHighlightedText(file.snippet)}
          </div>
        </div>
      )}

      <div className="details-section">
        <div className="details-label">Information</div>
        <div className="details-info-grid">
          <div className="info-cell">
            <span className="info-key">Size</span>
            <span className="info-value">{sizeKb} KB</span>
          </div>
          <div className="info-cell">
            <span className="info-key">Modified</span>
            <span className="info-value">{dateStr}</span>
          </div>
          <div className="info-cell">
            <span className="info-key">Type</span>
            <span className="info-value">{file.extension ? file.extension.toUpperCase() : file.type}</span>
          </div>
        </div>
      </div>

      {file.tags && (
        <div className="details-section">
          <div className="details-label">Tags</div>
          <div className="details-tags-list">
            {file.tags.split(',').map((t, i) => (
              <span key={i} className="details-tag">{t.trim()}</span>
            ))}
          </div>
        </div>
      )}

      <div className="details-footer">
        Local-first · No cloud uploads
      </div>
    </div>
  );
}
