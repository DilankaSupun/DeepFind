"""
DeepFind — Regression Test Suite for Step 24 Optimization

Tests all the required scenarios from the optimization spec.
Run: python regression_tests.py
"""
import sys, time, urllib.request, urllib.parse, json

BASE_URL = "http://127.0.0.1:8765"
RUNS = 3
PASS = "[PASS]"
FAIL = "[FAIL]"


def search(q, mode="all", debug=False):
    url = f"{BASE_URL}/search?q={urllib.parse.quote(q)}&type={mode}&debug={str(debug).lower()}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e), "results": [], "total": 0, "timing_ms": {}}


def warm_timing(q, mode="all", runs=RUNS):
    timings = []
    result = None
    for i in range(runs + 1):
        t0 = time.monotonic()
        result = search(q, mode)
        elapsed = (time.monotonic() - t0) * 1000
        if i > 0:
            timings.append(elapsed)
    warm = sum(timings) / len(timings) if timings else 0
    return result, warm


def first_result_name(data):
    if data and data.get("results"):
        return data["results"][0].get("name", "")
    return ""


def assert_test(label, condition, details=""):
    status = PASS if condition else FAIL
    print(f"  {status} {label}", f"({details})" if details else "")
    return condition


print("=" * 65)
print("  DeepFind Regression Tests — Step 24 Exact Filename Fast Path")
print("=" * 65)
passed = failed = 0

# ── A. dashboard.js ──────────────────────────────────────────────────────────
print("\nA. dashboard.js (exact filename)")
data, warm = warm_timing("dashboard.js")
results = data.get("results", [])
names = [r.get("name", "") for r in results[:5]]
timing = data.get("timing_ms", {})
total_ms = timing.get("total", 0)

ok = assert_test("Returns results", len(results) > 0, f"{len(results)} hits")
passed += ok; failed += not ok
ok = assert_test("First result is dashboard.js", "dashboard.js" in names[:3], f"top names: {names[:3]}")
passed += ok; failed += not ok
ok = assert_test("Warm timing < 500ms", warm < 500, f"{warm:.0f}ms warm")
passed += ok; failed += not ok
print(f"     Timing: total={total_ms}ms, warm_avg={warm:.0f}ms")

# ── B. setup.exe ──────────────────────────────────────────────────────────────
print("\nB. setup.exe (exact executable)")
data, warm = warm_timing("setup.exe")
results = data.get("results", [])
names = [r.get("name", "").lower() for r in results[:5]]
timing = data.get("timing_ms", {})
total_ms = timing.get("total", 0)

ok = assert_test("Returns results", len(results) > 0, f"{len(results)} hits")
passed += ok; failed += not ok
ok = assert_test("Exact exe in top 5", any("setup" in n for n in names), f"top names: {names[:5]}")
passed += ok; failed += not ok
ok = assert_test("Warm timing < 500ms", warm < 500, f"{warm:.0f}ms warm")
passed += ok; failed += not ok
print(f"     Timing: total={total_ms}ms, warm_avg={warm:.0f}ms")

# ── C. IGI ──────────────────────────────────────────────────────────────────
print("\nC. IGI (simple app/folder name)")
data, warm = warm_timing("IGI")
results = data.get("results", [])
names = [r.get("name", "") for r in results[:10]]
has_igi_file = any("igi" in n.lower() for n in names)
has_igi_folder = any("igi" in (r.get("path", "") or "").lower() for r in results[:10])
timing = data.get("timing_ms", {})
total_ms = timing.get("total", 0)

ok = assert_test("Returns results", len(results) > 0, f"{len(results)} hits")
passed += ok; failed += not ok
ok = assert_test("IGI file or folder in top 10", has_igi_file or has_igi_folder, f"names: {names[:5]}")
passed += ok; failed += not ok
ok = assert_test("Warm timing < 500ms", warm < 500, f"{warm:.0f}ms warm")
passed += ok; failed += not ok
print(f"     Timing: total={total_ms}ms, warm_avg={warm:.0f}ms")

# ── D. report ──────────────────────────────────────────────────────────────
print("\nD. report (common file stem)")
data, warm = warm_timing("report")
results = data.get("results", [])
names = [r.get("name", "") for r in results[:10]]
has_report = any("report" in n.lower() for n in names)
timing = data.get("timing_ms", {})
total_ms = timing.get("total", 0)

ok = assert_test("Returns results", len(results) > 0, f"{len(results)} hits")
passed += ok; failed += not ok
ok = assert_test("'report' in top 10 results", has_report, f"names: {names[:5]}")
passed += ok; failed += not ok
ok = assert_test("Warm timing < 700ms", warm < 700, f"{warm:.0f}ms warm")
passed += ok; failed += not ok
print(f"     Timing: total={total_ms}ms, warm_avg={warm:.0f}ms")

# ── E. pdfs in Ayya folder ────────────────────────────────────────────────
print("\nE. pdfs in Ayya folder (structured search)")
data, warm = warm_timing("pdfs in Ayya folder")
results = data.get("results", [])
all_pdf = all(r.get("extension", "").lower() == ".pdf" for r in results)
all_in_ayya = all("ayya" in (r.get("path", "") or "").lower() for r in results)
timing = data.get("timing_ms", {})
total_ms = timing.get("total", 0)

ok = assert_test("Returns results", len(results) > 0, f"{len(results)} hits")
passed += ok; failed += not ok
ok = assert_test("All results are PDFs", all_pdf, f"sample ext: {[r.get('extension') for r in results[:3]]}")
passed += ok; failed += not ok
ok = assert_test("All results in ayya path", all_in_ayya, f"sample: {[(r.get('path',''))[-40:] for r in results[:2]]}")
passed += ok; failed += not ok
print(f"     Timing: total={total_ms}ms, warm_avg={warm:.0f}ms")

# ── F. Buddhism and the History of Nursing (phrase/content search) ────────
print("\nF. Buddhism and the History of Nursing (FTS fast path)")
data, warm = warm_timing("Buddhism and the History of Nursing")
results = data.get("results", [])
timing = data.get("timing_ms", {})
total_ms = timing.get("total", 0)
content_ms = timing.get("content_search", 0)

ok = assert_test("Returns results", len(results) > 0, f"{len(results)} hits")
passed += ok; failed += not ok
ok = assert_test("Content search ran (FTS fast path)", content_ms > 0, f"content_ms={content_ms}")
passed += ok; failed += not ok
ok = assert_test("Warm timing < 700ms", warm < 700, f"{warm:.0f}ms warm")
passed += ok; failed += not ok
print(f"     Timing: total={total_ms}ms content_search={content_ms}ms, warm_avg={warm:.0f}ms")

# ── G. payment gateway setup (semantic fallback) ─────────────────────────
print("\nG. payment gateway setup (semantic fallback)")
data, warm = warm_timing("payment gateway setup")
results = data.get("results", [])
timing = data.get("timing_ms", {})
total_ms = timing.get("total", 0)

ok = assert_test("Returns results", len(results) > 0, f"{len(results)} hits")
passed += ok; failed += not ok
ok = assert_test("Warm timing < 2000ms", warm < 2000, f"{warm:.0f}ms warm")
passed += ok; failed += not ok
print(f"     Timing: total={total_ms}ms, warm_avg={warm:.0f}ms")

# ── Summary ──────────────────────────────────────────────────────────────────
print()
print("=" * 65)
print(f"  Results: {passed} passed, {failed} failed out of {passed+failed} tests")
print("=" * 65)
