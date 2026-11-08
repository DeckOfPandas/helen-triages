#!/bin/sh
# Click one element, then crop another at 2x, through tools/dev/crop.js
# --click: for a control that reveals or changes something once clicked (a
# toggle, a filter chip, a tab).
#   sh scripts/browser/click-crop.sh <path> <click-selector> <crop-selector> <name> [width]
# Output: tmp/shots/crop-<name>.png, and the cropped element's box in CSS px.
# The FIRST match of <click-selector> is clicked once.
set -eu
WRAPPER=click-crop.sh
[ "$#" -ge 4 ] && [ "$#" -le 5 ] \
  || { echo "usage: sh scripts/browser/click-crop.sh <path> <click-selector> <crop-selector> <name> [width]" >&2; exit 2; }
. scripts/browser/_site.sh
exec node tools/dev/crop.js "$base" "$4" "$3" "$page" --width "${5:-1280}" --click "$2"
