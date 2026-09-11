#!/bin/sh
# Bring this checkout's `origin/main` up to date with the public repo: the one
# fetch every worktree needs before merging or opening a PR, as one command
# with no arguments.
#
# WHY THIS EXISTS (2026-09-11), and why it takes nothing. Helen asked for
# commands that can be statically analysed without prompting her. The obvious
# allow rule, `git fetch *`, is not one of those: `git fetch` takes
# `--upload-pack=<command>` anywhere on its command line, so a rule that reads
# as "fetch" would also allow running any program at all. The forms that do
# work are all awkward somewhere -- `git fetch origin` dies in the devcontainer
# (`origin` is SSH, no host key), and `git fetch origin main:main` refuses in a
# worktree (CLAUDE.md, Git workflow). So the fetch lives here, with a fixed URL
# and a fixed refspec, and the allow rule is this exact command.
#
# WHAT IT TOUCHES. Only `refs/remotes/origin/main`. It never updates a local
# branch and never touches the working tree, so it cannot move `main` and
# cannot lose work. The repo is public, so no credential is involved. Follow it
# with `git merge origin/main`, which is also allow-listed as that exact
# command; guard-main-branch.py still refuses a merge while standing on `main`.
#
# USAGE:
#   sh scripts/git-fetch-main.sh
#
# Invoked via `sh` so it needs no execute bit.
set -eu

git fetch --quiet https://github.com/DeckOfPandas/helen-triages.git \
  +refs/heads/main:refs/remotes/origin/main

# What you actually got, so a stale view is visible rather than assumed.
git log -1 --format='%h %ad %s' --date=short origin/main
