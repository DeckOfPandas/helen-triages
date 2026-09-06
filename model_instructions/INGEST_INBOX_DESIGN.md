# INGEST INBOX — design for ingesting recipes through a Claude with no repository

Written by Fable 5.1, 2026-09-02, as workstream 5 of that day's architecture
audit.

> **STATUS 2026-09-06: IMPLEMENTED, in full.** Both PRs in §10 landed on
> 2026-09-03 (#672): `scripts/build_ingest_vocab.py` and the marker pairs,
> `scripts/ingest_inbox.py` with its fixtures, `.claude/commands/ingest-inbox.md`,
> `SUPPORTED_VERSIONS` and its test, HANDOVER §11.0.4, and READMEs in both
> private repos. §3's gaps are closed. **What still binds is §6 (the envelope),
> §8 (security and failure modes) and §9 (the rulings)** — `ingest-inbox.md`
> and both `INGEST_ONE_*.md` cite §6 as the spec. §1, §2, §3, §7, §10 and §11 are
> one-line stubs since the 2026-09-06 documentation split (their numbering
> kept because scripts and tests cite this file by section); §4 and §5 are
> the generator's design and still describe it. The paragraph that stood here said "this is
> a design, not an implementation; nothing described here exists yet" until
> this stamp.

Every path and line number was checked at commit 8191230 and several have
moved since. Re-check before editing (HANDOVER §11.2).

---

## 1. What Helen asked for

Helen's ask, 2026-09-02: *"How to enable a Claude web to ingest recipes for me in a useful way."* The answer is now `CLAUDE_WEB_INGEST.md`.

## 2. What exists today, and it is more than the audit first assumed

History — the state of the repo-less path on 2026-09-02, before the inbox existed. `DECISIONS.md` §11.0.4.

## 3. The gaps, precisely

History — the four gaps this design closed (transport; the documents under-serving; what the browser cannot know; no READMEs in the private repos). All closed by 2026-09-03; `DECISIONS.md` §11.0.4.

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

**Slug.** The whole title, folded to `[a-z0-9-]` — Helen's ruling 2026-09-03,
replacing the head-clause rule this first said, so that two "with" dishes
sharing a head clause do not collide. If the slug exists in the target
collection the consumer appends `-2` and reports it; it never overwrites.

## 7. The consumer — `/ingest-inbox`

Built 2026-09-03 (#672). `.claude/commands/ingest-inbox.md` is the procedure and `scripts/ingest_inbox.py` the engine; this section's outline is superseded by both.

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

## 9. Decisions — RULED by Helen, 2026-09-02

| ID | Question | Ruling |
|---|---|---|
| D8 | With `item` being retired (#544, WS4), where does the SOURCE's wording for a pour go at ingest, given `generic` and `suggestion` are `QQ` by her standing rule? | **`item` is a draft-only transcription field.** Allowed in `_cocktail_drafts/`, forbidden in `_cocktail_recipes/` by the WS1 schema guard, deleted by Helen when she fills `generic`/`suggestion` on making the drink. The cocktail document keeps teaching it, and says it is draft-only. |
| D9 | Label name and title prefix | **`ingest` and `ingest: <slug>`.** Both private repos get the label by hand once. |
| D10 | Does the browser get its own issue-writing access, or does Helen paste the output into an issue herself? | **Paste, for now.** Helen: "I am new to this and quite conservative." No new access, no connector. Revisit only if she asks. |
| D11 | Should `garnish.yml` gain a `group:` per entry so the document's grouping is data? | **Yes.** Every declared garnish carries a `group:`, and a test says so. |

None of these is open. Opus can start PR 1 immediately and PR 2 without
waiting on anything but PR 1.

## 10. Implementation plan for Opus

Done, both PRs, 2026-09-03. `DECISIONS.md` §11.0.4.

## 11. What this deliberately does not do

Still true: the browser runs no check that needs the corpus; the prose of the two documents is not generated; `/ingest` for photo batches is untouched; no web form, bot or Action — issues, one script, one command doc.

