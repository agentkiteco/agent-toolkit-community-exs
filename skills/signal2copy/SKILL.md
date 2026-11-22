---
name: signal2copy
description: Guide a client through creating Signal2Copy from its functional specification in useful increments, with local execution, recipient-owned Cloudflare deployment and English provider/investor guides. Use for a new independent build or continuation, not maintenance of the reference production installation.
metadata:
  version: 1.2.0
---

# Signal2Copy

Create one application and guide the client through its development. The target is the frozen 18 November 2026 Signal2Copy behavior through FB-033: [feature map](references/feature-map.md) and [full specification](references/full-target.md). Match functions and decisions; identical source code or pixels are unnecessary. Read [release status and limits](references/release-status.md) before presenting guarantees. This is a reusable build specification, not a prebuilt production trading app.

Keep the skill, generated app UI and provider/investor/owner guides in English. Conversation follows the client's language. Default name: Signal2Copy. Use a compact available stack and existing suitable tooling. Do not retrieve reference application source, old generated apps, private accounts or secrets. Supplied broker/SDK/infrastructure assets are reusable; the full copying application must be implemented in the new project.

For native copying, read the [runtime integration contract](references/runtime-integration.md) before choosing durable account/subscription schemas. Install the supplied runtime at that stage instead of rewriting its synchronization, execution and recovery internals. Build the host routes, durable storage, admission/controls and role UI around that contract; copied modules alone are not a completed feature.

The verified delivery track is a working local synthetic application followed by deployment of the same project to an isolated Worker in the recipient's Cloudflare account. When the user requests this track, finish it with verified synthetic copying, durable state, provider and investor guides, and a Cloudflare handoff. Continue each authorized milestone without routine reconfirmation. For an authorized native onboarding milestone, use the [live read verification track](references/live-read-verification.md). Verify each role and preserve execution denial while the installation is read-only.

## Plan, act and maintain continuity

Read [workflow](references/workflow.md). Inspect the destination and any BUILD_STATE.md; continue that project and reuse its decisions. Propose useful milestones: local provider-to-investor path, execution/persistence plus first Cloudflare delivery, remaining target features, then scoped handoff. State the next observable result and begin authorized work. Ask concise questions only when missing information materially affects the next action; continue independent work while waiting. Cloudflare parameters and real broker keys are not prerequisites to local development.

Define the current increment's implemented behavior and a proportionate acceptance check. Deliver it, update one [BUILD_STATE](assets/BUILD_STATE.template.md) and the guides, and report what works, known differences, unverified items and the next step. Continue authorized unblocked work without repeated next-step permission. Do not enlarge the increment or invent a new test series merely because additional permutations remain possible. Fix concrete failures; stop adding checks once its agreed outcome is demonstrated unless a new defect justifies more work. Never weaken ownership, consent, durable intent or unknown/no-resend boundaries to meet a deadline.

Use implemented / partial / missing separately from passed / failed / not run. A specified feature is not an implemented feature; a missing test is not automatically a missing feature. Inspect actual rendered controls and dynamic routing before declaring a UI capability absent. See [release status](references/release-status.md) for the evaluated reconstruction's limits; those are neither guarantees nor restrictions on every future client build.

## First useful local application

