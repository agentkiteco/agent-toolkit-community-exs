#!/bin/sh
set -eu
cd "$(dirname "$0")/cloud"
npm ci
cd ..
node scripts/build-hosted.mjs
cd cloud/app
../node_modules/.bin/wrangler d1 execute __D1_NAME__ --local --file schema.sql
if [ ! -f .dev.vars ]; then
  umask 077
  node -e 'process.stdout.write("STUDIO_CREDENTIALS_KEY="+require("node:crypto").randomBytes(32).toString("hex")+"\n")' > .dev.vars
fi
exec ../node_modules/.bin/wrangler dev --ip 127.0.0.1 --port 8790 --inspector-port 9230
