#!/bin/bash
# Default-deny outbound traffic, then allow only the hosts Claude Code and the
# GitHub tooling need, plus /etc/claude-kit/allowed-domains (written at build
# time from kit.env's toggles and EXTRA_ALLOWED_DOMAINS). run.sh runs this as
# root before the shell starts, unless given --no-firewall.
#
# It takes no arguments on purpose: the user may run it through sudo, so an
# argument would let anything inside the container widen its own allowlist.
#
# GitHub is allowed by its published ranges (api.github.com/meta), because
# github.com rotates its address within minutes. Other names are resolved
# when this runs; re-running it re-resolves them, and is safe while the
# firewall is live: the list is built aside and swapped in whole.

set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "init-firewall.sh must run as root (sudo /usr/local/bin/init-firewall.sh)" >&2
  exit 1
fi

DOMAINS=(
  api.anthropic.com
  claude.ai
  platform.claude.com
  statsig.anthropic.com
  sentry.io
  registry.npmjs.org
  storage.googleapis.com
  github.com
  api.github.com
  raw.githubusercontent.com
  codeload.github.com
  objects.githubusercontent.com
)

if [ -f /etc/claude-kit/allowed-domains ]; then
  while IFS= read -r line; do
    [ -n "$line" ] && DOMAINS+=("$line")
  done < /etc/claude-kit/allowed-domains
fi

# The live set cannot be destroyed while a rule uses it, so the new list is
# built in NEW_SET and swapped in at the end.
NEW_SET=allowed-domains-new
ipset destroy "$NEW_SET" 2>/dev/null || true
ipset create "$NEW_SET" hash:net

echo "Fetching GitHub's published ranges..."
meta="$(curl -fsS --max-time 10 https://api.github.com/meta 2>/dev/null || true)"
ranges="$(printf '%s' "$meta" | jq -r '(.git + .web + .api)[] | select(test(":") | not)' 2>/dev/null || true)"
if [ -z "$ranges" ]; then
  echo "  WARNING: no ranges from api.github.com/meta -- GitHub falls back to DNS" >&2
fi
count=0
for net in $ranges; do
  ipset add "$NEW_SET" "$net" -exist
  count=$((count + 1))
done
echo "  $count GitHub ranges"

echo "Resolving allowlisted domains..."
for domain in "${DOMAINS[@]}"; do
  if [[ ! "$domain" =~ ^[A-Za-z0-9.-]+$ ]]; then
    echo "  WARNING: '$domain' is not a hostname -- skipping" >&2
    continue
  fi
  ips="$(dig +short "$domain" A | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' || true)"
  if [ -z "$ips" ]; then
    echo "  WARNING: could not resolve $domain -- skipping" >&2
    continue
  fi
  for ip in $ips; do
    ipset add "$NEW_SET" "$ip/32" -exist
    echo "  $domain -> $ip"
  done
done

# The Docker bridge gateway, so DNS and any host-side proxy keep working.
read -r -a route <<< "$(ip route show default)"
if [ "${route[0]:-}" = default ] && [ -n "${route[2]:-}" ]; then
  ipset add "$NEW_SET" "${route[2]}/32" -exist
fi

if ipset list -n allowed-domains >/dev/null 2>&1; then
  ipset swap "$NEW_SET" allowed-domains
  ipset destroy "$NEW_SET"
else
  ipset rename "$NEW_SET" allowed-domains
fi

iptables -F OUTPUT 2>/dev/null || true
iptables -A OUTPUT -o lo -j ACCEPT
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT
iptables -A OUTPUT -m set --match-set allowed-domains dst -j ACCEPT
iptables -P OUTPUT DROP

echo ""
echo "Firewall active. Self-test:"
if curl -s --max-time 5 -o /dev/null https://example.com 2>/dev/null; then
  echo "  FAIL: https://example.com should have been blocked but succeeded"
else
  echo "  OK: https://example.com blocked"
fi
if curl -s --max-time 5 -o /dev/null https://api.github.com 2>/dev/null; then
  echo "  OK: https://api.github.com allowed"
else
  echo "  FAIL: https://api.github.com should have been allowed but failed"
fi
if curl -s --max-time 5 -o /dev/null https://github.com 2>/dev/null; then
  echo "  OK: https://github.com allowed"
else
  echo "  FAIL: https://github.com should have been allowed but failed"
fi
