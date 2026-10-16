# Repository instructions

Keep skills portable and self-contained. Use `example` for generic placeholders.
Keep required skill resources inside the skill folder and use relative links.
Treat `skills/`, `prompts/`, and `instructions/` as the only catalog sources.
Do not edit generated `website/dist/` content or duplicate catalog metadata in HTML.
Do not claim platform compatibility without documenting how it was checked.
Never commit credentials, tokens, private examples, or generated build output.

Run before committing:

```sh
python .github/scripts/validate.py
python -m unittest discover -s .github/tests
python .github/scripts/build.py
node --check website/src/app.js
```

The site is hosted on GitHub Pages; preserve relative asset URLs.
