#!/bin/sh
# Serve the local build (tmp/site, from `sh scripts/browser/build.sh`) at the
# site's own baseurl, so
# every relative_url resolves. Run in the background; port 4010 deliberately
# avoids jekyll-local's 4001 and jekyll-prod's 4002.
set -e
mkdir -p tmp/serve
if [ ! -e tmp/serve/helen-triages ]; then
  ln -s ../site tmp/serve/helen-triages
fi
cd tmp/serve
exec python3 -m http.server 4010 --bind 127.0.0.1
