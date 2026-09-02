# INGEST INBOX — design for ingesting recipes through a Claude with no repository

Written by Fable 5.1, 2026-09-02, as workstream 5 of that day's architecture
audit. **This is a design, not an implementation.** Nothing described here
exists yet unless the section says "exists today". An Opus session implements
it in the two PRs at the end; the decisions in §9 are Helen's and block the
parts that name them.

Every path and line number was checked at commit 8191230. Re-check before
editing (HANDOVER §11.2).

---

## 1. What Helen asked for

> "How to enable a Claude web to ingest recipes for me in a useful way."

She finds recipes away from her desk: a photograph of a book page, a
screenshot, a URL, pasted text. She wants to hand that to claude.ai (or the
Claude app) and have the result reach `_food_drafts/` or `_cocktail_drafts/`
with as little of her own typing as possible, and without lowering the bar the
local `/ingest` procedure holds.

## 2. What exists today, and it is more than the audit first assumed

**The repo-less path already exists.** `.claude/commands/ingest.md` has a
section "A FILE THAT ARRIVES FROM A REPO-LESS SESSION": Helen pastes
`model_instructions/INGEST_ONE_RECIPE.md` or `INGEST_ONE_COCKTAIL.md` into
claude.ai with the source, gets back one file in a code block plus a "what I
could not know" list, and a local session runs a six-step finishing pass
(save, derive moods for a drink, pytest, `/tidy-drafts` for food, work the
hand-back list as TIER 3 questions, `ingest_preflight.py`).

**The two documents are guarded, in one direction.** `tests/test_standalone_docs.py`
checks that every tag, star, garnish, glass and method step the documents
PRINT is still declared in `_data/`, and that each worked example obeys the
schema. Its header says why the check is one-way: a document that omits a new
garnish under-serves; a document that prints a retired one teaches a shape the
suite rejects, to a reader who cannot run the suite. That asymmetry is right
and this design keeps it.

**The tooling below the documents is already the right shape.**
`scripts/ingest_preflight.py` imports every rule from the test suite and never
writes; `scripts/tidy_drafts.py` fixes the mechanical and reports the rest;
`scripts/derive_cocktail_moods.py --write` fills `mood`. The "script reports,
command doc decides" split (HANDOVER §11.0.2) is the pattern the inbox copies.

**The write channel is fixed.** `GH_TOKEN` is issues-only on the three repos
(CLAUDE.md, probed 2026-08-17: file write 403, PR 403). Any Claude holding that
token can raise an issue and nothing else. The private drafts repos have no
build, so nothing an issue carries can publish. Neither constraint is a
problem; together they choose the transport.

## 3. The gaps, precisely

1. **Transport is manual.** The browser session's output reaches the repo by
   Helen copying a code block out of a chat and into a file, then telling a
   local session about it. On a phone that is the step that does not happen.
2. **The documents under-serve, never mislead.** Verified against `_data/` at
   8191230:
   - `INGEST_ONE_COCKTAIL.md` §4 prints 42 garnishes; `garnish.yml` declares
     six more it does not print (`pineapple wedge (cut to resemble a bird's
     plumage)`, `pineapple and brandied cherry`, `passion fruit shell filled
     with overproof rum`, `fruit stick (skewered pineapple cubes and a
     maraschino cherry)`, `3 dashes red creole-style bitters`, `5 drops of
     olive oil`). A reader will "correct" a valid string to a near one.
   - `INGEST_ONE_RECIPE.md` §6 lists ~12 accented words; `_data/accented_words.yml`
     has 45, plus eight explicit **no-accent** words (`chorizo`, `gratin`,
     `julienne`, `vinaigrette`, `dauphinoise`, `mornay`, `confit`, `echalion`)
     that a keen reader will accent wrongly.
   - `INGEST_ONE_RECIPE.md` shows only flat `method:`; `ingest.md` TIER 1
     requires `method_groups` to be split at ingest and
     `test_method_xor_method_groups` knows the key. The one job that is cheap
     with the page in frame is the one the repo-less document does not ask for.
   - `INGEST_ONE_COCKTAIL.md` never mentions `character:` (which
     `test_speciality_gin_declares_a_character` requires for speciality gins)
     and teaches `item:` on every pour while §9.10 has made `item` a field that
     renders nowhere and #544 is removing it. See D8.
3. **Things the browser cannot know and must not pretend to:** whether the
   drink or dish already exists (339 food drafts, 126 drink drafts, private);
   slug collisions; `main_ingredients` case against `proper_nouns`; the
   mood derivation; pytest; git. The documents already say "compare the
   formula, never the title" with nothing to compare against.
