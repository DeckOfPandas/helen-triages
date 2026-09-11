#!/bin/sh
# Build the site exactly as it deploys -- `_config.yml` alone, so no drafts and
# no local switches -- into tmp/site, which serve.sh serves at 127.0.0.1:4010
# for shoot.sh and crop.sh.
#
# WHY THIS EXISTS (2026-09-11). serve.sh's header said to build with
# `sh tmp/build.sh` or a hand-typed `bundle exec jekyll build ... -d tmp/site`.
# The first is a script no allow rule may cover (Helen's ruling that day:
# tmp/ scripts keep asking), and the second's `...` was a different command in
# every session. So the build that the screenshot harness expects is written
# down once, here, and the allow rule is this exact command.
#
# The flags match the production builds in tests/test_rendered_pages.py.
#
# USAGE:
#   sh scripts/browser/build.sh
set -eu

exec bundle exec jekyll build --config _config.yml -d tmp/site --quiet
