---
description: Work the `ingest` issue inbox on a private drafts repo -- parse each envelope Helen pasted in from her phone, write the files it earns, and hand her ONE list of everything that needs her.
---

Helen has put recipes into `ingest` issues from away from her desk.
`scripts/ingest_inbox.py` is the engine; this file is the procedure around it.
Same split as `/tidy-drafts` and `/ingest`: the script reports and writes
nothing but files, the doc decides.

**Read the script's module docstring before the first run**, and
`model_instructions/INGEST_INBOX_DESIGN.md` §6 for the envelope. This command
does not restate either.

## The boundary, in one line

The script does the mechanical half: parse, slug, deduplicate, write. **Every
judgement it finds is yours to bring to Helen, and none of it is yours to
fill in.** An envelope arrives from a session that had the page in frame and
this repository nowhere, so what is missing is exactly what needs the corpus --
and what is `QQ` is `QQ` by her standing rulings, not by omission.

## Procedure

1. **Fetch the drafts repo before anything you will act on.**

       sh scripts/git-fetch-agent.sh _food_drafts helen-triages-food-private
       sh scripts/git-fetch-agent.sh _cocktail_drafts helen-triages-cocktails-private

   That leaves the clone detached on the fetched `main`. Mid-work on a branch,
   add `main --keep-head`: it stays on the branch and prints how far behind it
   is, and a non-zero count means the next red test is probably not yours.

2. **Branch in the drafts repo**, never commit to its `main`. A bare `git
   checkout -b` would branch the public repo, so use the wrapper:

       sh scripts/git-drafts.sh _food_drafts checkout -b content/inbox-<YYYY-MM-DD>
       sh scripts/git-drafts.sh _cocktail_drafts checkout -b content/inbox-<YYYY-MM-DD>

3. **Dry run, and read the plan.** The default writes nothing.

       python3 scripts/ingest_inbox.py --site food
       python3 scripts/ingest_inbox.py --site cocktail

   Each envelope prints one of three things: what it would write, why it was
   rejected, or which existing draft it is a probable duplicate of. **A
   rejection is not yours to repair** -- the envelope is Helen's paste of a
   browser's output, so a malformed one is a question for her, and guessing
   what it meant is the invention this whole channel exists to prevent.

   `--issue N` works one envelope. `--from-file PATH` parses a local file, or
   every `.md` in a folder, instead of fetching. A file may be a whole batch:
   it is split at its `# ingest: <slug>` headings, the index above the first is
   dropped, and each envelope is reported as `<file> <slug>`.

4. **Write**: `--write`. Then the finishing pass from `/ingest`, steps 2 to 8,
   in its order. `ingest.md` has the detail of each; the order is the one the
   scripts need:

   1. **Cocktails: `python3 scripts/resolve_pours.py --apply`.** It types the
      generics an exact dictionary match settles and leaves the rest `QQ`. It
      runs first because the moods read the generics it writes.
   2. **Cocktails: `python3 scripts/derive_cocktail_moods.py --write`.** The
      file arrives with `mood: []`, and
      `test_every_drinks_moods_match_the_derivation` fails until this runs.
   3. **Food, only if the file has no `main_ingredients`:** `python3
      scripts/derive_main_ingredients.py --derive --only <slug>`.
   4. **Cocktails: `python3 scripts/tidy_drafts.py --site cocktails --only
      order --apply`.** An envelope can arrive with its keys in another order,
      and `test_a_draft_drinks_keys_are_in_page_order` fails until this runs.
      Then `/tidy-drafts`, either collection, if the quoting or typography
      needs it. It formats a food `QQ` line and never rewords one.
   5. **`pytest`.** Once, and never two at a time.
   6. **`python3 scripts/ingest_preflight.py`** -- undeclared bottles,
      near-miss garnishes, unstated times, in the same shape a photo batch
      gets.

5. **Bring Helen one page**, built by

       python3 scripts/ingest_review.py --from-file <the same path> --out tmp/review.md

   and put in the drafts PR's description: a table of every recipe's tags,
   star, servings and times as the drafts now stand, for her to answer with
   corrections only, then every hand-back bullet no standing ruling settles.
   A bullet a ruling settles (`ingest_inbox.FOLDS`, and per source
   `_data/food/sources.yml`) is counted, not asked; a bullet that asks
   something is never folded. Add every rejection, probable duplicate and
   Sazerac case, plus whatever the pre-flight found. **Treat each as a tier 3
   question**: ask, do not fill in. Not a question at a time -- arriving in a
   trickle is the failure the pre-flight was built to fix. **When she rules
   on something that will recur for one book or magazine, add it to
   `sources.yml`** and run `python3 scripts/build_ingest_vocab.py --write`:
   the next web Claude reads it, and the next batch never asks.

