#!/bin/sh
# Screenshot pages of the served build at 360, 390 and 1280 px and report any
# element past the viewport. Usage: sh scripts/browser/shoot.sh <label> <path>...
# With no paths, the family-weekend set of 2026-09-10 (both indexes, three
# drinks, two recipes, both reference pages, about). Output: tmp/shots/.
label="$1"
shift
if [ "$#" -eq 0 ]; then
  set -- /cocktails/ /cocktails/recipes/arrack-christmas-punch-wife-3/ \
    /cocktails/recipes/pear-apricot-and-rosemary-bellini/ /cocktails/recipes/cobras-fang/ \
    /food/ /food/recipes/moules-mariniere/ /food/recipes/pineapple-ginger-spatchcock-chicken/ \
    /food/reference/internal-temperatures/ /food/reference/cooking-methods-and-timings/ /about/
fi
mkdir -p tmp/shots
export PLAYWRIGHT_BROWSERS_PATH="$PWD/tmp/browser/ms-playwright"
export NODE_PATH="$PWD/tmp/browser/node_modules"
node scripts/browser/shoot.js http://127.0.0.1:4010/helen-triages tmp/shots "$label" "$@"
