# Synthetic broker v5 — M1 transport

This stdlib-only fixture owns broker effects, never copying decisions. It is not Exness REST/WebSocket and does not verify Ed25519 signatures. Keep explicit loopback origin, no real-broker fallback.

Run `python assets/sizing/broker.py --port PUBLIC --control-port CONTROL --log NEW_LOG_PATH` with a fresh private local ACCEPTANCE_CONTROL_TOKEN. Keep sibling fills/broker.py and pending/broker.py. Use two distinct available loopback ports (9011/9012 are suggestions) and an existing private log directory. Stop only processes you started.

| Purpose | Account | Public EXN-API-KEY |
| --- | --- | --- |
| Partner verification | none | synthetic-provider |
| Source |1111| synthetic-1111 |
| Investor |2222| synthetic-2222 |

Dummy private signing material may be a generated32-byte Ed25519-format hex seed. These identities are public fixture values, not personal credentials. Still protect submitted private material in app persistence/error/UI paths. Account-key mismatch returns401.

## Public application-facing API

Account routes require EXN-API-KEY. IDs/decimal values are strings; timestamps timezone-aware ISO8601.

| Method / route | Evidence |
| --- | --- |
| GET /healthz | protocol5 |
| GET /v1/partner | verified/401 |
| GET /v1/trading/accounts/{id}/details | account_id/settings.currency |
| GET /v1/trading/accounts/{id}/snapshot | account_state(balance,equity,used_margin),positions,orders |
| GET /v1/trading/accounts/{id}/instruments | inventory |
| GET /v1/trading/accounts/{id}/instruments/EURUSD | contract currencies/size/margin_percent/point_digits/trade_mode/min/step/max |
| GET /v1/trading/accounts/{id}/quotes/EURUSD | bid/ask/event_time/received_at |
| GET /v1/trading/accounts/{id}/limits or /history | settings/history coverage |
| GET /v1/trading/accounts/{id}/events?after=N | cursor/events |
| GET /v1/trading/accounts/{id}/operations/{op} | exact status/request correlation;404 unresolved |
| POST /v1/trading/accounts/{id}/positions | open body instrument,side,volume and optional protective prices |
| DELETE /v1/trading/accounts/{id}/positions/{pid}?volume=0.02 | exact partial amount, or full remaining close if volume omitted |

Mutations require durable unique EXN-IDEMPOTENCY-KEY or Idempotency-Key,5–128characters. Identical replay deduplicates; changed payload conflicts409. Dedup is not permission to repeat unknown writes. ACK202 contains operation_id/client_request_id/status=accepted. Event result carries exact correlation/position; similar snapshot exposure alone does not prove ownership.

## Operator-only test driver

Control origin is on the other port and requires Authorization: Bearer with fresh token. App receives neither this origin/token nor a control client.

| Route | Operator input/effect |
| --- | --- |
| GET /state | state plus parsed mutation-attempt ledger |
| POST /position | seed account,id,volume,side/instrument source/manual position; uncorrelated event |
| POST /change | account,id,remaining_volume or protective changes |
| POST /configuration | account,currency/balance/equity/used_margin/inventory/min/step/max |
| POST /quote | account,instrument,bid/ask,age_seconds; negative age means future |
| POST /fault | account,kind=apply_then_503_hold,method=POST/PATCH/DELETE |
| POST /release | reveal held correlated confirmations |

Seed example: `{"account":"1111","id":"91001","instrument":"EURUSD","side":"buy","volume":"0.08"}`. Independent checks can use other IDs/amounts. The app must calculate/dispatch itself, never read operator expected results.

`python scripts/check_fixture.py` checks only fixture transport/effects, not a generated app. Later pending/fill capabilities are inherited, not M1-certified. P/L/margin consumption are simplified, quotes controlled and events process-lifetime; actual signing, WebSocket reconnect, price triggers and full broker margin are not modeled. Synthetic success does not establish real-broker/cloud/full-product acceptance.

## Optional FX increment — protocol6wrapper

When implementing currency-sizing.md, copy assets/fx/broker.py alongside the existing sibling sizing/fills/pending folders and start fx/broker.py on separate public/control loopback ports with the same private operator token convention. It imports unchanged v5siblings. Only the test operator receives the control token. This synthetic overlay adds explicit currency metadata/candle/fault/fixed-time inputs; it is not a real broker API adapter.

# Synthetic FX wrapper — local protocol6 extension

fixture/fx/broker.py imports the unchanged sizing/fills/pending fixture siblings. It adds explicit contract/candle inputs and read-fault evidence. No real broker signature, API schema, price matching or settlement is modeled. All controls require the separate operator port/token. The application never sees these capabilities.

- POST /fx-contract: account, instrument and optional base_currency, quote_currency, margin_currency, calc_mode, trade_mode, contract_size, margin_percent. Overrides explicit public instrument metadata. Also creates a default tick; use the existing /quote and /configuration controls to configure quote/inventory. Tick-only valuation can use a trading-disabled forex instrument; actual traded-symbol guard cannot. Existing fixtures still provide default metadata for existing symbols.
- POST /fx-candles: account, instrument, timeframe=M1|D1, items list of {bid_close,ask_close,open_time}. Operator may supply age_seconds instead of open_time; the wrapper computes and stores original time ONCE at control input, never on public read. Invalid/future/old data may be seeded to exercise rejection.
- POST /fx-fixed-quote: account, instrument, bid, ask, optional age_seconds. Uses the normal quote validation but fixes original event_time/received_at once at control input. Repeated public reads cannot refresh the age. This optional path makes delayed-read rejection deterministic; default inheritedv5ticks retain their existing continuously observed convention.
- POST /fx-read-delay: account, resource, seconds0–2.7. Consumed by the NEXT matching authorized public read only. Two distinct2.6second delays can model5.2seconds of FX work without exceeding the app's individual3second request timeout. No indefinite sleep/retry loop.
- POST /fx-read-fault: account, resource such as candles/QUOTEREF, status. HTTP200 clears the fault. Fault persists until changed.
- GET public /v1/trading/accounts/ACCOUNT/candles/INSTRUMENT?timeframe=M1|D1&from_time=...&to_time=... returns {items:[...]}; app validates original window/time/close bounds. Auth/account inventory is enforced.
- Existing GET operator /state adds fx_reads[{account,resource,instrument,query}] so actual account scoping/cache/timeframe requests can be inspected. No secrets recorded in this evidence.

The three old fixture files remain unchanged. This wrapper is source-free test infrastructure, not original application code. Complete pagination, real bid/ask candle schema/availability, quotas/backoff, matching and broker permissions remain separate adapter work.
