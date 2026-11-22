# Recorded financial reports: useful M3 increment

Extend the existing application after authenticated native account reads. Start with source and investor whole-account reports; then add exactly attributed copying, CSV and quality views. Preserve the current installation, sessions, encrypted credentials and unresolved execution evidence. Use mocked native responses for this iteration. Do not ask again for live broker keys or treat them as a prerequisite.

Use the standalone [recorded reporting helper](../assets/reporting/recorded_reports.py) as reusable calculation infrastructure. Copy it into the generated project and wire its functions deliberately; it is not an application, native journal adapter or authorization layer. Do not copy an earlier product implementation, test bootstrap, private installation or signing identities.

Use the portable [domain check](../scripts/check_reports.py) when adopting/changing the helper; optional `--output /ABSOLUTE/RESULT.json` retains a result. This does not replace authenticated application and complete-export verification.

## Application integration

Add a small report service behind the existing authenticated router, lock and persistence boundary. Derive ownership from the session and registered source/strategy, never a submitted role or account ID. Reject foreign account/strategy selections before reading broker data. Reuse encrypted stored Trading credentials without key re-entry.

A compact implemented route shape is authenticated same-origin POST:

- `reports/read`: explicit bounded native deal-history ingestion for the provider's dedicated source or the connected investor's own account. Persist original event/deal payloads and distinct versions, requested interval, read time, pagination outcome and incomplete attempts.
- `reports/view`: saved-record report. Provider source/strategy performance uses the owned source; provider copying exposes anonymized aggregates by currency. Investor scopes are own whole account or exactly confirmed copied records for the selected strategy.
- `reports/financial.csv`: full requested saved set, independently of the displayed page. Provider copying exports only its anonymized projection.
- `reports/quality` and `reports/quality.csv`: retained normalized operation evidence for the authorized account/strategy. Label whether quality covers the selected interval or all retained commands; never silently imply date filtering.

Keep existing Host, Origin, session-expiry and request validation on JSON and CSV routes. Do not expose raw investor records or credentials to the provider. Provider copying aggregation can use already investor-ingested history; it must not silently read investor credentials. Use an installation-held secret for stable strategy-scoped pseudonyms. Keep currencies separate.

Expose reachable source/strategy reports, investor scope selection, UTC interval inputs, explicit Read history, Show saved report, financial CSV and quality CSV controls. Show meaningful totals and availability alongside inspectable evidence. Update provider/investor guides and BUILD_STATE with the next useful action. Avoid a UI redesign.

Use a compact escaped record table with Previous/Next over the server's deduplicated pages. Keep raw evidence collapsed and serialize it only on explicit expansion; a large default JSON dump is not usable record browsing. CSV still exports the complete matching set. Reset page1 after scope/date changes, disable repeated actions while loading, and discard stale responses/downloads when selection or the signed-in panel changes. Show explicit errors and label any retained older result. Quality browsing must disclose its retained-journal scope independently of financial date inputs.

## Calculation and evidence contract

`normalize_native(account_id, currency, items)` accepts the documented `event_time` plus `deal` shape, canonical string IDs and decimal strings. It preserves raw evidence. Do not invent universal aliases for native schemas. Supply verified currency explicitly; retain native profit currency. A present-day account type does not prove historical fee treatment.

At an explicit broker-to-domain boundary, normalize valid finite decimal text such as `.01` to the helper's canonical `0.01` without altering its value, inventing missing costs or losing the original raw row. Check the first actual history response before persisting a successful source connection; a normalization failure must remain a visible failed operation, with a usable retry rather than a half-completed connection.

`deduplicate(records)` keys by account plus deal ID, merges complementary sparse evidence and retains conflicting explicit versions. Deduplicate before aggregation and pagination. Never overwrite a conflicting fee with the newest version or turn missing data into calculation zero.

`build_report(..., account_id, currency, start, end, scope, mappings, strategy_id, history_complete=False)` calculates native-currency signed posted trading net: gross close profit plus recorded opening/closing commission, swap and admin fees, including fees posted on open positions. Funding and null compensation remain separate. Unknown/conflicting components withhold affected net while retaining known subtotals and reasons. Unsupported financial types require classification. Closed-position realized net is distinct and remains unavailable without sufficient attribution. No tariff, current FX, repeated opening fee or invented return is permitted.

An omitted closing commission can become effective zero only with dated, nonconflicting same-account/same-position opening evidence supporting the narrow Zero/Raw included-at-opening case. Preserve raw/effective values and basis. Do not infer this from current configuration or charge an out-of-period opening fee again.

Copying attribution requires exact confirmed account/deal, order or position mappings retained by the trusted execution journal. Dates, equal equity, similar trades and requested IDs alone do not establish ownership. Do not create a public mapping-seeding endpoint. Without confirmed mappings, empty copying reports are correct. `provider_copying_reports(...)` returns pseudonymous investor projections and currency groups; never send it arbitrary unauthorized account collections.

