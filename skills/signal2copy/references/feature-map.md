# Functional coverage and delivery map

Target: full-target.md, baseline signal2copy-2026-11-18-v1. All rows are required for the final target; intermediate releases explicitly list their omissions. **No row is claimed implemented or accepted in a new successor build.** This map organizes existing reference behavior, not test success percentages.

M1 = first local usable path; M2 = complete execution foundations/first Cloudflare deployment; M3 = current-product feature completion; M4 = independent reconstruction and final scoped acceptance. M1/M2 must retain core ownership/consent/durability safeguards even when other features remain unavailable.

Evidence below is a provenance pointer, not independent acceptance: D = reviewed product requirements/English guide; P = recorded product tests/release/feedback evidence; L = scoped product live observations, with their documented limits. A P/L entry never means every case in that row was exercised live.

| ID | Required observable result / distinguishing check | Increment | Reference basis |
| --- | --- | --- | --- |
| F01 | One atomic provider registration; pre-registration investor/catalog gate; invitation not consumed on failure | M1 | D; FB-002 |
| F02 | Unified verified role detection, registered-pair ownership; no foreign-Partner/failure fallback | M1 | D; FB-005/007 |
| F03 | Account-scoped investor sign-in, explicit connection, selected strategy continuity; login does not trade | M1 | D; FB-003/004/006/008 |
| F04 | Encrypted credentials, secure sessions/Origin checks; no browser-persisted keys or secret echo | M1 | D; FB-019 refinement |
| F05 | Source verification, dedicated source per strategy, create/publish/unpublish and subscriber/filter views | M1 core; M3 views | D; guide4.1–4.8 |
| F06 | Public registered catalog/detail/history/observed metrics with coverage; empty/loading/error states | M1 core; M3 metrics | D; FB-012/031 |
| F07 | One unfinished subscription; explicit scope/Start; successful creation routes to existing Subscription | M1 | D; FB-006/008 |
| F08 | Proportional/new-only defaults; both same-currency modes actually size eligible market entries | M1 | D; sizing packet; FB-009/023 |
| F09 | Exact1:1 lots, incompatible grid rejected, distinct capped activation risk budget | M1/M2 | D; numeric examples; guide5.3 |
| F10 | Proportional formula, positive source equity, step floor, rounded maximum/no clamp, actual equity cap | M1/M2 | D; sizing packet; FB-023; scoped L |
| F11 | Initial include-current exposure and new-only boundary; no paused-history/initial-catch-up replay | M2 | D; lifecycle/pending packets |
| F12 | Buy/Sell and four pending types, repricing/protection removal/cancellation, partial/full closes | M2 | D/P; scoped live matrix |
| F13 | Exact pending-fill/partial-fill ownership and anchored reductions; no duplicate market open | M2 | D/P; fills packet; limited L |
| F14 | Account-specific real broker signing/discovery/REST/streams/quotas; synthetic broker isolated | M2 | D/P; broker docs; scoped L |
| F15 | Consistent source/target observations; retain exact mappings, not matching by similar positions | M2 | observation-consistency packet |
| F16 | Direct/inverse/cross FX, Bid/Ask direction, account isolation, conversion-only disabled instruments | M2 | FB-022/024; scoped L |
| F17 | Bounded labeled M1/D1 reference fallback, tick-first merge/routes, age/cache/quota safeguards | M2 | FB-024; scoped Proportional L |
| F18 | Fresh actual traded-symbol tick/synchronized transactions/contract/permissions/margin checks | M2 | D/P; execution/FX evidence |
| F19 | Intent durably committed before dispatch; pre-dispatch retry differs from unknown/no-resend | M2 | D; observation/recovery evidence |
| F20 | Uncertain scope isolation, reserved margin/slots, independent safe same-symbol execution | M2 | D; November9 scope rules |
| F21 | Pause manages owned exposure, Resume rechecks/consents, restart preserves boundaries | M2 | D/P; scoped lifecycle L |
| F22 | Bounded Stop, permanent unresolved follow-up; no manual-exposure closure or blind resend | M2 | D; bounded-Stop supersession |
| F23 | Five optional Advanced controls OFF/null; confirmed edits and separately opted daily-loss closure | M3 | D; Advanced decision; guide5.6–5.8 |
| F24 | Paused mode/amount/multiplier edits atomically saved without resuming/remapping existing positions | M3 | FB-023 |
| F25 | Contextual manual exposure/protection/entry/loss-close review; preview/read is not authorization | M3 | D; FB-010; guide6 |
| F26 | Recovering/skipped/rejected/unknown/action-required distinct; acknowledge retains incident evidence | M2 core; M3 full UI | D; FB-010/011 |
| F27 | Real-only strict is_demo rule at connection/Start/Resume; defaults/active/source exemptions | M3 | FB-020 |
| F28 | Exact selected-account Partnership report rule, no email; reuse sign-in keys; failure remains pending | M3 | FB-019 account/refinement contracts |
| F29 | Same currency versus selected source, cents distinct; final bound strategy evidence | M3 | FB-025 |
| F30 | Same stream suffix type, open-ended codes, separate is_demo; source/policy freshness binding | M3 | FB-026 |
| F31 | Provider-only independent settings, revision races/omission compatibility and preserved active copying | M3 | FB-019/020/025/026 |
| F32 | Whole-account/source history, copying-only attribution; provider anonymized/per-currency reports | M3 | D; FB-012/016/027 |
| F33 | Recorded P/L/period summaries/equity/coverage; no fabricated subscription/full-period return | M3 | FB-012/016/027/030 |
| F34 | Signed posted native-currency fees/net; open fees, funding/compensation separate; unknown withholding | M3 | FB-027/030; scoped report L |
| F35 | Dedup before pagination; Zero/Raw Included-at-opening only with retained matching evidence | M3 | FB-027/030 |
| F36 | Operation-specific volume/entry-price availability; pending placement not fill; raw/effective CSV | M3 | FB-030 |
| F37 | Authenticated canonical Copy link; success only after write; keyboard/manual fallback | M3 | FB-033 |
| F38 | Owner-scoped settled-account disconnect deletes working access, fences refresh, retains history | M3 | FB-032; explicit one-account L |
| F39 | Responsive role workspaces, accessible reviews/forms, themes and long keys/cards without overlap | M1 onward | D; FB-017/031; visual similarity relaxed |
| F40 | Independent recipient Cloudflare resources; persistent nonempty state/restore; unattended execution | M2 | D/P; cloud operations; old empty-restore limit |
| F41 | Separate owner console/status/password/invitation; reset confirmation/freeze/idempotency/backup handling | M3 | FB-021; owner console docs |
| F42 | Provider and investor English guides match implemented version; owner deploy/restore notes | M1 onward | Current guide sections4/5/6/7; new delivery requirement |
| F43 | Independent clean-workspace reconstruction, failure case and held-out check; honest remaining gaps | M4 | New validation, not inherited product passes |

