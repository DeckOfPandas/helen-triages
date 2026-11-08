#!/bin/sh
# Screenshot one element of a served page at 2x, through tools/dev/crop.js.
#   sh scripts/browser/crop.sh <path> <selector> <name> [width] [type-into-selector] [text]
# Output: tmp/shots/crop-<name>.png, and the element's box in CSS px.
#
# The last two type <text> into <type-into-selector> before the shot, for a
# control that only shows once somebody has typed, such as the search box's
# dropdown (#1050):
#   sh scripts/browser/crop.sh /food/recipes/caramel/ .page-search-results dropdown 1280 .page-search-input ch
# The dropdown hangs outside the box, so crop `.page-search-results` itself.
set -eu
WRAPPER=crop.sh
[ "$#" -ge 3 ] && [ "$#" -le 6 ] \
  || { echo "usage: sh scripts/browser/crop.sh <path> <selector> <name> [width] [type-into-selector] [text]" >&2; exit 2; }
. scripts/browser/_site.sh
selector="$2"
name="$3"
width="${4:-1280}"
if [ "$#" -ge 5 ]; then
  [ "$#" -eq 6 ] || { echo "crop.sh: refused -- a type-into selector needs its text" >&2; exit 2; }
  exec node tools/dev/crop.js "$base" "$name" "$selector" "$page" --width "$width" --type-into "$5" "$6"
fi
exec node tools/dev/crop.js "$base" "$name" "$selector" "$page" --width "$width"
