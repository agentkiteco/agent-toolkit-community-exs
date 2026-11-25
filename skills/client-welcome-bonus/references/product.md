# Product behavior

## Working version

- Overview: partner reward, clients, active promotions, bonus totals and Partner Reward Wallet balance. An inaccessible balance is `null` with a visible warning, never a fabricated zero and never a reason to hide the whole overview.
- Promotions: first deposit (`ftd`) and verification (`kyc`), USD or EXD denomination, amount, budget, dates, new/existing audience and test option. Preserve the original qualification and idempotency data model.
- Promotion details: participants, qualification, budget, reward and volume/order/symbol analytics. The API exposes KYC/FTD booleans without event dates: baseline already-qualified clients at creation and record newly observed qualification during the window.
- Clients: partner-referred client records and their accounts, obtained from partnership reports. These are distinct from the partner's personal trading accounts.
- Settings: password-type API key and API secret inputs; verify and save; masked saved-key status; clear errors and successful-save feedback. No secret readback, OAuth or extra application sign-in.

## Required background behavior

Background qualification is part of the product, not optional. Run a server-side scheduler with no browser open, scan eligible FTD/KYC promotions, and persist results in D1. Follow `background-qualification.md` for cadence, qualification semantics, health reporting and acceptance evidence. Keep this active when payouts are disabled. The template's browser-triggered detail scan alone does not meet this requirement.

## Payment boundary

Payment execution code is omitted from this template. The engine rejects payment requests, the API client permits only GET, and `hosted/worker.js` blocks payment routes. No payment cron is provisioned. Creating `auto_pay: true` is rejected. A promotion's currency/bonus settings do not authorize a transfer. The API client rejects writes in demo mode.

Keep this boundary until the user separately requests payment implementation. Such work requires a complete review of transfer scopes, explicit payout authorization, budgets, idempotency, scheduling and the UI; removing a single route guard is insufficient.

## Connection and storage

`POST /api/settings/credentials` validates key/secret format and makes a signed partner-summary GET. On success, encrypt both credentials with AES-GCM and a fresh nonce, then atomically store ciphertext, the verified partner UID and clear wallet/partner caches. Reject switching partner identity when existing promotions belong to another partner.

Use the existing `meta` table for encrypted credentials and connection identity; do not add unnecessary schema tables. Without saved credentials, use the empty DemoExness account. With saved credentials, use real signed Exness reads. A failed replacement must retain the previous working credentials.

## Accounts and diagnostics

Overview calls `GET /v1/partnership/partner/summary`, selects an unarchived account with `account_type == "partner"`, then requests `/v1/accounts/{wallet}/balance`. It does not query personal trading accounts. The Clients screen calls partnership client and client-account reports. Wallet balances and partnership reports can have different permissions; a successful summary does not prove access to every endpoint.

Keep API failures distinct from application/storage failures. Show endpoint and status for API errors without returning signed headers, keys, secrets or raw sensitive upstream payloads.
