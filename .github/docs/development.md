# Development

Requires Python 3.11+ and Node.js for JavaScript syntax checking. The website has no JavaScript dependencies.

```sh
python -m pip install -r .github/requirements.txt
python .github/scripts/validate.py
python -m unittest discover -s .github/tests
python .github/scripts/build.py
node --check website/src/app.js
python -m http.server 8000 --directory website/dist
```

Open http://localhost:8000. Generated output is ignored. All asset paths are relative for GitHub Pages project hosting.

## Layout

- `skills/`, `prompts/`, `instructions/`: canonical catalog content.
- `website/src/`: landing source; `website/dist/` is generated.
- `.github/scripts/`: validation, catalog generation, and website build.
- `.github/tests/`: catalog validator tests.
- `.github/templates/example/`: starter for a new skill; excluded from catalog.
- `.github/docs/`: installation and development guides.
- `.github/workflows/`: validation and GitHub Pages publication.

The catalog is generated from Markdown metadata during each build. Never maintain a second copy in the website. Keep mandatory skill resources inside their skill folder.
