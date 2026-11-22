# M1 — One usable local application

## Observable path

1. A clean install shows provider registration only. Require installation invitation and broker-verified synthetic-provider pair. Failed verification leaves registration open; successful atomic registration closes it. Provider re-login uses the registered pair without invitation; foreign credentials do not gain access.
2. Provider connects source1111 with its separate Trading key/consent and actual details/history reads; returned account ID must match. Guide source verification→strategy creation/publication. Published catalog/detail become public. If Unpublish is exposed, it must block subsequent new entries while retaining owned-exposure cleanup; otherwise disclose it as not yet available. No test order is used to check read access.
3. Investor selects a strategy, signs in with synthetic-2222/account2222 and separately connects/verifies that account. Keep selected strategy. Server ownership prevents other-account access. Sign-in/connection sends no trading write.
4. Show source/investor verified currency/equity/connection, Proportional default, amount/multiplier, new-only scope and explicit Start. Reserve the account against a second unfinished subscription. M1 may label include-current/Advanced/policies unavailable; do not present them as functioning.
5. Record activation boundary. A separate operator seeds a new source market position. Independent server poller observes broker state, computes lots, persists request identity/intent before dispatch and submits through the broker public API. Mark confirmed only with exact operation/event evidence. Poll/restart does not duplicate; no browser-driven copying.
6. Show subscription/instrument/direction/actual copied lots and sizing evidence. Preserve account/strategy/subscription/intent state over app restart while fixture stays up. Safe local Stop disables entries and closes only exactly confirmed owned test exposure, leaving unrelated/manual positions intact. Unknown result holds/records incomplete cleanup without blind retry. Full bounded recovery/Stop is M2, not passed implicitly.

## First-demo clarity

When an unfinished subscription reserves the investor account, show its current Subscription and available management action instead of an enabled second Start form; retain server-side rejection as well. Show a compact copied-result summary with instrument, direction, actual copied lots and confirmed/pending/unknown status. Keep request/operation IDs and full sizing evidence available in a collapsed detail, rather than making raw JSON the only way a novice can find the copy.

## Same-currency rules

Use broker details/snapshot/contract/quote values and decimal arithmetic, not app defaults or expected outputs. Both accounts are USD in M1; clearly reject unsupported cross-currency sizing until M2.

- Proportional = source lots × amount ÷ fresh positive source equity × multiplier. Allocation positive≤verified investor equity; multiplier0.01–2. Floor to investor step; below min/rounded above max skips, never round up/clamp. Equity changes alone do not resize old mappings.
- Example: equity10000, amount2500, multiplier1, source0.08→0.02 at0.01step. Source0.03→raw0.0075→no entry. Other amounts/equity must use the same formula, not a constant ratio.
- 1:1 keeps exact lots, multiplier1. Incompatible min/step/max blocks. Separate activation risk budget is investor equity capped10000/floored to cents; it does not rescale lots. Source0.08→investor0.08 in a separate clean subscription run.
- Check eligible account/contract/trade settings, matching source/investor instrument/base/quote/calc-mode/contract-size specifications, actual traded-symbol quote≤5seconds, finite positive Bid≤Ask, margin/exposure and consistent source observation. Investor min/step/max may differ and must be checked separately, not required equal. Fixture exposes1% forex margin metadata: evaluate investor margin in account currency using available scoped quotes, not source equity as free investor funds. Missing data blocks with the relevant reason.
- Read-only hypothetical examples never authorize a trade or become order settings.

## Nonnegotiable local safeguards

Use server-side ownership/session/Origin boundaries, encrypted retained private credentials, failed-login protection and explicit consent. Use installed established crypto, not plaintext encoded as encryption or homemade crypto. Fixture skips signature verification, but app still verifies partner/account capability through actual fixture reads; do not trust a submitted role/account.

Separate synthetic broker origin, application origin/state and operator control origin/token. Only test driver may seed/control the fixture. App never imports fixture internals, uses control credentials, seeds a copied position or obtains expected results. Bind local services to loopback and never fall back to a real broker. Unknown dispatch/outcome remains durable and held; automatic unknown recovery need not be complete in M1, but unsafe retry/invented success is forbidden.

## Retained ordinary-flow corrections

Changing an input covered by confirmation may clear that confirmation; checking the confirmation itself must not clear it. Repeated sign-in with the identical verified account/key pair preserves the existing explicit connection and its ownership. A different pair must not overwrite working access.
