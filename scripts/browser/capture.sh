#!/bin/sh
# The whole design-review screenshot set, from this worktree's served build:
# every page type and state of both sites at three widths. No arguments:
#   sh scripts/browser/build.sh
#   sh scripts/browser/serve.sh      (in the background)
#   sh scripts/browser/capture.sh
# Output: tmp/shots/capture/, PNGs plus index.md, the manifest.
#
# It takes no arguments, so its allow rule can be the exact command. It reads
# only the local server and git, and writes only under tmp/shots/capture/.
set -eu
if [ ! -f tmp/browser/port ]; then
  echo "no tmp/browser/port: start this worktree's sh scripts/browser/serve.sh first" >&2
  exit 1
fi
read -r port < tmp/browser/port
commit=$(git rev-parse --short HEAD)
mkdir -p tmp/shots/capture
. scripts/browser/env.sh
exec node scripts/browser/capture.js "http://127.0.0.1:$port/helen-triages" tmp/shots/capture "$commit"
