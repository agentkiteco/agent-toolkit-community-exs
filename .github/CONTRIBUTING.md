# Contributing

1. Copy `.github/templates/example/` to `skills/<name>/`, or add Markdown to `prompts/` or `instructions/`.
2. Use a lowercase hyphenated name. Add YAML `name` and `description` metadata; the skill name must match its folder.
3. Describe when to use the item, the inputs it needs, its workflow, and how to verify its output.
4. Keep every required skill resource inside its folder. Add optional `references/`, `scripts/`, or `assets/` only when needed.
5. Run the commands in `../AGENTS.md` and submit a pull request explaining the behavior and checks.

For prompts and instructions, metadata is a repository convention, not an agent discovery standard. The website automatically includes new items after a successful build. Avoid secrets and private data. Mark examples as illustrative.
