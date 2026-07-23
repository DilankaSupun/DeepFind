# DeepFind UI Design System
## Premium Windows-Native File Search Experience

> **Primary purpose:** This document is the visual and UX specification for redesigning the DeepFind desktop application.
>
> **Before coding:** Read and follow `agent.md` completely. Use `agent.md` as the main project reference for code quality, architecture, security, performance, Electron integration, and existing decisions.
>
> **Scope:** Frontend/UI only. Do not modify backend logic, APIs, search behavior, ranking, database, semantic indexing, background automation, Electron lifecycle, PyInstaller, or installer configuration.

---

# 1. Product Vision

DeepFind should feel like a premium Windows desktop utility built for serious daily use.

The design must feel:

- modern
- clean
- calm
- precise
- professional
- fast
- trustworthy
- local-first
- native to Windows 11

The application should visually relate to:

- Windows 11 Settings
- Windows File Explorer
- Microsoft PowerToys
- modern Fluent desktop applications

It must **not** feel like:

- a gaming dashboard
- a glowing sci-fi interface
- a website landing page
- a developer control panel
- a collection of unrelated cards
- a purple-themed prototype

---

# 2. Core Design Direction

## Concept Name

**DeepFind Fluent Search Workspace**

## Main UX Model

Use a Windows-native application shell with:

1. Search
2. Library
3. Activity
4. System
5. Settings

The Search page is the primary user experience.

The interface should use:

- neutral graphite surfaces
- one controlled Azure-blue accent
- subtle depth
- compact Windows-style controls
- list-based file results
- selected-result details pane
- consistent Fluent icons
- restrained animation
- clear hierarchy

---

# 3. Brand Color System

The app uses a **Graphite + Azure** visual identity.

Purple is no longer the main accent.

## Core Palette

```css
:root {
  /* Window and Navigation */
  --df-bg-window: #0F141A;
  --df-bg-navigation: #141B22;

  /* Surfaces */
  --df-bg-surface-1: #1A232C;
  --df-bg-surface-2: #222D38;
  --df-bg-surface-3: #2A3642;
  --df-bg-hover: #31404D;
  --df-bg-selected: rgba(78, 167, 255, 0.14);

  /* Borders */
  --df-border-subtle: rgba(255, 255, 255, 0.06);
  --df-border-default: rgba(255, 255, 255, 0.10);
  --df-border-strong: rgba(255, 255, 255, 0.16);

  /* Text */
  --df-text-primary: #F4F7FA;
  --df-text-secondary: #A8B3BE;
  --df-text-tertiary: #74818E;
  --df-text-disabled: #58636E;

  /* Primary Brand Accent */
  --df-accent: #4EA7FF;
  --df-accent-hover: #70B8FF;
  --df-accent-pressed: #2F8CE5;
  --df-accent-subtle: rgba(78, 167, 255, 0.14);
  --df-accent-border: rgba(78, 167, 255, 0.48);

  /* Secondary Accent */
  --df-secondary-accent: #55C7D9;
  --df-secondary-accent-subtle: rgba(85, 199, 217, 0.14);

  /* States */
  --df-success: #52C78A;
  --df-success-subtle: rgba(82, 199, 138, 0.14);

  --df-warning: #F0BC5E;
  --df-warning-subtle: rgba(240, 188, 94, 0.14);

  --df-danger: #E8747C;
  --df-danger-subtle: rgba(232, 116, 124, 0.14);

  /* Search Highlight */
  --df-highlight-bg: rgba(240, 188, 94, 0.20);
  --df-highlight-text: #FFE09A;

  /* Shadows */
  --df-shadow-flyout: 0 12px 30px rgba(0, 0, 0, 0.38);
  --df-shadow-dialog: 0 24px 60px rgba(0, 0, 0, 0.50);
}
```

## Color Usage Rules

- Use Azure blue for selection, primary actions, focus, and branding.
- Use cyan only for secondary semantic/AI-related signals.
- Use green only for success and ready states.
- Use amber for warning and text highlighting.
- Use red only for errors and destructive actions.
- Most surfaces must remain neutral graphite.
- Do not add bright gradients everywhere.
- Do not add glow around every element.
- Do not use neon borders around result cards.
- Do not use color as the only way to communicate status.

---

# 4. Logo System

## Logo Concept

The DeepFind logo combines:

- a real folder shape
- a magnifying glass
- a premium Windows-style color treatment
- a simple silhouette that remains readable at app-icon size

## Logo Colors

