#!/bin/sh
# Show the uncommitted changes in the repository's main checkout from inside a
# git worktree, read-only. The main checkout is the directory that owns the
# shared .git, found through git itself, so no path is typed on the command
# line. It runs exactly one `git diff`, which writes nothing to either checkout,
# and its only output goes to stdout or to a file under tmp/, which is why
# .claude/settings.json can allow it unasked.
#
# USAGE:
#   sh scripts/git-diff-main-checkout.sh [--stat] [<path> ...]
#   sh scripts/git-diff-main-checkout.sh --patch tmp/<name>.patch [<path> ...]
#
# --patch writes the diff to the named file under tmp/, ready for
# `git apply tmp/<name>.patch` in the worktree.
#
# `git diff` shows changes to tracked files only: a file the main checkout has
# created but never added does not appear.
#
# REFUSES: a pathspec or patch file that is empty, absolute, starts `-`,
# contains `..` or any character outside [A-Za-z0-9._/-]; a patch file outside
# tmp/ or that is a symlink.
set -eu

refuse() {
  echo "git-diff-main-checkout.sh: refused -- $1" >&2
  exit 2
}

check_path() {
  case "$1" in
    '' | -* | /* | *..* | *[!A-Za-z0-9._/-]*)
      refuse "'$1' is not a plain relative path" ;;
  esac
}

mode=diff
out=
case "${1:-}" in
  --stat)
    mode=stat
    shift
    ;;
  --patch)
    [ "$#" -ge 2 ] || refuse "--patch needs a file under tmp/"
    out="$2"
    case "$out" in
      tmp/*) ;;
      *) refuse "the patch file must be under tmp/, got '$out'" ;;
    esac
    check_path "$out"
    [ ! -L "$out" ] || refuse "'$out' is a symlink, and a link can point outside the project"
    mode=patch
    shift 2
    ;;
esac

for p in "$@"; do
  check_path "$p"
done

common="$(git rev-parse --path-format=absolute --git-common-dir)"
main="$(dirname "$common")"

case "$mode" in
  stat) git -C "$main" diff --stat -- "$@" ;;
  diff) git -C "$main" diff -- "$@" ;;
  patch)
    git -C "$main" diff -- "$@" > "$out"
    echo "wrote $out"
    ;;
esac
