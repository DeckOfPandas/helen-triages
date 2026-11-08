#!/bin/bash
# Build this project's Claude Code image when it is missing or stale, then start
# a shell in it with only the project mounted, at /workspace.
#
# USAGE:  .devcontainer/run.sh [--firewall] [--build-only] [--rebuild]
#
#   --firewall    default-deny egress except an allowlist (init-firewall.sh)
#   --build-only  build if needed and stop; devcontainer.json runs this
#   --rebuild     rebuild from scratch, pulling the base image again
#
# What goes in the image is the kit.env and Dockerfile beside this script: run
# a worktree's copy (.claude/worktrees/<name>/.devcontainer/run.sh) to build
# from that branch. Either way the primary clone is what gets mounted. See
# README.md.
set -euo pipefail

die() {
  echo "run.sh: $1" >&2
  exit 1
}

FIREWALL=0
BUILD_ONLY=0
REBUILD=0
SHOW_HELP=0
for arg in "$@"; do
  case "$arg" in
    --firewall) FIREWALL=1 ;;
    --build-only) BUILD_ONLY=1 ;;
    --rebuild) REBUILD=1 ;;
    -h | --help) SHOW_HELP=1 ;;
    *) die "unknown option '$arg' (try --help)" ;;
  esac
done
if [ "$SHOW_HELP" = 1 ]; then
  head -n 14 "${BASH_SOURCE[0]}" | tail -n +2
  exit 0
fi

# The primary clone, even when run from inside a worktree: every worktree of a
# repo shares one container, and the fixed --name below refuses a second. A
# worktree made inside the container records its git dir as /workspace/.git/...,
# which the host does not have, so git fails there and the path decides.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if GIT_COMMON_DIR="$(git -C "$HERE" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)"; then
  REPO_ROOT="$(dirname "$GIT_COMMON_DIR")"
