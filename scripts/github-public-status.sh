#!/bin/sh
# Ask github.com, logged OUT, whether a page is visible: prints the HTTP status.
# A public URL returning 404 while the API returns 200 is how a spam flag on
# the agent account shows: GitHub hides what the account wrote from everyone
# else while the API reports it normal.
#
# USAGE:
#   sh scripts/github-public-status.sh https://github.com/DeckOfPandas/helen-triages/pull/1083
#   sh scripts/github-public-status.sh https://github.com/DeckOfPandas-agentic-claude
#
# Prints one line, the status: 200 is visible, 404 on something the API can see
# is hidden. It reads no file and writes none (the body goes to /dev/null),
# follows no redirect, and sends no credential.
#
# REFUSES anything but one URL on https://github.com under DeckOfPandas,
# DeckOfPandas-agentic or DeckOfPandas-agentic-claude, with no `..`, no `@`
# (userinfo) and only letters, digits and `._/:#?=%-`. A bare `curl` accepts
# any URL and any option, and `-o <path>` writes a file anywhere, so no allow
# rule for it could be narrow; this script's one argument is checked instead.
#
# AGENT_WRAPPER_DRY_RUN=1 prints the command instead of running it, one
# argument per line, for tests/test_agent_wrappers.py.
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
