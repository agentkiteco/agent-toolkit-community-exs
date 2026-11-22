# Exness Trading Challenge: Production APIs

## Production integration profile

Exness Production is the only upstream for connected local and Cloudflare versions. Local execution uses the same Production issuer, audiences, and API hosts; only the application origin, callback, and storage are local.

Use the following Production integration profile and recheck current metadata and actual reads during acceptance. Provider contracts can change; configuration alone does not prove that a particular account or deployment works.

| Purpose | Profile value |
| --- | --- |
| OAuth issuer, Partnership origin, Trading gateway | https://api.exness.com |
| Authorization-server metadata | https://api.exness.com/.well-known/oauth-authorization-server |
| Authorization endpoint | /oauth2/authorize on the issuer |
| Registration endpoint | /oauth2/register on the issuer |
| Token endpoint | /oauth2/token on the issuer |
| Organizer scope | partnership.all:read |
| Organizer resource | https://api.exness.com/v1/partnership/reports/clients/accounts |
| Trader scope | trading.all:read |
| Trader resource | https://api.exness.com/v1/trading/access-point |
| Callback | The exact application origin followed by /callback; use numeric `127.0.0.1` with the selected port locally, and the actual public HTTPS origin after deployment |

Metadata advertised code flow, refresh grant, S256, public-client method none, and query callback. DCR omitted scope; authorization requested the role's scope. These resource URIs are confirmed settings for these APIs, not a rule for deriving other audiences from endpoint paths.

Use direct, read-only HTTP requests with OAuth Bearer authentication and JSON responses. Public documentation may show signed API-key examples; retain OAuth rather than adding EXN signatures or key forms.

## Request identification

Configure a stable, truthful application User-Agent and `Accept: application/json` for all backend Exness requests. Use a shared request policy for metadata, DCR, code exchange, refresh, Partnership reports, AP discovery, account details, limits, and history. Preserve each request's method, Content-Type, and role-specific authorization. Do not depend on the runtime's generic User-Agent or add the header only to a metadata probe.

A generic Worker identifier can receive HTML 403 even when a shell request succeeds. Configure the current application's own truthful identity and JSON content negotiation, then verify from the actual backend runtime. Follow [Connection preflight and known failures](connection-preflight.md); a Node or curl success is not evidence that the Worker succeeds.

## Role-specific operations

| Operation | Destination and grant |
| --- | --- |
| Client-account report | The configured Partnership origin at /v1/partnership/reports/clients/accounts, using the organizer's grant and complete limit/offset pagination; no Access Point |
| Trading route discovery | The configured gateway at /v1/trading/access-point, with the selected account_id query and that trader's grant |
| Account details | The approved discovered AP at /v1/configuration/accounts/{account_id}/account, with the same trader grant |
| Account limits | That AP at /v1/configuration/accounts/{account_id}/limits, with the same trader grant |
| Deal history | That AP at /v1/history/accounts/{account_id}/deals, with the same trader grant and complete permitted pagination/windows |

Never send account-scoped reads to the general gateway as fallback. Never use organizer credentials for Trading or trader credentials for the report. Cache validated routing by grant, authorization version, and exact account; use a finite lifetime and rediscover on invalid/stale routing. A fifteen-minute route-cache lifetime was a prior implementation policy, not OAuth lifetime or a provider guarantee.

