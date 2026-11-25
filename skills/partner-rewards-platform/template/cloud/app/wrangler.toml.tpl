# Credential-enabled studio: UI + API. Requires an external owner-only hosting access boundary.
# The hosted entry point has no application login and no payment cron.
name = "__APP_WORKER__"
main = "../../hosted/worker.js"
compatibility_date = "2026-11-01"
workers_dev = false
preview_urls = false

[[d1_databases]]
binding = "DB"
database_name = "__D1_NAME__"
database_id = "__D1_ID__"

[vars]
EXN_API_HOST = "api.exness.com"
ALLOWED_EMAILS = "__OWNER_EMAILS__"
ACCESS_TEAM_DOMAIN = "__ACCESS_TEAM_DOMAIN__"
ACCESS_AUD = "__ACCESS_AUD__"

[observability]
enabled = true
