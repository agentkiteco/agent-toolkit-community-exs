# Sharing, disconnect and local owner management

Extend the same application and preserve existing role flows, history and unresolved execution evidence. Implement these as useful local increments with mocked broker data; live keys and production operations are not prerequisites. Do not import historical account-disconnect or reset authorizations into a new installation.

## F37: public strategy links

Provide one shared Copy strategy link component on authenticated provider/investor catalog cards and beside the strategy-detail title. Keep it a sibling of navigation controls, with a strategy-specific accessible label and title Copy strategy link. Allow card wrapping and keyboard navigation.

Construct only current origin + `/#strategy/` + encoded public strategy ID. Exclude the current query, private route, account data and secrets. Implement the public hash destination itself: after provider registration it must resolve published strategy details and preserve the selected strategy through investor sign-in. A correct clipboard string alone does not establish a usable destination. Keep anonymous catalog behavior unchanged.

Await clipboard `writeText` before showing Link copied for2.5seconds. Announce resolved success through an explicit live status region: changing inner text on a button with an unchanged aria-label may not announce success. Pending/rejected writes must not claim success. Missing/denied clipboard opens a selected read-only canonical URL with an English manual-copy instruction; Close/Escape dismisses the dialog and restores trigger focus. Copying must not navigate, subscribe, mutate settings, send messages or offer an unimplemented Share menu.

Verify clipboard pending/resolved/denied/missing cases, keyboard/focus behavior, sensitive dummy query exclusion and catalog/detail equality in a browser. Static served-code checks support integration only; they do not prove clipboard or assistive-technology behavior.

## F38: operator-assisted subscriber disconnect

Expose an authenticated owner-scoped DELETE operation for one exact subscriber account, without adding a disconnect menu button. Reject unauthenticated callers, foreign owners and provider source accounts. Require ended subscriptions and no unfinished root **or per-subscription commands**, unresolved intents, or queued/running execution jobs. Rejection must preserve all state.

Under the existing application lock, delete working encrypted credentials, mark disconnected, advance sync_id, revoke that owner's application sessions, audit and wake the executor. Fence both successful and failed in-flight refresh results so they cannot update disconnected state or resurrect access. Epoch/stop signals must reject late runtime events; retained gateways close on the executor's next tick. Test that worker boundary separately before claiming it works under concurrency.

Preserve account identity, subscriptions and their statuses, commands, mappings, financial/report/equity evidence and normal backup retention. Send no broker close/cancel/trading write. Ordinary refresh cannot reconnect. Later explicit key authentication may reuse historical identity but must require separate Connect and must not start copying automatically. Treat a specifically requested disconnect as a separate operator action, never acceptance cleanup.

## F41: separate owner console and safe local reset

Use independent owner password, session and durable job storage outside resettable application data. Provider authentication and standalone native owner-preview authentication must not grant console access. Keep its direct management URL separate from client navigation. Apply rate limits, idle expiry, exact-origin JSON mutations and HttpOnly/SameSite cookies with Secure on HTTPS. Hash panel passwords; rotating one requires the current password and revokes all panel sessions. Keep bootstrap credentials in private local tooling, never guides, APIs or shared evidence.

Show exact target, inventory, revision and job status without broker reads. Persist invitation overrides securely across restart/reset; changing an invitation does not reopen registered-provider onboarding. The independent panel password survives application reset.

For local reset, freeze the exact target and inventory revision under the application lock. Fence application mutations, unattended executor ticks, execution requests **before journal mutation**, and final broker dispatch; stopping only native read streams leaves synthetic execution unsafe. Require typed destructive confirmation and acknowledgment that automated management ends while broker exposure remains unchanged. Do not send broker close/cancel commands.

Persist an idempotent job phase before clearing. Commit an application-side job marker with the clear so a lost reply/restart can resume without repeating it. Clear declared application state and local snapshots, revoke application sessions, verify empty registration can reopen, then release the freeze. Retain technical configuration and independent console authentication. Describe retained external archives and storage limits accurately; do not promise forensic erasure. Any asynchronous local backup writer needs an explicit drain protocol too.

**Refuse cloud reset** until independent admin storage/service authentication, backup drain, storage epoch/restore fencing, remote snapshot deletion and verified resume are implemented. A local SQLite clear does not implement Cloudflare reset or independent cloud admin deployment. Never reset production as an acceptance or repair shortcut.

Use a focused generated-data walkthrough for ownership guards, settled/unfinished account cases, historical retention, explicit reconnect, independent sessions/password rotation, frozen execution, revision/confirmation checks and lost-response reset retry. Keep HTTP, offline dispatch checks, browser behavior, cloud operation and live broker evidence separate. Record only completed checks; leave remaining boundaries in BUILD_STATE and the role/owner guides.

For a local atomic owner-state file, fsync the containing directory after rename as well as the file before rename. The retained reset authorization, invitation/password and completed job need the same durable replacement discipline as application state. Orderly restart evidence does not certify a power-loss or mid-reset crash.
