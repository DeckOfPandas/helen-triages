#!/bin/sh
# Bring this checkout's `origin/main` up to date with the public repo: the one
# fetch every worktree needs before merging or opening a PR.
#
# USAGE:
#   sh scripts/git-fetch-main.sh
#
# It takes no arguments, and the allow rule is this exact command. `git fetch
# *` cannot be allowed: `git fetch` takes `--upload-pack=<command>` anywhere on
# its line, so that rule would run any program. `git fetch origin` fails in the
# devcontainer (`origin` is SSH, no host key), and `git fetch origin main:main`
# is refused in a worktree. So the URL and the refspec are fixed here.
# DECISIONS §11.
#
# It touches only `refs/remotes/origin/main`: never a local branch, never the
# working tree, so it cannot move `main` or lose work. The repo is public, so
# no credential is involved. Follow it with `git merge origin/main`, allowed as
# that exact command; guard-main-branch.py still refuses a merge on `main`.
#
# Invoked via `sh` so it needs no execute bit.
set -eu

git fetch --quiet https://github.com/DeckOfPandas/helen-triages.git \
  +refs/heads/main:refs/remotes/origin/main

# What you actually got, so a stale view is visible rather than assumed.
git log -1 --format='%h %ad %s' --date=short origin/main
