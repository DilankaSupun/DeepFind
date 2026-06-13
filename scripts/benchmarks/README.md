# scripts/benchmarks/

Performance benchmark scripts for DeepFind search engine.

These are **not automated tests**. They measure search timings and verify
SQLite query plan (EXPLAIN QUERY PLAN) to confirm index usage.

## Usage

Run from the repo root:
```
cd <repo_root>
engine\.venv\Scripts\activate
python scripts/benchmarks/<script>.py
```

## Scripts

| Script | Purpose |
|---|---|
| `profile_buckets.py` | Per-bucket SQL timing + EXPLAIN QUERY PLAN for Step 24 optimization work |
| `benchmark_optimized.py` | Post-Step-24 merged-bucket benchmark comparing old vs. new approach |
| `final_benchmark.py` | Warm-timing summary for all target queries after optimization |

## Target Timings (Step 24 baseline, from production DB)

| Query | Target | Typical Warm |
|---|---|---|
| `dashboard.js` | < 300 ms | ~200 ms |
| `setup.exe` | < 300 ms | ~195 ms |
| `IGI` | < 400 ms | ~155 ms |
| `report` | < 500 ms | ~325 ms |
| `movie.mp4` | N/A (broad ext) | ~360 ms |
