# Mandatory background qualification

## Required outcome

The partner can close the browser and clients can still qualify for active promotions. Qualification records survive browser refreshes, server restarts and redeployment. Payments being disabled must have no effect on scans.

Use a real server-side scheduler. Default: wake every minute; scan each eligible promotion at least every 25 minutes. These are separate intervals. Display the configured scan interval. If the user requests faster qualification, update cadence explicitly; do not claim real-time detection for periodic scans.

## Required implementation work

The template currently implements `Engine.scan(id)` and invokes it from promotion details. That alone is browser-triggered and insufficient. Before full handover, implement all of the following:

1. A reusable background runner that loads the encrypted credentials through `loadCredentials(env)` and builds the same read-only `Exness` client and `Engine` used by the HTTP application. Do not rely on a browser session, browser storage, a desktop process, an open tab or user interaction.
2. An actual deployed timer/task that calls this runner while the user is absent. Native Cloudflare triggers require both a scheduled handler and deployed cron configuration; Sites requires its currently supported unattended scheduling/access workflow. A configuration snippet or callback export alone is not evidence of registration.
3. Durable run metadata and a health display in Settings or Overview: scheduling state, last attempt, last successful scan, next due scan where supported, and safe errors. Show “not configured”, “awaiting credentials” or “paused” accurately. Never show “running” based solely on having source code.
4. Reliable iteration over due promotions, with per-promotion error isolation and retries. Bound each run and paginate/continue larger workloads; don't skip due campaigns indefinitely. Protect overlapping runs with leases or equivalent idempotency and concurrency control.
5. Verification through the same unattended access path as the production scheduler, with DB readback. Keep credentials and signing headers out of task prompts, task descriptions, logs and browser output. Do not add a public unauthenticated trigger route.

Do not enable or restore money-transfer code while implementing this runner. The Exness client remains GET-only. Reuse the existing qualification operation rather than calling the original payment engine or payment cron.

## Qualification semantics

- Scan only promotions whose status is active and whose period has started. Continue observation through the existing one-day grace window after the end date; do not scan future or ended promotions as currently eligible.
- Apply the promotion's audience: clients registered inside the promotion period for `new`, or before the start for `existing`.
- Read `ftd_received` for FTD and `kyc_passed` for KYC from partnership reports. Complete pagination; do not infer eligibility from balances or personal trading accounts.
- Respect the baseline saved at creation: clients already meeting the condition are excluded from a normal promotion. Preserve the test-promotion exception.
- These API flags do not provide actual FTD/KYC completion timestamps. Record the first observation time, not an invented event time. Do not promise exact event-time qualification if the API cannot provide it.
- Persist qualifying clients in `qualified` with unique `(promo_id, uid)`. Repeated scans and retries must not duplicate qualification or overwrite its original observation timestamp.
- Advance each promotion's `last_scan` only after successful processing. Track failed attempts and safe endpoint/status errors separately. Never swallow scan failures silently or mark them successful.
- Do not require wallet balance access to qualify clients. A balance failure must leave partnership client scans operational.
- With no saved credentials, do not call the real API or fabricate records. Report “awaiting credentials”.

## Acceptance tests

Use generated fixture credentials and deterministic mocked Exness responses for code tests. Do not make real transfers.

1. Create an FTD promotion before a fixture client has deposited. Change the API flag to true, invoke the background runner through the scheduler adapter without loading any UI, and read the new D1 qualification.
2. Repeat for KYC and both audiences. Show that a future promotion, ended promotion and baseline-qualified client are excluded; preserve the documented test exception.
3. Invoke the runner twice and simulate overlapping/retried work. Verify exactly one qualification and unchanged first-observation timestamp.
4. Deny wallet-balance access while allowing partnership reports. Verify background qualification still succeeds.
5. Fail one promotion's API request. Verify other promotions are processed, the failed scan is visible, and a subsequent successful run recovers without duplicates.
6. Verify stored credentials decrypt in the unattended runtime, not just in the interactive request path. Missing/decryption-failed credentials must produce a clear health state without leaking values.
7. Verify no transfer POST, payout insertion or automatic payout is caused by any run. Preserve payment route blocks and the GET-only API client.
8. For hosted acceptance, confirm the timer/task exists and is enabled, exercise its intended unattended entry point, and read back persisted run metadata. When the platform permits, observe a scheduled occurrence with the browser closed. Record which evidence is from mocks, manual unattended execution and an actual scheduled occurrence; do not label one as another.

## Final completion evidence

Report the scheduler mechanism, enabled/paused state, tick interval, scan interval, last successful server-side run and persisted qualification result when a client is available. An empty account may verify the runner and its metadata without fabricating qualifying clients; label fixture qualification tests separately.

If no functioning scheduler can be deployed or its unattended access cannot be verified, report this feature as incomplete with the exact blocker. Do not substitute page auto-refresh, a manual Refresh button, a chat reminder or an unscheduled `scheduled` function.
