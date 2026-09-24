"""The agent wrappers in scripts/ refuse what their allow rules must not allow.

WHY THIS FILE EXISTS (2026-09-11). Helen: "Please work out how to run sh
commands in a way that can be statically analysed, so things remain safe
without harrassing me for permissions all the time." The answer was allow rules
in `.claude/settings.json` for a handful of committed wrappers -- and an allow
rule ending in ` *` is only as narrow as the wrapper's own argument checks.

Before that day every wrapper call prompted, so the prompt WAS the guard, and
two of them needed it: `git-push-agent.sh feature:main` would have moved the
public `main` without a PR, and `git-clone-agent.sh <repo> --template=<dir>`
would have run whatever hooks that directory held. The question DECISIONS §11
asks of any widening -- "what was that prompt the last guard of" -- is answered
here, in tests, so a later edit to a wrapper cannot quietly re-open it.

Every wrapper case runs under AGENT_WRAPPER_DRY_RUN=1, which makes the wrapper
print the command it would run and exit, and with both token variables removed
from the environment. Nothing here touches the network or a credential.

The settings tests below pin the other half: which rules may be open-ended at
all, that merging stays denied, and Helen's ruling that tmp/ scripts keep
asking.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess

import pytest

# Suite marker, so `pytest -m shared` can run this half alone.
# tests/test_suite_hygiene.py asserts every module declares one --
# an unmarked file is silently missed by every filtered run.
pytestmark = pytest.mark.shared

ROOT = pathlib.Path(__file__).resolve().parents[1]
SETTINGS = ROOT / ".claude" / "settings.json"
TOKEN_HOOK = ROOT / ".claude" / "hooks" / "guard-token-expansion.py"


def _run(script: str, *args: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items()
           if k not in ("AGENT_GH_TOKEN", "GH_TOKEN")}
    env["AGENT_WRAPPER_DRY_RUN"] = "1"
    return subprocess.run(
        ["sh", f"scripts/{script}", *args],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=30,
    )


def _assert_refused(script: str, args: list[str]) -> None:
    result = _run(script, *args)
    assert result.returncode == 2 and "refused" in result.stderr, (
        f"{script} ACCEPTED {args!r} -- an allow rule covers this wrapper, so "
        f"whatever it accepts runs without asking Helen.\n"
        f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
    )


def _accepted_lines(script: str, args: list[str]) -> list[str]:
    result = _run(script, *args)
    assert result.returncode == 0, (
        f"{script} refused {args!r}, a call it exists to make:\n{result.stderr}"
    )
    lines = result.stdout.splitlines()
    assert lines, f"{script} printed nothing under AGENT_WRAPPER_DRY_RUN"
    return lines


# --- gh-read.sh: GET only, the three repos only ------------------------------

COMMENTS = "repos/DeckOfPandas/helen-triages/issues/944/comments"


@pytest.mark.parametrize("args", [
    [COMMENTS, "-X", "PATCH"],
    [COMMENTS, "--method", "PUT"],
    [COMMENTS, "-f", "title=x"],
    [COMMENTS, "-F", "body=@tmp/x.md"],
    [COMMENTS, "--input", "tmp/x.json"],
    [COMMENTS, "-H", "Accept: application/json"],
    [COMMENTS, "--hostname", "example.com"],
    [COMMENTS, "--jq"],
    [COMMENTS, "--jq", "env"],
    [COMMENTS, "--jq", "$ENV.HOME"],
    ["repos/DeckOfPandas/helen-triages/pulls/1/merge", "-X", "PUT"],
    ["repos/DeckOfPandas/some-other-repo/issues"],
    ["repos/someone-else/helen-triages/issues"],
    ["repos/DeckOfPandas/helen-triages-lookalike/issues"],
    ["repos/DeckOfPandas/helen-triages/../some-other-repo/issues"],
    ["/repos/DeckOfPandas/helen-triages/issues"],
    ["-X"],
    [],
])
def test_gh_read_refuses_anything_but_a_read_of_the_three_repos(args):
    _assert_refused("gh-read.sh", args)


@pytest.mark.parametrize("args, tail", [
    ([COMMENTS], [COMMENTS]),
    ([COMMENTS, "--jq", ".[].body"], [COMMENTS, "--jq", ".[].body"]),
    (["repos/DeckOfPandas/helen-triages/pulls?state=all&per_page=40",
      "--jq", ".[] | [.number, .title] | @tsv", "--paginate"],
     ["repos/DeckOfPandas/helen-triages/pulls?state=all&per_page=40",
      "--paginate", "--jq", ".[] | [.number, .title] | @tsv"]),
    (["repos/DeckOfPandas/helen-triages"], ["repos/DeckOfPandas/helen-triages"]),
    (["repos/DeckOfPandas/helen-triages-food-private/contents/README.md"],
     ["repos/DeckOfPandas/helen-triages-food-private/contents/README.md"]),
    (["repos/DeckOfPandas/helen-triages-cocktails-private/pulls"],
     ["repos/DeckOfPandas/helen-triages-cocktails-private/pulls"]),
    (["repos/DeckOfPandas/helen-triages/environments"],
     ["repos/DeckOfPandas/helen-triages/environments"]),
])
def test_gh_read_passes_a_read_through_as_an_explicit_get(args, tail):
    lines = _accepted_lines("gh-read.sh", args)
    assert lines[0] == "sh" and lines[1].endswith("/scripts/gh-agent.sh"), (
        "gh-read.sh must go through gh-agent.sh, so the token's name stays in "
        f"one file; it ran {lines[:2]!r}"
    )
    assert lines[2:5] == ["api", "--method", "GET"]
    assert lines[5:] == tail


# --fields and --each, 2026-09-15: a bracketed --jq made Claude Code ask Helen
# even though gh-read.sh is allow-listed, so the script builds that expression.

PR = "repos/DeckOfPandas/helen-triages/pulls/1091"


@pytest.mark.parametrize("args, jq", [
    ([PR, "--fields", "state"], "[.state] | @tsv"),
    ([PR, "--fields", "state,merged_at,user.login"],
     "[.state, .merged_at, .user.login] | @tsv"),
    (["repos/DeckOfPandas/helen-triages/pulls?state=all&per_page=40",
      "--each", "number,title"],
     ".[] | [.number, .title] | @tsv"),
])
def test_gh_read_builds_the_jq_from_plain_field_names(args, jq):
    lines = _accepted_lines("gh-read.sh", args)
    assert lines[-2:] == ["--jq", jq]


@pytest.mark.parametrize("args", [
    [PR, "--fields"],
    [PR, "--fields", ""],
    [PR, "--fields", "state]"],
    [PR, "--fields", "state|env"],
    [PR, "--fields", "state,"],
    [PR, "--fields", ",state"],
    [PR, "--fields", "state,,title"],
    [PR, "--fields", ".state"],
    [PR, "--fields", "user..login"],
    [PR, "--fields", "state name"],
    [PR, "--fields", "$ENV"],
    [PR, "--fields", "environment"],
    [PR, "--each", "number;id"],
    [PR, "--fields", "state", "--jq", ".title"],
    [PR, "--fields", "state", "--each", "title"],
])
def test_gh_read_refuses_field_lists_that_are_not_plain_names(args):
    _assert_refused("gh-read.sh", args)


# --- guard-unanalyzable-bash.py shape 7: quoted brackets to a wrapper ---------

UNANALYZABLE_HOOK = ROOT / ".claude" / "hooks" / "guard-unanalyzable-bash.py"


def _unanalyzable_denies(command: str) -> bool:
    result = subprocess.run(
        ["python3", str(UNANALYZABLE_HOOK)],
        input=json.dumps({"tool_input": {"command": command}}),
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    return '"deny"' in result.stdout


@pytest.mark.parametrize("command", [
    # the exact call Helen was asked about, 2026-09-15
    "sh scripts/gh-read.sh repos/DeckOfPandas/helen-triages/pulls/1091 "
    "--jq '[.state, .merged_at] | @tsv'",
    "sh scripts/gh-read.sh repos/DeckOfPandas/helen-triages/issues --jq '.[].title'",
    'sh scripts/gh-read.sh repos/DeckOfPandas/helen-triages/issues --jq ".number | tostring"',
    'sh scripts/gh-write.sh pr-create helen-triages feat/x "[wip] a title" tmp/b.md',
])
def test_the_hook_refuses_quoted_brackets_and_pipes_given_to_a_wrapper(command):
    assert _unanalyzable_denies(command), f"allowed {command!r}"


@pytest.mark.parametrize("command", [
    # the two measured calls that did NOT ask
    "sh scripts/gh-read.sh repos/DeckOfPandas/helen-triages/pulls/1091",
    "sh scripts/gh-read.sh repos/DeckOfPandas/helen-triages/pulls/1091 --jq .state",
    "sh scripts/gh-read.sh repos/DeckOfPandas/helen-triages/pulls/1091 --fields state,merged_at",
    'sh scripts/gh-write.sh pr-create helen-triages feat/x "(chore) a title" tmp/b.md',
    # shape 7 is measured on wrappers only; elsewhere quoted text stays inert
    "grep -rn 'a|b' model_instructions/",
    "grep -n '[0-9]' tests/test_agent_wrappers.py",
])
def test_the_hook_leaves_plain_wrapper_calls_and_other_quoted_text_alone(command):
    assert not _unanalyzable_denies(command), f"refused {command!r}"


# --- guard-unanalyzable-bash.py shape 8: a leading env assignment -----------

@pytest.mark.parametrize("command", [
    # the exact call Helen was asked about, 2026-09-15
    "PLAYWRIGHT_BROWSERS_PATH=/opt/playwright/ms-playwright "
    "NODE_PATH=/opt/playwright/node_modules node tmp/repro.js",
    "FOO=bar node tmp/x.js",
    "FOO=bar BAZ=qux python3 tmp/x.py",
    "FOO='a b' node tmp/x.js",
    'FOO="a b" node tmp/x.js',
])
def test_the_hook_refuses_a_leading_env_assignment(command):
    assert _unanalyzable_denies(command), f"allowed {command!r}"


@pytest.mark.parametrize("command", [
    # nothing to run after the assignment -- sets a variable, executes nothing
    "FOO=bar",
    # an `=` that is not a LEADING assignment
    "git -c credential.helper=value push origin main",
    "node --flag=value tmp/x.js",
    'git commit -m "PLAYWRIGHT_BROWSERS_PATH=foo bar"',
    "grep -rn 'FOO=bar' dir/",
    "sh scripts/browser/styles.sh /food/ .btn-shortlist-only 390",
])
def test_the_hook_leaves_non_leading_or_empty_assignments_alone(command):
    assert not _unanalyzable_denies(command), f"refused {command!r}"


# --- guard-unanalyzable-bash.py shape 9: an unquoted parenthesis -------------

@pytest.mark.parametrize("command", [
    # the exact call Helen was asked about and declined, 2026-09-15
    "git log origin/main -25 --format=%h%x09%s%x09%(trailers:key=Fixes,valueonly,separator=%x2C)",
    "(git status)",
    "echo (x)",
    "ls tmp)",
])
def test_the_hook_refuses_an_unquoted_parenthesis(command):
    assert _unanalyzable_denies(command), f"allowed {command!r}"


@pytest.mark.parametrize("command", [
    "git log origin/main -25 --format='%h %s %(trailers:key=Fixes,valueonly)'",
    'sh scripts/gh-write.sh pr-create helen-triages feat/x "(chore) a title" tmp/b.md',
    "grep -n 'foo(bar)' assets/js/filters.js",
    'grep -n "re.compile(r" .claude/hooks/guard-sed.py',
    "find tmp -name x",
    "grep -n foo\\(bar\\) assets/js/filters.js",
])
def test_the_hook_leaves_quoted_or_escaped_parentheses_alone(command):
    assert not _unanalyzable_denies(command), f"refused {command!r}"


# --- guard-unanalyzable-bash.py shape 10: `git -C` ---------------------------
#
# Helen, 2026-09-21: "please refuse git -C across the board". Every one of the
# refused commands below was actually run in the session that prompted the
# rule, and every one of them interrupted her: an allow rule is a PREFIX match,
# so a `-C` between `git` and its subcommand makes `Bash(git status *)`,
# `Bash(git add -- *)`, `Bash(git commit -F *)` and the exact
# `Bash(git branch --show-current)` all fail to match.

@pytest.mark.parametrize("command", [
    # the four real calls from 2026-09-21, one per allow rule they missed
    "git -C /workspace/.claude/worktrees/opus-improve-devops status --short",
    "git -C /workspace/.claude/worktrees/opus-improve-devops branch --show-current",
    "git -C /workspace/.claude/worktrees/opus-improve-devops add -- .claude/settings.json",
    "git -C /workspace/.claude/worktrees/opus-improve-devops commit -F tmp/msg.txt",
    # relative paths and `.` are the same shape
    "git -C . status",
    "git -C ../other log --oneline",
])
def test_the_hook_refuses_git_dash_capital_c(command):
    assert _unanalyzable_denies(command), f"allowed {command!r}"


@pytest.mark.parametrize("command", [
    # LOWERCASE -c is a different flag: config, not chdir. Every
    # scripts/git-*-agent.sh passes the credential helper this way, so refusing
    # it would break pushing outright.
    "git -c credential.helper=value push origin main",
    "git -c credential.helper=sh\\ scripts/git-credential-agent-token.sh push origin x",
    # the bare commands that should be written instead
    "git status --short",
    "git branch --show-current",
    "git add -- .claude/settings.json",
    # prose about it is inert inside quotes, like every other shape here
    'git commit -m "stop using git -C, it breaks the allow rules"',
    "grep -rn 'git -C' model_instructions/",
    # a -C belonging to some other command is not this shape
    "make -C subdir all",
])
def test_the_hook_leaves_lowercase_dash_c_and_bare_git_alone(command):
    assert not _unanalyzable_denies(command), f"refused {command!r}"


# --- session-ground-truth.py: the one hook that TELLS rather than refuses ----
#
# Added 2026-09-21. Every other hook here refuses something; this one reports
# where the session is, because CLAUDE.md had been asking sessions to remember
# to look ("am I still where I left off" -- the branch can move under a running
# session, /workspace being a bind mount). A report that fails is worse than no
# report, so what is pinned is that it always emits usable JSON and never
# blocks.

GROUND_TRUTH_HOOK = ROOT / ".claude" / "hooks" / "session-ground-truth.py"


def _ground_truth_payload() -> dict:
    result = subprocess.run(
        ["python3", str(GROUND_TRUTH_HOOK)],
        input="{}", cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_the_ground_truth_hook_is_wired_as_a_session_start_hook():
    hooks = json.loads(SETTINGS.read_text(encoding="utf-8"))["hooks"]
    commands = [
        entry["command"]
        for group in hooks["SessionStart"] for entry in group["hooks"]
        if entry.get("type") == "command"
    ]
    assert any("session-ground-truth.py" in c for c in commands), commands


def test_the_ground_truth_hook_reports_branch_tree_and_drafts():
    payload = _ground_truth_payload()
    context = payload["hookSpecificOutput"]["additionalContext"]
    # Both audiences get the same text: Helen reads systemMessage, the session
    # reads additionalContext. They must not drift apart.
    assert payload["systemMessage"] == context
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    for expected in ("branch:", "tree:", "vs origin/main:", "drafts:"):
        assert expected in context, f"{expected!r} missing from {context!r}"


def test_the_ground_truth_hook_never_blocks_a_session():
    """It has nothing to refuse, and a status report that could stop a session
    starting would be a worse trade than no report at all."""
    payload = _ground_truth_payload()
    assert "permissionDecision" not in payload.get("hookSpecificOutput", {})
    assert payload.get("continue") is not False
    assert payload.get("decision") != "block"


# --- git-push-agent.sh: never the public main --------------------------------

@pytest.mark.parametrize("args", [
    ["feature:main"],
    ["+feature:main"],
    ["feature:refs/heads/main"],
    [":main"],
    ["HEAD"],
    ["feature"],
    ["--force"],
    ["-f:x"],
    ["feature:feature", "some-other-repo"],
    ["feature:feature", "helen-triages", "/etc"],
    ["feature:feature", "helen-triages", "../elsewhere"],
    [],
])
def test_git_push_agent_refuses_the_public_main_and_anything_ambiguous(args):
    _assert_refused("git-push-agent.sh", args)


@pytest.mark.parametrize("args, repo, directory, refspec", [
    (["feature:feature"], "helen-triages", ".", "feature:feature"),
    ([":merged-branch"], "helen-triages", ".", ":merged-branch"),
    (["feature:feature", "helen-triages-food-private", "_food_drafts"],
     "helen-triages-food-private", "_food_drafts", "feature:feature"),
    # Helen, 2026-08-29: "Pushing to main in the private repos is fine."
    (["content/x:main", "helen-triages-cocktails-private", "_cocktail_drafts"],
     "helen-triages-cocktails-private", "_cocktail_drafts", "content/x:main"),
])
def test_git_push_agent_pushes_a_branch_over_a_plain_url(args, repo, directory, refspec):
    lines = _accepted_lines("git-push-agent.sh", args)
    assert lines[:3] == ["git", "-C", directory]
    assert lines[-3:] == [
        "push", f"https://github.com/DeckOfPandas/{repo}.git", refspec,
    ]
    assert any(line.startswith("credential.helper=") for line in lines)
    assert not any("@github.com" in line for line in lines), (
        "a credential in a URL is the shape that leaked on 2026-09-10"
    )


# --- git-fetch-agent.sh ------------------------------------------------------

@pytest.mark.parametrize("args", [
    [],
    ["_cocktail_drafts"],
    ["/etc", "helen-triages-cocktails-private"],
    ["../elsewhere", "helen-triages-cocktails-private"],
    ["_cocktail_drafts", "some-other-repo"],
    ["_cocktail_drafts", "helen-triages-cocktails-private", "--upload-pack=x"],
    ["_cocktail_drafts", "helen-triages-cocktails-private", "main:main"],
])
def test_git_fetch_agent_refuses_outside_the_checkout_and_the_three_repos(args):
    _assert_refused("git-fetch-agent.sh", args)


@pytest.mark.parametrize("args, ref", [
    (["_cocktail_drafts", "helen-triages-cocktails-private"], "main"),
    (["_food_drafts", "helen-triages-food-private", "content/some-branch"],
     "content/some-branch"),
])
def test_git_fetch_agent_fetches_one_branch(args, ref):
    lines = _accepted_lines("git-fetch-agent.sh", args)
    assert lines[:3] == ["git", "-C", args[0]]
    assert lines[-2] == f"https://github.com/DeckOfPandas/{args[1]}.git"
    assert lines[-1] == f"+refs/heads/{ref}:refs/remotes/origin/{ref}"


# --- git-clone-agent.sh: a repo and a folder, nothing else --------------------

@pytest.mark.parametrize("args", [
    [],
    ["some-other-repo"],
    ["helen-triages-food-private", "_food_drafts", "--template=tmp/hooks"],
    ["helen-triages-food-private", "--template=tmp/hooks"],
    ["helen-triages-food-private", "/etc/elsewhere"],
    ["helen-triages-food-private", "../elsewhere"],
])
def test_git_clone_agent_refuses_extra_options_and_outside_folders(args):
    _assert_refused("git-clone-agent.sh", args)


@pytest.mark.parametrize("args", [
    ["helen-triages-food-private", "_food_drafts"],
    ["helen-triages-cocktails-private"],
])
def test_git_clone_agent_clones_one_of_the_three(args):
    lines = _accepted_lines("git-clone-agent.sh", args)
    url = f"https://github.com/DeckOfPandas/{args[0]}.git"
    assert url in lines
    assert lines[lines.index(url) + 1:] == args[1:]


# --- gh-write.sh: three REST writes, the body always a file under tmp/ --------
#
# Helen, 2026-09-15: "When you want to run commands that build paths at
# runtime, please find a way into scripts that can be statically analysed so
# read/write scope can be checked without asking me." The `api -X` calls this
# replaces could never be allow-listed: `api` is also the door to a merge.

BODY = "tmp/test-agent-wrappers-body.md"


@pytest.fixture
def body_file():
    path = ROOT / BODY
    path.parent.mkdir(exist_ok=True)
    path.write_text("a body\n", encoding="utf-8")
    yield BODY
    path.unlink()


@pytest.mark.parametrize("args", [
    [],
    ["merge", "helen-triages", "1"],
    ["review", "helen-triages", "1", BODY],
    ["close", "helen-triages", "1"],
    ["api", "-X", "PUT", "repos/DeckOfPandas/helen-triages/pulls/1/merge"],
    # a PR from main, or onto anything but main
    ["pr-create", "helen-triages", "main", "t", BODY],
    ["pr-create", "helen-triages", "refs/heads/main", "t", BODY],
    ["pr-create", "helen-triages", "someone:feature", "t", BODY],
    ["pr-create", "helen-triages", "--base=other", "t", BODY],
    ["pr-create", "helen-triages", "feat/../main", "t", BODY],
    ["pr-create", "helen-triages", "feature", "", BODY],
    ["pr-create", "helen-triages", "feature", "t", BODY, "--base", "other"],
    ["pr-create", "helen-triages", "feature", "t"],
    # other repositories
    ["pr-create", "some-other-repo", "feature", "t", BODY],
    ["comment", "DeckOfPandas/helen-triages", "1", BODY],
    ["comment", "helen-triages-lookalike", "1", BODY],
    # bodies from anywhere but a plain file under tmp/
    ["comment", "helen-triages", "1", "/etc/passwd"],
    ["comment", "helen-triages", "1", "tmp/../CLAUDE.md"],
    ["comment", "helen-triages", "1", "tmp/does-not-exist.md"],
    ["comment", "helen-triages", "1", "CLAUDE.md"],
    ["comment", "helen-triages", "1", "@tmp/x.md"],
    # numbers that are not numbers
    ["comment", "helen-triages", "1/merge", BODY],
    ["pr-body", "helen-triages", "-1", BODY],
    ["pr-body", "helen-triages", "", BODY],
    ["pr-body", "helen-triages", "1", BODY, "-f", "state=closed"],
])
def test_gh_write_refuses_everything_but_its_three_writes(body_file, args):
    _assert_refused("gh-write.sh", args)


def test_gh_write_refuses_a_symlinked_body(body_file):
    link = ROOT / "tmp" / "test-agent-wrappers-link.md"
    link.symlink_to(ROOT / "CLAUDE.md")
    try:
        _assert_refused("gh-write.sh",
                        ["comment", "helen-triages", "1", "tmp/test-agent-wrappers-link.md"])
    finally:
        link.unlink()


def _gh_write_lines(args):
    lines = _accepted_lines("gh-write.sh", args)
    assert lines[0] == "sh" and lines[1].endswith("/scripts/gh-agent.sh"), (
        "gh-write.sh must go through gh-agent.sh, so the token's name stays in "
        f"one file; it ran {lines[:2]!r}"
    )
    return lines[2:]


def test_gh_write_opens_a_pr_onto_main(body_file):
    lines = _gh_write_lines(
        ["pr-create", "helen-triages-cocktails-private", "data/x", "(data) a title", BODY])
    assert lines[:3] == ["api", "--method", "POST"]
    assert lines[3] == "repos/DeckOfPandas/helen-triages-cocktails-private/pulls"
    assert "base=main" in lines and "head=data/x" in lines
    assert "title=(data) a title" in lines
    assert f"body=@{BODY}" in lines


def test_gh_write_replaces_a_pr_body_and_nothing_else(body_file):
    lines = _gh_write_lines(["pr-body", "helen-triages", "1081", BODY])
    assert lines[:4] == ["api", "--method", "PATCH", "repos/DeckOfPandas/helen-triages/pulls/1081"]
    fields = [lines[i + 1] for i, line in enumerate(lines) if line in ("-f", "-F")]
    assert fields == [f"body=@{BODY}"], f"a pr-body call sets only the body, not {fields!r}"


def test_gh_write_comments_on_an_issue_or_pr(body_file):
    lines = _gh_write_lines(["comment", "helen-triages", "1064", BODY])
    assert lines[:4] == ["api", "--method", "POST",
                         "repos/DeckOfPandas/helen-triages/issues/1064/comments"]
    fields = [lines[i + 1] for i, line in enumerate(lines) if line in ("-f", "-F")]
    assert fields == [f"body=@{BODY}"]


# --- github-public-status.sh: logged-out status of our own pages only ---------

@pytest.mark.parametrize("args", [
    [],
    ["https://example.com/"],
    ["http://github.com/DeckOfPandas/helen-triages"],
    ["https://github.com/someone-else/repo"],
    ["https://github.com/DeckOfPandasX/repo"],
    ["https://github.com/DeckOfPandas@example.com/"],
    ["https://github.com/DeckOfPandas/../someone-else"],
    ["https://github.com/DeckOfPandas/helen-triages", "--output", "tmp/x"],
    ["https://github.com/DeckOfPandas/helen-triages;id"],
    ["-K", "tmp/config"],
])
def test_github_public_status_refuses_other_urls_and_options(args):
    _assert_refused("github-public-status.sh", args)


@pytest.mark.parametrize("url", [
    "https://github.com/DeckOfPandas/helen-triages/pull/1083",
    "https://github.com/DeckOfPandas-agentic-claude",
    "https://github.com/DeckOfPandas/helen-triages/issues/1064#issuecomment-5679508121",
])
def test_github_public_status_asks_for_a_status_and_nothing_else(url):
    lines = _accepted_lines("github-public-status.sh", [url])
    assert lines[0] == "curl"
    assert lines[-1] == url
    assert "--proto" in lines and "=https" in lines
    assert not any(line in ("-L", "--location", "-H", "--header", "-u", "--user")
                   for line in lines), f"a logged-out status check sent more: {lines!r}"


# --- main-ci-status.sh: is the site deploying? ------------------------------
#
# Added 2026-09-22. A red `main` is a DEPLOY OUTAGE -- the suite gates the
# deploy, so one red merge stops every later one going live, silently, for as
# long as nobody looks (three days in September; DECISIONS §12). The manual has
# asked sessions to check since 2026-09-15 and nobody did, partly because the
# instruction sat on an unmerged branch and partly because the form it
# prescribed was a bracketed `--jq` that prompts Helen. This wrapper takes NO
# arguments, so there is no repo, path or option for a caller to steer.

@pytest.mark.parametrize("args", [
    ["main"],
    ["--repo", "someone-else/repo"],
    ["https://example.com/"],
    ["--output", "tmp/x"],
])
def test_main_ci_status_takes_no_arguments_at_all(args):
    _assert_refused("main-ci-status.sh", args)


def test_main_ci_status_reads_one_fixed_public_endpoint_with_no_credential():
    lines = _accepted_lines("main-ci-status.sh", [])
    assert lines[0] == "curl"
    url = lines[-1]
    assert url.startswith(
        "https://api.github.com/repos/DeckOfPandas/helen-triages/actions/runs"
    ), url
    assert "branch=main" in url
    # A public read: sending a credential here would be scope this does not need.
    assert not any(line in ("-H", "--header", "-u", "--user") for line in lines), lines


def test_main_ci_status_treats_an_empty_answer_as_unanswered_not_green():
    """`{"workflow_runs": []}` means the check did not run, not that all is
    well -- the green-that-lies failure this repo names everywhere else."""
    result = subprocess.run(
        ["python3", str(ROOT / "scripts" / "main_ci_status.py")],
        input='{"workflow_runs": []}',
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 2, result.stdout
    assert "NOT a green result" in result.stderr


def test_main_ci_status_calls_a_failure_a_deploy_outage():
    runs = {"workflow_runs": [
        {"conclusion": "failure", "created_at": "2026-09-12T16:32:00Z",
         "display_title": "Merge pull request #996"},
    ]}
    result = subprocess.run(
        ["python3", str(ROOT / "scripts" / "main_ci_status.py")],
        input=json.dumps(runs),
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 1, result.stdout
    assert "DEPLOY OUTAGE" in result.stdout


# --- scripts/browser/styles.sh, gaps.sh, click-crop.sh: arguments only -------
#
# Added 2026-09-15 alongside guard-unanalyzable-bash.py's new env-assignment
# refusal, so a Playwright question rarely needs a one-off tmp/ script that
# names PLAYWRIGHT_BROWSERS_PATH/NODE_PATH by hand. None of the three touches
# the network or a real build; every case here is refused before `. env.sh`
# runs, so nothing is exercised but the argument checks themselves.

@pytest.mark.parametrize("args", [
    [],
    ["/food/"],
    ["food/", ".btn"],
    ["../food/", ".btn"],
    ["/food/../etc", ".btn"],
    ["http://evil.example/", ".btn"],
    ["/food/", ""],
    ["/food/", ".btn", "abc"],
    ["/food/", ".btn", "199"],
    ["/food/", ".btn", "2001"],
    ["/food/", ".btn", "390", ",color"],
    ["/food/", ".btn", "390", "color,"],
    ["/food/", ".btn", "390", "color,,gap"],
    ["/food/", ".btn", "390", "Color"],
    ["/food/", ".btn", "390", "color;gap"],
    ["/food/", ".btn", "390", "background-color|gap"],
])
def test_styles_refuses_bad_arguments(args):
    _assert_refused("browser/styles.sh", args)


@pytest.mark.parametrize("args", [
    [],
    ["food/"],
    ["../food/"],
    ["/food/../etc"],
    ["http://evil.example/"],
    ["/food/", "abc"],
    ["/food/", "199"],
    ["/food/", "2001"],
])
def test_gaps_refuses_bad_arguments(args):
    _assert_refused("browser/gaps.sh", args)


@pytest.mark.parametrize("args", [
    [],
    ["food/", ".btn", ".results", "name"],
    ["/food/", "", ".results", "name"],
    ["/food/", ".btn,.btn2", ".results", "name"],
    ["/food/", ".btn", "", "name"],
    ["/food/", ".btn", ".results", ""],
    ["/food/", ".btn", ".results", "Name"],
    ["/food/", ".btn", ".results", "name with spaces"],
    ["/food/", ".btn", ".results", "../escape"],
    ["/food/", ".btn", ".results", "name", "abc"],
    ["/food/", ".btn", ".results", "name", "199"],
    ["/food/", ".btn", ".results", "name", "2001"],
])
def test_click_crop_refuses_bad_arguments(args):
    _assert_refused("browser/click-crop.sh", args)


# --- guard-token-expansion.py: gh's jq can read the environment ---------------

def _hook_denies(command: str) -> bool:
    result = subprocess.run(
        ["python3", str(TOKEN_HOOK)],
        input=json.dumps({"tool_input": {"command": command}}),
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    return '"deny"' in result.stdout


@pytest.mark.parametrize("command", [
    "sh scripts/gh-agent.sh issue list --repo DeckOfPandas/helen-triages "
    "--json number --jq 'env | length'",
    "sh scripts/gh-read.sh repos/DeckOfPandas/helen-triages/issues --jq '$ENV'",
    "gh api repos/DeckOfPandas/helen-triages --jq 'env.HOME'",
])
def test_the_token_hook_refuses_a_gh_jq_that_reads_the_environment(command):
    assert _hook_denies(command), (
        f"allowed {command!r}. gh's jq sees the environment (measured "
        "2026-09-11) and gh-agent.sh puts the token there."
    )


@pytest.mark.parametrize("command", [
    "sh scripts/gh-agent.sh issue list --repo DeckOfPandas/helen-triages "
    "--json number,title --jq '.[].title'",
    "sh scripts/gh-read.sh repos/DeckOfPandas/helen-triages/environments",
    "grep -rn env scripts",
])
def test_the_token_hook_leaves_ordinary_gh_and_env_mentions_alone(command):
    assert not _hook_denies(command), f"refused {command!r}"


# --- .claude/settings.json ---------------------------------------------------

def _rules(kind: str) -> list[str]:
    rules = json.loads(SETTINGS.read_text(encoding="utf-8"))["permissions"][kind]
    assert rules, f"no {kind} rules in {SETTINGS} -- has the file moved?"
    return rules


# Every allow rule that ends in ` *`, and so accepts ANY further arguments.
# Each was checked for an option that runs a program before it went in:
# `git fetch --upload-pack=`, `git clone --template=`, `node --import` are why
# those three are NOT here, and `git ls-remote` came out on 2026-09-11 for the
# same reason as fetch. The four scripts/ wrappers are here because their
# arguments are tested above. Adding to this set is a decision, not a chore:
# say in the commit which options of the tool you checked.
#
# FIVE CAME OUT ON 2026-09-21, and removing one is a decision too. Helen:
# "I'm keen to prune rules with *, so let's discuss", then, asked the one
# question that settled four of them -- does Claude ever run on the host? --
# "Claude always runs in a container, never on the host (any more). This will
# be my setup indefinitely."
#   * `Bash(.gh-runtime/bin/gh issue *)`, `Bash(.gh-runtime/bin/gh pr create *)`
#     and `Bash(.node-runtime/node/bin/node --test *)` named extracted runtimes
#     that only ever existed in a HOST checkout. Measured in the container the
#     same day: `which gh node` gives /usr/bin/gh and /usr/bin/node. Dead paths.
#     `Bash(.gh-runtime/bin/gh auth status)` went with them (exact, not open).
#   * `Bash(gh pr create *)` was superseded by the wrapper rules below and by
#     `sh scripts/gh-write.sh pr-create`.
#   * `Bash(curl -s "https://api.github.com/repos/DeckOfPandas/helen-triages/*)`
#     was the interesting one, and it had been REVIEWED AGAINST THE WRONG
#     CRITERION. The standard above is "an option that runs a program"; `curl`
#     has none, but `-o <path>` WRITES A FILE ANYWHERE, and the trailing `*`
#     accepted it. `scripts/gh-read.sh` does these reads now, GET-only and
#     three repos only. The lesson for the next addition: ask what the option
#     can WRITE as well as what it can RUN.
# The matching DENY rules were deliberately left alone. A deny on a dead path
# costs nothing, and removing safety rails is not pruning.
REVIEWED_OPEN_RULES = {
    "Bash(pytest *)",
    "Bash(python3 -m pytest *)",
    "Bash(git status *)",
    "Bash(git diff *)",
    "Bash(git log *)",
    "Bash(git show *)",
    "Bash(git blame *)",
    "Bash(git ls-tree *)",
    "Bash(git check-ignore *)",
    "Bash(git commit -F *)",
    "Bash(git add -- *)",
    "Bash(sh scripts/gh-agent.sh issue list *)",
    "Bash(sh scripts/gh-agent.sh issue view *)",
    "Bash(sh scripts/gh-agent.sh issue comment *)",
    "Bash(sh scripts/gh-agent.sh issue create *)",
    "Bash(sh scripts/gh-agent.sh issue edit *)",
    "Bash(sh scripts/gh-agent.sh pr list *)",
    "Bash(sh scripts/gh-agent.sh pr view *)",
    "Bash(sh scripts/gh-agent.sh pr diff *)",
    "Bash(sh scripts/gh-agent.sh pr create *)",
    "Bash(sh scripts/gh-agent.sh pr comment *)",
    "Bash(sh scripts/gh-agent.sh repo clone *)",
    "Bash(sh scripts/gh-read.sh *)",
    "Bash(sh scripts/gh-write.sh *)",
    "Bash(sh scripts/github-public-status.sh *)",
    "Bash(sh scripts/git-push-agent.sh *)",
    "Bash(sh scripts/git-fetch-agent.sh *)",
    "Bash(sh scripts/git-clone-agent.sh *)",
    "Bash(sh scripts/browser/shoot.sh *)",
    "Bash(sh scripts/browser/crop.sh *)",
    # Added 2026-09-15, alongside guard-unanalyzable-bash.py's env-assignment
    # refusal (Helen: "I want to reduce the number of interruptions to a
    # minimum"). All three only ever GET the local build through the local
    # server (a path validated to start with `/`, contain no `..` and no
    # scheme), and the only one that writes a file (click-crop.sh) writes
    # solely under tmp/shots/, to a name validated as [a-z0-9-]+. None takes
    # an option that runs a program or reads/writes anywhere else.
    "Bash(sh scripts/browser/styles.sh *)",
    "Bash(sh scripts/browser/gaps.sh *)",
    "Bash(sh scripts/browser/click-crop.sh *)",
}


def test_every_open_ended_allow_rule_has_been_reviewed():
    open_rules = {rule for rule in _rules("allow") if rule.endswith(" *)")}
    assert open_rules, "found no open-ended allow rules at all -- parsing broke?"
    unreviewed = sorted(open_rules - REVIEWED_OPEN_RULES)
    assert not unreviewed, (
        "these allow rules accept ANY further arguments and have not been "
        f"reviewed: {unreviewed}. Check the tool has no option that runs a "
        "program or writes outside the project (git fetch --upload-pack, git "
        "clone --template, node --import), prefer an exact command or a "
        "wrapper that checks its own arguments, and only then add it to "
        "REVIEWED_OPEN_RULES."
    )


def test_no_allow_rule_opens_the_gh_api_door():
    """`api` writes as well as reads -- PUT .../pulls/N/merge is a merge, and
    since 2026-09-09 only a rule stands in front of merging. Reads go through
    scripts/gh-read.sh, which cannot write."""
    for rule in _rules("allow"):
        assert not rule.startswith("Bash(sh scripts/gh-agent.sh api"), rule
        assert not rule.startswith("Bash(gh api"), rule
        assert rule != "Bash(sh scripts/gh-agent.sh *)", rule


def test_merging_and_approving_stay_denied():
    deny = set(_rules("deny"))
    for rule in (
        "Bash(gh pr merge *)",
        "Bash(.gh-runtime/bin/gh pr merge *)",
        "Bash(sh scripts/gh-agent.sh pr merge *)",
        "Bash(sh scripts/gh-agent.sh pr review *)",
    ):
        assert rule in deny, f"{rule} left the deny list"


def test_no_allow_rule_names_a_host_only_runtime():
    """`.gh-runtime/` and `.node-runtime/` are host-checkout artefacts, and
    Claude runs only in the container now (Helen, 2026-09-21: "never on the
    host (any more). This will be my setup indefinitely"). In there `gh` and
    `node` are on PATH at /usr/bin. An allow rule naming those paths grants
    nothing and reads as though the host setup were still live."""
    for rule in _rules("allow"):
        assert ".gh-runtime" not in rule, rule
        assert ".node-runtime/node/bin" not in rule, rule


def test_no_allow_rule_lets_curl_choose_where_to_write():
    """`curl -o <path>` writes anywhere, and a rule ending ` *` accepts it.
    GitHub reads go through scripts/gh-read.sh, which is GET-only and cannot
    write at all. Removed 2026-09-21; this keeps it removed."""
    for rule in _rules("allow"):
        assert not rule.startswith("Bash(curl"), rule


def test_no_allow_rule_runs_a_tmp_script():
    """Helen, 2026-09-11, asked whether tmp/ scripts should run without asking:
    "keep asking me please". A tmp/ script is code nobody has reviewed, and the
    checker sees only its name -- it could read outside the project, which
    `blockReadsOutsideWorkingDirectories` exists to stop."""
    for rule in _rules("allow"):
        assert "tmp/" not in rule, rule


def test_every_allow_listed_script_exists():
    named = []
    for rule in _rules("allow"):
        match = re.match(r"Bash\((?:sh|python3) (scripts/\S+?)[ )]", rule)
        if match:
            named.append(match.group(1))
            assert (ROOT / match.group(1)).is_file(), (
                f"{rule} names a script that does not exist -- renamed?"
            )
    assert named, "no allow rule names a scripts/ file -- parsing broke?"