`financial_csv(report)` exports the supplied **page**, so the application must iterate the full matching set first. Include raw/effective fees, availability, conflict fields and retained versions. Provider copying needs a separate projection-only export. `quality_rows`, `quality_summary` and `quality_csv` require deliberately normalized retained commands: operation-specific requested volume, explicit availability, and entry average only from confirmed submitted-entry evidence for one exact position. Protection, pending edits/cancellation and pending placement must not acquire invented entry prices or close volumes. Empty journals remain empty.

## Coverage and remaining curves

Use half-open timezone-aware intervals and UTC daily saved-posting summaries. Display coverage and missing components even when the result is empty. Completed cursor pagination proves only completion of that bounded request, not broker retention or complete economic history. On failed/truncated reads retain prior saved versions and mark the attempt incomplete. If the SDK discards partial pages on exception, state that limitation rather than claiming those pages were saved.

Expose the last verified equity snapshot with its original observation time. A cumulative saved-component net curve is not equity, percentage return, drawdown or TWR. Historical currency/account-type changes require dated evidence. Do not fill missing historical observations with today's values.

## Day, month and all saved history

Offer Today (UTC), This month (UTC), a custom half-open UTC interval and All saved history. Resolve calendar boundaries once per request in UTC, including year transitions. All saved history starts with the earliest retained record in the authorized account collection; label it as saved coverage, never complete broker lifetime. With no saved records, show no data, not a zero performance result. Do not silently fetch unbounded history for this selection; older broker reads remain explicit bounded actions.

Use the same deduplicated signed posted-component calculation for the overall total and every daily/monthly bucket. The bundled helper exposes `period_summaries(...)` for one authorized account/scope and `provider_period_summaries(...)` for anonymized currency aggregates. These call the existing report calculator; they are not a second P/L formula. Only periods with saved evidence or a relevant issue are emitted. Missing days/months are not fabricated zero buckets. Partial boundary buckets stay clipped to the selected interval; report the actual from/to.

Show period trading net, known gross close P/L and commissions with funding separate where applicable. Include fees posted on still-open copied positions. Carry unknown/conflicting/unattributed cost rules into each affected bucket; older unaffected buckets may remain available while the overall net and curve are withheld. The cumulative step result follows saved posting sequence and excludes funding, with no invented equity or percentage return. Keep the observed whole-account balance/equity timestamp visibly distinct from copying-only recorded results.

Keep Closed deals, Costs and Copying quality reachable with their actual evidence labels. A page's deal/cost tables may be paginated, but its totals, UTC summaries and curve cover the complete selected saved set. Financial CSV must export that same full matching set even from a later displayed page. Missing numeric values remain blank with availability/basis fields. Provider copying gets currency-group summaries and pseudonymous investors only; do not leak raw account/deal IDs through new period data or exports. Reject explicit foreign account selections and inconsistent provider strategy/source choices before calculation or broker access.

One useful generated walkthrough can establish real copied identity through the app's existing confirmed journal, then supply known economic history through separate broker controls. Include copied opening/closing costs and posted swap/admin, historical manual trades across a month boundary, funding, duplicate records and enough rows to exceed one displayed page. Write expected day/month/overall and copying/whole-account results before running. Compare provider source and anonymized copying views, full CSV and one later missing linked cost that must withhold affected net/curve. Do not add a public app endpoint to seed mappings or records, or turn this one walkthrough into an unrelated trading/cloud campaign.

Build historical performance later by persisting verified timestamped equity/balance observations, exact external cash-flow events and ordering, currency provenance and coverage/gap markers. Establish the valuation and cash-flow methodology, including treatment at subperiod boundaries, before linking returns. Calculate TWR only for subperiods with sufficient verified valuations and flows; keep gaps and unsupported periods unavailable. Avoid applying a cash-flow adjustment twice. Add focused checks when that later capability exists.

## Evidence boundary

The retained implementation experiment passed 19 actual loopback HTTP checks using generated signing keys and mocked native protocol responses: authenticated roles, signed SDK cursor ingestion, 209 unique full-export records, opening fees/funding separation, UTC summaries, unknown-fee withholding, failed-read preservation, confirmed-mapping isolation, anonymized per-currency provider output and CSV, and quality evidence. Processes were stopped. The UI check verified served controls and their native render hook; it did not establish browser-rendering acceptance.

This supports an iterative application increment, not full functional parity. It proves neither live broker schema/retention, enabled native copying, historical equity/TWR, cloud deployment nor live financial correctness. Keep those evidence boundaries visible and proceed with the next authorized milestone.

The period-summary extension has a separately scoped generated application walkthrough in the kit's release validation. Historical check counts above remain evidence of their earlier snapshot, not fresh results for each successor. Broader source-performance/filtering, historical valuation/TWR and all report/currency/account-type combinations still require their own evidence.
