#!/bin/bash
# Runs the sandboxed devcontainer for this project. Save this file,
# chmod +x it yourself, then just run it -- no arguments needed.
#
# Reads AGENT_GH_TOKEN from .claude/settings.local.json just for the
# duration of this one `docker run`, without ever printing it, writing it
# anywhere else, or exporting it into your persistent shell environment.
# AGENT_GH_TOKEN is DeckOfPandas-agentic's classic repo-scoped token -- a
# separate GitHub account, invited as a collaborator on just these three
# repos, so it can push and open PRs under its own identity without ever
# touching Helen's SSH keys. Builds the image itself on first run if it
# doesn't exist yet.
#
# GH_TOKEN WAS READ HERE TOO UNTIL 2026-09-09, when Helen deleted it on
# GitHub and it stopped existing. It was her own fine-grained token and it
# had been reduced to a subset of what AGENT_GH_TOKEN already did -- two
# credentials where one was enough. Nothing needs adding back: every caller
# reads AGENT_GH_TOKEN now.

set -euo pipefail

# ALWAYS MOUNT THE PRIMARY CLONE, EVEN WHEN INVOKED FROM INSIDE A WORKTREE.
# This script is a tracked file, so a copy of it sits in every worktree, and
# `--show-toplevel` resolves to whichever one you happen to be standing in --
# so running it from `.claude/worktrees/foo` used to mount that worktree as
# /workspace instead of the primary checkout. `--git-common-dir` points at the
# primary `.git` from anywhere in the worktree set.
GIT_COMMON_DIR="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --path-format=absolute --git-common-dir)"
REPO_ROOT="$(dirname "$GIT_COMMON_DIR")"
cd "$REPO_ROOT"

if ! docker image inspect helen-triages-devcontainer >/dev/null 2>&1; then
  echo "Image not found -- building helen-triages-devcontainer (first run only)..."
  docker build -t helen-triages-devcontainer -f .devcontainer/Dockerfile .devcontainer
fi

# Bundle cache is per-worktree (named after the worktree's own directory,
# e.g. "opus-cocktail-data" or "helen-triages" for the primary checkout) so
# two containers running on two worktrees at once never race each other's
# `bundle install`. The Claude config volume stays shared across all of
# them deliberately -- that mirrors how every host-side Claude Code
# session, across every worktree, already shares one ~/.claude directory.
BUNDLE_VOLUME="helen-triages-bundle-cache-$(basename "$REPO_ROOT")"

docker volume create helen-triages-claude-config >/dev/null
docker volume create "$BUNDLE_VOLUME" >/dev/null

# A FIXED CONTAINER NAME, SO A SECOND RUN IS REFUSED RATHER THAN GRANTED.
# `docker run` without `--name` invents a fresh one every time, so running
# this script in two terminals cheerfully gave two containers on ONE bind
# mount -- two Claudes editing one working tree and one branch. That is the
# trampling host-side worktrees exist to prevent, and it happened: on
# 2026-09-08 a session's branch moved under it four times mid-task, and an
# uncommitted edit rode into somebody else's branch (DECISIONS.md §11).
#
# Docker refuses a duplicate name outright, which turns that into an error
# at the door instead of a puzzle three hours later. It does NOT guard
# host-versus-container -- nothing here can -- so a worktree is still the
# answer for running several Claudes at once.

# Optional convenience dotfiles: mounted read-only, and only if they exist,
# so this works whether or not you've set any of them up. Mounted at
# alternate .host-* paths -- the container's own .bashrc (baked in at
# build time) sources them from there, layered on top of its own
# jekyll-local/jekyll-prod aliases rather than overwriting them.
DOTFILE_MOUNTS=()
[ -f "$HOME/.bashrc" ] && DOTFILE_MOUNTS+=(-v "$HOME/.bashrc:/home/helen/.host-bashrc:ro")
[ -f "$HOME/.bash_aliases" ] && DOTFILE_MOUNTS+=(-v "$HOME/.bash_aliases:/home/helen/.host-bash_aliases:ro")
[ -f "$HOME/.bash_profile" ] && DOTFILE_MOUNTS+=(-v "$HOME/.bash_profile:/home/helen/.host-bash_profile:ro")
[ -f "$HOME/.gitconfig" ] && DOTFILE_MOUNTS+=(-v "$HOME/.gitconfig:/home/helen/.gitconfig:ro")

# PORTS THE HOST WILL NEVER WANT -- Helen, 2026-09-09: "I'll always need to
# build the site locally from any branch so I'd expect to do so from outside
# the container, but inside the worktree, given it's bound... make it 4999 and
# 5000 or something I'll never use."
#
# THE OLD PAIR WAS ACTIVELY IN HER WAY, not merely useless: `-p 4001:4001`
# meant a running container HELD the host's own 4001, so her `jekyll-local`
# could not bind it while any container was up.
#
# The INSIDE pair stays 4001/4002, because the image's baked-in
# jekyll-local/jekyll-prod aliases serve there. Nothing listens on them today
# in any case -- the image carries no jekyll, which is the same gap that stops
# `scripts/verify.py` running in the container.
AGENT_GH_TOKEN="$(python3 -c "import json; print(json.load(open('.claude/settings.local.json'))['env']['AGENT_GH_TOKEN'])")" \
docker run -it --rm \
  --name helen-triages-primary \
  -v "$REPO_ROOT:/workspace" \
  -v helen-triages-claude-config:/home/helen/.claude \
  -v "$BUNDLE_VOLUME:/home/helen/.bundle-cache" \
  "${DOTFILE_MOUNTS[@]}" \
  -e AGENT_GH_TOKEN \
  -p 4999:4001 \
  -p 5000:4002 \
  -w /workspace \
  helen-triages-devcontainer \
  bash
