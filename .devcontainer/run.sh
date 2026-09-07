#!/bin/bash
# Runs the sandboxed devcontainer for this project. Save this file,
# chmod +x it yourself, then just run it -- no arguments needed.
#
# Reads GH_TOKEN from .claude/settings.local.json just for the duration
# of this one `docker run`, without ever printing it, writing it
# anywhere else, or exporting it into your persistent shell environment.
# Build the image first if you haven't:
#   docker build -t helen-triages-devcontainer -f .devcontainer/Dockerfile .devcontainer

set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
cd "$REPO_ROOT"

docker volume create helen-triages-claude-config >/dev/null
docker volume create helen-triages-bundle-cache >/dev/null

GH_TOKEN="$(python3 -c "import json; print(json.load(open('.claude/settings.local.json'))['env']['GH_TOKEN'])")" \
docker run -it --rm \
  -v "$REPO_ROOT:/workspace" \
  -v helen-triages-claude-config:/home/helen/.claude \
  -v helen-triages-bundle-cache:/home/helen/.bundle-cache \
  -e GH_TOKEN \
  -w /workspace \
  helen-triages-devcontainer \
  bash
