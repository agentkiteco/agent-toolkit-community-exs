---
name: trading-challenge
description: Build or update an Exness Trading Challenge from a self-contained Markdown specification. Includes organizer web password login, separate organizer and trader OAuth, direct Production APIs, verified USD rankings, championship design, local execution, and requested Cloudflare deployment through Wrangler.
---

# Trading Challenge

Create a working CFD trading competition with a password-protected organizer website, separate Exness OAuth for the organizer and every trader, verified account eligibility, exact closed-trade profit rankings, and autonomous result updates. Use a dark design with yellow accents, an attractive trophy, crowns, and a top-three podium above the full standings.

This package contains Markdown descriptions only. It has no application code, scripts, configuration templates, assets, or dependencies on another skill or starter. When asked to build a contest, implement and test the application in a separate project using these specifications. Do not require the code-based edition, previous projects, other chats, or saved credentials.

## Read the relevant specifications

- For a new implementation or local operation, read [Build and run](references/build-and-run.md).
- Before implementing or troubleshooting Connect Exness, read [Connection preflight and known failures](references/connection-preflight.md). Configure an explicit application User-Agent and the numeric local callback before making connection claims.
- Before implementing organizer access, read [Organizer web login](references/organizer-access.md). The organizer uses the website, never a CLI or setup link.
- For authorization, sessions, and renewal, read [Authorization for both roles](references/authorization.md).
- Before implementing data adapters, read [Exness Production APIs and routing](references/exness-api.md), including the verified REST limits, enveloped deals, and cursor-only continuation contract. Do not mistake guessed fixture fields for the Production response shape.
- Before admission, scoring, or scheduling, read [Contest rules](references/challenge-rules.md).
- For public pages and the organizer dashboard, read [Design and language](references/design.md).
- When publication is requested, read [Cloudflare deployment with Wrangler](references/cloudflare-deployment.md).
- Before claiming completion, follow [Acceptance and evidence](references/validation.md).

## Scope and event decisions

Building, updating this skill, running locally, and publishing are separate requests. Publish only when requested. Preserve the existing application and competition rules when the user asks for a limited modification.

Use a separate project and dedicated storage for each new contest. Never inherit another event's participants, grants, secrets, name, period, prize, or Access Point. Keep application files outside this skill directory.

Keep this skill and its references event-neutral: no real contest names, calendar dates, participant identities, or account-specific origins. Event-specific values belong in each application's configuration and private operational records.

Resolve the name, start, end, IANA timezone, and local or Cloudflare deployment target from the current request. Ask only for essential values that are missing and cannot be inferred. Use English unless another language is requested. Default to free entry, no prize, and an empty description. Resolve relative dates in the organizer's timezone, account for DST, and store an inclusive start and exclusive end as UTC instants.

Use Exness Production for every connected version. Local execution changes the application origin and storage, not the Exness issuer, resources, or API hosts. Deploy the website locally or to Cloudflare as requested; do not ask the organizer to choose an Exness environment.

For local operation, choose an unused port and use one canonical origin with the numeric loopback host `127.0.0.1`. Register that exact origin followed by `/callback`. A successful shell request or metadata read alone does not establish that the Worker, DCR, or browser login journey works; complete the connection preflight in the actual runtime.

## Required journeys

**Organizer:** open the organizer page, enter the contest password, select Sign in, and connect Exness when needed. The first connection requires the organizer's own Partner OAuth and a successful report read. Returning password logins reuse a valid saved grant. No organizer terminal, launcher, setup fragment, pasted token, or API-key form.

**Trader:** select Join the challenge, complete personal Trading OAuth, choose or enter a trading account, provide a nickname and consent, and receive automatic admission only after backend checks succeed. OAuth success alone is insufficient.

**Viewer:** see the public podium and complete standings without signing in. Management and private data remain protected on the server.

The password protects management; OAuth authorizes Exness data access. Every trader uses a separate grant. An organizer who competes also needs a personal Trading grant and the same eligibility checks.

## Essential invariants

- Use direct HTTP APIs with OAuth Bearer tokens. Do not substitute MCP, JSON-RPC, API-key forms, or signed-key authentication.
- Identify every backend Exness request with a stable, contest-specific application User-Agent and request JSON. Apply this to metadata, DCR, code exchange, refresh, and every data read through a shared transport policy.
- Check referral membership with the organizer's grant through the direct Partnership report, without an organizer Access Point.
- Separate opening registration from approving trading accounts. A verified organizer and valid API profile may open entries with an empty AP allowlist. Discover and verify each account's exact AP after that trader authorizes access; unknown origins keep that application pending without receiving credentials. Never require the first trader's server or a personal organizer Trading grant before enabling Open entries.
- With the selected trader's grant, discover that account's Access Point first, then read account details, limits, and history from the approved account-specific origin.
- Complete the operator step for `access_point_unapproved`: inspect protected discovery evidence, independently verify the exact server without credentials, configure only that origin, and retry the saved consented application through all checks. Preserve its grant and session ownership; do not make the trader start over or replace verification with manual admission. Follow [the AP recovery procedure](references/connection-preflight.md).
- When an organizer reports that approval or Retry checks does nothing, inspect the saved failure outcome before changing the button. Distinguish AP trust, limits parsing, and history pagination failures; show progress and persistent feedback. Verify admission separately from a complete score and a later scheduled update.
- Require the exact account number, confirmed real status, and USD currency. Ambiguous or failed checks never approve an entry.
- Rank by the exact sum of USD profit from closed deals within the contest interval. Equal profits share a place. Missing or incomplete history is not zero.
- Place the podium above the full table, with its leaders also included in that table. Use one snapshot, ranking, and freshness model.
- Keep OAuth tokens and temporary verifiers encrypted on the backend, with the encryption key separate from the database. Keep passwords, tokens, cookies, codes, and private responses out of source, logs, chat, and browser storage.
- Preserve storage, vault keys, grants, registrations, participants, and history coverage during ordinary restarts and redeployments. Cookie loss is solved by website login, not a database reset.
- Keep browser login destinations separate from API credential destinations. A provider redirect does not override browser approval requirements or authorize forwarding backend credentials.

## Implementation and handover

Use Workers, Static Assets, D1, and a minute Cron for a new Cloudflare application. Support local execution without creating remote resources when only local operation is requested. Preserve an existing suitable stack for limited updates.

Implement the application, schema migrations, dependency lockfile, documented build/run/check procedures, and relevant tests. This edition supplies requirements, not pre-existing commands or executable helpers. Verify the actual implementation instead of assuming that another edition's test results apply.

For requested publication, confirm the Cloudflare account through Wrangler, create dedicated resources, configure secrets and the public HTTPS callback, deploy, and observe real scheduled behavior. These are deployment-operator tasks; the organizer's experience stays entirely in the website.

Deliver the project location or public URL, organizer URL, resolved period/timezone, entry readiness, checks actually completed, and specific remaining limitations. Distinguish mocked tests, password login, owner OAuth/report, trader OAuth/AP, admission, first result, scheduled refresh, and renewal followed by an API read. Never claim a fully working live contest from documentation, a consent redirect, or mocked tests alone.
