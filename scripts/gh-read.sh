#!/bin/sh
# Read the GitHub REST API as DeckOfPandas-agentic: GET only, the three repos only.
#
# WHY THIS EXISTS (2026-09-11). Helen: "Please work out how to run sh commands in
# a way that can be statically analysed, so things remain safe without
# harrassing me for permissions all the time." Reads that no named `gh`
# subcommand covers (an issue's comments as JSON, a filtered PR list, a private
# repo's file) went through `sh scripts/gh-agent.sh api ...`, and that can never
# be allow-listed: `api` is also the door to every write the token can make --
# PATCH a PR body, and PUT .../pulls/N/merge, which IS a merge, on a token that
# since 2026-09-09 has nothing but a written rule between it and merging. So
# every read prompted. This wrapper cannot write, so it can be allow-listed, and
# `.claude/settings.json` allows `sh scripts/gh-read.sh *`.
#
# WHAT MAKES IT READ-ONLY. It builds the `gh` command itself and accepts nothing
# it does not understand: an endpoint, `--jq <expr>`, `--paginate`. Everything
# else -- `-X`, `--method`, `-f`/`-F` (either one switches gh to POST on its
# own), `--input`, `-H`, `--hostname` -- is refused before gh runs, and
# `--method GET` is always passed explicitly.
#
# THE THREE REPOS ONLY. CLAUDE.md: never act on any other repository. The
# endpoint must start `repos/DeckOfPandas/<one of the three>`, and may not
# contain `..`.
#
# AND NO `env` IN A --jq EXPRESSION. Measured 2026-09-11: gh's built-in jq can
# read the process environment (`env | length` printed 38), and gh-agent.sh
# hands gh the token through that environment. A jq expression that names
# `env` or `$ENV` is refused here; `guard-token-expansion.py` refuses the same
# thing on any other gh call.
#
# USAGE (quote the endpoint whenever it carries a query string):
#   sh scripts/gh-read.sh <endpoint> [--jq <expr>] [--paginate]
#
#   sh scripts/gh-read.sh repos/DeckOfPandas/helen-triages/issues/944/comments --jq '.[].body'
#   sh scripts/gh-read.sh 'repos/DeckOfPandas/helen-triages/pulls?state=all&per_page=40' --jq '.[] | [.number, .state, .title] | @tsv'
#
# A WRITE IS NOT THIS SCRIPT'S JOB. Use the named gh-agent.sh subcommands
# (allow-listed where routine), or for the one REST write the docs name -- a PR
# body, since `pr edit` fails on this token -- `sh scripts/gh-agent.sh api -X
# PATCH ...`, which prompts on purpose.
#
# AGENT_WRAPPER_DRY_RUN=1 prints the command it would run, one argument per
# line, and exits -- for tests/test_agent_wrappers.py, which proves the
# refusals and the accepted shapes without touching the network.
#
# Invoked via `sh` so it needs no execute bit, and it calls gh-agent.sh rather
# than naming the credential itself, so the token's name stays in one file.
set -eu

refuse() {
  echo "gh-read.sh: refused -- $1" >&2
  exit 2
}

[ "$#" -ge 1 ] || refuse "usage: sh scripts/gh-read.sh <repos/DeckOfPandas/REPO/...> [--jq <expr>] [--paginate]"
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
    --jq)
      [ "$#" -ge 2 ] || refuse "--jq needs an expression"
      jq="$2"
      have_jq=1
      shift 2
      ;;
    --paginate)
      paginate=1
      shift
      ;;
    *)
      refuse "'$1' -- this wrapper only reads, and takes an endpoint, --jq <expr> and --paginate. A write goes through gh-agent.sh"
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
