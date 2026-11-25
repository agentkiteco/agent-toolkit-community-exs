# Hosting and access

## Sites

Use the installed Sites workflow for source registration, repository access, packaging and publication. Read its current instructions instead of copying internal tool schemas into this skill.

- Start a new project unless the user identified an existing one; preserve an existing project ID on updates.
- Set `.openai/hosting.json` to the returned project ID, `d1: "DB"`, and `r2: null`. Do not set `static`: this is a server-backed Worker.
- Build with `node scripts/build-hosted.mjs`. The output is `dist/server/index.js`; its HTML, CSS and JS assets are bundled server-side. Keep the source manifest in the deployment artifact.
- Include `drizzle/0000_initial.sql` and `drizzle/meta/_journal.json` in source and package migrations through the supported hosting helper. Never regenerate an already-applied migration.
- Configure `STUDIO_CREDENTIALS_KEY` as a secret before deploying, without logging it. Reuse it across versions. Never place it in source or the hosting manifest.
- Confirm owner-only access **before exposing Settings or real partner data**. Use private deployment only for verified owner-only Sites. If a user changes access to public, do not silently deploy this shared credential store publicly. Explain the conflict and retain the private credential-enabled app; a public version needs a separate design with isolated accounts and authorization.
- Do not inspect `oai-authenticated-user-id` or add another app login in this single-owner version. The platform's private access policy is the boundary; therefore this Worker must not be deployed as a public endpoint.
- Preserve source identity and archive correspondence; use the platform's normal save/deploy flow. Respect pending and terminal status handling.

## Required unattended scheduling

Follow `background-qualification.md`. A successful deployment only proves publication, not scheduler registration or source access. Use a scheduler actually supported by the selected hosting platform and verify a run through its intended unattended authorization.

For Sites, read its current recurring-updates and identity/service-access instructions. Confirm that the supported scheduling mechanism can meet the required cadence. Do not assume `wrangler.toml` cron settings are deployed by Sites, or that exporting `scheduled` enables a timer. If the available platform cannot meet the requirement, explain the constraint and implement a supported equivalent or identify the account action needed; do not drop the feature. Do not create a chat reminder as a substitute for backend qualification. Avoid duplicate schedules and preserve paused state when updating an existing one.

For direct Cloudflare Workers, register and deploy `crons = ["* * * * *"]` and a `scheduled` handler that loads the same encrypted Settings credentials and invokes only the qualification runner. Verify the real trigger and persisted result. Keep the owner-only access boundary for HTTP routes; a native scheduled event is separate from browser authentication.

## Direct Cloudflare hosting

Use only when explicitly requested or Sites is unavailable. The bundled Worker assumes an external access boundary. Protect it with owner-only Cloudflare Access or another verified equivalent **before** exposing the credential form. Do not publish the authentication-free Worker on an open workers.dev URL. Do not claim direct hosting provides the same boundary automatically.

## Local

Use loopback-only Wrangler for the hosted entry point. Apply the schema locally and generate a local `STUDIO_CREDENTIALS_KEY` if missing. Never overwrite an existing local encryption key or `.dev.vars`. Managed preview must use the environment's supported launch and forwarding route; do not ship environment-specific relays as production code.
