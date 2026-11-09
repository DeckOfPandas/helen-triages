#!/bin/sh
# Which host:container port pairs this container publishes, and whether each
# container port is free: one line per pair, as `7002:7002 free`.
#
# USAGE:  sh scripts/kit-ports.sh
#
# run.sh passes the pairs in force as KIT_PORTS; reading it here keeps a `$`
# off the command line, where Claude Code cannot check it and asks. When it is
# unset (a container run.sh did not start), PORTS in .devcontainer/kit.env is
# read instead. Takes no arguments, reads only those and `ss -ltn`, and writes
# nothing. Exits 1 when no pair is published, 2 on a refusal.
set -eu

WRAPPER=kit-ports.sh
refuse() { echo "$WRAPPER: refused -- $1" >&2; exit 2; }
[ "$#" -eq 0 ] || refuse "usage: sh scripts/kit-ports.sh (no arguments)"

if [ -n "${KIT_PORTS+set}" ]; then
  pairs="$KIT_PORTS"
else
  here="$(cd "$(dirname "$0")" && pwd)"
  pairs=""
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      PORTS=*) pairs="${line#PORTS=}" ;;
    esac
  done < "$here/../.devcontainer/kit.env"
  pairs="$(printf '%s' "$pairs" | tr -d "\"'")"
  echo "(KIT_PORTS is unset, so these are kit.env's PORTS)"
fi

found=0
for pair in $pairs; do
  case "$pair" in
    *[!0-9:]* | :* | *: | *:*:*) refuse "'$pair' is not host:container" ;;
    *:*) ;;
    *) refuse "'$pair' is not host:container" ;;
  esac
  found=1
  inside="${pair#*:}"
  if ! command -v ss > /dev/null 2>&1; then
    state="unknown (no ss)"
  elif ss -Hltn "sport = :$inside" | grep -q .; then
    state="in use"
  else
    state="free"
  fi
  echo "$pair $state"
done

if [ "$found" = 0 ]; then
  echo "no ports are published: add host:container pairs to PORTS in .devcontainer/kit.env" >&2
  exit 1
fi
