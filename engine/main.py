"""
DeepFind Engine — Entry Point

Run from the engine/ directory:

    python main.py

Or run uvicorn directly:

    uvicorn api.server:app --host 127.0.0.1 --port 8765 --reload

Then test:
    http://127.0.0.1:8765/health       <- Health check
    http://127.0.0.1:8765/db/status    <- Database status (Step 5)
    http://127.0.0.1:8765/docs         <- Swagger UI (interactive API docs)
"""

import logging
import logging.handlers
import uvicorn
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8765

# ── Logging setup ──────────────────────────────────────────────────────────────
# Log to both console (INFO) and a rotating file (DEBUG).
# Rotating file: 5 MB max, 3 backup files → max 20 MB total.
# Logs are written to engine/data/logs/ — excluded from git via .gitignore.
# Packaging note: In production, this should write to %APPDATA%\DeepFind\logs\

def _configure_logging() -> None:
    log_dir = Path(__file__).parent / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "engine.log"

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Console handler — INFO level only to keep terminal clean
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    ))

    # Rotating file handler — DEBUG level for diagnostics
    rotating = logging.handlers.RotatingFileHandler(
        str(log_file),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    rotating.setLevel(logging.DEBUG)
    rotating.setFormatter(logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    ))

    # Suppress noisy third-party loggers at WARNING unless debugging
    logging.getLogger("watchdog").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("faiss").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    root.addHandler(console)
    root.addHandler(rotating)


if __name__ == "__main__":
    _configure_logging()

    print("\n" + "=" * 56)
    print("  DeepFind Engine")
    print("=" * 56)
    print(f"  Running at : http://{HOST}:{PORT}")
    print(f"  Health     : http://{HOST}:{PORT}/health")
    print(f"  DB Status  : http://{HOST}:{PORT}/db/status")
    print(f"  API Docs   : http://{HOST}:{PORT}/docs")
    print("=" * 56 + "\n")

    from api.server import app
    from config import IS_PACKAGED
    import runtime_control
    
    if IS_PACKAGED:
        config = uvicorn.Config(
            app=app,
            host=HOST,
            port=PORT,
            log_level="info",
        )
        server = uvicorn.Server(config)
        runtime_control.server = server
        server.run()
    else:
        config = uvicorn.Config(
            app="api.server:app",
            host=HOST,
            port=PORT,
            reload=True,
            reload_dirs=["api", "database"],
            log_level="info",
        )
        server = uvicorn.Server(config)
        runtime_control.server = server
        server.run()
