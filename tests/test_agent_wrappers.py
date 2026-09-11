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
REVIEWED_OPEN_RULES = {
    "Bash(pytest *)",
    "Bash(python3 -m pytest *)",
    "Bash(.node-runtime/node/bin/node --test *)",
    'Bash(curl -s "https://api.github.com/repos/DeckOfPandas/helen-triages/*)',
    "Bash(.gh-runtime/bin/gh issue *)",
    "Bash(git status *)",
    "Bash(git diff *)",
    "Bash(git log *)",
    "Bash(git show *)",
    "Bash(git blame *)",
    "Bash(git ls-tree *)",
    "Bash(git check-ignore *)",
    "Bash(git commit -F *)",
    "Bash(git add -- *)",
    "Bash(gh pr create *)",
    "Bash(.gh-runtime/bin/gh pr create *)",
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
    "Bash(sh scripts/git-push-agent.sh *)",
    "Bash(sh scripts/git-fetch-agent.sh *)",
    "Bash(sh scripts/git-clone-agent.sh *)",
    "Bash(sh scripts/browser/shoot.sh *)",
    "Bash(sh scripts/browser/crop.sh *)",
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