```text
Folder body:         #1F5F9D
Folder top layer:    #2F78B7
Magnifying lens:     #4EA7FF
Secondary highlight: #55C7D9
Outline:             #122231
Wordmark “Deep”:     #F4F7FA in dark UI
Wordmark “Find”:     #4EA7FF
```

For light backgrounds:

```text
Wordmark “Deep”: #15212C
Wordmark “Find”: #2F8CE5
```

## Logo Rules

- Keep the folder clearly recognizable.
- Keep the magnifying glass integrated into the folder.
- Avoid glossy 3D effects in the final production icon.
- Avoid heavy gradients.
- Avoid glow.
- Use a flat or very subtle two-tone treatment.
- Ensure the icon is readable at:
  - 16px
  - 24px
  - 32px
  - 48px
  - 256px
- Prepare a multi-resolution `.ico` file before the final installer build.

---

# 5. Typography

Use Windows-native fonts only.

```css
font-family:
  "Segoe UI Variable Text",
  "Segoe UI Variable",
  "Segoe UI",
  system-ui,
  sans-serif;
```

## Type Scale

```css
--df-type-display: 38px;
--df-type-page-title: 28px;
--df-type-section-title: 20px;
--df-type-card-title: 15px;
--df-type-body: 14px;
--df-type-body-small: 13px;
--df-type-caption: 12px;
```

## Font Weights

```text
App wordmark: 650
Page title: 600
Section title: 600
Filename: 600
Buttons: 500
Body: 400
Metadata: 400
```

## Rules

- Use sentence case.
- Avoid excessive uppercase headings.
- Do not use 9px or 10px text for important information.
- Keep paths and metadata at 12–13px.
- Keep filenames at 15–16px.
- Use strong contrast for important text.

---

# 6. Spacing and Radius

## Spacing Scale

```css
--df-space-1: 4px;
--df-space-2: 8px;
--df-space-3: 12px;
--df-space-4: 16px;
--df-space-5: 20px;
--df-space-6: 24px;
--df-space-8: 32px;
--df-space-10: 40px;
```

## Radius Scale

```css
--df-radius-small: 4px;
--df-radius-control: 6px;
--df-radius-card: 8px;
--df-radius-large: 12px;
```

## Rules

- Avoid pill shapes for normal cards and buttons.
- Use pills only for small tags, status badges, and segmented controls.
- Use 6–8px radius for native Windows-style controls.

---

# 7. Application Shell

## Main Layout

```text
┌──────────────────────────────────────────────────────────────┐
│ Native Windows title bar                                     │
├───────────────┬──────────────────────────────────────────────┤
│ Navigation    │ Page header / command area                   │
│               ├──────────────────────────────────────────────┤
│ Search        │                                              │
│ Library       │ Main page content                            │
│ Activity      │                                              │
│ System        │                                              │
│ Settings      │                                              │
│               │                                              │
│ Engine state  │                                              │
└───────────────┴──────────────────────────────────────────────┘
```

## Navigation Width

```text
Expanded: 220px
Collapsed: 64px
```

Collapse automatically below approximately `1050px`.

## Main Content Padding

```text
Large desktop: 24px
Medium: 20px
Narrow: 16px
```

## Rules

- Keep the real Electron/Windows title bar.
- Do not create fake minimize, maximize, or close buttons.
- Remove the current large centered hero once a search begins.
- Use the available desktop width.
- Do not keep the app inside a narrow centered website column.

---

# 8. Navigation Rail

Create or refine:

```text
NavigationRail.jsx
```

## Navigation Items

- Search
- Library
- Activity
- System
- Settings

Use Fluent icons consistently.

Recommended package:

```text
@fluentui/react-icons
```

Do not mix:

- emojis
- random SVGs
- multiple unrelated icon libraries
- text symbols

## Navigation Item Style

```text
Height: 40px
Horizontal padding: 10px
Gap: 12px
Radius: 6px
```

Selected state:

- soft Azure background
- 3px Azure indicator on the left
- primary text
- active icon

Hover state:

- neutral lighter background
- no glow

## Navigation Bottom Area

```text
● Engine ready
Local only

v0.1.0
```

Remove all roadmap/dev milestone labels such as:

```text
Step 11
Step 20
Development build step
```

---

# 9. Page Structure

Each page uses:

```text
Page title
Short description
Optional action area
```

Examples:

## Search

**Title:** Search  
**Description:** Find files by name, content, location, type, or meaning.

## Library

**Title:** Search library  
**Description:** Manage indexed locations and search-processing data.

## Activity

**Title:** Background activity  
**Description:** See how DeepFind keeps your local search index updated.

## System

**Title:** System usage  
**Description:** Monitor local storage and processing resources.

