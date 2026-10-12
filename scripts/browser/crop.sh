#!/bin/sh
# Screenshot one element of a served page at 2x, for looking closely.
# Usage: sh scripts/browser/crop.sh <path> <css-selector> <name> [viewport-width] [type-into-selector] [text]
# Output: tmp/shots/crop-<name>.png
#
# The last two type <text> into the element <type-into-selector> before the
# shot, for a control that only shows itself once somebody has typed, such as
# the search box's dropdown (#1050):
#   sh scripts/browser/crop.sh /food/recipes/caramel/ .page-search dropdown 1280 .page-search-input ch
# That box is local-build only (#1210) and build.sh builds what deploys, which
# has none: to look at it, build with `--config _config.yml,_config_local.yml`
# into tmp/site instead (MANUAL §13.11), then serve and crop as usual.
#
# The port comes from tmp/browser/port, written by this worktree's serve.sh;
# see shoot.sh. 4010 only when no server is running here.
port=4010
if [ -f tmp/browser/port ]; then
  read -r port < tmp/browser/port
fi
mkdir -p tmp/shots
. scripts/browser/env.sh
node scripts/browser/crop.js "http://127.0.0.1:$port/helen-triages$1" "$2" "tmp/shots/crop-$3.png" "$4" "$5" "$6"
