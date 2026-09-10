#!/bin/sh
# A headless Chromium for looking at the built site -- MANUAL §1.
#
# Installs Playwright and its Chromium ENTIRELY under tmp/browser/ (gitignored),
# Helen's grant of 2026-09-10: nothing lands in ~ or on the system. The system
# libraries Chromium links against are in the devcontainer image since the
# same day (.devcontainer/Dockerfile); on a host without them the launch names
# the missing packages and stops.
#
#   sh scripts/browser/install.sh        # once per fresh tmp/
#   sh scripts/browser/serve.sh          # serve tmp/site at 127.0.0.1:4010, in the background
#   sh scripts/browser/shoot.sh <label> <path>...   # screenshots + overflow report
#   sh scripts/browser/crop.sh <path> <selector> <name> [width]   # one element at 2x
set -e
mkdir -p tmp/browser
cd tmp/browser
export PLAYWRIGHT_BROWSERS_PATH="$PWD/ms-playwright"
export npm_config_cache="$PWD/npm-cache"
if [ ! -f package.json ]; then
  npm init -y >/dev/null
fi
npm install --no-audit --no-fund playwright@1.47.2
npx playwright install chromium
echo "BROWSER_READY"
