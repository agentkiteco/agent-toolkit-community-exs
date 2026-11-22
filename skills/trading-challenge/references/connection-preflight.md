# Exness Trading Challenge: Connection preflight and known failures

Apply this procedure before handing over Connect Exness as ready for personal login. These are integration instructions, not permission to approve the organizer's or a trader's consent. Updating this Markdown skill alone does not authorize a live connection or registration.

## Failure patterns and recovery

Use these failure patterns to diagnose the current implementation. Verify the actual runtime, configuration, and provider responses rather than assuming that a correction establishes a completed account connection.

| Stage | Failure pattern | Correction or boundary |
| --- | --- | --- |
| Public issuer metadata | The Worker receives HTML 403 with its generic identifier while shell requests receive JSON | Set a truthful application-specific User-Agent and JSON Accept header, then recheck metadata from the Worker |
| Dynamic Client Registration | An HTTP `localhost` callback receives `invalid_redirect_uri` | Use the exact numeric loopback origin with `127.0.0.1`, the selected port, `/callback`, and public-client method `none`; verify registration acceptance |
| Browser authorization | The trusted authorization endpoint redirects to a separate browser sign-in origin | Inspect the destination origin without following it or sending credentials; a provider redirect does not replace browser approval |
| Entry readiness | A verified organizer sees a warning and disabled Open entries solely because the AP allowlist is empty | Accept a valid empty allowlist; discover and independently verify each account's exact server after trader authorization |
| First trader's server | Authenticated discovery leaves a saved entry pending with `access_point_unapproved` | Independently verify and configure the exact discovered server, then retry the saved application through all checks; verify admission and scheduled scoring separately |
| Eligibility retry | Server approval exposes `limits_contract_unconfirmed` because the adapter expects flat fixture fields | Read the Production `limits.rest` operation profiles and their day-based history constraints; rerun the saved application without replacing consent or bypassing eligibility |
| First score | `history_contract_unconfirmed` because items are treated as flat deals | Read the `event_time`/`deal` envelope described in [the API contract](exness-api.md#verified-limits-and-history-payloads) |
| History continuation | The first history page works but continuation requests return HTTP 400 | Send only the saved cursor on continuation, retain the original window, and validate echoed coverage before publication |

For each new contest, configure a truthful application name and version belonging to that contest. Do not copy another event's identity, port, registration, or credentials.

## Preflight sequence

1. Choose a free local port before preparing origin-dependent settings or registering an OAuth client. Use `http://127.0.0.1` with the chosen port as the single local application origin. Derive `/callback` from that exact origin. Use the actual public HTTPS origin for Cloudflare.
2. Align the bind address, public origin, browser links, password delivery file, scheduler target, Origin checks, and OAuth redirect URI. Keep origin configuration explicit and consistent. Test the website's real cookie and CSRF behavior at the numeric address.
3. Use one backend request policy that sets a stable application `User-Agent` and `Accept: application/json` for every Exness request. Cover metadata, registration, code exchange, token renewal, Partnership reports, AP discovery, account details, limits, and history, including scheduled reads. Preserve each operation's required Content-Type, role, resource, and Bearer header.
4. Verify the issuer metadata from the actual Worker network with normal TLS verification, a finite timeout, and exact issuer/endpoint checks. A successful operator-side shell request is a comparison signal, not proof of Worker connectivity. For an HTML 403, check the application's request identification before assuming DNS failure, provider downtime, or revoked consent. Use an honest application identifier; do not impersonate a browser or disable transport protections.
5. Register and validate the exact callback with method `none`, code/refresh grants, and no DCR scope as specified in [Authorization](authorization.md). Record metadata success and registration success separately. A known `invalid_redirect_uri` is a registration configuration rejection, not an inability to reach Exness. Correct the callback and its application origin before another registration attempt.
6. Start the ordinary website Connect flow. Check browser login redirects under the rules below. The account owner completes personal sign-in and read-only consent. After callback, verify the actual token exchange and role-specific API read before claiming connected readiness.

Do not report the contest as live merely because metadata and registration succeed. Owner report verification, trader eligibility, complete results, scheduling, and renewal remain separate acceptance milestones.

After a successful owner report read, distinguish registration readiness from individual account approval. Enable the organizer's entry control with a valid API profile even when its AP allowlist is empty. Keep server trust and eligibility checks on each application, as specified in [Contest rules](challenge-rules.md). A pending trader server must not invalidate a verified organizer connection or prevent the first trader from starting authorization.

## Completing access_point_unapproved

This state means that discovery reached the exact-server trust boundary. It does not by itself mean the trader's authorization failed or the account is ineligible. Complete the following operator workflow when that work is authorized; avoid handing back only a generic request to contact an operator when the agent can perform the verification itself.

1. Read the saved application's sanitized discovery evidence through protected diagnostics. Correlate the candidate with the selected account and its personal Trading grant on the backend. Keep account numbers, grants, cookies, and raw private responses out of chat and logs. Retain the original nickname, consent, authorization, and application identity.
2. Validate the discovered URL as an exact HTTPS root origin with no userinfo, query, fragment, unexpected path, or port. Independently check provider ownership under the confirmed API contract, public DNS, and normal TLS certificate/hostname validation without credentials. A domain suffix or discovery response alone does not grant trust. An unfamiliar namespace needs separately verified provider evidence.
3. An unauthenticated root probe can legitimately return HTTP 404 because the root is not an API operation. That response does not prove account permissions and must not be mistaken for failed account authorization. Never add Bearer headers, provider cookies, registration credentials, or private account parameters to the verification probe, follow an unapproved redirect, or disable TLS validation.
4. After verification, add only that exact origin to the current event's approved AP configuration and reload or redeploy within the authorized scope. Preserve the database, vault, password, grants, and registrations. Do not approve a wildcard, a browser-login domain, or a host copied from another contest. New contests discover and verify their own routes.
5. Retry the saved application using its existing consent and valid trader grant. Use the same admission checker as the normal entry journey. Under its shared application lease, move a pending application back into checking before the conditional admission commit. Recheck current entry/end state, owner authorization and referral membership, trader authorization, exact routing, real/USD identity, history constraints, account uniqueness, and authorization/configuration versions. A protected operator retry may trigger these checks; it must never set admitted status directly or bypass a failed check.
6. Preserve the original trader session binding. Operator recovery does not transfer the entry into the operator's current browser session. Require renewed personal OAuth only when the affected grant actually needs it. A temporary trust-configuration issue does not justify making the trader re-enter the account, nickname, or consent, or reconnect an otherwise valid authorization.
7. Confirm admission separately from scoring. Publish no profit until complete eligible history is verified, then observe actual server-scheduled refreshes. Browser polling only reads snapshots. Record the trusted-origin check, successful account reads, admission, first complete result, and later calculation time as separate evidence.

If ownership, TLS, routing, consent, or eligibility cannot be verified, preserve the application and state the specific unresolved step. The organizer and trader continue to use the ordinary website; operator configuration is kept outside their normal forms.

When an organizer says the approval button does not work, inspect the protected saved outcome and request status first. Repeating a retry cannot resolve unapproved AP trust or an incompatible payload adapter. Complete the authorized operator recovery, then rerun all checks on the same saved application. Name the control Retry checks rather than implying discretionary admission; show Checking while it runs and keep success or failure visible afterward instead of relying only on a disappearing toast. Admission, first complete score, and subsequent scheduled freshness are separate observations.

## Registration evidence and recovery

Preserve minimal returned client identity, callback/method evidence, HTTP status, response kind, and an allowlisted OAuth error category before completing registration validation. Encrypt registration credentials and any retained sensitive response fields on the backend. Status APIs and logs expose only sanitized diagnostics; never print registration-management tokens, client secrets, raw private responses, or authorization URLs containing query parameters.

Distinguish a confirmed rejection from an uncertain outcome. A confirmed HTTP 400 with `invalid_redirect_uri` requires a callback correction. A timeout, lost response, or incomplete identity is not permission to blindly repeat registration. Reuse a validated saved registration when issuer, callback, and client metadata still match. Preserve uncertain records for operator review.

For an old implementation that saved an unfinished registration without enough evidence, recovery is an explicit operator action with current management authorization and a shared registration lock. Retain the old record, check that recovery cannot replace a working registration or grant, and retain encrypted evidence from the replacement attempt. Do not add a public reset route or make repeated client creation the normal retry mechanism. The organizer continues to use the ordinary website.

Changing from `localhost` to `127.0.0.1` changes the application origin and registration binding. Preserve the database, vault key, password verifier, grants, participants, and history. Begin a fresh website session and OAuth attempt at the canonical address as needed. Do not copy authentication cookies between hosts, relax Origin/CSRF checks, or reset storage to recover access. Old page links may redirect to the canonical local origin; credential-bearing POSTs and callback secrets must not be forwarded through such a redirect.

## Browser login redirect verification

Keep a record of browser login origins separately from the exact API/Bearer allowlist. A browser sign-in destination is not automatically trusted merely because the provider redirected there. Never add it to AP trust or send it API tokens, registration credentials, or a saved provider session through a backend probe.

When a login redirect is unexpected, first inspect only the redirect status and destination origin returned by the trusted authorization endpoint, using normal TLS and manual redirect handling. Do not follow the destination during that check. Avoid logging the full authorization URL, state, callback parameters, cookies, or codes. Record any remaining ownership or browser-approval uncertainty explicitly.

If browser security or automatic approval review rejects the destination, stop that browser action and explain the blocked origin and stated risk. Obtain the approval required by the governing browser policy before continuing. A first-party redirect is evidence to present during review; it does not override the gate. Do not use another browser surface, raw browser commands, or an HTTP client to perform the blocked login indirectly. Leave personal credentials and consent to the account owner.
