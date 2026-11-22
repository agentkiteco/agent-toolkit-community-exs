# M2 — Execution and recovery in the same application

Extend M1 source/state rather than resetting or replacing the project. Keep intent and exact broker correlation durably before dispatch; unknown after write is never an eligible resend. Make each substep runnable and update BUILD_STATE/guides before proceeding. Full-target.md governs final behavior; incomplete substeps stay explicit.

## Owned market positions

- Persist source→investor request/operation/position links and original sizing at entry. Apply source SL/TP updates and explicit-null independent/both-level removal to the exactly owned target. Broker protection is a separate order; do not infer its state from position fields alone.
- Anchor reductions to cumulative source change and recorded copied exposure. A0.08source/0.02copy reduced to0.04source targets0.01remaining copy; repeated observations do not repeatedly close0.01. Full source close closes only exact mapped remainder. Neither equity changes nor manual investor reductions authorize silent topping-up.
- Pause stops new entries/cancels owned pending and unfinished initial opens, keeps authorized management of existing copied market exposure. Consume paused entry history. Resume is explicit with fresh checks; it does not replay paused entries or initial catch-up. Unpublication must not create new entries.

## Pending lifecycle

Follow all Buy/Sell Limit/Stop types with exact placement correlation, price/protection edits, independent/both protection removal, cancellation and no assumed fill. Read pending-fills.md: reserved IDs are not positions; accumulate unique execution deals; keep filled exposure separate from residual, and do not open a market replacement after fill. Ambiguous links hold only the affected group. Pending residual review/partial-fill behavior is not equivalent to ordinary market-position reduction.

## Unknown outcomes and continuity

1. Persist a stable account/request identity, intended effect, ownership group, dispatch phase and evidence. Write denial before durable acknowledgement prevents the broker call. Traced pre-dispatch failure is retryable with backoff; explicit refusal is terminal, not unknown.
2. On ACK retain operation ID, but require exact account/request result/event/deal evidence for a confirmed fill. Lost ACK/503/timeout/malformed response or operation404 remains unknown. Query exact operation or account request identity; snapshots/history are supporting data, not authority to adopt a similar manual position.
3. After restart reuse the same evidence and investigate without resending. Late exact evidence can settle the operation and resume authorized safe processing. Replaying the same deal/event must not enlarge exposure.
4. Hold affected source groups/exact linked exposure; independent safe groups, including same symbol, may continue with fresh risk checks. Reserve uncertain margin/slots conservatively. Unknown account ownership/auth/market state can require a wider hold. Do not implement this as an always-global queue and claim scope isolation.
5. Ordinary connectivity/quote/quota recovery does not change active/paused/stopped intent or require repeated Resume. Explicit Pause/Stop, publication and protective holds win over recovery.

## Stop and restart

Stop closes/cancels only exactly owned copied exposure and blocks new entries immediately. Unknown cleanup remains unknown with bounded reconciliation and permanent broker follow-up; eventual Stopped is not proof the account is flat. Keep operation IDs/request IDs/times/known exposure for investigation. Archived follow_up_only records from stopped subscriptions do not alone block a new subscription. Known rejected cleanup retries need new exact-exposure confirmation; ordinary exact-result recovery does not.

Never resolve the M1 probe's retained unknown by pointing it at an empty replacement fixture. Preserve that ledger; a new isolated test installation can exercise newly implemented recovery with its own continuous broker state. Resume existing user state only with the original encryption key and actual broker evidence.

## Durable local-to-cloud boundary

Provide one persistence adapter called by every semantic state transition, especially before dispatch. Local SQLite alone suffices only for local tests. Cloud mode must restore before readiness/execution and await remote durable acknowledgement before every trade intent/dispatch fence. A stale revision/instance or unknown acknowledgement fails closed. Avoid persisting unchanged polling timestamps as constant R2 writes; keep monitoring observations separate from semantic journal transitions. Pin dependencies and document exact commands.
