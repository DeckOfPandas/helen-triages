#!/bin/sh
# Run part of the test suite: named test files or test ids under tests/.
#
# USAGE:
#   sh scripts/pytest.sh [-q] [-x] [-v] [-k <expression>] tests/<path>...
#
#   sh scripts/pytest.sh tests/kit/test_wrappers.py
#   sh scripts/pytest.sh -x tests/kit/test_hooks.py::test_guard_passes
#   sh scripts/pytest.sh -k "label and not create" tests/kit/test_wrappers.py
#
# A bare `python3 -m pytest` is its own allow rule. An allow rule for pytest
# with ANY arguments cannot be narrow: `--basetemp=<dir>` empties the folder it
# names, `-p <plugin>` imports code, and `--rootdir` or `-c` read another
# config. So this script takes only what it can check:
#   * one or more paths under tests/: letters, digits and `_ . / : -`, never
#     `..`, so a file, a folder or a `file.py::test_name` id;
#   * -q, -x and -v;
#   * -k with an expression of letters, digits, `_` and spaces (`and`, `or`,
#     `not` and names), which pytest matches against test names and never runs.
# Every argument is checked before any runs, and pytest gets them unchanged.
# pytest.ini still pins basetemp to tmp/pytest.
set -eu

WRAPPER=pytest.sh
here="$(cd "$(dirname "$0")" && pwd)"
. "$here/_github_conf.sh"

usage="usage: sh scripts/pytest.sh [-q] [-x] [-v] [-k <expression>] tests/<path>..."
[ "$#" -ge 1 ] || refuse "$usage"

paths=0
want_expr=""
for arg in "$@"; do
  if [ -n "$want_expr" ]; then
    case "$arg" in
      '' | *[!A-Za-z0-9_\ ]*) refuse "'$arg' is not a -k expression of names, and/or/not and spaces" ;;
    esac
    want_expr=""
    continue
  fi
  case "$arg" in
    -q | -x | -v) ;;
    -k) want_expr=1 ;;
    tests/*)
      case "$arg" in
        *..* | *[!A-Za-z0-9_./:-]*) refuse "'$arg' is not a plain path under tests/" ;;
      esac
      paths=$((paths + 1)) ;;
    *)
      refuse "'$arg' -- this wrapper takes -q, -x, -v, -k <expression> and paths under tests/. $usage" ;;
  esac
done
[ -z "$want_expr" ] || refuse "-k needs an expression"
[ "$paths" -ge 1 ] || refuse "name at least one path under tests/; the whole suite is python3 -m pytest"

run_or_print python3 -m pytest "$@"
