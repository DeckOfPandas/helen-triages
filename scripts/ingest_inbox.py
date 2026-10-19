#!/usr/bin/env python3
"""Turn `ingest` issues on a private drafts repo into draft files, or say why not.

    python3 scripts/ingest_inbox.py --site food                 # dry run, the plan
    python3 scripts/ingest_inbox.py --site cocktail --write     # write the files
    python3 scripts/ingest_inbox.py --site food --issue 12 --comment
    python3 scripts/ingest_inbox.py --site food --from-file tmp/pasted.md

Run it through `/ingest-inbox`, which is the procedure; this file is the
engine. `model_instructions/INGEST_INBOX_DESIGN.md` §6 describes the envelope
and §8 argues for the issue route; `parse_envelope` in `envelope.py` is the
authority on the envelope.

Flags:

    --site food|cocktail   required; picks the private repo and drafts folder
    --write                write the files; without it the run is a dry run
    --dry-run              the default, accepted so it can be said out loud;
                           contradicts --write
    --issue N              read that one issue, whatever its label or state
    --from-file PATH       parse a local envelope file, batch file or folder
                           instead of fetching
    --comment              post each outcome back on its issue; ignored with
                           --from-file
    --drafts-dir DIR       use DIR as the drafts folder, to prove a run on a
                           copy
    --every-bullet         print the hand-back bullets a standing ruling
                           settles (FOLDS), which are otherwise only counted

It reads the open issues labelled `ingest` on the site's private repo, through
the GitHub API with `AGENT_GH_TOKEN`, and every `.md` under the drafts folder,
recursively. With `--write` it creates `<slug>.md` at the top of the drafts
folder. Its only write to GitHub is the comment `--comment` posts.

The rules:

  - It parses, it never interprets. Every rule in `parse_envelope` is a
    rejection with a one-line reason, never a repair: a missing marker, two
    fenced blocks, YAML that is not a mapping, a fingerprint that disagrees
    with the file it sits under. Guessing what a malformed envelope meant
    would be an invention in the place built to keep inventions out.
  - A duplicate is found by fingerprint (the title, then every amount), never
    by title. A matching fingerprint is reported and not written. A matching
    title with a different fingerprint is a different recipe: it is written,
    and reported for Helen to name.
  - The slug is the whole title. A taken slug gets `-2`, then `-3`, and so on.
  - The file written is the fenced block byte for byte, at a path that does
    not yet exist. Nothing is ever overwritten. One line may differ: an empty
    `notes:` becomes an empty label/text pair.
  - It never commits, never pushes and never closes an issue. The `Fixes #N`
    trailer on the commit the command doc asks for closes the issue.
  - The envelope's version must be in SUPPORTED_VERSIONS.
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
sys.path.insert(0, str(ROOT / "scripts"))

# The parser lives in envelope.py, which imports nothing from this repository
# so that a web Claude can run it on its own output (CLAUDE_WEB_INGEST.md §2).
from envelope import (  # noqa: E402
    FRONT_MATTER, SITES, SLUG_OK, SUPPORTED_VERSIONS, Envelope, Rejected,
    fingerprint, parse_envelope, slug_for, split_batch,
)

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

# Read too: a duplicate of a published recipe is as much a duplicate, and a
# slug taken there collides at promotion.
PUBLISHED_ROOTS = {
    "food": ROOT / "_food_recipes",
    "cocktail": ROOT / "_cocktail_recipes",
}

LABEL = "ingest"


# --- The drafts already here ---

@dataclass
class Existing:
    slug: str
    title: str
    fingerprint: str
    where: str = ""     # "" a draft, "published", or "planned" earlier this run

    @property
    def label(self) -> str:
        if self.where == "published":
            return f"published {self.slug}"
        if self.where == "planned":
            return f"{self.slug} (earlier in this run)"
        return self.slug


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


def scan_drafts(root: Path, site: str, where: str = "") -> list:
    """Every draft (or, with `where="published"`, every recipe) on disk, with
    its fingerprint.

    `rglob`, not `glob`: `_food_drafts/` has staging subfolders and the files
    closest to promotion live in them.
    """
    out = []
    if not root.is_dir():
        return out
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
                            fingerprint(fm, site), where))
    return out


# --- Hand-back bullets a standing ruling already settles ---
# Each is (summary label, pattern on the bullet). Only a bullet the ruling
# settles whatever the recipe is folded, and never one that ASKS, since a fold
# drops its text: the two exceptions are page checks, which Helen takes at
# rewrite, and tags, which the review table carries in full. Every entry is a
# ruling of hers (DECISIONS §4 and §5, MANUAL §5).
ASKS = re.compile(r"\?|\bplease\b|\bsay (if|which)\b|\bconfirm\b|\bcheck\b", re.I)
TAGS_LABEL = "tags and star proposed (in the review table)"
PHOTO_LABEL = "a photo or page check (Helen picks these up at rewrite)"
FOLDS = [
    ("an unprinted time, written as `Estimated N mins`", r"^\*\*Times not printed"),
    ("printed times used as written", r"^\*\*Times (and serving )?are printed"),
    ("an uncooked dish, `cook_time: \"None\"`", r"^\*\*`cook_time` is \"None\""),
    ("a time phrase kept whole (\"plus chilling\")",
     r"^\*\*`prep_time` keeps the source's whole phrase.*bare number\.$"),
    ("`QQ butter`: the source does not say which", r"^\*\*Butter is unspecified"),
    ("salt or pepper with no amount", r"has no amount in the source's list"),
    ("an amount printed as a word or with no number",
     r"word amounts|has no (weight|number|volume)\b|have no number"),
    ("a tin or pan fat flagged `incidental: true`", r"^\*\*[^*]*is `incidental: true`[^*]*\*\*$"),
    ("the issue date read from the page footer", r"^\*\*Issue date is from the page footer"),
    ("no issue date in frame, so the date Helen gave", r"^\*\*No issue date in frame"),
    ("a labelled oven pair rewritten to its fan figure", r"rewrites? gives? the labelled fan figures?"),
    ("no intro, so the tagline is a bare `QQ`", r"^\*\*No intro, so the tagline is a bare"),
    ("source text kept in a `QQ` note", r"^\*\*The source's [^*]*(is|are) in (a|one) `QQ` note"),
    ("a page reference into the same book, kept",
     r"not in frame\.?\*\*\.? I kept (the|both) references?( in both halves)?\.$"),
    ("one source step, one pair", r"^\*\*The method is [^*]*, so (one|two) pairs?\.\*\*$"),
    ("groups named and split as the source heads them",
     r"^\*\*The source's list has an unheaded first block|"
     r"^\*\*(Method and ingredients|Ingredients and method) are both split"),
    ("quantities lifted from the method: the source prints no list",
     r"^\*\*(I lifted the ingredients|There is no ingredient list, so I lifted|"
     r"The source has no ingredient list)"),
    ("a sidebar box: no body, by the 2026-10-18 ruling",
     r"^\*\*This is a sidebar|^\*\*Helen's chat ruling: (sections like this|this will become)"),
    (TAGS_LABEL, r"^\*\*Tags are"),
    # The bold opening, and a word about the picture's quality: "the
    # photograph points to James Martin" is a credit question, not a check.
    (PHOTO_LABEL,
     r"^\*\*[^*]*\b(angled|blurred|clips?|clipped|cropped|show-through|page curve|"
     r"old-style face|hidden by a finger|dark photo|frame opened|in the photo)\b"),
]
# Settled only for a source with that ruling in _data/food/sources.yml.
SOURCE_FOLDS = {
    ("oven", "conventional"): ("a single oven figure its source's ruling converts to fan",
                               r"with no fan figure"),
    ("units", "metric"): ("imperial dropped, as its source's ruling says",
                          r"metric only|imperial"),
}


def fold_hand_back(bullets: list, fm: dict) -> tuple:
    """(bullets still for Helen, [(summary label, bullet)] settled already)."""
    from test_food_sources import source_for

    entry = source_for(str((fm or {}).get("source") or "")) or {}
    rules = [(label, pat) for (key, value), (label, pat) in SOURCE_FOLDS.items()
             if entry.get(key) == value] + FOLDS
    kept, folded = [], []
    for bullet in bullets:
        hit = next((label for label, pat in rules if re.search(pat, bullet, re.I)), None)
        if hit and ASKS.search(bullet) and hit not in (TAGS_LABEL, PHOTO_LABEL):
            hit = None
        if hit:
            folded.append((hit, bullet))
        else:
            kept.append(bullet)
    return kept, folded


def fold_summary(plans: list) -> list:
    """One line per fold label: how many bullets, and which recipes."""
    by_label = {}
    for plan in plans:
        for label, _ in plan.folded:
            by_label.setdefault(label, []).append(plan.slug or plan.origin)
    return [f"{label}: {len(slugs)} ({', '.join(sorted(set(slugs)))})"
            for label, slugs in sorted(by_label.items(), key=lambda kv: -len(kv[1]))]


# --- One envelope -> one plan ---

@dataclass
class Plan:
    number: object = None
    origin: str = ""            # where the envelope came from, for the report
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

    @property
    def kept(self) -> list:
        """The hand-back bullets no standing ruling settles."""
        if not self.envelope:
            return []
        return fold_hand_back(self.envelope.hand_back, self.envelope.fm)[0]

    @property
    def folded(self) -> list:
        if not self.envelope:
            return []
        return fold_hand_back(self.envelope.hand_back, self.envelope.fm)[1]

    def one_line(self) -> str:
        if self.reason:
            return f"REJECTED: {self.reason}"
        if self.duplicate_of:
            return (f"PROBABLE DUPLICATE of {self.duplicate_of} -- same "
                    f"fingerprint, nothing written")
        verb = "wrote" if self.written else "would write"
        return f"{verb} {self.path.name}"

    def comment_text(self) -> str:
        """What `--comment` posts on the issue: the outcome, then the notes (a
        collision, a Sazerac case) and the browser's hand-back list as
        bullets. The issue is where Helen reads on her phone (DECISIONS §11).
        """
        lines = [self.one_line()]
        for note in self.notes:
            lines.append(f"- {note}")
        if self.kept:
            lines.append("")
            lines.append("What the browser could not know:")
            for item in self.kept:
                lines.append(f"- {item}")
        if self.folded:
            lines.append("")
            lines.append(f"And {len(self.folded)} bullet(s) a standing ruling "
                         f"already settles.")
        return "\n".join(lines)


def plan_for(body: str, site: str, existing: list, root: Path, number=None,
             origin="", heading=None) -> Plan:
    plan = Plan(number=number, origin=origin)
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
    if heading and heading != slug:
        plan.notes.append(f"the batch heading says {heading!r}; the title "
                          f"gives {slug!r}, which is the one used")

    same_formula = next(
        (e for e in existing if e.fingerprint == envelope.fingerprint), None)
    if same_formula:
        plan.slug = slug
        plan.duplicate_of = same_formula.label
        return plan

    same_title = [e for e in existing
                  if e.title.strip().lower() == envelope.fm["title"].strip().lower()]
    if same_title:
        plan.notes.append(
            f"THE SAZERAC CASE: {', '.join(e.label for e in same_title)} "
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

    A dumper would lose comment placement, key order and the `[""]` shape
    `method_short` depends on. What the browser wrote is what Helen proofreads.

    One exception: an empty `notes:` becomes the empty label/text pair
    (#1258), through `tidy_drafts.fix_notes_slot`, imported and not retyped.
    That function's other half, labelling unlabelled text `QQ`, cannot fire
    here: `_reject_unlabelled_notes` has already refused any such envelope.
    """
    if not plan.ok:
        raise ValueError("refusing to write a rejected or duplicate envelope")
    if plan.path.exists():
        raise FileExistsError(f"{plan.path} exists; this script never overwrites")
    sys.path.insert(0, str(ROOT / "scripts"))
    from tidy_drafts import fix_notes_slot
    text, changed = fix_notes_slot(plan.envelope.block, plan.path)
    if changed:
        plan.notes.append("the envelope had no notes, so the draft carries an "
                          "empty {label, text} pair to type into")
    plan.path.write_bytes(text.encode("utf-8"))
    plan.written = True


