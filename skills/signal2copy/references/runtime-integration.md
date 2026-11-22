# Reuse the native runtime in the same application

Read this before choosing the first app's durable account/subscription schema when native copying is part of the requested outcome. Use the bundled core at the native stage rather than reimplementing synchronization, journal dispatch and fill recovery from prose. The app still supplies authentication, encrypted durable storage, admission, optional controls, role APIs and UI. This is a reusable core, not a finished trading application or live acceptance certificate.

## Install and wire

Run `python <skill>/scripts/install_runtime.py --app-dir <app-source-directory>`. It creates a new `signal2copy_runtime/` package with its manifest and pinned direct requirements. It never overwrites an existing package or edits the app, starts a process or connects to an account. Review/merge future updates explicitly. Install its `requirements.txt` through the project's chosen environment and record the dependencies in the app's deployment build.

```python
from signal2copy_runtime import NativeBroker, NativeEngine, Conversion

# Values come from explicit installation configuration, never guessed hosts.
app.broker = NativeBroker(gateway_origin, partnership_origin)
app.conversion = Conversion(app.broker)
# Implement the host contract below before constructing the engine.
app.engine = NativeEngine(app)
```

Initialize after restoring the original encrypted state and processing any owner freeze/reset. The constructor validates the host interface without calling its hooks, then pauses retained active native subscriptions pending fresh synchronization and explicit Resume. Instantiate once. No import starts background work. Serialize role mutations and `engine.tick()` with the same host lock; call tick from the server worker, independently of the page. Shut down account streams explicitly on disconnect/process exit.

For a native installation, default to `native-read-only`. `native-execution` selects the supported ordinary policy only for an explicitly configured installation whose app integration/gates and client authorization are complete. Preserve retained `state.mode`; changing an existing read-only installation's environment is not an activation procedure. Do not pass a test policy in shipping code. No browser checkbox or unconditional hook may bypass mandatory gates.

Connect/source/refresh are read actions. Use the existing onboarding references for capability-based role detection, source account verification and encrypted retained keys. After consent, `broker.sync(account, symbols)` starts managed reads; `broker.sync_status(account)` reports evidence, not trading permission. Bind explicit authorized Start to `engine.start(session, body)`, lifecycle actions to `engine.lifecycle(subscription, body)`, and the worker to `engine.tick()`. The core handles sizing, final dispatch, exact reconciliation, pending/owned management and bounded recovery for its supported cases.

## Host contract

`NativeEngine(app)` checks these names and callback signatures before changing retained state. That check verifies wiring only; a present function does not prove its authorization or durability semantics. The same application owns the data and trusted boundaries.

| Host member | Required behavior |
| --- | --- |
| `mode`, `state.mode` | Matching sealed `native-read-only` or `native-execution` strings; never reinterpret synthetic state as native. |
| `state.frozen`, `store.failed` | Boolean owner/durability fences. Unknown/lost checkpoint acknowledgement closes `store.failed` and stops dispatch. |
| `state.accounts/strategies/subscriptions/commands` | Canonical dictionaries keyed by retained IDs, not detached engine-only copies. Preserve unfinished reservations, exact links and all unknown requests. |
| `broker` | Bundled `NativeBroker`, its configured quota ledger and original-time stream evidence; no fixture fallback. |
| `save(event)` | Synchronously commit the complete canonical business state, including commands/mappings, with acknowledged revision/mutation identity before returning. Cloud uses the existing bridge contract; container-local files are insufficient. Raise and fence on an uncertain ACK. |
| `account(id)` | Return the canonical connected authorized account, including server-private access. Deny a disconnected/obsolete epoch. Never expose this object through a public view. |
| `admission(investor, source)` | Enforce the current revisioned provider requirements, including selected-account Partnership membership when enabled. Use retained provider keys, no investor email or second key entry. Raise on missing evidence. |
| `settings(body, equity)` | Validate requested sizing and return `mode/amount/multiplier`. Internal modes are `proportional` and `one_to_one`; map UI aliases deliberately. Proportional allocation is positive, at most verified equity, multiplier0.01–2. Exact1:1 has amountNone and multiplier1. |
| `signal_ids(snapshot)` | Return canonical `p:<position_id>` and `o:<order_id>` identifiers for positions and limit/stop entries. Use these same identities for activation, Pause and Resume boundaries. |
| `unresolved(subscription)` | Return that subscription's commands in prepared/intent/accepted/unknown states, preserving known refusal/review semantics separately. A stopped label never erases live follow-up. |
| `fx(account, from_currency, to_currency, purchase=False)` | Delegate to the bundled `Conversion.convert`, returning `(Decimal rate, route evidence)` from that account's inventory. No fixed FX defaults. |
| `controls(sub, signal, snapshot, lots, quote, exclude_command=None)` | Enforce implemented optional limits, including whole-account capacity plus uncertain reservations. Return `(None, None)` only when configured controls actually permit entry; otherwise return `(waiting/skipped status, reason)`. Unsupported configured controls must hold, not silently pass. |

