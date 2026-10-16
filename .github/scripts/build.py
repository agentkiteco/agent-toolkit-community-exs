"""Generate a static site with fingerprinted assets to avoid mixed cached releases."""
import hashlib
import json
import shutil
from catalog import ROOT, collect

entries=collect()
dist=ROOT/'website/dist'
if dist.exists():
    shutil.rmtree(dist)
shutil.copytree(ROOT/'website/src',dist)
(dist/'catalog.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
index=(dist/'index.html').read_text()
for filename in ['style.css','app.js','icon.svg','catalog.json']:
    original=dist/filename
    digest=hashlib.sha256(original.read_bytes()).hexdigest()[:12]
    hashed=f'{original.stem}.{digest}{original.suffix}'
    original.rename(dist/hashed)
    if filename=='catalog.json':
        index=index.replace('<body>',f'<body data-catalog="./{hashed}">')
    else:
        index=index.replace(f'"{filename}"',f'"{hashed}"')
(dist/'index.html').write_text(index)
(dist/'.nojekyll').touch()
print(f'Built website/dist with {len(entries)} entries and fingerprinted assets.')
