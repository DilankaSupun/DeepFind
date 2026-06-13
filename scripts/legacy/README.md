# scripts/legacy/

Archived code that was superseded by a newer implementation.

These files are retained for reference only and are NOT used at runtime.

## Contents

### FolderManager/

Original React component (`FolderManager.jsx`) and its stylesheet (`FolderManager.css`).

This component was the original folder-selection UI from Step 6, which required
users to manually toggle indexed folders on/off.

It was superseded by the automated `ScanScopePanel` (Step 19), which uses an
exclusion-first model instead of explicit folder toggling.

**Why retained:**
- The `engine/api/routes/folders.py` backend routes are still registered in `server.py`
  because `db.py` migration code and `reset.py` still reference the `indexed_folders` table.
- The schema and backend are intact for backward compatibility.
- Deleting the frontend component is safe (it is not imported in `App.jsx`).

**Where the active code lives:**
- `app/frontend/src/components/ScanScopePanel/` — active replacement UI
- `engine/api/routes/scan_scope.py` — active replacement backend routes
- `engine/database/schema.sql` — `scan_scope` table (active) and `indexed_folders` table (legacy, retained)
