#!/bin/sh
# Git credential helper for AGENT_GH_TOKEN.
#
# WHY THIS EXISTS. CLAUDE.md's documented pattern for pushing and cloning a
# private repo in the devcontainer used to be a URL built by hand with the
# token as the userinfo password. That works, but git stores a CLONE's URL --
# token included -- in the repo's own `.git/config` as the `origin` remote, and
# every later command that surfaces a remote URL (`git remote -v`, `git remote
# show`, `git config -l`, `cat .git/config`, some git error messages) then
# prints the token in plain text. Measured 2026-09-10: a routine `git remote
# -v`, run for an unrelated reason (MANUAL §2.1 asks you to check which remote
# a clone points at), printed the token straight into a transcript.
#
# This is the fix: a git credential helper. Git calls it at the moment it
# needs to authenticate; the token is read from the environment right here and
# handed to git over a pipe. It is never written into a URL, never written
# into `.git/config`, and so never something a later, unrelated command can
# print by accident. Same principle CLAUDE.md already applies to `gh`
# (scripts/gh-agent.sh): read the secret from the environment at the point of
# use, and keep its name out of every call site.
#
# YOU DO NOT CALL THIS, AND YOU DO NOT `git config` IT. The three git wrappers
# -- scripts/git-clone-agent.sh, git-fetch-agent.sh and git-push-agent.sh --
# pass it to git for one invocation each, with `-c credential.helper=...` and
# an absolute path resolved from their own location, against a PLAIN url.
# That is the whole interface. The first version of this file said to
# configure it per repo with `git config credential.helper`, and the session
# that wrote it did so in the shared /workspace/.git/config, which every
# worktree reads: git then ran a relative path from each worktree's own top
# level, the file existed on one branch only, and every push from every other
# worktree printed "sh: 0: cannot open scripts/git-credential-agent-token.sh"
# -- harmless while the token was still in the URL, a hard failure the moment
# it wasn't. Per invocation depends on nothing but the checkout the wrapper is
# run from.
#
# Needs no execute bit -- CLAUDE.md forbids chmod without asking, and this is
# invoked as `sh <path>` by the wrappers, same as every other script here.
#
# Only answers `get`. `store`/`erase` are git offering to cache what it just
# used; saying nothing back means nothing is ever written down, which is the
# whole point.
case "$1" in
    get)
        printf 'username=%s\n' "DeckOfPandas-agentic"
        printf 'password=%s\n' "${AGENT_GH_TOKEN}"
        ;;
esac
