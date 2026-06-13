"""
DeepFind — Metadata Bucket Profiler

Runs each metadata search bucket independently, with EXPLAIN QUERY PLAN,
and measures timings for the target queries.

Run from: d:/External Works/Portfolio/FileMind/DeepFind/
    python profile_buckets.py
"""

import sys
import os
import time
import sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "engine"))

from config import DB_PATH
from search.query_parser import parse_query

QUERIES = [
    "dashboard.js",
    "setup.exe",
    "IGI",
    "report",
    "assignment",
    "movie.mp4",
]

# How many runs per bucket (to get warm averages)
RUNS = 5


def raw_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA cache_size=-20000")
    return conn


def time_query(conn, sql, params, runs=RUNS):
    """Return (rows, cold_ms, warm_ms_avg)."""
    rows = None
    cold_ms = None
    timings = []
    for i in range(runs):
        t = time.monotonic()
        rows = conn.execute(sql, params).fetchall()
        elapsed = (time.monotonic() - t) * 1000
        if i == 0:
            cold_ms = elapsed
        else:
            timings.append(elapsed)
    warm_avg = sum(timings) / len(timings) if timings else cold_ms
    return rows, cold_ms, warm_avg


def profile_query(query_str: str):
    print(f"\n{'='*60}")
    print(f"  QUERY: {query_str!r}")
    print(f"{'='*60}")

    parsed = parse_query(query_str)
    meta_terms = parsed.get("metadata_terms", [])
    literal_terms = parsed.get("literal_terms", [])
    ext_filters = parsed.get("extension_filters", [])
    combined_terms = list(set(meta_terms + literal_terms))

    print(f"  meta_terms:    {meta_terms}")
    print(f"  literal_terms: {literal_terms}")
    print(f"  ext_filters:   {ext_filters}")
    print(f"  combined:      {combined_terms}")

    conn = raw_conn()

    base_filter = "status != 'missing'"
    base_params: list = []

    results_summary = {}

    for term in combined_terms:
        # ── BUCKET 1: Exact Name ─────────────────────────────────
        sql = f"""
            SELECT id, name FROM files
            WHERE {base_filter} AND lower(name) = lower(?)
            ORDER BY modified_at DESC LIMIT 50
        """
        rows, cold, warm = time_query(conn, sql, base_params + [term])
        key = f"exact_name({term!r})"
        results_summary[key] = {"hits": len(rows), "cold_ms": round(cold,2), "warm_avg_ms": round(warm,2)}

        # ── BUCKET 2: Exact Stem ──────────────────────────────────
        sql = f"""
            SELECT id, name FROM files
            WHERE {base_filter} AND lower(name) LIKE lower(?)
            ORDER BY modified_at DESC LIMIT 50
        """
        rows, cold, warm = time_query(conn, sql, base_params + [f"{term}.%"])
        key = f"exact_stem({term!r})"
        results_summary[key] = {"hits": len(rows), "cold_ms": round(cold,2), "warm_avg_ms": round(warm,2)}

        # ── BUCKET 3: Exact Folder ────────────────────────────────
        sql = f"""
            SELECT id, name FROM files
            WHERE {base_filter} AND (lower(path) LIKE lower(?) OR lower(path) LIKE lower(?))
            ORDER BY modified_at DESC LIMIT 50
        """
        rows, cold, warm = time_query(conn, sql, base_params + [f"%/{term}/%", f"%\\{term}\\%"])
        key = f"exact_folder({term!r})"
        results_summary[key] = {"hits": len(rows), "cold_ms": round(cold,2), "warm_avg_ms": round(warm,2)}

        # ── BUCKET 5: Name Contains ───────────────────────────────
        sql = f"""
            SELECT id, name FROM files
            WHERE {base_filter} AND lower(name) LIKE lower(?)
            ORDER BY modified_at DESC LIMIT 100
        """
        rows, cold, warm = time_query(conn, sql, base_params + [f"%{term}%"])
        key = f"name_contains({term!r})"
        results_summary[key] = {"hits": len(rows), "cold_ms": round(cold,2), "warm_avg_ms": round(warm,2)}

        # ── BUCKET 7: Path Segment ────────────────────────────────
        sql = f"""
            SELECT id, name FROM files
            WHERE {base_filter} AND lower(path) LIKE lower(?)
            ORDER BY modified_at DESC LIMIT 100
        """
        rows, cold, warm = time_query(conn, sql, base_params + [f"%{term}%"])
        key = f"path_segment({term!r})"
        results_summary[key] = {"hits": len(rows), "cold_ms": round(cold,2), "warm_avg_ms": round(warm,2)}

    # ── BUCKET 4: Extension ───────────────────────────────────────
    for ext in ext_filters:
        ext_clean = ext if ext.startswith(".") else f".{ext}"
        sql = f"""
            SELECT id, name FROM files
            WHERE {base_filter} AND lower(extension) = lower(?)
            ORDER BY modified_at DESC LIMIT 100
        """
        rows, cold, warm = time_query(conn, sql, base_params + [ext_clean])
        key = f"extension({ext_clean!r})"
        results_summary[key] = {"hits": len(rows), "cold_ms": round(cold,2), "warm_avg_ms": round(warm,2)}

    conn.close()

    print("\n  Bucket Results:")
    print(f"  {'Bucket':<40} {'Hits':>6}  {'Cold ms':>9}  {'Warm avg ms':>12}")
    print(f"  {'-'*40}  {'-'*6}  {'-'*9}  {'-'*12}")
    for k, v in results_summary.items():
        print(f"  {k:<40} {v['hits']:>6}  {v['cold_ms']:>9.2f}  {v['warm_avg_ms']:>12.2f}")

    # Total of warm timings simulates what _execute_bucket does for all terms
    total_warm = sum(v["warm_avg_ms"] for v in results_summary.values())
    print(f"\n  >> Sum of all bucket warm-avg timings: {total_warm:.2f} ms")


