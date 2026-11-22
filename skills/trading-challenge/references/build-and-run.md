# Exness Trading Challenge: Build and run

## Project boundary

Create application code in a new project directory, not inside the skill. This edition includes no starter or generator. Do not depend on a previous project, another edition, hidden files, saved curl requests, or another conversation to complete the build.

For a new implementation, use one Worker for the public website and same-origin backend, Static Assets for local images/styles/pages, and dedicated D1 storage. Provide a server-side scheduled handler and a local runtime capable of exercising Workers APIs, encryption, D1, and background updates.

Choose supported dependencies, pin their versions, and create a lockfile. Establish documented procedures for installing, building, running, checking, and deploying the application. Do not refer users to commands or helpers that have not actually been implemented.

## Configuration and dates

Keep event identity, display name, UTC start/end, IANA timezone, optional prize, public origin, Production OAuth issuer, exact callback, role resources/scopes, API origins, and approved Access Points in explicit configuration. Separate these settings from credentials and from the normal product interface.

Resolve calendar dates before implementation. A period through the last day of a month ends at midnight on the following day in the organizer's timezone. For a calendar month, use the same local time on the corresponding day next month, clamped to that month's last day, with DST. Ask about genuinely ambiguous or nonexistent local times rather than guessing.

Render event details consistently from configuration. Omit unspecified prizes and descriptions. Never carry old event branding or hard-coded dates into a new contest.

## Backend responsibilities

Implement opaque server sessions, organizer password verification, separate role grants, OAuth attempts and refresh, account admission, history coverage, exact scoring, and coherent leaderboard snapshots. The browser never directly owns Exness tokens or decides account eligibility.

Persist minimal records for sessions, password-session revision, reusable DCR registrations, encrypted grants and attempts, owner binding/readiness, applications and participants, deal identity or verified aggregates, coverage/progress, results, leases, rate budgets, and sanitized operational outcomes. Use parameterized queries, appropriate uniqueness constraints, and migrations.

Protect organizer APIs independently of the frontend. Keep private responses uncached. Public responses expose only contest details and allowlisted display-name/rank/profit/status/freshness fields.

## Local operation

Use a local Workers-compatible runtime with persistent local D1 and privately stored vault/password-verifier material. Run a server-side minute timer that invokes the same refresh behavior as the deployed scheduled handler. Browser polling only reads results.

Choose an unused port and use `127.0.0.1` as the canonical local hostname, with the exact origin followed by `/callback` as the redirect URI. The recorded Production DCR rejected an HTTP `localhost` callback with `invalid_redirect_uri` and accepted the numeric loopback form. Localhost and the numeric loopback host, different ports, and different callback paths are not interchangeable. Align the bind address, public origin, browser entry point, private password-delivery URL, scheduler target, and Origin checks. Use the same Exness Production APIs as the published version. Isolate cookies and storage by contest, local or Cloudflare deployment, and any offline local preview.

Keep local secrets in excluded, private storage with restrictive permissions. Preserve the database and vault key together. Ordinary restart retains registrations, owner binding, grants, participants, and coverage. Do not open the same persistent database concurrently from a second runtime for diagnostics.

The organizer opens the ordinary organizer page and signs in with a password. The deployment operator prepares the verifier privately; this is not an organizer terminal task. Never restore a launcher or setup-token flow after cookie loss.

## Network diagnosis

Check the local page/API/scheduler separately from Exness connectivity. From the backend's actual network, verify public issuer metadata with finite timeout and normal TLS verification. Browser access does not establish backend DNS or certificate trust.

Follow [Connection preflight and known failures](connection-preflight.md). Set a stable, contest-specific application User-Agent and request JSON through a shared backend transport policy. Apply it to every OAuth and data operation, including refresh and Cron. The local Worker's default identifier previously received HTML 403 while an explicit application identifier received JSON; a shell success alone did not expose that runtime difference.

Distinguish DNS resolution, routing/timeouts, TLS trust, metadata, registration, code exchange, token renewal, and API reads. Verify access to the configured Production endpoints from the actual backend runtime. Use normal system certificate trust and preserve TLS verification.

Complete actual-runtime metadata and DCR checks before presenting the connection as ready for personal consent. Identify `invalid_redirect_uri` as a callback configuration failure, and identify a blocked browser sign-in origin separately from a failed backend request. Preserve storage and secrets while correcting origins or request headers.

Preserve grants on temporary failures. Log only sanitized stage/status/outcome and approved origins without query or account data. Do not repeat ambiguously completed registration, code exchange, or rotating-token renewal blindly.

## Optional local preview

Implement an offline local preview only when requested. Use a separate namespace, database, encryption key, sessions, cookies, synthetic grants, and locally generated API responses. Unexpected external requests must fail; there is no fallback to real Exness.

Match the requested presentation. The established local preview presents a connected synthetic organizer, open entries, and a populated podium/table; its connection and Join interactions still work locally. Keep each synthetic participant's total PnL between minus 1000 and plus 5000 USD. Do not apply these bounds to real scoring. Do not add a PnL line chart unless requested.

The earlier presentation omitted a visible preview badge. Treat that as a presentation choice, not permission to mix mocked and real data or portray synthetic trading as genuine public results. A preview-only password cannot authenticate the connected Production version, and switching modes never transfers grants or participants.
