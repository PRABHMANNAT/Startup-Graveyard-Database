import urllib.request,pathlib,json,csv
base='https://raw.githubusercontent.com/rohitvpgawli/why-startups-die/13b7bce45f0f5da544303a17fa1c6235a9cbb619/'
for f in ['DATA_LICENSE.md','releases/v1.0.0/companies.csv','releases/v1.0.0/shutdown_enrichment.csv']:
 b=urllib.request.urlopen(base+f,timeout=60).read(); pathlib.Path('data/raw','yc_'+f.split('/')[-1]).write_bytes(b)
rows=list(csv.DictReader(open('data/raw/yc_companies.csv',encoding='utf8')));print(len(rows)); print(rows[:2]);print(list(csv.DictReader(open('data/raw/yc_shutdown_enrichment.csv',encoding='utf8')))[:4])
