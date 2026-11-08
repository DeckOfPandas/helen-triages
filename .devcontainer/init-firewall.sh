#!/bin/bash
# Default-deny outbound traffic, then allow only the hosts Claude Code and the
# GitHub tooling need, plus /etc/claude-kit/allowed-domains (written at build
# time from kit.env's toggles and EXTRA_ALLOWED_DOMAINS). run.sh --firewall
# runs this as root before the shell starts.
#
# It takes no arguments on purpose: the user may run it through sudo, so an
# argument would let anything inside the container widen its own allowlist.
#
# Names are resolved ONCE, when this runs. A host whose CDN rotates addresses
# can start failing mid-session; re-running this script re-resolves.

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

ipset destroy allowed-domains 2>/dev/null || true
ipset create allowed-domains hash:net

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
    ipset add allowed-domains "$ip/32" 2>/dev/null || true
    echo "  $domain -> $ip"
  done
done

# The Docker bridge gateway, so DNS and any host-side proxy keep working.
read -r -a route <<< "$(ip route show default)"
if [ "${route[0]:-}" = default ] && [ -n "${route[2]:-}" ]; then
  ipset add allowed-domains "${route[2]}/32" 2>/dev/null || true
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
