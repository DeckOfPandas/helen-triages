#!/bin/bash
# Runs the sandboxed devcontainer for this project. Save this file,
# chmod +x it yourself, then just run it -- no arguments needed.
#
# Reads AGENT_GH_TOKEN from .claude/settings.local.json just for the
# duration of this one `docker run`, without ever printing it, writing it
# anywhere else, or exporting it into your persistent shell environment.
# AGENT_GH_TOKEN is DeckOfPandas-agentic-claude's classic repo-scoped token -- a
# separate GitHub account, invited as a collaborator on just these three
# repos, so it can push and open PRs under its own identity without ever
# touching Helen's SSH keys. Builds the image itself when there isn't one,
# and rebuilds it whenever .devcontainer/ has changed since the image was
# built -- see the build-stamp block below.
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

IMAGE=helen-triages-devcontainer

# IS THE IMAGE BUILT FROM WHAT IS ON DISK RIGHT NOW? -- added 2026-09-21.
# "Does the image exist" was the old check, and it is a different question.
# Helen added packages to the Dockerfile, rebuilt, and containers kept
# coming up without them: the rebuild and the run were of different things
# and nothing ever compared them. An image that exists is not an image that
# matches.
#
# So the image now carries a LABEL holding a hash of its build inputs, and
# this rebuilds whenever that hash is missing or no longer matches the
# files on disk. Three cases, one comparison: no image, an image with no
# stamp (built before this existed, or built by hand), and a stamp that
# disagrees with the current .devcontainer/.
#
# IT COMPARES CONTENT, NOT TIMESTAMPS, which is stricter than "is the
# Dockerfile newer than the image" in both directions. `touch` alone does
# not trigger a rebuild; reverting an edit goes back to the image that
# matches rather than building a third thing. And mtime-vs-image-Created
# has a trap this avoids: a fully cached rebuild keeps the CACHED layer's
# Created date, so the image's timestamp can stay older than the Dockerfile
# forever and the check never settles.
#
# EVERY file in .devcontainer/ is hashed EXCEPT the ones .dockerignore names,
# rather than a hand-maintained list of "the files that matter" -- that list is
# one more thing to keep in sync, and the Dockerfile's note about
# requirements-test.txt says how that goes. Until 2026-09-24 there was no
# exception at all, so editing this script or the README cost one rebuild; #1191
# added `.devcontainer/.dockerignore`, which Docker already honours for the
# context and this now honours for the hash, so the two agree by construction
# rather than by someone remembering.
#
# AND IT ONLY UNDERSTANDS EXACT FILENAMES. A line in .dockerignore with a `*`,
# a `/` or a `!` in it makes this fall back to hashing the whole directory,
# ignore file and all. A half-understood pattern would silently shrink what the
# stamp covers, and an image NOT rebuilt when it should be is the entire bug
# this mechanism exists to prevent -- so the failure mode is a spurious cached
# rebuild, never a missed one.
#
# What it still cannot see: `ruby:3.3-bookworm` moving upstream, or an
# `apt-get install` resolving to newer packages than last time. The
# Dockerfile does not pin those, so nothing on disk changes when they move.
# `docker build --pull --no-cache` by hand is the answer when that matters.
STAMP_LABEL=com.deckofpandas.build-inputs

BUILD_INPUTS_HASH="$(python3 .devcontainer/build_inputs_hash.py)"
IMAGE_STAMP="$(docker image inspect --format "{{ index .Config.Labels \"$STAMP_LABEL\" }}" "$IMAGE" 2>/dev/null || true)"

if [ "$IMAGE_STAMP" != "$BUILD_INPUTS_HASH" ]; then
  if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    echo "Image not found -- building $IMAGE (first run)..."
  elif [ -z "$IMAGE_STAMP" ] || [ "$IMAGE_STAMP" = "<no value>" ]; then
    echo "Image carries no build stamp (built before this check, or by hand) -- rebuilding $IMAGE..."
  else
    echo ".devcontainer/ has changed since $IMAGE was built -- rebuilding..."
  fi
  docker build -t "$IMAGE" --label "$STAMP_LABEL=$BUILD_INPUTS_HASH" -f .devcontainer/Dockerfile .devcontainer
fi

# ONE BUNDLE CACHE, AND THE NAME NO LONGER VARIES -- corrected 2026-09-21.
# This was `helen-triages-bundle-cache-$(basename "$REPO_ROOT")`, under a
# comment promising a volume per worktree ("opus-cocktail-data" or
# "helen-triages"). That promise stopped being true the moment REPO_ROOT
# started coming from `--git-common-dir` above: that always resolves to the
# PRIMARY clone, from anywhere in the worktree set, so the basename could
# only ever be "helen-triages" and the computation was dead cleverness under
# a false comment. Nothing is lost -- the race it claimed to prevent is
# already impossible, because --name below refuses a second container
# outright. Both volumes are shared across every worktree, deliberately,
# the same way every host-side Claude Code session shares one ~/.claude.
BUNDLE_VOLUME=helen-triages-bundle-cache-helen-triages

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
# jekyll-local/jekyll-prod aliases serve there.
#
# THIS COMMENT USED TO SAY "the image carries no jekyll, which is the same gap
# that stops scripts/verify.py running in the container". BOTH HALVES WERE
# FALSE, and nobody checked for twelve days. Measured inside a real container,
# 2026-09-21: `bundle exec jekyll --version` prints 4.4.1 and
# `python3 scripts/verify.py` exits 0. The image does not BAKE the gem -- it
# comes from the Gemfile via `bundle install` into the cache volume below --
# but that is a first-run cost, not a gap, and the aliases above are exactly
# how it gets used. Helen: "I'm pretty sure the container has Jekyll... Are you
# not able to check?" The answer was yes, all along.
AGENT_GH_TOKEN="$(python3 -c "import json; print(json.load(open('.claude/settings.local.json'))['env']['AGENT_GH_TOKEN'])")" \
docker run -it --rm \
  --name helen-triages-primary \
  -v "$REPO_ROOT:/workspace" \
  -v helen-triages-claude-config:/home/helen/.claude \
  -v "$BUNDLE_VOLUME:/home/helen/.bundle-cache" \
  "${DOTFILE_MOUNTS[@]}" \
  -e AGENT_GH_TOKEN \
  -p 5998:4001 \
  -p 5999:4002 \
  -w /workspace \
  "$IMAGE" \
  bash
