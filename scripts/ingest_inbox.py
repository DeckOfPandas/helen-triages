#!/usr/bin/env python3
"""Turn `ingest` issues on a private drafts repo into draft files, or say why not.

    python3 scripts/ingest_inbox.py --site food                 # dry run, the plan
    python3 scripts/ingest_inbox.py --site cocktail --write     # write the files
    python3 scripts/ingest_inbox.py --site food --issue 12 --comment
    python3 scripts/ingest_inbox.py --site food --from-file tmp/pasted.md

RUN IT THROUGH `/ingest-inbox`, which is the procedure; this file is only the
engine, the same split `/tidy-drafts` and `/ingest` already use.

WHY AN ISSUE AND NOT A BRANCH (INGEST_INBOX_DESIGN.md §8). Helen finds recipes
away from her desk and hands them to a claude.ai session that has no checkout;
that session's output has to reach `_food_drafts/` or `_cocktail_drafts/`
somehow. A branch would need contents-write on a private repo from a session
that runs neither of this repo's git guard hooks. An issue needs nothing any
token here does not already have -- `GH_TOKEN` is issues-only on the three repos
-- the private repos have no build so nothing an issue carries can publish, and
the session that finally writes the file is a local one, under every guard. So
the envelope travels as issue text and lands here.

IT PARSES, IT NEVER INTERPRETS. Every rule in `parse_envelope` is a rejection
with a one-line reason rather than a repair: a marker that is not there, two
fenced blocks, YAML that is a list, a fingerprint that disagrees with the file
it sits under. This script exists to keep inventions out of the drafts, so
guessing what a malformed envelope meant would be the invention.

IT NEVER COMMITS, NEVER PUSHES, NEVER CLOSES AN ISSUE and never overwrites a
file. The `Fixes #N` trailer on the commit the command doc asks for is what
closes an issue, so the closure is tied to the commit that earned it (CLAUDE.md,
Helen's standing preference). `--write` is the only thing here that touches the
disk, and only ever at a path that does not yet exist.

EVERY SCHEMA RULE IS IMPORTED FROM THE TEST SUITE, NEVER RE-TYPED, for the
reason `tidy_drafts.py`'s header gives at length: a checker carrying its own
copy of the contract eventually accepts a shape the suite rejects while looking
green the whole time.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

from test_taxonomy import _fold, _title_head_clause  # noqa: E402

# THE VERSIONS THIS SCRIPT IMPLEMENTS. §0 of each standalone document tells a
# repo-less browser which one to write, and
# tests/test_ingest_inbox.py::test_both_documents_name_a_supported_version
# holds the two ends together -- the one failure mode §8 calls silent is a
# document teaching v2 to a browser while this file understands only v1.
SUPPORTED_VERSIONS = frozenset({1})

SITES = ("food", "cocktail")

# The PRIVATE repos, never the public one: an envelope carries source text that
# may be copyright, and these two are private for exactly that reason.
REPOS = {
    "food": "DeckOfPandas/helen-triages-food-private",
    "cocktail": "DeckOfPandas/helen-triages-cocktails-private",
}

DRAFT_ROOTS = {
    "food": ROOT / "_food_drafts",
    "cocktail": ROOT / "_cocktail_drafts",
}

LABEL = "ingest"

MARKER = re.compile(r"^<!--\s*ingest\s+v(\d+)\s+([a-z]+)\s*-->$")
FENCE = re.compile(r"^```(.*)$")
FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---", re.S)
HAND_BACK_HEADING = "## What I could not know"
FINGERPRINT_HEADING = "## Fingerprint"
SLUG_OK = re.compile(r"^[a-z0-9-]+$")


class Rejected(Exception):
    """A malformed envelope, with the one line that says which rule it broke."""


# =============================================================================
# THE ENVELOPE
# =============================================================================

@dataclass
class Envelope:
    version: int
    site: str
    block: str          # the fenced block VERBATIM, which is what gets written
    fm: dict
    hand_back: list
    fingerprint: str


def _fenced_blocks(body: str):
    """Every fenced block as (info string, verbatim contents including its
    trailing newline). Counted rather than searched-for: `two fenced blocks` is
    a rejection, so the parser has to see the second one."""
    out, info, buf, inside = [], None, [], False
    for line in body.splitlines(keepends=True):
        match = FENCE.match(line.rstrip("\n"))
        if match and not inside:
            inside, info, buf = True, match.group(1).strip(), []
        elif match and inside:
            out.append((info, "".join(buf)))
            inside = False
        elif inside:
            buf.append(line)
    if inside:
        raise Rejected("a fenced code block is never closed")
    return out


def _strip_fences(body: str) -> str:
    """The prose half. Headings are looked for HERE so that a `##` line inside
    the file being carried can never be mistaken for the envelope's own."""
    out, inside = [], False
    for line in body.splitlines():
        if FENCE.match(line):
            inside = not inside
            continue
        if not inside:
            out.append(line)
    return "\n".join(out)


