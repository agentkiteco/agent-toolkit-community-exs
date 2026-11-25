---
name: partner-rewards-platform
description: Build or update Partner Rewards Studio, a private Exness partner dashboard with promotions for first deposits or verification, clients, rewards, unattended background qualification and trading analytics. Use for requests to create, reproduce, publish or fix this partner rewards platform. Reuse the bundled working template, with API key and secret entered in Settings, encrypted server storage and owner-only hosting access.
---

# Partner Rewards Studio

Copy the bundled template; do not rewrite the app from scratch. Read [product.md](references/product.md) before changing behavior, [hosting.md](references/hosting.md) before publishing, and [exness-api.md](references/exness-api.md) when working with the Exness client.

## Required outcome — acceptance contract

Treat every item below as required unless the user explicitly changes it. Do not silently reduce scope because of a hosting migration, template limitation or disabled payments.

1. **Background qualification is mandatory.** Run server-side scans while all browser tabs are closed. Persist newly qualified clients in D1. Opening a page must not be necessary for a client to qualify.
2. **Provide a real enabled scheduler.** Default to a tick every minute and scan each eligible promotion at least once per 25 minutes. A Worker `scheduled` function without a deployed trigger is not a running background service.
3. **Keep qualification independent of payment execution.** Disabling transfers must not remove, pause or replace background qualification. Do not confuse a qualification scheduler with a payment cron. Payments remain disabled by default.
4. **Preserve the agreed connection UX.** Use Settings API key/secret fields, server verification and encrypted storage. Do not substitute a demo-only backend, CLI-only connection or OAuth.
5. **Use owner-only hosting access without a second app login.** No public credential store or unauthenticated public scheduler endpoint.
6. **Keep the cabinet usable with partial API permissions.** A missing wallet balance must not block partnership reports, promotion scans or the whole Overview. Never display an inaccessible balance as zero.
7. **Expose background health.** Show the last successful scan, enabled/paused/error state and a useful safe error. Do not hide failures or show “running” based solely on a configured interval.
8. **Prove completion.** Verify an unattended run, persisted qualification and deduplication; return scheduler and scan evidence. A published UI or passing mocked tests alone does not prove production background operation.

Read [background-qualification.md](references/background-qualification.md) before implementing or modifying scheduling. The bundled template currently contains promotion scanning logic but **does not register a production scheduler**. Implement and connect the missing background runner, deployment trigger and health display before calling a new full platform complete. Do not present this known template gap as an optional enhancement.

## Defaults and scope

- Use the prompt's brand; otherwise use `Partner Rewards`.
- Build a fresh project from `template/`. Never copy another customer's project, credentials, database, deployment identity or runtime state.
- Keep the empty state: no fabricated clients, balances or promotions.
- Use owner-only hosting access for the credential-enabled app. Do not add a second app login, ChatGPT sign-in screen, Exness OAuth, or Cloudflare Access screen. The hosting platform owns the access boundary.
- Connect Exness through **Settings → API key / API secret → Save and test connection**. Do not replace this form with CLI instructions.
- Keep transfers and automatic payouts disabled; do not add transfer-execution code. The working version supports real partner reads and promotion management; it does not execute payouts or run a payment cron.
- Do not change a live site's audience or connect live credentials while updating this skill itself.

## Create the project

Resolve this skill's directory as `SKILL_DIR`. Choose a unique fresh destination. Run:

```sh
PARTNER_NAME="Partner Rewards" BRAND_NAME="Partner Rewards" \
OWNER_EMAILS="owner@localhost" APP_WORKER="partner-rewards" \
D1_NAME="partner-rewards" D1_ID="00000000-0000-0000-0000-000000000000" \
sh "$SKILL_DIR/scripts/configure.sh" "$TARGET"
cd "$TARGET/cloud"
npm ci
cd ..
node scripts/build-hosted.mjs
```

Use the generated project for both preview and publication. `hosted/worker.js` is the credential-enabled entry point. `cloud/app/src/index.js` exports the API handler; do not deploy its legacy standalone `fetch` entry point for this workflow.

