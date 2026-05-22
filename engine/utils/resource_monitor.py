import os
import psutil
from pathlib import Path
from config import DATA_DIR, DB_PATH, FAISS_INDEX_PATH

def _human_size(num: int) -> str:
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return f"{num:g} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"

def _get_dir_size(path: Path) -> int:
    """Recursively calculate the size of a directory."""
    if not path.exists():
        return 0
    total_size = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

def get_system_resources() -> dict:
    """
    Gather and return system resource usage matching the requested spec.
    """
    # 1. Calculate Storage
    
    # DB Size
    db_exists = DB_PATH.exists()
    db_size = DB_PATH.stat().st_size if db_exists else 0
    
    # FAISS Size
    faiss_exists = FAISS_INDEX_PATH.exists()
    faiss_size = FAISS_INDEX_PATH.stat().st_size if faiss_exists else 0
    
    # Model Cache Size
    # Our semantic indexer saves models in engine/data/models by default when sentence-transformers downloads them
    models_dir = DATA_DIR / "models"
    model_exists = models_dir.exists()
    model_size = _get_dir_size(models_dir) if model_exists else 0
    
    # Total App Data Size (engine/data folder)
    data_exists = DATA_DIR.exists()
    data_size = _get_dir_size(DATA_DIR) if data_exists else 0
    
    # 2. Calculate Runtime
    process = psutil.Process()
    # non-blocking CPU check
    cpu_percent = process.cpu_percent(interval=None) 
    memory_info = process.memory_info()
    rss_bytes = memory_info.rss
    
    return {
        "status": "ok",
        "storage": {
            "sqlite_db": {
                "path": str(DB_PATH.relative_to(DB_PATH.parent.parent)),
                "exists": db_exists,
                "size_bytes": db_size,
                "size_human": _human_size(db_size) if db_exists else "Not created yet"
            },
            "faiss_index": {
                "path": str(FAISS_INDEX_PATH.relative_to(FAISS_INDEX_PATH.parent.parent)),
                "exists": faiss_exists,
                "size_bytes": faiss_size,
                "size_human": _human_size(faiss_size) if faiss_exists else "Not created yet"
            },
            "data_folder": {
                "path": str(DATA_DIR.relative_to(DATA_DIR.parent)),
                "exists": data_exists,
                "size_bytes": data_size,
                "size_human": _human_size(data_size)
            },
            "model_cache": {
                "path": str(models_dir.relative_to(models_dir.parent.parent)) if model_exists else None,
                "exists": model_exists,
                "size_bytes": model_size,
                "size_human": _human_size(model_size) if model_exists else "Not tracked"
            },
            "total_tracked": {
                "size_bytes": data_size,
                "size_human": _human_size(data_size)
            }
        },
        "runtime": {
            "process_memory": {
                "rss_bytes": rss_bytes,
                "rss_human": _human_size(rss_bytes)
            },
            "cpu_percent": round(cpu_percent, 1)
        }
    }