def _section(prose: str, heading: str) -> list:
    """The non-blank lines under one `## ` heading, up to the next one."""
    lines = prose.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == heading)
    except StopIteration:
        raise Rejected(f"no `{heading}` section") from None
    out = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if line.strip():
            out.append(re.sub(r"^[-*]\s+", "", line.strip()))
    return out


def parse_envelope(body: str, site: str) -> Envelope:
    """§6 of the design, rule for rule. Raises `Rejected` with one line."""
    lines = [line.rstrip() for line in body.replace("\r\n", "\n").split("\n")]
    first = next((line for line in lines if line.strip()), "")
    match = MARKER.match(first.strip())
    if not match:
        raise Rejected(
            f"first non-blank line is not an `<!-- ingest v<N> <site> -->` "
            f"marker: {first.strip()[:60]!r}"
        )
    version, named_site = int(match.group(1)), match.group(2)
    if named_site not in SITES:
        raise Rejected(
            f"marker names site {named_site!r}, which is not one of "
            f"{', '.join(SITES)}"
        )
    if version not in SUPPORTED_VERSIONS:
        raise Rejected(
            f"envelope is v{version} and this script implements "
            f"v{'/v'.join(str(v) for v in sorted(SUPPORTED_VERSIONS))}"
        )
    if named_site != site:
        raise Rejected(f"marker says site {named_site!r} but --site is {site!r}")

    blocks = _fenced_blocks(body)
    if len(blocks) != 1:
        raise Rejected(
            f"{len(blocks)} fenced code blocks; the envelope carries exactly "
            f"one, holding the whole file"
        )
    info, block = blocks[0]
    if info not in ("", "yaml"):
        raise Rejected(
            f"the fenced block's info string is {info!r}; it must be `yaml` or "
            f"empty"
        )
    if not block.startswith("---\n"):
        raise Rejected(
            "the fenced block does not begin with `---`; it must be the whole "
            "file, front matter and all"
        )
    fm_match = FRONT_MATTER.match(block)
    if not fm_match:
        raise Rejected("the fenced block's front matter is never closed with `---`")
    try:
        fm = yaml.safe_load(fm_match.group(1))
    except yaml.YAMLError as exc:
        raise Rejected(
            f"the fenced block is not valid YAML: "
            f"{str(exc).splitlines()[0][:80]}"
        ) from None
    if not isinstance(fm, dict):
        raise Rejected(
            f"the fenced block's YAML is a {type(fm).__name__}, not a mapping"
        )
    title = fm.get("title")
    if not isinstance(title, str) or not title.strip():
        raise Rejected("the fenced block has no `title:`")

    prose = _strip_fences(body)
    hand_back = _section(prose, HAND_BACK_HEADING)
    printed = _section(prose, FINGERPRINT_HEADING)
    if len(printed) != 1:
        raise Rejected(
            f"the `{FINGERPRINT_HEADING}` section has {len(printed)} non-blank "
            f"lines; it carries exactly one"
        )

    envelope = Envelope(version, named_site, block, fm, hand_back, printed[0])
    rebuilt = fingerprint(fm, named_site)
    if rebuilt != envelope.fingerprint:
        raise Rejected(
            f"fingerprint does not match the file it sits under: envelope says "
            f"{envelope.fingerprint!r}, the file gives {rebuilt!r}"
        )
    return envelope


def fingerprint(fm: dict, site: str) -> str:
    """The title lowercased, then every amount in the file's own order.

    THE POINT IS TO COMPARE FORMULAS, NEVER TITLES -- §9.2.1's Sazerac, where
    two genuinely different drinks share a name and four of Helen's own
    ingredient suggestions. An entry with no amount contributes nothing, which
    is why "salt and pepper" is absent from the food document's own example.
    """
    amounts = []
    if site == "food":
        for group in (fm.get("ingredient_groups") or []):
            if not isinstance(group, dict):
                continue
            for item in (group.get("items") or []):
                if isinstance(item, dict) and item.get("amount") not in (None, ""):
                    amounts.append(str(item["amount"]).strip())
    else:
        for item in (fm.get("ingredients") or []):
            if isinstance(item, dict) and item.get("amount") not in (None, ""):
                amounts.append(str(item["amount"]).strip())
    title = str(fm.get("title") or "").strip().lower()
    return " | ".join([title] + amounts)


