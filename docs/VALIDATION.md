# Validation — 30 October 2026

Local `python -m pytest -q` with DATABASE_URL configured: **10 passed** in 16.30 seconds.
One third-party warning: Starlette deprecates its httpx TestClient integration in favor of httpx2.
It did not affect assertions; httpx remains pinned for this release.

Test server: real PostgreSQL **18.4**, workspace-local Windows binaries from
`@embedded-postgres/windows-x64@18.4.0-beta.17`. Binary package and live database files are ignored by Git.
Server listens only on 127.0.0.1:55432; local disposable test initialization uses trust authentication.
Do not copy that authentication configuration to production. Docker/CI configuration uses PostgreSQL 17
with password authentication; its hosted CI result is not asserted by this local report.

The database contains 4,778 entities and eight verified historical failures. Integration testing loaded
the same snapshot twice, verified row counts and references, and retrieved Dinnr through PostgreSQL full-text search.
Export tests compare every CSV/JSONL/Parquet record ID and every Parquet value to JSONL, including empty partitions.
Other checks cover SHA-256 snapshot integrity, deterministic rebuilds, explicit verification evidence,
date ordering, exclusion of reviewed non-terminal cases, API authentication and request bounds,
and evidence-bearing lexical retrieval. The pipeline is offline-reproducible.

A real import exposed Unicode line-separator characters inside original source strings; JSONL now
escapes non-ASCII characters and the loader reads physical lines. The regression test validates every
line of every JSONL file. Unicode is restored normally by JSON decoders.

Not validated: production hosting, Playground's live server integration, sustained concurrent load,
backup restoration in a deployment environment, semantic retrieval relevance, independent human
fact-checking of the entire candidate pool, or every upstream evidence URL's current availability.
The first eight source-content verification decisions are agent judgments with explicit scope and links.
