# Publishing a drink — the steps, who does each, and what the words mean

Written 2026-09-04, on the day the first sixteen drinks went through it, for
Helen to check and for the next session to follow. It is short on purpose.
**HANDOVER §9.1.1 has the gate's mechanics and §4.0 says what the flags MEAN;
`.claude/commands/ingest.md` is how a drink gets INTO the drafts and where the
mechanical/non-mechanical boundary is stated in full.** This is the procedure
that carries a drink from there to the public repo, and it is linked from
HANDOVER §11.

## The one working copy

For a batch in progress there is **one** working copy of the private drinks
repo: the clone inside the coordinating Claude's worktree, on a branch named
for the batch, served on a known port (today: **4004**, branch
`content/first-batch-to-promote`). Helen edits there, Claude commits and
pushes there, and the dev server builds from there. Helen's own local clone
is not used while a batch is open — it is where promotion happens afterwards
(step 6), from `main`, after the branch is merged.

Two copies is how the first batch got tangled: sixteen files sat only on one
disk for an evening. One copy, always pushed, is the rule.

## The steps

1. **Helen rewrites** a drink — tagline, notes, bottles, anything — and moves
   it into `_cocktail_drafts/to-promote/`. The move is the signal; nothing
   else is needed. She tells Claude when a round of moves is done, because
   Claude will be editing the same files next.
2. **Claude runs the mechanical pass** over everything in `to-promote/`: flips
   `rewritten: true` (Helen's standing instruction, for files in that folder
   only — it is the ONE place an agent may write that flag, and
   `ingest.md`'s TIER 3 names the same exception), runs the suite, fixes what
   the suite names — spellings the vocabularies already declare, a missing key,
   a hyphen that should be an en dash, a house name where a bottle belongs, an
   alias where the canonical name belongs, an `item` that must go — and never
   touches a tagline, a note's words, a method's words or an amount. Commits and
   pushes. **The full boundary is in `ingest.md` under "Fixing a draft the
   suite is complaining about"; the two say the same thing on purpose.**
3. **Claude lists the non-mechanical things**, one line each, and Helen rules
   on them. Each ruling is written into the vocabularies, the handover and
   the ingest documents the same day, so it is never asked twice.
4. **Claude says "final: <slugs>".** That word means: the suite is green over
   those drinks, every open ruling is applied, and Claude will not touch
   those files again except to flip a flag Helen asks for or to open an
   `awaiting_fix` round. **Until Helen sees that word, the served pages are
   work in progress and not for proofreading.** (This is the step that was
   missing on the first day.)
5. **Helen proofreads** by reading each drink's built page on the dev server —
   `/cocktails/drafts/to-promote/<slug>/` — and flips `proofread: true` in
   the file, or tells Claude the slugs and Claude flips them on her word.
   Reading the served page *is* the proofread; the flag says "I read this
   rendered and it is what I want". Claude commits, pushes, and Helen merges
   the branch on GitHub.
   - If a small thing is wrong: `awaiting_fix: true` in a commit that says
     what; fix between them; Helen re-reads (the whole page — drinks are
     short); flag back.
   - Claude does a final read-only review after the proofread; sometimes Helen
     does too.
6. **Helen promotes**, herself, always, unless she explicitly asks Claude to:
   in her own checkouts, copy the proofread drink into `_cocktail_recipes/`
   in the public repo and commit; delete it from the private repo and commit.
   The public commit deploys.

## What the flags mean, in one line each

- `rewritten: true` — the words are Helen's. Only she claims it; the move into
  `to-promote/` is how she claims it for a batch.
- `awaiting_fix: true` — one thing is ticketed; she has read it; it will not
  publish until the flag is false again.
- `proofread: true` — she read the rendered page. Any agent edit after that
  sets it false again in the same commit (issue #367), which takes the drink
  off the live site until she reads it again. That is the point.

## What "promotion-ready" means for the data

In `to-promote/` and in `_cocktail_recipes/` a drink is in its published
tense: every `suggestion` is a bottle's canonical name (aliases are for
reading drafts, never for a published file), no ingredient carries `item`
(the transcription field lives in drafts only), and every generic is a
declared one. Two tests in `tests/test_cocktails.py` hold that, so the
mechanical pass cannot forget it.

## Where the rulings live

- Bottles and their aliases, and the "a house is not a bottle" rule:
  `_data/cocktails/bottles.yml`, HANDOVER §9.3.2.
- Generics, syrups, honey water, the whole-fruit units: `_data/cocktails/ingredients.yml`.
- Method steps, ice, the rim, the automatic twist step: `_data/cocktails/methods.yml`.
- The ingest rules a session with no repo can use: `INGEST_ONE_COCKTAIL.md`.
  Its vocabulary blocks are generated — `scripts/build_ingest_vocab.py --write`
  after any ruling that changes `_data/`, never a hand edit.
- The in-repo procedure: `.claude/commands/ingest.md`.
- The flags' meaning and the gate: HANDOVER §4.0 and §9.1.1.
- The one-working-copy rule, restated where a worktree is set up: HANDOVER §9.1
  and §11.0.1.
