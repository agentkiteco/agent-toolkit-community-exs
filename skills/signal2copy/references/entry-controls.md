# Initial exposure and actual optional entry controls

This continuation connects the existing pure `policy_controls.py` rules to the generated app's actual **synthetic** engine through a narrow `entry_controls.py` bridge. Native order execution remains disabled. Reuse these behaviors and lessons when implementing F11/F23/F24; do not mistake this bounded evidence for full native enforcement or all lifecycle combinations.

## Explicit Start scope

New setup defaults to Copy new trades only, with explicit scope confirmation at Start. Include current exposure retains exact positions and eligible Limit/Stop order IDs from a fresh source snapshot for one-time evaluation. Market copies use current executable prices; pending copies use current source levels, without replaying closed history. Existing exact mappings/journal prevent duplicate entry. Retain one unfinished subscription per account.

Waiting initial entries remain eligible only while active. Pause/Stop cancel unfinished waiting entries and clear initial eligibility. Manual Resume consumes current observations rather than replaying initial catch-up or signals created while paused. A terminal skipped entry stays historical. Saving or opening Advanced preferences enables nothing. Only explicit application of saved preferences at a new Start copies them into that subscription; existing subscriptions remain unchanged.

## Five independent optional controls

Keep OFF/null defaults and explicit validated values. Feed the same actual server-observed source position, target snapshot, original executable quotes, calculated lots and exact mappings into optional checks; browser values are settings, not account/quote evidence.

- Adverse market entry deviation waits. Buy uses target Ask against source open price; Sell uses Bid. Better entry passes. Do not imply the check guarantees a pending order's eventual fill.
- Excess copied volume skips without clamping; mandatory min/step/max remain independent.
- Full whole-account position/pending-entry capacity waits. Include manual positions and placed Limit/Stop entries; protective SL/TP orders do not consume extra entry slots. Snapshot-represented exact mappings are not counted twice. Reserve unrepresented uncertain entry effects conservatively until exact reconciliation; never guess that a similar position belongs to an unknown command.
- Daily-loss threshold holds new entries. Automatic normal Stop is separate opt-in, with enabled threshold and explicit close consent.
- Expired optional signal age re-reads the exact source. Changed evidence waits for current observation; unchanged expired evidence skips, with refresh evidence. Never turn its original timestamp into a new signal merely by receiving or refreshing it.

Keep `waiting`, terminal `skipped`, confirmed, rejected and unknown outcomes distinct. Retriable waits re-evaluate current source/target conditions and never blindly resend uncertain effects. Disabled optional controls add no invented preset threshold. Mandatory broker/margin/quote/idempotency gates still apply.

## Daily equity state and durable desired Stop

Observe first-seen UTC-day whole-account equity even while the optional loss limit is off and while Paused. Retain that baseline and measured loss across restart; it includes manual/floating/funding effects and is not copying-only realized P/L or a funding-neutral return. Daily cash threshold is current Proportional amount or retained capped/floored 1:1 activation-equity budget, times enabled percentage. Multiplier does not silently rescale the threshold. Explain threshold consequences in paused sizing edits.

Preserve the activation-equity budget for later confirmed switch to 1:1, without resizing existing mappings. Legacy missing budget may be initialized only from fresh verified equity during explicit confirmed switching, with audit evidence; do not guess historical equity.

Persist a subscription/day Stop marker and desired-action identity before normal exact owned cleanup. A processing action continues journal recovery after restart; do not issue another blind Stop or repeat uncertain commands. Close only confirmed owned exposure, leave manual/unrelated exposure intact, retain unknown/permanent follow-up evidence and never automatically Resume on a new day. Disabling the daily limit disables auto-close. Missing broker/durability observations hold with visible evidence; automatic protection is not an execution-price or availability guarantee.

## Paused settings and final checks

Use the app's actual saved fields consistently (`amount` in this generated app); a compatible `allocation` alias may be accepted, conflicting values must reject. Support same-mode edits and preservation of omitted old-client values. Exact 1:1 rejects Proportional-only parameters, resets multiplier 1 and keeps the saved budget. Ownership, current settings revision, explicit confirmation and unresolved **commands plus intents** gate edits. Invalid/above-equity input must not partially save subscription settings. Audit atomically, keep Paused, do not Resume or remap existing lots. Prefill saved values and reset confirmation after every edit.

Recheck current provider policy with fresh source/investor evidence at final Start/manual Resume commitment under the application lock. Optional controls also run after durable entry command fencing, immediately before send, using current source/target/quote evidence and original executable quote ages. A veto before any write is `not_sent`, with waiting/skip action; it is not an unknown broker outcome. If a send may have happened, preserve exact request/operation identity and never resend based on absence or a similar snapshot.

## Retained execution evidence and boundaries

Parent executed the focused actual-app/fixture driver using a retained author-side driver (not a recipient startup command): **17 checks passed**, processes stopped. Evidence is retained in its `evidence/results.json`. Cases cover default new-only, one-time current market inclusion, paused same-mode actual-amount edits/above-equity rejection, no paused backlog, new-entry sizing, volume skip, slot wait without confirmed-mapping double count, adverse-price wait/recovery, original-age refresh/skip, explicit preference application, whole-account daily block, separately consented owned Stop/manual preservation and restart non-repetition. Counts overlap; they are not a success probability or complete F11/F23/F24 matrix.

The separate `check_final_boundary.py` is an offline actual `Engine.open/request` plus `EntryControls.before_dispatch` probe with an injected state change after the durable fence. Parent executed **2 offline assertions**, both passed: command `not_sent`, proper waiting/skipped mapping and zero broker writes after the fence changed. Actual evidence is retained in `evidence/final-boundary-offline.json`; these are separate from the focused HTTP driver and prior native SDK callback evidence. No socket or real transport was used by this offline probe.

Application source was cloned from the retained composed app into a new branch. Keep prior source, private ledgers, failed evidence and unknown records; do not reset them to make a run pass. Driver controls stay outside application code and never share their control token with the app. This increment has no actual broker/account/credentials, native WebSocket/TLS, cloud, browser/mobile/theme or full native Advanced/copier/RMS acceptance. Existing common-engine regressions remain a separate evidence responsibility. Full target behavior and broader exact lifecycle/ownership/recovery remain required where unaccepted.
