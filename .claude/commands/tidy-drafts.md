---
description: Tidy the mechanical half of _food_drafts/ and _cocktail_drafts/ -- quoting, dashes, typography, accents, the #429 meta block, a size word stranded in item: (#577), tin-and-pan incidentals (#1356), a cocktail's key order (#1213), a food draft's meta under its title, and Title Case (#1089) -- and report everything that needs Helen instead.
---

Helen has asked for a drafts tidy-up. Run `scripts/tidy_drafts.py`, which is the
engine; this file is the procedure around it.

**Read `scripts/tidy_drafts.py`'s module docstring before the first run.** It
states what the script will not do and why, and that list is the load-bearing
half of this command. Each rule's exact behaviour is in the docstring of its
`fix_*` function; this file does not restate them.

## The boundary, in one line

The script fixes **formatting**. It never resolves a **judgement**. If a fix
would need Helen's source material, her palate or her voice, it is reported and
left alone — which milk, which flour, which mustard, whether an oven figure is
the fan one, whether a note's first word is a proper noun.

A draft's title disagreeing with its filename is neither, and is not reported:
the title is still the source's title while the slug is already the dish.

It never rewords a `QQ` line: that is the source's own wording awaiting
Helen's rewrite. **On food, `dashes`, `typography`, `units` and `accents` do
format one**, so she rewrites from text already in house style; nothing else
reaches it, and on a drink nothing does (MANUAL §5). A `QQ Claude` line is ours
and is tidied like any other prose.

It never touches `source:` (a citation is spelled as the publication spells
itself), never renames a file, and never runs a YAML dumper over a draft.

## The rules

`python3 scripts/tidy_drafts.py` covers `_food_drafts/` and `_cocktail_drafts/`,
each recursively, so the numbered folders are in. `--site food` or `--site
cocktails` does one alone; an absent private repo is announced and skipped, and
only both absent is a refusal.

`--only` takes a comma-separated subset of these names (`RULE_NAMES` in the
script; `--help` prints them):

| rule | collections | what it does |
|---|---|---|
| `notes` | both | `notes: []` becomes one empty `{label: "", text: ""}` pair; a note with text and an empty label is labelled `"QQ"`. Never changes a note's `text` |
| `quoting` | both | quotes the scalar string fields; on food also the `main_ingredients`/`tags` lists and every group's `- name:` |
| `dashes` | both | `3-4` → `3–4` |
| `typography` | both | `--` → em dash, `->` → → |
| `units` | both | `15ml` → `15 ml`, for `kg g ml cl cm mm oz tsp tbsp`; never a temperature, which wants a degree sign and is reported |
| `accents` | both | the words in `_data/accented_words.yml` |
| `meta` | food | the `meta:` block's keys, order and unquoted booleans; it never invents a flag |
| `size` | food | `amount: "2"` / `item: "large onions"` → `amount: "2 large"` / `item: "onions"`, only where `test_size_word_is_with_the_count_not_the_item` would fire |
| `incidentals` | food | a fat or flour only for the tin or the pan (`"butter, for greasing"`) gains `incidental: true`; `", plus extra for the tin"` and its kin are trimmed off a real line; deep-frying oil loses its amount and reads `"<oil>, for deep frying"`. All by `incidental_verdict` in `tests/test_taxonomy.py`, over the words in `_data/food/incidentals.yml` (#1356). A `QQ` line gains the flag but is never trimmed |
| `titles` | cocktails | Title Case by the suite's `title_cased`: it only raises a letter, and leaves anything in brackets as written |
| `order` | both | a cocktail's top-level keys into `TOP_LEVEL_KEYS_IN_ORDER` (`tests/test_cocktails.py`); a food draft's `meta:` block to directly under `title:`, so the flags are the first thing Helen sees. Moves whole blocks and edits no line |

Two of them are run alone, each as its own commit in the drafts repo:

- **`size`** rewrites two fields per hit, and the diff of its one commit is
  Helen's review. It refuses and names an item whose remainder starts `or`
  (`1` / `large or 2 small onions` holds a second count) and `baby`, which is a
  kind as often as a size; those appear under `SKIPPED`.
- **`order`** moves every block in a file, so its diff cannot be reviewed by
  eye. The evidence is the fixer's own checks (the same lines, the same parsed
  data, the declared order; it raises instead of writing if one fails) and, if
  you want more, a run on a copy first: `--drafts-dir <copy> --site cocktails
  --only order --apply`. It refuses and names an undeclared key, a key written
  twice, and a column-0 comment. Drafts only: never reorder a file in
  `_cocktail_recipes/` or `_food_recipes/`.

## A cocktail's boundary is narrower

A cocktail recipe's front matter is mostly not prose: most of its lines are a
closed vocabulary, somebody else's words, or a number. So on a cocktail every
rule except `notes` and `order` reaches **only Helen's own writing** — `title`,
`tagline`, `snippet`, `to_serve`, a `notes` entry's `label` and `text`, an ingredient's
`note` — and fixes there only what `tests/test_cocktails.py` already demands.

What it will not touch on a cocktail, and why each is a decision rather than an
oversight:

- **A `QQ` line**, by the suite's predicate (`conftest.checkable_text`). On a
  cocktail the marker sits behind a key — `tagline: "QQ"`, `text: "QQ - ..."`.
