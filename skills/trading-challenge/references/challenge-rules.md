# Exness Trading Challenge: Contest rules

## Entry readiness and period

Open entries only after organizer OAuth has successfully read the Partner client-account report and the necessary API profiles are configured. Password login, saving settings, token issuance, and default-link access are not equivalent checks. A valid empty report proves API access but admits no participant.

Configured API profiles include the trusted issuer, role scopes/resources, Trading discovery gateway, and a valid exact-origin trust policy. An explicitly empty AP allowlist is valid initial configuration. Reject missing or malformed API profiles and broad or invalid trust rules; do not define profile readiness as having at least one approved account server.

After organizer verification, make Open entries available when the period and management authorization permit it. Keep Open/Pause under organizer control. Opening registration allows traders to authorize and submit applications; it does not approve their accounts or create ranked results.

AP discovery requires the selected trader's own Trading grant. Requiring that account-specific server before allowing trader OAuth creates a circular dependency. Do not require a trader to join first, an approved AP, or the organizer's personal Trading authorization as a prerequisite for opening registration.

During application verification, discover the exact AP with the trader's grant. An unapproved origin leaves only that application pending. Record minimal sanitized origin/check evidence in protected operator diagnostics; do not send it account credentials or request account details, limits, or history. The operator independently verifies and configures the exact origin, after which the saved application can be retried through all eligibility checks. Discovery never approves the origin automatically or authorizes a wildcard trust rule.

Provide a retry path for that saved, consented application. Under the shared application lease, transition pending back to checking before the conditional admission commit, and rerun the complete normal checker. Keep the original trader grant and session binding. An operator-triggered retry is not manual approval, and it cannot override paused/ended entries, changed authorization, ineligible account data, or incomplete checks. See [AP recovery](connection-preflight.md) for the operator procedure.

Bind readiness to the current owner authorization, issuer, resource, relevant configuration, and successful check time. A new owner grant, changed permissions/profile, or confirmed permission loss requires rechecking. Temporary failures do not prove revocation, but cannot justify an unverified new admission. A trader failure does not reset another valid organizer.

Store UTC instants while displaying the organizer's local dates/timezone. Include deals at the start and exclude deals at the end. Admission stops at the end even if a check began earlier. Late entrants may count eligible deals from the contest start only if the complete period can be verified.

## Automatic admission

1. Check entry readiness, end boundary, valid nickname, consent, and a server-bound personal trader grant. Start or resume a pending application without a rank.
2. Fetch a fresh Partner report with the organizer's OAuth grant. Match the exact selected trading account, including later pages. Preserve consistent paging/filter/order settings and do not add activity/date/campaign filters that exclude referrals. A valid matching page can establish membership; absence requires a complete valid scan. An incomplete scan remains pending rather than falsely absent.
3. With that trader's grant, discover and validate the account-specific AP, then read account details. Match identity when returned, require confirmed boolean real status, and check canonical USD currency as described in the API profile. Neither organizer credentials nor another trader's grant can substitute.
4. Retain minimal check evidence, timestamps, and nonsecret authorization/configuration versions. Avoid retaining the organizer's full client list or raw private responses.
5. Admit atomically after rechecking entry state, end, ownership, and the checked authorization/configuration versions. Enforce account uniqueness per contest and prevent a different session from replacing an existing participant's grant. Normal token rotation does not count as a new owner.

There is no discretionary approval queue for a fully verified eligible account. OAuth success, eligibility approval, and the first complete ranked result remain separate stages. A pending or ambiguous check is not a manual approval opportunity. Imports, retries, and organizer actions must not bypass the same rules.

## Exact score and ranking

The score is the exact decimal sum of deal.profit.amount in USD for deals whose type is close, from the inclusive start to the earlier of now and the exclusive end. Exclude balance operations, deposits, withdrawals, open/unrealized PnL, and additional costs outside that defined metric.

Do not round values before ranking or substitute ROI, balance, equity, volume, or trade count. Equal exact scores share ranks, such as first, first, third. A stable display order among ties does not decide prizes or award an advantage.

Confirm USD account and deal currency. Deduplicate by deal identity within an account. Handle negative results and confirmed zero correctly. A fully verified empty elapsed interval may equal zero; an error or missing history may not.

Before start, do not request future history or represent future results as active performance. After end, verify coverage to the exact final boundary before announcing final winners.

## Limits, pagination, and coverage

Read each account's current limits, including history range, history age, and method/account quotas. Missing limits are not unlimited access. Split the required interval into permitted windows, fetch every page, follow only supported cursor parameters, and enforce exact event-time boundaries locally.

Pagination cannot bypass history age. Assess late entrants individually. If complete coverage is unavailable, retain an unranked state or the previous complete result with an explicit delay. Explain the unavailable period; never silently move dates or publish a partial total as final.

Persist verified deals or exact aggregates with sufficient coverage metadata to survive age-out and resume interrupted work. Overlap incremental reads and deduplicate. A gap must remain visible until it is genuinely resolved.

## Autonomous refresh

Use a server-side minute schedule with a shared database lease to prevent overlap. Browser polling reads published snapshots and is not the updater. Cloudflare Cron runs independently of the organizer's computer; local operation depends on the server process remaining active.

Read approved participants before preparing credentials or calling Exness. With none, report a no-participants outcome without refresh, discovery, or history calls and without inventing a successful calculation timestamp. Organizer access verification is separate from an empty refresh run.

Respect per-account, per-method, and shared budgets plus Retry-After and traffic from other applications. Distinguish actual upstream rate limits from local backoff. A tick that only waits for a deadline must not extend it or advance freshness. Coordinate or stagger shared-account pollers when necessary.

Renew only the affected grant under the OAuth rules. Preserve prior complete results for temporarily failing or disconnected traders with their true timestamps and delayed status. The organizer's grant cannot replace a missing trader grant.

Persist partial work for continuation, but publish a total only after complete verification. Commit a coherent snapshot atomically; a database publication failure retains the previous snapshot. Advance participant freshness and completed-calculation time only after successful relevant fetch and publication, even when the numeric result is unchanged.

Use the same snapshot, ranks, and freshness for podium and table. Previously complete stale results may remain in provisional standings if clearly marked; participants without a complete result have no rank. Finalization remains pending while gaps or missing grants prevent full final coverage. Stop unnecessary reads once results are finalized.
