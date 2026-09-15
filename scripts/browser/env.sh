# Where the browser harness finds Playwright. SOURCED by shoot.sh and crop.sh
# (`. scripts/browser/env.sh`), never run on its own.
#
# Two places, in this order (2026-09-15):
#   1. tmp/browser/ -- this worktree's own `sh scripts/browser/install.sh`. It
#      wins when present because somebody installed it on purpose: on a host
#      with no devcontainer, or while the image is older than the pin.
#   2. /opt/playwright -- the devcontainer image's copy (.devcontainer/Dockerfile),
#      so a fresh worktree can take a screenshot with no download at all.
# Neither: say what to run, and stop the calling script.
if [ -d "$PWD/tmp/browser/node_modules/playwright" ]; then
  PLAYWRIGHT_BROWSERS_PATH="$PWD/tmp/browser/ms-playwright"
  NODE_PATH="$PWD/tmp/browser/node_modules"
elif [ -d /opt/playwright/node_modules/playwright ]; then
  PLAYWRIGHT_BROWSERS_PATH=/opt/playwright/ms-playwright
  NODE_PATH=/opt/playwright/node_modules
else
  echo "no Playwright in tmp/browser/ or the image: run sh scripts/browser/install.sh" >&2
  exit 1
fi
export PLAYWRIGHT_BROWSERS_PATH NODE_PATH
