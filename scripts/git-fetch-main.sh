#!/bin/sh
# Bring this checkout's `origin/main` up to date with the default repo (the
# first of GH_REPOS). Follow it with `git merge origin/main`.
#
# USAGE:  sh scripts/git-fetch-main.sh
#
# No arguments, so the allow rule is this exact command. `git fetch *` cannot
# be allowed: `--upload-pack=<command>` anywhere on its line runs a program.
# It touches only refs/remotes/origin/main, never a local branch or the
# working tree, so it cannot move `main` or lose work.
set -eu

WRAPPER=git-fetch-main.sh
here="$(cd "$(dirname "$0")" && pwd)"
. "$here/_github_conf.sh"
load_conf

[ "$#" -eq 0 ] || refuse "this takes no arguments"

if [ -n "${AGENT_WRAPPER_DRY_RUN:-}" ]; then
  printf '%s\n' git fetch "https://github.com/$GH_OWNER/${DEFAULT_REPO}.git" \
    +refs/heads/main:refs/remotes/origin/main
  exit 0
fi

git -c "credential.helper=!sh '${here}/git-credential-agent-token.sh'" \
  fetch --quiet "https://github.com/$GH_OWNER/${DEFAULT_REPO}.git" \
  +refs/heads/main:refs/remotes/origin/main

# What you actually got, so a stale view is visible rather than assumed.
git log -1 --format='%h %ad %s' --date=short origin/main
