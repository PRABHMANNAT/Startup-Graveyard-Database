"""Fetch only allowlisted licensed datasets; never overwrite a pinned snapshot silently."""
import hashlib, json, urllib.request
from pipeline import RAW, ROOT, sources

def main():
    expected=json.loads((ROOT/'exports/checksums.json').read_text())
    for source in sources():
        if source['decision']!='import': continue
        path=RAW/source['file']
        digest=expected['data/raw/'+source['file']]
        if path.exists():
            if hashlib.sha256(path.read_bytes()).hexdigest()!=digest: raise ValueError('Snapshot modified: '+str(path))
            print('Verified local snapshot',path.name);continue
        req=urllib.request.Request(source['download_url'],headers={'User-Agent':'Playground-Graveyard-Research/1.0'})
        with urllib.request.urlopen(req,timeout=60) as response: data=response.read(20_000_001)
        if len(data)>20_000_000: raise ValueError('Download exceeds limit')
        if hashlib.sha256(data).hexdigest()!=digest: raise ValueError('Upstream changed; review license and diff before accepting a new snapshot')
        path.write_bytes(data)

if __name__=='__main__': main()