def slug_for(title: str) -> str:
    """The title's head clause, as `INGEST_ONE_RECIPE.md` §2 says.

    `_title_head_clause` is imported rather than re-derived because
    `test_title_and_slug_dont_diverge` judges the result with it: a slug built
    any other way could fail the suite the moment it lands.
    """
    text = _fold(_title_head_clause(title).replace("’", "").replace("'", ""))
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text)).strip("-")


# =============================================================================
# THE DRAFTS ALREADY HERE
# =============================================================================

@dataclass
class Existing:
    slug: str
    title: str
    fingerprint: str


def drafts_root(site: str, override=None) -> Path:
    return Path(override).resolve() if override else DRAFT_ROOTS[site]


def require_drafts(root: Path, site: str):
    """A loud refusal, never an empty list treated as success (#537)."""
    if not root.is_dir():
        sys.exit(
            f"{root.name}/ is not here. It is a separate private repo "
            f"({REPOS[site].split('/')[-1]}), gitignored from this one, so a "
            f"clean checkout does not have it. Nothing read; nothing written."
        )


def scan_drafts(root: Path, site: str) -> list:
    """Every draft already on disk, with its fingerprint.

    `rglob`, not `glob`: `_food_drafts/` has staging subfolders and the files
    closest to promotion live in them.
    """
    out = []
    for path in sorted(root.rglob("*.md")):
        match = FRONT_MATTER.match(path.read_text(encoding="utf-8"))
        if not match:
            continue
        try:
            fm = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            continue
        if not isinstance(fm, dict):
            continue
        out.append(Existing(path.stem, str(fm.get("title") or ""),
                            fingerprint(fm, site)))
    return out


# =============================================================================
# ONE ENVELOPE -> ONE PLAN
# =============================================================================

@dataclass
class Plan:
    number: object = None
    reason: str = ""            # set iff the envelope was rejected
    envelope: object = None
    slug: str = ""
    path: object = None
    duplicate_of: str = ""      # an existing draft with the same fingerprint
    notes: list = field(default_factory=list)
    written: bool = False

    @property
    def ok(self) -> bool:
        return not self.reason and not self.duplicate_of

    def one_line(self) -> str:
        if self.reason:
            return f"REJECTED: {self.reason}"
        if self.duplicate_of:
            return (f"PROBABLE DUPLICATE of {self.duplicate_of}.md -- same "
                    f"fingerprint, nothing written")
        verb = "wrote" if self.written else "would write"
        return f"{verb} {self.path.name}"


def plan_for(body: str, site: str, existing: list, root: Path, number=None) -> Plan:
    plan = Plan(number=number)
    try:
        envelope = parse_envelope(body, site)
    except Rejected as why:
        plan.reason = str(why)
        return plan
    plan.envelope = envelope

    slug = slug_for(envelope.fm["title"])
    if not SLUG_OK.match(slug):
        plan.reason = (f"slug {slug!r} from title {envelope.fm['title']!r} is "
                       f"not [a-z0-9-]")
        return plan

    same_formula = next(
        (e for e in existing if e.fingerprint == envelope.fingerprint), None)
    if same_formula:
        plan.slug = slug
        plan.duplicate_of = same_formula.slug
        return plan

    same_title = [e for e in existing
                  if e.title.strip().lower() == envelope.fm["title"].strip().lower()]
    if same_title:
        plan.notes.append(
            f"THE SAZERAC CASE: {', '.join(e.slug for e in same_title)} "
            f"share(s) this title and has a DIFFERENT fingerprint, so this is "
            f"a different recipe under the same name. Written separately; "
            f"Helen names it."
        )

    taken = {e.slug for e in existing} | {p.stem for p in root.rglob("*.md")}
    plan.slug = slug
    if slug in taken:
        n = 2
        while f"{slug}-{n}" in taken:
            n += 1
        plan.slug = f"{slug}-{n}"
        plan.notes.append(
            f"slug collision: {slug}.md exists, so this one is "
            f"{plan.slug}.md -- nothing was overwritten"
        )
    plan.path = root / f"{plan.slug}.md"
    return plan


def write(plan: Plan) -> None:
    """The fenced block, byte for byte. Never a YAML round-trip.

    A dumper would lose comment placement, key order and the exact `[""]` shape
    `method_short` depends on -- `tidy_drafts.py` refuses one for the same
    reason. What the browser wrote is what Helen proofreads.
    """
    if not plan.ok:
        raise ValueError("refusing to write a rejected or duplicate envelope")
    if plan.path.exists():
        raise FileExistsError(f"{plan.path} exists; this script never overwrites")
    plan.path.write_bytes(plan.envelope.block.encode("utf-8"))
    plan.written = True


