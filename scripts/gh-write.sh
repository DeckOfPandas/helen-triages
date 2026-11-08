#!/bin/sh
# The GitHub writes a session makes routinely, each checked. It builds the
# `gh api` call itself and accepts nothing it does not understand, which is
# why .claude/settings.json can allow it unasked.
#
# USAGE -- a body is always a file under tmp/, written with the Write tool:
#   sh scripts/gh-write.sh pr-create    <repo> <branch> "<title>" tmp/<body>.md
#   sh scripts/gh-write.sh pr-body      <repo> <number> tmp/<body>.md
#   sh scripts/gh-write.sh comment      <repo> <number> tmp/<body>.md
#   sh scripts/gh-write.sh issue-create <repo> "<title>" tmp/<body>.md [<label>]
#   sh scripts/gh-write.sh issue-label  <repo> <number> <label>
#   sh scripts/gh-write.sh label-create <repo> <label> <rrggbb>
#
# <repo> is a bare name from GH_REPOS in the GitHub config; a repo in
# PR_ONLY_REPOS takes pr-create and pr-body only. A PR's base is
# always main and its head never is. `comment` and `issue-label` take an
# issue or PR number. A label is letters, digits, dots, dashes, underscores
# and single spaces; a colour is six hex digits with no #. `issue-label` and
# `issue-create` check that the label already exists, and remove none. One label per issue, and never issues in
# a burst.
#
# It cannot merge, approve, close, delete, change a title or state, or touch
# settings. Prints the login GitHub recorded, so the author is read, not assumed.
set -eu

WRAPPER=gh-write.sh
here="$(cd "$(dirname "$0")" && pwd)"
. "$here/_github_conf.sh"
load_conf

usage="usage: sh scripts/gh-write.sh pr-create <repo> <branch> \"<title>\" tmp/<body>.md | pr-body <repo> <number> tmp/<body>.md | comment <repo> <number> tmp/<body>.md | issue-create <repo> \"<title>\" tmp/<body>.md [<label>] | issue-label <repo> <number> <label> | label-create <repo> <label> <rrggbb>"

check_label() {
  case "$1" in
    '' | -* | ' '* | *' ' | *'  '* | *[!A-Za-z0-9._\ -]*)
      refuse "'$1' is not a plain label name (letters, digits, . _ - and single spaces)" ;;
  esac
}

# A label's URL path segment: the space is the only character check_label
# lets through that a path cannot carry.
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

# GitHub creates a label it is given that does not exist, so a typo becomes a
# new label. label-create is the only way one is made. Skipped in a dry run,
# which never reaches the network.
require_label() {
  [ -z "${AGENT_WRAPPER_DRY_RUN:-}" ] || return 0
  sh "$here/gh-agent.sh" api --method GET \
    "repos/$GH_OWNER/$1/labels/$(encode_label "$2")" --jq .name >/dev/null 2>&1 \
    || refuse "'$2' is not an existing label on $1 -- label-create makes one"
}

check_colour() {
  case "$1" in
    [0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]) ;;
    *) refuse "'$1' is not six hex digits" ;;
  esac
}

check_number() {
  case "$1" in
    '' | *[!0-9]* | 0*) refuse "'$1' is not an issue or PR number" ;;
  esac
}

check_branch() {
  case "$1" in
    '' | main | master | refs/* | -* | *..* | */ | *[!A-Za-z0-9._/-]*)
      refuse "'$1' is not a branch this wrapper opens a PR from (never main, no options, no owner: prefix)" ;;
  esac
}

# A body outside tmp/, or reached through `..` or a symlink, would let gh read
# and post a file from anywhere.
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

case "$action" in
  pr-create)
    [ "$#" -eq 4 ] || refuse "$usage"
    check_repo "$1"
    check_branch "$2"
    [ -n "$3" ] || refuse "a PR needs a title"
    check_body "$4"
    set -- sh "$here/gh-agent.sh" api --method POST "repos/$GH_OWNER/$1/pulls" \
      -f "title=$3" -f "head=$2" -f "base=main" -F "body=@$4" \
      --jq '[.number, .html_url, .user.login] | @tsv'
    ;;
  pr-body)
    [ "$#" -eq 3 ] || refuse "$usage"
    check_repo "$1"
    check_number "$2"
    check_body "$3"
    set -- sh "$here/gh-agent.sh" api --method PATCH "repos/$GH_OWNER/$1/pulls/$2" \
      -F "body=@$3" \
      --jq '[.number, .html_url, .user.login, .state] | @tsv'
    ;;
  comment)
    [ "$#" -eq 3 ] || refuse "$usage"
    check_issue_repo "$1"
    check_number "$2"
    check_body "$3"
    set -- sh "$here/gh-agent.sh" api --method POST "repos/$GH_OWNER/$1/issues/$2/comments" \
      -F "body=@$3" \
      --jq '[.html_url, .user.login] | @tsv'
    ;;
  issue-create)
    [ "$#" -eq 3 ] || [ "$#" -eq 4 ] || refuse "$usage"
    check_issue_repo "$1"
    [ -n "$2" ] || refuse "an issue needs a title"
    check_body "$3"
    if [ "$#" -eq 4 ]; then
      check_label "$4"
      require_label "$1" "$4"
      set -- sh "$here/gh-agent.sh" api --method POST "repos/$GH_OWNER/$1/issues" \
        -f "title=$2" -F "body=@$3" -f "labels[]=$4" \
        --jq '[.number, .html_url, .user.login] | @tsv'
    else
      set -- sh "$here/gh-agent.sh" api --method POST "repos/$GH_OWNER/$1/issues" \
        -f "title=$2" -F "body=@$3" \
        --jq '[.number, .html_url, .user.login] | @tsv'
    fi
    ;;
  issue-label)
    [ "$#" -eq 3 ] || refuse "$usage"
    check_issue_repo "$1"
    check_number "$2"
    check_label "$3"
    require_label "$1" "$3"
    set -- sh "$here/gh-agent.sh" api --method POST "repos/$GH_OWNER/$1/issues/$2/labels" \
      -f "labels[]=$3" \
      --jq '[.[].name] | @tsv'
    ;;
  label-create)
    [ "$#" -eq 3 ] || refuse "$usage"
    check_issue_repo "$1"
    check_label "$2"
    check_colour "$3"
    set -- sh "$here/gh-agent.sh" api --method POST "repos/$GH_OWNER/$1/labels" \
      -f "name=$2" -f "color=$3" \
      --jq '[.name, .color] | @tsv'
    ;;
  *)
    refuse "'$action' is not a write this wrapper makes. $usage"
    ;;
esac

run_or_print "$@"