- **`suggestion`, `source`, `source_url`** — somebody else's words
  (`VERBATIM_KEYS` in `tests/test_cocktails.py`). The suite blanks them before
  it looks, so it is not asking for them either. The script blanks
  those lines before any fixer sees them, the quoting fixer included.
- **`glass`, `garnish`, `mood`, `generic`, `character`** — closed vocabularies
  declared in `_data/cocktails/` and enforced against those declarations. An
  accent or a dash written into one is a change to the vocabulary, which is a
  question for `_data/`.
- **A `method` step** — `methods.yml` holds the canonical steps and a
  `proposals` mechanism for changing one. Editing a step in a cocktail file
  quietly de-canonicalises it.
- **An `amount`.** A cocktail can carry `amount: "Top (30-45) ml"` beside a `QQ`
  note quoting that string back verbatim; en-dashing the amount would
  desynchronise the note from the value it describes. The suite checks amounts,
  so a range in one is **reported** and left for Helen.
- **A non-house spelling** (`demarara` → `demerara`) or a temperature missing
  its `°`. Reported, never fixed, on either collection: a spelling is a word,
  not a character.

## Procedure

1. **Report first, always.** `python3 scripts/tidy_drafts.py` writes nothing.
   Read the three sections it prints: what it would change, what it is reporting
   and never touching, and what it deliberately did not look at.

2. **Check whether the drafts repo is clean** (`sh scripts/git-drafts.sh
   _food_drafts status --short`). `_food_drafts/`
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

   `scripts/git-drafts.sh` is how every local git command in a drafts repo is
   run; its header lists the verbs it accepts. It refuses a commit on the
   drafts repo's `main`.

4. **Apply**: `python3 scripts/tidy_drafts.py --apply`. It refuses on a dirty
   tree unless you pass `--allow-dirty`, and that refusal is deliberate: the
   diff afterwards shows exactly what the script did, and mixed in with Helen's
   own edits it does not.

   Use `--only` with any of
   `notes,quoting,meta,dashes,typography,units,accents,titles,size,incidentals,order` to do
   one class at a time if the full pass is too much to review in one go.

5. **Verify, and not by reading the diff.** Run the suite for the half you
   touched, one run at a time:

       pytest -m food
       pytest -m cocktails

   A green run is the claim. A diff can look entirely plausible over files that
   no longer parse; the front-matter tests are what say so.

6. **Report to Helen**, in this order, before committing:
   - the count of mechanical changes, by class;
   - every **report-only** finding, individually — an instruction left in a
     file for Claude, or a `meta:` flag the script would not invent. These are
     hers to decide;
   - anything the script SKIPPED (it says so inline: a value containing a double
     quote, an unrecognised `meta:` key);
   - what is still red in `pytest` and why, so a judgement backlog is not
     mistaken for something the tidy pass missed.

7. **Commit in the drafts repo**, one commit per class if the pass was large,
   checking the branch in a call of its own first:

       sh scripts/git-drafts.sh _food_drafts branch --show-current
       sh scripts/git-drafts.sh _food_drafts add -- .
       sh scripts/git-drafts.sh _food_drafts commit -F tmp/commit-msg.txt

   Tag an issue as `Towards DeckOfPandas/helen-triages#N` — a bare `#N`
   resolves against the drafts repo's own empty tracker, and a cross-repo
   trailer from a private repo does not close or even cross-reference the
   public issue, so treat closing as a separate deliberate step.

8. **Run `python3 scripts/verify.py` before the push, every time.** Nothing
   else runs the drafts checks (`PIPELINE.md` §3), and a tidy pass touches many
   files at once, which is exactly when this matters most.

9. **Push, per `CLAUDE.md`.** No ask. In a private drafts repo a small tidy
   may be pushed straight to its `main`; a pass with a bigger footprint is a
   branch and a PR. Committing on `main` is forbidden in every repo.

## What this does not cover

- **Everything on a cocktail that is not Helen's own prose** — an `amount`, a
  method step, a vocabulary value or a `suggestion`. The section above lists
  them with a reason each; the script's report names the ones the cocktails
  suite will still fail on, so a decline never looks like a miss.
- **A size word the `size` rule refused** — no count to attach it to, an `or`
  remainder, or `baby`. The report names them.
- **A draft with no `meta.awaiting_fix`** (the report names them). The flag
  fails closed, so writing `false` in asserts the recipe is fit to publish.
  That is Helen's to say, not a formatting fix.

## If you are tempted to widen it

`tests/test_drafts.py`'s `NOT_FOR_DRAFTS` is the registry of every recipe rule
not applied to drafts, with a reason each. Read the reason before deciding a
rule is mechanical: a rule that looks like a formatting gap can be one whose
fix would invent content.

On the cocktails side the equivalent question is **whose words is this?** The three
answers are Helen's (fix it), somebody else's (`VERBATIM_KEYS`, and a `QQ` line
anywhere), and `_data/cocktails/`'s (a closed vocabulary, or a canonical method
step — change the declaration, then the files, never one file). A rule that
cannot be sorted into one of those three is not a formatting rule.
`model_instructions/PUBLISHING_A_COCKTAIL.md` step 2 remains the human pass over a
cocktail, and this script does not replace it.
