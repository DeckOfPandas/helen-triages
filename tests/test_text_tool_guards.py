"""guard-sed.py, guard-awk.py and guard-inline-script.py refuse inline programs.

The three are one rule: an inline program in a quoted argument is opaque to the
permission checker, whether it is spelled `sed 's/a/b/'`, `awk '{print}'` or
`python3 -c '...'`. Each hook is run here through the same JSON the harness
hands it (#1198).
"""
from __future__ import annotations

import json
import pathlib
import subprocess

import pytest

pytestmark = pytest.mark.shared

HOOKS = pathlib.Path(__file__).resolve().parents[1] / ".claude" / "hooks"


def _denied(hook: str, command: str) -> bool:
    result = subprocess.run(
        ["python3", str(HOOKS / hook)],
        input=json.dumps({"tool_input": {"command": command}}),
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    return '"deny"' in result.stdout


@pytest.mark.parametrize("command", [
    "awk '{print $1}' data.csv",
    "awk -F, -f tmp/prog.awk data.csv",
    "gawk -i inplace '{gsub(/a/,\"b\")}1' file.txt",
    "mawk 'BEGIN{system(\"id\")}'",
    "nawk 'END{print NR}' file",
    "/usr/bin/awk '{print}' file",
    "env awk '{print}' file",
    "busybox awk '{print}' file",
    "grep -rn x dir/ | awk '{print $2}'",
    "true && awk 'BEGIN{print > \"out\"}'",
    "(awk '{print}' file)",
])
def test_guard_awk_refuses_every_way_of_running_awk(command):
    assert _denied("guard-awk.py", command), f"allowed {command!r}"


@pytest.mark.parametrize("command", [
    "python3 .claude/hooks/guard-awk.py",
    "grep -rn 'awk' .claude/hooks/",
    "git commit -F tmp/msg-about-awk.txt",
    "cat hawkish.txt",
    "ls gawking/",
    'echo "no awk here, only prose"',
    "grep -c awkward notes.md",
])
def test_guard_awk_leaves_mentions_and_lookalikes_alone(command):
    assert not _denied("guard-awk.py", command), f"refused {command!r}"


@pytest.mark.parametrize("command", [
    "sed -n '1,5p' file",
    "sed -i 's/a/b/' file",
    "grep x file | sed 's/x/y/'",
    "/bin/sed 's/a/b/' file",
])
def test_guard_sed_refuses_sed(command):
    assert _denied("guard-sed.py", command), f"allowed {command!r}"


@pytest.mark.parametrize("command", [
    "python3 .claude/hooks/guard-sed.py",
    "grep -rn 'sed' model_instructions/",
    "cat processed.txt",
])
def test_guard_sed_leaves_mentions_and_lookalikes_alone(command):
    assert not _denied("guard-sed.py", command), f"refused {command!r}"


def test_guard_sed_no_longer_recommends_python_dash_c():
    """guard-sed.py's refusal must not suggest `python3 -c '...'`, which
    guard-inline-script.py refuses: advice that walks into the next guard."""
    text = (HOOKS / "guard-sed.py").read_text(encoding="utf-8")
    assert "single-quoted `python3 -c" not in text


def _denied_reason(hook: str, command: str) -> str | None:
    """The refusal text, or None if the hook allowed the call.

    The inline-script guard's refusal has to say what to do instead, so its
    content is asserted on, where `_denied` only answers yes or no.
    """
    result = subprocess.run(
        ["python3", str(HOOKS / hook)],
        input=json.dumps({"tool_input": {"command": command}}),
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    if not result.stdout.strip():
        return None
    output = json.loads(result.stdout)["hookSpecificOutput"]
    if output.get("permissionDecision") != "deny":
        return None
    return output["permissionDecisionReason"]


@pytest.mark.parametrize("command", [
    "python3 -c 'import yaml,sys; print(yaml.safe_load(open(sys.argv[1])))' _data/x.yml",
    'python3 -c "print(1)"',
    "python -c 'print(1)'",
    "python2 -c 'print 1'",
    "ruby -e 'puts 1'",
    "node -e 'console.log(1)'",
    "perl -e 'print 1'",
    # Path-qualified and env-invoked: the interpreter is still the word
    # governing the flag.
    "/usr/bin/python3 -c 'print(1)'",
    "env python3 -c 'print(1)'",
    # Options between the interpreter and its flag.
    "python3 -B -c 'print(1)'",
    "python3 -u -B -c 'print(1)'",
    # Multi-line, which is the form that actually gets reached for.
    "python3 -c '\nimport sys\nprint(sys.version)\n'",
])
def test_guard_inline_script_refuses_every_inline_program(command):
    assert _denied("guard-inline-script.py", command), f"allowed {command!r}"


@pytest.mark.parametrize("command", [
    "python3 -c 'x'",
    "python3 -c ''",
    "node -e '1'",
])
def test_guard_inline_script_has_no_length_or_quoting_carve_out(command):
    """No inline program is short enough or quoted well enough to be allowed.

    Pinned against reinstatement: there is no length at which an opaque
    command stops being opaque, and a carve-out for short single-quoted
    one-liners still prompts Helen on every one.
    """
    assert _denied("guard-inline-script.py", command), (
        f"allowed {command!r} -- a length or quoting carve-out is back"
    )


@pytest.mark.parametrize("command", [
    # What the hook pushes towards: one static path.
    "python3 tmp/fix_thing.py",
    "python3 scripts/verify.py",
    "python3 -m pytest -q",
    "node --test tests/js/*.test.js",
    "ruby -w scripts/parse_amounts.rb",
    # `sh -c` and `bash -c` are deliberately absent from INTERPRETERS: `sh -c`
    # is how a git credential helper is spelled.
    "sh -c 'git credential fill'",
    "bash -c 'echo hello'",
    "sh scripts/git-push-agent.sh branch:branch",
    # `-c` on something that is not an interpreter. The interpreter has to be
    # the word immediately governing the flag.
    "git -c credential.helper=scripts/git-credential-agent-token.sh push",
    "git -c user.name=x commit -F tmp/m.txt",
    "bundle exec jekyll build",
    # The flag with no program after it is not ours to judge.
    "python3 -c",
    # Writing ABOUT the forbidden shape.
    "grep -rn 'python3 -c' model_instructions/",
    "git commit -F tmp/msg-about-python3-dash-c.txt",
])
def test_guard_inline_script_leaves_files_and_lookalikes_alone(command):
    assert not _denied("guard-inline-script.py", command), f"refused {command!r}"


def test_guard_inline_script_allows_what_it_cannot_parse():
    """Unbalanced quotes make `shlex.split` raise, and the hook allows the call
    instead of guessing: another guard, or the permission checker, has it. A
    guard that blocks on parse failure blocks its own bug reports."""
    command = "python3 -c 'unterminated"
    assert not _denied("guard-inline-script.py", command), (
        f"refused {command!r}, which shlex cannot tokenise -- the hook is "
        "guessing rather than standing aside"
    )


def test_guard_inline_script_refusal_names_the_file_shape_to_use():
    """A refusal that does not say what to do instead gets routed around."""
    reason = _denied_reason("guard-inline-script.py", "python3 -c 'print(1)'")
    assert reason is not None
    assert "tmp/thing.py" in reason, reason
    assert "Write" in reason, reason
    assert "blockReadsOutsideWorkingDirectories" in reason, (
        "the refusal no longer gives the real reason, which is not style and "
        f"not length:\n{reason}"
    )


def test_all_three_guards_are_wired_into_settings():
    settings = json.loads((HOOKS.parent / "settings.json").read_text(encoding="utf-8"))
    entries = [
        hook
        for entry in settings["hooks"]["PreToolUse"]
        if entry.get("matcher") == "Bash"
        for hook in entry["hooks"]
    ]
    for name in ("guard-sed.py", "guard-awk.py", "guard-inline-script.py"):
        wired = [h for h in entries if h["command"].endswith(f'/.claude/hooks/{name}"')]
        assert wired, f"{name} exists but no PreToolUse hook runs it"
        # Ungated: an `if` is a prefix match, and an interpreter can appear
        # anywhere in a command line (`env python3 -c`), so an `if` here
        # would be a hole.
        assert "if" not in wired[0], (
            f"{name} has been gated on {wired[0].get('if')!r}. An `if` is a "
            "prefix match, and an inline program need not start the command."
        )
