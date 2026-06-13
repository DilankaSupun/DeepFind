"""Final benchmark: measure search_files() timings after Step 24 optimization."""
import sys, os, time, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "engine"))
from config import DB_PATH
from search.query_parser import parse_query
from search.filename_search import search_files

QUERIES = [
    ("dashboard.js",  "Exact filename"),
    ("setup.exe",     "Exact exe"),
    ("IGI",           "Simple app name"),
    ("report",        "Common stem"),
    ("assignment",    "Common stem"),
    ("movie.mp4",     "Exact filename+ext"),
]
RUNS = 6

def raw_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA cache_size=-20000")
    return conn

# Verify index usage
conn = raw_conn()
print("INDEX USAGE (EXPLAIN QUERY PLAN):")
tests = [
    ("exact_name=?",    "SELECT id FROM files WHERE lower(name)=?",       ["dashboard.js"]),
    ("stem LIKE x.%",   "SELECT id FROM files WHERE lower(name) LIKE ?",  ["dashboard.%"]),
    ("extension=?",     "SELECT id FROM files WHERE lower(extension)=?",  [".js"]),
    ("name_contains",   "SELECT id FROM files WHERE lower(name) LIKE ?",  ["%dashboard%"]),
]
for label, sql, params in tests:
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    detail = rows[0]["detail"] if rows else "?"
    print(f"  {label:<20} {detail}")
conn.close()

print()
print("search_files() END-TO-END TIMINGS (warm avg over 5 runs):")
sep = "-" * 75
print(sep)

for query_str, label in QUERIES:
    parsed = parse_query(query_str)
    timings = []
    cold_ms = 0.0
    hits = 0
    for i in range(RUNS):
        t0 = time.monotonic()
        result = search_files(parsed)
        elapsed = (time.monotonic() - t0) * 1000
        if i == 0:
            cold_ms = elapsed
            hits = result["total"]
        else:
            timings.append(elapsed)
    warm_avg = sum(timings) / len(timings) if timings else cold_ms
    print(f"  {query_str:<20}  hits={hits:<6}  cold={cold_ms:>7.1f}ms  warm_avg={warm_avg:>7.1f}ms  ({label})")

print(sep)
print("Done.")