# --- GitHub: the only functions that touch the network ---

def _api(path: str, method="GET", payload=None):
    # Read at the point of use and never printed: the failure below names the
    # variable and never renders it.
    token = os.environ.get("AGENT_GH_TOKEN")
    if not token:
        sys.exit("AGENT_GH_TOKEN is not set, so there is no way to read the issues.")
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
    """Open `ingest` issues: the one network read, and the one function the
    tests replace.

    A single door on purpose: a suite that reaches GitHub fails offline.
    Everything above this line is pure.
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

def _bodies(args) -> list:
    """(issue number or None, origin, body) before any batch is split."""
    if args.from_file:
        path = Path(args.from_file)
        if path.is_dir():
            files = sorted(path.glob("*.md"))
            if not files:
                sys.exit(f"--from-file {path}/ holds no .md files.")
        elif path.is_file():
            files = [path]
        else:
            sys.exit(f"--from-file {path} is neither a file nor a folder.")
        return [(None, f.name, f.read_text(encoding="utf-8")) for f in files]
    try:
        issues = fetch_issues(args.site, args.issue)
    except urllib.error.HTTPError as exc:
        sys.exit(f"GitHub said {exc.code} for {REPOS[args.site]}. A 401 or 403 "
                 f"is the answer, not a problem to route around (CLAUDE.md); "
                 f"if access is genuinely missing, Helen grants it by hand.")
    except urllib.error.URLError as exc:
        sys.exit(f"could not reach GitHub: {exc.reason}")
    return [(i["number"], f"#{i['number']}", i.get("body") or "") for i in issues]


def _envelopes(args) -> list:
    """(issue number or None, origin, heading slug or None, envelope text) for
    every envelope this run should consider, a batch split into its parts."""
    out = []
    for number, origin, body in _bodies(args):
        for heading, text in split_batch(body):
            where = f"{origin} {heading}" if heading else origin
            out.append((number, where, heading, text))
    return out


def render(plans: list, site: str, wrote: bool, every: bool = False) -> str:
    """The plan, one block per envelope. A bullet a standing ruling settles is
    counted in one summary at the end rather than printed, unless `every`."""
    if not plans:
        return (f"No open `{LABEL}` issues on {REPOS[site]}. Nothing to do -- "
                f"which is a fact about the inbox, not a failure.")
    out = [f"{len(plans)} envelope(s) from {REPOS[site]}.", ""]
    for plan in plans:
        out.append(f"{plan.origin}: {plan.one_line()}")
        for note in plan.notes:
            out.append(f"    {note}")
        shown = (plan.envelope.hand_back if plan.envelope else []) if every else plan.kept
        for item in shown:
            out.append(f"    hand-back: {item}")
        out.append("")
    if not every and any(p.folded for p in plans):
        settled = sum(len(p.folded) for p in plans)
        out.append(f"Settled by a standing ruling, so not shown ({settled} "
                   f"bullets; --every-bullet prints them):")
        out.extend(f"    {line}" for line in fold_summary(plans))
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
                         "at Helen's real drafts.")
    ap.add_argument("--recipes-dir", default=None,
                    help="the published collection to check for duplicates; "
                         "the real one by default, none with --drafts-dir")
    ap.add_argument("--every-bullet", action="store_true",
                    help="print the hand-back bullets a standing ruling settles too")
    args = ap.parse_args(argv)

    if args.write and args.dry_run:
        sys.exit("--write and --dry-run contradict each other. Pick one.")

    root = drafts_root(args.site, args.drafts_dir)
    require_drafts(root, args.site)
    existing = scan_drafts(root, args.site)
    # A run on a copy (--drafts-dir) reads published recipes only if told where.
    published = (Path(args.recipes_dir) if args.recipes_dir
                 else None if args.drafts_dir else PUBLISHED_ROOTS[args.site])
    if published:
        existing += scan_drafts(published, args.site, "published")

    plans = []
    for number, origin, heading, body in _envelopes(args):
        plan = plan_for(body, args.site, existing, root, number, origin, heading)
        if args.write and plan.ok:
            write(plan)
        # Every envelope counts for the ones after it, written or not, so a
        # dry run shows the same -2 and the same duplicate a --write would.
        if plan.ok:
            existing.append(Existing(plan.slug, plan.envelope.fm["title"],
                                     plan.envelope.fingerprint,
                                     "" if plan.written else "planned"))
        plans.append(plan)

    print(render(plans, args.site, args.write, args.every_bullet))

    if args.comment and not args.from_file:
        for plan in plans:
            if plan.number is None:
                continue
            post_comment(args.site, plan.number, plan.comment_text())

    return 0


if __name__ == "__main__":
    sys.exit(main())
