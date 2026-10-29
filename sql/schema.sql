CREATE SCHEMA IF NOT EXISTS graveyard;
CREATE TABLE IF NOT EXISTS graveyard.source (
  id text PRIMARY KEY, name text NOT NULL, url text NOT NULL,
  license text, decision text NOT NULL, metadata jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS graveyard.startup (
  id uuid PRIMARY KEY, name text NOT NULL,
  status text NOT NULL CHECK (status IN ('candidate','verified_failure','active','acquired','pivot')),
  country text, industry text, confidence text NOT NULL,
  profile jsonb NOT NULL, search_document tsvector NOT NULL,
  CHECK (status <> 'verified_failure' OR
    (profile->'verification'->>'url' IS NOT NULL AND profile->'verification'->>'reviewer' IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS startup_search ON graveyard.startup USING gin(search_document);
CREATE INDEX IF NOT EXISTS startup_filters ON graveyard.startup(status,country,industry);
CREATE TABLE IF NOT EXISTS graveyard.source_record (
  source_id text REFERENCES graveyard.source(id), record_id text,
  payload jsonb NOT NULL, PRIMARY KEY(source_id,record_id)
);
CREATE TABLE IF NOT EXISTS graveyard.assertion (
  id text PRIMARY KEY, startup_id uuid NOT NULL REFERENCES graveyard.startup(id),
  source_id text NOT NULL REFERENCES graveyard.source(id), source_record_id text NOT NULL,
  field text NOT NULL, value jsonb NOT NULL, evidence_url text NOT NULL, basis text NOT NULL
);
CREATE INDEX IF NOT EXISTS assertion_startup ON graveyard.assertion(startup_id);
CREATE TABLE IF NOT EXISTS graveyard.failure_category (
  id text PRIMARY KEY, explanation text NOT NULL
);
CREATE TABLE IF NOT EXISTS graveyard.startup_failure (
  startup_id uuid REFERENCES graveyard.startup(id), category_id text REFERENCES graveyard.failure_category(id),
  evidence_url text NOT NULL, classification_basis text NOT NULL,
  PRIMARY KEY(startup_id,category_id)
);
CREATE TABLE IF NOT EXISTS graveyard.verification (
  startup_id uuid PRIMARY KEY REFERENCES graveyard.startup(id),
  reviewed_at date NOT NULL, reviewer text NOT NULL, evidence_url text NOT NULL,
  outcome text NOT NULL, summary text NOT NULL, scope text NOT NULL
);
CREATE OR REPLACE VIEW graveyard.verified_failures AS
SELECT * FROM graveyard.startup WHERE status='verified_failure';
CREATE OR REPLACE FUNCTION graveyard.search_failures(idea text, result_limit integer DEFAULT 10,
  country_filter text DEFAULT NULL, industry_filter text DEFAULT NULL)
RETURNS TABLE(id uuid,name text,rank real,profile jsonb)
LANGUAGE sql STABLE AS $$
  SELECT s.id,s.name,ts_rank_cd(s.search_document,websearch_to_tsquery('english',idea)),s.profile
  FROM graveyard.verified_failures s
  WHERE s.search_document @@ websearch_to_tsquery('english',idea)
    AND (country_filter IS NULL OR s.country=country_filter)
    AND (industry_filter IS NULL OR s.industry=industry_filter)
  ORDER BY 3 DESC,s.id LIMIT greatest(1,least(result_limit,100));
$$;