else
  case "$HERE" in
    */.claude/worktrees/*/.devcontainer) REPO_ROOT="${HERE%/.claude/worktrees/*}" ;;
    *) REPO_ROOT="$(dirname "$HERE")" ;;
  esac
fi
cd "$REPO_ROOT"
if [ "$HERE" != "$REPO_ROOT/.devcontainer" ]; then
  echo "run.sh: building from $HERE, mounting $REPO_ROOT"
fi

[ "$(id -u)" -ne 0 ] || die "run this as your own user, not root: the container user copies your uid"
command -v docker >/dev/null || die "docker is not on PATH"
command -v python3 >/dev/null || die "python3 is needed on the host for the build stamp"

# --- kit.env: parsed, never sourced, and every key must be a known one, so a
# typo is an error rather than a toggle silently left at its default.
PROJECT_NAME=""
NODE_MAJOR=24
WITH_RUBY=0
RUBY_VERSION=3.3
WITH_PLAYWRIGHT=0
PLAYWRIGHT_VERSION=1.63.0
WITH_PY_REQS=0
PORTS=""
EXTRA_ALLOWED_DOMAINS=""
MOUNT_DOTFILES=1

# read_kit_file <file> <local>: with <local> = 1, only PROJECT_NAME is accepted.
read_kit_file() {
  local file="$1" only_name="$2" line key value
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%%#*}"
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [ -z "$line" ] && continue
    case "$line" in
      *=*) ;;
      *) die "$file: '$line' is not KEY=value" ;;
    esac
    key="${line%%=*}"
    value="${line#*=}"
    case "$value" in
      \"*\") value="${value#\"}"; value="${value%\"}" ;;
      \'*\') value="${value#\'}"; value="${value%\'}" ;;
    esac
    [ "$only_name" = 0 ] || [ "$key" = PROJECT_NAME ] \
      || die "$file: only PROJECT_NAME belongs here, not '$key'"
    case "$key" in
      PROJECT_NAME | NODE_MAJOR | WITH_RUBY | RUBY_VERSION | WITH_PLAYWRIGHT | \
      PLAYWRIGHT_VERSION | WITH_PY_REQS | PORTS | EXTRA_ALLOWED_DOMAINS | MOUNT_DOTFILES)
        printf -v "$key" '%s' "$value" ;;
      *) die "$file: unknown key '$key'" ;;
    esac
  done < "$file"
}

KIT_ENV="$HERE/kit.env"
[ -f "$KIT_ENV" ] || die "$KIT_ENV is missing"
read_kit_file "$KIT_ENV" 0
# Gitignored, so a template can commit PROJECT_NAME=changeme while its own
# checkout builds under a real name.
KIT_LOCAL_ENV=.devcontainer/kit.local.env
[ ! -f "$KIT_LOCAL_ENV" ] || read_kit_file "$KIT_LOCAL_ENV" 1

[[ "$PROJECT_NAME" =~ ^[a-z0-9][a-z0-9_.-]*$ ]] \
  || die "PROJECT_NAME '$PROJECT_NAME' must be lowercase letters, digits, . _ -"
[ "$PROJECT_NAME" != changeme ] \
  || die "set a PROJECT_NAME first: python3 .devcontainer/set-project-name.py <name>, or in $KIT_LOCAL_ENV"
for flag in WITH_RUBY WITH_PLAYWRIGHT WITH_PY_REQS MOUNT_DOTFILES; do
  [[ "${!flag}" =~ ^[01]$ ]] || die "$flag must be 0 or 1, not '${!flag}'"
done
[[ "$NODE_MAJOR" =~ ^[0-9]+$ ]] || die "NODE_MAJOR '$NODE_MAJOR' is not a number"
[[ "$RUBY_VERSION" =~ ^[0-9]+(\.[0-9]+)*$ ]] || die "RUBY_VERSION '$RUBY_VERSION' is not a version"
[[ "$PLAYWRIGHT_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "PLAYWRIGHT_VERSION '$PLAYWRIGHT_VERSION' is not N.N.N"
for domain in $EXTRA_ALLOWED_DOMAINS; do
  [[ "$domain" =~ ^[A-Za-z0-9.-]+$ ]] || die "EXTRA_ALLOWED_DOMAINS: '$domain' is not a hostname"
done
for pair in $PORTS; do
  [[ "$pair" =~ ^[0-9]+:[0-9]+$ ]] || die "PORTS: '$pair' is not host:container"
done

IMAGE="$PROJECT_NAME-devcontainer"
if [ "$WITH_RUBY" = 1 ]; then
  BASE_IMAGE="ruby:$RUBY_VERSION-slim-bookworm"
else
  BASE_IMAGE=debian:bookworm-slim
fi
USERNAME="$(id -un)"
[[ "$USERNAME" =~ ^[a-z_][a-z0-9_-]*$ ]] || USERNAME=dev

BUILD_ARGS=(
  "BASE_IMAGE=$BASE_IMAGE"
  "NODE_MAJOR=$NODE_MAJOR"
  "WITH_RUBY=$WITH_RUBY"
  "WITH_PLAYWRIGHT=$WITH_PLAYWRIGHT"
  "PLAYWRIGHT_VERSION=$PLAYWRIGHT_VERSION"
  "WITH_PY_REQS=$WITH_PY_REQS"
  "EXTRA_ALLOWED_DOMAINS=$EXTRA_ALLOWED_DOMAINS"
  "USERNAME=$USERNAME"
  "USER_UID=$(id -u)"
  "USER_GID=$(id -g)"
)

# --- Is the image built from what is on disk now, with these arguments? The
# stamp covers both; Claude Code's version is a second label so a new release
# rebuilds only the last layer and says so.
STAMP_LABEL=claude-kit.build-inputs
VERSION_LABEL=claude-kit.claude-code-version
label() {
  local value
  value="$(docker image inspect --format "{{ index .Config.Labels \"$1\" }}" "$IMAGE" 2>/dev/null || true)"
  [ "$value" = "<no value>" ] && value=""
  printf '%s' "$value"
}

BUILD_HASH="$(python3 "$HERE/build_inputs_hash.py" "${BUILD_ARGS[*]}" "$HERE")"
IMAGE_HASH="$(label "$STAMP_LABEL")"
IMAGE_VERSION="$(label "$VERSION_LABEL")"
# Not knowing the newest version is never a reason to rebuild or to stop.
CLAUDE_CODE_VERSION="${PIN_CLAUDE_CODE:-$(python3 "$HERE/claude_code_latest.py" || true)}"
[ -n "$CLAUDE_CODE_VERSION" ] || CLAUDE_CODE_VERSION="${IMAGE_VERSION:-latest}"

if [ "$REBUILD" = 1 ] || [ "$IMAGE_HASH" != "$BUILD_HASH" ] || [ "$IMAGE_VERSION" != "$CLAUDE_CODE_VERSION" ]; then
  EXTRA_FLAGS=()
  if [ "$REBUILD" = 1 ]; then
    echo "Rebuilding $IMAGE from scratch..."
    EXTRA_FLAGS=(--no-cache --pull)
  elif ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    echo "Building $IMAGE (first run)..."
  elif [ "$IMAGE_HASH" != "$BUILD_HASH" ]; then
    echo ".devcontainer/ or kit.env has changed since $IMAGE was built -- rebuilding..."
  else
    echo "Claude Code $CLAUDE_CODE_VERSION is out; $IMAGE has ${IMAGE_VERSION:-an unrecorded version} -- rebuilding..."
  fi
  ARG_FLAGS=()
  for build_arg in "${BUILD_ARGS[@]}"; do
    ARG_FLAGS+=(--build-arg "$build_arg")
  done
  docker build -t "$IMAGE" "${EXTRA_FLAGS[@]}" "${ARG_FLAGS[@]}" \
    --build-arg "CLAUDE_CODE_VERSION=$CLAUDE_CODE_VERSION" \
    --label "$STAMP_LABEL=$BUILD_HASH" \
    --label "$VERSION_LABEL=$CLAUDE_CODE_VERSION" \
    -f "$HERE/Dockerfile" "$HERE"
fi

[ "$BUILD_ONLY" = 1 ] && exit 0

# --- Run.
RUN_ARGS=(
  --name "$PROJECT_NAME-primary"
  -v "$REPO_ROOT:/workspace"
  -v "$PROJECT_NAME-claude-config:/state/claude-config"
  -w /workspace
)
docker volume create "$PROJECT_NAME-claude-config" >/dev/null
if [ "$WITH_RUBY" = 1 ]; then
  docker volume create "$PROJECT_NAME-bundle-cache" >/dev/null
  RUN_ARGS+=(-v "$PROJECT_NAME-bundle-cache:/state/bundle")
fi

if [ "$MOUNT_DOTFILES" = 1 ]; then
  for dotfile in .bashrc .bash_aliases .bash_profile; do
    [ -f "$HOME/$dotfile" ] && RUN_ARGS+=(-v "$HOME/$dotfile:/home/$USERNAME/.host-${dotfile#.}:ro")
  done
  [ -f "$HOME/.gitconfig" ] && RUN_ARGS+=(-v "$HOME/.gitconfig:/home/$USERNAME/.gitconfig:ro")
fi

for pair in $PORTS; do
  RUN_ARGS+=(-p "$pair")
done

# The token is read for this one `docker run` and never printed: from
# .claude/settings.local.json if it holds one, else from this shell's own
# environment. Neither present, the container simply has none.
FILE_TOKEN="$(python3 .devcontainer/read_local_token.py)"
if [ -n "$FILE_TOKEN" ]; then
  export AGENT_GH_TOKEN="$FILE_TOKEN"
fi
unset FILE_TOKEN
if [ -n "${AGENT_GH_TOKEN+x}" ]; then
  RUN_ARGS+=(-e AGENT_GH_TOKEN)
fi

COMMAND=(bash)
if [ "$FIREWALL" = 1 ]; then
  RUN_ARGS+=(--cap-add=NET_ADMIN --cap-add=NET_RAW)
  COMMAND=(bash -c 'sudo /usr/local/bin/init-firewall.sh && exec bash')
fi

docker run -it --rm "${RUN_ARGS[@]}" "$IMAGE" "${COMMAND[@]}"
