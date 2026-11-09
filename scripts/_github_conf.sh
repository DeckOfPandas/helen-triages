# Shared by the scripts/ GitHub wrappers: loads the GitHub config and checks
# arguments against it. Sourced, never run; the caller sets WRAPPER (its name,
# for messages) and `here` (its own directory) first.
#
# github.conf is PARSED, never sourced. Every allow rule naming a wrapper runs
# whatever these checks let through, so the config must not be able to run code
# or widen a check: unknown keys and out-of-charset values are refused.

refuse() {
  echo "$WRAPPER: refused -- $1" >&2
  exit 2
}

in_list() {
  item="$1"
  shift
  for candidate in "$@"; do
    [ "$candidate" = "$item" ] && return 0
  done
  return 1
}

# Trims and collapses whitespace, and drops quote characters.
_conf_clean() {
  set -f
  # shellcheck disable=SC2086
  set -- $(printf '%s' "$1" | tr -d "\"'")
  set +f
  printf '%s' "$*"
}

# github.local.conf, gitignored, replaces the committed placeholder copy. A
# worktree has no copy of an ignored file, so it reads the main checkout's,
# found through git rather than a typed path.
conf_path() {
  if [ -f "$here/github.local.conf" ]; then
    printf '%s' "$here/github.local.conf"
    return
  fi
  # git-remote-https hands the credential helper the pushing repo's GIT_DIR,
  # relative to a nested clone, which would hide this checkout's own.
  common="$(unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
    git -C "$here" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
  if [ -n "$common" ] && [ -f "$(dirname "$common")/scripts/github.local.conf" ]; then
    printf '%s' "$(dirname "$common")/scripts/github.local.conf"
    return
  fi
  printf '%s' "$here/github.conf"
}

load_conf() {
  GH_OWNER=""
  GH_REPOS=""
  GH_AGENT_USER=""
  MAIN_PUSH_REPOS=""
  PR_ONLY_REPOS=""
  NESTED_DIRS=""
  conf="$(conf_path)"
  conf_name="${conf##*/}"
  [ -f "$conf" ] || refuse "$conf is missing"
  # A Windows editor saves CRLF; without this every value ends in a CR, and
  # the checks below refuse names that look right.
  cr="$(printf '\r')"
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%"$cr"}"
    line="${line%%#*}"
    case "$line" in
      *[!\ \	]*) ;;
      *) continue ;;
    esac
    case "$line" in
      *=*) ;;
      *) refuse "$conf_name:'$line' is not KEY=value" ;;
    esac
    key="$(_conf_clean "${line%%=*}")"
    value="$(_conf_clean "${line#*=}")"
    case "$key" in
      GH_OWNER) GH_OWNER="$value" ;;
      GH_REPOS) GH_REPOS="$value" ;;
      GH_AGENT_USER) GH_AGENT_USER="$value" ;;
      MAIN_PUSH_REPOS) MAIN_PUSH_REPOS="$value" ;;
      PR_ONLY_REPOS) PR_ONLY_REPOS="$value" ;;
      NESTED_DIRS) NESTED_DIRS="$value" ;;
      *) refuse "$conf_name:unknown key '$key'" ;;
    esac
  done < "$conf"

  case "$GH_OWNER" in
    '' | -* | *[!A-Za-z0-9-]*) refuse "$conf_name:GH_OWNER '$GH_OWNER' is not a GitHub account name" ;;
    your-org) refuse "copy scripts/github.conf to scripts/github.local.conf and fill it in: GH_OWNER is still the placeholder" ;;
  esac
  case "$GH_AGENT_USER" in
    '' | -* | *[!A-Za-z0-9-]*) refuse "$conf_name:GH_AGENT_USER '$GH_AGENT_USER' is not a GitHub account name" ;;
  esac
  [ -n "$GH_REPOS" ] || refuse "$conf_name:GH_REPOS is empty"
  for repo in $GH_REPOS; do
    case "$repo" in
      -* | .* | *[!A-Za-z0-9._-]*) refuse "$conf_name:'$repo' is not a repository name" ;;
    esac
  done
  # shellcheck disable=SC2086
  for repo in $MAIN_PUSH_REPOS; do
    in_list "$repo" $GH_REPOS || refuse "$conf_name:MAIN_PUSH_REPOS names '$repo', which is not in GH_REPOS"
  done
  # A PR-only repo's main moves only by a merged PR, so it is never a main-push repo.
  # shellcheck disable=SC2086
  for repo in $PR_ONLY_REPOS; do
    in_list "$repo" $GH_REPOS || refuse "$conf_name:PR_ONLY_REPOS names '$repo', which is not in GH_REPOS"
    ! in_list "$repo" $MAIN_PUSH_REPOS || refuse "$conf_name:'$repo' is in both PR_ONLY_REPOS and MAIN_PUSH_REPOS"
  done
  # An entry is `path` or `path:repo`; the repo is only for
  # session-ground-truth.py's clone hint. NESTED_DIRS leaves holding paths only.
  # A path is folder names joined by `/`, each one plain and not starting `.`
  # or `-`, so it can name neither `..`, `.git`, an option nor anywhere outside.
  folders=""
  for entry in $NESTED_DIRS; do
    dir="${entry%%:*}"
    case "$dir" in
      "" | /* | */ | *//* | *[!A-Za-z0-9._/-]*)
        refuse "$conf_name:NESTED_DIRS '$dir' is not a folder path in this checkout" ;;
    esac
    rest="$dir"
    while [ -n "$rest" ]; do
      part="${rest%%/*}"
      case "$part" in
        -* | .*) refuse "$conf_name:NESTED_DIRS '$dir' has a folder name starting '-' or '.'" ;;
      esac
      case "$rest" in
        */*) rest="${rest#*/}" ;;
        *) rest="" ;;
      esac
    done
    case "$entry" in
      *:*)
        # shellcheck disable=SC2086
        in_list "${entry#*:}" $GH_REPOS || refuse "$conf_name:NESTED_DIRS '$entry' names a repo not in GH_REPOS" ;;
    esac
    folders="${folders:+$folders }$dir"
  done
  NESTED_DIRS="$folders"
  # shellcheck disable=SC2086
  set -- $GH_REPOS
  DEFAULT_REPO="$1"
}

check_repo() {
  # shellcheck disable=SC2086
  in_list "$1" $GH_REPOS || refuse "'$1' is not one of the repos in $conf_name ($GH_REPOS)"
}

# For a write other than opening or editing a PR: comment, issue, label.
check_issue_repo() {
  check_repo "$1"
  # shellcheck disable=SC2086
  ! in_list "$1" $PR_ONLY_REPOS || refuse "'$1' is in PR_ONLY_REPOS in $conf_name: open and edit PRs there, nothing else"
}

# A path relative to this checkout: no absolute path, no `..`, no option.
check_dir() {
  case "$1" in
    /* | *..* | -*) refuse "'$1' is outside this checkout" ;;
  esac
}

# Prints the command instead of running it, one argument per line, when
# AGENT_WRAPPER_DRY_RUN is set; tests/kit/test_wrappers.py relies on it.
run_or_print() {
  if [ -n "${AGENT_WRAPPER_DRY_RUN:-}" ]; then
    printf '%s\n' "$@"
    exit 0
  fi
  exec "$@"
}
