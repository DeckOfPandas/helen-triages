"""The scripts/ GitHub wrappers: what each accepts and refuses, in dry-run mode.

Each test runs against a copy of scripts/ with its own github.conf, so the
shipped placeholder config is never edited and nothing touches the network.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

CONF = """\
# test config
GH_OWNER=acme
GH_REPOS="site drafts"   # first is the default
GH_AGENT_USER=acme-bot

MAIN_PUSH_REPOS=drafts
"""


@pytest.fixture
def project(tmp_path: Path, kit_root: Path) -> Path:
    shutil.copytree(kit_root / "scripts", tmp_path / "scripts")
    (tmp_path / "scripts" / "github.local.conf").unlink(missing_ok=True)
    (tmp_path / "scripts" / "github.conf").write_text(CONF)
    (tmp_path / "tmp").mkdir()
    (tmp_path / "tmp" / "body.md").write_text("hello\n")
    return tmp_path


def run(project: Path, script: str, *args: str, conf: str | None = None):
    if conf is not None:
        (project / "scripts" / "github.conf").write_text(conf)
    return subprocess.run(
        ["sh", f"scripts/{script}", *args],
        cwd=project, capture_output=True, text=True, timeout=30,
        # The ceiling stops git finding the kit's own checkout above the copy,
        # whose github.local.conf would otherwise be read.
        env={"PATH": "/usr/local/bin:/usr/bin:/bin", "AGENT_WRAPPER_DRY_RUN": "1",
             "AGENT_GH_TOKEN": "not-a-real-token", "GIT_CEILING_DIRECTORIES": str(project.parent)},
    )


def ok(result) -> list[str]:
    assert result.returncode == 0, result.stderr
    return result.stdout.splitlines()


def refused(result) -> bool:
    return result.returncode == 2 and "refused" in result.stderr


# --- push ---------------------------------------------------------------

def test_push_a_branch_to_the_default_repo(project):
    out = ok(run(project, "git-push-agent.sh", "feat:feat"))
    assert "https://github.com/acme/site.git" in out
    assert out[-1] == "feat:feat"
    assert any("git-credential-agent-token.sh" in line for line in out)


@pytest.mark.parametrize("refspec", ["feat:main", "+feat:main", "feat:refs/heads/main",
                                     ":main", "feat:heads/main", "feat:master"])
def test_push_to_main_is_refused(project, refspec):
    assert refused(run(project, "git-push-agent.sh", refspec))


def test_push_to_main_allowed_for_main_push_repos(project):
    out = ok(run(project, "git-push-agent.sh", "feat:main", "drafts", "sub"))
    assert "https://github.com/acme/drafts.git" in out


@pytest.mark.parametrize("args", [["feat"], ["HEAD"], ["-f:x"], ["feat:feat", "other"],
                                  ["feat:feat", "site", "/etc"], ["feat:feat", "site", "../x"],
                                  ["feat:feat", "site", "-C"], ["a:a", "site", ".", "extra"]])
def test_push_refusals(project, args):
    assert refused(run(project, "git-push-agent.sh", *args))


# --- clone / fetch ------------------------------------------------------------

def test_clone(project):
    out = ok(run(project, "git-clone-agent.sh", "drafts", "_drafts"))
    assert out[-2:] == ["https://github.com/acme/drafts.git", "_drafts"]


@pytest.mark.parametrize("args", [["other"], ["site", "/abs"], ["site", "d", "--template=x"]])
def test_clone_refusals(project, args):
    assert refused(run(project, "git-clone-agent.sh", *args))


def test_fetch_agent(project):
    out = ok(run(project, "git-fetch-agent.sh", "_drafts", "drafts", "topic"))
    assert out[-1] == "+refs/heads/topic:refs/remotes/origin/topic"


@pytest.mark.parametrize("args", [["/x", "drafts"], ["d", "nope"], ["d", "drafts", "-x"],
                                  ["d", "drafts", "a:b"], ["d", "drafts", "main", "--nope"]])
def test_fetch_agent_refusals(project, args):
    assert refused(run(project, "git-fetch-agent.sh", *args))


def test_fetch_main_uses_the_default_repo(project):
    out = ok(run(project, "git-fetch-main.sh"))
    assert "https://github.com/acme/site.git" in out
    assert refused(run(project, "git-fetch-main.sh", "--upload-pack=x"))


# --- gh-read --------------------------------------------------------------------

def test_read_fields(project):
    out = ok(run(project, "gh-read.sh", "repos/acme/site/pulls/3", "--fields", "state,user.login"))
    assert out[-2:] == ["--jq", "[.state, .user.login] | @tsv"]
    assert "GET" in out


def test_read_each_and_query_string(project):
    out = ok(run(project, "gh-read.sh", "repos/acme/drafts/pulls?state=all", "--each", "number"))
    assert out[-1] == ".[] | [.number] | @tsv"


@pytest.mark.parametrize("args", [
    ["repos/other/site/pulls"], ["repos/acme/nope"], ["repos/acme/site/../x"],
    ["repos/acme/sitex"], ["repos/acme/site", "-X", "POST"], ["repos/acme/site", "-f", "a=b"],
    ["repos/acme/site", "--jq", "env"], ["repos/acme/site", "--jq", "$ENV.X"],
    ["repos/acme/site", "--fields", "a|b"], ["repos/acme/site", "--fields", "a", "--jq", "."],
])
def test_read_refusals(project, args):
    assert refused(run(project, "gh-read.sh", *args))


# --- gh-write -------------------------------------------------------------------

def test_pr_create(project):
    out = ok(run(project, "gh-write.sh", "pr-create", "site", "feat/x", "Title", "tmp/body.md"))
    assert "repos/acme/site/pulls" in out and "base=main" in out and "head=feat/x" in out


@pytest.mark.parametrize("args", [
    ["pr-create", "site", "main", "T", "tmp/body.md"],
    ["pr-create", "site", "owner:feat", "T", "tmp/body.md"],
    ["pr-create", "other", "feat", "T", "tmp/body.md"],
    ["pr-create", "site", "feat", "", "tmp/body.md"],
    ["pr-create", "site", "feat", "T", "body.md"],
    ["pr-create", "site", "feat", "T", "tmp/../scripts/github.conf"],
    ["pr-create", "site", "feat", "T", "tmp/missing.md"],
    ["comment", "site", "01", "tmp/body.md"],
    ["merge", "site", "1"],
])
def test_write_refusals(project, args):
    assert refused(run(project, "gh-write.sh", *args))


def test_comment(project):
    out = ok(run(project, "gh-write.sh", "comment", "drafts", "12", "tmp/body.md"))
    assert "repos/acme/drafts/issues/12/comments" in out


def test_issue_create(project):
    out = ok(run(project, "gh-write.sh", "issue-create", "site", "A title", "tmp/body.md"))
    assert "repos/acme/site/issues" in out and "title=A title" in out and "body=@tmp/body.md" in out
    assert not any(line.startswith("labels") for line in out)


def test_issue_create_with_a_label(project):
    out = ok(run(project, "gh-write.sh", "issue-create", "site", "T", "tmp/body.md", "parked"))
    assert "labels[]=parked" in out


def test_label_create(project):
    out = ok(run(project, "gh-write.sh", "label-create", "drafts", "parked", "9a9a9a"))
    assert "repos/acme/drafts/labels" in out and "name=parked" in out and "color=9a9a9a" in out


def test_issue_label(project):
    out = ok(run(project, "gh-write.sh", "issue-label", "site", "5", "parked"))
    assert "repos/acme/site/issues/5/labels" in out and "labels[]=parked" in out and "POST" in out


def test_a_label_may_hold_single_spaces(project):
    out = ok(run(project, "gh-write.sh", "issue-label", "site", "5", "devops and docs"))
    assert "labels[]=devops and docs" in out


def _without_dry_run(project: Path, *args: str, agent_exit: int):
    """gh-write.sh for real, with gh-agent.sh replaced by a stub that records
    its arguments and exits `agent_exit`: nothing reaches the network."""
    (project / "scripts" / "gh-agent.sh").write_text(
        f'printf "%s\\n" "$@" >> "{project}/tmp/agent-calls"\nexit {agent_exit}\n')
    return subprocess.run(
        ["sh", "scripts/gh-write.sh", *args], cwd=project, capture_output=True, text=True,
        timeout=30, env={"PATH": "/usr/local/bin:/usr/bin:/bin",
                         "GIT_CEILING_DIRECTORIES": str(project.parent)})


@pytest.mark.parametrize("args", [
    ["issue-label", "site", "5", "no such label"],
    ["issue-create", "site", "T", "tmp/body.md", "nolabel"],
])
def test_a_label_that_does_not_exist_is_refused_before_any_write(project, args):
    result = _without_dry_run(project, *args, agent_exit=1)
    assert refused(result) and "not an existing label" in result.stderr
    calls = (project / "tmp" / "agent-calls").read_text().splitlines()
    assert "POST" not in calls, "the write ran although the label check failed"
    assert any(c.startswith("repos/acme/site/labels/") for c in calls)


def test_the_label_check_encodes_spaces(project):
    _without_dry_run(project, "issue-label", "site", "5", "devops and docs", agent_exit=1)
    calls = (project / "tmp" / "agent-calls").read_text().splitlines()
    assert "repos/acme/site/labels/devops%20and%20docs" in calls


@pytest.mark.parametrize("args", [
    ["issue-create", "other", "T", "tmp/body.md"],
    ["issue-create", "site", "", "tmp/body.md"],
    ["issue-create", "site", "T", "body.md"],
    ["issue-create", "site", "T", "tmp/body.md", "two  words"],
    ["issue-create", "site", "T", "tmp/body.md", " lead"],
    ["issue-create", "site", "T", "tmp/body.md", "-x"],
    ["issue-create", "site", "T", "tmp/body.md", "a", "b"],
    ["label-create", "site", "parked", "#9a9a9a"],
    ["label-create", "site", "parked", "9a9a9"],
    ["label-create", "site", "parked", "gggggg"],
    ["label-create", "site", "a;b", "9a9a9a"],
    ["label-create", "other", "parked", "9a9a9a"],
    ["issue-label", "site", "05", "parked"],
    ["issue-label", "site", "x", "parked"],
    ["issue-label", "site", "5", "two  words"],
    ["issue-label", "site", "5", "trail "],
    ["issue-label", "site", "5", "a/b"],
    ["issue-label", "site", "5", "-x"],
    ["issue-label", "other", "5", "parked"],
    ["issue-label", "site", "5"],
    ["issue-label", "site", "5", "parked", "more"],
])
def test_issue_and_label_refusals(project, args):
    assert refused(run(project, "gh-write.sh", *args))


# --- PR-only repos ----------------------------------------------------------------

PR_ONLY_CONF = CONF + "PR_ONLY_REPOS=kit\n"
PR_ONLY_CONF = PR_ONLY_CONF.replace('GH_REPOS="site drafts"', 'GH_REPOS="site drafts kit"')


@pytest.mark.parametrize("args", [
    ["comment", "kit", "1", "tmp/body.md"],
    ["issue-create", "kit", "T", "tmp/body.md"],
    ["issue-label", "kit", "1", "parked"],
    ["label-create", "kit", "parked", "9a9a9a"],
])
def test_a_pr_only_repo_refuses_every_write_but_a_pr(project, args):
    result = run(project, "gh-write.sh", *args, conf=PR_ONLY_CONF)
    assert refused(result) and "PR_ONLY_REPOS" in result.stderr


def test_a_pr_only_repo_takes_a_pr_and_its_body(project):
    out = ok(run(project, "gh-write.sh", "pr-create", "kit", "feat/x", "T", "tmp/body.md",
                  conf=PR_ONLY_CONF))
    assert "repos/acme/kit/pulls" in out
    out = ok(run(project, "gh-write.sh", "pr-body", "kit", "4", "tmp/body.md"))
    assert "repos/acme/kit/pulls/4" in out


def test_a_pr_only_repos_main_is_never_pushed(project):
    assert refused(run(project, "git-push-agent.sh", "feat:main", "kit", "sub", conf=PR_ONLY_CONF))
    assert ok(run(project, "git-push-agent.sh", "feat:feat", "kit", "sub"))


def test_other_repos_keep_their_writes_beside_a_pr_only_one(project):
    out = ok(run(project, "gh-write.sh", "comment", "site", "1", "tmp/body.md", conf=PR_ONLY_CONF))
    assert "repos/acme/site/issues/1/comments" in out


# --- public status --------------------------------------------------------------

@pytest.mark.parametrize("url", ["https://github.com/acme/site/pull/1", "https://github.com/acme-bot"])
def test_public_status_ok(project, url):
    assert ok(run(project, "github-public-status.sh", url))[-1] == url


@pytest.mark.parametrize("url", ["https://github.com/other", "https://github.com/acme@evil.com",
                                 "http://github.com/acme", "https://github.com/acmex"])
def test_public_status_refusals(project, url):
    assert refused(run(project, "github-public-status.sh", url))


# --- check a link -----------------------------------------------------------------

@pytest.mark.parametrize("url", ["https://example.org/page", "https://www.gov.uk/a/b?c=1&d=2#e",
                                 "https://web.archive.org/web/20250323181601/https://ahdb.org.uk/news/x"])
def test_check_link_ok(project, url):
    out = ok(run(project, "check-link.sh", url))
    assert out[-1] == url
    assert "/dev/null" in out and "--location" in out and "--proto" in out


@pytest.mark.parametrize("url", ["http://example.org", "ftp://example.org", "example.org",
                                 "https://user@example.org", "https://example.org/../x",
                                 "https://example.org/a b", "https://example.org/$(id)",
                                 "https://example.org/x;rm", ""])
def test_check_link_refusals(project, url):
    assert refused(run(project, "check-link.sh", url))


@pytest.mark.parametrize("url", ["http://localhost:4001/", "http://localhost:4001/mysite/about/"])
def test_check_link_reaches_a_local_server_over_plain_http(project, url):
    out = ok(run(project, "check-link.sh", url))
    assert out[-1] == url
    assert "--proto" in out and out[out.index("--proto") + 1] == "=http"
    assert "--location" not in out and "--user-agent" not in out


@pytest.mark.parametrize("url", ["http://localhost/", "http://localhost:4001",
                                 "http://localhost:40a1/", "http://localhost:4001@evil.org/",
                                 "http://localhost.evil.org:4001/", "http://127.0.0.1:4001/"])
def test_check_link_refuses_any_other_plain_http(project, url):
    assert refused(run(project, "check-link.sh", url))


def test_check_link_takes_one_url(project):
    assert refused(run(project, "check-link.sh", "https://a.org", "https://b.org"))
    assert refused(run(project, "check-link.sh"))


# --- part of the suite ------------------------------------------------------------

@pytest.mark.parametrize("args", [
    ["tests/kit/test_wrappers.py"],
    ["-q", "-x", "tests/kit/test_hooks.py::test_guard_passes", "tests/kit/"],
    ["-k", "label and not create", "tests/kit/test_wrappers.py"],
    ["-v", "tests/test_site.py", "-k", "food"],
])
def test_pytest_runs_named_tests_with_the_arguments_unchanged(project, args):
    assert ok(run(project, "pytest.sh", *args)) == ["python3", "-m", "pytest", *args]


@pytest.mark.parametrize("args", [
    [],
    ["-q"],
    ["--basetemp=.", "tests/x.py"],
    ["tests/x.py", "--basetemp", "."],
    ["-p", "evil", "tests/x.py"],
    ["--rootdir=/", "tests/x.py"],
    ["-c", "/etc/x.ini", "tests/x.py"],
    ["tests/../scripts/x.py"],
    ["/workspace/tests/x.py"],
    ["src/test_x.py"],
    ["tests/x.py[a]"],
    ["tests/x.py", "-k"],
    ["-k", "a(b)", "tests/x.py"],
    ["-k", "--basetemp=.", "tests/x.py"],
    ["-k", "", "tests/x.py"],
    ["tests/x.py", "--end--", "--basetemp=."],
])
def test_pytest_refuses_anything_it_cannot_check(project, args):
    assert refused(run(project, "pytest.sh", *args))


# --- config parsing ---------------------------------------------------------------

@pytest.mark.parametrize("conf", [
    "GH_OWNER=your-org\nGH_REPOS=a\nGH_AGENT_USER=b\n",           # placeholder
    "GH_OWNER=acme\nGH_REPOS=a\nGH_AGENT_USER=b\nSURPRISE=1\n",   # unknown key
    "GH_OWNER=acme\nGH_REPOS=a\nGH_AGENT_USER=b\nMAIN_PUSH_REPOS=z\n",
    "GH_OWNER=acme\nGH_REPOS=\"a b;rm\"\nGH_AGENT_USER=b\n",
    "GH_OWNER=$(id)\nGH_REPOS=a\nGH_AGENT_USER=b\n",
    "GH_OWNER=acme\nGH_REPOS=\nGH_AGENT_USER=b\n",
    "GH_OWNER=acme\nGH_REPOS=a\nGH_AGENT_USER=b\nPR_ONLY_REPOS=z\n",
    "GH_OWNER=acme\nGH_REPOS=a\nGH_AGENT_USER=b\nMAIN_PUSH_REPOS=a\nPR_ONLY_REPOS=a\n",
])
def test_bad_config_is_refused(project, conf):
    assert refused(run(project, "git-fetch-main.sh", conf=conf))


def test_a_config_saved_with_windows_line_endings_is_read(project):
    """An editor on Windows saves CRLF. Each value then ends in a carriage
    return, which the account-name check refuses with a message about a name
    that looks right."""
    out = ok(run(project, "git-fetch-main.sh", conf=CONF.replace("\n", "\r\n")))
    assert "https://github.com/acme/site.git" in out
    out = ok(run(project, "git-push-agent.sh", "feat:main", "drafts", "sub"))
    assert "https://github.com/acme/drafts.git" in out


def test_shipped_config_is_the_placeholder_or_valid(kit_root, project):
    # The kit ships the placeholder; a project made from it may commit its own.
    shipped = (kit_root / "scripts" / "github.conf").read_text()
    result = run(project, "git-fetch-main.sh", conf=shipped)
    if "GH_OWNER=your-org" in shipped:
        assert refused(result) and "placeholder" in result.stderr
    else:
        ok(result)


def test_local_config_replaces_the_committed_one(project):
    shipped = "GH_OWNER=your-org\nGH_REPOS=a\nGH_AGENT_USER=b\n"
    (project / "scripts" / "github.local.conf").write_text(CONF)
    out = ok(run(project, "git-fetch-main.sh", conf=shipped))
    assert "https://github.com/acme/site.git" in out


def test_a_worktree_reads_the_main_checkouts_local_config(tmp_path, kit_root):
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]
    main = tmp_path / "main"
    shutil.copytree(kit_root / "scripts", main / "scripts")
    (main / "scripts" / "github.conf").write_text("GH_OWNER=your-org\nGH_REPOS=a\nGH_AGENT_USER=b\n")
    (main / "scripts" / "github.local.conf").unlink(missing_ok=True)
    (main / ".gitignore").write_text("scripts/github.local.conf\n")
    subprocess.run([*git, "init", "-q"], cwd=main, check=True)
    subprocess.run([*git, "add", "."], cwd=main, check=True)
    subprocess.run([*git, "commit", "-qm", "x"], cwd=main, check=True)
    subprocess.run([*git, "worktree", "add", "-q", str(main / "wt")], cwd=main, check=True)
    (main / "scripts" / "github.local.conf").write_text(CONF)
    assert not (main / "wt" / "scripts" / "github.local.conf").exists()
    out = ok(run(main / "wt", "git-fetch-main.sh"))
    assert "https://github.com/acme/site.git" in out


def test_credential_helper(project):
    done = subprocess.run(
        ["sh", str(project / "scripts" / "git-credential-agent-token.sh"), "get"],
        cwd=project, capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin", "AGENT_GH_TOKEN": "not-a-real-token",
             "GIT_CEILING_DIRECTORIES": str(project.parent)},
    )
    assert done.stdout.splitlines() == ["username=acme-bot", "password=not-a-real-token"]
    store = subprocess.run(
        ["sh", str(project / "scripts" / "git-credential-agent-token.sh"), "store"],
        cwd=project, capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin", "GIT_CEILING_DIRECTORIES": str(project.parent)},
    )
    assert store.stdout == ""
