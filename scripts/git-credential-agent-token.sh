#!/bin/sh
# Git credential helper for AGENT_GH_TOKEN. Git calls it when it needs to
# authenticate, and the token goes to git over a pipe: never into a URL or
# .git/config, where `git remote -v` or `git config -l` would print it.
#
# Never call it and never `git config` it. The git-*-agent.sh wrappers pass it
# with `-c credential.helper=...` for one invocation each, by absolute path:
# configured in the shared .git/config, git would run it relative to each
# worktree's top level and fail wherever the file is absent.
#
# Only `get` is answered; ignoring `store` and `erase` means git never writes
# the token down.

case "$1" in
  get)
    WRAPPER=git-credential-agent-token.sh
    here="$(cd "$(dirname "$0")" && pwd)"
    . "$here/_github_conf.sh"
    load_conf
    printf 'username=%s\n' "$GH_AGENT_USER"
    printf 'password=%s\n' "${AGENT_GH_TOKEN}"
    ;;
esac
