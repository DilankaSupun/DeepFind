import logging
import threading
import time
import os
import faiss
import numpy as np

from database.db import get_connection
from ai.embeddings import generate_embeddings
from config import FAISS_INDEX_PATH, EMBED_BATCH_SIZE

log = logging.getLogger(__name__)

# State for tracking indexing progress
class EmbeddingState:
    def __init__(self):
        self.is_running = False
        self.chunks_checked = 0
        self.chunks_embedded = 0
        self.chunks_skipped = 0
        self.files_covered = set()
        self.errors = 0
        self.current_file_id = None
        self.start_time = None
        
    def to_dict(self):
        return {
            "status": "running" if self.is_running else "idle",
            "active": self.is_running,
            "chunks_checked": self.chunks_checked,
            "chunks_embedded": self.chunks_embedded,
            "chunks_skipped": self.chunks_skipped,
            "files_covered": len(self.files_covered),
            "errors": self.errors,
            "current_file_id": self.current_file_id
        }

_state = EmbeddingState()
_thread = None

# FAISS constants
DIMENSION = 384  # MiniLM-L6-v2 dimension

def get_faiss_index():
    """Loads existing FAISS index or creates a new one (IndexFlatIP for cosine similarity)"""
    if os.path.exists(FAISS_INDEX_PATH):
        try:
            return faiss.read_index(str(FAISS_INDEX_PATH))
        except Exception as e:
            log.error(f"Failed to read FAISS index, recreating: {e}")
            
    return faiss.IndexFlatIP(DIMENSION)

def save_faiss_index(index):
    """Saves FAISS index to disk"""
    try:
        faiss.write_index(index, str(FAISS_INDEX_PATH))
    except Exception as e:
        log.error(f"Failed to save FAISS index: {e}")

def get_status() -> dict:
    return _state.to_dict()

def get_summary() -> dict:
    faiss_exists = os.path.exists(FAISS_INDEX_PATH)
    vectors = 0
    if faiss_exists:
        try:
            index = faiss.read_index(str(FAISS_INDEX_PATH))
            vectors = index.ntotal
        except:
            vectors = 0
            
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(DISTINCT file_id) as n FROM embeddings").fetchone()
        files_covered = row["n"] if row else 0
        
    return {
        "status": "ok",
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "vectors": vectors,
        "files_covered": files_covered,
        "faiss_index_exists": faiss_exists
    }

def start_embedding():
    global _thread
    
    if _state.is_running:
        return False
        
    # Reset state
    _state.is_running = True
    _state.chunks_checked = 0
    _state.chunks_embedded = 0
    _state.chunks_skipped = 0
    _state.files_covered = set()
    _state.errors = 0
    _state.current_file_id = None
    _state.start_time = time.monotonic()
    
    _thread = threading.Thread(target=_embed_worker, daemon=True)
    _thread.start()
    return True

def _embed_worker():
    log.info("Starting background embedding generator")
    try:
        index = get_faiss_index()
        
        while True:
            # Fetch a batch of chunks that need embedding
            # Must join files to ensure file is not 'missing'
            # Must ensure chunk_text is not empty or too small (handled loosely here by skipping empty)
            with get_connection() as conn:
                rows = conn.execute(f"""
                    SELECT c.id, c.file_id, c.chunk_text 
                    FROM file_chunks c
                    JOIN files f ON c.file_id = f.id
                    WHERE c.vector_id IS NULL
                      AND f.status != 'missing'
                      AND c.chunk_text IS NOT NULL
                      AND c.chunk_text != ''
                    LIMIT {EMBED_BATCH_SIZE}
                """).fetchall()
                
            if not rows:
                log.info("No more chunks require embedding.")
                break
                
            batch_texts = []
            valid_rows = []
            
            for row in rows:
                _state.chunks_checked += 1
                text = row["chunk_text"].strip()
                
                # Very loose filter for tiny chunks
                if len(text.split()) < 5:
                    _state.chunks_skipped += 1
                    # Mark vector_id as -1 to indicate skipped
                    with get_connection() as conn:
                        conn.execute("UPDATE file_chunks SET vector_id = -1 WHERE id = ?", (row["id"],))
                    continue
                    
                batch_texts.append(text)
                valid_rows.append(row)
                _state.current_file_id = row["file_id"]
                _state.files_covered.add(row["file_id"])
                
            if not valid_rows:
                continue
                
            try:
                # Generate embeddings
                embeddings = generate_embeddings(batch_texts)
                
                if len(embeddings) > 0:
                    start_vec_id = index.ntotal
                    index.add(embeddings)
                    
                    with get_connection() as conn:
                        for i, row in enumerate(valid_rows):
                            vec_id = start_vec_id + i
                            chunk_id = row["id"]
                            file_id = row["file_id"]
                            
                            conn.execute("UPDATE file_chunks SET vector_id = ? WHERE id = ?", (vec_id, chunk_id))
                            conn.execute(
                                "INSERT INTO embeddings (file_id, chunk_id, vector_id, model_name, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                                (file_id, chunk_id, vec_id, "all-MiniLM-L6-v2")
                            )
                            _state.chunks_embedded += 1
                            
                    # Optionally flush to disk every batch so progress isn't lost on crash
                    save_faiss_index(index)
                    
            except Exception as e:
                log.error(f"Error embedding batch: {e}")
                _state.errors += 1
                time.sleep(2) # Backoff
                
    except Exception as e:
        log.error(f"Fatal error in embedding worker: {e}")
    finally:
        _state.is_running = False
        log.info(f"Embedding worker stopped. Total embedded: {_state.chunks_embedded}")
