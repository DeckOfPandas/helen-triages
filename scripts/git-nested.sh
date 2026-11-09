#!/bin/sh
# Run a short, fixed list of git commands inside a nested clone, without a `cd`
# or `git -C` at the call site: guard-unanalyzable-bash.py refuses both, and a
# tmp/ script asks the human every time.
#
# USAGE:  sh scripts/git-nested.sh <dir> <verb> [args]
#
#   sh scripts/git-nested.sh _drafts status --short
#   sh scripts/git-nested.sh _drafts checkout -b tidy/what-this-is
#   sh scripts/git-nested.sh _drafts add -- .
#   sh scripts/git-nested.sh _drafts commit -F tmp/msg.txt
#
# What it accepts is a list, not a pattern, because an allow rule runs it unasked:
#
#   dir       a folder path named in NESTED_DIRS in the GitHub config, holding
#             .git: `_drafts`, or a clone inside a clone, `site/_drafts`.
#   status    --short, --porcelain, --branch.
#   diff      --stat, --shortstat, --name-only, --name-status, --cached, then
#             plain refs and paths.
#   log       --oneline, --stat, --name-only, -<N>, then plain refs and paths.
#   show      --stat, --name-only, then plain refs.
#   branch    --show-current only.
#   checkout  -b <new-branch> only: switching to an existing branch is how a
#             session ends up on `main`.
#   add       -- then plain paths.
#   commit    -F <file under tmp/> only, never on `main` or a detached HEAD.
#             guard-main-branch.py sees no `-C` here and would check the
#             outer repo, so this script refuses it itself.
#
# Everything else is refused. "Plain" is letters, digits and `_ . / @ ~ ^ -`,
# not starting with `-` or `/`, with no `..`.
#
# The nested .git/ lies inside the working directory, where the session can
# write, so every call disables hooks and fsmonitor, and diff, log and show run
# with --no-ext-diff --no-textconv: none of them can run a program a repo's
# config names. A clean/smudge filter set in that config still runs on `add`;
# list only clones the agent made.
set -eu

WRAPPER=git-nested.sh
here="$(cd "$(dirname "$0")" && pwd)"
. "$here/_github_conf.sh"
load_conf

plain() {
  case "$1" in
    "" | -* | /* | *..* | *[!A-Za-z0-9_./@~^-]*) return 1 ;;
  esac
  return 0
}

# options_or_plain <allowed options, space-separated> <args...>
options_or_plain() {
  allowed="$1"
  shift
  for arg in "$@"; do
    case " $allowed " in
      *" $arg "*) continue ;;
    esac
    plain "$arg" || refuse "'$arg' is not an option '$verb' takes here, nor a plain ref or path"
  done
}

[ "$#" -ge 2 ] || refuse "usage: sh scripts/git-nested.sh <dir> <verb> [args]"
dir="$1"
verb="$2"
shift 2

[ -n "$NESTED_DIRS" ] || refuse "NESTED_DIRS in $conf_name is empty: name the nested clones there first"
# shellcheck disable=SC2086
in_list "$dir" $NESTED_DIRS || refuse "'$dir' is not in NESTED_DIRS ($NESTED_DIRS)"

case "$verb" in
  status)
    for arg in "$@"; do
      case "$arg" in
        --short | --porcelain | --branch) ;;
        *) refuse "'$arg' is not an option 'status' takes here" ;;
      esac
    done
    ;;
  diff)
    options_or_plain "--stat --shortstat --name-only --name-status --cached" "$@"
    set -- --no-ext-diff --no-textconv "$@"
    ;;
  log)
    for arg in "$@"; do
      case "$arg" in
        -[0-9] | -[0-9][0-9] | -[0-9][0-9][0-9]) ;;
        *) options_or_plain "--oneline --stat --name-only" "$arg" ;;
      esac
    done
    set -- --no-ext-diff --no-textconv "$@"
    ;;
  show)
    options_or_plain "--stat --name-only" "$@"
    set -- --no-ext-diff --no-textconv "$@"
    ;;
  branch)
    [ "$#" -eq 1 ] && [ "$1" = "--show-current" ] \
      || refuse "'branch' takes --show-current and nothing else here"
    ;;
  checkout)
    [ "$#" -eq 2 ] && [ "$1" = "-b" ] \
      || refuse "'checkout' takes '-b <new-branch>' and nothing else here"
    plain "$2" || refuse "'$2' is not a branch name"
    case "$2" in
      main | master) refuse "'$2' is not a branch to create" ;;
    esac
    ;;
  add)
    [ "$#" -ge 2 ] && [ "$1" = "--" ] || refuse "'add' takes '--' and then paths"
    shift
    for arg in "$@"; do
      plain "$arg" || refuse "'$arg' is not a plain path"
    done
    set -- -- "$@"
    ;;
  commit)
    [ "$#" -eq 2 ] && [ "$1" = "-F" ] \
      || refuse "'commit' takes '-F <file under tmp/>' and nothing else here"
    file="$2"
    plain "$file" || refuse "'$file' is not a plain path"
    case "$file" in
      tmp/*) ;;
      *) refuse "'$file' is not under tmp/" ;;
    esac
    [ -f "$file" ] && [ ! -L "$file" ] || refuse "'$file' is not a regular file"
    # git -C resolves the message from inside the clone, at any depth, so it
    # gets the checkout's absolute path.
    set -- -F "$(pwd)/$file"
    ;;
  *)
    refuse "'$verb' is not one of status, diff, log, show, branch, checkout, add, commit"
    ;;
esac

set -- git -c core.hooksPath=/dev/null -c core.fsmonitor=false -C "$dir" "$verb" "$@"

if [ -z "${AGENT_WRAPPER_DRY_RUN:-}" ]; then
  [ -d "$dir/.git" ] || refuse "'$dir' holds no clone -- sh scripts/git-clone-agent.sh <repo> $dir"
  if [ "$verb" = commit ]; then
    current="$(git -C "$dir" branch --show-current)"
    case "$current" in
      "" | main | master) refuse "'$dir' is on '${current:-a detached HEAD}': branch first with checkout -b" ;;
    esac
  fi
fi

run_or_print "$@"
