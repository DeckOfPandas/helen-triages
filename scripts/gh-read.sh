#!/bin/sh
# Read the GitHub REST API as DeckOfPandas-agentic-claude: GET only, the three
# repos only. It cannot write, which is why `.claude/settings.json` can allow
# `sh scripts/gh-read.sh *`; `gh-agent.sh api` cannot be allow-listed, because
# `api` is also the door to every write the token can make, a merge included.
# DECISIONS §11.
#
# USAGE (quote the endpoint whenever it carries a query string):
#   sh scripts/gh-read.sh <endpoint> [--fields a,b.c | --each a,b.c | --jq <expr>] [--paginate]
#
#   sh scripts/gh-read.sh repos/DeckOfPandas/helen-triages/pulls/1091 --fields state,merged_at,user.login
#   sh scripts/gh-read.sh 'repos/DeckOfPandas/helen-triages/pulls?state=all&per_page=40' --each number,state,title
#   sh scripts/gh-read.sh repos/DeckOfPandas/helen-triages/issues/944 --jq .body
#
# ACCEPTS an endpoint, at most one of --fields, --each and --jq, and
# --paginate. It builds the `gh` command itself and always passes
# `--method GET`.
#
# REFUSES, before gh runs:
#   * any other argument. `-X`, `--method`, `--input`, `-H` and `--hostname`
#     change the method, the body or the host, and `-f`/`-F` each switch gh to
#     POST on their own.
#   * an endpoint not under `repos/DeckOfPandas/<one of the three>`, or
#     containing `..`: the token never acts on another repository.
#   * a jq expression, or a field list, containing `env` in any case: gh's jq
#     can read the process environment, where gh-agent.sh puts the token.
#     guard-token-expansion.py refuses the same on any other gh call.
#   * a --fields or --each value that is not plain names: letters, digits and
#     `_`, with `.` inside a name's path and `,` between fields.
#
# PREFER --fields AND --each TO --jq. Claude Code reads a script's arguments as
# possible paths, and a bracket or a pipe makes one look computed, quotes or
# not, so guard-unanalyzable-bash.py refuses a quoted `[`, `]` or `|` given to
# any `sh scripts/` wrapper. This script builds the expression itself:
# `--fields a,b` is `[.a, .b] | @tsv` on one object, `--each a,b` is
# `.[] | [.a, .b] | @tsv` on a list.
#
# A write goes through scripts/gh-write.sh (a PR, a PR body, a comment);
# anything else goes through gh-agent.sh and asks, on purpose.
#
# AGENT_WRAPPER_DRY_RUN=1 prints the command instead of running it, one
# argument per line, for tests/test_agent_wrappers.py.
#
# Invoked via `sh` so it needs no execute bit. It calls gh-agent.sh rather than
# naming the credential, so the token's name stays in one file.
set -eu

refuse() {
  echo "gh-read.sh: refused -- $1" >&2
  exit 2
}

[ "$#" -ge 1 ] || refuse "usage: sh scripts/gh-read.sh <repos/DeckOfPandas/REPO/...> [--fields a,b | --each a,b | --jq <expr>] [--paginate]"

# `a,b.c` -> `[.a, .b.c] | @tsv`. Plain names only: letters, digits, `_`, and
# `.` between names; nothing jq could run.
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
case "$endpoint" in
  repos/DeckOfPandas/helen-triages | repos/DeckOfPandas/helen-triages/* | \
  repos/DeckOfPandas/helen-triages\?* | \
  repos/DeckOfPandas/helen-triages-food-private | repos/DeckOfPandas/helen-triages-food-private/* | \
  repos/DeckOfPandas/helen-triages-cocktails-private | repos/DeckOfPandas/helen-triages-cocktails-private/*) ;;
  *) refuse "'$endpoint' is not under repos/DeckOfPandas/ and one of the three repos (CLAUDE.md: never act on any other repository)" ;;
esac

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
      refuse "'$1' -- this wrapper only reads, and takes an endpoint, --fields, --each or --jq, and --paginate. A write goes through gh-write.sh"
      ;;
  esac
done

case "$jq" in
  *[Ee][Nn][Vv]*) refuse "a --jq expression may not mention env: gh's jq can read the environment, and the environment holds the token" ;;
esac

here="$(cd "$(dirname "$0")" && pwd)"

set -- sh "$here/gh-agent.sh" api --method GET "$endpoint"
if [ -n "$paginate" ]; then
  set -- "$@" --paginate
fi
if [ -n "$have_jq" ]; then
  set -- "$@" --jq "$jq"
fi

if [ -n "${AGENT_WRAPPER_DRY_RUN:-}" ]; then
  printf '%s\n' "$@"
  exit 0
fi
exec "$@"
