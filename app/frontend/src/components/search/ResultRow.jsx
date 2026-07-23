import React from 'react';
import { Document20Regular, Folder20Regular, Open20Regular, FolderOpen20Regular, DocumentText20Regular, DocumentPdf20Regular, Code20Regular, Image20Regular, Video20Regular } from '@fluentui/react-icons';

function getFileIcon(extension) {
  const ext = (extension || '').toLowerCase();
  switch(ext) {
    case 'pdf': return <DocumentPdf20Regular style={{ color: '#ef737d' }} />;
    case 'txt': case 'md': case 'csv': case 'log': return <DocumentText20Regular style={{ color: '#60a5fa' }} />;
    case 'js': case 'jsx': case 'py': case 'json': case 'html': case 'css': return <Code20Regular style={{ color: '#8278f8' }} />;
    case 'jpg': case 'jpeg': case 'png': case 'gif': case 'svg': return <Image20Regular style={{ color: '#5ecdb3' }} />;
    case 'mp4': case 'mkv': case 'avi': return <Video20Regular style={{ color: '#8278f8' }} />;
    default: return <Document20Regular style={{ color: 'var(--df-text-tertiary)' }} />;
  }
}

function getMatchBadge(matchType) {
  switch(matchType) {
    case 'exact_name': return <span className="match-badge match-badge--exact">Exact match</span>;
    case 'name': return <span className="match-badge match-badge--exact">Name match</span>;
    case 'content': return <span className="match-badge match-badge--content">Content match</span>;
    case 'semantic': return <span className="match-badge match-badge--semantic">Semantic match</span>;
    case 'path': return <span className="match-badge match-badge--folder">Folder match</span>;
    default: return null;
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

export default function ResultRow({ file, isSelected, onSelect }) {
  const sizeKb = file.size ? Math.round(file.size / 1024) : 0;
  const dateStr = file.modified_at ? new Date(file.modified_at).toLocaleDateString() : 'Unknown date';
  
  const handleOpen = (e) => {
    e.stopPropagation();
    if (window.deepfind?.openFile) {
      window.deepfind.openFile(file.path);
    }
  };

  const handleOpenFolder = (e) => {
    e.stopPropagation();
    if (window.deepfind?.showInFolder) {
      window.deepfind.showInFolder(file.path);
    }
  };

  return (
    <div 
      className={`result-row ${isSelected ? 'is-selected' : ''}`}
      onClick={onSelect}
      onDoubleClick={handleOpen}
      tabIndex={0}
      role="option"
      aria-selected={isSelected}
      onKeyDown={(e) => { if(e.key === 'Enter') handleOpen(e); }}
    >
      <div className="result-row-indicator" />
      
      <div className="result-row-icon">
        {file.type === 'directory' ? <Folder20Regular style={{ color: '#efc461' }} /> : getFileIcon(file.extension)}
      </div>

      <div className="result-row-content">
        <div className="result-row-header">
          <span className="result-row-name" title={file.name}>{file.name}</span>
          <div className="result-row-badges">
            {getMatchBadge(file.match_type)}
          </div>
          <div className="result-row-actions">
            <button className="row-action-btn" onClick={handleOpenFolder} title="Show in folder">
              <FolderOpen20Regular />
            </button>
            <button className="row-action-btn--text" onClick={handleOpen}>Open</button>
          </div>
        </div>

        <div className="result-row-path" title={file.path}>{file.path}</div>

        {(file.match_type === 'content' || file.match_type === 'semantic') && file.snippet && (
          <div className="result-row-snippet">
            <div className="snippet-indicator" />
            <p>{renderHighlightedText(file.snippet)}</p>
          </div>
        )}

        <div className="result-row-meta">
          {sizeKb} KB · {dateStr}
          {file.tags && (
            <>
              <span className="meta-dot">·</span>
              <div className="result-row-tags">
                {file.tags.split(',').slice(0, 2).map((t, i) => (
                  <span key={i} className="row-tag">{t}</span>
                ))}
                {file.tags.split(',').length > 2 && (
                  <span className="row-tag">+{file.tags.split(',').length - 2}</span>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
