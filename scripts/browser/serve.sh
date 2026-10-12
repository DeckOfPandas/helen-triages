#!/bin/sh
# Serve the local build (tmp/site, from `sh scripts/browser/build.sh`) at the
# site's own baseurl, so every relative_url resolves. Run in the background.
#
# The port is the first free one from 4010, and serve.py writes it to
# tmp/browser/port for the other harness scripts to read. A fixed port, in a
# container running several worktrees' sessions, makes the second server fail
# to bind and that session's screenshots measure somebody else's build. 4010
# and up avoids jekyll-local's 4001 and jekyll-prod's 4002.
set -e
mkdir -p tmp/serve
if [ ! -e tmp/serve/helen-triages ]; then
  ln -s ../site tmp/serve/helen-triages
fi
exec python3 scripts/browser/serve.py
