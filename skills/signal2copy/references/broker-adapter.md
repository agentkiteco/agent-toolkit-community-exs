# Real broker boundary — official references checked18November2026

The synthetic adapter is not a production API. Implement a separate real adapter and validate its transport independently. Without real credentials, offline signing/recorded-response checks can pass; actual authentication/trading stays unverified and disabled until authorized. Never rename the fixture endpoints and call it Exness integration. Do not retrieve private keys from unrelated projects.

For the account-level Partnership requirement, use the application's registered provider credentials to query the first-level client-account report with the exact selected `client_account` filter and complete pagination. Do not ask the investor for email. Bind the report evidence to the provider credentials used by this application.

## Signing and discovery

Follow [request signing](https://www.exness-api.com/authentication/request-signing): Ed25519 signs the exact UTF-8 payload containing api_key/idempotency_key/timestamp/sign_version/method/path/body_hash. Header values must agree; body hash covers exact transmitted bytes and path includes the exact query. Base64url has no padding. Signed GET uses the required empty idempotency header and empty body; mutations use a stable persisted request key. Refresh timestamp/signature per request without replacing the trade's request identity. Do not follow redirects with signed headers.

Send an explicit product User-Agent. Actual read verification found a non-JSON edge403 with Python urllib's default; the packaged transport's `Signal2Copy/0.1` succeeds on the retained read scope. This is a transport lesson, not permission to reinterpret all403responses or retry automatically. See [bounded real reads](live-read-verification.md) for authorization and precise evidence limits.

[Code examples](https://www.exness-api.com/trading/guides/code-examples) demonstrate Gateway discovery `GET /v1/trading/access-point?account_id=...`, then account-specific Access Point `GET /v1/configuration/accounts/{id}/account`. Use the user's configured Gateway, not a guessed global host. Validate returned HTTPS origin and keep per-account routing. The official expanded128-hex private representation includes seed/public halves, which must agree; support compatible owner-confirmed seed formats deliberately, not accidental truncation. Test signature/body/query bytes offline with generated dummy keys.

## Runtime and recovery

Use [runtime semantics](https://www.exness-api.com/trading/guides/runtime-semantics) to normalize orders/positions/deals and transaction snapshots. ACK accepts processing, not a final fill. Correlate request/operation IDs; resubscribe and rebuild after disconnect rather than assuming durable WebSocket replay. Operation-status polling is recovery evidence, not permission to repeat unknown writes. Scope state/history to the account and preserve decimal/timestamp semantics. Check the current operation schema before enabling each write; record unsupported/unverified methods rather than guessing success.

[Configuration/limits](https://www.exness-api.com/trading/guides/api-configuration-and-limits) supplies account/method limits; schedule per account and respect Retry-After. Access Point discovery, signing, current reads, streaming recovery and trading permissions require separate checks. A successful read does not prove write access, nor does a transient auth error establish permanent invalidation. Owner-confirmed is_demo/stream_id conventions in full-target.md remain distinct from independently verified current official fields.

Keep a native adapter map for discovery/account/snapshot/history/inventory/quotes/transactions/open/close/protection/pending/status. Before actual use, verify exact current routes/fields from official docs. No real broker request is required for synthetic M2; production acceptance remains open without authenticated proof.

The optional assets/exness_signing.py implements only offline-capable signing/key parsing; scripts/check_signing.py verifies generated-key signatures, tampering/body/query/key-pair errors without network access. It is not a real transport/stream/RMS adapter or proof of broker authentication. Check current dependency versions and key-format requirements before integration.

## Native routes and integration order

These native namespaces are separate from the fixture protocol. Keep decimal/account identifiers as strings and preserve the original response until an explicit normalizer exists.

| Resource | Native path below account-specific Access Point |
| --- | --- |
| Account | /v1/configuration/accounts/{id}/account |
| Available instruments | /v1/configuration/accounts/{id}/instruments |
| Conditions | /v1/configuration/accounts/{id}/instruments/{symbol}/conditions |
| Limits | /v1/configuration/accounts/{id}/limits |
| Current state | /v1/trading/accounts/{id}/snapshot |
| Closed orders/deals | /v1/history/accounts/{id}/orders or /deals |
| Candles | /v1/market-data/accounts/{id}/candles |
| Events/ticks handshake | /v1/server-events/accounts/{id}/ws/events or /ws/ticks |

Sources: [conditions](https://www.exness-api.com/reference/trading/get-instrument-condition), [limits](https://www.exness-api.com/reference/trading/get-limits), [history](https://www.exness-api.com/reference/trading/get-orders-history), [candles](https://www.exness-api.com/reference/trading/get-candle-history), [events](https://www.exness-api.com/reference/trading/get-ws-events), [ticks](https://www.exness-api.com/reference/trading/get-ws-ticks). Recheck the exact schema when implementing each method. History cursor pages retain only cursor/limit; candles use native from/to or count and price_type=both, then normalize time/bid.close/ask.close deliberately. Do not expose unavailable REST quote/event endpoints as native methods.

1. Add a separate native module and a usable read-only probe in the same project. Reuse encrypted owner-authorized credentials when integration exists; otherwise accept an explicit private local config file. Do not search unrelated projects or ask for keys in chat. A successful read-only probe is not completed browser onboarding/copying.
2. Verify discovery/signature/routes/body/query/redirect handling against injected native-shaped I/O with generated keys; separately classify actual TLS/WS handshakes and broker authentication. A mocked response is not a recording from a live account. Inspect exact transmitted bytes independently of the code that builds them.
3. Map native objects to the copying engine explicitly: configuration/conditions, current snapshot, historical closed objects, tick time, transaction deltas and exact operation results. Preserve closed/active separation and missing/conflicting fields. The fixture transport's operation/event assumptions must not silently govern native responses.
4. A lost stream invalidates its synchronization state. Resubscribe to transactions and receive a new baseline before treating cached state as execution-ready. Ticks require their own signed GET handshake and subscription. Preserved data is evidence, not permission to trade after disconnect.

The supplied client offers the live-observed `exness-ws-protocol` subprotocol and a product User-Agent. It retains each subscription request ID. An exact matching `{id, code: "200"}` control ACK is acknowledged without treating it as an error or as a transaction/tick baseline. Reject uncorrelated control statuses. These cases have both portable checks and a bounded real-source read observation; keep full runtime/reconnect and trade acceptance separate.
5. Persist account/request/method/exact-body identity before any optional native write; default writes off. Classify ACK, unknown, explicit rejection and exact final status separately. A write timeout or operation404 never permits blind resend. Keep a useful standalone transport component available while full engine/RMS/admission integration remains explicitly disabled.

Business code governs automation in addition to HTTP status. Official endpoint quota REQUEST_RATE_LIMIT(3015) is not automatically retryable; use reported limits/local accounting and surface the block. Preserve Retry-After for scheduling, without automatically replaying writes. Distinguish this from platform SYSTEM_RATE_LIMIT. Read errors must not invalidate an unknown trade journal or become a fresh empty snapshot.

## Acceptance before enabling native copying

Check account/key routing isolation, expanded private-key public-half validation, exact Unicode/query bytes, redirect denial, cursor bounds, native candle shape/time, snapshot/stream generation and disconnect fencing, ACK versus confirmed operation, persisted unknown write/no repeat across restart and error-code/quota behavior. Record how each was exercised (pure function, injected I/O, loopback wire, real TLS, authorized read or trade). Do not add the counts as distinct end-to-end scenarios.

Native copying additionally needs actual provider/Partnership onboarding, general account binding, complete field normalization, fresh synchronized transaction/quote/condition/account state, broker margin/RMS, ownership reconciliation and durable pre-dispatch gates. A library or CLI alone does not close these requirements. Keep browser/health mode labels truthful and keep synthetic/live transports from falling back into one another.

## Bundled native component

Optional assets/exness_adapter.py, assets/exness_signing.py and assets/exness_probe.py are sibling modules; copy them into the generated app when implementing this increment. assets/requirements-exness.txt pins optional dependencies. Run python -B scripts/check_exness_adapter.py for offline generated-key/injected-wire checks (optional --output /ABSOLUTE/PATH/results.json); it writes no skill-local state by default and makes no network requests. These tests are portable algorithm/serialization checks, not actual TLS/WS/broker authentication. The standalone probe uses --config /PRIVATE/owner.json --allow-read-only-network for an explicitly authorized read; its config fields are gateway, account_id, api_key, private_key in an owner-only regular file. It prints a limited summary, never secrets. Do not run the network flag as a skill self-check.

The browser copying engine stays synthetic until native normalization and live gates are implemented. The supplied client provides native transport/streams/journal interfaces; preflight callback and optional write flag are not a verified RMS or trading authorization. Unknown request handling must also preserve the original known operation binding: a matching request ID cannot rebind a stored ACK to another operation. Valid system/balance events need not contain user command IDs and must not settle unrelated commands. Partial-close volume is an exact signed DELETE query with empty body.

For the application increment after this component, read [native read integration](native-read-app.md). Distinguish a usable owner-configured read-only workspace from completed provider/investor onboarding and native execution.