## Settings

**Title:** Settings  
**Description:** Control automation, exclusions, and application data.

---

# 10. Search Page — Empty State

Do not show the current oversized landing hero.

Use:

```text
[48px DeepFind icon]

Find anything on this computer

Search by filename, text inside documents, folder, file type, or meaning.

[ Search field ]

[All] [Name / path] [Content] [Semantic]

Examples:
report.pdf · files in Downloads · payment gateway · videos from 2025
```

Maximum width:

```text
760px
```

Top spacing:

```text
approximately 72–80px
```

Do not repeat a huge DeepFind wordmark if the navigation already contains the brand.

---

# 11. Search Page — Active Results State

After search starts, switch to a compact workspace.

## Sticky Search Area

```text
[ Search field                                       ] [Search]

[All] [Name / path] [Content] [Semantic]    ● Engine ready
```

Height:

```text
100–112px
```

Use:

- subtle solid surface
- bottom border
- no floating glowing capsule

---

# 12. Search Input

## Dimensions

```text
Height: 48px
Radius: 8px
```

## Style

```css
background: var(--df-bg-surface-2);
border: 1px solid var(--df-border-default);
```

Focus:

```css
border-color: var(--df-accent-border);
box-shadow: 0 0 0 2px rgba(78, 167, 255, 0.18);
```

## Search Button

```text
Height: 40px
Width: about 92px
Radius: 8px
Background: Azure
```

Rules:

- no gradient
- no glow
- clear hover/pressed/disabled states
- spinner inside button while loading
- prevent duplicate search submissions

## Keyboard Shortcuts

```text
Ctrl + L  Focus/select search
/         Focus search when no input is active
Escape    Close details/clear selection
```

---

# 13. Search Mode Selector

Use a Windows-style segmented control.

Modes:

- All
- Name / path
- Content
- Semantic

Height:

```text
32px
```

Active state:

- Azure subtle background
- Azure text
- subtle border

Inactive:

- tertiary text
- neutral hover background

Do not use thick bright outlines.

---

# 14. Results Workspace

Use a list-and-details layout.

```text
┌────────────────────────────────┬───────────────────────────┐
│ Results list                   │ Selected result details   │
│                                │                           │
└────────────────────────────────┴───────────────────────────┘
```

Recommended:

```css
grid-template-columns:
  minmax(520px, 1fr)
  minmax(300px, 360px);
gap: 16px;
```

Below `1100px`, use a right-side drawer or expandable details area.

---

# 15. Results Toolbar

Left:

```text
182 results
for “Christianity and the History of Nursing”
```

Right:

```text
Showing 50
```

Typography:

```text
Count: 14px semibold
Query: 13px secondary
Showing count: 12px muted
```

Do not display `Showing first 50` inside a large pill.

---

# 16. Result List Design

Replace large glowing cards with compact native list rows.

## Row Heights

```text
Metadata-only: 72–78px
With snippet: 104–118px
```

## Row Layout

```text
[icon] Filename                         [Match] [Actions]
       Path
       Content/Semantic preview
       Size · Modified · Match explanation
```

## Row States

Default:

```css
background: var(--df-bg-surface-1);
```

Hover:

```css
background: var(--df-bg-hover);
```

Selected:

```css
background: var(--df-bg-selected);
border-left: 2px solid var(--df-accent);
```

Keyboard focus must be visible.

Do not use neon outlines or heavy shadows.

---

# 17. File Icons

Use a consistent 40px icon tile.

Suggested colors:

```text
PDF: muted red
Text/document: blue
Code: Azure/violet-blue
Folder: amber
Image: teal
Audio: magenta
Video: blue-violet
Executable: cyan
Archive: orange
Unknown: gray
```

Rules:

- use Fluent icons where possible
- keep colors muted
- do not use extension text alone as the icon
- ensure icon remains readable at small size

---

# 18. Filename and Path

Filename:

```text
15–16px
600 weight
Primary text
Single line with ellipsis
```

Path:

```text
12–13px
Tertiary text
Single line with ellipsis
Tooltip shows full path
```

---

# 19. Match Badges

Use compact 20–22px badges.

Labels:

- Exact match
- Name match
- Content match
- Semantic match
- Folder match
- Hybrid match

Colors:

```text
Exact / Name: Azure
Content: Blue
Semantic: Teal
Folder / Path: Neutral
Hybrid: Azure + Cyan
```

Style:

```css
font-size: 11px;
font-weight: 500;
border-radius: 4px;
padding: 2px 6px;
```

Do not make badges visually dominant.

---

