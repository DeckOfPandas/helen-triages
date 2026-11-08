#!/bin/sh
# Does a link resolve? Prints the HTTP status after redirects and the final
# address, one line: "200 https://where/it/ended". For an external link, and
# for a page on a branch's local server.
#
# USAGE:
#   sh scripts/check-link.sh https://example.org/page
#   sh scripts/check-link.sh http://localhost:4001/mysite/about/
#
# Sends no credential, writes no file (the body goes to /dev/null) and gives up
# after 30 seconds. An https address follows redirects over https only and
# sends a browser's user agent, because many sites refuse curl's own. A
# localhost address is plain http, follows no redirect, and reaches nothing but
# this machine.
#
# REFUSES anything but one https:// URL, or one http://localhost:<port>/ URL,
# of plain URL characters, with no `..` and no `@`: a bare `curl -o <path>`
# writes anywhere, so no allow rule for curl itself could be narrow, which is
# why this wrapper exists and .claude/settings.json allows it.
set -eu

WRAPPER=check-link.sh
here="$(cd "$(dirname "$0")" && pwd)"
. "$here/_github_conf.sh"

[ "$#" -eq 1 ] || refuse "usage: sh scripts/check-link.sh https://example.org/page"
url="$1"

case "$url" in
  *..* | *@* | *[!A-Za-z0-9._~/:#?=\&%+-]*) refuse "'$url' is not a plain URL" ;;
esac

case "$url" in
  https://?*)
    run_or_print curl --silent --output /dev/null --location --max-time 30 \
      --proto '=https' --proto-redir '=https' \
      --user-agent 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36' \
      --write-out '%{http_code} %{url_effective}\n' "$url"
    ;;
  http://localhost:[0-9]*/*)
    port="${url#http://localhost:}"
    port="${port%%/*}"
    case "$port" in
      *[!0-9]*) refuse "'$url' does not name a numeric localhost port" ;;
    esac
    run_or_print curl --silent --output /dev/null --max-time 30 \
      --proto '=http' \
      --write-out '%{http_code} %{url_effective}\n' "$url"
    ;;
  *) refuse "'$url' is not an https:// address or an http://localhost:<port>/ one" ;;
esac