When the user only asks for a local version, use `sh start-local.sh` and stop after verification. Adapt local preview launch to the execution environment's supported mechanism. Do not invent a user-facing loopback URL for a remote host or bypass preview restrictions. For managed preview, use the platform's preview daemon. Report unavailable browser QA honestly.

When the user asks to publish, follow [hosting.md](references/hosting.md) and the hosting platform's supported source/build/deployment workflow. Do not require Cloudflare account login if Sites hosting is available.

## Credential handling

1. Provision `STUDIO_CREDENTIALS_KEY` as a cryptographically random 32-byte key encoded as 64 hex characters, stored as a runtime secret. Keep an existing key unchanged when editing or redeploying; rotating it makes stored credentials unreadable.
2. Let the user enter their credentials directly into Settings. Never request them in chat, print them, log request bodies or export credential database records.
3. Verify the submitted credentials using only `GET /v1/partnership/partner/summary` before saving.
4. Preserve AES-256-GCM encryption with a fresh random 12-byte nonce for each save. Store only ciphertext and nonce in D1 `meta.credentials_v1`; never return decrypted values to the browser or store them in localStorage.
5. Keep upstream host fixed to `api.exness.com`; do not add an arbitrary host field that could receive credentials.
6. Preserve the same-origin/custom-header guard on write routes. Mask API keys in status responses and clear form fields after success.
7. Preserve the partner-switch guard when promotions already exist. Clear wallet/partner caches only after successful verification and save.

## Completion gate

Before final handover, mark each acceptance-contract item as verified, incomplete or blocked, with evidence. If scheduling or unattended access is unavailable, finish the reviewable app work and state **“Background qualification is not operational; the requested platform is incomplete”**, with the exact blocker. Do not call the whole solution finished, quietly replace background work with browser polling, or omit this feature from the summary. Only ask for user input when an actual account action or choice is required to resolve that blocker.

## Verify before handover

- Execute the exact generated SQL migrations, split by `--> statement-breakpoint`, against an empty SQLite/D1 database. Five application tables must exist. The bundled migrations are schema-only.
- Build the Worker and check frontend syntax.
- Check the actual Worker entry point, not only the underlying handler: HTML opens without an extra app login; no keys gives the empty demo; invalid credentials are rejected; successful verification stores encrypted values; session JSON contains no full key or secret.
- Test credential round-trip and rejected/cross-origin saves using generated fixture credentials and a mocked Exness endpoint. Never use real transfers as a validation step.
- Check `/api/session`, `/api/overview`, `/api/promos`, `/api/clients`. With real credentials, partner reads must use the saved account.
- Simulate a failed wallet-balance request: Overview must remain available, show `Unavailable` rather than `$0`, and retain the warning with the endpoint and HTTP status.
- Verify the background contract and browser-closed acceptance tests in `references/background-qualification.md`; test failure and retry independently of payouts.
- Preserve backend blocks for `/pay`, `/autopay` and promotion creation with `auto_pay: true`; do not enable payment execution implicitly.
- Inspect Settings, Overview, Promotions and Clients in the browser when available. Show clean empty states before the user connects; do not seed promotions.
- Describe publication as complete only when deployment returns `succeeded`. For pending publication, report the pending state and follow the hosting tool's current status guidance.

## Troubleshoot

`Exness API connected` confirms that the partner-summary request succeeded, not that every other scope is available. Overview reads the partner profile, local promotions and the selected **partner** Reward Wallet balance. `/v1/accounts/{wallet}/balance` is a separate request and may fail independently; it is not a scan of the partner's trading accounts.

Do not hide all failures behind `Unable to load the account` or tell the user to re-enter valid credentials for every error. Preserve endpoint/status diagnostics without exposing secrets. Keep missing balance distinct from a zero balance.

If deployment reports SQLite syntax errors, inspect the actual migration first. Never split raw SQL at semicolons inside comments; remove inline `--` comments before generating statement boundaries, or use the bundled verified migration unchanged.

## Deliver

Return the live URL or verified local result and briefly describe connection through Settings. Report background scheduler enabled/paused state, cadence and last observed successful run separately from website publication. State that payouts remain disabled if relevant. Do not claim that a mock test proves the user's real credentials work. Never include a previous deployment URL or project ID in a reusable skill.
