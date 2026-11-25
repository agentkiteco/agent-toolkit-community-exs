#!/bin/sh
# Copy the template to a target folder and fill in placeholders.
# Usage: configure.sh <target_dir>   with env vars:
#   PARTNER_NAME  BRAND_NAME  OWNER_EMAILS  APP_WORKER  D1_NAME
#   D1_ID (optional, fill later)  ACCESS_TEAM_DOMAIN (optional)  ACCESS_AUD (optional)
set -e
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="$1"
[ -n "$TARGET" ] || { echo "usage: configure.sh <target_dir>"; exit 1; }
[ ! -e "$TARGET/cloud/app/wrangler.toml" ] || { echo "refusing: $TARGET already configured"; exit 1; }
: "${PARTNER_NAME:?}" "${BRAND_NAME:?}" "${OWNER_EMAILS:?}" "${APP_WORKER:?}" "${D1_NAME:?}"
mkdir -p "$TARGET"
cp -R "$SKILL_DIR/template/." "$TARGET/"
esc() { printf '%s' "$1" | sed -e 's/[\/&|]/\\&/g'; }
for f in "$TARGET/cloud/app/wrangler.toml.tpl" "$TARGET/static/index.html" "$TARGET/start-local.sh"; do
  sed -i.bak \
    -e "s|__PARTNER_NAME__|$(esc "$PARTNER_NAME")|g" -e "s|__BRAND_NAME__|$(esc "$BRAND_NAME")|g" \
    -e "s|__OWNER_EMAILS__|$(esc "$OWNER_EMAILS")|g" -e "s|__APP_WORKER__|$(esc "$APP_WORKER")|g" \
    -e "s|__D1_NAME__|$(esc "$D1_NAME")|g" -e "s|__D1_ID__|$(esc "${D1_ID:-__D1_ID__}")|g" \
    -e "s|__ACCESS_TEAM_DOMAIN__|$(esc "${ACCESS_TEAM_DOMAIN:-}")|g" -e "s|__ACCESS_AUD__|$(esc "${ACCESS_AUD:-}")|g" "$f"
  rm -f "$f.bak"
done
mv "$TARGET/cloud/app/wrangler.toml.tpl" "$TARGET/cloud/app/wrangler.toml"
chmod +x "$TARGET/cloud/app/build.sh"
echo "Configured $TARGET"
grep -rn "__[A-Z0-9_]*__" "$TARGET/cloud/app/wrangler.toml" "$TARGET/static/index.html" || echo "No placeholders left."