The [AP discovery](https://www.exness-api.com/trading/get-started/access-point-host-discovery), [account details](https://www.exness-api.com/reference/trading/get-account-details), [client-account report](https://www.exness-api.com/reference/partnership/list-report-client-accounts), [history](https://www.exness-api.com/reference/trading/get-deals-history), and [limits](https://www.exness-api.com/trading/guides/api-configuration-and-limits) documentation describe the relevant routes/data. Signed-auth examples do not independently establish OAuth support.

## Trust before forwarding credentials

Obtain the AP from a successful authenticated gateway response for the selected account, checking its echoed account identifier when present. A supplied arbitrary URL is not discovery evidence. Require a valid HTTPS root origin with no userinfo, query, fragment, unexpected path, or port.

Approve only an exact verified API origin before transmitting a token. The known Production AP namespace was ap-prefixed hosts under exness.com; verify provider ownership and normal TLS trust without credentials. Do not treat the namespace as a wildcard allowlist or copy a prior trader's host. An unfamiliar host requires a separately verified provider contract.

A successful discovery response does not expand trust automatically. If a newly discovered origin is unapproved, leave the application pending, expose only sanitized configuration diagnostics, verify the origin, update the explicit allowlist, then restart or redeploy and retry. Preserve existing grants and encryption keys. Browser provider-login redirects do not add destinations to the server's Bearer allowlist.

Carry this operator workflow through to a retry of the saved consented application once the exact origin is verified. Use normal DNS/TLS checks without credentials and retain minimal verification evidence. HTTP 404 at an unauthenticated server root does not establish an account-read failure or account permissions. See [Completing access_point_unapproved](connection-preflight.md) for the full recovery procedure, including preservation of the original grant and session ownership.

An empty valid AP allowlist permits initial trader OAuth and registration after organizer readiness is established. Enforce exact AP approval at the individual account-read and admission boundary. Do not require a known trader server before its owner can connect; see [Entry readiness](challenge-rules.md).

Unauthenticated root/discovery probes can establish network or route behavior, not the permissions of a live OAuth token. Do not forward Bearer as an unapproved-host probe or disable TLS.

## Exact account fields

Treat account identifiers as canonical positive unsigned 64-bit decimal strings and parse numeric JSON losslessly. Do not use floating-point conversion or remove ambiguous leading zeros. Trading identifies account_id; the Partner report matches client_account. Client UID, partner UID, and partner account are not replacements for that trading-account match.

The confirmed Production account response had string account_id, boolean is_demo set to false, and USD in settings.currency. A present canonical nested currency of null, EUR, or an unknown value cannot fall back to a conflicting flat USD alias. Legacy aliases are acceptable only when the canonical field is absent and the adapter contract supports them.

Missing real-status evidence, string false, numeric zero, trade mode, or account status cannot establish that the account is real. A successful token or discovery response cannot establish account eligibility by itself.

## Verified limits and history payloads

Use the following Production payload structure when implementing adapters, and verify compatibility through consented reads in the current application. Account identifiers, AP origins, grants, and storage remain specific to each event.

| Purpose | Confirmed response fields |
| --- | --- |
| Global REST quota | `limits.rest.global_account_rate.limit` and `window_seconds` |
| Operation profiles | `limits.rest.methods`, identified by `api_operation_id`, `http_method`, and exact templated `path` |
| Closed-deal history limits | The GET `getDealsHistory` operation for `/v1/history/accounts/{account_id}/deals`, with `limits.history_range_days` and `limits.history_age_days` |
| Per-operation quota | Each relevant method's `rate_limit.limit` and `window_seconds`; include account details, limits, and history reads |
| History items | `items` contains envelopes with `event_time` and nested `deal`; use `deal.deal_id`, `deal.type`, and `deal.profit.amount`/`currency` |
| Page evidence | `has_more`, `next_cursor`, and echoed `range.from`/`range.to` |

Convert explicit day units correctly and enforce the advertised quota windows. The flat fields `history.max_range_seconds` and `rate_limits.requests_per_minute` used by an early fixture were not this Production response. Supporting a fixture adapter does not establish live compatibility. Preserve numeric values losslessly through parsing and normalization.

The initial history request uses `from`, `to`, and a supported `limit`. A continuation request sends **only `cursor`**. Repeating the initial range or limit alongside the cursor produced HTTP 400 with an invalid-request response; the same saved cursor succeeded alone and returned matching range evidence. Keep the original window in backend progress, validate every echoed range against it, and never decode or alter the opaque cursor. A terminal page may return an empty `next_cursor`; `has_more: true` without a usable cursor remains incomplete.

Use the envelope's `event_time` for interval checks and the nested deal for identity and profit. Skip non-close deals before requiring profit currency; an open deal's missing currency must not reject otherwise valid closed-deal history. Closed deals still require verified USD and exact arithmetic. Unknown shapes remain pending or delayed; inspect only protected, sanitized field names/types and error classifications before updating the adapter.

## Failure classification

| Observation | Required behavior |
| --- | --- |
| Unapproved AP origin | Keep the application pending; verify the exact discovered origin without credentials, configure that origin, then rerun the saved application through all checks; no premature credential forwarding or grant deletion |
| JSON API permission denial | Check scope, audience, and account access; no refresh loop or weaker admission |
| HTML edge-protection denial | Recoverable upstream blockage, not proof of OAuth revocation; preserve grants and the pending application |
| Metadata works in a shell but the Worker receives HTML 403 | Check the shared application User-Agent and JSON Accept header in the actual runtime; do not assume DNS failure or weaken TLS |
| DCR returns `invalid_redirect_uri` | Correct the exact configured callback, using numeric loopback locally; preserve registration evidence and existing storage |
| Browser review rejects a separate login origin | Stop the browser action and resolve the required approval; backend connectivity and browser-origin approval are separate checks |
| Discovery server error or routing-context failure | Stop before account/history reads, retain credentials, and retry after the routing/API issue is resolved |
| Unauthorized API response | At most one eligible refresh and safe read replay; an expired saved token is not evidence about fresh access |
| Network, TLS, rate limit, or server outage | Separate diagnosis and bounded backoff; preserve the last complete result and its timestamp |

Log only stage/outcome, sanitized status/response kind, and an exact AP origin when needed. Never log accounts, tokens, cookies, callback queries, or raw private error bodies.
