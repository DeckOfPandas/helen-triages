#!/bin/sh
# A headless Chromium for looking at the built site -- MANUAL §1.
#
# IN THE DEVCONTAINER THIS USUALLY DOES NOTHING, SINCE 2026-09-15. The image
# carries Playwright, its Chromium and Chromium's system libraries under
# /opt/playwright (.devcontainer/Dockerfile), and scripts/browser/env.sh finds
# them there. This script checks that copy is the pinned version and stops.
#
# Otherwise -- on a host, or in an image built before the pin moved -- it
# installs Playwright and its Chromium ENTIRELY under tmp/browser/ (gitignored),
# Helen's grant of 2026-09-10: nothing lands in ~ or on the system. On a host
# without Chromium's libraries the launch names the missing packages and stops.
#
# THE VERSION IS PINNED HERE AND IN THE DOCKERFILE; tests/test_browser_harness.py
# fails if they differ.
#
#   sh scripts/browser/install.sh        # once per fresh tmp/, and only outside the image
#   sh scripts/browser/serve.sh          # serve tmp/site at 127.0.0.1:4010, in the background
#   sh scripts/browser/shoot.sh <label> <path>...   # screenshots + overflow report
#   sh scripts/browser/crop.sh <path> <selector> <name> [width] [type-into] [text]   # one element at 2x, after typing
set -e
version=1.47.2

image=/opt/playwright/node_modules/playwright/package.json
if [ -f "$image" ] && grep -q "\"version\": \"$version\"" "$image"; then
  echo "Playwright $version is in the devcontainer image (/opt/playwright); nothing to install."
  echo "BROWSER_READY"
  exit 0
fi
if [ -f "$image" ]; then
  echo "The image's Playwright is not $version -- rebuild the devcontainer image. Installing $version into tmp/browser/ meanwhile."
fi

mkdir -p tmp/browser
cd tmp/browser
export PLAYWRIGHT_BROWSERS_PATH="$PWD/ms-playwright"
export npm_config_cache="$PWD/npm-cache"
if [ ! -f package.json ]; then
  npm init -y >/dev/null
fi
npm install --no-audit --no-fund "playwright@$version"
npx playwright install chromium
echo "BROWSER_READY"
