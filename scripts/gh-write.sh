#!/bin/sh
# The four GitHub writes a session makes routinely, over REST, each checked.
# It builds the `gh api` call itself and accepts nothing it does not
# understand, which is why `.claude/settings.json` can allow
# `sh scripts/gh-write.sh *`. A bare `gh-agent.sh api` cannot be allow-listed:
# `-F body=@<file>` is a read gh performs at run time, which the checker cannot
# see as a path, and `api` also reaches every other write the token can make,
# a merge included. DECISIONS §11.
#
# USAGE -- the body is always a file under tmp/, written with the Write tool:
#   sh scripts/gh-write.sh pr-create <repo> <branch> "<title>" tmp/<body>.md
#   sh scripts/gh-write.sh pr-body   <repo> <number> tmp/<body>.md
#   sh scripts/gh-write.sh comment   <repo> <number> tmp/<body>.md
#   sh scripts/gh-write.sh issue-label <repo> <number> "<label>"
#
# <repo> is one of the three, bare: helen-triages, helen-triages-food-private,
# helen-triages-cocktails-private. A PR's base is always main, and its head is
# never main. `comment` and `issue-label` take an issue or a PR number: GitHub
# files both under issues/. `issue-label` adds one label that already exists
# on the repo and removes none; GitHub would otherwise create a new label.
#
# REFUSES: an action other than those four, or the wrong number of arguments;
# a repo outside the three; a number that is not plain digits; a branch that
# is `main`, starts `-` or `refs/`, ends `/`, or contains `..` or anything but
# letters, digits and `._/-` (so no option and no `owner:` prefix); an empty
# title; and a body that is not an existing regular file with a plain path
# under tmp/, since `..` or a symlink would let gh read a file outside the
# project and post it; a label that is empty, starts `-`, has a leading,
# trailing or doubled space, or holds anything but letters, digits, `._-` and
# single spaces.
#
# It cannot merge, approve, close, delete, change a title or state, touch
# settings, or talk to any other repository. Those stay prompts.
#
# AGENT_WRAPPER_DRY_RUN=1 prints the command instead of running it, one
# argument per line, for tests/test_agent_wrappers.py.
#
# Invoked via `sh` so it needs no execute bit. It calls gh-agent.sh rather than
# naming the credential, so the token's name stays in one file.
set -eu

refuse() {
  echo "gh-write.sh: refused -- $1" >&2
  exit 2
}

usage="usage: sh scripts/gh-write.sh pr-create <repo> <branch> \"<title>\" tmp/<body>.md | pr-body <repo> <number> tmp/<body>.md | comment <repo> <number> tmp/<body>.md | issue-label <repo> <number> \"<label>\""

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

check_label() {
  case "$1" in
    '' | -* | ' '* | *' ' | *'  '* | *[!A-Za-z0-9._\ -]*)
      refuse "'$1' is not a plain label name" ;;
  esac
}

# A label's path segment: the only character check_label lets through that a
# URL path cannot carry is the space.
encode_label() {
  rest="$1"
  out=
  while :; do
    case "$rest" in
      *' '*) out="$out${rest%% *}%20"; rest="${rest#* }" ;;
      *) out="$out$rest"; break ;;
    esac
  done
  printf '%s' "$out"
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
  issue-label)
    [ "$#" -eq 3 ] || refuse "$usage"
    check_repo "$1"
    check_number "$2"
    check_label "$3"
    if [ -z "${AGENT_WRAPPER_DRY_RUN:-}" ]; then
      sh "$here/gh-agent.sh" api --method GET \
        "repos/DeckOfPandas/$1/labels/$(encode_label "$3")" --jq .name >/dev/null 2>&1 \
        || refuse "'$3' is not an existing label on $1"
    fi
    set -- sh "$here/gh-agent.sh" api --method POST "repos/DeckOfPandas/$1/issues/$2/labels" \
      -f "labels[]=$3" \
      --jq '[.[].name] | @tsv'
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
