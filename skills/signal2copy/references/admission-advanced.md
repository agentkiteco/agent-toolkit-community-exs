# Admission requirements and optional Advanced controls

Implement behavior against full-target sections 4/5. Use `assets/policies/policy_controls.py` as the reviewed pure-domain component, not as evidence that broker reads, UI, execution or cloud deployment already work. Wire it into the new application's own authenticated state, transport and transaction boundaries. Keep the interface simple; functional behavior matters more than visual matching.

Run the portable [domain check](../scripts/check_policies.py) when adopting or changing this component; optional `--output /ABSOLUTE/RESULT.json` retains its scoped result. Application ownership, actual settings changes and executor effects require their own integration evidence.

## Provider requirements

Expose four strict boolean settings, all OFF: `real_accounts_only`, `partner_accounts_only`, `same_currency_only`, `same_account_type_only`. Only the owning provider can save them. Require the current revision, preserve omitted flags, reject unknown fields/coerced booleans, and retain audit evidence. Saving requirements must not interrupt existing active copy management or force-close positions. Source accounts are exempt.

For real-only, use the exact owner-confirmed top-level Trading account extension `is_demo`: False passes, True blocks, missing/invalid remains pending. Do not infer demo status from credentials, account names, stream segments or a false-looking string. Preserve the provenance distinction: this field and top-level `stream_id` are owner-confirmed extensions, not independently verified public schema claims.

Currency comparison uses the selected strategy's fresh authenticated source and investor observations. Require exact nonempty currency equality; cents are distinct from USD. Account type compares only the final dot-delimited `stream_id` code, preserving case and supporting future codes without a static whitelist. Missing/malformed values remain pending. A `trial` segment does not establish demo status.

## Account-level partner attribution

Do not request email or join a client UID. Reuse the provider's already registered encrypted Partnership pair. Enabling the requirement needs separate explicit consent and fresh successful report-access verification using that exact registered identity. A default-link/provider-login success alone does not establish report access or investor attribution. Disabling removes the separate policy verification/evidence, not the provider's login credentials.

Use signed GET `/v1/partnership/reports/clients/accounts` with `client_account=FULL_CANONICAL_ACCOUNT`, `limit=100`, `offset=0`, `ordering=client_account`. The documented `client_account` array uses comma-separated encoding; a single full account is one array value. The response collection is `data`, each row's `client_account` is a string, and pagination coverage is `totals.count`. Do not invent response aliases. Extract only minimal account evidence and discard report directory/UID/contact data.

A valid exact matching row provides positive attribution evidence. A complete exact filtered empty report can establish absence. Preserve stable filters/order/limit and validate offsets/counts if reading more pages. Ignored filters, mismatched rows, changing/incomplete coverage, malformed responses, authorization failures, throttling and transport errors remain pending/configuration issues, never a fabricated pass or definitive absence. Keep provider report authorization distinct from independently verified investor Trading ownership.

Bound evidence to provider, full investor account, selected strategy/source, policy revision and original observation time, with at most 30 seconds freshness. Do not relabel stale observations as newly verified. Apply a bounded verification deadline and conservative local request budget; the documented 600 requests/60 seconds allowance is shared across all partner keys/operations. A process-local limiter is not a global scheduler. Existing HTTP timeouts also limit calls; an elapsed-time check before the next page is not a hard interrupt deadline.

## Admission boundaries and actual wiring

Login verifies identity; strategy currency/type do not block it. Connection applies real-only and partner attribution. Start, legacy activation and manual Resume also apply the selected strategy's currency/type requirements. Keep Pause, Stop, existing active management and per-trade management exempt from new Partnership admission requests. Technical recovery is not silently a new Start.

The reviewed independent app integration wires provider settings UI/API, native connection guard and native selected-strategy readiness, using injected signed GET responses in local HTTP acceptance. It also performs synthetic connection/Start/Resume prechecks. This does not prove live broker behavior or completed native final transitions.

At each actual Start/manual Resume commit, revalidate ownership, revision, source/strategy/context and evidence immediately before the atomic state transition. Use `validate_admission` under the same final transition lock with current trusted observations. An earlier readiness result or precheck is insufficient after delayed I/O. Do not overwrite the application's native runtime readiness with the older integration branch's execution-disabled placeholder; combine admission with the actual runtime's synchronization/RMS/recovery gates. Preserve independent authentication fixes when merging narrow hooks.

## Optional Advanced controls

Expose five independent thresholds, OFF/null initially: adverse entry deviation %, copied trade volume 0.01–2 lots, total account positions plus pending entries 1–10, daily loss 0.01–20% of saved risk budget, signal age 10–300 seconds. Do not impose presets or enable controls merely because a field has a value. Require explicit values and confirmation; omitted fields preserve state, disabled thresholds become null, cancellation causes no mutation. Better entry prices pass. Do not claim an entry-price cap constrains a pending order's eventual fill.

Use owner/revision/confirmation guards for edits of actual active/paused subscriptions. Block unresolved command/intent/recovery states. Mode/allocation/multiplier changes require paused status and freshly verified equity; commit atomically, leave paused, and preserve existing copy mappings and their original sizing snapshots. No nominal 10000 allocation cap. Proportional allocation uses a positive plain decimal with at most 16 digits/two decimals and cannot exceed verified equity. Multiplier is 0.01–2; exact 1:1 fixes it to 1. Never invent a native subscription to demonstrate active editing.

Keep future-use preferences separate from current subscription controls. The reviewed app stores investor preferences with `execution_applied:false`, and can atomically edit an actual owned synthetic subscription. Its optional entry enforcement remains incomplete and is explicitly reported as such. Native active editing requires an actual native subscription and the runtime's own locking/recovery state.

Continue with [actual executor integration](entry-controls.md): the successor implements these checks in the synthetic executor, applies saved preferences only by explicit Start choice, and exposes actual active/paused settings. Map HTTP `amount` to the helper's allocation parameter deliberately, reject conflicting aliases and inspect actual subscription commands as well as intents before edits. Native preferences remain unapplied until an actual native executor exists.

Daily-loss automatic closing is a separate opt-in requiring its own explicit consent and an enabled threshold. The helper observes whole-account equity against the first observed UTC-day baseline and saved risk budget, including floating/manual/funding effects; track while paused and do not automatically resume the next day. `daily_loss_update` returns a desired normal-Stop action, never a close command. Persist the observation/stop-request identity atomically with an idempotent normal Stop outbox. The reviewed app does not schedule daily observations or wire this Stop outbox. Never present recorded consent/preferences as functioning automatic protection.

Before claiming Advanced complete, integrate final entry/volume/slot/signal checks and daily-loss observation/Stop into the application's actual engine. Mandatory margin/RMS/recovery gates remain independent. Update provider/investor guides with what is enforced, what is stored only and the next useful step.

The synthetic continuation in entry-controls.md supplies this scheduler/outbox integration with scoped execution evidence; the earlier settings-only statements above describe its starting point. They are not a claim that native daily-loss closing is available. Do not copy an old enforcement=false response into a functioning synthetic implementation or mark a native preference as applied.

## Evidence scope

Pure-domain acceptance: 29 offline checks. Independent settings/admission app acceptance: 12 local HTTP checks with generated dummy Ed25519 keys and injected native signed GET responses. No live broker, cloud, actual accounts, trades or automatic closes were involved. These counts describe retained focused evidence, not an end-to-end functional-equivalence guarantee. Reuse the component and contracts without repeating low-value verification; test changed integration boundaries and keep incomplete enforcement explicit.
