#!/bin/sh
# Print every element matching a selector's box (CSS px) and computed styles,
# for spot-checking spacing and typography drift without squinting at two
# screenshots. Usage:
#   sh scripts/browser/styles.sh <path> <selector> [width] [prop,prop,...]
#
# By default: font-family, font-size, font-weight, line-height,
# letter-spacing, text-transform, color, background-color, the four margin
# and four padding longhands, gap, display. A comma list of lowercase-hyphen
# property names overrides that -- e.g. `color,background-color`.
#
# THE PORT COMES FROM tmp/browser/port, written by THIS worktree's serve.sh
# (2026-09-11), so the page measured is this worktree's own build and never
# another session's -- see shoot.sh. 4010 only when no server is running here.
#
# Added 2026-09-15, alongside gaps.sh and click-crop.sh, so a Playwright
# question ("what's the computed spacing here") is a committed, allow-listed
# call rather than a one-off tmp/ script naming PLAYWRIGHT_BROWSERS_PATH and
# NODE_PATH by hand (which guard-unanalyzable-bash.py now refuses outright).
set -eu

refuse() {
  echo "styles.sh: refused -- $1" >&2
  exit 2
}

[ "$#" -ge 2 ] || refuse "usage: sh scripts/browser/styles.sh <path> <selector> [width] [prop,prop,...]"
path="$1"
selector="$2"
width="${3:-1280}"
props="${4:-}"

case "$path" in
  /*) ;;
  *) refuse "'$path' must start with /" ;;
esac
case "$path" in
  *..*) refuse "'$path' may not contain '..'" ;;
  *://*) refuse "'$path' may not contain a scheme" ;;
esac
[ -n "$selector" ] || refuse "the selector may not be empty"
case "$width" in
  ''|*[!0-9]*) refuse "'$width' must be an integer" ;;
esac
if [ "$width" -lt 200 ] || [ "$width" -gt 2000 ]; then
  refuse "'$width' must be between 200 and 2000"
fi
if [ -n "$props" ]; then
  case "$props" in
    ''|,*|*,|*,,*|*[!a-z,-]*)
      refuse "'$props' must be a comma-separated list of lowercase-hyphen property names" ;;
  esac
fi

port=4010
if [ -f tmp/browser/port ]; then
  read -r port < tmp/browser/port
fi
. scripts/browser/env.sh
node scripts/browser/styles.js "http://127.0.0.1:$port/helen-triages$path" "$selector" "$width" "$props"
