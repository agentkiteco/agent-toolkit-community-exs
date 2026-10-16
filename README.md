# Agent Toolkit

A shared home for portable agent skills, prompts, and instructions.

[Browse the catalog](https://agentkiteco.github.io/agent-toolkit-community-exs/) · [Installation](docs/installation.md) · [Contributing](CONTRIBUTING.md)

## Catalog

| Type | Example | Purpose |
| --- | --- | --- |
| Skill | [example](skills/example/SKILL.md) | Self-contained workflow demonstrating the Agent Skills format |
| Prompt | [example](prompts/example.md) | Copyable request with an input placeholder |
| Instruction | [example](instructions/example.md) | Reusable rules to attach explicitly |

All initial entries are illustrative examples. Replace or extend them with your own workflows.

## Install a skill

Using the third-party [Skills CLI](https://github.com/vercel-labs/skills) (requires Node.js):

```sh
npx skills add agentkiteco/agent-toolkit-community-exs --skill example --agent claude-code
npx skills add agentkiteco/agent-toolkit-community-exs --skill example --agent codex
```

Skills are portable; installation support varies by product. Prompts and instructions are copied explicitly. A GitHub repository alone does not install anything into ChatGPT.

## Repository

- `skills/`: canonical, self-contained skills with `SKILL.md`.
- `prompts/`, `instructions/`: standalone Markdown with catalog metadata.
- `templates/example/`: starter for a new skill; excluded from the public catalog.
- `website/src/`: static landing; generated catalog comes from the source files above.
- `scripts/`: validation, catalog generation, and build tooling.
- `docs/`: setup and compatibility notes.
- `.github/workflows/`: validation and Pages deployment.

## Develop

Requires Python 3.11+; no website JavaScript dependencies or bundler.

```sh
python -m pip install -r requirements.txt
python scripts/validate.py
python -m unittest discover -s tests
python scripts/build.py
python -m http.server 8000 --directory website/dist
```

Open http://localhost:8000. Build output is ignored. Relative URLs also work under a GitHub Pages project subpath.

## Publish

Once, choose **Settings → Pages → Source → GitHub Actions**, then run **Actions → Pages → Run workflow**. Later pushes to `main` rebuild and deploy automatically. GitHub App commits may require workflow permission from the connection. See [installation](docs/installation.md).

## References

[Agent Skills specification](https://agentskills.io/specification) · [Claude Code skills](https://code.claude.com/docs/en/skills) · [Codex skills](https://developers.openai.com/codex/skills) · [GitHub Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
