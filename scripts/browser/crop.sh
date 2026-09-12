#!/bin/sh
# Screenshot one element of a served page at 2x, for looking closely.
# Usage: sh scripts/browser/crop.sh <path> <css-selector> <name> [viewport-width]
# Output: tmp/shots/crop-<name>.png
#
# The port comes from tmp/browser/port, written by this worktree's serve.sh
# (2026-09-11) -- see shoot.sh for why. 4010 only when no server is running here.
port=4010
if [ -f tmp/browser/port ]; then
  read -r port < tmp/browser/port
fi
mkdir -p tmp/shots
export PLAYWRIGHT_BROWSERS_PATH="$PWD/tmp/browser/ms-playwright"
export NODE_PATH="$PWD/tmp/browser/node_modules"
node scripts/browser/crop.js "http://127.0.0.1:$port/helen-triages$1" "$2" "tmp/shots/crop-$3.png" "$4"
