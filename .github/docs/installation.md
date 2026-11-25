# Installation and publishing

## Skills

Use the commands in the README, or copy the whole `skills/partner-pulse/` directory:

| Agent | Project location | User location |
| --- | --- | --- |
| Codex | `.agents/skills/partner-pulse/` | `~/.agents/skills/partner-pulse/` |
| Claude Code | `.claude/skills/partner-pulse/` | `~/.claude/skills/partner-pulse/` |

Keep the entire folder, including references and assets. For ChatGPT and other interfaces, use the product's supported skill or plugin installation flow; this repository does not claim automatic installation. The Skills CLI is a separate third-party tool, not an official OpenAI or Anthropic installer.

## Prompts and instructions

Open an entry on the site, copy its content, replace `{{example}}` where applicable, and attach it to your agent explicitly. YAML metadata describes the catalog entry and is not part of the copied prompt.

## GitHub Pages

1. In repository Settings → Pages, select GitHub Actions as the publishing source.
2. Open Actions → Pages → Run workflow on `main`.
3. Wait for a successful deploy job. Its environment URL is the published site.

Subsequent pushes to `main` run validation and deployment. Pull requests run validation and build without deployment. If a GitHub App cannot write `.github/workflows/`, grant the connection Workflows write permission or commit those files using an authorized account. No personal access token is needed in this project.

## Compatibility

The skills use Agent Skills metadata and self-contained relative resources. Local validation and static build checks are automated. Interactive invocation in Claude Code, Codex, and ChatGPT has not been tested. No plugin or marketplace manifest is included yet.
