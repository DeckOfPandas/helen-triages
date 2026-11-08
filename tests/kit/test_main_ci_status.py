"""scripts/main-ci-status.sh and main_ci_status.py: the call it makes and the verdict it reads."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from .test_wrappers import ok, project, refused, run  # noqa: F401  (project is a fixture)

REPO = "acme/site"


def verdict(kit_root: Path, runs, repo: str = REPO) -> subprocess.CompletedProcess:
    body = runs if isinstance(runs, str) else json.dumps({"workflow_runs": runs})
    return subprocess.run(["python3", str(kit_root / "scripts" / "main_ci_status.py"), repo],
                          input=body, capture_output=True, text=True, timeout=30)


def push(conclusion, title="a merge"):
    return {"event": "push", "head_repository": {"full_name": REPO}, "conclusion": conclusion,
            "display_title": title, "created_at": "2026-11-02T10:00:00Z"}


def fork_pr(conclusion):
    return {"event": "pull_request", "head_repository": {"full_name": "someone/site"},
            "conclusion": conclusion, "display_title": "fork", "created_at": "2026-11-02T11:00:00Z"}


def test_reads_the_default_repo_with_get(project):
    out = ok(run(project, "main-ci-status.sh"))
    assert out[2:5] == ["api", "--method", "GET"]
    assert "repos/acme/site/actions/runs?branch=main&per_page=10" in out
    assert out[-1] == "acme/site"


def test_reads_a_named_repo(project):
    out = ok(run(project, "main-ci-status.sh", "drafts"))
    assert "repos/acme/drafts/actions/runs?branch=main&per_page=10" in out and out[-1] == "acme/drafts"


@pytest.mark.parametrize("args", [["other"], ["site", "x"], ["../site"], ["-X"]])
def test_refusals(project, args):
    assert refused(run(project, "main-ci-status.sh", *args))


def test_green(kit_root):
    done = verdict(kit_root, [push("success"), push("failure")])
    assert done.returncode == 0 and "GREEN" in done.stdout and "1 of the last 2" in done.stdout


def test_still_running(kit_root):
    done = verdict(kit_root, [push(None), push("success")])
    assert done.returncode == 1 and "not finished" in done.stdout


def test_cancelled_is_not_red(kit_root):
    done = verdict(kit_root, [push("cancelled"), push("success")])
    assert done.returncode == 1 and "CANCELLED" in done.stdout and "Nothing is broken" in done.stdout


def test_red(kit_root):
    done = verdict(kit_root, [push("failure"), push("success")])
    assert done.returncode == 1 and "main is FAILURE" in done.stdout


def test_a_forks_pull_request_is_listed_but_not_judged(kit_root):
    done = verdict(kit_root, [fork_pr("failure"), push("success")])
    assert done.returncode == 0 and "[not a push to main]" in done.stdout


def test_a_dependabot_run_is_not_judged(kit_root):
    dependabot = dict(push("failure"), event="dynamic")
    assert verdict(kit_root, [dependabot, push("success")]).returncode == 0


@pytest.mark.parametrize("body", ["", "not json", "[]", json.dumps({"workflow_runs": []}),
                                  json.dumps({"workflow_runs": [fork_pr("success")]})])
def test_no_answer_is_not_green(kit_root, body):
    assert verdict(kit_root, body).returncode == 2


def test_needs_the_repo(kit_root):
    assert verdict(kit_root, [push("success")], repo="site").returncode == 2