## Supersessions applied

| Historical instruction | Current baseline decision |
| --- | --- |
| November10 function/UI target and deferred later changes | Current product through FB-033; implementation-independent functional target |
| Preserve original visual design/pixel screenshots | Preserve function, readability, accessibility and responsive behavior; exact visuals optional |
| Provider keys fingerprint-only/re-enter in settings | Disclosed encrypted sign-in key reuse; separate verification consent; old-session migration caveat |
| Client affiliation/email/full-client-UID prerequisite | Selected full trading-account attribution; no email/UID join |
| Same-type control awaits new broker field/known-code whitelist | Trading stream_id final-code equality, open-ended, separate is_demo |
| All production candle FX prohibited | Bounded account-scoped conversion references; actual execution tick still mandatory |
| Proportional10,000 cap | Actual equity cap; retain separate1:1 activation budget rule |
| Net always unavailable/missing always0 | Recorded signed period net with evidence completeness; display-only cost0 and narrow opening-fee resolution |
| All uncertainty globally blocks/Stop waits indefinitely | Scope-level holds, bounded Stop with permanent unknown follow-up |
| Laptop height forces one-wide catalog card | Width-based multiple cards, ordinary scrolling; no exact CSS reproduction obligation |
| Old profile heading Session details | Copy settings; Account settings remains the menu meaning |
| Share messengers/combined Trading results chart discussed | Proposals excluded from target; Copy link only |

No row imports source-only one-off maintenance, live test balances, forced account disconnection or trading authorization into a new build. Existing product evidence informs the contract but never marks a generated implementation passed.
