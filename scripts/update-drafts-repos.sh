#!/bin/bash
# Helen's, run on the HOST (README.md, "General dev workflow"): updates both
# private drafts repos to the latest main over her SSH `origin`. An agent never
# runs it -- it checks out `main`, and SSH dies in the container; an agent
# clones or fetches with scripts/git-clone-agent.sh / git-fetch-agent.sh.
# Stops on any git error rather than attempting to fix it, so you see the real
# error (uncommitted changes, a diverged history, network trouble) and decide.

set -e

REPO_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"

for repo in _food_drafts _cocktail_drafts; do
  echo "=== $repo ==="
  cd "$REPO_ROOT/$repo"
  git checkout main
  git pull origin main
done

echo "Done."
