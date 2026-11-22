# Signal2Copy owner operations

Draft: replace authoring instructions with the generated app's exact target, paths, commands and executed evidence. Keep keys/tokens/invitation outside this guide in a private ignored0600file. Do not publish a local secret file or imply untested recovery works.

## Installation and updates

Record recipient Account ID, new Worker/origin/bucket, config path, pinned tool/runtime dependencies and dry-run/deploy commands. Before publishing verify target collision/authorization. Preserve original encryption/bridge/operations keys on updates; never regenerate to repair an existing installation. Give app startup/health and actual deploy result, not only an uploaded-image message.

## Durable state and backups

Explain restore-before-execution, semantic commit acknowledgement and stale revision/instance fencing. Check authenticated status, checkpoint/backup revisions, image and failed-ack hold. Back up changed state encrypted; a backup is distinct from acknowledged primary durability. State the actual storage/size/retention limits and independently verified nonempty restore scope.

The initial scaffold uses separate OPS_TOKEN for /__ops/status, /backup, /restart and /restore; BRIDGE_TOKEN is not an owner token. Retain secrets privately, never in URLs or sample commands. Exact-revision R2 restore requires expected revision, backup key, RESTORE <worker> and broker-exposure acknowledgment. It advances revision, never rolls a trade journal back. Older/catastrophic lost-primary restore is unaccepted until a separate safe reconciliation workflow exists.

## Verify and recover

Compare nonempty identifiers/settings/intent after cold process recreation with the original key. If acknowledgement/restore fails, leave dispatch fenced and inspect authoritative state. A restarted empty synthetic broker cannot resolve retained unknown exposure. Do not infer flat positions from Stopped, restored UI or missing snapshot entries. No production reset or real-broker order is an installation diagnostic.

## Handoff status

List local lifecycle, offline signing, cloud bridge, actual generated app deployment, backup/restore and real broker checks separately. Supply actual provider/investor guide links and remaining M2/M3/M4 work. Record whether idle containers sleep and active/paused management keeps them alive; no browser/Codex process should be needed for the server executor.

## Independent owner state

Describe bootstrap OWNER_PASSWORD, retained/rotated authentication and invitation, and separate encrypted cloud admin storage/backups. Preserve them and the original state key during app reset and image updates. Record local populated restart, remote owner-only restore, remote populated-business restore and cloud reset as separate outcomes. Never promote infrastructure hooks or an orderly local reset into a remote/crash acceptance claim.


When native execution is implemented, document the actual installation capability selection and its supported cases. Preserve existing sealed read-only state rather than silently enabling it. Configuration alone is not trade consent: normal Start and all per-effect checks remain mandatory. Clearly distinguish generated-I/O acceptance from real broker acceptance. Use only an authorized recipient target and private inputs; skill updates do not enable existing live installations.
