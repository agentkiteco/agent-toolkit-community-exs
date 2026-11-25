---
name: partner-pulse
description: Build or update Partner Pulse, a private Exness partner portfolio dashboard using the official Exness MCP. Includes verified portfolio analytics, client priorities, onboarding insights, read-only rebates, exports, and client follow-up drafts, with honest live or snapshot-based updates. Use when asked to create, implement, or modify this dashboard.
---

# Partner Pulse

Build “Partner Pulse”: a working dashboard that helps an Exness partner
understand portfolio changes and prepare client follow-ups.

This package supplies implementation instructions, not application source code or
a running service. Build the application in a separate project; keep its code,
configuration and private data outside the skill folder. Preserve an existing
application's stack and behavior for narrowly scoped updates. Use English unless
the user requests another language. Publish only when requested.

Complete the application end to end. Do not stop after research, a plan,
or an initial scaffold. Work incrementally: launch a visible first version
early, then continue implementing and verifying the remaining features
without asking for approval between routine steps.

## 1. Deliver a visible first version early

Use a simple, maintainable stack consistent with the repository.
This is a fresh application unless existing project files indicate otherwise.

First create and launch a responsive English-language interface with:

- Near-black background, dark cards and warm yellow accents.
- An original pulse-wave logo and “Partner Pulse” wordmark.
- Clear typography, accessible contrast and keyboard-accessible controls.
- Left navigation: Overview, Clients in focus, Business insights,
  Rebates and Exports.
- Overview metric cards, a client table and a prominent priorities area.

Inspect the available Exness MCP tools and make a minimal read-only
portfolio request to populate the first screen with real data.

If the connection is unavailable, still launch the interface with:
“Connect Exness to load your portfolio.”
Show unavailable metrics and an accurate connection or error explanation.

Provide the working preview or local URL as soon as it is available,
then continue building. Do not use demo data to make the screen look complete.

## 2. Use official Exness MCP

Use the connected official Exness MCP as the portfolio data source.
Access only the current user's authorized partner portfolio.

Discover the available tool names and schemas first. If documentation search and
page tools are available, use their actual names to verify the following; otherwise
use provider documentation accessible in the environment. Treat unverified contracts
as unavailable rather than guessing:

- Available reports and response fields.
- Date semantics and reporting timezone.
- Pagination and request limits.
- Aggregation dimensions and identifiers.
- Currency and volume units.
- Missing-data behavior.

Record documentation provenance and freshness. If documentation tools expose a
snapshot, describe it as a snapshot, not live documentation.
Do not guess tool names, fields, authentication methods or endpoint URLs.
Do not substitute Trader API data for the partner's client portfolio.

Determine whether the application runtime can invoke MCP through a supported,
authenticated integration.

If supported, wire the application to that integration and implement real refresh.

If unsupported, use a private snapshot fetched by the assistant through MCP.
Clearly label the application as snapshot-based, display its fetch time,
and provide an honest update workflow: the assistant must explicitly fetch a new
snapshot and replace it through a private import or update path. Reloading the page
only reloads the existing snapshot. Do not promise unattended updates without a
verified runtime integration. Do not imply that the website
can independently invoke tools available only in the assistant session.

Do not build a separate direct Exness API integration as a fallback.
Do not request credentials in chat or expose secrets in frontend code,
logs, screenshots, exports or source control.

## 3. Real data and reliable loading

All clients, metrics, charts and recommendations must come from real
MCP responses. Never invent values or substitute mocks after failures.
Fixtures are permitted only in isolated tests.

Fetch every required page for the implemented analyses.
Respect documented date-range limits and use bounded retries only
for appropriate transient failures.

Validate numeric values, dates and identifiers.
Distinguish clients from trading accounts and join them only through
documented relationships. Do not invent IDs or deduplicate legitimate
rows merely because their displayed fields match.

For each dataset track:

- Source MCP tool and request parameters.
- Last successful fetch timestamp.
- Reporting period and verified timezone.
- Coverage and pagination completeness.
- Missing fields, errors and reconciliation issues.

Missing values are not zeros.
Show zero only when complete, valid data supports it.
Do not present partial-page calculations as portfolio totals.

Preserve previously fetched data after a refresh failure, with a visible
stale-data warning. Do not advance the successful-fetch timestamp.

Before loading real records into a hosted preview, verify that only the portfolio
owner can access both the interface and its data endpoints. Use supported owner-only
hosting when available; otherwise keep real data local until access controls are
implemented and verified. A hidden URL or client-side gate does not provide access
control. Keep credentials in the supported authenticated integration and keep
sensitive responses out of logs and analytics.

Keep private records, snapshots and exports out of public repositories
and public deployments. Never bundle a real snapshot into public static assets.

## 4. Overview and business insights

Implement supported metrics:

- Direct-client credited commission.
- Second-level credited commission.
- Reconciliation with equivalent report totals.
- Trading volume in lots and USD.
- Rewarded orders.
- Distinct reward-generating clients.
- Registrations.
- Retention, reactivation and inactivity.
- Latest known trading dates.

Support these comparisons where data permits:

- Last seven complete reporting days versus the preceding seven.
- Month-to-date through the latest verified complete reporting day
  versus the equivalent period last month.
- On the first day of a month, the latest two complete months.

