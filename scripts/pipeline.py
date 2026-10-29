"""Deterministic, offline-first licensed-source normalization and exports."""
import csv, hashlib, json, re, unicodedata, uuid
from collections import Counter, defaultdict
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
OUT = ROOT / 'exports'
FIELDS = ['website','country','city','industry','founders','founded_date','shutdown_date',
          'founded_year','shutdown_year','product_description','features','target_audience',
          'business_model','monetization','pricing','funding_usd','investors','revenue',
          'competitors','market_conditions','gtm_strategy','primary_failure_reason',
          'secondary_failure_reasons','product_market_fit','customer_acquisition_issues',
          'financial_failures','technical_failures','operational_failures','team_failures',
          'warning_signs','root_causes','lessons_learned','prevention_strategies']
TAXONOMY = {
 'market_need': 'Insufficient demonstrated customer demand or product-market fit.',
 'unit_economics': 'Revenue per customer or order does not cover associated costs.',
 'capital': 'Cash depletion or inability to secure required financing.',
 'acquisition': 'Customer acquisition or distribution does not scale economically.',
 'competition': 'Competitive pressure limits adoption or differentiation.',
 'technical': 'Product engineering, reliability or feasibility problems.',
 'operations': 'Supply chain, manufacturing or service delivery problems.',
 'team': 'Team capability, alignment or management problems.',
 'governance': 'Governance, fraud allegations or financial controls problems.',
 'regulatory': 'Legal or regulatory restrictions impede the business.',
 'timing': 'Market timing or macroeconomic conditions.',
 'unknown': 'No sufficiently reviewed causal evidence.'}

def clean(v):
    if v is None: return None
    if isinstance(v, str):
        v = unicodedata.normalize('NFKC', v).strip()
        return None if v.casefold() in ('','unknown','n/a','na','null','none','-') else v
    return v

def key(v):
    return re.sub(r'[^\w]', '', unicodedata.normalize('NFKC', v).casefold())

def year(v):
    v = str(v or '')
    return int(v) if re.fullmatch(r'(19|20)\d{2}', v) and int(v) <= 2026 else None

def country(v):
    v = clean(v)
    return {'USA':'United States','US':'United States','United States of America':'United States',
            'UK':'United Kingdom'}.get(v,v)

def sources():
    return json.loads((ROOT/'data/sources.json').read_text(encoding='utf8'))

def source_rows():
    for r in json.loads((RAW/'ideaproof.json').read_text(encoding='utf8'))['records']:
        yield dict(source='ideaproof', source_id=r['slug'], name=r['name'], url=r['url'],
                   source_status='failure_claim', fields={
                       'country':country(r.get('country')), 'industry':r.get('industry'),
                       'founded_year':year(r.get('founded')), 'shutdown_year':year(r.get('failed')),
                       # Currency ambiguity: USD label conflicts with AUD narrative in some rows.
                       # Preserve funding as an assertion but do not canonicalize it as USD.
                       'investors':r.get('investors'), 'primary_failure_reason':r.get('failure_reason'),
                       'lessons_learned':r.get('lesson')}, raw=r)
    with (RAW/'postmortems.tsv').open(encoding='utf8',newline='') as f:
        rows=csv.reader(f,delimiter='\t'); next(rows)
        for r in rows:
            if not clean(r[4]): continue
            yield dict(source='zenodo',source_id=r[0], name=r[4],url=r[3] or r[2],
                       source_status='postmortem_candidate',fields={
                           'country':country(r[16]),'founded_year':year(r[17]),
                           'shutdown_year':year(r[18]),'industry':r[22],
                           'product_description':r[7]},raw=dict(zip(
                               ['id','title','postmortem_url','mirror_url','company_name','company_profile_url',
                                'other_url','description','other_sources','rater1','rater2','agreement','rater3',
                                'software_final','founder_statement','useful','country','start_year','closing_year',
                                'active_period','calculated_period','considered_period','business_domain','author'],r)))
    with (RAW/'yc_companies.csv').open(encoding='utf8',newline='') as f:
        for r in csv.DictReader(f):
            yield dict(source='yc',source_id=r['company_id'],name=r['name'],
                       url='https://www.ycombinator.com/companies/'+r['company_id'],
                       source_status=r['status'].lower(),fields={
                           'website':r['website'],'industry':r['subindustry'],
                           'country':country(r['region']) if r['region'] not in ('Remote','') and ';' not in r['region'] else None,
                           'product_description':r['one_liner']},raw=r)

