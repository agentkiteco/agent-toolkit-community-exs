# Exness Trading Challenge: Authorization

## Authorization contract

Use Authorization Code with PKCE S256 and Dynamic Client Registration for a public client using token endpoint authentication method none, as recorded for the Exness profile. Token exchange and refresh happen on the backend, never in browser code.

Configure and persist issuer, exact redirect URI, trusted metadata/API origins, resource, requested/registered/granted scopes, and refresh capabilities separately. Scope and audience are different restrictions. Do not infer audiences from the issuer or forward a token to another resource merely because the hostname matches.

The organizer requests Partnership read access; each trader requests Trading read access under a separate grant. Request no trading, payment, withdrawal, or broader fallback permissions. An organizer who also competes needs a separate personal Trading grant.

The organizer password controls management authority. Exness OAuth provides data access, not automatic website ownership or an assumed OpenID Connect identity. Do not invent userinfo endpoints, ID tokens, email identity, or JWT claims that the provider contract does not establish.

## Metadata and registration

Read trusted authorization-server metadata and require exact issuer, approved endpoint origins, Authorization Code, and S256 support. A returned URL does not expand trust. Consult [authorization-server metadata](https://www.rfc-editor.org/rfc/rfc8414.html) and [Dynamic Client Registration](https://www.rfc-editor.org/rfc/rfc7591.html) when implementing the protocol.

Register the application's actual callback and its supported code/refresh grants. For the recorded Production profile, omit scope during DCR and request the role's read scope during authorization. Do not invent offline access permission.

For local HTTP operation, use the canonical numeric loopback origin `http://127.0.0.1` with the selected port, followed by `/callback`. Keep it identical in DCR, authorization, code exchange, browser entry, and server configuration. A `localhost` callback was rejected with `invalid_redirect_uri` in the recorded Production integration. Follow [Connection preflight](connection-preflight.md) before registering a client; a metadata read alone does not test redirect acceptance.

Validate the returned client identity, callback, and public-client method. Reuse a registration bound to issuer, redirect URIs, and relevant client metadata across users and restarts. Use a shared lock for concurrent initialization. An ambiguous timeout does not justify blind duplicate registration.

Retain encrypted minimal registration evidence before validation can fail, including any returned client identity, callback/method evidence, HTTP status, and allowlisted error category. Separate confirmed rejection from an uncertain registration outcome. Correct a rejected callback without discarding the vault, password verifier, database, or existing grants. Preserve incomplete records for guarded operator recovery instead of silently creating another client on every retry.

Store any registration-management token as a separate secret. Unexpected confidential-client requirements need a deliberately supported backend contract, never a secret embedded in the browser. Narrow compatibility handling for known numeric-string timestamps is acceptable without re-registering.

## Login attempts and callback

Create independent random state and PKCE verifier/challenge values for every attempt, following [PKCE](https://www.rfc-editor.org/rfc/rfc7636.html). Bind each attempt to its opaque pre-auth session, contest, action/role, issuer/client, callback, resource/scopes, creation time, and organizer password-session authority where relevant. Give attempts short expiry and keep parallel tabs independent.

The authorization redirect includes the saved client/callback, code response type, role scope, resource, state, and S256 challenge. The owner of the Exness account personally completes provider login and consent.

Provider login may redirect the browser to a separate origin. Verify unexpected destinations and honor browser approval requirements as described in [Connection preflight](connection-preflight.md). A redirect from the trusted authorization endpoint does not approve a blocked browser destination or expand API/Bearer trust. Do not forward backend credentials to a browser login host or complete the owner's consent on their behalf.

The callback validates session binding, unique parameters, expected issuer, state equality/expiry, and single use before exchanging a code. Check a returned issuer parameter when the contract provides it. Cancellation never creates membership. Atomically consume a valid attempt and use its saved parameters rather than changed frontend settings.

Exchange the code through a form-encoded server request containing the original client, redirect URI, verifier, resource, and returned code. Public-client method none uses no Basic authentication or client secret. Do not replay an ambiguously completed exchange.

Validate response status, absence of OAuth error, nonempty access token, Bearer type, and any returned scopes/refresh credential. Persist receipt time and calculate expiry from the actual lifetime; absent lifetime is unknown, not permanent. Preserve issuer, resource, and role in grant context.

After callback, redirect to an ordinary same-origin page without sensitive query parameters. Disable callback caching and third-party analytics/assets. Do not support arbitrary return destinations.

## Sessions and storage

Use opaque server sessions and challenge/deployment-scoped cookies with HttpOnly, Secure, SameSite Lax, and no Domain. Lax permits the top-level GET callback to retain session binding. Require exact Origin and CSRF protection for mutations; callbacks use their own state, PKCE, issuer, and single-use checks.

Encrypt access/refresh tokens and temporary verifiers with authenticated encryption, unique nonces, and contest/role/grant context. Keep the vault key outside D1. Never return saved tokens through status APIs or put credentials in browser storage, source, chat, logs, reflected errors, or captured callback URLs.

Use finite timeouts and reject automatic redirects on credential-bearing DCR, token, and API requests. The browser's verified authorization redirect is a different operation. Send Bearer only to explicitly approved HTTPS destinations for the grant and API contract.

Apply the configured application User-Agent and JSON Accept header to metadata, DCR, code exchange, and refresh through the same request policy used for data reads. Keep form-encoded token requests and JSON registration requests intact when adding these headers.

Logout ends a browser session and its unfinished attempts, while consented background grants remain. Explicit disconnection disables the relevant grant and prevents future refresh. Use provider revocation only under a confirmed contract; local disconnection does not prove provider-side revocation.

## Refresh and concurrency

Refresh shortly before known expiry or once after an API unauthorized response. With unknown lifetime, rely on the server response. If renewal is unavailable or permanently rejected, reconnect only the affected grant's owner, not all participants.

Use the original token endpoint, client identity, resource, and current refresh token in a form-encoded request. Do not repeat DCR, include code/verifier/state, or widen scope. Retain a previous refresh token if the valid response omits a replacement; reject an empty or malformed replacement. Preserve scopes when omitted and treat absent new lifetime as unknown.

Coordinate renewal across web requests, callback, and Cron with a shared database lock and generation checks. Reread current credentials under the lock and reuse another completed renewal. Atomically persist token rotation. Late responses cannot restore a disconnected grant or overwrite a newer authorization.

Limit each operation to one renewal and one safe read replay. API permission denial does not start a refresh loop. Permanent invalid-grant or unsupported-refresh errors stop the affected automatic flow. Temporary network failure, rate limit, or server error preserves credentials/results with bounded backoff. An ambiguous rotating-token timeout must not trigger blind token reuse.

Normal rotation is not a new owner or authorization. A changed issuer/resource/scope or confirmed permission loss requires renewed readiness checks. Follow the [OAuth Security Best Current Practice](https://www.rfc-editor.org/rfc/rfc9700.html) and verify renewal with an actual subsequent API read.
