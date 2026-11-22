# Native pending entries and fills

Extend the existing native executor, journal, sizing and position-management paths. Keep production writes denied while exercising generated-key native-shaped traffic through a separate test policy. This reference specifies implementation decisions; acceptance evidence belongs to the delivered build, not to these instructions. Read [pending-fill behavior](pending-fills.md) for the functional outcomes and its explicitly synthetic fixture convention.

## Placement and management

Evaluate the actual fresh source order and its account/instrument conditions. Do not inject a fake source position to bypass a position-only preflight. Support buy/sell combined with limit/stop, preserving source price and supported SL/TP. Use the documented [pending placement](https://www.exness-api.com/reference/trading/place-pending-order) request variant, current target sizing and price precision. Keep source order and source position identifiers in separate namespaces.

Baseline pre-existing orders at Start unless the selected include-current policy actually supports them. Resume must not replay entries observed during Pause. Record the source order observation, calculated target volume, exact request and operation identity durably. Require correlated final target order evidence before adopting its order ID; a returned ID or operation-confirmed status alone does not establish an executed position.

Modify price and levels through the exact owned order using [PATCH](https://www.exness-api.com/reference/trading/modify-order). Omitted levels are unchanged; null removal is explicit. Source cancellation, Pause and Stop may [cancel](https://www.exness-api.com/reference/trading/cancel-pending-order) only the confirmed owned residual. Require exact terminal cancellation evidence. Unknown placement/edit/cancel commands remain serialized and are not resent after restart or replaced by a fresh request.

## Executions are separate from residual entries

The native order enum has pending_new, placed, filled, cancelled and rejected; do not invent a partially_filled enum. Public Order.volume does not establish whether a partial execution leaves initial or residual volume. Use active order existence/state to track a remaining entry and uniquely identified open deals to establish executed volume. Never subtract fills from an ambiguous Order.volume to authorize a mutation. Initial placement requires a supported fresh unfilled source observation; ambiguous earlier execution remains held.

Deduplicate deals by account and deal ID. Attribute each to the exact owned order and position; instrument/side/price similarity is insufficient. A reserved position_id without executed evidence is not a fill. Persist observed deal identities and links. Reconcile pending groups before ordinary source-position discovery so a newly filled source cannot trigger a replacement market open. Never top up a partial execution with a new market order.

Missing links can occur while the residual still appears placed. Do not treat that state as evidence that a newly appeared same-instrument position is an independent market signal. Hold ambiguous candidates until exact origin is established. Preserve enough baseline order identity to exclude its later fills under new-only scope, including after restart; lack of an owned target order does not make a baseline source fill eligible.

Start with one exact filled position per order. Multiple position links, missing links or unsupported source/target fill asymmetry require a visible review hold. Preserve known group identity even while links are missing; late exact evidence may establish ownership without authorizing an earlier guessed trade. Once a supported group completes, retain actual executed source/target anchors and pass it to existing anchored position management. While the residual is active, defer ordinary proportional reductions as required by the baseline.

Pause cancels the owned target residual and preserves the filled exposure for review. Stop retains cleanup intent and closes only exactly attributed exposure after prior unknown commands resolve. Never touch source residuals, manual target orders or similar unowned positions. A stopped session with unresolved cleanup is not a flat-account guarantee.

## Partial-fill recovery as one group

Keep execution evidence, residual state and command outcome separate. Persist the original planned quantities, unique source/target deals, cumulative executed anchors and exact order-to-position links. Repeated polling must not add a deal twice. Fill reconciliation must not overwrite an unknown cancellation with pending_fill or resurrect a confirmed cancelled residual merely because the source residual remains active.

Serialize effects across the related order and its exactly linked filled position, rather than checking unresolved commands only on each individual mapping. An unknown residual placement/edit/cancellation blocks related child trade effects, including Stop cleanup. Check that relationship again at final dispatch; exclude the current reserved command from its own uncertainty check. Independent groups need not be blocked.

An app-only restart retains this group, original request identity, desired lifecycle and review state. Require fresh synchronized observations before management; absence of the residual from a new snapshot does not prove the old cancellation succeeded. Do not create a replacement pending order or market top-up. After exact late cancellation evidence settles the original command, an explicit retained Stop may close the verified child once. Pause keeps the executed exposure for review instead of silently resuming ordinary resizing.

For the investor, show executed lots separately from residual state and distinguish cancellation awaiting confirmation, preserved exposure and cleanup waiting. Offer only actions actually implemented by the app. A numeric residual requires established broker semantics; the fixture's residual-volume convention is insufficient for a native claim.

## History and final boundaries

[Native order history](https://www.exness-api.com/reference/trading/get-orders-history) contains finalized orders, not the active-order inventory. Use synchronized snapshots for active entries and bounded [native deal history](https://www.exness-api.com/reference/trading/get-deals-history) for recovery. Respect returned method-specific history age/range limits; an omitted limit is unknown, not permission for an invented unlimited scan. Cursor continuation uses only the documented cursor and page limit. A bounded response does not prove absence outside the covered interval.

Recheck source order semantics, target residual/position ownership, stream generation, permissions and durability after slow reads and durable reservation, immediately before transport. An altered or ambiguous observation defers the effect. Preserve the original unknown command and its evidence through restart; exact late results may resolve it before a fresh decision is considered.

The [runtime semantics guide](https://www.exness-api.com/trading/guides/runtime-semantics) distinguishes active snapshots from finalized history and states that transaction events contain changed entities only. Reconnection requires a fresh snapshot; it does not provide durable event replay. Preserve previously verified fill links rather than expecting old fill events to reappear. A missing event may still require bounded history recovery; this partial-fill scenario does not establish general gap recovery.

For full executions missed while the app was offline, [known-order history recovery](native-recovery.md#lost-fill-events-for-already-owned-pending-entries) describes a bounded positive-evidence path, including previously retained exact partial executions. Preserve those deals and deduplicate their union with new history; do not erase them because the broker did not return them again. Keep fill recovery separate from unknown command resolution. The current snapshot alone cannot establish a lost fill's ownership.

## Acceptance and guides

Use focused application-level cases for all four entry variants, exact price/level edits, cancellation, reserved IDs, full fills with unequal sizing anchors, repeated unique partial fills, Pause residual cancellation, Stop/restart/lost acknowledgement, missing/late links and unrelated exposure preservation. Inspect actual broker effects and absence of replacement market requests. Keep fixture controls outside application routes.

Choose only the checks relevant to the agreed increment; the list above is a staged coverage map, not a requirement to rerun every case for each release. For a bounded partial/recovery increment, use one continuous generated-data walkthrough: place unequal-sized source/target entries, fill each independently with unique increments, Pause with an applied cancellation whose exact result is held, restart only the app against the same broker, synchronize and request Stop, verify no child close while cancellation is unknown, then release its exact result and observe one owned close. Inspect the broker ledger and preserve same-symbol manual exposure and the entire source account. Record which topology and transport were actually exercised.

Pending placement is an order result, not an entry-fill price. Report actual requested quantities for placement and no invented quantity/entry average for edit or cancellation; derive fill metrics from exact execution evidence. Update current provider/investor guides and BUILD_STATE with supported labels, holds and remaining limits. Distinguish mocked protocol acceptance from live mutations, final cloud deployment and clean independent reconstruction.
