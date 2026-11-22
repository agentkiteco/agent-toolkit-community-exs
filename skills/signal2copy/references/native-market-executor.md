# Native market executor: useful bounded increment

Continue the same application after native onboarding, managed synchronization and bounded preflight. Build an unattended market execution/recovery/report-journal path first; do not expand immediately into every pending topology. Preserve existing encrypted credentials, subscriptions, private ledgers and evidence. Shipping production execution stays technically disabled until all required authorization gates are accepted.

## Build in observable steps

1. Install and connect the [bundled native executor/runtime](runtime-integration.md), keeping subscriptions in the canonical account-owned collection so unfinished-account reservations, operator disconnect checks and history see them. Reuse stored encrypted credentials; never request keys again for execution settings. Implement host hooks and ordinary role routes rather than rewriting the supplied engine.
2. Back the SDK journal interface with the application's existing durable state (`AppJournal` or equivalent). Persist exact account, request UUID, method, resource/body fingerprint, dispatch state and operation binding before writes. Cloud acknowledgement must precede dispatch. Journal rows contain no signing credentials. Distinguish encrypted credentials/checkpoints from local business-state file permissions.
3. Wire explicit Start/Pause/Resume/Stop and an unattended worker into the actual app. Start requires separate Connect, synchronized fresh baselines, admission, sizing and consent. Support new-only Buy/Sell market opens initially. Baseline existing source positions; Pause consumes current observations; Resume never replays paused history. Process restart or changed stream generation pauses entries until fresh synchronization and explicit Resume.
4. Route market submissions through the native SDK and one final authorization boundary. Preserve original executable quote times and re-evaluate exact source/target/epoch/sizing evidence after durable reservation, immediately before send. Owner-reset freeze and a closed durability fence must stop the worker **before reconciliation or mutation**, as well as block request creation and final dispatch. Recheck fences after potentially slow authorization work.
5. Reconcile exact outcomes, record trusted owned mappings and feed the existing report/quality journal. Add useful state, next actions and role guides before broadening supported methods.

## Production denial and injected acceptance

Use production-denying enabled/open/close policies with no browser or environment enable switch while full gates remain incomplete. A passing bounded margin calculation is not full RMS or write authorization. UI/API must distinguish production execution disabled from an explicitly injected simulation.

Exercise lifecycle and native-shaped mutations only through a generated-key test policy and transport outside shipping application code. That external subclass/bootstrap may authorize bounded injected scenarios; do not package it, create fake verified live metadata or use it as a production bypass. First test the shipping policy's actual API denial and zero mutations. A separately successful native SDK read or WebSocket handshake does not certify managed copying, risk controls or trades.

## Exact correlation and ownership

ACK accepts processing; it is not a fill. Bind observations to the correct account and apply these rules:

- With an already known exact operation ID, accept a matching operation-only transaction when its request field is absent. Reject a present conflicting request ID or different operation ID.
- Without a known operation ID, require the exact retained request ID plus an operation ID before binding. Never infer a lost ACK's operation from a similar position or timing.
- A confirmed operation status alone establishes no position ownership. Retain an entity-linkage hold unless exact correlated transaction/history evidence identifies the effect. Lookup 404, missing events or a new snapshot do not prove non-execution.

For a bounded single-position market open, require exact correlated changed-position evidence matching instrument, side, volume and open state; any order/deal links must agree. Record actual target ID/lots and request/operation evidence only then. Reject conflicting operation rebinding. Full-close confirmation must identify the same mapped position and its explicit terminal state. If the schema/topology does not establish the required evidence, hold it; do not invent a normalizer or approximate match.

A close authorization must validate the exact target ID **and** instrument, direction, open state, positive remaining volume and confirmed volume anchor. Changed semantics or increased exposure require review. Manual/unrelated exposure is never a fallback target. Source snapshot absence alone is not a source close; use exact evidence. Missed events are not replayed by resubscription.

## Unknown results and Stop

Persist pending/unknown outcomes and never blindly resend after timeout, malformed success, disconnect, restart or operation lookup failure. A proven pre-dispatch veto is distinct from an unknown broker effect. Known terminal refusal remains terminal; any supported cleanup retry needs a new explicit action and fresh exact-owned evidence.

Stop blocks entries and closes only confirmed owned targets. Unknown opens remain unowned, with follow-up. If a genuinely late exact result establishes ownership after Stop, retained Stop intent can clean up that exact target. Unknown closes are never repeated. Stopped does not mean flat, resolved or archived: live unknown commands and confirmed unclosed owned exposure must continue reserving the account until settled or an explicit supported investigation/archive procedure is completed. Do not silently release it by changing the status label.

A strict account-level unresolved-risk hold is acceptable for this bounded increment when disclosed. It is not the full target's independent-group risk scheduler. Preserve all original evidence and explain the next action.

## Trusted reporting and limits

Append confirmed account/strategy/subscription/position/request/operation links to the server-owned mapping journal. Populate copying-quality operations from actual command evidence: submitted target volume, dispatch/result status, confirmed position IDs and entry average only when a confirmed single-position submission supports it. An unsized full close uses full remaining, never fabricated numeric lots. Attribute saved native history through trusted exact mappings; preserve missing costs, unknown ownership and incomplete coverage. Provider outputs must not expose investor identity or unrelated account data.

The first market increment excludes partial/protection management; continue with [native position management](native-position-management.md) to add that supported subset, then [native pending entries](native-pending.md). Keep the current increment's unsupported cases explicit, including include-current, native Advanced/daily-loss enforcement and paused sizing edits. Do not silently open an unprotected copy when source protection cannot be managed. Full production session, quota/remaining-capacity, write-permission, ownership and portfolio RMS acceptance remain separate gates. Status-only operation/entity-history recovery may remain held rather than guessed.

## Focused acceptance boundary

Verify through actual app HTTP plus native-shaped injected SDK/stream traffic: production denial, unattended new-only copies, ACK versus exact finalization, known operation-only events, Pause/Resume without backlog, exact owned full close, terminal refusal, unknown/restart/no resend, Stop retaining live follow-up/account reservation, late exact cleanup, trusted report journals and status-only ownership holds. Use focused offline checks for semantic close anchors and freeze/durability fencing before worker mutation and final dispatch.

Record authored, executed and live-confirmed results separately. Preserve failed branches and unknown ledgers; do not reset them to manufacture success. Counts from SDK reads, offline guards, HTTP scenarios and real transports overlap and never establish a success probability or full native executor parity. Update BUILD_STATE and provider/investor/owner guides with actual supported actions, executed evidence and remaining gates.
