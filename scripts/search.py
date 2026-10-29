"""Inspectable TF-IDF cosine retrieval, no training or external AI calls."""
import argparse,json,math,re
from collections import Counter
from pipeline import OUT

STOP=set('a an and are as at be by for from in is it of on or that the this to with we our'.split())
def tokens(text): return [t for t in re.findall(r'[a-z0-9]+',text.lower()) if t not in STOP and len(t)>1]
EXPERIMENTS={
 'market_need':'Pre-register a paid concierge pilot: define the target customer, price, minimum paid conversion and repeat-use thresholds before recruiting.',
 'unit_economics':'Run a small paid cohort and measure contribution margin including delivery, support, refunds and repeat purchases before scaling.',
 'capital':'Build a monthly runway model with delayed-funding scenarios and explicit spending stop conditions.',
 'acquisition':'Test two independent acquisition channels with a fixed budget; compare activated paid customers, CAC and retention.',
 'team':'Assign accountable owners and measurable goals for customer development, engineering and operations.'}

def compare(idea,limit=10,country=None,industry=None,include_candidates=False):
    if not idea.strip() or len(idea)>4000: raise ValueError('Idea must contain 1-4000 characters')
    rows=[json.loads(x) for x in (OUT/'startups.jsonl').read_text(encoding='utf8').splitlines()]
    rows=[r for r in rows if (r['status']=='verified_failure' or include_candidates and r['status']=='candidate')
          and (country is None or r['country']==country) and (industry is None or r['industry']==industry)]
    docs=[Counter(tokens(' '.join(str(r.get(k) or '') for k in ['name','industry','product_description','primary_failure_reason','lessons_learned']))) for r in rows]
    df=Counter(t for d in docs for t in d)
    idf={t:math.log((1+len(rows))/(1+n))+1 for t,n in df.items()}
    def vector(c): return {t:(1+math.log(n))*idf[t] for t,n in c.items() if t in idf}
    q=vector(Counter(tokens(idea))); qnorm=math.sqrt(sum(v*v for v in q.values()))
    hits=[]
    for r,d in zip(rows,docs):
        v=vector(d); norm=math.sqrt(sum(x*x for x in v.values()))
        score=sum(q[t]*v.get(t,0) for t in q)/(qnorm*norm) if qnorm and norm else 0
        if score<=0: continue
        experiments=[{'category':c,'proposal':EXPERIMENTS[c],'basis':'generated_hypothesis_not_historical_fact','evidence_url':r['verification']['url']} for c in r['failure_categories'] if c in EXPERIMENTS]
        hits.append({'id':r['id'],'name':r['name'],'status':r['status'],'similarity':round(score,6),
                     'shared_terms':sorted(set(q)&set(v)),'evidence_urls':r['evidence_urls'],
                     'review':r['verification'],'failure_reason':r['primary_failure_reason'],
                     'validation_experiments':experiments})
    hits.sort(key=lambda x:(-x['similarity'],x['id']))
    return {'method':'tfidf_cosine_v1','warning':'Similarity is not failure probability. This selected failure corpus has no representative survival denominator.',
            'eligible_records':len(rows),'results':hits[:max(1,min(limit,100))]}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('idea');p.add_argument('--limit',type=int,default=10)
    p.add_argument('--country');p.add_argument('--industry');p.add_argument('--include-candidates',action='store_true')
    print(json.dumps(compare(**vars(p.parse_args())),indent=2,ensure_ascii=False))
