import urllib.request,json,pathlib
urls={'ideaproof.json':'https://ideaproof.io/data/startup-failures.json','zenodo_metadata.json':'https://zenodo.org/api/records/4017712','yc_metadata.json':'https://api.github.com/repos/rohitvpgawli/why-startups-die','analysis_metadata.json':'https://api.github.com/repos/JoaoJimenez/Startup_failures_analysis'}
for name,url in urls.items():
 try:
  b=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'PlaygroundResearch/1.0'}),timeout=60).read(); pathlib.Path('data/raw',name).write_bytes(b)
  obj=json.loads(b); print(name,len(b),str(obj)[:3500])
 except Exception as e: print(name,str(e))
