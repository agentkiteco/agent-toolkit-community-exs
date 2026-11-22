# Native provider and investor onboarding

Continue the same application's native component/read-only work. Deliver the ordinary provider/source/strategy/investor user path with broker-backed read verification, not another installation-owner preview. Native execution stays disabled until transaction/tick synchronization, RMS, ownership and durable final dispatch gates are integrated. Existing synthetic and native-owner installations remain mode-bound and unchanged; no implicit identity migration.

## Observable flow

| Step | Required behavior |
| --- | --- |
| First provider registration | Installation invitation, explicit encrypted-storage/read consent, signed Partnership default-link read with valid response; atomically close registration only on success |
| Provider sign-in | Match the registered cryptographic key identity first, then verify Partnership capability; don't require an investor account or silently fall through to investor after a provider error |
| Source connection | Separate Trading account/key verification and consent; exact returned account ID; encrypted retained credentials and native account state |
| Strategy | Provider-owned dedicated source binding, actual create/publish, public safe catalog/detail, no private keys or investor financial data |
| Investor sign-in | Selected published strategy plus explicit canonical Trading account and verified key pair; no investor registration, role selector or email |
| Investor connection | Separate explicit consent/verification; account/strategy/session bindings server-side; a successful sign-in is not Connect or Start |
| Readiness | Fresh authorized source/investor read availability, actual currency/equity/account restrictions and explicit remaining blockers; native copying staysfalse |

Use the official [default partner link](https://www.exness-api.com/reference/partnership/get-default-partner-link) operation at GET /v1/partnership/partner/default-link on the configured Partnership HTTPS origin. Validating Trading credentials does not establish provider Partnership capability. A malformed HTTP200response, failed signature/access, quota or transport error must not create a registered provider. Retain a useful safe error and allow a later authorized retry without replacing stored identity.

Trading uses its configured Gateway/account Access Point; Partnership uses its separately configured API origin. Don't accept arbitrary request-supplied hosts or guess global hosts. The [Partnership example](https://www.exness-api.com/partnership/guides/code-examples) retains an empty signed idempotency_key but omits the idempotency header for its read. This differs from the generic Trading GET header rule. Follow the documented product-specific operation, keep exact signature bytes, and disclose any unresolved discrepancy. Handle numeric request-processing errors separately from string Partnership errors; never leak raw private headers/diagnostics.

## Identity and ownership

Canonicalize equivalent signing material for role matching (seed, expanded seed/public pair, PEM); do not treat text formatting as a different owner or truncate an invalid expanded key. Registered provider identity takes precedence even when that key also has Trading access. Don't infer a new provider role from a submitted selector. Investor account authorization must not allow access to another investor's saved records, source credentials or unpublished provider data.

For an unregistered identity, probe Partnership capability before granting investor access. A successful valid Partnership response identifies a foreign provider and must refuse this installation's investor login. Only the documented HTTP403 with numeric code1002 establishes the negative scope result that permits separate selected-account Trading verification. String PermissionDenied, malformed success, signature/authentication errors, quota and transport failures remain indeterminate and cannot become investor fallback. Failed probes never replace the registered provider or erase retained keys.

Preserve selected strategy through login/connection and recheck its availability where required. Bind source/account IDs and credentials explicitly, never fixture1111/2222. Record separate source-read and investor-connect consent. Reuse encrypted authorized keys for account refresh/restart; do not request them again merely because a user is already signed in. Keys never enter URLs, browser storage, public records or logs.

Do not ask for email. Account-level partner affiliation, when implemented, uses [client accounts report](https://www.exness-api.com/reference/partnership/list-report-client-accounts) at GET /v1/partnership/reports/clients/accounts with its documented stable filters/limit+offset pagination and stored provider keys. Provider login/default-link success alone does not establish selected-investor affiliation. Keep unimplemented admission/Advanced policies unavailable rather than bypassed or presented as verified.

## Focused application acceptance

Verify successful and failed registration, provider key-format equivalence/priority, source verification/strategy ownership/publication, selected-investor sign-in/separate Connect, two-investor isolation, direct API tampering, encrypted key reuse after restart, no email, and server-side native lifecycle denial with zero broker writes. Test actual app HTTP with generated keys and native-shaped signed responses; label constructed I/O, real TLS/authenticated reads and browser proof separately. Preserve failures/limits, update both role guides/BUILD_STATE, and recommend synchronization/RMS as the next execution work rather than claiming that login enables copying.

Require the investor's explicit Connect before readiness performs source/investor refresh. After a successful account refresh, clear stale failure diagnostics rather than leaving an old403beside available data. Publishing requires a fresh authorized source check; an already owned strategy can be unpublished locally even while the broker is unavailable, without a broker request. Distinguish this permission-reducing action from new trading/publication.

Continue with [native synchronization/preflight](native-runtime.md) before any native copying authorization. A completed read-only role flow is not a synchronized executor.
