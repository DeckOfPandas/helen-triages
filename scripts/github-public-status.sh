#!/bin/sh
# Ask github.com, logged OUT, whether a page is visible, and print the status.
# A page that is 404 here while the API returns 200 is how a spam flag on the
# agent account shows: GitHub hides what it wrote from everyone else.
#
# USAGE:  sh scripts/github-public-status.sh https://github.com/<owner>/<repo>/pull/12
#
# Sends no credential, follows no redirect, writes no file. REFUSES anything
# but one https://github.com URL under GH_OWNER or GH_AGENT_USER, with no `..`,
# no `@` and only plain URL characters: a bare `curl -o <path>` writes anywhere,
# so no allow rule for curl itself could be narrow.
set -eu

WRAPPER=github-public-status.sh
here="$(cd "$(dirname "$0")" && pwd)"
. "$here/_github_conf.sh"
load_conf

[ "$#" -eq 1 ] || refuse "usage: sh scripts/github-public-status.sh https://github.com/$GH_OWNER/..."
url="$1"

case "$url" in
  "https://github.com/$GH_OWNER" | "https://github.com/$GH_OWNER/"*) ;;
  "https://github.com/$GH_AGENT_USER" | "https://github.com/$GH_AGENT_USER/"*) ;;
  *) refuse "'$url' is not a github.com page under $GH_OWNER or $GH_AGENT_USER" ;;
esac
case "$url" in
  *..* | *@* | *[!A-Za-z0-9._/:#?=%-]*) refuse "'$url' is not a plain URL" ;;
esac

run_or_print curl --silent --output /dev/null --write-out '%{http_code}\n' \
  --max-time 20 --proto '=https' "$url"