6. **Run `python3 scripts/verify.py` before anything is pushed, every time.**
   Nothing else runs the drafts checks (`PIPELINE.md` §3), and an inbox pass
   writes brand-new files from text Helen pasted off her phone, which is the
   likeliest source of a schema surprise in the whole pipeline.

7. **Commit in the drafts repo**, one commit per envelope, with a bare
   `Fixes #N` for the issue it came from. That trailer is valid here and
   nowhere else in this workflow: the issue and the commit are in the same
   private repo. **The trailer is what closes the issue** -- the script never
   closes one, and neither do you by API. Name the issues before pushing, while
   the message can still be rewritten. Check the branch in a call of its own
   first:

       sh scripts/git-drafts.sh _cocktail_drafts branch --show-current
       sh scripts/git-drafts.sh _cocktail_drafts add -- <paths>
       sh scripts/git-drafts.sh _cocktail_drafts commit -F tmp/commit-msg.txt

   Then push, per `CLAUDE.md`, with no ask:

       sh scripts/git-push-agent.sh <branch>:<branch> helen-triages-cocktails-private _cocktail_drafts

8. **Report what is still `QQ` and why**, as `/ingest` does.

## What this never does

This list is about the script, `scripts/ingest_inbox.py`. The session running
it does commit and push (steps 7 and 8), and the finishing pass does type what
a dictionary settles (step 4); everything else here binds the session too.

- **Repair an envelope.** A rejection goes back to Helen. `--comment` posts the
  reason on the issue if she wants it there; it does nothing with
  `--from-file`.
- **Overwrite a file, or write one twice.** A taken slug gains `-2`; a matching
  fingerprint is reported and not written at all.
- **Commit, push, or close an issue.** The session commits and pushes; the
  `Fixes #N` trailer closes. Nobody closes one by API, and nobody commits on a
  `main`.
- **Fill in a `generic`, a `suggestion`, a `tagline`, a glass or a
  `star_ingredient`**, rewrite the prose, re-derive `main_ingredients`, or
  "improve" a `QQ Claude` line. The script writes the envelope's values as they
  came. Afterwards `resolve_pours.py` types only the generics and suggestions
  an exact match settles, and the session types none by hand: a rewrite pass
  has already happened, and redoing it burns Helen's review twice.
- **Touch `_food_recipes/` or `_cocktail_recipes/`.** The inbox lands in drafts,
  always.
- **Merge two recipes that share a name.** They are two recipes until she says
  otherwise; the script writes the second under its own slug and says so.

## Traps

- **A batch pasted into an issue is cut off at GitHub's 65,536-character
  body limit**, and the cut lands after a marker line, so the last envelope
  rejects as "0 fenced code blocks". Split batches end that way, and the
  envelope is in no issue at all: ask Helen to paste it again.
- **A batch in a PUBLIC-repo issue** is source text that may be copyright
  (INGEST_INBOX_DESIGN.md §8). Save the bodies to `tmp/` with `sh
  scripts/gh-read.sh repos/DeckOfPandas/helen-triages/issues/<N> --jq .body >
  tmp/<dir>/<N>.md`, run `--from-file` over the folder, and tell Helen first:
  only she can delete an issue. A private-repo `Fixes #N` does not reach it.
- **A probable duplicate is a report, not a verdict.** The fingerprint compares
  formulas, so a match is strong evidence and still hers to confirm -- an
  identical drink transcribed from a second book is a citation worth having.
- **A missing drafts repo is a refusal, not an empty run.** Both private repos
  are gitignored and absent in a fresh worktree; the script exits non-zero
  saying so rather than reporting a clean inbox. Clone it: `sh
  scripts/git-clone-agent.sh helen-triages-cocktails-private _cocktail_drafts`.
- **The version marker is the handshake.** If the script rejects everything for
  its version, the standalone documents have moved ahead of it. That is a code
  change here, never a hand-edit of the envelope.
