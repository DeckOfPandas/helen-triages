#!/bin/sh
# Screenshot site paths of this worktree's served build at 360, 390 and 1280
# px, and report any element past the viewport, through tools/dev/shoot.js.
#   sh scripts/browser/shoot.sh <label> [/path/...]
# With no paths, a default set: both indexes, three drinks, two recipes, both
# reference pages, about. Output: tmp/shots/<label>-<width>-light-<page>.png.
#
# The port comes from tmp/browser/port, written by this worktree's serve.sh,
# so the page measured is this worktree's own build and never another
# session's. With no port file it falls back to 4010 and the ERROR lines name
# the refused connection.
set -eu
[ "$#" -ge 1 ] || { echo "usage: sh scripts/browser/shoot.sh <label> [/path/...]" >&2; exit 2; }
label="$1"
shift
if [ "$#" -eq 0 ]; then
  set -- /cocktails/ /cocktails/recipes/arrack-christmas-punch-wife-3/ \
    /cocktails/recipes/pear-and-rosemary-bellini/ /cocktails/recipes/cobras-fang/ \
    /food/ /food/recipes/moules-mariniere/ /food/recipes/pineapple-ginger-spatchcock-chicken/ \
    /food/reference/internal-temperatures/ /food/reference/cooking-methods-and-timings/ /about/
fi
port=4010
if [ -f tmp/browser/port ]; then
  read -r port < tmp/browser/port
fi
# shoot.js takes pages relative to the base URL; ours are site paths. Each
# argument is taken off the front and its relative form put on the back.
n="$#"
while [ "$n" -gt 0 ]; do
  p="$1"
  shift
  case "$p" in
    /*) ;;
    *) echo "shoot.sh: '$p' must start with /" >&2; exit 2 ;;
  esac
  rel="${p#/}"
  set -- "$@" "${rel:-.}"
  n=$((n - 1))
done
. scripts/browser/env.sh
exec node tools/dev/shoot.js "http://127.0.0.1:$port/helen-triages" "$label" "$@"
