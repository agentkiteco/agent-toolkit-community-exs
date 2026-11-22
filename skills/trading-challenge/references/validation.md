# Exness Trading Challenge: Acceptance and evidence

This package is an instruction-only specification. It includes no executable application, tests, or deployment helpers. Validation of the Markdown skill does not prove that an implementation works, and another edition's past test counts do not apply automatically.

When implementing a contest, create meaningful checks against the actual chosen runtime and record what was observed. Use fictional accounts/grants and isolated storage for mocked tests, fixed clocks where appropriate, and no network fallback. Do not borrow live credentials or state from an old project.

## Implementation acceptance

| Area | Observable requirement |
| --- | --- |
| Fresh build | Documented dependency install/build/run/check procedures work in an empty project without old files or hidden helpers |
| Persistence | Restart retains database, vault key, registrations, owner binding, grants, participants, and coverage; only one scheduler uses the state |
| Password login | Incorrect/missing password fails closed; distributed attempt limits, exact Origin/CSRF, session rotation, expiry, sign-out, and password-revision invalidation work |
| Organizer experience | Ordinary website login and Connect Exness suffice; no CLI, setup URL, or token field; returning login reuses a valid saved grant |
| First-trader onboarding | A verified organizer with a valid empty AP allowlist can enable registration and the first trader can authorize; no personal organizer Trading grant or pre-discovered server is required |
| Privileged backend | Forged roles, hidden-control bypasses, obsolete bootstrap routes, and unauthenticated OAuth/management calls cannot acquire access |
| Authorization | Exact issuer/resource/callback, S256, one-use session-bound state, cancellation, parallel attempts, registration reuse, and sanitized callback redirect work |
| Local connection preflight | Actual Worker metadata and DCR succeed with the configured application User-Agent, JSON Accept header, and exact numeric-loopback callback; shell-only success is insufficient |
| Registration failure evidence | Rejected and uncertain registrations remain distinct; minimal encrypted response evidence survives validation failure; retries cannot overwrite a working identity or blindly duplicate an uncertain client |
| Browser login origins | Unexpected redirects are checked separately from API trust; blocked origins require the governing browser approval; account login and consent remain personal |
| Grant separation | Partner report uses owner authorization; account routing/limits/history use the selected trader's grant; wrong-role/audience credentials never reach another API |
| Access Point | No account read precedes discovery; account reads use the correct trusted AP; unapproved hosts and redirects receive no credentials |
| Registration and admission boundaries | Unknown trader APs keep the relevant application pending without blocking global registration; missing owner verification or malformed/broad trust configuration still prevents opening entries |
| AP trust recovery | Independent credential-free origin verification is followed by an exact configuration update and a protected retry of the saved application; original consent/grant/session ownership are preserved and every eligibility check reruns |
| Eligibility | Exact lossless account match, including later report pages, confirmed real boolean status, canonical USD, and complete checks are required |
| Incomplete data | Unknown fields, failed pages, permission errors, routing errors, and timeouts remain pending or delayed rather than falsely absent, approved, or zero |
| Renewal | At most one renewal/read replay, correct token rotation, shared locking, and late-write protection; permission denial never loops |
| Scoring | Exact close-only USD sums, all pages/windows, overlap/deduplication, correct start/end boundaries, negative/zero scores, and shared ranks |
| Coverage | Late-entry age limits and persisted gaps are honored; partial totals never become complete results or final winners |
| Scheduler | Two distinct refresh runs fetch relevant data and advance successful calculation time; browser polling is not mistaken for scheduling |
| Empty/backoff/failure | No participants means no Exness work; waiting does not extend rate-limit deadlines or freshness; failed publication preserves the last snapshot |
| UI | Readable desktop/mobile forms, accessible focus/labels, independent emblem, attractive CFD trophy/crowns, podium above full standings, coherent states and plain language |
| Privacy | Public responses, local files, platform logs, errors, and browser storage do not expose account numbers, passwords, tokens, cookies, verifiers, or callback secrets |
| Offline local preview | Mock storage/keys/cookies remain separate, Join works locally, and every external request is blocked; mock passwords never authorize the connected Production version |

Test admission races, duplicate accounts, owner rebind during checking, end reached during admission, rotating-token uncertainty, quota-bound history continuation, and database publication rollback where the implementation can encounter them. Do not write superficial checks that merely reproduce implementation wording.

