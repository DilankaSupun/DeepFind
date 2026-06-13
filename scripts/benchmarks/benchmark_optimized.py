"""
DeepFind — Post-Optimization Benchmark

Applies expression indexes if missing, then benchmarks:
  A. Cold + warm timings for each target query using new merged-bucket approach
  B. EXPLAIN QUERY PLAN to verify index usage
  C. End-to-end hybrid search timings via the search engine

Run from: d:/External Works/Portfolio/FileMind/DeepFind/
    python benchmark_optimized.py
"""

import sys
import os
import time
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "engine"))

from config import DB_PATH
from search.query_parser import parse_query
from search.filename_search import search_files

QUERIES = [
    ("dashboard.js",   "Exact filename"),
    ("setup.exe",      "Exact filename + exe"),
    ("IGI",            "Simple app/folder name"),
    ("report",         "Common file stem"),
    ("assignment",     "Common file stem"),
    ("movie.mp4",      "Exact filename + video ext"),
]

RUNS = 5


def raw_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA cache_size=-20000")
    return conn


def ensure_indexes():
    """Create expression indexes if they don't exist (simulates the migration)."""
    conn = raw_conn()
    existing = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='files'"
        ).fetchall()
    }
    created = []
    if "idx_files_name_lower" not in existing:
        conn.execute("CREATE INDEX idx_files_name_lower ON files(lower(name))")
        conn.commit()
        created.append("idx_files_name_lower")
    if "idx_files_extension_lower" not in existing:
        conn.execute("CREATE INDEX idx_files_extension_lower ON files(lower(extension))")
        conn.commit()
        created.append("idx_files_extension_lower")
    conn.close()
    if created:
        print(f"  [Created indexes: {', '.join(created)}]")
    else:
        print("  [Expression indexes already exist — no action needed]")


def show_query_plans():
    print("\n" + "="*62)
    print("  EXPLAIN QUERY PLAN — AFTER OPTIMIZATION")
    print("="*62)
    conn = raw_conn()
    plans = [
        ("lower(name)='dashboard.js'  → expects SEARCH via idx_files_name_lower",
         "SELECT id,name FROM files WHERE status!='missing' AND lower(name)=lower(?)",
         ["dashboard.js"]),

        ("lower(name) LIKE 'dashboard.%'  → expects range scan",
         "SELECT id,name FROM files WHERE status!='missing' AND lower(name) LIKE lower(?)",
         ["dashboard.%"]),

        ("lower(name) LIKE '%igi%'  → full scan expected (leading %)",
         "SELECT id,name FROM files WHERE status!='missing' AND lower(name) LIKE lower(?)",
         ["%igi%"]),

        ("lower(extension)='.js'  → expects SEARCH via idx_files_extension_lower",
         "SELECT id,name FROM files WHERE status!='missing' AND lower(extension)=lower(?)",
         [".js"]),
    ]
    for label, sql, params in plans:
        print(f"\n  -- {label}")
        for r in conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall():
            print(f"     {dict(r)}")
    conn.close()


def benchmark_search_files():
    print("\n" + "="*62)
    print("  SEARCH_FILES() BENCHMARK  (filename_search.search_files)")
    print("="*62)
    print(f"  {'Query':<20} {'Hits':>5}  {'Cold ms':>9}  {'Warm avg ms':>12}  {'Notes'}")
    print(f"  {'-'*20}  {'-'*5}  {'-'*9}  {'-'*12}  {'-'*30}")

    for query_str, label in QUERIES:
        parsed = parse_query(query_str)
        timings = []
        hits = 0
        for i in range(RUNS):
            t0 = time.monotonic()
            result = search_files(parsed)
            elapsed = (time.monotonic() - t0) * 1000
            hits = result["total"]
            if i == 0:
                cold_ms = elapsed
            else:
                timings.append(elapsed)
        warm_avg = sum(timings) / len(timings) if timings else cold_ms
        print(f"  {query_str:<20} {hits:>5}  {cold_ms:>9.1f}  {warm_avg:>12.1f}  {label}")


def benchmark_individual_buckets():
    """Compare new single-merged-query approach vs old per-bucket timing."""
    print("\n" + "="*62)
    print("  MERGED BUCKET SQL TIMING (direct SQL)")
    print("="*62)

    conn = raw_conn()
    base_where = "status != 'missing'"

    test_cases = [
        ("dashboard.js", ["dashboard", "dashboard.js"]),
        ("setup.exe",    ["setup", "setup.exe"]),
        ("IGI",          ["igi"]),
        ("report",       ["report"]),
    ]

    for label, terms in test_cases:
        print(f"\n  Query: {label!r}  terms={terms}")

        # New: merged exact+stem in ONE query
        exact_clauses = " OR ".join(["lower(name) = lower(?)"] * len(terms))
        stem_clauses  = " OR ".join(["lower(name) LIKE lower(?)"] * len(terms))
        merged_cond   = f"({exact_clauses} OR {stem_clauses})"
        stem_params   = [f"{t}.%" for t in terms]

        sql = f"""
            SELECT id, name FROM files
            WHERE {base_where} AND {merged_cond}
            ORDER BY modified_at DESC LIMIT 100
        """
        params = terms + stem_params

        timings = []
        for i in range(RUNS):
            t0 = time.monotonic()
            rows = conn.execute(sql, params).fetchall()
            elapsed = (time.monotonic() - t0) * 1000
            if i == 0:
                cold_ms = elapsed
                hits = len(rows)
            else:
                timings.append(elapsed)
        warm_avg = sum(timings) / len(timings) if timings else cold_ms
        print(f"    merged exact+stem: hits={hits}  cold={cold_ms:.1f}ms  warm_avg={warm_avg:.1f}ms")

    conn.close()


if __name__ == "__main__":
    print("DeepFind — Post-Optimization Benchmark")
    print("Ensuring expression indexes exist...")
    ensure_indexes()
    show_query_plans()
    benchmark_individual_buckets()
    benchmark_search_files()
    print("\nDone.")
