import csv,json,pathlib
rows=list(csv.reader(open('data/raw/postmortems.tsv',encoding='utf8'),delimiter='\t'))[1:]
reviews=[]
for name,url,status,summary,fields,categories in json.loads(pathlib.Path('data/review_specs.json').read_text(encoding='utf8')):
 r=next(x for x in rows if x[4].strip()==name)
 reviews.append(dict(match_source='zenodo',match_id=r[0],name=name,url=url,status=status,confidence='high' if status=='verified_failure' else 'reviewed',reviewer='Codex source-content review',reviewed_at='2026-10-30',scope='Historical operating venture; not legal-entity dissolution or current trademark status',summary=summary,fields=fields,categories=categories))
pathlib.Path('data/reviews.json').write_text(json.dumps(reviews,indent=2),encoding='utf8')