def build():
    OUT.mkdir(exist_ok=True)
    reviews=json.loads((ROOT/'data/reviews.json').read_text(encoding='utf8'))
    rows=list(source_rows()); grouped=defaultdict(list)
    for r in rows: grouped[key(r['name'])].append(r)
    records=[]; claims=[]; duplicates=[]
    for namekey, group in sorted(grouped.items()):
        countries={r['fields'].get('country') for r in group if r['fields'].get('country')}
        # Exact normalized name + compatible country only. Ambiguous matches remain separate.
        buckets=defaultdict(list)
        for r in group:
            buckets[(r['fields'].get('country') or r['source']+':'+r['source_id']) if len(countries)>1 else 'same'].append(r)
        if len(buckets)>1: duplicates.append({'name_key':namekey,'reason':'country conflict; not merged','sources':[(r['source'],r['source_id']) for r in group]})
        for bucket, members in sorted(buckets.items()):
            sid=str(uuid.uuid5(uuid.NAMESPACE_URL,'playground:startup:'+namekey+':'+bucket))
            record={f:None for f in FIELDS}
            record.update(id=sid,name=members[0]['name'].strip(),status='candidate',confidence='unverified',
                          source_ids=sorted({r['source'] for r in members}),evidence_urls=sorted({r['url'] for r in members}),
                          failure_categories=[],verification=None,conflicts={})
            statuses={r['source_status'] for r in members}
            if 'active' in statuses: record['status']='active'
            elif 'acquired' in statuses: record['status']='acquired'
            for field in FIELDS:
                vals=[]
                for r in members:
                    v=clean(r['fields'].get(field))
                    if v is not None:
                        vals.append(v)
                        claims.append(dict(startup_id=sid,source_id=r['source'],source_record_id=r['source_id'],
                                           field=field,value=v,evidence_url=r['url'],basis='source_reported_not_independently_verified'))
                uniq=list(dict.fromkeys(vals))
                if len(uniq)==1: record[field]=uniq[0]
                elif len(uniq)>1: record['conflicts'][field]=uniq
            # Source causal labels are preserved as claims, never promoted to reviewed facts.
            for f in ['primary_failure_reason','lessons_learned']: record[f]=None
            matches=[v for v in reviews if any(r['source']==v['match_source'] and r['source_id']==v['match_id'] for r in members)]
            if len(matches)>1: raise ValueError('Multiple reviews for '+sid)
            if matches:
                review=matches[0]
                record.update(status=review['status'],confidence=review['confidence'],verification=review)
                for f,v in review.get('fields',{}).items():
                    record[f]=v
                    claims.append(dict(startup_id=sid,source_id='review',source_record_id=review['match_id'],
                                       field=f,value=v,evidence_url=review['url'],basis='reviewed_source_paraphrase'))
                record['failure_categories']=review.get('categories',[])
                record['evidence_urls']=sorted(set(record['evidence_urls']+[review['url']]))
            if 'active' in statuses and record['status']=='verified_failure':
                record.update(status='candidate',confidence='conflicting')
            if record['founded_year'] and record['shutdown_year'] and record['founded_year']>record['shutdown_year']:
                record['conflicts']['chronology']=[record['founded_year'],record['shutdown_year']]
                record['shutdown_year']=None
            records.append(record)
    write_exports('startups',records)
    for status in ['verified_failure','candidate','active','acquired','pivot']:
        write_exports(status,[r for r in records if r['status']==status])
    write_jsonl(OUT/'assertions.jsonl',claims)
    write_jsonl(OUT/'source_records.jsonl',rows)
    (OUT/'duplicate_review.json').write_text(json.dumps(duplicates,indent=2,ensure_ascii=False),encoding='utf8')
    stats={'target':8000,'unique_entities':len(records),'status_counts':dict(Counter(r['status'] for r in records)),
           'source_rows':dict(Counter(r['source'] for r in rows)),
           'source_entity_counts':{s:sum(s in r['source_ids'] for r in records) for s in ['ideaproof','zenodo','yc']},
           'source_verified_counts':{s:sum(s in r['source_ids'] and r['status']=='verified_failure' for r in records) for s in ['ideaproof','zenodo','yc']},
           'countries':dict(Counter(r['country'] or 'Unknown' for r in records)),
           'industries':dict(Counter(r['industry'] or 'Unknown' for r in records)),
           'verified_countries':dict(Counter(r['country'] or 'Unknown' for r in records if r['status']=='verified_failure')),
           'missing':{f:sum(r[f] is None for r in records) for f in FIELDS},
           'conflicting_entities':sum(bool(r['conflicts']) for r in records),
           'funding':{'canonical_usd_count':0,'reason':'Currency ambiguity; original source amounts retained only in raw records.'},
           'ambiguous_name_groups':len(duplicates)}
    (OUT/'quality.json').write_text(json.dumps(stats,indent=2,ensure_ascii=False),encoding='utf8')
    (OUT/'taxonomy.json').write_text(json.dumps(TAXONOMY,indent=2),encoding='utf8')
    files=list(RAW.iterdir())+list(OUT.iterdir())
    checks={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files) if p.is_file() and p.name!='checksums.json'}
    (OUT/'checksums.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
    print(json.dumps({k:stats[k] for k in ['unique_entities','status_counts','source_rows']}))
    return records

def write_jsonl(path,rows):
    path.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows),encoding='utf8')

def write_exports(name,rows):
    write_jsonl(OUT/(name+'.jsonl'),rows)
    # Flat representation is identical in CSV and Parquet: complex values are JSON strings.
    keys=['id','name','status','confidence']+FIELDS+['source_ids','evidence_urls','failure_categories','verification','conflicts']
    flat=[{k:json.dumps(r[k],ensure_ascii=False,sort_keys=True) if isinstance(r[k],(dict,list)) else r[k] for k in keys} for r in rows]
    with (OUT/(name+'.csv')).open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(flat)
    schema=pa.schema([(k,pa.int64() if k in ['founded_year','shutdown_year','funding_usd'] else pa.string()) for k in keys])
    pq.write_table(pa.Table.from_pylist(flat,schema=schema),OUT/(name+'.parquet'),compression='zstd')

if __name__=='__main__': build()
