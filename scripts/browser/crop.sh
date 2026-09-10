#!/bin/sh
# Screenshot one element of a served page at 2x, for looking closely.
# Usage: sh scripts/browser/crop.sh <path> <css-selector> <name> [viewport-width]
# Output: tmp/shots/crop-<name>.png
mkdir -p tmp/shots
export PLAYWRIGHT_BROWSERS_PATH="$PWD/tmp/browser/ms-playwright"
export NODE_PATH="$PWD/tmp/browser/node_modules"
node scripts/browser/crop.js "http://127.0.0.1:4010/helen-triages$1" "$2" "tmp/shots/crop-$3.png" "$4"
