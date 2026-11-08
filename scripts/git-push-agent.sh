#!/bin/sh
# Push as the agent account over HTTPS, without naming the credential and
# without it ever being in a URL. An SSH `origin` has no key in the container,
# so the URL is built here.
#
# USAGE:
#   sh scripts/git-push-agent.sh <branch>:<branch> [repo] [dir]
#   sh scripts/git-push-agent.sh :<branch>              # delete a remote branch
#
# `repo` defaults to the first of GH_REPOS; `dir` is the checkout to push FROM
# and defaults to here. Nothing checks that the two match: pushing from a
# nested clone of another repo, give both.
#
# REFUSES: a destination of `main` or `master` however spelled (`x:main`,
# `+x:main`, `x:refs/heads/main`, `:main`), unless the repo is in
# MAIN_PUSH_REPOS; a refspec with no colon, since a bare name or HEAD pushes to
# whatever is checked out; one starting `-`; a repo outside GH_REPOS; and a
# `dir` that is absolute, contains `..` or starts `-`.
#
# GitHub itself refuses a push that adds or changes a file under
# .github/workflows/ unless the token has the `workflow` scope (README.md,
# "GitHub agent account"). The refusal names the scope; the fix is a new token,
# not a retry.
set -eu

WRAPPER=git-push-agent.sh
here="$(cd "$(dirname "$0")" && pwd)"
. "$here/_github_conf.sh"
load_conf

[ "$#" -ge 1 ] && [ "$#" -le 3 ] || refuse "usage: sh scripts/git-push-agent.sh <branch>:<branch> [repo] [dir]"
refspec="$1"
repo="${2:-$DEFAULT_REPO}"
dir="${3:-.}"

case "$refspec" in
  -*) refuse "'$refspec' starts with '-', which git would read as an option" ;;
  *:*) ;;
  *) refuse "give the refspec as <branch>:<branch>, never a bare name or HEAD" ;;
esac
check_repo "$repo"
check_dir "$dir"

destination="${refspec##*:}"
case "$destination" in
  main | */main | master | */master)
    # shellcheck disable=SC2086
    in_list "$repo" $MAIN_PUSH_REPOS \
      || refuse "that pushes to $repo's $destination, which only moves by a merged PR (MAIN_PUSH_REPOS in $conf_name)" ;;
esac

run_or_print git -C "$dir" \
  -c "credential.helper=!sh '${here}/git-credential-agent-token.sh'" \
  push "https://github.com/$GH_OWNER/${repo}.git" "$refspec"
