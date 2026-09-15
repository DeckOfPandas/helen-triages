#!/bin/sh
# The three GitHub writes a session makes routinely, over REST, each checked.
#
# WHY THIS EXISTS (2026-09-15). Helen, after a session opened two PRs, posted a
# comment and corrected a PR body through `sh scripts/gh-agent.sh api -X ...`
# and every one of them asked her: "When you want to run commands that build
# paths at runtime, please find a way into scripts that can be statically
# analysed so read/write scope can be checked without asking me." Those calls
# could never be allow-listed, for two reasons at once: `-F body=@tmp/x.md` is a
# file read gh performs at run time, which the checker cannot see as a path,
# and `api` is also the door to every other write the token can make --
# including PUT .../pulls/N/merge, which is a merge, on a token that has had
# nothing but a written rule between it and merging since 2026-09-09.
#
# So this wrapper builds the `gh api` call itself and accepts nothing it does
# not understand. `.claude/settings.json` allows `sh scripts/gh-write.sh *`, and
# tests/test_agent_wrappers.py proves what that rule lets through.
#
# USAGE -- the body is ALWAYS a file under tmp/, written with the Write tool:
#   sh scripts/gh-write.sh pr-create <repo> <branch> "<title>" tmp/<body>.md
#   sh scripts/gh-write.sh pr-body   <repo> <number> tmp/<body>.md
#   sh scripts/gh-write.sh comment   <repo> <number> tmp/<body>.md
#
# <repo> is one of the three, bare: helen-triages, helen-triages-food-private,
# helen-triages-cocktails-private. A PR's base is ALWAYS main (CLAUDE.md: every
# PR's base is main, never another PR's branch), and its head is never main.
# `comment` takes an issue OR a PR number -- GitHub files both under issues/.
#
# WHAT IT CANNOT DO, BY CONSTRUCTION: merge, approve, close, delete, change a
# title or state, touch settings, or talk to any other repository. Those stay
# prompts (or rules), which is where they belong.
#
# AGENT_WRAPPER_DRY_RUN=1 prints the command it would run, one argument per
# line, and exits -- for the tests, which need neither network nor credential.
#
# Invoked via `sh` so it needs no execute bit, and it calls gh-agent.sh rather
# than naming the credential, so the token's name stays in one file.
set -eu

refuse() {
  echo "gh-write.sh: refused -- $1" >&2
  exit 2
}

usage="usage: sh scripts/gh-write.sh pr-create <repo> <branch> \"<title>\" tmp/<body>.md | pr-body <repo> <number> tmp/<body>.md | comment <repo> <number> tmp/<body>.md"

check_repo() {
  case "$1" in
    helen-triages | helen-triages-food-private | helen-triages-cocktails-private) ;;
    *) refuse "'$1' is not one of the three repos (CLAUDE.md: never act on any other repository)" ;;
  esac
}

check_number() {
  case "$1" in
    '' | *[!0-9]* | 0*) refuse "'$1' is not an issue or PR number" ;;
  esac
}

check_branch() {
  case "$1" in
    '' | main | refs/* | -* | *..* | */ | *[!A-Za-z0-9._/-]*)
      refuse "'$1' is not a branch this wrapper opens a PR from (never main, no options, no owner: prefix)" ;;
  esac
}

check_body() {
  case "$1" in
    tmp/*) ;;
    *) refuse "the body must be a file under tmp/, got '$1'" ;;
  esac
  case "$1" in
    *..* | *[!A-Za-z0-9._/-]*) refuse "'$1' is not a plain path under tmp/" ;;
  esac
  [ ! -L "$1" ] || refuse "'$1' is a symlink, and a link can point outside the project"
  [ -f "$1" ] || refuse "'$1' does not exist -- write the body with the Write tool first"
}

[ "$#" -ge 1 ] || refuse "$usage"
action="$1"
shift

here="$(cd "$(dirname "$0")" && pwd)"

case "$action" in
  pr-create)
    [ "$#" -eq 4 ] || refuse "$usage"
    check_repo "$1"
    check_branch "$2"
    [ -n "$3" ] || refuse "a PR needs a title"
    check_body "$4"
    set -- sh "$here/gh-agent.sh" api --method POST "repos/DeckOfPandas/$1/pulls" \
      -f "title=$3" -f "head=$2" -f "base=main" -F "body=@$4" \
      --jq '[.number, .html_url, .user.login] | @tsv'
    ;;
  pr-body)
    [ "$#" -eq 3 ] || refuse "$usage"
    check_repo "$1"
    check_number "$2"
    check_body "$3"
    set -- sh "$here/gh-agent.sh" api --method PATCH "repos/DeckOfPandas/$1/pulls/$2" \
      -F "body=@$3" \
      --jq '[.number, .html_url, .user.login, .state] | @tsv'
    ;;
  comment)
    [ "$#" -eq 3 ] || refuse "$usage"
    check_repo "$1"
    check_number "$2"
    check_body "$3"
    set -- sh "$here/gh-agent.sh" api --method POST "repos/DeckOfPandas/$1/issues/$2/comments" \
      -F "body=@$3" \
      --jq '[.html_url, .user.login] | @tsv'
    ;;
  *)
    refuse "'$action' is not a write this wrapper makes. $usage"
    ;;
esac

if [ -n "${AGENT_WRAPPER_DRY_RUN:-}" ]; then
  printf '%s\n' "$@"
  exit 0
fi
exec "$@"
