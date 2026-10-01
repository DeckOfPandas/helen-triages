#!/bin/sh
# Screenshot one element of a served page at 2x, for looking closely.
# Usage: sh scripts/browser/crop.sh <path> <css-selector> <name> [viewport-width] [type-into-selector] [text]
# Output: tmp/shots/crop-<name>.png
#
# The last two type <text> into the element <type-into-selector> before the
# shot (2026-09-15, #1050) -- for a control that only shows itself once
# somebody has typed, such as the search box's dropdown:
#   sh scripts/browser/crop.sh /food/recipes/caramel/ .page-search dropdown 1280 .page-search-input ch
# THAT BOX IS LOCAL-BUILD ONLY SINCE #1210 (2026-09-30), in the header, and
# build.sh builds what deploys, which has none -- so to look at it, build with
# `--config _config.yml,_config_local.yml` into tmp/site instead (MANUAL 13.11
# has the command), then serve and crop as usual.
#
# The port comes from tmp/browser/port, written by this worktree's serve.sh
# (2026-09-11) -- see shoot.sh for why. 4010 only when no server is running here.
port=4010
if [ -f tmp/browser/port ]; then
  read -r port < tmp/browser/port
fi
mkdir -p tmp/shots
. scripts/browser/env.sh
node scripts/browser/crop.js "http://127.0.0.1:$port/helen-triages$1" "$2" "tmp/shots/crop-$3.png" "$4" "$5" "$6"
