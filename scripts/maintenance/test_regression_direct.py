"""
DeepFind — Pure-Python Regression Tests (no server needed)
Tests search_files() and unified_search() directly.
Run from repo root: python scripts/maintenance/test_regression_direct.py
Or from this directory: python test_regression_direct.py
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "engine"))

from search.query_parser import parse_query
from search.filename_search import search_files
from search.hybrid_search import unified_search

RUNS = 4
PASS = "PASS"
FAIL = "FAIL"
passed = failed = 0


def check(label, cond, detail=""):
    global passed, failed
    status = PASS if cond else FAIL
    mark = "  [" + status + "]"
    print(mark, label, f"({detail})" if detail else "")
    if cond: passed += 1
    else: failed += 1
    return cond


def warm_search(q, mode="all"):
    timings = []
    result = None
    for i in range(RUNS + 1):
        t0 = time.monotonic()
        result = unified_search(q, mode=mode)
        e = (time.monotonic() - t0) * 1000
        if i > 0:
            timings.append(e)
    warm = sum(timings) / len(timings)
    return result, warm


def names_top(data, n=5):
    return [r.get("name", "") for r in data.get("results", [])[:n]]


print("=" * 65)
print("  DeepFind — Regression Tests (direct Python, no server)")
print("=" * 65)

# ─── A. dashboard.js ────────────────────────────────────────────────────────
print("\nA. dashboard.js")
data, warm = warm_search("dashboard.js")
results = data.get("results", [])
names = names_top(data)
check("Has results",
      len(results) > 0, f"{len(results)} hits")
check("dashboard.js in top 5",
      any("dashboard.js" in n for n in names), f"top: {names}")
check("dashboard.js is first or second",
      any("dashboard.js" in n for n in names[:2]), f"top2: {names[:2]}")
check("Warm timing < 500ms",
      warm < 500, f"{warm:.0f}ms")
print(f"     timing_ms={data.get('timing_ms',{})}")

# ─── B. setup.exe ───────────────────────────────────────────────────────────
print("\nB. setup.exe")
data, warm = warm_search("setup.exe")
results = data.get("results", [])
names = names_top(data)
check("Has results", len(results) > 0, f"{len(results)} hits")
check("setup.exe in top results",
      any("setup" in n.lower() for n in names), f"top: {names}")
check("Warm timing < 500ms", warm < 500, f"{warm:.0f}ms")
print(f"     timing_ms={data.get('timing_ms',{})}")

# ─── C. IGI ─────────────────────────────────────────────────────────────────
print("\nC. IGI")
data, warm = warm_search("IGI")
results = data.get("results", [])
names = names_top(data, 10)
paths = [(r.get("path","") or "") for r in results[:10]]
has_igi_name = any("igi" in n.lower() for n in names)
has_igi_path = any("igi" in p.lower() for p in paths)
check("Has results", len(results) > 0, f"{len(results)} hits")
check("IGI in top results (name or path)",
      has_igi_name or has_igi_path, f"names: {names[:5]}")
check("Warm timing < 500ms", warm < 500, f"{warm:.0f}ms")
print(f"     timing_ms={data.get('timing_ms',{})}")

# ─── D. report ──────────────────────────────────────────────────────────────
print("\nD. report")
data, warm = warm_search("report")
results = data.get("results", [])
names = names_top(data, 10)
check("Has results", len(results) > 0, f"{len(results)} hits")
check("'report' in top results",
      any("report" in n.lower() for n in names), f"names: {names[:5]}")
# Report should return multiple file types
check("Warm timing < 700ms", warm < 700, f"{warm:.0f}ms")
print(f"     timing_ms={data.get('timing_ms',{})}")

# ─── E. pdfs in Ayya folder ─────────────────────────────────────────────────
print("\nE. pdfs in Ayya folder")
data, warm = warm_search("pdfs in Ayya folder")
results = data.get("results", [])
ext_ok = all(r.get("extension", "").lower() == ".pdf" for r in results)
path_ok = all("ayya" in (r.get("path", "") or "").lower() for r in results)
check("Has results", len(results) > 0, f"{len(results)} hits")
check("All results are PDFs", ext_ok,
      f"exts: {[r.get('extension') for r in results[:5]]}")
check("All in ayya path", path_ok,
      f"paths (last 40 chars): {[(r.get('path',''))[-40:] for r in results[:2]]}")
check("Warm timing < 700ms", warm < 700, f"{warm:.0f}ms")
print(f"     timing_ms={data.get('timing_ms',{})}")

# ─── F. Buddhism and the History of Nursing ─────────────────────────────────
print("\nF. Buddhism and the History of Nursing")
data, warm = warm_search("Buddhism and the History of Nursing")
results = data.get("results", [])
timing = data.get("timing_ms", {})
check("Has results", len(results) > 0, f"{len(results)} hits")
check("Content search ran", timing.get("content_search", 0) > 0,
      f"content_ms={timing.get('content_search',0)}")
check("Warm timing < 700ms", warm < 700, f"{warm:.0f}ms")
print(f"     timing_ms={timing}")

# ─── G. payment gateway setup ───────────────────────────────────────────────
print("\nG. payment gateway setup")
data, warm = warm_search("payment gateway setup")
results = data.get("results", [])
check("Has results", len(results) > 0, f"{len(results)} hits")
check("Warm timing < 3000ms", warm < 3000, f"{warm:.0f}ms")
print(f"     timing_ms={data.get('timing_ms',{})}")

# ─── H. Path-only child suppression (files in IGI) ─────────────────────────
print("\nH. files in IGI — path-only suppression check")
data, warm = warm_search("IGI")
results = data.get("results", [])
# Path-only matches should have path_only_match_penalty applied (lower scores)
# We verify that exact-name/folder hits outrank path-only hits
if results:
    top_sources = [r.get("candidate_sources", []) for r in results[:5]]
    top_has_direct = any(
        "exact_name" in src or "exact_stem" in src or "exact_folder" in src
        for src in top_sources
    )
    check("Top results have direct name/folder matches (not path-only)",
          top_has_direct, f"top sources: {top_sources[:3]}")

# ─── I. Extension + folder (structured) ─────────────────────────────────────
print("\nI. videos in Downloads")
data, warm = warm_search("videos in Downloads")
results = data.get("results", [])
video_exts = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".wmv", ".flv"}
ext_ok = all(r.get("extension", "").lower() in video_exts for r in results)
check("Has results", len(results) > 0, f"{len(results)} hits")
check("All results are video files", ext_ok,
      f"exts: {list(set(r.get('extension','') for r in results[:5]))}")
print(f"     timing_ms={data.get('timing_ms',{})}")

# ─── Summary ────────────────────────────────────────────────────────────────
print()
print("=" * 65)
print(f"  Regression Results: {passed} PASS, {failed} FAIL out of {passed+failed}")
print("=" * 65)
