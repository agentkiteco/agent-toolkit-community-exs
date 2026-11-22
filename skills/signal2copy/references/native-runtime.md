# Native synchronization and pre-dispatch checks

After native onboarding, connect managed account-scoped streams and one shared evaluator to the same app's readiness and final dispatch boundary. A REST snapshot, open socket or previously cached green result is not current authorization. Preserve encrypted account bindings and explicit user intent.

## Managed streams

Reuse `NativeBroker`, `ManagedStreams` and the supported policy/quota ledger from the [bundled runtime](runtime-integration.md). Connect their account/epoch evidence to host routes and final dispatch rather than implementing a second synchronization engine. Its current supported design uses five account connections and denies insufficient returned capacity.

Use actual NativeStream/native protocol workers with retained credentials. Transactions require the new subscription's trading_state_snapshot before deltas. Ticks use the separate endpoint and preserve original broker time. Consume account floating state, selected instrument changes and HMR using their documented shapes. Some streams are quiet; a normal bounded receive timeout is not by itself a disconnect. Explicit disconnect/parse/subscription failures immediately invalidate relevant readiness, then reconnect with bounded backoff and fresh baseline. Do not claim durable replay.

Fence every worker/session by account and epoch. Late messages from an older epoch cannot restore synchronization or overwrite new state. A new transaction baseline does not alone validate ticks, conditions, account restrictions, HMR or session metadata. Unrelated account data is never a fallback. Keep in-memory stream observations separate from semantic durable intent writes; do not checkpoint unchanged monitoring timestamps every tick.

Expose authenticated sync/status/check actions in the app. Investor can inspect only its bound account and authorized selected-strategy summary; provider sees its source, never another investor's credentials/data. Starting read subscriptions is separate from trading consent. On restart, stored subscription intent/key material may persist, but synchronized/live flags must be reacquired. Old REST data can remain visibly historical while execution is blocked.

## One evaluator, explicit limits

Use decimal arithmetic and native configuration schemas. The current instrument reference names forex/forex_no_leverage/cfd/cfd_leverage; formula guides may also use historical1–4codes. Map documented equivalents explicitly, never infer from a symbol. Inspect actual leverage/fixed-margin/HMR units and supported calculation modes; missing/unsupported inputs block. Do not reuse fixture-only percent or time-zone assumptions as native facts.

A bounded evaluator must state which formulas/context it supports and disclose omitted full RMS/session/quota/ownership checks. It may return a useful proposed lot/margin calculation while authorization staysfalse. Distinguish calculation_passed, execution_gate_passed and execution_enabled. Unsupported native cases are unavailable, never an invented conservative-looking default labeled verified.

Weekly session boundaries are documented as UTC `Day, HH:MM:SS` strings in the current instrument reference. State when the implementation does not support their complete semantics; do not describe timezone as unknown merely because an earlier bounded gate rejected all nonempty schedules. Omitted boundaries and conflicting rules still cannot be guessed.

Check canonical source/investor/strategy binding, separate Connect/consent/publication, source-position observation and metadata, fresh positive finite account values, synchronized transaction epochs, actual traded-symbol Bid/Ask at most5seconds old/nonfuture, applicable permissions/conditions, exact1:1or Proportional allocation/FX/step/min/roundedmax, account-currency margin and uncertain exposure reservations. Preserve conversion-only candle rules; candle prices never satisfy executable tick checks. Native sessions/HMR/caps require authoritative evidence; unknown staysblocked. Use [official formulas](https://www.exness-api.com/trading/guides/formulas-calculations) and the current reference rather than guessing margin units.

## Durable final boundary

Bind evaluated plan/effect to the data epochs/revisions and original quote times. Evaluate again after slow discovery, state acknowledgement or journal commit, immediately before any broker write. If conditions changed/expired, no request may be sent. A proven pre-dispatch block is not an unknown broker outcome; preserve its evidence and retry semantics separately. If dispatch might have happened, retain exact account/request/operation identity and never blindly resend. SDK callback wiring alone is not full application RMS.

Do not enable native trading merely to demonstrate a green report. Validate the gate with generated-key/native-shaped injected streams and a deliberate delay/epoch change. Record actual effect/zero-write evidence separately from pure calculation checks, real WS/TLS and authorized broker reads/trades. Update both role guides with sync states, rejected checks, recovery and actual next action.

## Focused acceptance

Exercise baseline-before-delta, disconnect/reconnect, old-epoch rejection, quiet stream timeout, quote/account/condition changes, native mode permission/source/investor isolation, both sizing modes, missing margin/HMR/session data, and a final check that fails AFTER durable latency with zero broker write. Existing synthetic behavior and prior native onboarding remain regression responsibilities when common code changes. The full F11–F22 lifecycle/ownership matrix and M3/M4 remain separate until actually completed.

## Retained integration lessons

Before opening streams after process restoration, fetch and validate the account's fresh authenticated limits; a restored display observation does not repopulate the runtime quota ledger. A malformed fresh response must not silently reuse old valid quota configuration.

Bind each prepared effect to source and target stream generations. Read the live generation bindings again after durable acknowledgement and after any blocking final REST/policy reads, immediately before dispatch. Transaction versions and account epoch can remain unchanged during a ticks-only reconnect. Preserve fencing across complete runtime replacement as well as per-worker reconnects; reusing a counter value is not proof of the same session. Fresh verified owned cleanup may use a new binding rather than being permanently blocked by the subscription's original Start generation.


## Ordinary execution capability and replacement identity

Provide an explicit recipient installation distinction between native read-only operation and supported native execution. A fresh installation configured for execution must reach the same complete evaluator and durable journal through ordinary authenticated Start/Resume/management routes, without substituting a test permission policy. Keep existing read-only installations read-only; reject an implicit mode change on restoring sealed state. Configuration selects capability, not blanket authorization. Connect/readiness/stream consent alone sends no order; investor Start and every final mandatory check remain required. Unsupported native contexts stay held. Do not treat implementing this path as proof of real broker acceptance or enable an existing live installation during skill development.

Bind observations to a unique runtime/session incarnation in addition to account epoch and individual worker generations. Two completely different runtime instances may both report worker counters1, transaction version1 and account epoch0. Store the runtime component with the prepared effect and compare live bindings before and after blocking final work and acknowledged durable reservation. Invalidate the old generation at disconnect/replacement before discovery or connection can block. An obsolete per-connection callback must not update the current baseline or mark the replacement disconnected, even when its account epoch matches. Quiet receive timeouts alone do not replace the session.

A focused generated check can first make an ordinary explicit copy, reconnect reads and require explicit Resume, then replace only the target runtime immediately after durable command reservation. Arrange equal per-worker counters, transaction version and account epoch with an unexpired original quote; only the runtime incarnation changes. Require zero stale broker write and a proven not-sent command, not invented unknown execution. Resume consumes that source boundary without replay; a fresh later signal and owned Stop must still work under the new binding and preserve manual exposure. Inject only generated I/O and the timing fault, not permission-policy success. Retain real HTTPS/WebSocket and broker mutation acceptance as separate evidence.
