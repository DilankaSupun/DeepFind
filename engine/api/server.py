"""
DeepFind Engine — FastAPI Application

Step 6:  Added /folders endpoints for folder selection.
Step 9:  Added /extract endpoints for text content extraction.
Step 19: Added /scan-scope endpoints for automatic scan + exclusion manager.

Future steps will add routers for:
  - Semantic AI       (Step 15+ / V2)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.db import init_db
from api.routes import health
from api.routes import db as db_routes
from api.routes import folders as folders_routes
from api.routes import index as index_routes
from api.routes import search as search_routes
from api.routes import extract as extract_routes
from api.routes import tags as tags_routes
from api.routes import history as history_routes
from api.routes import files as files_routes
from api.routes import dashboard as dashboard_routes
from api.routes import semantic as semantic_routes
from api.routes import system as system_routes
from api.routes import watcher as watcher_routes
from api.routes import reset as reset_routes
from api.routes import scan_scope as scan_scope_routes
from api.routes import pipeline as pipeline_routes

log = logging.getLogger(__name__)


# ── Lifespan: startup / shutdown ───────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Code before `yield` runs on startup; code after runs on shutdown.
    """
    # Startup: initialize the SQLite database
    log.info("Initializing database...")
    init_db()
    log.info("Database ready.")
    
    # Initialize Scan Scope (idempotent, sets up default scan roots)
    from api.routes.scan_scope import initialize_scan_scope
    try:
        initialize_scan_scope()
        log.info("Scan scope initialized.")
    except Exception as e:
        log.error(f"Failed to initialize scan scope: {e}")
        
    from config import AUTO_SCAN_ENABLED
    if AUTO_SCAN_ENABLED:
        from scanner.file_watcher import get_watcher
        from indexer.background_pipeline import start_pipeline, get_status
        
        # Only start watcher/pipeline if auto processing is enabled
        status = get_status()
        if status.get("auto_processing_enabled", True):
            get_watcher().start()
            start_pipeline()

    yield  # App runs here

    # Shutdown
    log.info("DeepFind Engine shutting down.")
    from indexer.background_pipeline import stop_pipeline
    stop_pipeline()
    from scanner.file_watcher import get_watcher
    get_watcher().stop()


# ── FastAPI app instance ───────────────────────────────────────────────────────

app = FastAPI(
    title="DeepFind Engine",
    version="0.1.0",
    description=(
        "Local AI file search engine. "
        "Local-first — no cloud APIs, no file uploads."
    ),
    docs_url="/docs",    # Swagger UI — useful for manual testing
    redoc_url="/redoc",  # ReDoc alternative UI
    lifespan=lifespan,
)

# ── CORS Middleware ────────────────────────────────────────────────────────────
#
# Electron renderer origins allowed to call this API:
#   - http://localhost:5173   → Vite dev server (development)
#   - http://127.0.0.1:5173  → Alternate Vite address
#   - file://                 → Electron production (loadFile)
#   - app://.                 → Electron custom protocol (optional)
#
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "file://",
        "app://.",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ── Register Routers ───────────────────────────────────────────────────────────

app.include_router(health.router,             tags=["Health"])
app.include_router(db_routes.router,          tags=["Database"])
app.include_router(folders_routes.router,     tags=["Folders"])
app.include_router(index_routes.router,       tags=["Indexing"])
app.include_router(search_routes.router,      tags=["Search"])
app.include_router(extract_routes.router,     tags=["Extraction"])
app.include_router(tags_routes.router,        tags=["Tags"])
app.include_router(history_routes.router,     tags=["History"])
app.include_router(files_routes.router,       tags=["Files"])
app.include_router(dashboard_routes.router,   tags=["Dashboard"])
app.include_router(semantic_routes.router,    tags=["Semantic"])
app.include_router(system_routes.router,      tags=["System"])
app.include_router(watcher_routes.router,     tags=["Watcher"])
app.include_router(reset_routes.router,       tags=["Reset"])
app.include_router(scan_scope_routes.router,  tags=["ScanScope"])
app.include_router(pipeline_routes.router,    tags=["Pipeline"])

# Future routers — added in later steps:
# app.include_router(settings.router,prefix="/settings",tags=["Settings"])
