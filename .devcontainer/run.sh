#!/bin/bash
# Runs the sandboxed devcontainer for this project. Save this file,
# chmod +x it yourself, then just run it -- no arguments needed.
#
# Reads GH_TOKEN from .claude/settings.local.json just for the duration
# of this one `docker run`, without ever printing it, writing it
# anywhere else, or exporting it into your persistent shell environment.
# Builds the image itself on first run if it doesn't exist yet.

set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
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

GH_TOKEN="$(python3 -c "import json; print(json.load(open('.claude/settings.local.json'))['env']['GH_TOKEN'])")" \
docker run -it --rm \
  -v "$REPO_ROOT:/workspace" \
  -v helen-triages-claude-config:/home/helen/.claude \
  -v "$BUNDLE_VOLUME:/home/helen/.bundle-cache" \
  "${DOTFILE_MOUNTS[@]}" \
  -e GH_TOKEN \
  -p 4001:4001 \
  -p 4002:4002 \
  -w /workspace \
  helen-triages-devcontainer \
  bash
