#!/bin/sh
# The vertical rhythm under an element of a served page, through
# tools/dev/gaps.js: each visible block child's height, margins, padding and
# gap to the sibling above, as an indented tree to depth 4.
#   sh scripts/browser/gaps.sh <path> [width] [root-selector]
# The root defaults to `main`.
set -eu
WRAPPER=gaps.sh
[ "$#" -ge 1 ] && [ "$#" -le 3 ] \
  || { echo "usage: sh scripts/browser/gaps.sh <path> [width] [root-selector]" >&2; exit 2; }
. scripts/browser/_site.sh
exec node tools/dev/gaps.js "$base" "${3:-main}" "$page" --width "${2:-1280}"
