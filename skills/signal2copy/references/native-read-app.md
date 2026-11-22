# Native read integration in the same application

Read after the standalone native adapter works. Extend the same project with authenticated account binding, native data normalization and readiness visible in its application. A second CLI or static status badge is not this increment. Full native copying still requires the remaining M2gates.

Use the [bundled runtime and host contract](runtime-integration.md) for the broker facade and managed reads. Preserve the first app's state, role access and server worker; importing the package does not connect those app surfaces for you.

## Useful read-only application increment

A distinct native-read-only installation mode can deliver useful account/condition/history views before trading is enabled. Default synthetic behavior must continue to work. Seal the chosen mode in persisted installation state, preserve original encryption keys/unresolved records, and reject incompatible restoration/configuration before execution or broker activity. Never silently convert a synthetic subscription into a native one or fall back to synthetic data after native read failure.

When provider Partnership onboarding is unfinished, a privately configured owner workspace is an acceptable explicitly temporary path. Authenticate it as installation owner, not broker-verified provider/investor. Native Trading account reads do not establish partner affiliation or provider identity. Keep missing onboarding visible in the plan and guides; no fabricated partner-verification success.

Use explicit owner-only local configuration and consent for first import when required. Bind source/investor to configured canonical account IDs and their credentials. Encrypt retained keys and reuse them on refresh/restart; never ask the client to re-enter a known key for ordinary refresh. UI/API responses, errors and logs omit keys, signed headers, tokens and raw private config. Do not allow request parameters to select arbitrary credentials/accounts or change installation mode.

## Normalized data and readiness

- Obtain details/snapshot/conditions/history through the native client and validate returned identity. Keep account/position/order IDs as strings and money/volume as finite decimals. Derive currency/specifications from native metadata, not fixture identities/symbol names.
- Preserve distinct account trade_mode/account_status, source versus investor roles, actual read time, and availability/coverage. Closed-history objects are separate from current snapshot positions/orders. Missing fields do not become zero, guessed states or synthetic defaults.
- Surface source/investor account, equity/currency/current exposure, instrument conditions and bounded history through the application's authenticated routes/UI. Preserve original native evidence for unresolved mappings; a normalized display is not ownership or confirmed execution.
- Readiness must expose data availability separately from permission to copy. A healthy native read-only workspace can be operational while Start remains blocked for absent onboarding, streams, risk/margin or write integration. REST snapshot alone is not verified continuous transaction synchronization.
- Native error/quota/identity/schema failure keeps that account unavailable and copying blocked. Do not replace it with empty successful state or stale apparently fresh cached data. Reuse keys privately; return a relevant actionable read error instead of requiring repeated sign-in on every transient failure.

All trade entry, modification and cleanup endpoints must remain disabled in native read-only mode. Enforce this server-side, including direct Start/Resume/Stop requests; UI controls alone are insufficient. The native client remains writes-disabled. Explicit owner consent to read/import never authorizes orders or closing existing exposure.

## Focused application acceptance

Use generated-key/native-shaped injected I/O behind the real application routes, plus a small separate reviewer case. Check anonymous/foreign-session denial, private-config consent/encryption/reuse, non-fixture account IDs, distinct source/investor data, malformed/mismatched native responses, readiness blocked despite successful reads, direct mutation denial with zero broker writes, restart without key re-entry, and incompatible mode restoration preserving prior state. Verify the unchanged synthetic increment when shared dispatcher/startup/UI changes. Record actual browser proof separately from HTTP and JavaScript syntax.

Update BUILD_STATE and both role guides with exact mode/control labels, tested routes and next step. Document owner startup/config/backup/key handling. Only after native normalization/admission/sync/RMS/recovery and authorized broker checks pass may native execution be enabled. No new deployment or real-account access follows merely from installing this skill.

When validating the selected native conditions, require its instrument identity to match and its volume min/step/max to be finitepositive and coherent. Invalid or unavailable metadata must not yield available data readiness; preserve prior successful time and explicit unavailable state. Authentication denial401and foreign-role403are distinct valid outcomes; do not change application auth semantics merely to satisfy a mistaken test expectation.

Next read [native provider/investor onboarding](native-onboarding.md) to replace temporary owner-preview access with ordinary role flows in a separate verified mode. Never silently promote owner-configured bindings into broker-verified identities.

## Usable account and stream status

Use the same authorized account selection for readiness and read-stream actions. Reuse retained keys; do not add a key-entry prompt to ordinary refresh/synchronization. Show connection state and received baseline state separately, with observed time and an explicit refresh action; read readiness is not trade permission. Keep technical evidence collapsed. Invalidate asynchronous responses after account/strategy selection or render changes, expose busy/error/retry, and clear read consent when account/instruments change. Match the actual implemented controls in both role guides; equivalent clear designs are acceptable.
