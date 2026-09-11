#!/bin/sh
# Serve the local build (tmp/site, from `sh scripts/browser/build.sh`) at the
# site's own baseurl, so every relative_url resolves. Run in the background.
#
# THE PORT IS THE FIRST FREE ONE FROM 4010, SINCE 2026-09-11, and serve.py
# writes it to tmp/browser/port for shoot.sh and crop.sh to read. It was a
# fixed 4010 before, which in a container running several worktrees' sessions
# meant the second server failed to bind and that session's screenshots
# measured somebody else's build (DECISIONS §14, 2026-09-10). 4010 and up
# deliberately avoids jekyll-local's 4001 and jekyll-prod's 4002.
set -e
mkdir -p tmp/serve
if [ ! -e tmp/serve/helen-triages ]; then
  ln -s ../site tmp/serve/helen-triages
fi
exec python3 scripts/browser/serve.py
