#!/bin/bash
# Optional egress allowlist for the devcontainer. NOT run automatically --
# see .devcontainer/README.md "Phase 2" for when and how to use this.
#
# Default-deny outbound traffic, then allow only the specific hosts Claude
# Code and this project's tooling actually need: the Anthropic API and
# claude.ai (for login and requests), GitHub (git/gh), npm's registry
# (JS test tooling), and rubygems.org (bundler/Jekyll).
#
# This is a defense-in-depth layer, not the primary protection -- the
# primary protection is that the container's filesystem simply does not
# contain ~/.ssh, ~/.bashrc, or anything else from the host home directory
# in the first place (nothing outside the bind-mounted project directory
# is ever visible to it). A compromised or mistaken command inside the
# container that tries to phone a random host home gets refused by this;
# a command that tries to read a file that was never mounted in has
# nothing to send regardless.

set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "init-firewall.sh must run as root (use: sudo init-firewall.sh)" >&2
  exit 1
fi

ALLOWED_DOMAINS=(
  api.anthropic.com
  claude.ai
  platform.claude.com
  github.com
  api.github.com
  raw.githubusercontent.com
  codeload.github.com
  objects.githubusercontent.com
  registry.npmjs.org
  rubygems.org
  index.rubygems.org
  storage.googleapis.com
)

ipset destroy allowed-domains 2>/dev/null || true
ipset create allowed-domains hash:net

echo "Resolving allowlisted domains..."
for domain in "${ALLOWED_DOMAINS[@]}"; do
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

# The Docker bridge gateway, so DNS resolution and any host-side proxy
# keep working.
GATEWAY_IP="$(ip route | awk '/default/ {print $3}')"
if [ -n "$GATEWAY_IP" ]; then
  ipset add allowed-domains "$GATEWAY_IP/32" 2>/dev/null || true
fi

# Flush any prior rules from a previous run of this script.
iptables -F OUTPUT 2>/dev/null || true

iptables -A OUTPUT -o lo -j ACCEPT
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT
iptables -A OUTPUT -m set --match-set allowed-domains dst -j ACCEPT
iptables -P OUTPUT DROP

echo ""
echo "Firewall active. Self-test:"
if curl -s --max-time 5 -o /dev/null -w '' https://example.com 2>/dev/null; then
  echo "  FAIL: https://example.com should have been blocked but succeeded"
else
  echo "  OK: https://example.com correctly blocked"
fi
if curl -s --max-time 5 -o /dev/null https://api.github.com 2>/dev/null; then
  echo "  OK: https://api.github.com correctly allowed"
else
  echo "  FAIL: https://api.github.com should have been allowed but failed"
fi
