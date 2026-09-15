#!/bin/sh
# Click one element, then crop another at 2x -- for a control that only
# reveals or changes something once clicked (a toggle, a filter chip, a tab),
# where crop.sh's type-into pair only covers the type-then-look case.
# Usage: sh scripts/browser/click-crop.sh <path> <click-selector> <crop-selector> <name> [width]
# Output: tmp/shots/crop-<name>.png
#
# Clicks the FIRST match of <click-selector> once, waits for the network to
# go quiet plus a short beat, then crops <crop-selector> as crop.sh does and
# prints its box in CSS px.
#
# THE PORT COMES FROM tmp/browser/port, written by THIS worktree's serve.sh
# -- see shoot.sh. 4010 only when no server is running here.
set -eu

refuse() {
  echo "click-crop.sh: refused -- $1" >&2
  exit 2
}

[ "$#" -ge 4 ] || refuse "usage: sh scripts/browser/click-crop.sh <path> <click-selector> <crop-selector> <name> [width]"
path="$1"
click_selector="$2"
crop_selector="$3"
name="$4"
width="${5:-1280}"

case "$path" in
  /*) ;;
  *) refuse "'$path' must start with /" ;;
esac
case "$path" in
  *..*) refuse "'$path' may not contain '..'" ;;
  *://*) refuse "'$path' may not contain a scheme" ;;
esac
[ -n "$click_selector" ] || refuse "the click selector may not be empty"
case "$click_selector" in
  *,*) refuse "the click selector must be comma-free -- it is clicked once, as its first match" ;;
esac
[ -n "$crop_selector" ] || refuse "the crop selector may not be empty"
case "$name" in
  ''|*[!a-z0-9-]*) refuse "'$name' must match [a-z0-9-]+" ;;
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
mkdir -p tmp/shots
. scripts/browser/env.sh
node scripts/browser/click-crop.js "http://127.0.0.1:$port/helen-triages$path" "$click_selector" "$crop_selector" "tmp/shots/crop-$name.png" "$width"