# 20. Content and Semantic Preview

Keep existing secure snippet rendering.

Never use:

```text
dangerouslySetInnerHTML
```

## List Preview

```text
13px
Secondary text
Line-height 1.45
Maximum 2 lines
```

## Details Preview

```text
Maximum 5 lines
```

Do not place every preview inside a heavy bordered box.

Use a 2px indicator line at the left.

## Search Highlight

```css
mark {
  background: var(--df-highlight-bg);
  color: var(--df-highlight-text);
  border-radius: 3px;
  padding: 0 2px;
}
```

---

# 21. Tags

List view:

- show maximum two tags
- show `+N` for remaining tags

Details pane:

- show all useful tags

Tag style:

```text
11px
20px height
4px radius
Neutral surface
No glow
```

Do not create an entire extra row of pills for every result.

---

# 22. Metadata Row

Use one compact line:

```text
91 KB · Modified 4 Jun 2026 · Exact phrase in content
```

Do not create separate pills for:

- file size
- date
- match reason
- content source

Keep debug scoring hidden from normal users.

---

# 23. Result Actions

Preferred behavior:

- Single-click selects row.
- Double-click opens file.
- Open button appears on hover/selection.
- Folder action uses a compact icon button.
- Tooltips explain icon-only actions.

Minimum click target:

```text
32px
```

Do not change secure IPC behavior.

---

# 24. Result Details Pane

Create:

```text
ResultDetailsPane.jsx
```

Width:

```text
320–360px
```

Contents:

1. Large file icon
2. Filename
3. File type
4. Match badge
5. Full path
6. Open button
7. Show in folder button
8. Match explanation
9. Longer snippet
10. File metadata
11. Tags
12. Local-only privacy note where useful

Do not show raw debug scores.

---

# 25. No Results State

Use:

**Title:** No matching files  
**Text:** Try fewer words, check the spelling, or choose another search mode.

If structured filters are available, summarize them in normal language.

Do not expose parser internals.

---

# 26. Search Error State

Use:

**Title:** Search could not be completed  
**Text:** The local DeepFind engine did not respond.

Optional action:

```text
Try again
```

Do not show raw stack traces.

---

# 27. Loading State

Use:

- spinner inside Search button
- subtle progress line
- lightweight skeleton rows if no previous results

Do not use a full-screen loader for normal searches.

---

# 28. Library Page

## Section 1: Search Coverage

Show:

- scanned locations
- excluded locations
- indexed file count
- last scan status

## Section 2: Search Data

Show compact status tiles:

- Files indexed
- Content extracted
- Tagged files
- Semantic chunks

## Section 3: Maintenance Tools

Move manual controls into collapsed:

```text
Maintenance tools
```

Include:

- Run indexing now
- Extract text now
- Generate tags now
- Force re-tag
- Build semantic index

Add note:

> DeepFind normally performs these tasks automatically. Manual tools are intended for troubleshooting or forced reprocessing.

Do not remove functionality.

---

# 29. Activity Page

Top status:

```text
Background automation   On
File watcher            Running
Current task            Indexing
```

Use a 4-stage timeline:

1. Indexing
2. Extraction
3. Tagging
4. Semantic indexing

Show states:

- complete
- current
- pending
- error

Main control:

```text
Automation On / Off
```

Advanced controls inside collapsed:

```text
Advanced controls
```

Include:

- Run now
- Pause current job
- Stop current job

---

# 30. System Page

Use a clean 2-column dashboard.

Cards:

- CPU usage
- Memory usage
- DeepFind storage
- Database size
- FAISS size
- Model status
- Log status

Use neutral progress bars.

Do not add heavy charting libraries.

---

# 31. Settings Page

Group settings into:

## Automation

- Auto Processing toggle
- explanation

## Search Coverage

- excluded location management
- scan-scope controls

## Appearance

Only show already implemented options.

## About

Show:

```text
DeepFind
v0.1.0
Local-first
No cloud uploads
```

## Danger Zone

Place reset and clear-index actions at the bottom.

Use red only here.

Keep existing confirmation behavior.

---

# 32. Buttons

Create reusable variants:

- Primary
- Secondary
- Subtle
- Danger
- Icon-only

## Heights

```text
Compact: 28px
Standard: 32px
Prominent: 40px
```

## Rules

- no gradient
- no glow
- one primary button per area
- clear hover/focus/pressed states

---

# 33. Toggle Switches

Windows-style toggle:

```text
Width: about 40px
Height: about 20px
```

Show state text:

```text
On
Off
```

Do not rely on color alone.

---

# 34. Status Indicators

