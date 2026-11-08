#!/bin/sh
# Read the GitHub REST API as the agent account: GET only, configured repos
# only. It cannot write, which is why .claude/settings.json can allow it
# unasked; `gh-agent.sh api` cannot be allowed, because `api` is also the door
# to every write the token can make, a merge included.
#
# USAGE (quote an endpoint that carries a query string):
#   sh scripts/gh-read.sh <endpoint> [--fields a,b.c | --each a,b.c | --jq <expr>] [--paginate]
#
#   sh scripts/gh-read.sh repos/<owner>/<repo>/pulls/12 --fields state,merged_at,user.login
#   sh scripts/gh-read.sh 'repos/<owner>/<repo>/pulls?state=all&per_page=40' --each number,state,title
#
# REFUSES before gh runs: any other argument (`-X`, `--method`, `--input`,
# `-H`, `--hostname`, `-f`/`-F` change the method, body or host); an endpoint
# outside repos/<GH_OWNER>/<one of GH_REPOS>, or containing `..`; `env` in a jq
# expression or field list, since gh's jq can read the environment that holds
# the token; and a field list that is not plain names.
#
# Prefer --fields/--each to --jq: a quoted bracket or pipe in a wrapper's
# arguments makes Claude Code ask, so this builds the expression itself.
set -eu

WRAPPER=gh-read.sh
here="$(cd "$(dirname "$0")" && pwd)"
. "$here/_github_conf.sh"
load_conf

[ "$#" -ge 1 ] || refuse "usage: sh scripts/gh-read.sh <repos/$GH_OWNER/REPO/...> [--fields a,b | --each a,b | --jq <expr>] [--paginate]"

# `a,b.c` -> `[.a, .b.c] | @tsv`. Plain names only.
fields_to_jq() {
  case "$1" in
    '' | ,* | *, | *,,* | .* | *.,* | *,.* | *. | *..* | *[!A-Za-z0-9_.,]*)
      refuse "'$1' is not a comma-separated list of field names (letters, digits, _ and . only)" ;;
  esac
  list=""
  old_ifs="$IFS"
  IFS=,
  for field in $1; do
    list="${list:+$list, }.$field"
  done
  IFS="$old_ifs"
  printf '[%s] | @tsv' "$list"
}

endpoint="$1"
shift

case "$endpoint" in
  *..*) refuse "an endpoint may not contain '..'" ;;
esac
allowed=""
for repo in $GH_REPOS; do
  case "$endpoint" in
    "repos/$GH_OWNER/$repo" | "repos/$GH_OWNER/$repo/"* | "repos/$GH_OWNER/$repo?"*) allowed=1 ;;
  esac
done
[ -n "$allowed" ] || refuse "'$endpoint' is not under repos/$GH_OWNER/ and one of: $GH_REPOS"

jq=""
have_jq=""
paginate=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --jq | --fields | --each)
      [ "$#" -ge 2 ] || refuse "$1 needs a value"
      [ -z "$have_jq" ] || refuse "give one of --fields, --each and --jq, not two"
      case "$1" in
        --jq) jq="$2" ;;
        --fields) jq="$(fields_to_jq "$2")" ;;
        --each) jq=".[] | $(fields_to_jq "$2")" ;;
      esac
      have_jq=1
      shift 2
      ;;
    --paginate)
      paginate=1
      shift
      ;;
    *)
      refuse "'$1' -- this wrapper only reads. It takes an endpoint, --fields, --each or --jq, and --paginate"
      ;;
  esac
done

case "$jq" in
  *[Ee][Nn][Vv]*) refuse "a jq expression may not mention env: gh's jq can read the environment, which holds the token" ;;
esac

set -- sh "$here/gh-agent.sh" api --method GET "$endpoint"
[ -z "$paginate" ] || set -- "$@" --paginate
[ -z "$have_jq" ] || set -- "$@" --jq "$jq"
run_or_print "$@"
