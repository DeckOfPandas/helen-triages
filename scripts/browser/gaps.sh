#!/bin/sh
# The vertical gap in px between consecutive visible block siblings under
# <root-selector> (default `main`), as an indented tree to depth 4 -- each
# line names the element's tag.class, its height, its margin/padding
# top/bottom, and the gap to the sibling before it. Skips inline elements,
# absolutely/fixed positioned elements, and anything under 6px in both
# dimensions. This is the tool that found two spacing drifts in #1093's
# review.
# Usage: sh scripts/browser/gaps.sh <path> [width] [root-selector]
#
# THE PORT COMES FROM tmp/browser/port, written by THIS worktree's serve.sh
# -- see shoot.sh. 4010 only when no server is running here.
set -eu

refuse() {
  echo "gaps.sh: refused -- $1" >&2
  exit 2
}

[ "$#" -ge 1 ] || refuse "usage: sh scripts/browser/gaps.sh <path> [width] [root-selector]"
path="$1"
width="${2:-1280}"
root="${3:-main}"

case "$path" in
  /*) ;;
  *) refuse "'$path' must start with /" ;;
esac
case "$path" in
  *..*) refuse "'$path' may not contain '..'" ;;
  *://*) refuse "'$path' may not contain a scheme" ;;
esac
case "$width" in
  ''|*[!0-9]*) refuse "'$width' must be an integer" ;;
esac
if [ "$width" -lt 200 ] || [ "$width" -gt 2000 ]; then
  refuse "'$width' must be between 200 and 2000"
fi

port=4010
if [ -f tmp/browser/port ]; then
  read -r port < tmp/browser/port
fi
. scripts/browser/env.sh
node scripts/browser/gaps.js "http://127.0.0.1:$port/helen-triages$path" "$width" "$root"
