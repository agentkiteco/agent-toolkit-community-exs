# M2 sizing and account-specific FX

Reuse `Conversion` and the native engine's sizing/margin path from the [bundled runtime](runtime-integration.md). Bind the host's `fx` hook to the same account-scoped conversion instance used by the actual execution path; a separate screen-only formula is insufficient.

Use decimal arithmetic and the full-target formula. Preserve exact1:1lots and multiplier1. Proportional uses fresh positive source equity, investor amount converted into source currency, multiplier0.01–2, floor to target step, then min/max rejection without clamp. Compare rounded, not raw, volume to maximum. Amount is not reserved funds or an exposure cap; actual investor equity constrains it. Preserve the separate capped1:1risk-budget rule.

Useful differentiating case: source0.11, source equity10000, amount5000×1, target step0.01/max0.05 → raw0.055→0.05permitted. Source0.12→0.06exceeds max: no order. Exact1:1source0.03 with target0.02step is incompatible, not rounded.

Same currency is rate1. Otherwise sell base at Bid, inverse at1/Ask, multiply bounded fiat cross legs. Prefer valid tick-only routes before routes using references. Get inventory/specifications/quotes for the actual account; source/target may differ. Source observation needs source contracts, not an irrelevant source-margin FX stream. Real execution still needs the traded symbol's fresh actual tick≤5seconds and independent permissions/contract/margin/transaction checks.

Accept finite positive Bid≤Ask, original nonfuture timestamps; a new reception does not refresh old broker time. Trading-disabled fiat pairs may value currencies, never authorize trading. When ticks are unusable, permitted conversion fallback uses broker Bid/Ask M1 over the preceding hour then D1 over preceding7days, newest valid reference. Keep original candle OPEN time≤now/age≤7days, reference_only=true, broker_candle_close/timeframe/open-time provenance and unknown constituent tick time. Never use a candle as execution price or a non-fiat bridge. Fresh actual ticks supersede references, not vice versa.

Cache positive/negative candle lookup60seconds per account/instrument; readiness report reuse30seconds. Access/transport/quota errors retain normal recovery rather than silently trying another timeframe. Missing route remains unavailable with from/to and rejected quote/cause evidence, never external/manual rates or currency inference from names. No exchange trade is used for FX. Disclose route/rate/source/times and raw/rounded lot evidence in readiness/volume calculation. Authored conversion code and displayed rates do not prove broker submissions used them; inspect actual native request/effect evidence.

## Wire the conversion into the existing application

Keep one conversion policy shared by Start/readiness, manual Resume and actual dispatch sizing; journal the exact snapshot used by each decision. Label units: allocation is in INVESTOR currency; rate is SOURCE currency per one INVESTOR currency; source equity is in SOURCE currency. Multiply allocation by this rate exactly once. Existing copied exposure keeps its recorded entry sizing; later equity/rate changes alone do not resize it.

Discover currencies from explicit contract base_currency/quote_currency metadata in the relevant account inventory, never split an instrument name. Source account contracts establish source observations; do not require a conversion stream on the source when the investor account supplies valid valuation data. Unknown/missing currency or route is unavailable, never rate1by default. Currency equality is exact; do not silently equate cent and ordinary currency units.

Keep valuation direction separate from liability/margin estimation: conversion of available allocation sells its currency, while the funds required to cover foreign-currency margin must use a conservative purchase cost (or authoritative broker margin result). Preserve the earlier same-currency traded-symbol Ask guard. Record amount/rate/units and investor-currency margin separately; a valid sizing rate does not establish sufficient margin.

| Native application case | Inspect actual evidence |
| --- | --- |
| Same/direct/inverse/cross | Submitted lots, input units, each leg's Bid or1/Ask, account identity |
| Tick-only versus reference | Valid tick cross wins over a direct candle route; fresh tick replaces cached reference |
| M1/D1 reference | Original open time, newest valid row, reference-only marker and unknown last constituent tick |
| Missing/invalid/error | No submitted order, actionable unavailable cause; access/quota failure does not silently retry D1 |
| Execution quote invalid | No order even when conversion candles are valid |
| Volume and margin | Floor before maximum comparison, exact1:1grid rejection, insufficient investor-currency margin rejection |

Verify positive/negative candle caching by account/instrument and unchanged original timestamps, not only a computed rate in a helper. Keep the scope of native HTTP cases separate from offline algorithm checks. The target defines5seconds for execution ticks and7days for candle references; any extra FX last-tick age limit chosen by the reconstruction must be recorded as a policy assumption until independently matched, not silently presented as reference parity. A full readiness report UI/30-second report reuse remains a separate deliverable if this increment lacks it.
