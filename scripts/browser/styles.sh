#!/bin/sh
# Print every element matching a selector's box (CSS px) and computed styles,
# through tools/dev/styles.js, for spot-checking spacing and typography drift.
#   sh scripts/browser/styles.sh <path> <selector> [width] [prop,prop,...]
# Without a property list: type, colour, the margin and padding longhands, gap
# and display.
set -eu
WRAPPER=styles.sh
[ "$#" -ge 2 ] && [ "$#" -le 4 ] \
  || { echo "usage: sh scripts/browser/styles.sh <path> <selector> [width] [prop,prop,...]" >&2; exit 2; }
. scripts/browser/_site.sh
if [ "$#" -eq 4 ]; then
  exec node tools/dev/styles.js "$base" "$2" "$page" --width "$3" --props "$4"
fi
exec node tools/dev/styles.js "$base" "$2" "$page" --width "${3:-1280}"