# =============================================================================
# GITHUB -- the only two functions that touch the network
# =============================================================================

def _api(path: str, method="GET", payload=None):
    token = os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("GH_TOKEN is not set, so there is no way to read the issues.")
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        method=method,
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "helen-triages-ingest-inbox",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8") or "null")


def fetch_issues(site: str, number=None) -> list:
    """THE ONE FUNCTION THE TESTS REPLACE. Open `ingest` issues, newest last.

    Kept to a single door on purpose: a test that has to stub two of these will
    one day stub one, and a suite that reaches GitHub is a suite that fails on a
    train. Everything above this line is pure.
    """
    repo = REPOS[site]
    if number is not None:
        issue = _api(f"/repos/{repo}/issues/{number}")
        return [issue]
    issues = _api(f"/repos/{repo}/issues?state=open&labels={LABEL}&per_page=100")
    return [i for i in issues if "pull_request" not in i]


def post_comment(site: str, number: int, text: str) -> None:
    _api(f"/repos/{REPOS[site]}/issues/{number}/comments", "POST", {"body": text})


# =============================================================================

def _envelopes(args) -> list:
    """(issue number or None, body) for everything this run should consider."""
    if args.from_file:
        path = Path(args.from_file)
        if not path.is_file():
            sys.exit(f"--from-file {path} is not a file.")
        return [(None, path.read_text(encoding="utf-8"))]
    try:
        issues = fetch_issues(args.site, args.issue)
    except urllib.error.HTTPError as exc:
        sys.exit(f"GitHub said {exc.code} for {REPOS[args.site]}. The token is "
                 f"issues-only on three repos; nothing here routes around that.")
    except urllib.error.URLError as exc:
        sys.exit(f"could not reach GitHub: {exc.reason}")
    return [(i["number"], i.get("body") or "") for i in issues]


def render(plans: list, site: str, wrote: bool) -> str:
    if not plans:
        return (f"No open `{LABEL}` issues on {REPOS[site]}. Nothing to do -- "
                f"which is a fact about the inbox, not a failure.")
    out = [f"{len(plans)} envelope(s) from {REPOS[site]}.", ""]
    for plan in plans:
        where = f"#{plan.number}" if plan.number is not None else "--from-file"
        out.append(f"{where}: {plan.one_line()}")
        for note in plan.notes:
            out.append(f"    {note}")
        for item in (plan.envelope.hand_back if plan.envelope else []):
            out.append(f"    hand-back: {item}")
        out.append("")
    ok = sum(1 for p in plans if p.ok)
    out.append(f"{ok} writable, {sum(1 for p in plans if p.reason)} rejected, "
               f"{sum(1 for p in plans if p.duplicate_of)} probable duplicate(s).")
    if not wrote and ok:
        out.append("Dry run -- nothing written. Re-run with --write.")
    out.append("Nothing was committed and no issue was closed; the `Fixes #N` "
               "trailer on your commit does that.")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--site", required=True, choices=SITES)
    ap.add_argument("--write", action="store_true",
                    help="write the files (default is a dry run)")
    ap.add_argument("--dry-run", action="store_true",
                    help="the default; accepted so it can be said out loud")
    ap.add_argument("--issue", type=int, default=None, help="one issue number")
    ap.add_argument("--comment", action="store_true",
                    help="post the outcome back on the issue")
    ap.add_argument("--from-file", default=None,
                    help="parse a local envelope file instead of fetching")
    ap.add_argument("--drafts-dir", default=None,
                    help="operate on a different directory. Exists so this can "
                         "be proved against a COPY before it is ever pointed "
                         "at Helen's real drafts -- see the command doc.")
    args = ap.parse_args(argv)

    if args.write and args.dry_run:
        sys.exit("--write and --dry-run contradict each other. Pick one.")

    root = drafts_root(args.site, args.drafts_dir)
    require_drafts(root, args.site)
    existing = scan_drafts(root, args.site)

    plans = []
    for number, body in _envelopes(args):
        plan = plan_for(body, args.site, existing, root, number)
        if args.write and plan.ok:
            write(plan)
            existing.append(Existing(plan.slug, plan.envelope.fm["title"],
                                     plan.envelope.fingerprint))
        plans.append(plan)

    print(render(plans, args.site, args.write))

    if args.comment and not args.from_file:
        for plan in plans:
            if plan.number is None:
                continue
            post_comment(args.site, plan.number, plan.one_line())

    return 0


if __name__ == "__main__":
    sys.exit(main())
