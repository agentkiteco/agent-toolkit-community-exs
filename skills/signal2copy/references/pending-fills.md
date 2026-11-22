# Pending fills and residual exposure

Current full-target.md wins over historical evaluated-slice limits. These rules generalize across both copying modes using each mapping's recorded sizing; fixture examples are not live-broker guarantees.

## Required behavior

- A reserved position_id on a placed entry, without an actual position or executed deal, does not establish a fill. Do not fabricate a position or send a market opening.
- Correlate placement ownership using the exact account/request/operation result. Then use order_id and position_id from published broker orders/deals to link fills. Similar instrument, direction, price or volume is insufficient.
- Full execution creates exposure at the broker. The application must adopt that exact owned exposure without opening it again. Observed example: Buy Limit 0.08 fills on both accounts; source 0.08→0.05 causes one exact target close of 0.03, and source closure closes the remaining 0.05.
- Partial executions keep executed exposure separate from the unexecuted entry. Observed Sell Stop 0.10 fills 0.04 then 0.02 into the same linked position: exposure becomes 0.06, residual becomes 0.04, with no market top-up. Accumulate unique deal volumes; replay of the same deal must not increase executed volume again.
- While a linked residual remains active, the baseline reports pending_fill and defers volume adjustment of the filled group. In the observed case source exposure falls 0.06→0.04; target stays 0.06 and the residual stays 0.04. Do not apply the ordinary completed-position reduction rule to this state.
- Pause cancels only the owned target residual. It preserves filled exposure (0.06 in the example), reports review, and continues to exclude new entries. A further source reduction to 0.02 does not silently resize that held group. This is scoped baseline behavior, not a claim about every already owned market position.
- Explicit Stop closes the owned filled exposure and leaves source positions/residuals and manual target exposure untouched. An applied close with a lost response remains unresolved until exact result evidence; restart must preserve the session/correlation, send no duplicate close and permit completion after that evidence arrives.
- When filled positions appear but terminal orders have no position links and deal links are unavailable, do not guess ownership or open replacement positions. A source close during that ambiguity does not authorize closing a similar target position. After exact links arrive, close only the linked copied exposure, once, without a market opening.
- Expose pending_fill and review through the application API; native names may differ if documented. Preserve per-command request correlation and distinguish unresolved from confirmed effects.
- Treat an owned residual and its exactly linked filled child as one uncertainty group. Unknown residual cancellation blocks child trade effects after restart as well as before it. A missing active residual is not a terminal cancellation result. Preserve exact executed anchors and the original command until late correlated evidence resolves it; retained explicit Stop may then close only the owned child once. See [native pending recovery](native-pending.md#partial-fill-recovery-as-one-group).

## Fixture v4 execution convention

Application routes and account identities extend protocol v3. The bundled sizing entrypoint advertises protocol5 and inherits these v4 controls. The fixture does not implement application decisions or automatically copy/fill the investor account. The operator explicitly selects each account's executions.

For these bounded experiments, a partially executed order remains state=placed with volume equal to its **unexecuted residual**. A fully executed order is state=filled, volume=0 and absent from active orders. This is an explicit fixture convention: the local API schema describes volume only as "Order volume" and does not enumerate partially_filled. Do not infer live Exness volume semantics from this fixture.

Each fill generates a unique open deal containing deal_id, order_id, position_id, direction, instrument, volume, price and create_time. An event publishes order/position/deal changes. Published history contains the same exact deals; repeated reads/events must not double-count them. The root /history endpoint retains its synthetic legacy readiness sample and is not complete P/L history. /history/deals is the execution history used for exact linkage.

GET /history/deals accepts timezone-aware from_time/to_time, deal_type and limit. This experiment has fewer than 200 deals; overflow returns an error rather than a false complete page. Full pagination and reporting are not modeled.

## Operator-only controls

These controls require the separate control port and bearer token. They are scenario inputs, never application-facing capabilities. Each action runs under the broker lock.

| Action | JSON body | Effect |
| --- | --- | --- |
| POST /reserve | account, id (order), position_id | Publish reserved link without creating a position/deal |
| POST /fill | account, id, position_id, volume; optional publish_link=false | Execute an exact increment, leave residual or finish order |
| POST /fill-batch | fills: list of /fill bodies | Apply all executions atomically or roll back invalid batch |
| POST /release-links | empty object | Publish held exact order/deal links; no new execution |

Explicit execution may create a new position or add volume to the same position from the same order. It refuses merging an unrelated manual position. Hidden-link mode publishes actual positions and terminal orders without position links, withholding the deal from both events and history until release. Closing an executed position does not cancel or resize its independent residual entry. This slice places pending entries without protective levels; protective trigger execution is outside it.

## Build and verify this increment

Use the existing app's pending placement mapping and durable command journal. Add exact fill observation before enabling completed-position management; do not build another copying engine. Persist unique account/deal IDs and source/target order-to-position links so restart and repeated polling cannot adopt twice. Reconcile pending entries before discovering new market positions in the same observation; otherwise the newly filled source can be copied twice. A reserved link without execution must remain eligible for normal pending edits/cancellation.

Verify through native application requests and separate broker observations, keeping these outcomes distinct:

| Scenario | Required broker/application outcome |
| --- | --- |
| Reserved position ID | No exposure/no market open; later normal edit or cancel still works |
| Both entries fully fill | Adopt exact positions; no market open; source reduction/close manages only mapped target |
| Repeated partial fills | Unique-deal accumulation, residual separate, repeated reads/restart leave volumes unchanged |
| Partial-fill Pause | Cancel owned target residual, preserve filled/manual positions, hold the affected group for review |
| Hidden links then release | No guessed adoption/market replacement/closure; exact late links permit safe owned cleanup |
| Stop with lost close response | Stable request identity survives restart; no resend; exact late evidence settles cleanup and recomputes follow-up flags without another write |

Exercise at least one full-fill path in Proportional mode using unequal source/target lots; equal-lot1:1 evidence alone does not verify recorded sizing anchors. Keep source and target execution increments separate: the fixture never fills the investor automatically. Stop/restart the application while retaining the same broker process and state. Preserve original unresolved ledgers outside the new isolated test state.

Update both role guides with the actual pending_fill/review labels and Pause/Stop effects, including that Stopped with follow-up is not a flat-account guarantee. Record tests and missing topologies in BUILD_STATE. Locally accepted pending behavior does not establish that deployed code changed or that a real adapter understands a live broker's fill semantics.

## Limits

No price-trigger engine, broker matching simulation, real signatures/permissions, multi-position fills of one order, arbitrary fill asymmetry, partial-fill protection lifecycle, SL/TP trigger fills, manual-volume resolution, complete reporting, UI or Cloudflare deployment is proven here. Acceptance evidence is versioned separately from these requirements; do not infer that every listed behavior has run successfully or that a scoped continuation measures general build reliability.
