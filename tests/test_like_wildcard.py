"""
DeepFind — LIKE Wildcard Safety Tests (Step 25)

Tests that user-supplied terms containing %, _, and \\ are correctly
escaped before being embedded in SQLite LIKE patterns.

Tests:
  - escape_like() function correctness
  - Special character cases: %, _, \\, apostrophe, quotes, combined
  - search_files() still returns results for normal queries post-escaping
  - Wildcard injection: searching for 'a%' does not match all files

Run: python tests/test_like_wildcard.py
"""

import sys
import os
import pytest

# live_db: these tests run against the real production database.
# They require a populated deepfind.db with indexed files.
# Exclude from default fast test run: python -m pytest -m "not live_db"
pytestmark = pytest.mark.live_db

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))

from search.like_utils import escape_like
from search.filename_search import search_files
from search.query_parser import parse_query


_passed = 0
_failed = 0
_results: list[tuple[str, bool, str]] = []


def _record(name: str, condition: bool, detail: str = "") -> None:
    global _passed, _failed
    if condition:
        _passed += 1
        _results.append((name, True, detail))
    else:
        _failed += 1
        _results.append((name, False, detail))


# ─────────────────────────────────────────────────────────────────────────────
# escape_like() unit tests
# ─────────────────────────────────────────────────────────────────────────────

def test_escape_like_function():
    # Percent
    _record("escape %: literal percent escaped", escape_like("50%off") == "50\\%off")
    _record("escape %: double percent", escape_like("100%%") == "100\\%\\%")

    # Underscore
    _record("escape _: underscore escaped", escape_like("report_2024") == "report\\_2024")
    _record("escape _: multiple underscores", escape_like("a_b_c") == "a\\_b\\_c")

    # Backslash — must be escaped FIRST
    _record("escape \\: backslash doubled", escape_like("C:\\users") == "C:\\\\users")
    _record("escape \\: backslash before percent", escape_like("\\%") == "\\\\\\%")

    # Apostrophe — no change (SQL parameterisation handles it)
    _record("escape ': apostrophe unchanged", escape_like("it's") == "it's")

    # Double quote — no change
    _record("escape \": double quote unchanged", escape_like('say "hello"') == 'say "hello"')

    # Combined
    _record("escape combined: %_\\", escape_like("50%_report\\") == "50\\%\\_report\\\\")

    # Empty/normal strings
    _record("escape normal: plain term unchanged", escape_like("report") == "report")
    _record("escape empty: empty string unchanged", escape_like("") == "")
    _record("escape None: None returned as-is", escape_like(None) is None)

    # Unicode
    _record("escape unicode: unicode chars unchanged", escape_like("日本語テスト") == "日本語テスト")
    _record("escape unicode: unicode with %", escape_like("テスト%") == "テスト\\%")


# ─────────────────────────────────────────────────────────────────────────────
# search_files() correctness after escaping
# ─────────────────────────────────────────────────────────────────────────────

def test_search_files_normal_queries():
    """Normal queries must still work correctly after escape_like is applied."""

    cases = [
        ("dashboard.js", "Exact filename"),
        ("setup.exe",    "Exact exe"),
        ("IGI",          "App/folder name"),
        ("report",       "Common stem"),
    ]
    for q, label in cases:
        parsed = parse_query(q)
        data = search_files(parsed)
        _record(f"normal query: {q!r} still returns results", data["total"] > 0,
             f"total={data['total']} [{label}]")


# ─────────────────────────────────────────────────────────────────────────────
# Wildcard injection prevention
# ─────────────────────────────────────────────────────────────────────────────

def test_wildcard_injection_prevention():
    """
    Queries containing % and _ must NOT expand into wildcard matches
    that inflate the result count.
    """
    # Searching for "%" should NOT return all files (it would without escaping)
    parsed_pct = parse_query("%")
    data_pct = search_files(parsed_pct)

    # Searching for "a" for comparison (a common prefix)
    parsed_a = parse_query("a")
    data_a = search_files(parsed_a)

    # "%" alone — with escaping, should return very few or zero results
    # (very unlikely any file is literally named "%")
    # The key is it should NOT return ALL files like it would without escaping.
    # We can't guarantee 0 results (someone could have a file called "%"),
    # but it should be much fewer than a broad letter search.
    _record("injection: '%' query returns fewer results than 'a'",
         data_pct["total"] <= data_a["total"],
         f"pct_total={data_pct['total']}, a_total={data_a['total']}")

    # Searching for "_" should not match all single-char filenames
    parsed_us = parse_query("_")
    data_us = search_files(parsed_us)
    _record("injection: '_' query returns reasonable result count",
         data_us["total"] <= data_a["total"],
         f"us_total={data_us['total']}, a_total={data_a['total']}")

    # Searching for "report_2024" — with escaping, underscore is literal
    parsed_report = parse_query("report_2024")
    data_report = search_files(parsed_report)
    # Without escaping: LIKE '%report_2024%' would match 'reportX2024' too.
    # With escaping: LIKE '%report\_2024%' ESCAPE '\\' only matches 'report_2024'.
    # We just verify the query executes without error.
    _record("injection: 'report_2024' query executes without error",
         isinstance(data_report["total"], int))

    # Backslash in query
    parsed_bs = parse_query("C:\\users")
    data_bs = search_files(parsed_bs)
    _record("injection: backslash query executes without error",
         isinstance(data_bs["total"], int))


# ─────────────────────────────────────────────────────────────────────────────
# Apostrophe and quote safety (SQL injection via parameterisation)
# ─────────────────────────────────────────────────────────────────────────────

def test_special_chars_no_sql_injection():
    """
    Apostrophes and quotes in query terms must be handled safely by
    SQLite's parameterised query mechanism (not escaped in Python).
    """
    for q, label in [
        ("it's file", "apostrophe"),
        ('say "hello"', "double quote"),
        ("O'Brien's report", "multiple apostrophes"),
        ("'; DROP TABLE files; --", "SQL injection attempt"),
    ]:
        try:
            parsed = parse_query(q)
            data = search_files(parsed)
            _record(f"sql safety: {label!r} — no exception", True)
            _record(f"sql safety: {label!r} — returns int total",
                 isinstance(data["total"], int))
        except Exception as exc:
            _record(f"sql safety: {label!r} — no exception", False, str(exc))
            _record(f"sql safety: {label!r} — returns int total", False)


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 65)
    print("  DeepFind — LIKE Wildcard Safety Tests (Step 25)")
    print("=" * 65)

    test_escape_like_function()
    test_search_files_normal_queries()
    test_wildcard_injection_prevention()
    test_special_chars_no_sql_injection()

    print()
    for name, ok, detail in _results:
        status = "PASS" if ok else "FAIL"
        mark = f"  [{status}] {name}"
        if detail:
            print(f"{mark}  ({detail})")
        else:
            print(mark)

    print()
    print("=" * 65)
    print(f"  Results: {_passed} PASS, {_failed} FAIL out of {_passed + _failed}")
    print("=" * 65)
