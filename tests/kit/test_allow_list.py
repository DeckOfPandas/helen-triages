"""The allow list in .claude/settings.json: what it may and may not open."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SETTINGS = ROOT / ".claude" / "settings.json"


def _rules(kind: str) -> list[str]:
    rules = json.loads(SETTINGS.read_text(encoding="utf-8"))["permissions"][kind]
    assert rules, f"no {kind} rules in {SETTINGS} -- has the file moved?"
    return rules


# Every allow rule that ends in ` *`, and so accepts any further arguments.
# Before one goes in, check the tool for an option that runs a program
# (`git fetch --upload-pack=`, `git clone --template=`, `node --import` are
# why those are not here) and for one that writes a file anywhere
# (`curl -o <path>`). The scripts/ wrappers are here because their arguments
# are tested in test_wrappers.py and test_diff_main_checkout.py. Adding to this
# set is a decision: say in the commit which options of the tool you checked.
REVIEWED_OPEN_RULES = {
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
    "Bash(sh scripts/gh-read.sh *)",
    "Bash(sh scripts/gh-write.sh *)",
    "Bash(sh scripts/github-public-status.sh *)",
    "Bash(sh scripts/git-push-agent.sh *)",
    "Bash(sh scripts/git-fetch-agent.sh *)",
    "Bash(sh scripts/git-clone-agent.sh *)",
    "Bash(sh scripts/git-diff-main-checkout.sh *)",
    # One https URL of plain characters; curl writes only to /dev/null.
    "Bash(sh scripts/check-link.sh *)",
    # One optional repo name from GH_REPOS; a GET through gh-agent.sh.
    "Bash(sh scripts/main-ci-status.sh *)",
    # Paths under tests/, -q/-x/-v and a plain -k; never --basetemp, -p, -c or
    # --rootdir. test_wrappers.py pins every refusal.
    "Bash(sh scripts/pytest.sh *)",
    # A NESTED_DIRS folder and a fixed list of verbs, hooks and external diff
    # off, commit refused on main; tests/kit/test_git_nested.py pins it.
    "Bash(sh scripts/git-nested.sh *)",
    # Arguments after the script name go to the script, never to node, so no
    # node option can be slipped in. Each checks its own arguments, writes only
    # under tmp/ or nothing, and only ever reads the URL or the tmp/ PNG given.
    "Bash(node tools/dev/shoot.js *)",
    "Bash(node tools/dev/slice-png.js *)",
    "Bash(node tools/dev/crop.js *)",
    "Bash(node tools/dev/styles.js *)",
    "Bash(node tools/dev/gaps.js *)",
    # Arguments go to the script, never to python3. One .png under tmp/ and a
    # number; reads that file, writes nothing.
    "Bash(python3 tools/dev/inkbox.py *)",
}


PROJECT_SETTINGS = ROOT / ".claude" / "settings.project.json"


def _project_reviewed() -> dict[str, str]:
    """A project's own open-ended rules, each with the note saying what was
    checked: `_reviewedOpenRules` in .claude/settings.project.json."""
    if not PROJECT_SETTINGS.is_file():
        return {}
    return json.loads(PROJECT_SETTINGS.read_text(encoding="utf-8")).get("_reviewedOpenRules", {})


def test_every_project_review_says_what_was_checked():
    for rule, note in _project_reviewed().items():
        assert isinstance(note, str) and note.strip(), (
            f"{rule} in settings.project.json's _reviewedOpenRules has no note: say which "
            "options of the tool you checked for running a program or writing a file")


def test_every_open_ended_allow_rule_has_been_reviewed():
    open_rules = {rule for rule in _rules("allow") if rule.endswith(" *)")}
    assert open_rules, "found no open-ended allow rules at all -- parsing broke?"
    unreviewed = sorted(open_rules - REVIEWED_OPEN_RULES - set(_project_reviewed()))
    assert not unreviewed, (
        "these allow rules accept ANY further arguments and have not been "
        f"reviewed: {unreviewed}. Check the tool has no option that runs a "
        "program or writes outside the project (git fetch --upload-pack, git "
        "clone --template, node --import), prefer an exact command or a "
        "wrapper that checks its own arguments, and only then add it to "
        "REVIEWED_OPEN_RULES (a kit rule) or to _reviewedOpenRules in "
        ".claude/settings.project.json (a project rule)."
    )


def test_no_allow_rule_opens_the_gh_api_door():
    """`api` writes as well as reads -- PUT .../pulls/N/merge is a merge, and
    only a rule stands in front of merging. Reads go through
    scripts/gh-read.sh, which cannot write."""
    for rule in _rules("allow"):
        assert not rule.startswith("Bash(sh scripts/gh-agent.sh api"), rule
        assert not rule.startswith("Bash(gh api"), rule
        assert rule != "Bash(sh scripts/gh-agent.sh *)", rule


def test_merging_and_approving_stay_denied():
    deny = set(_rules("deny"))
    for rule in (
        "Bash(gh pr merge *)",
        "Bash(sh scripts/gh-agent.sh pr merge *)",
        "Bash(sh scripts/gh-agent.sh pr review *)",
    ):
        assert rule in deny, f"{rule} left the deny list"


def test_the_github_config_cannot_be_edited():
    """scripts/github.local.conf lists the repos the wrappers may act on, so a
    session that could edit it could widen its own reach."""
    deny = set(_rules("deny"))
    for tool in ("Edit", "Write"):
        for path in ("./scripts/github.local.conf", "//workspace/scripts/github.local.conf"):
            assert f"{tool}({path})" in deny, f"{tool}({path}) left the deny list"


def test_no_allow_rule_lets_curl_choose_where_to_write():
    """`curl -o <path>` writes anywhere, and a rule ending ` *` accepts it."""
    for rule in _rules("allow"):
        assert not rule.startswith("Bash(curl"), rule


def test_pytest_is_allowed_only_without_arguments():
    """`--basetemp=<dir>` empties the folder it names, so a pytest rule ending
    ` *` would let one unasked call wipe the project. pytest.ini pins basetemp
    to tmp/pytest; anything past `-q` asks, or goes through scripts/pytest.sh,
    which checks every argument."""
    for rule in _rules("allow"):
        if "pytest" in rule:
            assert rule in ("Bash(python3 -m pytest)", "Bash(python3 -m pytest -q)",
                            "Bash(sh scripts/pytest.sh *)"), rule


def test_no_allow_rule_runs_a_tmp_script():
    """A tmp/ script keeps asking. It is code nobody has reviewed, and the
    checker sees only its name -- it could read outside the project, which
    `blockReadsOutsideWorkingDirectories` exists to stop."""
    for rule in _rules("allow"):
        assert "tmp/" not in rule, rule


def test_every_allow_listed_script_exists():
    named = []
    for rule in _rules("allow"):
        match = re.match(r"Bash\((?:sh|python3|node) ((?:scripts|tools)/\S+?)[ )]", rule)
        if match:
            named.append(match.group(1))
            assert (ROOT / match.group(1)).is_file(), (
                f"{rule} names a script that does not exist -- renamed?"
            )
    assert named, "no allow rule names a scripts/ file -- parsing broke?"
