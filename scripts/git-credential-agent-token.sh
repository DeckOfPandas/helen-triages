#!/bin/sh
# Git credential helper for AGENT_GH_TOKEN.
#
# WHY THIS EXISTS. CLAUDE.md's documented pattern for pushing/cloning a
# private repo in the devcontainer was to build the URL by hand with the
# token embedded as the userinfo password -- `scheme, then the account name,
# a colon, the token, an @, then github.com`. That works, but git then
# stores the resulting URL -- token included -- in
# the repo's own `.git/config` as the `origin` remote. Every later command
# that surfaces a remote URL (`git remote -v`, `git remote show`, `git config
# -l`, `cat .git/config`, some git error messages) then prints the token in
# plain text. Measured 2026-09-10: a routine `git remote -v`, run for an
# unrelated reason (MANUAL §2.1 asks you to check which remote a clone points
# at), printed the token straight into a transcript.
#
# This is the fix: a git credential helper. Configure it PER REPO (never
# globally -- CLAUDE.md forbids touching anything outside this project).
# MIND THE PATH: git runs a repo's configured helper with its cwd at THAT
# repo's own top level, not this project's root, so the path is one level up
# from inside a nested drafts repo:
#
#     git -C <drafts-repo> config credential.helper \
#         '!sh ../scripts/git-credential-agent-token.sh'
#
# Clone and push then use a PLAIN url with no embedded credential --
# `https://github.com/OWNER/REPO.git` -- and git calls this helper at the
# moment it needs to authenticate. The token is read from the environment
# right here and handed to git over a pipe; it is never written into a URL,
# never written into `.git/config`, and so never something a later, unrelated
# command can print by accident. Same principle CLAUDE.md already applies to
# `gh` (`scripts/gh-agent.sh`): read the secret from the environment at the
# point of use, and keep its name out of every call site.
#
# For the FIRST clone of a repo that doesn't exist locally yet, there is
# nothing to configure the helper ON, so pass it for that one invocation with
# `-c` instead (this does not persist anywhere). Run from this project's own
# root, same as every other command, so the path has no `../`:
#
#     git -c credential.helper='!sh scripts/git-credential-agent-token.sh' \
#         clone https://github.com/OWNER/REPO.git DEST
#
# Then configure it in the new clone with the OTHER form above (`../scripts/
# ...`, run from inside DEST) so a later `git -C DEST push`/`fetch` picks it
# up too. Measured both forms 2026-09-10, cloning and fetching
# helen-triages-food-private -- the wrong path (`scripts/...` from inside the
# nested repo) fails with "cannot open ... No such file", not a silent
# no-op, so a mixed-up path is at least loud.
#
# Needs no execute bit -- CLAUDE.md forbids chmod without asking, and this is
# invoked as `sh scripts/git-credential-agent-token.sh`, same as every other
# script in this repo.
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
