# Decisions log

One entry per decision, the day it is made. Newest day first.
Format: decision — rejected alternative — why.

## Day 1 (2026-09-19 → 2026-10-01) — setup and walking skeleton

- Monorepo for all six projects — one repo per project — shared bundle, CI and test suite; reads as one platform.
- dev/test/prod = three catalogs + three bundle targets in one workspace — three workspaces — Free Edition gives one workspace; the YAML shape is identical to the multi-workspace setup.
- Walking skeleton first, then widen one layer per day — build layer by layer — proves every connection on day one; later failures are local to the new layer.
- Environment is created by `src/vendor_drop/sql/00_foundation.sql` from the repo — hand-typed SQL in the editor — the script is the record; dev and test cannot drift.
- Bronze reads every column as STRING with `_rescued_data`; typing happens in Silver — infer types at ingest — a vendor tape never fails on load and never loses a byte.
- Freddie Mac SFLLD Release 47 layout (31 origination / 35 performance fields) is the contract; the data file outranks the documents — trust the PDF — three of four vendor docs were stale.
- 2026 sample vintage for Days 1–3; a full vintage (2023) before Day 4 — 2026 only — three months of history cannot show delinquency transitions.
- No local PySpark on Windows; Spark-dependent tests run through databricks-connect on serverless — local Spark — Java/winutils pain, and pyspark conflicts with databricks-connect.
- Linter knows the platform globals via `builtins = ["spark", "dbutils"]` in `pyproject.toml` — `# noqa` on each line — one declaration, every other name still checked.
- Local auth = OAuth profile `free`; CI = PAT in GitHub Secrets — PAT on the laptop — humans get short-lived tokens, machines get long-lived ones.
- Files and folders are created when they have content — pre-built placeholder tree — nothing speculative in the repo.
