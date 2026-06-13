"""Final direct regression check — no server, no numpy needed."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "engine"))
from search.query_parser import parse_query
from search.filename_search import search_files

CASES = [
    ("dashboard.js", "Exact filename"),
    ("setup.exe",    "Exact exe"),
    ("IGI",          "App/folder name"),
    ("report",       "Common stem"),
    ("assignment",   "Common stem"),
    ("movie.mp4",    "Exact filename+ext"),
    ("pdfs in Ayya folder", "Structured folder+ext"),
    ("Buddhism and the History of Nursing", "Multi-word phrase"),
    ("payment gateway setup", "Multi-word semantic"),
]
RUNS = 5

print("search_files() FINAL REGRESSION CHECK")
print("-" * 75)
all_pass = True
for q, label in CASES:
    parsed = parse_query(q)
    tms = []
    cold_ms = 0.0
    hits = 0
    names = []
    for i in range(RUNS + 1):
        t0 = time.monotonic()
        data = search_files(parsed)
        e = (time.monotonic() - t0) * 1000
        if i == 0:
            cold_ms = e
            hits = data["total"]
            names = [r.get("name", "") for r in data["results"][:5]]
        else:
            tms.append(e)
    warm = sum(tms) / len(tms) if tms else cold_ms
    status = "OK" if hits > 0 else "!!"
    print(f"  [{status}] {q!r:<32}  hits={hits:<5}  cold={cold_ms:>7.1f}ms  warm={warm:>7.1f}ms  [{label}]")
    print(f"       top5: {names}")
    if hits == 0:
        all_pass = False

print("-" * 75)
print()

# Query parser sanity checks
print("Query parser check:")
for q in ["dashboard.js", "setup.exe", "IGI", "pdfs in Ayya folder", "Buddhism and the History of Nursing"]:
    p = parse_query(q)
    intent = p.get("search_intent")
    meta = p.get("metadata_terms")
    ext = p.get("extension_filters")
    folder = p.get("folder_filters")
    literal = p.get("literal_terms")
    print(f"  {q!r}")
    print(f"      intent={intent}  meta={meta}  ext={ext}  folder={folder}  literal={literal}")

print()
print("Verify structured search preserves ext+folder filters:")
# pdfs in Ayya — check all results are .pdf and in ayya path
parsed = parse_query("pdfs in Ayya folder")
data = search_files(parsed)
results = data["results"]
ext_ok = all(r.get("extension", "").lower() == ".pdf" for r in results)
path_ok = all("ayya" in (r.get("path", "") or "").lower() for r in results)
print(f"  pdfs in Ayya: {len(results)} hits, all_pdf={ext_ok}, all_in_ayya={path_ok}")
if results:
    for r in results[:3]:
        print(f"    {r.get('name')}  ext={r.get('extension')}  path=...{(r.get('path',''))[-50:]}")

print()
if all_pass:
    print("All queries returned results.")
else:
    print("WARNING: Some queries returned 0 results — check search data.")
