#!/bin/sh
# Clone one of the configured repos as the agent account over HTTPS, without
# the credential ever entering the URL git stores as `origin`.
#
# USAGE:  sh scripts/git-clone-agent.sh <repo> [dir]
#
# REFUSES anything but a repo from GH_REPOS and an optional relative `dir`
# with no `..` and no leading `-`. Passing further arguments through would let
# the allow rule run any program: `git clone --template=<dir>` runs its hooks.
set -eu

WRAPPER=git-clone-agent.sh
here="$(cd "$(dirname "$0")" && pwd)"
. "$here/_github_conf.sh"
load_conf

[ "$#" -ge 1 ] && [ "$#" -le 2 ] || refuse "usage: sh scripts/git-clone-agent.sh <repo> [dir]"
repo="$1"
shift
check_repo "$repo"
[ "$#" -eq 0 ] || check_dir "$1"

run_or_print git -c "credential.helper=!sh '${here}/git-credential-agent-token.sh'" \
  clone --quiet "https://github.com/$GH_OWNER/${repo}.git" "$@"
