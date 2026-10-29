import urllib.request,json,pathlib
urls={'postmortems.tsv':'https://zenodo.org/api/records/4017712/files/postmortems.tsv/content','zenodo_README.txt':'https://zenodo.org/api/records/4017712/files/README.txt/content','yc_tree.json':'https://api.github.com/repos/rohitvpgawli/why-startups-die/git/trees/main?recursive=1','yc_README.md':'https://raw.githubusercontent.com/rohitvpgawli/why-startups-die/main/README.md','yc_LICENSE':'https://raw.githubusercontent.com/rohitvpgawli/why-startups-die/main/LICENSE'}
for name,url in urls.items():
 try:
  b=urllib.request.urlopen(url,timeout=60).read(); pathlib.Path('data/raw',name).write_bytes(b); print(name,len(b)); print(b.decode('utf8')[:14000] if name in ['yc_tree.json','yc_README.md'] else '')
 except Exception as e: print(e)
