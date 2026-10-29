"""Generate documentation from actual exports; no invented statistics."""
import json
from pipeline import ROOT,OUT,FIELDS,TAXONOMY
q=json.loads((OUT/'quality.json').read_text())
definitions={
'website':'Company website reported by source; not a promise it is still live.',
'country':'Reported country, conservatively normalized. Conflicts become null.',
'city':'Reported city.', 'industry':'Source sector or business domain; mixed taxonomies preserved.',
'founders':'Names explicitly supported by a reviewed source; not inferred from article authorship.',
'founded_date':'Exact founding date, ISO YYYY-MM-DD only when supported.',
'shutdown_date':'Exact operating closure date, ISO YYYY-MM-DD only when supported.',
'founded_year':'Year of founding; a YC batch year is not a founding year.',
'shutdown_year':'Reported closure year, with provenance and status gate; not a verification by itself.',
'product_description':'Brief source-reported description of product.',
'features':'Documented product capabilities.', 'target_audience':'Documented customers or users.',
'business_model':'How the business creates and delivers value.',
'monetization':'Documented revenue mechanism.', 'pricing':'Documented price, currency and period.',
'funding_usd':'Reliable total funding in USD only. Currently entirely null because currency reconciliation is pending.',
'investors':'Source-reported investor names, preserved as text; unreviewed assertions are not adjudicated facts.',
'revenue':'Documented revenue with currency and period; never estimated.',
'competitors':'Documented competing companies.', 'market_conditions':'Documented market context at the relevant time.',
'gtm_strategy':'Documented go-to-market approach.',
'primary_failure_reason':'Reviewed attributed causal account; null unless reviewed.',
'secondary_failure_reasons':'Other documented contributing causes.',
'product_market_fit':'Evidence of product-market fit or mismatch.',
'customer_acquisition_issues':'Reviewed evidence of acquisition cost/channel problems.',
'financial_failures':'Documented financing or cash-flow issues.',
'technical_failures':'Documented engineering or reliability failures.',
'operational_failures':'Documented production, supply or delivery issues.',
'team_failures':'Documented team or management issues.',
'warning_signs':'Observed early warning indicators; not hindsight invention.',
'root_causes':'Reviewed deeper causal mechanisms, with uncertainty.',
'lessons_learned':'Source-attributed lessons; not unlabeled AI advice.',
'prevention_strategies':'Documented source prevention proposals; generated experiments are separate API output.'}
verified=[json.loads(x) for x in (OUT/'verified_failure.jsonl').read_text().splitlines()]
text=f'''# Startup Graveyard Intelligence Database for Playground

An evidence-gated research database for [Playground](https://tryplayground.net), with PostgreSQL,
reproducible CSV/JSONL/Parquet exports, source assertions, and citation-bearing idea comparison.

**Release 0.1: {q['status_counts']['verified_failure']} verified historical failures out of the 8,000 target.**
This is a working research release, not a completed 8,000-case corpus or a deployed production service.
All eight verification decisions were agent source-content reviews, not independent human audits.
No fictional companies were added. Do not treat the total entity count as a failure count.

## Actual collection and status counts

4,905 downloaded rows from three licensed compilations produced **{q['unique_entities']:,} conservatively resolved entities**.
127 source rows were merged by exact normalized name with compatible country information.
Remaining homonyms and unmatched aliases require further review; this is not a guarantee of perfect global uniqueness.

| Canonical status | Entities |
|---|---:|
'''
for k,v in q['status_counts'].items():text+=f'| {k} | {v:,} |\n'
text+='\n| Source | Input rows | Entities with this source | Verified entities with this source |\n|---|---:|---:|---:|\n'
for s,n in q['source_rows'].items():text+=f"| {s} | {n:,} | {q['source_entity_counts'][s]:,} | {q['source_verified_counts'][s]} |\n"
text+='''
Source entity counts overlap and must not be added. Source-wise active/acquired totals differ from canonical
totals because repeated entities were merged. `Inactive` is always a candidate, never automatic verification.
Acquired takes precedence over a failure claim; active takes precedence over both until adjudicated.

## Downloads

Complete exports (not samples):

| Population | CSV | JSONL | Parquet |
|---|---|---|---|
'''
for n in ['startups','verified_failure','candidate','active','acquired','pivot']:
    text+=f'| {n} | [CSV](exports/{n}.csv) | [JSONL](exports/{n}.jsonl) | [Parquet](exports/{n}.parquet) |\n'
text+='''
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
'''
for f in FIELDS:
    typ='integer' if f in ['founded_year','shutdown_year','funding_usd'] else 'string'
    text+=f"| {f} | nullable {typ} | {definitions[f]} | {q['missing'][f]:,} / {q['unique_entities']:,} |\n"
text+='\n## Failure taxonomy\n\nCategories are multi-label source-based classifications. No keyword-only causal inference is used.\n\n| Category | Meaning |\n|---|---|\n'
for k,v in TAXONOMY.items():text+=f'| {k} | {v} |\n'
text+='\n## Coverage and quality\n\nAll-entity coverage includes active/acquired records and is not a failure prevalence estimate.\n\n| Country (top 10) | All entities |\n|---|---:|\n'
for k,v in sorted(q['countries'].items(),key=lambda x:-x[1])[:10]:text+=f'| {k} | {v} |\n'
text+='\n| Industry (top 10; source taxonomies retained) | All entities |\n|---|---:|\n'
for k,v in sorted(q['industries'].items(),key=lambda x:-x[1])[:10]:text+=f'| {k} | {v} |\n'
text+=f"\nVerified-country counts: `{json.dumps(q['verified_countries'])}`.\n\n{q['conflicting_entities']} entities contain conflicting fields; {q['ambiguous_name_groups']} name groups remain unmerged because country data conflicts.\n"
text+='''
**Funding:** zero canonical reliable USD totals; no funding sum/mean is reported. IdeaProof's nominal USD
amounts conflict with narrative currencies in some records; all original amounts remain in raw source records.
Founders, business models, features, revenue, pricing, competitors and GTM are mostly or completely missing.
This release does not pretend to fill those gaps. Exact missing counts for every field are above and in quality.json.

## Examples and Playground integration

Real verified example:

```json
'''
example=next(r for r in verified if r['name']=='Dinnr')
text+=json.dumps({k:example[k] for k in ['id','name','status','shutdown_date','product_description','primary_failure_reason','evidence_urls']},indent=2)
text+='''
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
'''
(ROOT/'README.md').write_text(text,encoding='utf8')
print('README generated from actual exports')
