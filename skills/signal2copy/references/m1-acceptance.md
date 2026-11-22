# M1 outcome checks

Run one application against a separate fresh fixture. Use the app's native HTTP/browser operations; document their routes, do not change the broker to implement copying. Keep control token out of app configuration. Record actual commands/results in BUILD_STATE. These are small integration checks, not an upstream benchmark.

| Case | Required evidence |
| --- | --- |
| Registration failure/success | Invalid invitation/key leaves registration open; successful verified provider closes it. Pre-provider investor entry is blocked; registered pair re-login works. |
| Publication | Read-verified source1111 and published strategy appear in public catalog/detail without source secret disclosure. If Unpublish is offered, it blocks new entries without abandoning safe owned-exposure cleanup. |
| Investor isolation | Account2222 connection/read is scoped; wrong/foreign source-account access denied. Initial sign-in/connection makes zero broker trading mutations. |
| Explicit boundary | Seed source exposure before Start: new-only excludes it. No investor copy before consent. Double Start cannot create a second unfinished subscription. |
| Proportional actual effect | Source0.08, equity10000, amount2500×1 → actual submitted/confirmed investor0.02. Read actual broker ledger and exact result mapping, not just displayed arithmetic. |
| Repeated polling/restart | Same source observed repeatedly and after app restart while fixture stays up: same confirmed target, no extra POST. Subscription/intent persists. |
| Minimum failure | New source0.03 under same inputs gives0.0075<0.01: explicit skip, no investor mutation. Invalid/missing quote/equity must not be disguised as that minimum failure. |
|1:1actual effect | After safe cleanup/new subscription, a fresh source0.08 gives actual0.08, not the Proportional result. |
| Safe local Stop | Stops new entries, closes only exact confirmed copied test position, preserves a separately seeded manual investor position. Unknown outcome holds, never blind resend. |
| UI/guides/continuation | Usable provider/investor controls, masked fields, readable desktop/mobile; both guides reflect actual commands/labels/limits. BUILD_STATE gives reproducible checks and next action; continue does not reset/re-ask cloud info. |

At least one differently valued same-currency case should use the same public contract, avoiding hardcoded expected lots. A later evaluator may hold this case out from tuning. Do not report this packet's examples as independent held-out evidence.

Fixture self-check is a separate prerequisite. Missing socket/dependency/tool permission is not an app failure; use normal approvals or record the concrete blocker and complete independent work. Do not claim passed without executing the relevant check. No real accounts, broker calls, trades, cloud deployment or production mutation are part of M1 acceptance.

## Deliberately incomplete at M1

The map's remaining required functions are still open: real Exness transport/crypto verification, cross-currency/candle FX, pending/partial/protective lifecycle, full automatic recovery/bounded Stop and uncertainty scheduling, Advanced/admission controls, complete reports/fees/CSV, owner console/disconnect/share link, durable Cloudflare restore and full baseline acceptance. An M1 demonstration cannot close these gaps. Update their states when later implementation and actual tests exist.
