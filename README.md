# Agent Toolkit

Portable skills, prompts, and instructions for AI agents.

**[Explore the catalog ↗](https://agentkiteco.github.io/agent-toolkit-community-exs/)** · [Installation](.github/docs/installation.md) · [Contributing](.github/CONTRIBUTING.md)

| Collection | Contents |
| --- | --- |
| [Skills](skills/) | Self-contained agent workflows |
| [Prompts](prompts/) | Copyable request templates |
| [Instructions](instructions/) | Reusable rules |

```sh
npx skills add agentkiteco/agent-toolkit-community-exs --skill example --agent claude-code
```

Replace `claude-code` with `codex` for Codex. Uses the third-party [Skills CLI](https://github.com/vercel-labs/skills). The `example` entries are illustrative.

## Build Signal2Copy

[Build Signal2Copy 1.2.0](skills/build-signal2copy/SKILL.md) guides staged development of a copy-trading application, beginning with a local synthetic demo. It includes runtime helpers, broker fixtures, Cloudflare scaffolding and English role guides. It is a build kit; each generated application needs its own verification.

```sh
npx skills add agentkiteco/agent-toolkit-community-exs --skill build-signal2copy --agent codex
```

[Getting started](skills/build-signal2copy/guides/START.md) · [Copyable prompts](skills/build-signal2copy/guides/PROMPTS.txt) · [Capabilities and limits](skills/build-signal2copy/references/release-status.md)

[Development](.github/docs/development.md) · [Skill template](.github/templates/example/SKILL.md) · [MIT license](LICENSE)

