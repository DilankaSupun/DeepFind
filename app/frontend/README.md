# app/frontend/

This folder will contain the **React frontend UI**.

## Planned Structure (Step 2)

```
frontend/
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── SearchBar/
│   │   ├── ResultCard/
│   │   ├── FileDetailsPanel/
│   │   ├── IndexingProgress/
│   │   └── Sidebar/
│   ├── pages/              # App screens
│   │   ├── Search/
│   │   ├── Settings/
│   │   └── Welcome/
│   ├── hooks/              # Custom React hooks
│   ├── api/                # API call functions (to Python backend)
│   ├── styles/             # Global CSS and design tokens
│   └── App.jsx             # Root component
├── public/
├── index.html
└── package.json
```

## UI Screens Planned

| Screen | Purpose |
|--------|---------|
| Welcome / Setup | First run, folder selection |
| Search | Main search bar, filters, result list |
| File Details Panel | Tags, metadata, extracted text preview |
| Indexing Progress | Live scan/index progress display |
| Settings | Indexed folders, limits, preferences |

## UI Rules

- Vanilla CSS (no TailwindCSS)
- Debounced search input (250–400 ms)
- Paginated results (top 20–50)
- Loading, empty, and error states required

> ⏳ Not implemented yet — awaiting Step 2.