4. **The private repos describe themselves nowhere.** `_cocktail_drafts/README.md`
   is empty and `_food_drafts/` has no README.

## 4. Design principle

**Keep the boundary the documents already draw.** The browser transcribes,
converts, canonicalises what it can from a printed vocabulary, and writes `QQ`
for every judgement. The repo validates, derives, deduplicates and asks Helen.
This design changes the TRANSPORT between those two halves and the
COMPLETENESS of what the browser is told. It does not move judgement into the
browser, and it does not move validation out of the repo.

Two consequences:

- **The documents stay hand-written.** They are mostly prose and calibration
  (Helen's own rewrites, the "trust the cook" table, the Sazerac trap), and a
  generator would flatten exactly the part that makes them work. Only the
  VOCABULARY blocks become generated. §5.
- **The repo side parses, never interprets.** If the envelope is malformed the
  consumer says so on the issue and stops. A guess here would be an invention
  in the one place the design exists to keep inventions out of.

## 5. Generated vocabulary blocks in the two documents

**Mechanism.** Each vocabulary section the documents print gains a pair of
HTML-comment markers:

```
<!-- vocab:garnish start -->
**Citrus peel:** lemon twist · lemon twist (discarded) · …
<!-- vocab:garnish end -->
```

A new script, `scripts/build_ingest_vocab.py`, renders every marked block
from `_data/` and the test suite's own loaders, and either rewrites the block
in place (`--write`) or reports the diff (`--check`). A new test in
`test_standalone_docs.py` runs the check and fails if a committed block differs
from what the generator would write. That is the two-way guard, applied only
where duplication is mechanical. Everything outside a marker pair is prose and
stays under the existing one-way tests, unchanged.

**Blocks, and where each is sourced.** Every source is an existing loader,
imported, never re-typed — the rule `ingest_preflight.py` set:

| Block | Document | Source |
|---|---|---|
| `tags` (mood and practicalities groups) | food | `_data/food/taxonomy.yml` via `test_taxonomy`'s loaders; the group split and the "meanings you would not guess" bullets stay prose |
| `stars` | food | same |
| `accents` and `no_accent` | both | `_data/accented_words.yml` |
| `source_type` table | food | `test_source_attribution.py`'s allowed types; the shape/example columns stay prose, checked as today |
| `glass` spellings | cocktail | `_glass_icons()` in `test_cocktails.py` |
| `glass` correction table | cocktail | `glasses.yml` `canonical_glasses` (already tested one-way) |
| `garnish` groups | cocktail | `_declared_garnishes()`; the grouping (citrus peel, cherries…) needs a `group:` key in `garnish.yml` or a small map in the script — Opus decides, prefer the data file |
| `method` canonical steps by group | cocktail | `_canonical_steps()` from `methods.yml`, which already groups |
| `measures` (non-volumetric amounts) | cocktail | `measures:` in `ingredients.yml`, so "to top" / "to rinse" (WS1, D4) appear the day they are declared |

**Rendering rules.** Middle dot `·` separators as today, so the existing
scrapers keep working; the script emits exactly the formatting the one-way
tests already parse, and those tests are the check that it does. Wrap at 80
columns like the rest of the documents.

**The hand-written fixes that no generator covers**, done in the same PR:
- Food document §2 and §3: add `method_groups` with the same rule `ingest.md`
  states (split once, at ingest, when the source has phases) and a two-group
  example. Keep flat `method:` as the single-phase form.
- Cocktail document §3: add `character:` with its rule from HANDOVER §9.3.1,
  and resolve the `item:` question per D8.
- Both documents: a short §0 "How to hand this back" that describes the
  envelope in §6, so the browser produces it without being told twice.

## 6. The envelope — one GitHub Issue per recipe

**Where.** The private repo matching the site: `helen-triages-food-private`
or `helen-triages-cocktails-private`. Never the public repo: the issue body
carries source text that may be copyright, and the private repos are private
for exactly this reason (HANDOVER §2.1).

**Who raises it.** Either of two authors, and the consumer cannot tell them
apart, which is the point:
- Helen herself, pasting the browser's output into a new issue from her
  phone. Works today with no new access.
- The browser session, if Helen gives claude.ai her GitHub connector or a
  fine-grained token of its own scoped to issues on the two private repos.
  That is HER token, not `GH_TOKEN`, and it is her decision (D10). Nothing in
  this design needs it.

**Shape.** Machine-checkable, in this order, nothing else at top level:

```
title:  ingest: <slug>                      e.g. ingest: crispy-sage-butter-gnocchi
label:  ingest                              created once per repo, by hand

<!-- ingest v1 food -->                     line 1 of the body: marker, version, site
```yaml
---
title: "Crispy Sage Butter Gnocchi"         the complete file, exactly as it
…                                           should be saved, front matter and all
---
```
## What I could not know
- …                                         the hand-back list, verbatim
## Fingerprint
crispy sage butter gnocchi | 500 g | 60 g | 12 | 1 | 30 g
```

Rules the consumer enforces:
- The marker is the first non-blank line and names a site the consumer
  knows. Version is an integer; the consumer refuses a version it does not
  implement rather than guessing what changed.
- Exactly one fenced `yaml` block. Its first line is `---`. It parses as
  YAML with a dict at the top. Its `title` is present.
- `## What I could not know` is present, even if its only bullet is "nothing".
- `## Fingerprint` is one line: the title lowercased, then every amount in
  ingredient order, `|`-separated. The consumer builds the same line from the
  parsed file and from every existing draft, so the duplicate check compares
  formulas, not titles, the way §6 of the cocktail document already demands.
  A drink whose fingerprint matches an existing draft's is reported as a
  probable duplicate and NOT written; one whose title matches but whose
  fingerprint differs is written under a disambiguated slug and reported as
  the Sazerac case.
- Anything else in the body is ignored; anything missing is a rejection.

**Slug.** From the title's head clause, as `INGEST_ONE_RECIPE.md` §2 says.
If the slug exists in the target collection the consumer appends `-2` and
reports it; it never overwrites.

## 7. The consumer — `/ingest-inbox`

Two files, copying `/tidy-drafts` and `/ingest` exactly: a script that does
the mechanical part and never commits, and a command doc that holds the
procedure.

**`scripts/ingest_inbox.py`** — reads issues labelled `ingest` from one
private repo (argument `--site food|cocktail`), parses each envelope per §6,
and for each one either writes the file into the drafts root and prints what
it did, or prints why it did not. Flags: `--dry-run` (default; prints the
plan), `--write`, `--issue N` (one envelope), `--comment` (post the
rejection or the "saved as" note back on the issue). It uses `urllib` with
`GH_TOKEN` from the environment at the point of use, never `gh` (absent in a
worktree, see the memory note of 2026-08-27), and never prints the token. It
imports the slug and front-matter helpers from the test suite rather than
re-typing them.

**`.claude/commands/ingest-inbox.md`** — the procedure:

1. `cd _<site>_drafts && git fetch origin` and report if `main` has moved.
2. Branch in the drafts repo: `content/inbox-<YYYY-MM-DD>`. Never its `main`.
3. `python3 scripts/ingest_inbox.py --site <site>` dry, read the plan.
4. `--write`. Then, per file, the existing finishing pass from `ingest.md`,
   in its order: cocktails `derive_cocktail_moods.py --write`; `pytest`
   (alone — never two at once); food `/tidy-drafts`;
   `ingest_preflight.py`.
5. Bring Helen ONE list: every rejection, every probable duplicate, every
   hand-back bullet from every envelope, grouped by file. Treat each as a
   TIER 3 question. Do not fill in a `generic`, a `suggestion`, a glass or a
   tagline.
6. Commit in the drafts repo with a bare `Fixes #N` per envelope — valid
   because the issue and the commit are in the same private repo (the
   cross-repo trap in CLAUDE.md does not apply). Push on her confirmation.
   The trailer is what closes the issue; the script never closes one.
7. Report what is still `QQ` and why, as `/ingest` does.

**What the consumer never does:** rewrite prose, derive `main_ingredients`,
fill a `QQ`, set a `meta` flag to anything but the values the document says,
close an issue by API, or touch `_food_recipes/` / `_cocktail_recipes/`.

## 8. Security and failure modes

- **Why an issue and not a branch.** A branch needs contents-write on a
  private repo from a session that does not run the two git hooks
  (`guard-main-branch.py`, `guard-destructive-git.py`). The issue channel
  needs nothing the tokens do not already have, and the local session that
  writes the file runs under every guard this repo has.
- **What a bad body can do.** Nothing beyond a rejection. The parser accepts
  one fenced block, one YAML document, a dict at top; it does not `eval`,
  does not follow URLs, does not write outside the drafts root, and refuses a
  slug containing anything but `[a-z0-9-]`. A body with two fenced blocks or
  a YAML document that is a list is rejected with the reason.
- **Copyright.** The issue holds source text. It is in a private repo, which
  is the same protection the drafts have. The consumer never copies an
  envelope into the public repo, and `tmp/` is where any scratch parse lands.
- **Idempotence.** Re-running the script over an issue whose slug already
  exists reports and skips; it never overwrites a file it did not just write.
- **The one thing that can silently go wrong** is a version bump: a document
  that teaches `v2` to a browser while the consumer implements `v1`. The
  marker carries the version so this is loud, and the document's §0 and the
  script's `SUPPORTED_VERSIONS` are checked equal by a test.

## 9. Decisions for Helen

| ID | Question | Recommendation |
|---|---|---|
| D8 | With `item` being retired (#544, WS4), where does the SOURCE's wording for a pour go at ingest, given `generic` and `suggestion` are `QQ` by her standing rule? | Keep `item` as a **draft-only** transcription field: allowed in `_cocktail_drafts/`, forbidden in `_cocktail_recipes/` by the WS1 schema guard, deleted by Helen when she fills `generic`/`suggestion` on making the drink. The cocktail document keeps teaching it. Alternative: a `note: "source: Patron Reposado"` on the entry, which loses structure. |
| D9 | Label name and title prefix | `ingest` and `ingest: <slug>`; both private repos get the label by hand once. |
| D10 | Does the browser get its own issue-writing access (her GitHub connector or a token of her own), or does she paste the output into an issue herself? | Start with paste. It needs no new access and produces the identical envelope; add the connector later if pasting from a phone proves to be the step that does not happen. |
| D11 | Should `garnish.yml` gain a `group:` per entry so the document's grouping is data, or may the script hold a small map? | Data file. A map in a script is the drift this design exists to remove. |

## 10. Implementation plan for Opus

Two PRs in this repo, plus small commits in the private repos.

**PR 1 — documents and generator (one day).**
1. `scripts/build_ingest_vocab.py` with `--check` / `--write`, sourcing every
   block from an imported loader (§5 table). If a loader is private to a test
   module, import it from there as `ingest_preflight.py` does; do not copy it.
2. Markers in both documents; run `--write`; diff by eye once.
3. `test_standalone_docs.py::test_every_vocab_block_matches_its_generator`.
   Keep every existing one-way test; if a scraper stops matching the generated
   formatting, fix the generator's output, not the scraper.
4. Hand-written fixes from §5: `method_groups`, `character:`, `item:` per D8,
   §0 "How to hand this back" in both documents.
5. `garnish.yml` `group:` keys per D11, with the test that every declared
   garnish has one.
6. Acceptance: `pytest tests/test_standalone_docs.py` green; `--check` clean;
   the six missing garnishes and the eight no-accent words now print.

**PR 2 — inbox (one to two days), after D8–D10.**
1. `scripts/ingest_inbox.py` per §7, with unit tests in `tests/` over fixture
   envelopes in `tests/fixtures/ingest_inbox/`: one valid food, one valid
   cocktail, and one each of: no marker, unknown site, unsupported version,
   two fenced blocks, YAML that is a list, missing hand-back section, slug
   collision, fingerprint duplicate, title-only match. Tests never call
   GitHub; the fetch is one function that the tests replace.
2. `.claude/commands/ingest-inbox.md` per §7.
3. A `SUPPORTED_VERSIONS` constant, and a test that both documents' §0 name a
   version in it.
4. HANDOVER: a §11.0.4 for the command, and a pointer from §9.2.1 and from
   `ingest.md`'s repo-less section, which becomes "if it arrived by paste,
   this is still the procedure; if it arrived as an issue, run
   `/ingest-inbox`".
5. Acceptance: with one hand-written issue in each private repo, a dry run
   prints the right plan, `--write` lands two files that pass `pytest`, and
   the finishing pass produces one hand-back list.

**Private repos (30 minutes, either PR).** `_food_drafts/README.md` and
`_cocktail_drafts/README.md`: three lines each — private, unpublished; schema
lives in `helen-triages` HANDOVER §4 / §9.3; ingest arrives via `ingest`
issues here, see `INGEST_INBOX_DESIGN.md`. Branch, commit, push (allowed).

## 11. What this deliberately does not do

- Does not let the browser run any check that needs the corpus. Every such
  check moved to the consumer, where it is one function over files it can read.
- Does not generate the prose of the two documents. Their value is judgement
  and calibration; a generator would preserve the words and lose the point.
- Does not touch `/ingest` for photo batches. That path is local, has the
  photos, and works.
- Does not build a web form, a bot, or an Action. Issues, one script, one
  command doc: the same three parts every other procedure in this repo uses.