An account has string `id`, server-private `key/private`, boolean `connected`, integer connection `epoch` and `observation` with `details/snapshot/checked_at`. Native roles use session `role` and canonical `identity` (account ID for an investor). A strategy has `id/source/published`; source is an account ID. The core creates native subscriptions/mappings/commands through Start. Do not construct them from browser-submitted ownership claims or replace old rows with an empty schema to make integration pass. An existing different schema needs an explicit lossless adapter/migration preserving original keys, IDs, unresolved effects and mode; otherwise hold native activation while continuing unrelated work.

Host views must whitelist public fields. Account objects, nested observations and engine state are private implementation objects, not safe API payloads. Reuse reporting/management/admission references for role projections, owner storage, Advanced/reviews, source history and guides. Importing this core does not implement those routes or user actions.

## Required integration outcomes

Continue one project through these gates; report the current useful result and continue authorized unblocked work:

| Stage | Observable result before marking complete |
| --- | --- |
| Local foundation | Provider/source/publication, selected investor Connect and explicit confirmed synthetic copies in both modes; retained state, Stop and actual role guides. Choose the native-compatible state contract or record its explicit adapter. |
| Native reads and first cloud delivery | Ordinary role UI uses retained access, managed baselines/stream state and configured quotas; native trading remains denied. The same app integrates encrypted cloud business/owner restore and acknowledgement. Deploy once the local execution/persistence foundation is useful; synthetic/read-only cloud scope is acceptable and does not require real keys just to start. |
| Native execution and target actions | Core Start/lifecycle/tick plus admission/controls/durable host integration are implemented; role actions cover required pending/protection/fills, FX, initial scope, Advanced/reviews, strategy/sizing views and reports. Generated observations precede any authorized live use. Missing evidence holds only dependent operations; it does not erase a missing target feature. |
| Handoff | One feature-map status for the same app, actual implemented guides and relevant cloud outcome. A healthy synthetic deployment cannot close native/target gaps. A user asking for the whole app has not asked to stop after the first demo. No second clean rebuild is a normal client milestone. |

## Evidence and limits

The core was extracted from the previously generated author reconstruction, not reference production source. Six logical modules are reused: SDK/signing, managed runtime, execution/recovery, supported policy/quotas and FX. Package-relative imports and an early host-interface check are the extraction changes; the SDK includes the tested stream lock/callback integration required by managed synchronization. Existing generated evidence covers bounded ordinary execution, stream replacement and retained partial-history recovery. Those are historical source observations, not a fresh client or real-broker pass.

`scripts/check_runtime.py` installs the package into a fresh directory and checks real package imports, no-overwrite behavior, missing-hook refusal before mutation, read-only Start denial, retained unknown/no-resend, late exact ownership, runtime replacement and FX sizing boundaries without network access. This is one integration observation, not a full app rebuild or live acceptance. Follow up with one ordinary app/independent-broker example once the host routes are connected.

Known limits remain: ambiguous initial partly executed pending volume, unsupported fill/protection/formula topologies, quota capacity and assembled real TLS/WebSocket/broker acceptance. Refer to the specific native references; do not weaken holds or infer residual volume. Official [runtime semantics](https://www.exness-api.com/trading/guides/runtime-semantics) were consulted through public documentation only; no client connector dependency or account authorization is introduced.

When the generated Dockerfile installs dependencies before copying the application, also copy `signal2copy_runtime/requirements.txt` before running pip if the main requirements file includes it. Keep old checkpoint identities and configured mode through an image update. Verify the served app version and restored checkpoint on the existing test target.