Document timezone, reporting finality and unequal month lengths.
Do not assume yesterday's reports are finalized.
Suppress affected comparisons when dates, coverage or aggregation
cannot be validated, and explain the specific reason.

Define activity criteria, cohorts and denominators.
Do not use lifetime totals as period-specific activity.
Do not equate absence of rewarded orders with absence of all trading.
Reconcile only matching periods, currencies and aggregation scopes.

Do not infer trading profit or loss from commission, volume or deposits.
Show P&L only if an appropriate documented partner source supports it.

Use actual data for every chart.
Document: displayed metric → calculation → MCP tool → response fields.

## 5. Clients in focus and today's plan

Make these areas prominent:

- Today's priorities.
- Signal of the week.
- Portfolio pulse.
- A 30-minute follow-up plan.

Rank up to five clients using verified evidence of:

- Commission contribution decline.
- Reduced activity.
- Recency.
- Supported onboarding or deposit difficulties.

For each priority show:

- Verified client identifier and relevant trading accounts.
- Supporting values and comparison dates.
- Latest known trading date, if available.
- A concise explanation.
- Relevant uncertainty.
- A short, personalized support message ready to copy.

Explain the ranking criteria.
Return fewer than five clients when fewer qualify.
Never fill the list artificially.

Allocate 30 minutes across qualifying follow-ups and note-taking.
If none qualify, suggest planned relationship check-ins without
inventing recipients.

Do not invent causes, assume losses or distress, promise results,
or encourage clients to trade more.
Prepare messages only. Never send them.

## 6. Onboarding and data conflicts

Show the supported funnel:
Registration → KYC → First deposit → First trade.

Clearly separate current-status counts from dated cohort conversion.
Do not infer historical conversion dates from current flags.
Treat deposit ranges as ranges, not exact amounts.
Do not infer an absence of deposits from undated fields or
attribution-only zeros.

Show suspected blockers as questions to investigate.

If a first-trade flag is false but documented trading volume is positive:

- Display a data inconsistency.
- Exclude the client from “No first trade” recommendations.
- Do not present the inconsistency as a confirmed client problem.

Show dated deposits, first deposits and failed-deposit statistics
only where the source supports their meaning and reporting period.

## 7. Rebates and exports

Keep Rebates read-only.
Show existing rebate information only when supported by MCP.

If adding a scenario calculator, label user-entered assumptions
and hypothetical results clearly. Never suggest that rebates
guarantee restored activity or profits.

Do not construct EXD transfer links manually.
Use a supported link-building tool only when recipient mapping,
tool prerequisites and an explicitly chosen amount are available.
Otherwise explain that the links are unavailable.
Never execute transfers.

Exports must reflect the same verified data, periods, coverage
and limitations as the interface. Protect export access with the same owner-only
controls. For CSV exports, safely encode cells and neutralize spreadsheet formula
injection in untrusted text while preserving valid numeric types.

Do not place trades, send messages, transfer funds or EXD,
create rebate groups, or modify account settings.

## 8. Honest application states

Handle these states separately:

- Not connected.
- Loading.
- Request failed.
- Incomplete coverage.
- No portfolio records.
- No qualifying signals.
- Filters hiding existing signals.
- Stale snapshot or cached data.

Show congratulations only when the relevant checks completed
successfully and found no qualifying follow-ups.

Use a polished success card with a yellow checkmark and subtle glow:

> A MOMENT TO CELEBRATE
>
> Congratulations!
> No follow-ups flagged.
>
> “[actual count] clients checked. No follow-ups were triggered
> by the current rules.”

Show KYC, first-deposit and failed-deposit statistics only when supported.

Add:

> Make room for meaningful conversations.
>
> Use this time for planned check-ins and stronger client relationships.

An empty queue is not proof that the portfolio is healthy.
Display limitations separately. Missing data, failed checks or hidden
results must never trigger congratulations.

## 9. Verify and deliver

Run appropriate checks for:

- Pagination.
- Comparison periods.
- Metric calculations and reconciliation.
- Client/account aggregation.
- Missing and conflicting data.
- Signal eligibility.
- Loading, error, empty and success states.

Build the application and visually verify desktop and mobile layouts.
Check keyboard navigation and readable contrast.

When MCP access is available:

- Perform a real read-only fetch.
- Verify its returned data appears in the interface.
- Check at least one metric against its source or calculation.
- Verify the supported refresh or snapshot-update workflow.
- Confirm that failed refreshes preserve successful-fetch timestamps.
- Verify that unauthenticated requests cannot read portfolio data or exports in
  hosted deployments; inspect served assets for accidentally bundled snapshots.

If access is unavailable, finish the runnable interface, data integration
code that can be implemented from verified contracts, and setup guidance.
State precisely which live checks remain blocked.
Do not claim successful integration based only on fixtures or compilation.

Provide:

- Complete source code and dependency manifests.
- Reproducible install, development, build and start commands.
- Placeholder-only configuration.
- Appropriate `.gitignore` rules.
- README with MCP setup, architecture, source mappings,
  documentation links and known limitations.

End with the working preview or local URL and a concise report:
what was implemented, how to run it, which checks passed,
whether real MCP data was verified, whether updates are live or
snapshot-based, and which capabilities remain unavailable.
