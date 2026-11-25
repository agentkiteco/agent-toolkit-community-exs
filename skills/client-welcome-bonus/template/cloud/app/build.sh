#!/bin/sh
# Copies the shared UI (../../static) into public/ for Workers Static Assets.
set -e
cd "$(dirname "$0")"
rm -rf public && mkdir -p public/static
# Cache-bust app.js / styles.css so browsers pick up each new build.
V=$(cat ../../static/app.js ../../static/styles.css | shasum | cut -c1-10)
sed -e "s#/static/app.js\"#/static/app.js?v=$V\"#" -e "s#/static/styles.css\"#/static/styles.css?v=$V\"#" ../../static/index.html > public/index.html
cp ../../static/app.js ../../static/styles.css public/static/
