# Exness Trading Challenge: Cloudflare deployment

This is deployment-operator guidance, not an organizer workflow. Publish only when the user requests it. A request to edit or use the skill does not by itself authorize publishing the current application.

Use one Worker for the website and same-origin backend, Static Assets for public files, a dedicated D1 database for encrypted grants and contest state, Worker secrets for sensitive configuration, and Cron for autonomous refresh. There is no Google runtime dependency.

## Prepare a reviewable deployment

Implement the application and migrations in a separate project, pin dependencies and a project-local Wrangler version, and retain the lockfile. Verify the selected version against current [Wrangler installation guidance](https://developers.cloudflare.com/workers/wrangler/install-and-update/) and [configuration documentation](https://developers.cloudflare.com/workers/wrangler/configuration/). This Markdown package does not contain a deploy configuration to copy.

Complete local behavioral checks first. Choose a stable Worker name and dedicated database name. Use the authorized Cloudflare account and verify its identity with Wrangler before creating resources. Reuse existing authorization; if browser login is needed, the account owner completes it without sharing passwords or tokens in chat. Clarify genuinely ambiguous account selection before mutations.

Updating an existing contest preserves its resource identity, database, encryption key, owner binding, registrations, grants, participants, and history coverage. Do not create a replacement database or import another event's state as a routine redeployment.

## Origin, runtime, and bindings

Resolve the actual public HTTPS origin before users authorize. Compile/configure that exact origin and its callback path. Do not deploy a backend that still trusts only loopback or reuse a localhost OAuth registration for the published callback. A changed final hostname requires consistent origin/callback configuration and rebuild before authorization.

Choose and record a supported compatibility date. Preserve it on routine redeployments; changing runtime behavior requires validation. Add Node compatibility only when required by selected dependencies, rather than automatically.

Provide the database binding expected by the backend and an ASSETS binding for public files. Configure Worker-first routing so API, callback, password-session checks, and security headers cannot be skipped by automatic asset serving.

Avoid an organizer redirect loop caused by automatic HTML extension handling. One suitable design disables automatic HTML handling, explicitly maps the public root to its index asset and the organizer route to its organizer asset, and leaves unknown API/callback routes as genuine errors. Verify this behavior in the actual runtime. Refer to [Worker-first routing](https://developers.cloudflare.com/workers/static-assets/routing/worker-script/) and [HTML handling](https://developers.cloudflare.com/workers/static-assets/routing/advanced/html-handling/).

Keep Production deployments free of local-preview bindings, synthetic clocks, mock transport, and stale issuer/API overrides. Maintain exact approved API origins; newly discovered APs still undergo verification before allowlist updates and credential forwarding.

## Database and secrets

Create a dedicated remote D1 in the confirmed account and bind its actual identifier. List and apply pending remote migrations through Wrangler, targeting the intended database. Migration state and schema must match the application; do not reset tables or lose existing ciphertext. Follow [D1 operations](https://developers.cloudflare.com/d1/wrangler-commands/) and [migration tracking](https://developers.cloudflare.com/d1/reference/migrations/).

Store the vault encryption key and organizer password verifier as separate Worker secrets. Neither belongs in ordinary variables, public assets, tracked files, command arguments, or chat. Use an authorized private input or secret-manager workflow. Generate or validate a secret completely before invoking its uploader so cancellation cannot replace an existing value with empty input.

A new empty deployment needs a fresh cryptographic vault key. A redeployment over existing encrypted data retains the existing key unless a deliberate migration handles rotation. Password rotation is separate and invalidates management sessions without deleting consented trading grants. Follow [Worker secret management](https://developers.cloudflare.com/workers/configuration/secrets/).

The organizer receives the contest password privately and uses only the web sign-in page. Do not add remote bootstrap SQL, setup fragments, first-visitor ownership, or a local launcher to compensate for missing password configuration.

## Build, dry run, and publish

Run the implemented build/check procedures, verify public OAuth metadata from Exness Production, and perform Wrangler's deployment dry run. Inspect the bundle, assets, bindings, runtime settings, callback configuration, and absence of accidental local-preview or validation overrides before publication.

A dry run is packaging evidence only. It does not establish remote database access, configured secrets, deployed Cron, Exness authorization, or live results. Deploy the reviewed project through the pinned Wrangler within the user's requested scope. A secret operation that creates a stub or new version is not by itself an operational contest.

Use server-side DCR tied to the published issuer/callback. The organizer completes password sign-in and own Partner OAuth; traders complete separate personal Trading OAuth. Password success does not open an unverified initial contest.

## Observe and verify

Verify the public page, assets, public API, organizer password gating/sign-out, protected management APIs, exact callback, D1 operations, and end-boundary admission behavior. Confirm that API/callback requests are not swallowed by static or SPA fallbacks.

Configure a once-per-minute UTC Cron and observe an actual remote scheduled event, allowing normal propagation time. Scheduled operation must be independent of the organizer's browser/computer. Follow [Cron configuration](https://developers.cloudflare.com/workers/configuration/cron-triggers/).

Use sanitized operational logs through Wrangler or Cloudflare observability. Disable invocation URL capture where it would retain callback query secrets and avoid unfiltered request-event output containing cookies or headers. Inspect only the fields needed for diagnosis; application log sanitization alone does not sanitize platform request metadata. See [Workers logging controls](https://developers.cloudflare.com/workers/observability/logs/workers-logs/).

With no approved participants, prove a no-participants outcome without Exness calls or a fabricated calculation time. Report infrastructure/Cron readiness while live calculation remains pending. With a consenting participant, verify exact referral membership, trader discovery/AP reads, real USD status, complete history, first result, and a later scheduled snapshot advancing successful calculation time. Renewal also needs a successful read using the new access token.

Deliver the public and organizer URLs, resolved period/timezone, entry readiness, actual scheduled evidence, and specific pending consent/routing/history/quota limitations. The organizer handover contains website actions, not developer tooling.
