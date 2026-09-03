---
description: Work the `ingest` issue inbox on a private drafts repo -- parse each envelope Helen pasted in from her phone, write the files it earns, and hand her ONE list of everything that needs her.
---

Helen has put recipes into `ingest` issues from away from her desk.
`scripts/ingest_inbox.py` is the engine; this file is the procedure around it.
Same split as `/tidy-drafts` and `/ingest`: the script reports and writes
nothing but files, the doc decides.

**Read the script's module docstring before the first run**, and
`model_instructions/INGEST_INBOX_DESIGN.md` §6 for the envelope. This command
does not restate either -- two copies of a spec drift.

## The boundary, in one line

The script does the MECHANICAL half: parse, slug, deduplicate, write. **Every
judgement it finds is yours to bring to Helen, and none of it is yours to
fill in.** An envelope arrives from a session that had the page in frame and
this repository nowhere, so what is missing is exactly what needs the corpus --
and what is `QQ` is `QQ` by her standing rulings, not by omission.

## Procedure

1. **Fetch the drafts repo before anything you will act on.**

       cd _<site>_drafts && git fetch origin && git rev-list --count HEAD..origin/main

   A non-zero answer means the next red test is probably not yours.

2. **Branch in the drafts repo**, never commit to its `main`:

       git checkout -b content/inbox-<YYYY-MM-DD>

3. **Dry run, and read the plan.** The default writes nothing.

       python3 scripts/ingest_inbox.py --site food
       python3 scripts/ingest_inbox.py --site cocktail

   Each envelope prints one of three things: what it would write, why it was
   rejected, or which existing draft it is a probable duplicate of. **A
   rejection is not yours to repair** -- the envelope is Helen's paste of a
   browser's output, so a malformed one is a question for her, and guessing
   what it meant is the invention this whole channel exists to prevent.

   `--issue N` works one envelope. `--from-file PATH` parses a local file
   instead of fetching, which is what a paste from the clipboard uses.

4. **Write**: `--write`. Then, per file, **the finishing pass from `/ingest`,
   in its order**:

   1. **COCKTAILS: `python3 scripts/derive_cocktail_moods.py --write`.** The
      file arrives with `mood: []` and **the suite fails until this runs** --
      `test_every_drinks_moods_match_the_derivation`, expected, not a fault in
      the file.
   2. **`pytest`.** Once, and never two sessions at a time.
   3. **FOOD: `/tidy-drafts`**, if the quoting or typography needs it. It never
      touches a `QQ` line.
   4. **`python3 scripts/ingest_preflight.py`** -- undeclared bottles,
      near-miss garnishes, unstated times, in the same shape a photo batch
      gets.

5. **Bring Helen ONE list.** Every rejection, every probable duplicate, every
   Sazerac case, and every hand-back bullet from every envelope, grouped by
   file, plus whatever the pre-flight found. **Treat each as a TIER 3
   question**: ask, do not fill in. Not a question at a time -- arriving in a
   trickle is the failure the pre-flight was built to fix.

6. **Commit in the drafts repo**, one commit per envelope, with a bare
   `Fixes #N` for the issue it came from. That trailer is valid here and
   nowhere else in this workflow: the issue and the commit are in the same
   private repo, so CLAUDE.md's cross-repo trap does not apply. **The trailer
   is what closes the issue** -- the script never closes one, and neither do
   you by API. Name the issues before pushing, while the message can still be
   rewritten. Push on her confirmation.

7. **Report what is still `QQ` and why**, as `/ingest` does.

## What this never does

- **Repair an envelope.** A rejection goes back to Helen. `--comment` posts the
  reason on the issue if she wants it there; it is a no-op with `--from-file`.
- **Overwrite a file, or write one twice.** A taken slug gains `-2`; a matching
  fingerprint is reported and not written at all.
- **Close an issue by API**, commit, push, or touch `main` in either repo.
- **Fill in a `generic`, a `suggestion`, a `tagline`, a glass or a
  `star_ingredient`**, rewrite the prose, re-derive `main_ingredients`, or
  "improve" a `QQ Claude` line. A rewrite pass has already happened and redoing
  it burns Helen's review twice.
- **Touch `_food_recipes/` or `_cocktail_recipes/`.** The inbox lands in drafts,
  always.
- **Merge two recipes that share a name.** They are two recipes until she says
  otherwise; the script writes the second under its own slug and says so.

## Traps

- **A probable duplicate is a REPORT, not a verdict.** The fingerprint compares
  formulas, so a match is strong evidence and still hers to confirm -- an
  identical drink transcribed from a second book is a citation worth having.
- **A missing drafts repo is a refusal, not an empty run.** Both private repos
  are gitignored and absent in a worktree; the script exits non-zero saying so
  rather than reporting a clean inbox.
- **The version marker is the handshake.** If the script rejects everything for
  its version, the standalone documents have moved ahead of it. That is a code
  change here, never a hand-edit of the envelope.
