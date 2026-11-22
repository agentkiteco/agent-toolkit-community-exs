# Start Signal2Copy with Codex - 1.2.0

You need this ZIP and a Codex workspace. The skill guides Codex while it writes an application; the ZIP itself is not a running app. For the first local demonstration you do not need Exness keys, trading accounts or Cloudflare setup. Codex inspects installed development tools and chooses a suitable small stack.

## 1. Install the skill

Attach the ZIP, or give Codex its local file path, and send:

> Install the build-signal2copy skill from the attached ZIP. Preserve any existing copy, tell me the installed path and version, and stop after installation. Do not create the application yet.

Install the inner **build-signal2copy** folder, with SKILL.md directly inside it, not the outer kit folder. Use one supported skill location; avoid installing duplicate versions. For a project-scoped manual setup, the folder is `.agents/skills/build-signal2copy/`. Codex detects skill changes; refresh the skill list or open a new conversation if it does not appear. [Official skill setup documentation](https://learn.chatgpt.com/docs/build-skills).

If installation is unavailable, extract the kit and supply the exact local path to build-signal2copy/SKILL.md in the next request. This uses the file directly and is not a claim that it was installed.

## 2. Build the first local demonstration

Open the intended new project workspace, then send:

> Use $build-signal2copy to create Signal2Copy in a new project in this workspace. Start with a working local demonstration using mock data only. I do not have Exness keys or Cloudflare set up. Propose a short plan and build the first local milestone. Show me the local URL, demo steps and guides. Stop after that milestone and recommend one next action.

If that workspace already has unrelated files, Codex should use a separate project directory and tell you its path. You do not need to choose a framework or provide live credentials to begin.

The first result is a local browser app: a provider verifies a mock source and publishes a strategy; an investor connects a mock account, explicitly starts copying and sees a broker-confirmed copy. The first milestone also covers both same-currency modes, retained state, safe local Stop and short provider/investor guides. These are simulated accounts and orders.

## 3. Use the result and know what is next

The handoff should give you the actual local URL, portable startup/restart commands, where generated demo inputs are kept privately, one provider/investor walkthrough, guide paths and one recommended next action. It should clearly say what is implemented and what is unavailable. If the server stopped, ask Codex to restore the same project instead of creating a new one.

Before closing the demo, follow its confirmed Stop procedure. The app can retain its state while the mock broker may lose its positions/events when stopped. Ask Codex to inspect that distinction on return; do not reset unresolved state to make the screen look clean.

[Copyable prompts](PROMPTS.txt) include installation, the first local milestone, continuation and later cloud deployment.

| Track | When it is needed | Information needed then |
| --- | --- | --- |
| Local mock demonstration | First useful milestone | Workspace; missing development tools only if actually required |
| Exness integration | When implementing real broker reads/execution | Authorized private account access, supplied through private local tooling |
| Cloudflare deployment | After local execution/persistence foundations; mock/read-only cloud scope is allowed | Cloudflare login, Account ID, new Worker/bucket/origin |

Real broker access is not a prerequisite to every cloud step. Neither sign-in nor a successful read authorizes trades. [Capabilities and limits](../references/release-status.md) distinguish the specified full target from evaluated-app gaps. [Skill entry](../SKILL.md) and [validation](VALIDATION.md).

## Deploy the same project

When the local walkthrough is ready, use prompt 4 to deploy it to your own isolated Cloudflare Worker. Ask Codex to verify the actual running app, a populated encrypted checkpoint and owner access. The handoff includes the URL, role guides, and the restart and backup procedure. Broker accounts and orders remain synthetic for this track.

## Native implementation

The skill now includes an installable native core rather than requiring the copying runtime to be rewritten. Codex connects it to the same app using the [host integration contract](../references/runtime-integration.md). Package installation alone does not implement authentication, storage, admission, controls or UI and starts no trades. Continue the agreed milestones; a synthetic cloud demo does not complete the full target.

## Connect Exness for read-only verification

Use prompt 5 when you want to verify real account reads. Keep the synthetic installation and create a separate native read-only installation of the same project. Use private app forms or an authorized private connection to the retained vault. Record each actual verification outcome in BUILD_STATE. A later demo execution scenario needs an explicitly agreed scope and positively identified demo accounts.

## Verify a broker-backed demo

Use prompt 6 for one explicitly authorized pilot on dedicated Exness demo accounts. Use the [provider guide](PROVIDER_GUIDE.md) and [investor guide](INVESTOR_GUIDE.md). Check [validation](VALIDATION.md) for the actual local and cloud verification scopes.
