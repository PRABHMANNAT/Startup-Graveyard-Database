# Startup Graveyard Intelligence Database for Playground

An evidence-gated research database for [Playground](https://tryplayground.net), with PostgreSQL,
reproducible CSV/JSONL/Parquet exports, source assertions, and citation-bearing idea comparison.

**Release 0.1: 8 verified historical failures out of the 8,000 target.**
This is a working research release, not a completed 8,000-case corpus or a deployed production service.
All eight verification decisions were agent source-content reviews, not independent human audits.
No fictional companies were added. Do not treat the total entity count as a failure count.

## Actual collection and status counts

4,905 downloaded rows from three licensed compilations produced **4,778 conservatively resolved entities**.
127 source rows were merged by exact normalized name with compatible country information.
Remaining homonyms and unmatched aliases require further review; this is not a guarantee of perfect global uniqueness.

| Canonical status | Entities |
|---|---:|
| active | 3,044 |
| candidate | 1,530 |
| verified_failure | 8 |
| acquired | 196 |

| Source | Input rows | Entities with this source | Verified entities with this source |
|---|---:|---:|---:|
| ideaproof | 1,028 | 1,007 | 3 |
| zenodo | 311 | 311 | 8 |
| yc | 3,566 | 3,534 | 0 |

Source entity counts overlap and must not be added. Source-wise active/acquired totals differ from canonical
totals because repeated entities were merged. `Inactive` is always a candidate, never automatic verification.
Acquired takes precedence over a failure claim; active takes precedence over both until adjudicated.

## Downloads

Complete exports (not samples):

| Population | CSV | JSONL | Parquet |
|---|---|---|---|
| startups | [CSV](exports/startups.csv) | [JSONL](exports/startups.jsonl) | [Parquet](exports/startups.parquet) |
| verified_failure | [CSV](exports/verified_failure.csv) | [JSONL](exports/verified_failure.jsonl) | [Parquet](exports/verified_failure.parquet) |
| candidate | [CSV](exports/candidate.csv) | [JSONL](exports/candidate.jsonl) | [Parquet](exports/candidate.parquet) |
| active | [CSV](exports/active.csv) | [JSONL](exports/active.jsonl) | [Parquet](exports/active.parquet) |
| acquired | [CSV](exports/acquired.csv) | [JSONL](exports/acquired.jsonl) | [Parquet](exports/acquired.parquet) |
| pivot | [CSV](exports/pivot.csv) | [JSONL](exports/pivot.jsonl) | [Parquet](exports/pivot.parquet) |

Additional full datasets: [assertions](exports/assertions.jsonl), [source records](exports/source_records.jsonl),
[quality report](exports/quality.json), [duplicate review queue](exports/duplicate_review.json),
[checksums](exports/checksums.json). All files are below GitHub's 100 MB limit; Git LFS is unnecessary for this release.
JSONL preserves types and nulls. CSV uses empty cells for null and JSON strings for nested fields;
Parquet uses typed nullable scalar columns and JSON strings for nested fields, matching CSV's structure.
Raw CSV text is untrusted: when opening in spreadsheet applications import columns as text to prevent formula execution.

## Sources, licenses and attribution

Data is **CC BY 4.0**, code is MIT. Preserve attribution and disclose normalization changes.
See [full source/license decisions](docs/SOURCES.md), [source register](data/sources.json), and [code license](LICENSE).
IdeaProof Research Team (2026); Melegati, Edison & Wang (2020), DOI 10.5281/zenodo.4017712;
Gawli (2026), Startup Lifecycle Project v1.0.0. No endorsement is implied.
The YC compilation's data license is distinct from its MIT code license. Linked articles retain their rights;
we redistribute no article bodies. Original review summaries are short factual paraphrases.
GTM Right, Autopsy, the JoaoJimenez repo, the noncommercial Kaggle compilation and CB Insights were not bulk imported.
Hugging Face discovery found no suitable additional licensed company-failure dataset in this pass.

## Architecture and reproducibility

Licensed pinned downloads → source rows → exact-name/country entity resolution → field assertions and
conflict detection → explicit review gate → status-separated exports → atomic PostgreSQL load → retrieval/API.

Raw files are immutable release inputs. `scripts/fetch.py` verifies SHA-256 before reuse or restoring
a missing dataset. Mutable upstream changes are rejected for manual license/content review.
`scripts/pipeline.py` works offline and produces deterministic exports, stable UUIDs and analytics.
Canonical identity can change when a previously unknown homonym is resolved; review migrations before refreshing.
Every populated canonical field has a source assertion, except identity/status metadata derived by documented rules.
Conflicts are retained in `conflicts`; disputed fields are null unless explicitly reviewed.
Dates of incomplete precision stay years. Empty and unknown values remain null, never zero.

`verified_failure` means the historical operating venture has explicit closure/postmortem evidence that
was read and matched to the company. It does not assert legal dissolution, absence of later asset sales,
or current ownership of a brand. Bankruptcy protection, acquisition, a failed product, funding decline,
inactive labels and dead websites do not alone establish startup failure.
Vidme is excluded after its own announcement reported acquisition. Take Eat Easy, Dijiwan and Sansaire
remain candidates because the reviewed material does not settle the required terminal-event distinction.

## Installation and running

Python 3.12+, PostgreSQL 17+, optionally Docker Compose:

```sh
python -m venv .venv
# Activate .venv using your shell, then:
pip install -r requirements.txt
python scripts/fetch.py
python scripts/pipeline.py
# Set POSTGRES_PASSWORD securely in your environment.
docker compose up -d --wait
# Set DATABASE_URL to your PostgreSQL connection string securely.
python scripts/load_db.py
python -m pytest -q
python scripts/search.py "same day cooking ingredients delivery" --limit 5
python scripts/document.py
```

PowerShell uses `$env:VARIABLE='value'`; POSIX shells use `export VARIABLE='value'`.
The loader transaction owns only the `graveyard` schema and replaces that schema's snapshot.
Never use it for unrelated data. See [operations, updates, backup and deployment](docs/OPERATIONS.md).

## Complete schema and data dictionary

Executable DDL: [sql/schema.sql](sql/schema.sql). Profiles store sparse domain fields as JSONB;
entities, sources, raw rows, assertions, verification and failure categories are relationally separated.

| Table | Columns and meaning |
|---|---|
| source | id PK, name attribution, url origin, license SPDX-style ID, decision import/exclude/original, metadata JSONB license audit |
| startup | id UUID PK, name display, status constrained outcome, country, industry, confidence ordinal, profile JSONB full export record, search_document English tsvector |
| source_record | source_id FK + record_id composite PK, payload JSONB original row plus source mapping |
| assertion | id SHA-256 PK, startup_id FK, source_id FK, source_record_id original ID, field, value JSONB, evidence_url, basis source-reported or reviewed paraphrase |
| failure_category | id PK, explanation definition |
| startup_failure | startup_id FK + category_id FK composite PK, evidence_url, classification_basis |
| verification | startup_id FK/PK, reviewed_at date, reviewer, evidence_url, outcome, summary, scope |

`verified_failures` is the status-gated view. `search_failures(idea,result_limit,country_filter,industry_filter)`
is a bounded, parameterizable full-text search function. GIN supports search; B-tree indexes support filtering and provenance lookup.

Profile metadata fields: `id` stable UUID; `name` source display name; `status` candidate/verified_failure/active/acquired/pivot;
`confidence` unverified/high/reviewed/conflicting, **not a numeric calibrated score**;
`source_ids` attribution IDs; `evidence_urls` links; `failure_categories` reviewed taxonomy IDs;
`verification` review object or null; `conflicts` field→disputed values.
Review objects contain match_source, match_id, name, url, status, confidence, reviewer, reviewed_at,
scope, summary, fields (reviewed overrides), and categories. Assertion records use the table fields above.

| Profile field | Type | Definition | Missing / all entities |
|---|---|---|---:|
| website | nullable string | Company website reported by source; not a promise it is still live. | 1,285 / 4,778 |
| country | nullable string | Reported country, conservatively normalized. Conflicts become null. | 226 / 4,778 |
| city | nullable string | Reported city. | 4,775 / 4,778 |
| industry | nullable string | Source sector or business domain; mixed taxonomies preserved. | 234 / 4,778 |
| founders | nullable string | Names explicitly supported by a reviewed source; not inferred from article authorship. | 4,776 / 4,778 |
| founded_date | nullable string | Exact founding date, ISO YYYY-MM-DD only when supported. | 4,778 / 4,778 |
| shutdown_date | nullable string | Exact operating closure date, ISO YYYY-MM-DD only when supported. | 4,777 / 4,778 |
| founded_year | nullable integer | Year of founding; a YC batch year is not a founding year. | 3,726 / 4,778 |
| shutdown_year | nullable integer | Reported closure year, with provenance and status gate; not a verification by itself. | 3,693 / 4,778 |
| product_description | nullable string | Brief source-reported description of product. | 994 / 4,778 |
| features | nullable string | Documented product capabilities. | 4,778 / 4,778 |
| target_audience | nullable string | Documented customers or users. | 4,778 / 4,778 |
| business_model | nullable string | How the business creates and delivers value. | 4,778 / 4,778 |
| monetization | nullable string | Documented revenue mechanism. | 4,778 / 4,778 |
| pricing | nullable string | Documented price, currency and period. | 4,778 / 4,778 |
| funding_usd | nullable integer | Reliable total funding in USD only. Currently entirely null because currency reconciliation is pending. | 4,778 / 4,778 |
| investors | nullable string | Source-reported investor names, preserved as text; unreviewed assertions are not adjudicated facts. | 4,217 / 4,778 |
| revenue | nullable string | Documented revenue with currency and period; never estimated. | 4,778 / 4,778 |
| competitors | nullable string | Documented competing companies. | 4,778 / 4,778 |
| market_conditions | nullable string | Documented market context at the relevant time. | 4,778 / 4,778 |
| gtm_strategy | nullable string | Documented go-to-market approach. | 4,778 / 4,778 |
| primary_failure_reason | nullable string | Reviewed attributed causal account; null unless reviewed. | 4,773 / 4,778 |
| secondary_failure_reasons | nullable string | Other documented contributing causes. | 4,778 / 4,778 |
| product_market_fit | nullable string | Evidence of product-market fit or mismatch. | 4,778 / 4,778 |
| customer_acquisition_issues | nullable string | Reviewed evidence of acquisition cost/channel problems. | 4,777 / 4,778 |
| financial_failures | nullable string | Documented financing or cash-flow issues. | 4,778 / 4,778 |
| technical_failures | nullable string | Documented engineering or reliability failures. | 4,778 / 4,778 |
| operational_failures | nullable string | Documented production, supply or delivery issues. | 4,778 / 4,778 |
| team_failures | nullable string | Documented team or management issues. | 4,778 / 4,778 |
| warning_signs | nullable string | Observed early warning indicators; not hindsight invention. | 4,777 / 4,778 |
| root_causes | nullable string | Reviewed deeper causal mechanisms, with uncertainty. | 4,778 / 4,778 |
| lessons_learned | nullable string | Source-attributed lessons; not unlabeled AI advice. | 4,775 / 4,778 |
| prevention_strategies | nullable string | Documented source prevention proposals; generated experiments are separate API output. | 4,778 / 4,778 |

## Failure taxonomy

Categories are multi-label source-based classifications. No keyword-only causal inference is used.

| Category | Meaning |
|---|---|
| market_need | Insufficient demonstrated customer demand or product-market fit. |
| unit_economics | Revenue per customer or order does not cover associated costs. |
| capital | Cash depletion or inability to secure required financing. |
| acquisition | Customer acquisition or distribution does not scale economically. |
| competition | Competitive pressure limits adoption or differentiation. |
| technical | Product engineering, reliability or feasibility problems. |
| operations | Supply chain, manufacturing or service delivery problems. |
| team | Team capability, alignment or management problems. |
| governance | Governance, fraud allegations or financial controls problems. |
| regulatory | Legal or regulatory restrictions impede the business. |
| timing | Market timing or macroeconomic conditions. |
| unknown | No sufficiently reviewed causal evidence. |

## Coverage and quality

All-entity coverage includes active/acquired records and is not a failure prevalence estimate.

| Country (top 10) | All entities |
|---|---:|
| United States | 3063 |
| Unknown | 226 |
| India | 204 |
| United Kingdom | 196 |
| China | 171 |
| Unspecified | 86 |
| Canada | 77 |
| France | 70 |
| Germany | 69 |
| Mexico | 49 |

| Industry (top 10; source taxonomies retained) | All entities |
|---|---:|
| B2B | 537 |
| B2B -> Engineering, Product and Design | 409 |
| Unknown | 234 |
| B2B -> Infrastructure | 208 |
| Fintech | 150 |
| Consumer | 140 |
| B2B -> Productivity | 112 |
| B2B -> Operations | 102 |
| B2B -> Finance and Accounting | 96 |
| B2B -> Sales | 89 |

Verified-country counts: `{"Australia": 1, "United States": 6, "United Kingdom": 1}`.

79 entities contain conflicting fields; 23 name groups remain unmerged because country data conflicts.

**Funding:** zero canonical reliable USD totals; no funding sum/mean is reported. IdeaProof's nominal USD
amounts conflict with narrative currencies in some records; all original amounts remain in raw source records.
Founders, business models, features, revenue, pricing, competitors and GTM are mostly or completely missing.
This release does not pretend to fill those gaps. Exact missing counts for every field are above and in quality.json.

## Examples and Playground integration

Real verified example:

```json
{
  "id": "0b1d574a-4a7f-5de6-8983-d2ccce4450b1",
  "name": "Dinnr",
  "status": "verified_failure",
  "shutdown_date": "2014-01-12",
  "product_description": "Same-day delivery of pre-measured cooking ingredients and recipe instructions.",
  "primary_failure_reason": "Insufficient customer demand and repeat purchasing to sustain the service.",
  "evidence_urls": [
    "https://ideaproof.io/failure/dinnr",
    "https://medium.com/@michalbohanes/seven-lessons-i-learned-from-the-failure-of-my-first-startup-dinnr-c166d1cfb8b8"
  ]
}
```

```sql
SELECT name,country,industry FROM graveyard.verified_failures;
SELECT * FROM graveyard.search_failures('ingredients', 10);
SELECT source_id, count(*) FROM graveyard.source_record GROUP BY source_id;
SELECT field,value,evidence_url,basis FROM graveyard.assertion WHERE startup_id = $1;
```

Start the private API after setting a long random `GRAVEYARD_API_KEY` environment variable:

```sh
python -m uvicorn api:app --app-dir scripts --host 127.0.0.1 --port 8000
```

From Playground's **server**, POST `/compare` with header `X-API-Key` and JSON:

```json
{"idea":"same day cooking ingredients delivery","limit":5}
```

Optional exact `country` and `industry` filters are accepted. The API uses the checksummed export
snapshot for deterministic TF-IDF cosine comparison; it does not require a model service or transmit ideas
to external AI providers. SQL full-text retrieval is also available directly against PostgreSQL.
Results contain matched terms, evidence URLs, review summary and category-linked validation experiments.
Candidates are excluded by default and never exposed by the API; the research CLI has an explicit opt-in.
Experiments are labeled `generated_hypothesis_not_historical_fact`. Their proposed tests are original
templates, not claims that historical founders conducted them or that they would have prevented failure.

Similarity is **not** failure probability. No predictive failure rate is derived from a failure-selected corpus.
Lexical TF-IDF is an inspectable baseline, not semantic embedding retrieval. Production relevance evaluation,
human review and deployment hardening remain necessary before relying on this for consequential decisions.

## Tests and limitations

Tests cover all export formats, all JSONL framing, checksums, missing-value/date handling, conservative
verification exclusions, reproducibility, API authentication/input bounds, evidence-bearing retrieval,
and real PostgreSQL loading twice without row duplication. See [validation report](docs/VALIDATION.md).

The gap to 8,000 is 7,992 verified failures. Major advertised archives cannot simply be summed: licensing,
duplicates, active companies, acquisitions and incomplete evidence reduce usable coverage. This pass has
not exhausted every possible source or verified every candidate. The next meaningful work is rights-cleared
bulk expansion and candidate adjudication, not generated filler. Source facts can be stale; coverage favors
English-language technology ventures and public postmortems. No deployment into tryplayground.net was performed.
