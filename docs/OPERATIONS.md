# Operations and release process

Use Python 3.12+ and PostgreSQL 17+. Pin deployment image digests after testing in your own environment.
`compose.yaml` is a local development database, not a managed production deployment.

1. Install dependencies in a virtual environment: `pip install -r requirements.txt`.
2. Run `python scripts/fetch.py` to validate or restore pinned source downloads.
3. Run `python scripts/pipeline.py` to reproduce every export and quality report.
4. Set `POSTGRES_PASSWORD` privately, then `docker compose up -d --wait`.
5. Set `DATABASE_URL` privately, then `python scripts/load_db.py`.
6. Run `python -m pytest -q`. PostgreSQL integration skips explicitly if DATABASE_URL is absent.
7. Generate a logical backup with `pg_dump --schema=graveyard --format=custom` using libpq environment credentials.

The loader owns the dedicated `graveyard` schema. It replaces its assertion, review, category assignment
and source-record snapshot in a transaction, upserts entities and removes stale entities. It does not
touch other schemas. Never point it at an unrelated application schema. Run one loader at a time.
Use a migration/owner credential for ingestion, a SELECT-only credential for application SQL,
encrypted connections outside localhost, encrypted backups, retention limits and tested restoration.
The bundled API reads immutable export files; PostgreSQL remains the authoritative relational store.
Publish exports and database loads together from the same checksummed snapshot. Restart API workers
after publishing new exports. Protect the API behind HTTPS, a request-size limit and rate limiting.
API keys belong only in Playground's server environment, never client JavaScript. Source prose is
untrusted retrieval content: downstream LLMs must never execute instructions contained in records.

## Refresh

Do not silently refresh mutable source URLs. Download new material into a staging directory,
recheck the dataset-specific license, compare row/status/field changes, and inspect conflicts.
Add a source register entry or revise its reviewed snapshot and hashes only after approval by a data maintainer.
Do not re-run exploratory `discover.py`, `download_more.py`, or `yc_download.py` to update a release;
they record the initial acquisition work and can overwrite raw snapshots. Use `fetch.py` for pinned rebuilds.

Reviews in data/reviews.json must match a source ID and record ID. Read explicit closure evidence,
identify the historical venture, inspect acquisitions/pivots and specify the scope. A dead URL,
an Inactive flag, bankruptcy protection or down round alone cannot verify closure. Exact dates
must be supported; year-only values remain years. Re-review past findings when new evidence conflicts.
No automatic AI labels promote candidates to verified status. Confidence is ordinal evidence strength,
not calibrated probability. The eight initial decisions were agent reviews, not independent human audits.

## Availability and limitations

Missing/blocked primary pages remain candidates. Examples encountered: LinkedIn Shyp and Yeloha posts
could not be retrieved; old NewsTilt and Tutorspree URLs returned 404; Wesabe domain failed DNS.
The independently reviewed sample is deliberately small. Do not advertise this release as 8,000
verified failures or as an exhaustive worldwide database. Broader licensing, human adjudication,
additional primary evidence, semantic relevance evaluation and deployment/load testing remain work.