def show_indexes():
    print("\n\n" + "="*60)
    print("  CURRENT INDEX LIST")
    print("="*60)
    conn = raw_conn()
    rows = conn.execute(
        "SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND tbl_name='files' ORDER BY name"
    ).fetchall()
    for r in rows:
        print(f"  {r['name']}")
    conn.close()


def explain_plans():
    print("\n\n" + "="*60)
    print("  EXPLAIN QUERY PLAN — KEY QUERIES")
    print("="*60)
    conn = raw_conn()

    plans = [
        ("lower(name)='dashboard.js'",
         "SELECT id,name FROM files WHERE status!='missing' AND lower(name)=lower(?)",
         ["dashboard.js"]),

        ("lower(name) LIKE 'dashboard.%'",
         "SELECT id,name FROM files WHERE status!='missing' AND lower(name) LIKE lower(?)",
         ["dashboard.%"]),

        ("lower(name) LIKE '%igi%'",
         "SELECT id,name FROM files WHERE status!='missing' AND lower(name) LIKE lower(?)",
         ["%igi%"]),

        ("lower(path) LIKE '%igi%'",
         "SELECT id,name FROM files WHERE status!='missing' AND lower(path) LIKE lower(?)",
         ["%igi%"]),

        ("lower(extension)='.js'",
         "SELECT id,name FROM files WHERE status!='missing' AND lower(extension)=lower(?)",
         [".js"]),
    ]

    for label, sql, params in plans:
        print(f"\n  -- {label}")
        explain_sql = "EXPLAIN QUERY PLAN " + sql
        rows = conn.execute(explain_sql, params).fetchall()
        for r in rows:
            print(f"     {dict(r)}")

    conn.close()


if __name__ == "__main__":
    print("DeepFind — Metadata Bucket Profiler")
    show_indexes()
    explain_plans()
    for q in QUERIES:
        profile_query(q)
    print("\n\nDone.")
