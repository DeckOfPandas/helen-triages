#!/usr/bin/env python3
"""One page for Helen to review a food ingest batch in a single pass.

    python3 scripts/ingest_review.py --from-file tmp/inbox --out tmp/review.md

It reads the envelopes, as `ingest_inbox.py --from-file` does, and the draft
each one became, by slug, as it stands now (after the finishing pass). It
writes markdown for the drafts PR's description:

  1. a table, one row per recipe: tags, star, servings and times, for her to
     answer with corrections only;
  2. the web Claude's reasons for each row's tags, folded away;
  3. every hand-back bullet no standing ruling settles, by recipe;
  4. one line per standing ruling that settled bullets, with a count.

It writes only `--out` (or stdout), and never a draft. A draft that is not
on disk yet is shown from its envelope and marked so. `ingest-inbox.md` step
5 is the procedure; the folds are `ingest_inbox.FOLDS`.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import ingest_inbox as inbox  # noqa: E402

# GitHub's limit on an issue or PR body, in characters (CLAUDE_WEB_INGEST.md §1).
BODY_LIMIT = 65536
REPLY_SHAPE = ("`12: +make-ahead -main; star poultry; serves ~4`, by row number, "
               "one line per recipe you would change. Silence means the row stands.")


def _cell(value) -> str:
    """Table-safe text: a pipe would end the cell, a newline the row."""
    return str(value).replace("|", "\\|").replace("\n", " ").strip() or "—"


def _draft_fm(root: Path, slug: str):
    """The draft's front matter now, or None when no draft has that slug."""
    for path in root.rglob(f"{slug}.md"):
        match = inbox.FRONT_MATTER.match(path.read_text(encoding="utf-8"))
        if match:
            return yaml.safe_load(match.group(1)) or {}
    return None


def _serves(fm: dict) -> str:
    said = fm.get("serves") or fm.get("makes") or ""
    est = fm.get("serves_estimate")
    return f"{said} (~{est})" if est is not None and said else (said or (f"~{est}" if est else ""))


def _times(fm: dict) -> str:
    def short(value):
        text = str(value or "QQ")
        return re.sub(r"^Estimated\s+", "est. ", text)
    return f"{short(fm.get('prep_time'))} / {short(fm.get('cook_time'))}"


def review(paths: list, root: Path) -> str:
    rows, why, questions, plans = [], [], [], []
    for number, origin, heading, body in paths:
        try:
            env = inbox.parse_envelope(body, "food")
        except inbox.Rejected as reason:
            questions.append((origin, [f"REJECTED: {reason}"]))
            continue
        slug = inbox.slug_for(env.fm["title"])
        fm = _draft_fm(root, slug)
        unwritten = fm is None
        fm = env.fm if unwritten else fm
        plan = inbox.Plan(origin=origin, envelope=env, slug=slug)
        plans.append(plan)
        name = _cell(fm.get("title")) + (" (not written)" if unwritten else "")
        rows.append(f"| {len(rows) + 1} | {name} | {_cell(', '.join(fm.get('tags') or []))} "
                    f"| {_cell(fm.get('star_ingredient') or '')} | {_cell(_serves(fm))} "
                    f"| {_cell(_times(fm))} |")
        reasons = [b for label, b in plan.folded if label == inbox.TAGS_LABEL]
        if reasons:
            why.append(f"- {len(rows)}. " + " ".join(reasons))
        if plan.kept:
            questions.append((f"{len(rows)}. {fm.get('title')}", plan.kept))

    out = [f"## Tags, star and servings: {len(rows)} recipes", "",
           f"Reply with corrections only: {REPLY_SHAPE} \"est.\" is an "
           f"estimated time, which `4-promote/` refuses until it is replaced.", "",
           "| # | Recipe | Tags | Star | Serves | Prep / cook |",
           "|---|---|---|---|---|---|", *rows, ""]
    if why:
        out += ["<details><summary>Why these tags (the web Claude's reasons)</summary>",
                "", *why, "", "</details>", ""]
    total = sum(len(q) for _, q in questions)
    out += [f"## Questions still open: {total}", ""]
    for name, items in questions:
        out.append(f"**{name}**")
        out.extend(f"- {item}" for item in items)
        out.append("")
    summary = inbox.fold_summary(plans)
    if summary:
        settled = sum(len(p.folded) for p in plans)
        out += [f"<details><summary>Settled by a standing ruling: {settled} bullets, "
                f"not asked</summary>", "", *[f"- {line}" for line in summary], "",
                "</details>", ""]
    return "\n".join(out).rstrip() + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--from-file", required=True,
                    help="an envelope file, a batch file, or a folder of them")
    ap.add_argument("--out", default=None, help="write here instead of stdout")
    ap.add_argument("--drafts-dir", default=None,
                    help="read drafts from DIR instead of _food_drafts/")
    args = ap.parse_args(argv)

    root = inbox.drafts_root("food", args.drafts_dir)
    inbox.require_drafts(root, "food")
    page = review(inbox._envelopes(argparse.Namespace(from_file=args.from_file)), root)
    if len(page) > BODY_LIMIT:
        print(f"WARNING: {len(page)} characters. A PR description stops at "
              f"{BODY_LIMIT}, cutting the end silently: post the questions as a "
              f"comment, or review the batch in two halves.", file=sys.stderr)
    if args.out:
        Path(args.out).write_text(page, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(page)
    return 0


if __name__ == "__main__":
    sys.exit(main())
