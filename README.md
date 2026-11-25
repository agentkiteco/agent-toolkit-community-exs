# Agent Toolkit

Portable skills, prompts, and instructions for AI agents.

**[Explore the catalog ↗](https://agentkiteco.github.io/agent-toolkit-community-exs/)** · [Installation](.github/docs/installation.md) · [Contributing](.github/CONTRIBUTING.md)

| Collection | Contents |
| --- | --- |
| [Skills](skills/) | Self-contained agent workflows |

```sh
npx skills add agentkiteco/agent-toolkit-community-exs --skill partner-pulse --agent claude-code
```

Replace `claude-code` with `codex` for Codex. Uses the third-party [Skills CLI](https://github.com/vercel-labs/skills).

## Signal2Copy

[Signal2Copy 1.2.0](skills/signal2copy/SKILL.md) guides staged development of a copy-trading application, beginning with a local synthetic demo. It includes runtime helpers, broker fixtures, Cloudflare scaffolding and English role guides. It is a build kit; each generated application needs its own verification.

```sh
npx skills add agentkiteco/agent-toolkit-community-exs --skill signal2copy --agent codex
```

[Getting started](skills/signal2copy/guides/START.md) · [Copyable prompts](skills/signal2copy/guides/PROMPTS.txt) · [Capabilities and limits](skills/signal2copy/references/release-status.md)

## Trading Challenge

[Trading Challenge](skills/trading-challenge/SKILL.md) is an instruction-only skill for building an Exness trading competition with separate organizer/trader OAuth, verified account eligibility, exact closed-deal USD profit rankings, a public leaderboard, and scheduled updates. It includes nine reference documents covering implementation, API contracts, authorization, validation, and optional Cloudflare deployment; it does not contain a prebuilt application.

```sh
npx skills add agentkiteco/agent-toolkit-community-exs --skill trading-challenge --agent codex
```

[Skill specification](skills/trading-challenge/SKILL.md) · [Contest rules](skills/trading-challenge/references/challenge-rules.md) · [Validation](skills/trading-challenge/references/validation.md)

## Client Welcome Bonus

[Client Welcome Bonus](skills/client-welcome-bonus/SKILL.md) builds a private Exness partner dashboard with encrypted API credentials, promotions, client qualification and rewards reporting. It bundles an application template and requires implementation and verification of unattended background scheduling; payments are disabled.

```sh
npx skills add agentkiteco/agent-toolkit-community-exs --skill client-welcome-bonus --agent codex
```

[Development](.github/docs/development.md) · [Skill template](.github/templates/example/SKILL.md) · [MIT license](LICENSE)