Use:

```text
● Ready
● Running
● Paused
● Error
```

Use text plus color.

Do not use large bordered pills for every state.

---

# 35. Background and Materials

Remove the visible dotted grid.

Use a solid graphite background.

Use subtle layered surfaces instead of constant blur.

Blur is allowed only for:

- menus
- popovers
- tooltips
- modals

Normal cards and result rows must remain opaque.

---

# 36. Accessibility

Required:

- visible focus states
- keyboard navigation
- `aria-label` for icon buttons
- proper contrast
- minimum 32px click targets
- status text plus color
- logical headings
- no essential information only on hover
- live region for result counts if practical

Respect:

```css
@media (prefers-reduced-motion: reduce)
```

---

# 37. Motion

Use short native transitions.

```text
Hover/focus: 120ms
Drawer/panel: 160ms
Page content: maximum 180ms
```

Do not add:

- animated gradients
- continuous glow
- floating logo loops
- bouncing effects
- zoom-heavy transitions

---

# 38. Responsive Rules

Test:

- 1920×1080
- 1600×900
- 1366×768
- 1280×720
- narrow Electron window

Below `1050px`:

- collapse navigation
- hide wordmark
- details pane becomes drawer

Below `760px`:

- one-column results
- compact search button
- metadata may wrap
- no horizontal scrolling

---

# 39. Frontend Architecture

Recommended structure:

```text
components/
  shell/
    AppShell
    NavigationRail
    PageHeader

  search/
    SearchWorkspace
    SearchInput
    SearchModeSelector
    ResultsToolbar
    ResultList
    ResultRow
    ResultDetailsPane
    SearchEmptyState
    SearchNoResults
    SearchErrorState

  ui/
    Button
    IconButton
    Badge
    StatusIndicator
    Panel
    SectionHeader
    Toggle
    Tooltip
    Skeleton
```

Styles:

```text
styles/
  tokens.css
  reset.css
  app-shell.css
  utilities.css
```

Do not introduce Tailwind or a full UI framework.

---

# 40. Strict Technical Boundaries

Do not modify:

- Python backend
- API routes
- query parser
- ranking
- FTS
- semantic search
- database
- extraction
- tagging
- watcher
- background pipeline
- Electron BackendManager
- preload security
- packaging
- installer

Do not add:

- analytics
- cloud services
- remote fonts
- online assets
- runtime network dependencies
- unsafe HTML
- arbitrary IPC

The application must remain offline-capable and local-first.

---

# 41. Implementation Order

## Phase 1

- design tokens
- typography
- backgrounds
- AppShell
- NavigationRail
- PageHeader

## Phase 2

- Search page
- Search input
- Search modes
- Result list
- Details pane
- Empty/loading/no-results/error states

## Phase 3

- Library page
- Activity page
- System page
- Settings page
- reorganize existing dashboard components

## Phase 4

- keyboard navigation
- accessibility
- responsive behavior
- motion polish
- final QA

---

# 42. Verification

Run:

- frontend lint, if configured
- Vite production build
- Electron development launch
- Electron production frontend launch

Test:

- empty state
- loading state
- exact filename result
- content result
- semantic result
- long filename
- long path
- many tags
- no results
- backend offline
- open file
- show in folder
- keyboard navigation
- narrow window
- Library page
- Activity page
- System page
- Settings page
- reset confirmation
- startup overlay

Confirm:

- no console errors
- no React warnings
- no blank screen
- no hardcoded port
- no unsafe HTML
- no production CSP warning
- no broken API calls
- no backend changes

---

# 43. Deliverables

After completion, provide:

1. UI files created
2. UI files modified
3. Design tokens implemented
4. Navigation implementation
5. Search-page redesign
6. Result-list redesign
7. Details pane implementation
8. Library/Activity/System/Settings organization
9. Accessibility changes
10. Responsive changes
11. Frontend build result
12. Electron development result
13. Electron production result
14. Console errors/warnings
15. Known limitations
16. Before screenshots
17. After screenshots:
    - 1920×1080
    - 1366×768
    - empty search
    - results
    - Library page
    - Activity page
18. Confirmation that no backend or packaging files were changed
19. Confirmation that installer rebuild is required after approval

---

# 44. Final Design Principle

DeepFind should feel like a **native Windows search utility** that users can trust every day.

The redesign must prioritize:

1. search clarity
2. filename readability
3. quick result scanning
4. safe file actions
5. calm visual hierarchy
6. native desktop behavior
7. local-first trust
8. minimal visual noise

Do not create a generic dashboard.

Create a focused, premium file-search workspace.
