import csv,hashlib,json,sys
from pathlib import Path
import pyarrow.parquet as pq
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from pipeline import ROOT,OUT,FIELDS,key,year,clean,build
from search import compare

def records(): return [json.loads(s) for s in (OUT/'startups.jsonl').read_text(encoding='utf8').splitlines()]
def test_checksums():
    for path,digest in json.loads((OUT/'checksums.json').read_text()).items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
def test_identity_and_evidence():
    rows=records();assert len({r['id'] for r in rows})==len(rows)
    for r in rows:
        assert r['name'] and r['source_ids'] and r['evidence_urls']
        if r['status']=='verified_failure':
            assert r['verification']['status']=='verified_failure'
            assert r['verification']['url'].startswith('https://')
            assert r['verification']['summary']
        assert not r['founded_year'] or not r['shutdown_year'] or r['founded_year']<=r['shutdown_year']
def test_all_jsonl_line_framing():
    for path in OUT.glob('*.jsonl'):
        for line in path.read_text(encoding='utf8').splitlines():
            assert isinstance(json.loads(line),dict)
def test_export_parity():
    for name in ['startups','verified_failure','candidate','active','acquired','pivot']:
        jsonrows=[json.loads(s) for s in (OUT/(name+'.jsonl')).read_text(encoding='utf8').splitlines()]
        with (OUT/(name+'.csv')).open(encoding='utf8',newline='') as f: csvrows=list(csv.DictReader(f))
        prows=pq.read_table(OUT/(name+'.parquet')).to_pylist()
        assert [r['id'] for r in jsonrows]==[r['id'] for r in csvrows]==[r['id'] for r in prows]
        for a,b in zip(jsonrows,prows):
            for k,v in a.items(): assert b[k]==(json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,(dict,list)) else v)
def test_no_false_verification():
    rows=records()
    assert all(r['status']!='verified_failure' for r in rows if r['name'] in ['Vidme','Take Eat Easy','Dijiwan','Sansaire'])
    assert all(r['funding_usd'] is None for r in rows)
def test_normalizers():
    assert key(' Acme, Inc. ')==key('ACME INC')
    assert year('unknown') is None and year('2027') is None and year('2014')==2014
    assert clean('n/a') is None
def test_retrieval():
    r=compare('same day cooking ingredients delivery')
    assert r['results'][0]['name']=='Dinnr'
    assert all(x['status']=='verified_failure' for x in r['results'])
    assert r['results'][0]['validation_experiments']
    assert compare('zzzznonexistent')['results']==[]
    assert compare('delivery',country='Not a country')['results']==[]
def test_api(monkeypatch):
    from fastapi.testclient import TestClient
    from api import app
    monkeypatch.setenv('GRAVEYARD_API_KEY','test-only-key')
    client=TestClient(app)
    assert client.post('/compare',json={'idea':'delivery'}).status_code==401
    headers={'X-API-Key':'test-only-key'}
    assert client.post('/compare',headers=headers,json={'idea':'delivery'}).status_code==200
    assert client.post('/compare',headers=headers,json={'idea':' '}).status_code==422
    assert client.post('/compare',headers=headers,json={'idea':'x','limit':1000}).status_code==422
def test_reproducibility():
    before=(OUT/'checksums.json').read_bytes();build();assert before==(OUT/'checksums.json').read_bytes()