For a first-use or mock-only request, follow the [first-session workflow](references/workflow.md#first-client-session). Keep the initial explanation short: what the local demo will show, the few useful milestones and what you are doing now. Do not lead with all 43 target rows or later test matrices. Inspect the workspace/tools before asking about directories or packages; choose reversible defaults for stack and local setup. Do not ask for broker keys, trading account numbers, email or Cloudflare information merely to begin the local demo.

Read [M1 behavior](references/m1-local.md), [fixture protocol](references/fixture.md) and [M1 acceptance](references/m1-acceptance.md). Build provider registration, source verification, strategy publication, selected investor sign-in/Connect, explicit Start and actual synthetic copies in both same-currency sizing modes. The external fixture is a broker, not the application's copying engine or database. Verify through app actions and broker effects rather than hardcoded success or arithmetic-only checks.

Create actual English [provider](assets/PROVIDER_GUIDE.template.md) and [investor](assets/INVESTOR_GUIDE.template.md) guides, then [owner operations](assets/OWNER_OPERATIONS.template.md) when deployment/admin exists. Replace template instructions with the build's controls, startup/deploy commands, recovery steps and current limits. Keep the first provider/investor guides short; omit future-feature sections until implemented rather than leaving pages of authoring instructions. Use established encryption and sessions; retain keys privately on the server and reuse them for ordinary refresh/reconnect. Do not request secrets in chat, persist them in the browser or include them in reusable artifacts. Repeated sign-in with the identical verified pair must not silently revoke a prior explicit connection.

## Extend the same app as needed

Read the next relevant reference, not the whole library on every turn:

| Next capability | References |
| --- | --- |
| Reusable native core, host integration and completion gates | [runtime integration](references/runtime-integration.md) |
| Strategy discovery, observed source results and sizing examples | [strategy experience](references/strategy-experience.md) |
| Execution lifecycle, pending fills and FX | [M2 execution](references/m2-execution.md), [pending fills](references/pending-fills.md), [currency sizing](references/currency-sizing.md), [M2 acceptance](references/m2-acceptance.md) |
| Native broker boundary and ordinary role onboarding | [broker adapter](references/broker-adapter.md), [native reads](references/native-read-app.md), [native onboarding](references/native-onboarding.md) |
| Read streams, native policy and final dispatch | [native runtime](references/native-runtime.md), [market executor](references/native-market-executor.md) |
| Reductions, protection and pending orders | [position management](references/native-position-management.md), [native pending](references/native-pending.md) |
| Initial exposure, Advanced and uncertain recovery | [native entry controls](references/native-entry-controls.md), [native recovery](references/native-recovery.md), [native reviews](references/native-reviews.md), [entry controls](references/entry-controls.md) |
| Admission, reports and owner/user management | [admission and Advanced](references/admission-advanced.md), [recorded reports](references/recorded-reporting.md), [management](references/management.md) |
| Cloudflare deployment and restore | [Cloudflare](references/cloudflare.md) |

Bind domain helpers to actual app routes, lifecycle and broker effects; importing them is not a completed feature. Preserve original fill anchors and exact source/target/request/operation ownership. Persist intent and await durable acknowledgement before dispatch. Unknown writes are not blindly replayed, and an empty restarted broker does not prove exposure is flat. Keep synthetic and native modes explicit, sealed in retained state and free of automatic fallback. The server executor runs independently of the browser.

Expose native readiness, consented stream connection and observed status through normal role UI using retained credentials. Separate received baselines and original quote times from an open connection or permission to trade. Discard asynchronous replies from an obsolete account/strategy selection. Native unsupported data/formulas and unresolved ownership stay held; do not turn a green read into trade authorization.

## Deploy at a useful stage

After working local execution/persistence foundations, deploy the same app in the recipient's Cloudflare account before completing all report/UI refinements. Obtain or reuse Account ID, new Worker, bucket and origin just in time, and inspect resource collisions. Describe the concrete target/effect, honor existing authorization and tool approvals, and preserve prior installation state and encryption keys. Installing this skill alone does not authorize cloud publication, real trades, resets or account disconnects.

Use the generated app's actual deployment files and [Cloudflare instructions](references/cloudflare.md). The bundled scaffold supplies authenticated encrypted checkpoint and independent owner storage; the app must integrate the protocols. Configuration, dry-run, uploaded image, healthy app, owner-state restore and populated subscription/uncertain-intent restore are different outcomes. Report exactly which occurred. Keep deployments and generated credentials outside the skill/client ZIP.

## Native execution and handoff

When the client explicitly authorizes a broker-backed demo execution milestone, follow [demo acceptance](references/demo-acceptance.md). Use the separate installation and selected demo accounts, record the enabled admission rules, and verify the entire copying effect through the broker before claiming that the pilot passed.

Use generated-key/native-shaped injected I/O for execution and failure cases before considering real use. When a specific decision needs real API evidence, follow [bounded real reads](references/live-read-verification.md): announce the stage, reuse only authorized private credentials, bound reads and keep trading disabled. Missing live access blocks only dependent work. Native execution requires completed application-level permissions, sizing/margin/session/stream/ownership/durability and recovery gates plus the client's actual authorization. Do not deploy a test-policy bypass or use a real order as an installation diagnostic.

At handoff provide the app, portable dependency/setup commands, actual local/deployed locations, three guides and one honest BUILD_STATE. Separate known behavior differences from unverified scenarios. A useful staged release may be delivered with visible limits; call it fully functionally equivalent only after the required feature-map differences are closed and the relevant outcomes demonstrated. Reference evidence and this kit's author checks never become the recipient build's results or a general success-rate guarantee.

## Getting started

For installation and copyable client requests, see [start guide](guides/START.md) and [prompts](guides/PROMPTS.txt). The [provider guide](guides/PROVIDER_GUIDE.md), [investor guide](guides/INVESTOR_GUIDE.md) and [validation record](guides/VALIDATION.md) describe the supplied kit and prior evaluation; verify each new application independently.
