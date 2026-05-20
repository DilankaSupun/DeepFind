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

import uvicorn

HOST = "127.0.0.1"
PORT = 8765


if __name__ == "__main__":
    print("\n" + "=" * 56)
    print("  DeepFind Engine")
    print("=" * 56)
    print(f"  Running at : http://{HOST}:{PORT}")
    print(f"  Health     : http://{HOST}:{PORT}/health")
    print(f"  DB Status  : http://{HOST}:{PORT}/db/status")
    print(f"  API Docs   : http://{HOST}:{PORT}/docs")
    print("=" * 56 + "\n")

    uvicorn.run(
        "api.server:app",
        host=HOST,
        port=PORT,
        reload=True,
        reload_dirs=["api", "database"],  # Watch both api and database folders
        log_level="info",
    )

