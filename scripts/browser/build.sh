#!/bin/sh
# Build the site exactly as it deploys -- `_config.yml` alone, so no drafts and
# no local switches -- into tmp/site, which serve.sh serves for the other
# harness scripts. The build is fixed here so the allow rule is this exact
# command; a tmp/ script would ask Helen each time.
#
# USAGE:
#   sh scripts/browser/build.sh
set -eu

exec bundle exec jekyll build --config _config.yml -d tmp/site --quiet
