# Shared by the scripts/browser/ wrappers that measure one page. SOURCED,
# never run. Sets `base`, this worktree's served build, and `page`, the site
# path in $1 made relative to it, as tools/dev/ takes pages. Refuses a path
# that does not start with /, or holds `..` or a scheme.
case "$1" in
  /*) ;;
  *) echo "$WRAPPER: refused -- '$1' must start with /" >&2; exit 2 ;;
esac
case "$1" in
  *..* | *://*) echo "$WRAPPER: refused -- '$1' may not contain '..' or a scheme" >&2; exit 2 ;;
esac
page="${1#/}"
page="${page:-.}"
# The port is this worktree's serve.sh's (tmp/browser/port), so the page is
# this worktree's own build; 4010 only when no server runs here.
port=4010
if [ -f tmp/browser/port ]; then
  read -r port < tmp/browser/port
fi
base="http://127.0.0.1:$port/helen-triages"
. scripts/browser/env.sh
