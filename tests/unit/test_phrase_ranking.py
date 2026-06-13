import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../engine')))
from unittest.mock import patch
from database.db import get_connection
from search.hybrid_search import unified_search
from search.query_parser import parse_query

def test_phrase_ranking_tiers():
    """
    Test that the phrase-first search strategy correctly ranks:
    A (Exact continuous phrase) > B (Separated words) > C (Repeated single words) > D (Semantic fallback)
    """
    # 1. Setup DB with test files using a very unique phrase to avoid clashing with real DB files
    unique_phrase = "xyzzyplugh and the zorkmid of xyzzyplugh"
    
    with get_connection() as conn:
        conn.execute("DELETE FROM files WHERE id IN (999901, 999902, 999903, 999904)")
        conn.execute("DELETE FROM files_fts WHERE rowid IN (999901, 999902, 999903, 999904)")
        
        files = [
            (999901, "File A", "C:\\a_test.txt", f"{unique_phrase} developed through careful study."),
            (999902, "File B", "C:\\b_test.txt", "xyzzyplugh influenced healthcare. zorkmid history developed later."),
            (999903, "File C", "C:\\c_test.txt", "zorkmid zorkmid zorkmid. xyzzyplugh xyzzyplugh. xyzzyplugh."),
            (999904, "File D", "C:\\d_test.txt", "Religious traditions influenced the development of patient care.")
        ]
        
        for fid, name, path, content in files:
            conn.execute("""
                INSERT INTO files (id, name, path, extracted_text, status, modified_at, size)
                VALUES (?, ?, ?, ?, 'content_extracted', '2023-01-01T00:00:00', 100)
            """, (fid, name, path, content))
            
            conn.execute("""
                INSERT INTO files_fts (rowid, name, path, extracted_text, tags)
                VALUES (?, ?, ?, ?, '')
            """, (fid, name, path, content))
            
    # 2. Mock semantic search to simulate File D matching semantically
    original_semantic = unified_search # not needed
    def mock_semantic(query, limit, offset, date_filters):
        print("INSIDE MOCK SEMANTIC!!!")
        return {
            "total": 1,
            "results": [{
                "id": 999904,
                "name": "File D",
                "path": "C:\\d_test.txt",
                "size": 100,
                "modified_at": "2023-01-01T00:00:00",
                "semantic_score": 0.85,
                "score": 0.85,
                "snippet": "xyzzyplugh traditions influenced the development of patient zorkmid.",
                "snippet_source": "semantic"
            }]
        }
        
    original_parse = parse_query
    def mock_parse_query(q):
        parsed = original_parse(q)
        parsed["semantic_allowed"] = True
        return parsed

    with patch('search.hybrid_search.search_semantic', side_effect=mock_semantic), \
         patch('search.hybrid_search.parse_query', side_effect=mock_parse_query), \
         patch('scanner.scan_scope_utils.filter_allowed_files', side_effect=lambda x, **kwargs: x):
        # 3. Execute search
        res = unified_search("xyzzyplugh and the zorkmid of xyzzyplugh", mode="all", limit=200)
        results = res["results"]
        
        # 4. Verify ranking: A > B > C > D
        # We find our specific files in the results list
        test_results = [r for r in results if r["id"] in [999901, 999902, 999903, 999904]]
        
        assert len(test_results) == 4, f"Expected our 4 test files in results, got {len(test_results)}"
        
        # Their relative order MUST be A, B, C, D
        assert test_results[0]["id"] == 999901, "File A (exact phrase) should be ranked highest among test files"
        assert test_results[0]["match_tier"] == 1
        assert test_results[0]["match_source"] == "content_phrase"
        
        assert test_results[1]["id"] == 999903, "File C (partial terms, but outranked B due to FTS occurrences)"
        assert test_results[1]["match_tier"] == 2
        assert test_results[1]["match_source"] == "content_all_terms"
        
        assert test_results[2]["id"] == 999902, "File B (all terms)"
        assert test_results[3]["id"] == 999904, "File D (semantic only) should be 4th"
        assert test_results[3]["match_tier"] == 4
        assert "semantic" in test_results[3]["match_sources"]

def test_explicit_quoted_phrase():
    unique_phrase = "xyzzyplugh and the zorkmid of xyzzyplugh"
    with get_connection() as conn:
        conn.execute("DELETE FROM files WHERE id IN (999905, 999906)")
        conn.execute("DELETE FROM files_fts WHERE rowid IN (999905, 999906)")
        
        conn.execute(f"INSERT INTO files (id, name, path, extracted_text, status, modified_at, size) VALUES (999905, 'F1', 'C:\\1_test.txt', '{unique_phrase}', 'content_extracted', '2023-01-01T00:00:00', 100)")
        conn.execute(f"INSERT INTO files_fts (rowid, name, path, extracted_text, tags) VALUES (999905, 'F1', 'C:\\1_test.txt', '{unique_phrase}', '')")
        
        conn.execute("INSERT INTO files (id, name, path, extracted_text, status, modified_at, size) VALUES (999906, 'F2', 'C:\\2_test.txt', 'zorkmid xyzzyplugh', 'content_extracted', '2023-01-01T00:00:00', 100)")
        conn.execute("INSERT INTO files_fts (rowid, name, path, extracted_text, tags) VALUES (999906, 'F2', 'C:\\2_test.txt', 'zorkmid xyzzyplugh', '')")
        
    res = unified_search('"xyzzyplugh and the zorkmid of xyzzyplugh"', mode="content")
    
    # We should get both, but phrase match first
    test_results = [r for r in res["results"] if r["id"] in [999905, 999906]]
    
    assert len(test_results) == 2
    assert test_results[0]["id"] == 999905
    assert test_results[0]["match_tier"] == 1
    
    assert test_results[1]["id"] == 999906
    assert test_results[1]["match_tier"] == 2

