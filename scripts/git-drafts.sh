#!/bin/sh
# Run a short, fixed list of git commands INSIDE one of the two nested drafts
# repos, without a `cd` and without a `git -C` at the call site.
#
# WHY THIS EXISTS (2026-10-02, #1258's tidy pass). `_food_drafts/` and
# `_cocktail_drafts/` are their own repos, so branching, reading a diff and
# committing there has to run git from inside them -- and the two ordinary ways
# to say that, `cd _food_drafts && git ...` and `git -C _food_drafts ...`, are
# both refused by guard-unanalyzable-bash.py, rightly. `tidy-drafts.md` still
# taught the first. So a session wrote a throwaway `tmp/` script, which asks
# Helen on every call (test_no_allow_rule_runs_a_tmp_script: "keep asking me
# please") -- eight prompts for one drafts pass. Helen, shown that: "gotcha,
# thanks. Yes please do it."
#
# USAGE:
#   sh scripts/git-drafts.sh <dir> <verb> [args]
#
#   sh scripts/git-drafts.sh _food_drafts status --short
#   sh scripts/git-drafts.sh _food_drafts branch --show-current
#   sh scripts/git-drafts.sh _food_drafts checkout -b tidy/what-this-is
#   sh scripts/git-drafts.sh _food_drafts diff --stat
#   sh scripts/git-drafts.sh _food_drafts add -- .
#   sh scripts/git-drafts.sh _food_drafts commit -F tmp/commit-msg.txt
#
# WHAT IT ACCEPTS IS A LIST, NOT A PATTERN, because an allow rule covers it and
# whatever it accepts runs without asking Helen:
#
#   dir       `_food_drafts` or `_cocktail_drafts`, spelled exactly.
#   status    --short, --porcelain, --branch.
#   diff      --stat, --shortstat, --name-only, --name-status, --cached, then
#             plain refs and paths. NOT `--output=` (writes a file anywhere),
#             `--no-index` (reads any two files on the disk) or `--ext-diff`.
#   log       --oneline, --stat, --name-only, -<N>, then plain refs and paths.
#   show      --stat, --name-only, then plain refs.
#   branch    --show-current and nothing else. Not `-D`, not `-m`.
#   checkout  `-b <new-branch>` and nothing else. Switching to an existing
#             branch is how a session ends up standing on `main`; `checkout --`
#             and a path is how uncommitted work is discarded.
#   add       `--` then plain paths (`.` included). The `--` is what makes every
#             later word a path and never `--chmod`.
#   commit    `-F <file under tmp/>` and nothing else. Never on `main`: the
#             guard-main-branch.py hook reads the command text, sees no `-C`,
#             and would check THIS repo's branch, so the refusal is made here.
#             Not `-a`, not `--amend`, not `--no-verify`.
#
# Everything else -- push, fetch, clone, reset, restore, stash, merge, rebase,
# config -- is refused. The three `git-*-agent.sh` wrappers do the network
# half; the destructive ones are Helen's.
#
# "PLAIN" MEANS letters, digits and `_ . / @ ~ ^ -`, not starting with `-` or
# `/` and containing no `..` -- so no option, no absolute path and no way out
# of the folder can be smuggled in as a ref or a path.
#
# AGENT_WRAPPER_DRY_RUN=1 prints the git command, one word per line, instead
# of running it, for tests/test_agent_wrappers.py. Invoked via `sh` so it needs
# no execute bit.
set -eu

refuse() {
  echo "git-drafts.sh: refused -- $1" >&2
  exit 2
}

plain() {
  case "$1" in
    "" | -* | /* | *..* | *[!A-Za-z0-9_./@~^-]*) return 1 ;;
  esac
  return 0
}

[ "$#" -ge 2 ] || refuse "usage: sh scripts/git-drafts.sh <dir> <verb> [args]"
dir="$1"
verb="$2"
shift 2

case "$dir" in
  _food_drafts | _cocktail_drafts) ;;
  *) refuse "'$dir' is not one of the two drafts folders" ;;
esac

# options_or_plain <allowed options, space separated> <args...>
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
    ;;
  log)
    for arg in "$@"; do
      case "$arg" in
        -[0-9] | -[0-9][0-9] | -[0-9][0-9][0-9]) ;;
        *) options_or_plain "--oneline --stat --name-only" "$arg" ;;
      esac
    done
    ;;
  show)
    options_or_plain "--stat --name-only" "$@"
    ;;
  branch)
    [ "$#" -eq 1 ] && [ "$1" = "--show-current" ] \
      || refuse "'branch' takes --show-current and nothing else here"
    ;;
  checkout)
    [ "$#" -eq 2 ] && [ "$1" = "-b" ] \
      || refuse "'checkout' takes '-b <new-branch>' and nothing else here"
    plain "$2" || refuse "'$2' is not a branch name"
    [ "$2" != "main" ] || refuse "'main' is not a branch to create"
    ;;
  add)
    [ "$#" -ge 2 ] && [ "$1" = "--" ] \
      || refuse "'add' takes '--' and then paths"
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
    [ -f "$file" ] && [ ! -L "$file" ] \
      || refuse "'$file' is not a regular file"
    # The drafts folder is one level down, so the message is one level up.
    set -- -F "../$file"
    ;;
  *)
    refuse "'$verb' is not one of status, diff, log, show, branch, checkout, add, commit"
    ;;
esac

if [ -n "${AGENT_WRAPPER_DRY_RUN:-}" ]; then
  printf '%s\n' git -C "$dir" "$verb" "$@"
  exit 0
fi

[ -d "$dir/.git" ] || refuse "'$dir' is not cloned here -- sh scripts/git-clone-agent.sh"

if [ "$verb" = "commit" ]; then
  current="$(git -C "$dir" branch --show-current)"
  case "$current" in
    "" | main) refuse "'$dir' is on '${current:-a detached HEAD}'; branch first with checkout -b" ;;
  esac
fi

git -C "$dir" "$verb" "$@"
