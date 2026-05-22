import logging
import os
import numpy as np
import time

from database.db import get_connection
from ai.embeddings import generate_embeddings
from indexer.embedding_manager import get_faiss_index
from config import FAISS_INDEX_PATH

log = logging.getLogger(__name__)

# Basic human_size formatter copied from hybrid_search
def _human_size(num: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if num < 1024.0:
            return f"{num:g} {unit}"
        num /= 1024.0
    return f"{num:.1f} TB"

def search_semantic(query: str, limit: int = 50, offset: int = 0, date_filters: dict = None) -> dict:
    """
    Generate query embedding, search FAISS index, and map back to files/chunks.
    """
    if not query.strip():
        return {"total": 0, "results": [], "no_index": False}
        
    if not os.path.exists(FAISS_INDEX_PATH):
        return {"total": 0, "results": [], "no_index": True}
        
    # Check if there are any vectors in the index
    index = get_faiss_index()
    if index.ntotal == 0:
        return {"total": 0, "results": [], "no_index": True}
        
    try:
        query_embeddings = generate_embeddings([query])
        
        # We fetch extra to allow grouping chunks by file
        k = limit * 4 
        distances, indices = index.search(query_embeddings, k)
        
        valid_indices = indices[0]
        valid_distances = distances[0]
        
        # Filter out -1 indices
        mask = valid_indices != -1
        valid_indices = valid_indices[mask]
        valid_distances = valid_distances[mask]
        
        if len(valid_indices) == 0:
            return {"total": 0, "results": [], "no_index": False}
            
        # Map vectors to chunks to files
        vector_ids = valid_indices.tolist()
        vector_to_score = {vid: float(score) for vid, score in zip(valid_indices, valid_distances)}
        
        # We need to preserve the ranking. Use a placeholder in the query.
        placeholders = ",".join("?" for _ in vector_ids)
        params = list(vector_ids)
        
        date_sql = ""
        fallback_date_sql = ""
        fallback_params = []
        
        if date_filters:
            field = date_filters.get("field", "modified_at")
            if field not in ["modified_at", "created_at", "last_indexed_at"]:
                field = "modified_at"
                
            def _add_date_clauses(fld, pf, curr_params):
                d_sql = ""
                if date_filters.get(f"{pf}after"):
                    curr_params.append(date_filters[f"{pf}after"])
                    d_sql += f" AND f.{fld} >= ?"
                if date_filters.get(f"{pf}before"):
                    curr_params.append(date_filters[f"{pf}before"])
                    d_sql += f" AND f.{fld} < ?"
                if date_filters.get(f"{pf}year"):
                    y = date_filters[f"{pf}year"]
                    curr_params.append(f"{y}-01-01T00:00:00")
                    curr_params.append(f"{y+1}-01-01T00:00:00")
                    d_sql += f" AND f.{fld} >= ? AND f.{fld} < ?"
                return d_sql
                
            if field == "created_at":
                date_sql = _add_date_clauses("created_at", "created_", params)
                if date_filters.get("fallback_to_modified"):
                    fallback_params = list(vector_ids)
                    fallback_date_sql = _add_date_clauses("modified_at", "modified_", fallback_params)
            elif field == "last_indexed_at":
                date_sql = _add_date_clauses("last_indexed_at", "indexed_", params)
            else:
                date_sql = _add_date_clauses("modified_at", "modified_", params)
            
        def _run_query(d_sql, query_params):
            sql = f"""
                SELECT 
                    e.vector_id,
                    f.id, f.path, f.name, f.extension, f.size, f.created_at, f.modified_at, f.status, f.tags,
                    c.chunk_text
                FROM embeddings e
                JOIN files f ON e.file_id = f.id
                JOIN file_chunks c ON e.chunk_id = c.id
                WHERE e.vector_id IN ({placeholders})
                  AND f.status != 'missing'
                  {d_sql}
            """
            with get_connection() as conn:
                return conn.execute(sql, query_params).fetchall()
                
        rows = _run_query(date_sql, params)
        fallback_used = False
        if not rows and fallback_date_sql:
            rows = _run_query(fallback_date_sql, fallback_params)
            fallback_used = True
            
        # Group by file_id to pick the best chunk per file
        files_map = {}
        
        for row in rows:
            fid = row["id"]
            vid = row["vector_id"]
            score = vector_to_score.get(vid, 0.0)
            
            # Semantic search can return scores slightly > 1.0 or < -1.0 due to fp precision
            # Or low scores. We'll set a soft threshold.
            if score < 0.2:
                continue
                
            if fid not in files_map or files_map[fid]["semantic_score"] < score:
                d = dict(row)
                d["semantic_score"] = score
                d["snippet"] = d.pop("chunk_text")[:300] + "..." # basic snippet
                files_map[fid] = d
                
        # Sort files by best chunk score
        sorted_files = sorted(files_map.values(), key=lambda x: x["semantic_score"], reverse=True)
        
        # Apply offset and limit
        total = len(sorted_files)
        paginated = sorted_files[offset : offset + limit]
        
        results = []
        for d in paginated:
            # Format to match existing search output
            d["match_type"] = "semantic"
            d["score"] = round(d["semantic_score"], 3)
            d["size_human"] = _human_size(d.get("size") or 0)
            # Determine exact matched date filter field
            d["matched_date_filter_field"] = None
            has_active_date = date_filters and any(date_filters.get(k) for k in ["modified_after", "modified_year", "created_after", "created_year", "indexed_after", "indexed_year", "modified_before", "created_before", "indexed_before"])
            
            if has_active_date:
                d["matched_date_filter_field"] = "modified_at" if fallback_used else date_filters.get("field", "modified_at")
                d["fallback_to_modified_used"] = fallback_used
                d["matched_date_filter"] = True
                
            d["matched_reasons"] = []
            d["exact_name_match"] = False
            
            # Initialize empty fields for compatibility
            d["matched_metadata_terms"] = []
            d["matched_extensions"] = []
            d["matched_tag_terms"] = []
            d["matched_weak_tag_terms"] = []
            d["matched_content_terms"] = []
            
            results.append(d)
            
        return {"total": total, "results": results, "no_index": False}
        
    except Exception as e:
        log.error(f"Semantic search failed: {e}")
        return {"total": 0, "results": [], "no_index": False, "error": str(e)}
