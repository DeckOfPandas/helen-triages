#!/usr/bin/env python3
"""Block the destructive git commands, but only when there is something to lose.

WHY THIS EXISTS, AND WHY IT IS CODE RATHER THAN A SENTENCE IN CLAUDE.md.
CLAUDE.md has said "NEVER run `git reset --hard` (or `git checkout --` /
`git restore` over a dirty tree, or `git clean -fd`) without asking me first,
every single time" since 2026-08-18, when one of those commands destroyed a
half-finished handover edit. On 2026-08-19 an agent that had read that rule ran
`git checkout -- <two files> 2>/dev/null || true` anyway, to undo an edit it had
just made itself, and discarded work in the process.

So the rule is not the problem. A rule an agent reads and then breaks needs
enforcement, not rewording -- which is the same conclusion this repository
already reached about `meta.awaiting_fix` and `meta.proofread`, both of which
were documented long before anything checked them.

WHAT IT DOES NOT DO, deliberately:

  - It does not block on a CLEAN tree. `git checkout -- x` with nothing
    uncommitted is a no-op, and a guard that fires on harmless invocations
    teaches whoever meets it to route around the guard rather than to think.
    The dangerous thing is the combination, so the combination is what is
    checked.
  - It does not block `git stash`, which is the reversible answer, or
    `git restore --staged` on its own, which only unstages and leaves the
    working tree untouched.
  - It cannot see a `cd` earlier in the command line: it asks git about the
    directory the hook itself runs in. A command that changes directory first
    may be judged against the wrong repository. Accepted -- the common case is
    the one that bit, and a wrong-but-loud block is recoverable in a way that a
    silent discard is not.

The reason to prefer this over a `deny` entry in permissions is that a deny
pattern is a prefix match on the command string, and the command that got past
the written rule was `git checkout -- a b 2>/dev/null || true`: a compound line
with redirection and a fallback. This reads the whole command, and asks git
whether anything would actually be lost.

Invoked as `python3 .claude/hooks/guard-destructive-git.py` so it needs no
execute bit -- CLAUDE.md forbids changing file permissions without asking, and a
hook that requires a chmod to install would be self-defeating.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

# Each entry: (compiled pattern, how to name the command in the refusal).
#
# `[^|;&]*?` keeps a match inside ONE command of a compound line, so
# `git log && git checkout -- x` is caught on its second clause and
# `echo "git reset --hard"` is not caught at all.
#
# THE FLAG-WITH-A-VALUE CASE, FIXED 2026-09-10 AND IT WAS A REAL HOLE. This read
# `(?:-\S+\s+)*`, which allows a flag but NOT the value after it -- so in
# `git -C _food_drafts reset --hard` the `-C ` matched, `_food_drafts` did not,
# and the pattern failed. **Every destructive command aimed at a nested repo by
# `git -C` walked straight past this hook**, unrecognised: not judged and
# allowed, but never looked at.
#
# It went unnoticed because CLAUDE.md documents `cd _food_drafts && git ...` as
# the way those repos are edited, and that form matched fine. It became urgent
# the same day, when guard-unanalyzable-bash.py started refusing a leading `cd`
# and left `git -C` as the only way in.
#
# Spelled out rather than loosened to `\S+\s*\S*\s*`: `-C <path>` and
# `-c <key=value>` take a value, `--flag` and `-flag` do not, and a pattern that
# lets any token follow any flag can swallow the subcommand it is looking for.
_GIT = r"\bgit\s+(?:-[cC]\s+\S+\s+|--\S+\s+|-\S+\s+)*"

PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # git checkout -- <paths>   and   git checkout <ref> -- <paths>
    (re.compile(_GIT + r"checkout\b[^|;&]*?\s--\s"), "git checkout -- <paths>"),
    # git checkout .   (same discard, no separator)
    (re.compile(_GIT + r"checkout\s+\.(?:\s|$|[|;&])"), "git checkout ."),
    # git reset --hard
    (re.compile(_GIT + r"reset\b[^|;&]*?\s--hard\b"), "git reset --hard"),
    # git clean -f / -fd / -xfd / --force
    (re.compile(_GIT + r"clean\b[^|;&]*?\s-(?:-force\b|[a-eg-zA-Z]*f)"), "git clean -f"),
]

# git restore is handled separately: `--staged` WITHOUT `--worktree` only
# unstages, which leaves the working tree alone and is recoverable.
RESTORE = re.compile(_GIT + r"restore\b([^|;&]*)")

# `git checkout <path>` WITH NO `--`, which discards exactly as thoroughly as the
# separator form and reads far more innocently. Added 2026-08-19 after the hook
# failed to stop its own author doing precisely this: `git checkout
# tests/test_style.py`, run reflexively to undo a deliberate test-break, took a
# file's uncommitted work with it. The first version only patterned the ` -- `
# form, so this walked straight past.
#
# TELLING A PATH FROM A BRANCH IS THE WHOLE DIFFICULTY, and it cannot be done by
# regex: `git checkout main` switches branch and is harmless, `git checkout
# tests/foo.py` destroys work, and `git checkout feat/some-branch` is harmless
# despite looking exactly like a path. So this asks the filesystem -- an argument
# naming a file that EXISTS is a path, and nothing else is. Branch names do not
# usually name real files, and on the rare occasion one does, git itself calls it
# ambiguous and blocking is the right answer anyway.
CHECKOUT_ARGS = re.compile(_GIT + r"checkout\b([^|;&]*)")


def _checkout_targets_a_real_file(command: str) -> bool:
    match = CHECKOUT_ARGS.search(command)
    if not match:
        return False
    for arg in match.group(1).split():
        if arg.startswith("-"):
            continue                     # a flag, not a path
        if arg in ("--",):
            continue
        try:
            if pathlib.Path(arg.strip("\"'")).exists():
                return True
        except OSError:
            continue
    return False

# Quoted spans are stripped before matching, and this is not a nicety. Commit
# messages and handover notes in this repository quote these commands by name
# constantly -- the entry in CLAUDE.md that this hook enforces contains three of
# them -- so without this, `git commit -m "...git checkout -- ..."` is refused.
# A guard that fires on writing ABOUT a command, rather than running one, is a
# guard people learn to work around, which is worse than no guard.
#
# The cost is that `bash -c "git reset --hard"` slips through. That is deliberate
# evasion rather than the accident this exists to catch, and no amount of regex
# fixes it -- the answer to an agent determined to route around a safety rail is
# not a better rail.
QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")

# Heredoc BODIES are stripped too, for the same reason and then some. Found the
# hard way: this hook blocked the very commit that introduced it, because the
# commit message -- written as `git commit -F` from a heredoc, which is the
# house style here for anything longer than a line -- described the commands it
# refuses. Quoted-span stripping does not help, since a heredoc body is not
# quoted; it is data on stdin that merely looks like shell text.
#
# Matches `<<EOF`, `<<'EOF'`, `<<"EOF"` and the `<<-` indented form, and drops
# everything up to a line holding just the delimiter.
HEREDOC = re.compile(
    r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1.*?^\2$",
    re.DOTALL | re.MULTILINE,
)


# DESTROYING A STASH IS A SECOND KIND OF LOSS, and it needs its own gate.
#
# Everything above is about the WORKING TREE, so it is correctly allowed when
# the tree is clean -- there is nothing to lose. `git stash drop` and
# `git stash clear` are not like that: what they destroy is the stash list, and
# that is just as gone whether or not the tree happens to be dirty. Running the
# clean-tree check against them would have waved them straight through.
#
# The irony is on the record: this hook's own refusal message recommends
# `git stash -u` as the safe alternative, and until 2026-08-20 it would then
# have permitted `git stash clear` without a murmur. Helen spotted the gap when
# it was described to her. The lesson is the same one the bare-path `checkout`
# hole taught -- enumerate what the dangerous ACT is, not the commands you
# happen to picture.
#
# `git stash pop` is deliberately NOT here. It applies and then drops, so the
# content lands in the working tree rather than vanishing, and on a conflict git
# keeps the stash. Blocking it would be over-blocking a normal workflow, which
# is how a guard teaches people to route around it.
STASH_DESTRUCTIVE = re.compile(_GIT + r"stash\s+(drop|clear)\b")


def _stash_entries() -> list[str]:
    """`git stash list` lines, or [] if there are none or this is not a repo."""
    try:
        result = subprocess.run(
            ["git", "stash", "list"],
            capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _matched_stash(command: str) -> str | None:
    command = HEREDOC.sub(" ", command)
    command = QUOTED.sub(" ", command)
    m = STASH_DESTRUCTIVE.search(command)
    return f"git stash {m.group(1)}" if m else None


def _matched(command: str) -> str | None:
    command = HEREDOC.sub(" ", command)
    command = QUOTED.sub(" ", command)
    for pattern, label in PATTERNS:
        if pattern.search(command):
            return label
    if _checkout_targets_a_real_file(command):
        return "git checkout <path>"
    m = RESTORE.search(command)
    if m:
        args = m.group(1)
        staged = "--staged" in args or re.search(r"\s-S\b", args)
        worktree = "--worktree" in args or re.search(r"\s-W\b", args)
        if staged and not worktree:
            return None    # unstages only; the working tree is untouched
        return "git restore"
    return None


# WHICH REPOSITORY THE COMMAND IS AIMED AT, added 2026-09-10 -- until then this
# hook always asked the process's own working directory, whatever the command
# said. `git -C _food_drafts reset --hard` was therefore judged by whether the
# OUTER worktree was dirty: outer tree clean, so allowed, and uncommitted work in
# the nested drafts repo destroyed. That is the exact loss this hook exists to
# prevent, arriving through the door it was not watching.
#
# DUPLICATED FROM guard-main-branch.py RATHER THAN SHARED, deliberately and in
# keeping with this file's existing QUOTED/HEREDOC duplication: each hook is a
# single file with no import path of its own, and a shared module would make both
# depend on how they happen to be invoked. If one of these is ever fixed, fix the
# other -- they are the same twenty lines and they have now been wrong together
# once.
CD_TARGET = re.compile(r"\bcd\s+([^\s;&|]+)")
GIT_C_TARGET = re.compile(r"\bgit\s+(?:-\S+\s+\S+\s+)*?-C\s+([^\s;&|]+)")


def _resolve(raw: str, base: pathlib.Path) -> pathlib.Path | None:
    """A path argument as a real directory, resolved against `base`, or None."""
    try:
        target = pathlib.Path(raw.strip("\"'")).expanduser()
        if not target.is_absolute():
            target = base / target
        target = target.resolve()
        return target if target.is_dir() else None
    except (OSError, ValueError):
        return None


def _repo_dir(command: str) -> pathlib.Path:
    """The directory git will actually run in, modelling the shell in order.

    A `cd` moves the shell; a later `-C` moves git again, RELATIVE TO WHERE THE
    `cd` LEFT IT, so the two compose rather than compete: `cd a && git -C b`
    runs in `a/b`.
    """
    base = pathlib.Path.cwd()

    cd_match = CD_TARGET.search(command)
    if cd_match:
        moved = _resolve(cd_match.group(1), base)
        if moved is not None:
            base = moved

    c_match = GIT_C_TARGET.search(command)
    if c_match:
        moved = _resolve(c_match.group(1), base)
        if moved is not None:
            return moved

    return base


def _dirty(directory: pathlib.Path) -> list[str]:
    """Lines of `git status --porcelain` in `directory`, or [] if not a repo."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=directory, capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0            # nothing to judge; never break the tool call

    command = (payload.get("tool_input") or {}).get("command") or ""

    # The stash family first, because its gate is different: what is at risk is
    # the stash list, not the working tree, so tree cleanliness says nothing.
    stash_label = _matched_stash(command)
    if stash_label:
        entries = _stash_entries()
        if not entries:
            return 0        # nothing stashed, so nothing to lose
        shown = "\n  ".join(entries[:10])
        if len(entries) > 10:
            shown += f"\n  ... and {len(entries) - 10} more"
        return _deny(
            f"BLOCKED: {stash_label} with {len(entries)} stash(es) that would go.\n\n"
            f"  {shown}\n\n"
            "A stash is where work goes to be SAFE -- this hook's own refusal "
            "message recommends `git stash -u` for exactly that -- so destroying "
            "one is the same loss as destroying the tree, and it does not matter "
            "whether the tree is clean.\n\n"
            "A dropped stash is not in `git stash list`, not in the tree, and not "
            "anywhere obvious. It survives briefly as an unreachable commit and "
            "can sometimes be found with `git fsck --unreachable`, which is a "
            "rescue operation rather than a plan.\n\n"
            "BEFORE DROPPING ANYTHING: record the SHAs (`git rev-parse "
            "'stash@{N}'` for each), and check each stash against what is already "
            "committed -- an old stash is usually redundant, and occasionally it "
            "is the only copy of something. On 2026-08-20 nine stashes were "
            "reviewed this way: seven were redundant, and two held work that had "
            "never been applied, including a live config fix.\n\n"
            "Ask Helen, name what would be lost, and wait."
        )

    label = _matched(command)
    if not label:
        return 0

    target = _repo_dir(command)
    dirty = _dirty(target)
    if not dirty:
        return 0            # nothing to lose, so nothing to stop

    shown = "\n  ".join(dirty[:20])
    if len(dirty) > 20:
        shown += f"\n  ... and {len(dirty) - 20} more"

    reason = (
        f"BLOCKED: {label} with {len(dirty)} uncommitted change(s) in "
        f"{target}.\n\n"
        f"  {shown}\n\n"
        "This discards uncommitted work with no undo and no reflog entry to "
        "recover it from, and it does not distinguish your edits from Helen's -- "
        "she edits this tree while you work. CLAUDE.md: ask first, every single "
        "time, and name what would be lost.\n\n"
        "If you are undoing an edit YOU just made, re-edit the file instead; "
        "reaching for git to revert your own change is what caused this rule to "
        "be written. If something genuinely has to be put aside, `git stash -u` "
        "does it reversibly. If it genuinely has to be destroyed, ask Helen and "
        "let her run it.\n\n"
        "(This hook allows the same command on a clean tree -- it is the "
        "combination that is dangerous, not the command.)"
    )

    return _deny(reason)


def _deny(reason: str) -> int:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
