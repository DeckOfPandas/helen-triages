#!/bin/sh
# Ask github.com, logged OUT, whether a page is visible: prints the HTTP status.
#
# WHY THIS EXISTS (2026-09-15). CLAUDE.md, after the agent account was flagged
# as spam on 2026-09-14: "when Helen says she cannot see something the API says
# exists, believe her first and curl the page anonymously -- a public URL
# returning 404 while the API returns 200 is the flag." The check itself
# (`curl -s -o /dev/null -w '%{http_code}' <url>`) asked Helen every time it ran:
# it names a path outside the project, and a bare `curl` accepts any URL and
# any option, so no allow rule for it could be narrow. Helen: "please find a way
# into scripts that can be statically analysed so read/write scope can be
# checked without asking me."
#
# USAGE:
#   sh scripts/github-public-status.sh https://github.com/DeckOfPandas/helen-triages/pull/1083
#   sh scripts/github-public-status.sh https://github.com/DeckOfPandas-agentic-claude
#
# Prints one line, the status: 200 is visible, 404 on something the API can see
# is hidden. It reads nothing and writes nothing, follows no redirect, and sends
# no credential -- curl does not read the gh token variables, and none is passed.
#
# THE URL MUST BE ON github.com, UNDER DeckOfPandas OR ONE OF THE TWO AGENT
# ACCOUNTS, and plain: no `..`, no `@` (userinfo), nothing a shell would treat
# specially. Anything else is refused before curl runs.
#
# AGENT_WRAPPER_DRY_RUN=1 prints the command it would run and exits, for
# tests/test_agent_wrappers.py.
set -eu

refuse() {
  echo "github-public-status.sh: refused -- $1" >&2
  exit 2
}

[ "$#" -eq 1 ] || refuse "usage: sh scripts/github-public-status.sh https://github.com/DeckOfPandas/..."
url="$1"

case "$url" in
  https://github.com/DeckOfPandas | https://github.com/DeckOfPandas/*) ;;
  https://github.com/DeckOfPandas-agentic | https://github.com/DeckOfPandas-agentic/*) ;;
  https://github.com/DeckOfPandas-agentic-claude | https://github.com/DeckOfPandas-agentic-claude/*) ;;
  *) refuse "'$url' is not a github.com page under DeckOfPandas or an agent account" ;;
esac
case "$url" in
  *..* | *@* | *[!A-Za-z0-9._/:#?=%-]*) refuse "'$url' is not a plain URL" ;;
esac

set -- curl --silent --output /dev/null --write-out '%{http_code}\n' \
  --max-time 20 --proto '=https' "$url"

if [ -n "${AGENT_WRAPPER_DRY_RUN:-}" ]; then
  printf '%s\n' "$@"
  exit 0
fi
exec "$@"
