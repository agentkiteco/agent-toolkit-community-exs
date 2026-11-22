# Exness Trading Challenge: Organizer access

## User experience

The organizer opens `/organizer`, enters the contest password, and selects Sign in. On first connection, the organizer selects Connect Exness and personally approves read-only Partner access. Successful report verification makes the contest eligible to accept participants.

Once the organizer is verified and the API profile is valid, enable Open entries even when no trader-specific AP has been discovered or approved yet. Keep the verified connection status intact. An empty valid allowlist alone must not produce a global operator-configuration warning or disable registration. The organizer does not need a personal Trading grant to manage the contest. Each trader's separate server and eligibility checks occur during their application, as described in [Contest rules](challenge-rules.md).

A returning organizer signs in through the same password form. Reuse a valid saved Exness authorization instead of forcing OAuth on every visit. Reconnect only when required. Cookie loss or session expiry leads back to the password form.

Keep the interface simple: password field, Sign in, clear errors, Connect Exness, connection status, entry controls, View contest, and Sign out. Do not require a terminal, Wrangler, launcher, secret URL, setup fragment, copied OAuth token, or API configuration from the organizer.

## Password and role enforcement

The password authorizes contest management; OAuth separately authorizes Exness reads. Password success alone cannot fabricate a grant, open initial entries, admit a trader, or generate results.

The deployment operator configures a unique contest password through a private secret workflow. Store a salted verifier from an established password-derivation method compatible with the runtime. Keep the verifier in a Worker secret in production and excluded private storage locally. Do not embed a real default password or request plaintext passwords in chat, command arguments, or logs.

There is no public first-visitor password setup or organizer registration route. OAuth alone cannot turn an arbitrary Partner into the owner. A password-authenticated session may bind its verified Partner grant, and a later authorized login may reuse the currently bound owner grant. Deliberate rebinds require both management authorization and a fresh Partner-access check.

Verify the password on the server. Apply distributed attempt limits that cannot be bypassed by changing cookies or Worker instances. Rotate the opaque session identifier and CSRF token on successful login. Use HttpOnly, Secure, SameSite Lax cookies with bounded lifetime; four hours is a suitable initial management-session policy.

Enforce current password-session authorization on organizer OAuth initiation/callback and every management endpoint. Hiding controls is not authorization. Reject forged roles, missing configuration, obsolete bootstrap routes, and replayed setup links.

Bind management sessions to the password-verifier revision so rotation invalidates old organizer access without deleting OAuth grants, participants, or results. Check validity again before privileged commits and code exchange when relevant.

## Logout, recovery, and messages

Sign out removes the management session and its outstanding attempts. Background result updates continue using consented grants. Disconnect Exness is a separate explicit action that stops that grant's future refresh and reads.

Forgotten-password recovery is private operator-assisted rotation, followed by ordinary web login. Never reset the contest database or replace the vault key to recover website access.

Use plain messages for an incorrect password, expired session, or temporary attempt limit. If no valid verifier is configured, show that organizer access is not ready and refuse authentication. Do not fall back to a default credential or a setup link.

Keep mock credentials and mock grants strictly within an offline local preview. They must not authorize connected Production sessions or real management APIs.
