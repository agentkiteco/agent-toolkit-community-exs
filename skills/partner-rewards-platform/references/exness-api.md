# Exness API — endpoints used and known gotchas

Host `api.exness.com`. OpenAPI specs:
- Partnership public OpenAPI specification: partnership.public.yaml.
- Payments public OpenAPI specification: payments.public.yaml.

## Signing (sign_version 1, Ed25519) — implemented in `cloud/app/src/exness.js`

- Headers: `EXN-API-KEY`, `EXN-IDEMPOTENCY-KEY` (UUID for writes, empty for GET), `EXN-TIMESTAMP` (ms),
  `EXN-SIGN-VERSION: 1`, `EXN-DATA`, `EXN-SIGN`.
- `EXN-DATA` = base64url(JSON `{api_key, idempotency_key, timestamp, sign_version, method, path(+query), body_hash}`),
  `body_hash` = base64url(sha256(body bytes)) (empty body for GET).
- `EXN-SIGN` = base64url(Ed25519 signature of those JSON bytes).
- Secret = 128 hex chars = 32-byte seed + 32-byte public key → import as JWK `{kty:"OKP", crv:"Ed25519", d, x}`.
- **Always send `User-Agent`.** Without it the Cloudflare edge in front of the API returns a bot challenge (403 "Just a moment").

## Endpoints

| Purpose | Request | Notes |
|---|---|---|
| Partner profile, Reward Wallet | `GET /v1/partnership/partner/summary` | wallet = `accounts[]` with `account_type == "partner"`; `permissions` shows key scopes |
| Clients | `GET /v1/partnership/reports/clients?reg_date_from&reg_date_to&limit&offset` | `ftd_received`, `kyc_passed`, `ftt_made` are **booleans with no dates** |
| Client accounts | `GET /v1/partnership/reports/clients/accounts?client_uid=` | `platform` (`mt4`/`mt5`/other), `client_account_last_trade` |
| Rewards per client per day | `GET /v1/partnership/reports/rewards?aggregate_by=day&reward_date_from&reward_date_to` | `volume_lots`, `volume_mln_usd`, `orders_count`, `reward_usd`, full `client_uid` |
| Orders | `GET /v1/partnership/reports/orders?date_from&date_to&limit<=1000&offset` | per order `symbol`, `volume_lots`, `client_account`. **Period must be < 1 month** → fetch in 28-day chunks. No symbol filter |
| Wallet balance | `GET /v1/accounts/{wallet}/balance` | |
| Payout | `POST /v1/transfers` `{destination_type:"another_client", source_account, destination_account, amount:"10.00"}` | 201 + `transfer_id`; needs `EXN-IDEMPOTENCY-KEY` |
| Payout status | `GET /v1/transfers/{id}` | `processing` → `done` / `rejected`. Usually 2–6 min, can take a few hours |
| EXD payout | `POST /v1/partnership/exd/transfers/clients` `{operation_uid, partner_uid, client_uids:[…], amount:"10.00"}` | **Not in the public specs.** 200 → `{idempotency_key, partner_uid, operation_type:"CLIENT", total_amount, status:"PENDING"}`. `operation_uid` = a new UUID per transfer (send the same value as `EXN-IDEMPOTENCY-KEY`); `partner_uid` = `uid` from partner summary. GET on it → 405. The app sends one client per request |

Paging: `limit` + `offset`, stop when a page is shorter than `limit` (`Exness.paged`).

## Known gotchas

- **MT4/MT5 accounts cannot receive transfers.** Pay to the client's non-MT account; pick the one with the latest trade.
  A client with only an MT5 account shows "No account that can receive transfers" until they open another account.
- **`OPERATION_NOT_ALLOWED` (422)** can be transient, or can mean a restriction on the destination. Engine retries up to
  3 times with a new key, then marks `failed`. Resetting a `failed` row with `transfer_id IS NULL` is safe (no money moved).
- **One-off `403 PermissionDenied invalid token`** happens occasionally with a valid key. Reads are retried once after
  700 ms; writes are never auto-retried outside the idempotent payout engine.
- Unknown outcome / 5xx / 429 on a transfer → retry with the **same** idempotency key.
- Orders report rejects periods ≥ 1 month ("Period must be less then 1 month").
- Account → client mapping in orders: `client_account` → accounts report → `client_uid`; match by the first 8 chars of the uid.
- Symbols come with suffixes (`EURUSDm`, `XAUUSDc`) → strip trailing lowercase letters before grouping.
- **EXD has no read endpoints**: no EXD balance (the EXD wallet doesn't appear in partner summary accounts) and no transfer
  status (`/exd/transfers/{id}`, `/exd/balance` … → 404). An empty POST body returns 422 `ValidationError` listing the
  required fields — handy to re-check the contract. Whether `amount` is per client or a total for several `client_uids`
  is unverified, so send one client per request.
- Partner reward per participant from the clients report is lifetime, not per promo period; use the rewards report for the period.

## Current hosted template

Read `product.md` for the active connection and payment boundary. The transfer endpoints above document the original platform; the current template omits payment execution and blocks transfers and auto-pay. Store credentials through Settings, encrypted with the server runtime key. A partner-summary success and wallet-balance permission are separate checks. Never automatically broaden key scopes or test POST transfers while diagnosing read access.