Add connection regressions that simulate an HTML 403 for a generic runtime identifier and accept the configured application identifier across every OAuth and data operation. Verify required Content-Type and authorization headers survive the shared policy. Make the provider fixture reject an HTTP `localhost` callback and accept the exact numeric-loopback callback. Exercise cookie/CSRF and callback session binding at that canonical origin, plus safe handling of old local page links without forwarding credential-bearing requests or callback queries. Check that registration validation retains encrypted evidence and uncertain outcomes cannot trigger repeated DCR.

Add a complete first-trader regression starting with a verified organizer, a valid empty AP allowlist, and no participants. Confirm that the organizer can open registration and a trader can complete their own OAuth. An unapproved discovered origin must receive no credentials or account/history reads, leave the application unranked and pending, and appear only in protected sanitized diagnostics. After independent exact-origin approval, retry the saved application and require all referral, real/USD, identity, and history checks before admission. Verify that an empty allowlist cannot substitute for owner report verification and that malformed or wildcard trust settings still block opening entries. Check the actual organizer page: Verified connection remains visible, Open entries is enabled, and the empty allowlist alone produces no global setup warning.

Exercise the saved-entry retry itself, rather than only a freshly submitted form. Check the pending-to-checking transition under its lease, current management authorization and CSRF protection for operator-triggered requests, unchanged trader ownership, and complete eligibility checks. Unauthorized callers, paused or ended entries, an unapproved origin, and a non-USD or demo account must remain blocked. A successful retry must admit at most once, require no duplicate entry data or unnecessary OAuth, and leave scoring awaiting complete history. Keep a credential-free root HTTP 404 distinct from authenticated API verification in live evidence.

For visual-only changes, apply appropriate layout/accessibility/data checks rather than repeating unrelated live authorization. Updating documentation alone does not justify creating external resources.

Include a provider-shaped regression using the [verified limits/history contract](exness-api.md#verified-limits-and-history-payloads), rather than testing only invented flat fixtures. Exercise the saved pending application through AP recovery, day-based REST limits, admission, enveloped closed-deal scoring, and multiple history windows/pages. Make the provider fixture reject cursor requests containing initial range/limit parameters, and require exact echoed coverage, terminal empty-cursor handling, USD validation, and quota-window enforcement. Check that Retry checks displays progress and a persistent result, that success removes the admitted application from the pending queue, and that the same trader appears in public standings only with a complete score. Keep mocked passes distinct from an observed live recovery and later scheduled update.

## Live milestones

Treat each milestone as a separate claim:

Before the account milestones, record actual-runtime metadata verification, successful DCR for the exact callback, and browser login-origin approval separately. An authorization endpoint's redirect to a login page proves none of personal consent, token exchange, or a successful report read. See [Connection preflight and known failures](connection-preflight.md) for failure patterns and the browser approval boundary.

1. Local or public site/API works with the intended database and protected organizer web login.
2. Organizer OAuth exchanges successfully and actually reads the Partner client-account report; entry readiness follows the verified state.
3. A consenting trader completes personal OAuth, discovery and trusted AP access; exact referral membership and real USD eligibility lead to atomic admission.
4. Complete history produces a first published result, and a later actual scheduled event advances successful coverage/calculation time.
5. A real renewal is followed by a successful API read using the renewed access token.
6. At the end, complete final coverage is verified before results are announced as final.

For Cloudflare, also verify the intended account, dedicated bindings/resources, remote migrations, secrets, public callback, Static Assets routing, and deployed Cron. A local scheduled call or dry run is not remote evidence.

When no approved participants exist, verify only the no-participants scheduled path. Do not manufacture a successful calculation timestamp. When consent or a required contract is missing, finish independent implementation/checks and identify the exact next action without claiming live completion.

## Handover

Record project/runtime/dependency versions, commands actually implemented and run, event period, observed mocked/live results, and unresolved stages. Use clear evidence labels such as mocked pass, live pass, pending input, or failed. Keep credentials, real private identifiers, and callback queries out of the record.

For the Markdown skill itself, verify that every packaged file is Markdown, internal references resolve within the package, no code snippets or missing executable dependencies remain, and frontmatter meets the skill format. Do not report application tests as passed merely because these documentation checks passed.
