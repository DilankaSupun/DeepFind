import logging
import threading
from config import MODEL_DIR

log = logging.getLogger(__name__)

# Lazy loaded singleton
_model = None
_model_lock = threading.Lock()

def _get_model():
    """Lazy loads the embedding model to avoid slow startup times."""
    global _model
    with _model_lock:
        if _model is None:
            log.info(f"Loading semantic embedding model from {MODEL_DIR} locally...")
            try:
                from sentence_transformers import SentenceTransformer
                # Ensure the model cache runs offline and does not attempt any Hugging Face network lookups
                _model = SentenceTransformer(str(MODEL_DIR), local_files_only=True)
                log.info("Semantic model loaded successfully.")
            except ImportError:
                log.error("sentence-transformers is not installed.")
                raise
            except Exception as e:
                log.error(f"Failed to load embedding model: {e}")
                raise
    return _model

def generate_embeddings(texts: list[str]):
    """
    Generate normalized embeddings for a list of texts.
    Normalization ensures we can use inner product in FAISS as a proxy for cosine similarity.
    """
    if not texts:
        return []
        
    model = _get_model()
    # Ensure they are numpy arrays and normalized
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return embeddings
