#!/bin/bash
# Updates both private drafts repos to the latest main. Stops immediately
# on any git error rather than attempting to fix it -- if something's
# wrong (uncommitted changes, a diverged history, network trouble), you
# see the real git error and decide what to do, not a script guessing.

set -e

REPO_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"

for repo in _food_drafts _cocktail_drafts; do
  echo "=== $repo ==="
  cd "$REPO_ROOT/$repo"
  git checkout main
  git pull origin main
done

echo "Done."
