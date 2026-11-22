# M2 acceptance — scope each result

Continue the existing generated app in a versioned source branch with separate test state, preserving M1 evidence/keys. Choose checks for the agreed increment; the table is a staged coverage map. A bounded pending/recovery step can finish with one local lifecycle/failure walkthrough from [native pending recovery](native-pending.md#acceptance-and-guides); add the cloud persistence probe when deployment or cloud state is actually changing. Do not claim unrun matrix cases or run historical live trade/reset scripts.

| Boundary | Required outcome/evidence |
| --- | --- |
| Source management | Confirm actual SL/TP set/remove, anchored repeated partial close and full close, preserving manual exposure |
| Pause/Resume | No new paused entries, existing owned management continues, explicit Resume with fresh checks/no replay |
| Pending | Four types placement/edit/cancel; exact full/partial fills without market top-up; residual review/unknown link handling |
| Unknown write | Apply-then-lost ACK, no resend during polling/restart, exact late result settles same intent; independent safe scope continues |
| Stop | Known copied items cleaned; uncertain cleanup bounded/follow-up, no false flat/confirmation or manual closure |
| Sizing/FX | Actual submitted lots across exact/proportional/rounding and direct/inverse/cross/reference guards; no candle execution price |
| Real adapter | Official signing/discovery/streams mapped and tested offline; actual reads/trades separately authorized and classified |
| Local/cloud persistence | Restore nonempty provider/account/strategy/subscription/intent; original key; stale revision/instance rejected, failed durable ack blocks broker writes |
| Cloud installation | New explicit account/Worker/bucket/origin; public health/UI/protected denial/assets; generated backend actually running, not a bridge-only canary |
| Cold restart | Stop/recreate process, restore original nonempty state, no duplicate ambiguous request; do not resolve unknown from a fresh empty broker |
| Guides/continuation | Provider/investor procedures updated, owner deploy/key-backup/restore note added; BUILD_STATE separates implemented/tests/live/deployed/missing |

Synthetic transport lacks real signing/WebSocket/dynamic-margin/price-trigger behavior. Fixture tests do not prove real-broker permissions or every partial-fill topology. Cloud health/upload and an empty checkpoint do not prove application durability. Code review, configuration validation/dry run, isolated state-bridge test and full app cloud restore are four distinct statuses.

Record failed checks with their exact next dependency, never as passed by inference. A missing credential blocks real-broker validation, not local implementation. A missing cloud answer blocks deployment only. A failed cloud persistence gate leaves trading disabled. Full target/M3/M4 acceptance remains separate.
