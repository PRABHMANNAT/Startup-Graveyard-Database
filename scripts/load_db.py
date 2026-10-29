"""Atomic idempotent load; requires DATABASE_URL, never logs credentials."""
import hashlib,json,os
import psycopg
from psycopg.types.json import Jsonb
from pipeline import ROOT, OUT, sources

def read(name):
    with (OUT/name).open(encoding='utf8') as f:
        return [json.loads(line) for line in f]

def load():
    with psycopg.connect(os.environ['DATABASE_URL']) as conn:
        conn.execute((ROOT/'sql/schema.sql').read_text())
        for s in sources():
            conn.execute('INSERT INTO graveyard.source VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET metadata=EXCLUDED.metadata',
                         (s['id'],s['name'],s['url'],s.get('license'),s['decision'],Jsonb(s)))
        records=read('startups.jsonl')
        for r in records:
            text=' '.join(str(r.get(k) or '') for k in ['name','industry','product_description','primary_failure_reason','lessons_learned'])
            conn.execute('''INSERT INTO graveyard.startup VALUES (%s,%s,%s,%s,%s,%s,%s,to_tsvector('english',%s))
                ON CONFLICT(id) DO UPDATE SET name=EXCLUDED.name,status=EXCLUDED.status,country=EXCLUDED.country,
                industry=EXCLUDED.industry,confidence=EXCLUDED.confidence,profile=EXCLUDED.profile,search_document=EXCLUDED.search_document''',
                         (r['id'],r['name'],r['status'],r['country'],r['industry'],r['confidence'],Jsonb(r),text))
        # Owned snapshot only: remove stale entities and dependent claims within this dedicated schema.
        ids=[r['id'] for r in records]
        for table in ['assertion','startup_failure','verification']:
            conn.execute('DELETE FROM graveyard.'+table)
        conn.execute('DELETE FROM graveyard.startup WHERE NOT (id=ANY(%s::uuid[]))',(ids,))
        conn.execute('DELETE FROM graveyard.source_record')
        with conn.cursor() as cur:
            cur.executemany('INSERT INTO graveyard.source_record VALUES (%s,%s,%s)',
                            [(r['source'],r['source_id'],Jsonb(r)) for r in read('source_records.jsonl')])
            cur.executemany('INSERT INTO graveyard.assertion VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING',
                [(hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest(),r['startup_id'],r['source_id'],r['source_record_id'],r['field'],Jsonb(r['value']),r['evidence_url'],r['basis']) for r in read('assertions.jsonl')])
        for k,v in json.loads((OUT/'taxonomy.json').read_text()).items():
            conn.execute('INSERT INTO graveyard.failure_category VALUES (%s,%s) ON CONFLICT(id) DO UPDATE SET explanation=EXCLUDED.explanation',(k,v))
        for r in records:
            if not r['verification']: continue
            v=r['verification']
            conn.execute('INSERT INTO graveyard.verification VALUES (%s,%s,%s,%s,%s,%s,%s)',(r['id'],v['reviewed_at'],v['reviewer'],v['url'],r['status'],v['summary'],v['scope']))
            for category in r['failure_categories']:
                conn.execute('INSERT INTO graveyard.startup_failure VALUES (%s,%s,%s,%s)',(r['id'],category,v['url'],'reviewed_source_classification'))
        print('Committed',len(records),'entities to PostgreSQL')

if __name__=='__main__': load()
