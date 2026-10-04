---
description: Tidy the mechanical half of _food_drafts/ and _cocktail_drafts/ -- quoting, dashes, typography, accents, the #429 meta block, a size word stranded in item: (#577), a cocktail's key order (#1213) -- and report everything that needs Helen instead.
---

Helen has asked for a drafts tidy-up. Run `scripts/tidy_drafts.py`, which is the
engine; this file is the procedure around it.

**Read `scripts/tidy_drafts.py`'s module docstring before the first run.** It
states what the script will not do and why, and that list is the load-bearing
half of this command.

## The boundary, in one line

The script fixes **formatting**. It never resolves a **judgement**. If a fix
would need Helen's source material, her palate or her voice, it is reported and
left alone — which milk, which flour, which mustard, whether an oven figure is
the fan one, whether a note's first word is a proper noun.

A title disagreeing with its filename is neither: it is **not a finding at all**
on a draft, and the script stopped reporting it on 2026-09-01. A draft's title
is still the source's title while the slug is already the dish, so
`chocolate-fudge-cake` titled "Cassie's Favourite Chocolate Fudge Cake" is the
ingest doing the right thing. The recipe-side test is untouched.

It never touches a `QQ` line. That is the source's own wording awaiting Helen's
rewrite, and correcting its dash or its degree sign is editing someone else's
words (MANUAL §5, issue #426). Two thirds of the corpus-wide en-dash hits are
inside `QQ` text, so this is not a technicality.

**The `notes` rule (#1258, 2026-10-02) is the one that writes a line Helen did
not.** On both collections, `--only notes` turns an empty `notes: []` into one
empty `{label: "", text: ""}` pair, so she never has to recall the YAML shape,
and labels a note that has text and an empty label `"QQ"`, so imported text
cannot publish unread. It never changes a note's `text`, and never touches a
note that already has a label.

## Both collections, since 2026-09-05

`python3 scripts/tidy_drafts.py` covers `_food_drafts/` **and**
`_cocktail_drafts/`, each recursively, so `to-promote/` is in. Helen asked for
the widening in those words: *"Widen please — cocktail drafts passing will save
me a lot of time."* `--site food` or `--site cocktails` does one alone; an
absent private repo is announced and skipped, and only BOTH absent is a refusal.

**The cocktails boundary is much narrower than food's, because a cocktail
recipe's front matter is mostly not prose.** What the pass does on a cocktail
recipe:

| | |
|---|---|
| **fixes** | an unquoted `title`/`tagline`/`source`/`source_url`/`to_serve`; `--` → em dash; `->` → →; `3-4` → `3–4`; `15ml` → `15 ml`; accents from `_data/accented_words.yml` |
| **but only in** | `title`, `tagline`, `to_serve`, a `notes` entry's `label`/`text`, an ingredient's `note` — Helen's own writing and nothing else |

What it will **not** touch on a cocktail, and why each one is a decision rather
than an oversight:

- **A `QQ` line**, by the *suite's* predicate rather than the food one. On a
  cocktail the marker sits behind a key — `tagline: "QQ"`, `text: "QQ - ..."` — and
  the food pattern, which allows only a list dash and a quote in front of it,
  matches none of those. The script asks `conftest.checkable_text`.
- **`item`, `suggestion`, `source`, `source_url`** — somebody else's words
  (`test_cocktails.VERBATIM_KEYS`). The cocktails suite blanks them before it
  looks, so it is not asking for them either.
- **`glass`, `garnish`, `mood`, `generic`, `character`** — closed vocabularies
  declared in `_data/cocktails/` and enforced against those declarations. An
  accent or a dash written into one is a change to the vocabulary, which is a
  question for `_data/`.
- **A `method` step** — `methods.yml` holds the canonical steps and a
  `proposals` mechanism for changing one. Editing a step in a cocktail file
  quietly de-canonicalises it.
- **An `amount`** — and this one is a *recorded harm*, not a principle.
  anitas-attitude-adjuster said `amount: "Top (30-45) ml"` with a `QQ` note
  quoting that string back verbatim; en-dashing the amount would have
  desynchronised the note from the value it describes. The cocktails suite checks
  amounts and is right to — they render — so a range in one is **reported** in
  the second section and left for Helen.
- **A non-house spelling** (`demarara` → `demerara`) or a temperature missing
  its `°`. Reported, never auto-fixed, on either collection: a spelling is a
  word, not a character.

Food's own three rules stay food's: the `main_ingredients`/`tags` flow quoting,
the #429 `meta:` migration and the #577 `size` rule run on `_food_drafts/` and
nowhere else. A cocktail's `meta:` is five keys in its own order and
nobody asked to migrate it; its `amount` is never edited and its `item` was
retired.

## The unit space, since 2026-10-01

`15ml` → `15 ml`. Helen: *"Please add unit spaces (15ml -> 15 ml) as a
mechanical fix to perform at ingest, and check when I ask you to check
drafts."*

**Measured before it was written**, which is what makes it a fix and not a
preference: across both food collections `amount:` reads `40 g` **1,461** times
and `40g` **13** times. The spaced form is the house form by a factor of 112.

The units are `kg`, `g`, `ml`, `cl`, `cm`, `mm`, `oz`, `tsp`, `tbsp`.

**`units` IS IN BOTH RULE TABLES AND MEANS TWO DIFFERENT THINGS.** On **food** it
runs over the whole file, so an `amount: "40g"` and an `item: "…3cm chunks"` are
both fixed. On a **drink** it is wrapped in `only_where_editable`, so it reaches
Helen's own prose and **a drink's `amount` is never touched** — the recorded harm
this file already describes, where editing an amount desynchronised a `QQ` note
quoting it back. A drink cannot carry `15ml` in an amount anyway: `measures:`
declares the unit and not the glue, so it would fail
`test_every_amount_is_readable_as_a_quantity` first.

**Three things deliberately out of the pattern**, each because including them
would be silent rather than wrong:

- **a bare `l`** — never measured in either collection, and `1ltr` is a real
  string this would mangle;
- **`mins`** — a duration is not a measure and reads fine closed up nowhere in
  the corpus;
- **anything temperature-shaped.** `180C` wants a **degree sign**, which this
  script reports and never fixes. Spacing it to `180 C` would half-fix it and
  make the real fault harder to see.

`kg` matches **before** `g` in the alternation. A short-first list turns `2kg`
into `2k g`, which parses fine and reads almost right — the only failure in this
rule that produces a plausible wrong answer, and the one its test pins.

## The size word, since 2026-09-24 (#577, Helen's option 1)

`amount: "2"` / `item: "large onions, chopped"` becomes `amount: "2 large"` /
`item: "onions, chopped"` — the recipe rule
`test_size_word_is_with_the_count_not_the_item`, whose regex the script imports.
It fires **only where that test would**: a bare integer count beside an item
starting `small`/`medium`/`large`/`extra large`. A weight (`400 g large open
mushrooms`), a fraction (`½ small bunch of chives`) and a `small handful of
parsley` with no amount at all are left exactly as they are; the last is
**reported**, so a survivor is not mistaken for a miss.

It **refuses and names** the shapes that needed an eye when #149 was fixed by
hand: an item whose remainder starts `or` (`1` / `large or 2 small onions` holds
a second count), and `baby`, which is a kind as often as a size (`baby gem`,
DECISIONS §6). Those stay for Helen, in the report, under `SKIPPED`.

Helen's ruling was *"script it with a hand-review of the diff, one commit,
before promotion"* — so `--only size` is run as its own commit in the drafts
repo and the diff of that commit is the review.

## Key order, cocktails only (#1213)

Helen: *"yaml fields should be rewritten in the order they appear on the page,
top to bottom."* Drafts and new ingests; *"Do not apply this retrospectively to
published recipes."* `--only order` re-deals a cocktail draft's top-level keys
into `TOP_LEVEL_KEYS_IN_ORDER` (`tests/test_cocktails.py`, derived from
`_layouts/cocktail.html` by a test): `title`, `tagline`, `glass`, `garnish`,
`meta`, `mood`, `ingredients`, `serve`, `serves`, `method`, `to_serve`,
`notes`, `source`, `source_url`.

**It moves whole blocks and edits no line**, so it is the one cocktail rule
that is not confined to Helen's prose and does not need to be: an `amount`, a
method step and a `QQ` line each travel inside their block exactly as written.
It checks its own output before returning it — the same lines, the same parsed
data, the declared order — and raises instead of writing if any fails.

**The diff of a reorder cannot be reviewed by eye**: every moved block shows as
a deletion and an insertion. The evidence is the fixer's own three checks, and
a run on a COPY first (`--drafts-dir <copy> --site cocktails --only order
--apply`) with both sides parsed and compared — the 2026-08-29 lesson — never
a read of the diff.

It **refuses and names** an undeclared key, a key written twice, and a
column-0 comment, which belongs to no block. As with `size`, run it as its own
commit in the drafts repo. **The first full pass ran on 2026-10-04, all 62
drafts, and is drafts schema 2**; `test_a_draft_drinks_keys_are_in_page_order`
keeps it that way, so a draft that arrives or is hand-edited out of order
fails until this rule is run again.

`tests/test_tidy_drafts.py` is the proof, on a fixture cocktail under `tmp/` and
never on Helen's files: it asserts the whole output byte for byte, so "fixed the
six faults" cannot pass while something also happened to the other thirty lines.

## Procedure

1. **Report first, always.** `python3 scripts/tidy_drafts.py` writes nothing.
   Read the three sections it prints: what it would change, what it is reporting
   and never touching, and what it deliberately did not look at.

2. **Check whether the drafts repo is clean.** `_food_drafts/`
   (`helen-triages-food-private`) and `_cocktail_drafts/`
   (`helen-triages-cocktails-private`) are separate private repos with their own
   `main`, and the CLAUDE.md branch rules apply to each exactly as they do here.
   Helen edits drafts constantly, so expect uncommitted work and **do not stash,
   commit or discard it** — ask her. `--apply` refuses on either dirty tree.

   **If she is proofreading, do not run `--apply` over that collection at all.**
   `meta.proofread: true` means she has read what is in the file; a tidy pass
   afterwards is a change she has not read, and while she is mid-pass the file
   she is looking at may not be the file on disk. Report, hand her the list,
   wait.

3. **Branch in the drafts repo**, never commit to its `main`:

       sh scripts/git-drafts.sh _food_drafts checkout -b tidy/<what-this-pass-is>
       sh scripts/git-drafts.sh _cocktail_drafts checkout -b tidy/<what-this-pass-is>

   `scripts/git-drafts.sh` is how every git command in a drafts repo is run —
   `status`, `diff`, `log`, `show`, `branch --show-current`, `checkout -b`,
   `add --` and `commit -F tmp/<file>`. A leading `cd` and `git -C` are both
   refused by the hook, and the wrapper is allow-listed, so it does not ask
   Helen. It refuses a commit on the drafts repo's `main`.

4. **Apply**: `python3 scripts/tidy_drafts.py --apply`. It refuses on a dirty
   tree unless you pass `--allow-dirty`, and that refusal is deliberate: the
   whole safety story is that the diff afterwards shows exactly what the script
   did, and mixed in with Helen's own edits it does not.

   Use `--only quoting,meta,dashes,typography,units,accents,size,order` to do
   one class at a time if the full pass is too much to review in one go. `size`
   rewrites two fields per hit and is the one Helen asked to review as its own
   commit; `order` (cocktails) moves every block in a file and is its own
   commit for the same reason.

5. **Verify, and not by reading the diff.** Run the suite for the half you
   touched:

       pytest -m food
       pytest -m cocktails

   A green run is the claim. If anything in `_food_drafts/` no longer parses,
   the front-matter tests fail loudly — which is how the one real bug in this
   script was found, and it had silently broken 341 of 342 files while the diff
   looked entirely plausible.

6. **Report to Helen**, in this order, before committing:
   - the count of mechanical changes, by class;
   - every **report-only** finding, individually — an instruction left in a
     file for Claude, or a `meta:` flag the script would not invent. These are
     hers to decide;
   - anything the script SKIPPED (it says so inline: a value containing a double
     quote, an unrecognised `meta:` key);
   - what is still red in `pytest` and why, so a judgement backlog is not
     mistaken for something the tidy pass missed.

7. **Commit in the drafts repo**, one commit per class if the pass was large.
   `Towards DeckOfPandas/helen-triages#N` — a bare `#N` resolves against the
   drafts repo's own empty tracker, and a cross-repo trailer from a private repo
   does not close or even cross-reference the public issue, so treat closing as
   a separate deliberate step.

8. **Run `python3 scripts/verify.py` before the push, every time.** It runs the
   drafts checks, and until the private repos get CI of their own (#1194)
   nothing else ever will: CI checks out the public repo alone, and most draft
   checks are parametrised per file, so without a clone they are never CREATED
   rather than skipped — a green run that examined nothing. A tidy pass touches
   many files at once, which is exactly when this matters most.

9. **Push per `CLAUDE.md`, which changed on 2026-08-29 and this line did not.**
   Pushing `main` in the two PRIVATE drafts repos is fine and needs no ask —
   nothing there triggers a build, and a commit sitting unpushed on one disk is
   the real risk. Everything else is unchanged: `helen-triages` itself is never
   pushed without her explicit confirmation, and COMMITTING to `main` is still
   forbidden in every repo, hook-enforced.

## What this does not cover

- **Everything on a cocktail that is not Helen's own prose** — an `amount`, a
  method step, a vocabulary value, an `item` or a `suggestion`. The section
  above lists them with a reason each; the script's report names the ones the
  cocktails suite will still fail on, so a decline never looks like a miss.
- **A size word the `size` rule refused** — no count to attach it to, an `or`
  remainder, or `baby`. The section above says why each is Helen's; the
  report names them.
- **A draft with no `meta.awaiting_fix`** (the report names them). The flag fails closed, so
  writing `false` in asserts the recipe is fit to publish. That is Helen's to
  say, not a formatting fix.

## If you are tempted to widen it

`tests/test_drafts.py`'s `NOT_FOR_DRAFTS` is the registry of every recipe rule
not applied to drafts, with a measured count and a reason each. Read the reason
before deciding a rule is mechanical. One entry was mislabelled as a mechanical
gap until 2026-08-29 and would have had a tidy pass inventing 256 note labels
that are meant not to exist.

On the cocktails side the equivalent question is **whose words is this?** The three
answers are Helen's (fix it), somebody else's (`VERBATIM_KEYS`, and a `QQ` line
anywhere), and `_data/cocktails/`'s (a closed vocabulary, or a canonical method
step — change the declaration, then the files, never one file). A rule that
cannot be sorted into one of those three is not a formatting rule.
`model_instructions/PUBLISHING_A_COCKTAIL.md` step 2 remains the human pass over a
cocktail, and this script does not replace it.
