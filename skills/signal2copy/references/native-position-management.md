# Native partial reductions and protection

Extend the same native market executor after its exact ownership/journal path works. This increment manages already confirmed copies; use [native pending entries](native-pending.md) for the separate order-to-position handover. Full production RMS remains a separate gate. Keep real execution denied until all required gates are accepted. Use generated-key injected mutations for acceptance; live read success is not write authorization.

## Partial reductions use fixed anchors

Retain the original confirmed source volume S0 and actual target fill T0, separately from current remaining target volume. For a supported source reduction S, compute desired remaining lots from T0 × S / S0, floored to the applicable target step. Compare that absolute desired remainder to fresh confirmed/observed owned exposure. Never repeatedly apply a ratio to an already reduced target anchor, resize because equity/FX changed, top up a manually reduced target or touch another position.

Recheck account/position identity, instrument, side, open state, current conditions and remaining volume. A source increase or changed semantic anchor is a separate unsupported/review case, never a silent top-up. Validate partial-close quantity and resulting remainder against current broker rules; missing/incompatible metadata remains held. A full remaining close uses its documented full-close semantics rather than inventing a dust order.

Native partial close is DELETE `/v1/trading/accounts/{account}/positions/{position}` with positive `volume` in the signed query and an empty body. Persist the exact close amount, expected remainder, source observation and request identity before dispatch. A correlated finalized partial result must identify the owned position and expected remaining volume/open state; full closure needs its terminal result. Operation-confirmed status alone is insufficient.

Lost ACK/final-event uncertainty retains the original command. Neither restart nor a changed snapshot permits resending it. Pause continues authorized reductions/protection of owned positions while excluding new entries; Stop waits for exact resolution of an earlier unknown reduction, then manages only the confirmed remaining exposure. Preserve paused/stopped intent and original anchors across restart.

## SL/TP belongs to the exact copied position/order

Use [open position](https://www.exness-api.com/reference/open-position) fields for atomic protected entry when supported. Validate positive finite price strings and `point_digits`; do not silently strip source protection or open first and pretend later protection is already confirmed. Obtain source levels from an exact related SLTP order or explicitly supported position representation, not a same-symbol order. Missing or contradictory source evidence remains unavailable.

To add protection later, [POST orders](https://www.exness-api.com/reference/trading/place-pending-order) supports SLTP linked to the target position. Verify the actual SLTP variant rather than borrowing a pending limit/stop body. A finalized SLTP transaction may contain only changed orders, without a position row. Require exact command correlation, related target position ID, SLTP type, actual target order ID, state and expected levels before confirming protection.

Use [PATCH order](https://www.exness-api.com/reference/trading/modify-order) for a confirmed owned SLTP order. Omitted levels remain unchanged; string sets a level; null removes it. Handle independent and both-level removal deliberately. If an implementation deletes an empty SLTP order, require exact owned-order terminal evidence. A linked position alone does not prove that a pre-existing manually created target order belongs to this copy command. Multiple candidates, unowned orders or changed target protection require review rather than arbitrary selection/overwrite.

Validate explicit position-level protection as well as linked SLTP orders against the confirmed anchor. Contradictory representations cannot authorize a restore. A missing response level is not automatically a confirmed null; use a documented trusted delta merge or hold incomplete evidence. Likewise, a linked pending_new SLTP must not disappear merely because a selector accepts only placed orders: unresolved source protection cannot become an unprotected signal, and unresolved target protection cannot authorize a duplicate creation.

Account/instrument permissions differ by operation: the documented close-only exception for SLTP creation does not make PATCH universally permitted. Reuse actual account/instrument conditions, current quotes and supported price rules. Reject unsupported cases without claiming full production authorization.

## Consistent decisions and final dispatch

Bind each effect to the exact source/target position, protection order and canonical level/volume values. Re-observe after potentially slow target reads and after durable reservation. If source protection/volume, target ownership, stream generation or owner/durability fence changed, defer without a broker request. A source-position fingerprint alone does not cover protection stored in a separate order.

Serialize unresolved management commands within the affected copy group. An unknown protection command cannot be replaced by another create/edit just because the latest source changed. Keep entry confirmation, position ownership and protection confirmation separate. Never reopen an entry to repair uncertain protection. Exact late evidence may settle the original command; then a fresh supported decision may address the current source state.

## Reporting and acceptance

Record partial closes with the actual requested close quantity (`requested_close_volume` in the supplied reporting contract). Protection operations normalize to `protection` and have no invented lots or entry average. Preserve request/operation/order/position links, raw evidence and unavailable values. Financial reports still derive posted amounts from native deal records, not requested prices or anticipated profit.

Verify through the application and broker effects: anchored repeated reductions, manual target reduction/no top-up, paused management, Stop after an unknown partial close/restart, protected entry, later protection creation, edit, single/both removal and unrelated exposure preservation. Include source/target change at the final boundary and exact late outcomes. Keep scenario count bounded and label mocked native writes, offline guards, actual reads and live trades separately. Update BUILD_STATE and role guides only with implemented/passed scope; retain failures and outstanding review/production gaps.
