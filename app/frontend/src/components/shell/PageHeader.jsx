import React from 'react';

function PageHeader({ title, description, children }) {
  return (
    <div className="page-header">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">{title}</h1>
          {description && <p className="page-desc">{description}</p>}
        </div>
        {children && <div className="page-actions">{children}</div>}
      </div>
    </div>
  );
}

export default PageHeader;
