# Documentation review — 2026-09-06

Written by Fable 5.1 after reading every instruction document in one sitting:
`CLAUDE.md`, `README.md`, all nine files in `model_instructions/`, the three
command docs in `.claude/commands/`, and both private repos' READMEs. Every
claim below was checked against the code and data at `main` 0b7959c plus the
two private clones, not inferred from the documents. Line numbers are as of
that commit and will drift; section numbers are the stable reference.

**This document has a death date.** It is a worklist. Delete it when §1 has
been applied and §4 has either happened or been declined.

Helen asked for three things: gaps, inconsistencies, and parts that should be
combined or deleted. §1 is what is wrong today and is small enough to fix in
one PR. §2 is what is said twice. §3 is what nothing says. §4 is the shape of
the restructure the architecture plan deferred, and why this review should
come before it rather than after.

---

## 1. Wrong or stale today — fix in one PR, regardless of the restructure

Each of these is a statement a reader would act on and get wrong.

### 1.1 Contradictions between documents

| # | Where | It says | What is true |
|---|---|---|---|
| 1 | `.claude/commands/ingest.md` QQ table, "a drink's `meta.ship`" | `"QQ"` — she has not drunk it | `"who knows"`, since 2026-09-05. `QQ` is not a ship value and `test_meta_ship_is_a_rung_or_who_knows` refuses it. `INGEST_ONE_COCKTAIL.md` §2/§8 and HANDOVER §9.5 have it right. |
| 2 | `ingest.md` TIER 2 | "cocktail `mood`" is a fill-in-and-propose field | Never write a mood. It is derived by `derive_cocktail_moods.py --write` and a hand edit is reverted on the next run (HANDOVER §9.3, `INGEST_ONE_COCKTAIL.md` §2). The same file's cocktails-only bullet says run the deriver. What is TIER 2 is asking Helen for the ten hand-assigned moods (§9.13). |
| 3 | `ingest.md` "THE 2026-09-04 SHAPE RULINGS" | "one big cube is `giant` … `Strain over a giant ice cube.`" | Retired 2026-09-05 with the whole strain group (`methods.yml` L81–93, HANDOVER §9.10a/§9.12). The ice is `serve.ice: "large cube"`; a strain step names neither glass nor ice; `test_serve_ice_is_not_restated_in_the_method` refuses one that does. |
| 4 | `ingest.md` finishing pass steps 4 and 3-of-the-order; `ingest-inbox.md` step 4.3 | "`/tidy-drafts` for the food side" / "FOOD: `/tidy-drafts`" | Both collections since 2026-09-05 (`tidy-drafts.md`, HANDOVER §11.0.2 and the §11.0.3 diagram, `INGEST_INBOX_DESIGN.md` §7). |
| 5 | `ingest.md` step 9; `ingest-inbox.md` step 6; `INGEST_INBOX_DESIGN.md` §7 step 6 | "push with her confirmation" / "Push on her confirmation" — in the PRIVATE drafts repos | No ask needed there: `main` since 2026-08-29, branches since 2026-09-05 (`CLAUDE.md`). `tidy-drafts.md` step 8 states it correctly. Committing to `main` is still forbidden everywhere. |
| 6 | HANDOVER §9.1, "The API token is a different channel" | "Push access to the private repos exists — policy still says ask Helen every time, per CLAUDE.md." | CLAUDE.md says the opposite (above). |
| 7 | HANDOVER §9.13, card section, "The clamps themselves did not change — the ingredient line stays at two lines, and that is a decision rather than an omission" | two lines | Three lines since 2026-09-06 (#552), stated 40 lines earlier in the same section. The later paragraph is the 2026-09-04 state and should be marked history or cut. |
| 8 | HANDOVER §13.4.1, last paragraph, "To extend the device somewhere new: `@include punched(raised)` plus `-webkit-text-stroke`…" | write both by hand | `LETTERING.md` §9: say the tier, never write either by hand. The section's own 2026-09-02 header says the same; the closing paragraph was not updated with it and is the one a skimmer reads. |
| 9 | `LETTERING.md` §1, §4, §7 (third bullet), §10 (fourth bullet) | `punched()` "still has exactly one direct caller: `_sass/cocktails/_cocktail.scss`'s drink-page headings (lines 236, 357)"; the `--emboss-*` aliases stay for `_cocktail.scss` and `_cards.scss` | Zero direct callers of `punched()` remain (`grep "include punched" _sass/` finds only comments). `_cocktail.scss` reads no `--emboss-*` either; `_cards.scss`, `shared/_layout.scss` and `food/_recipe-header.scss` still do, so the alias block stays for those. The mixin itself is still defined. |

### 1.2 Stale facts

| # | Where | It says | What is true |
|---|---|---|---|
| 10 | HANDOVER §1 | "`_config_local.yml` overrides two things: `show_source_wording: true` and the `food_drafts` collection" | It sets seven keys and three collection outputs: `show_source_wording`, `pdf_downloads`, `show_awaiting_fix`, `show_costs`, `show_units`, `show_drafts`, and `output: true` on `dev`, `food_drafts`, `cocktail_drafts`. |
| 11 | HANDOVER §2.1 tree | lists `_includes/ filter_group.html recipe_badges.html`, `_data/ cocktails/{taxonomy,ingredients,bottles,glasses,methods,garnish}.yml`, no `_plugins/` | `_plugins/` holds four (`publish_gate`, `cocktail_costs`, `cocktail_units`, `cocktail_card_ingredients`); `_data/cocktails/` also has `serve`, `costs`, `abv`; `_includes/cocktails/ship.html` and `_includes/icons/glasses/` exist; `_design_sources/`, `_dev/`, `scripts/`, `tests/js/` are absent from the tree. See §3.1 below. |
| 12 | HANDOVER §4, one line before §4.1 | "**Cocktails front matter does not exist yet and must not be invented.** See §9." | False since 2026-08-16. Delete. |
| 13 | HANDOVER §9.5, `made_before` bullet, "The open consequence, unbuilt: a published `who knows` card draws the ship mark with no word beside it… needs `_includes/cocktails/ship.html` changed" | unbuilt | Built 2026-09-05 (commit 8557c6e): `ship_unrated_word: "???"` in `taxonomy.yml`, read by `ship.html`. |
| 14 | HANDOVER §9.13, narrow screens, "Three layouts currently sit behind `?narrow=` and TWO OF THEM ARE DUE TO BE DELETED" | pending | Done. §11.2.1 records Helen choosing `stack` and the losers going; `cocktails/index.html` carries no `?narrow=` switch. |
| 15 | HANDOVER §11, "End every commit: `Co-Authored-By: Claude Opus 5`" | a specific model | Sessions run on more than one model. The test matches `co-authored-by: claude` case-insensitively. Say "the `Co-Authored-By: Claude …` trailer the harness supplies". |
| 16 | HANDOVER §13.10.2 value table | `$color-emboss-shadow rgba($color-text, 0.68)`, `$color-emboss-light` is `$color-white`, `$color-label-stroke lighten(…, 30%)` | None of `$color-emboss-*` exists in `_sass/shared/_rule.scss` any more; the values are the `--lettering-*` tiers (`LETTERING.md` §3 is the table, and §2 explains why 0.68/white were the fault). Only the four `$emboss-*` lines and the ceiling argument survive. |
| 17 | HANDOVER §9.9 and §9.13 ("**It reads DRAFTS**") | the drinks index loops drafts | `all_drinks = site.cocktail_recipes` plus drafts under `show_drafts`, since #668 (§9.1.1). History, but stated in the present tense twice. |
| 18 | HANDOVER header, "26 glasses, 43 garnishes and 32 canonical method steps" | counts | Self-flagged as stale in the next sentence. Delete the numbers; the sentence stands without them. |
| 19 | `INGEST_ONE_COCKTAIL.md` §1 | "171 declared terms", "107 declared, and none outstanding" | Bottles are 127 (HANDOVER §9.3). These counts sit outside the vocab markers, so nothing regenerates them. Delete the numbers. |
| 20 | `PUBLISHING_A_DRINK.md`, "The one working copy" | "today: **4004**, branch `content/first-batch-to-promote`" | That branch is merged and gone. The remote holds `data/caribbean-sazerac-faff` and `feat/serves-for-punches`. State the rule (one clone, one branch named for the batch, one port), not the day's values. |
| 21 | `INGEST_INBOX_DESIGN.md` header | "This is a design, not an implementation. Nothing described here exists yet" | All of §10 shipped (#672, 2026-09-03): `build_ingest_vocab.py`, `ingest_inbox.py`, `/ingest-inbox`, the fixtures, `SUPPORTED_VERSIONS`. §3's gaps 2 and 4 are closed (both private READMEs exist; the vocab blocks are generated). Needs the stamp `ARCHITECTURE_PLAN` got today. |
| 22 | `SOURCE_ATTRIBUTION_SPEC.md`, "The current corpus" table | 82 recipes / 314 drafts, zero violations | Self-declared stale in the header. Delete the table; the test is the count. |
| 23 | `tidy-drafts.md`, "A missing `meta.awaiting_fix` (2 drafts)" | 2 | 1 today. Drop the number. |
| 24 | `LETTERING.md` §5 consumer table | `.site-logo-top` at `_layout.scss:521`; `.cocktail-section-heading` 1.35rem at `_cocktail.scss:465` | 497 and 769; the heading is 1.5rem since 2026-09-05. Drop the line numbers (the file name is enough and does not rot); fix the size. |
| 25 | `_cocktail_drafts/README.md` | `item` "is allowed here and forbidden in `_cocktail_recipes/`" | The rule is conditional: gone once the pour's `generic` is filled in, drafts included (`test_item_is_gone_once_the_generic_is_filled_in`), and refused in `to-promote/` too. Private repo, one line. |

### 1.3 One rule stated three different ways

`item`'s deadline is described as "promotion" (`_cocktail_drafts/README.md`),
"the staging folder" (HANDOVER §9.10, `ingest.md`'s to-promote box), and "the
moment the generic is filled in" (HANDOVER §9.3, `PUBLISHING_A_DRINK.md`,
`INGEST_ONE_COCKTAIL.md` §3). All three tests exist and agree in effect, but a
reader meets three different "the deadline is X" sentences. One wording, used
everywhere: *an `item` may exist only beside `generic: "QQ"`; it goes when the
generic is filled in, wherever the file is, so a staged or published drink
never carries one.*

### 1.4 Not wrong, but a trap that bit today

`CLAUDE.md` says never print `GH_TOKEN`. Nothing says that `${GH_TOKEN:-unset}`
prints it — the very shell idiom for "is it set" leaks the value. I did exactly
that this morning. One line under the token rules: *to test whether it is set,
use `${GH_TOKEN:+set}` alone; never a form with a fallback that expands the
variable.*

---

## 2. Said twice — combine

The pattern across all of these: the handover says "X is the authority, this
does not restate it", and then restates it. Each pair has already diverged at
least once (§1.1 rows 1–5 are all divergences between a copy and its
authority).

| Topic | Copies | Keep | Cut to a pointer |
|---|---|---|---|
| The ingest contract (in the source vs in Helen's head; TIER 1/2/3) | `ingest.md`; HANDOVER §4 "THE INGEST CONTRACT" box plus the three TIER paragraphs (~70 lines); `INGEST_ONE_RECIPE.md` §1 (for the repo-less reader, legitimately) | `ingest.md` | HANDOVER §4: the boxed one-line question and "see `ingest.md`" |
| The `QQ` conventions (`QQ original` / `QQ Claude` pairs, notes, the content-filter trap) | `ingest.md` QQ table; HANDOVER §4 "Easy to get wrong" first bullet (~75 lines) | `ingest.md` | HANDOVER §4: "QQ is Helen's placeholder, never flag it" and the pointer |
| The three commands | `.claude/commands/*.md`; HANDOVER §11.0.2, §11.0.3, §11.0.4 (~260 lines, mostly the story of building each) | the command docs | one paragraph each in the handover: what it is for, when to reach for it |
| The branch workflow and the two hooks | `CLAUDE.md`; HANDOVER §11.-1 and §11.0 (~150 lines); HANDOVER §11's boxed "TAG THE ISSUE" | `CLAUDE.md` (the handover already says so: "that's the source of truth now, not this file") | the handover keeps the one paragraph of *why* per hook |
| Clone the drafts into a worktree | HANDOVER §1, §9.1, §11.0.1, §13.11; two memory notes | §11.0.1 | the other three point at it |
| Lettering | `LETTERING.md`; HANDOVER §13.4.1 (~260 lines) and §13.10.2 (~70 lines), both marked superseded | `LETTERING.md` | the handover keeps the "since 2026-09-02 a consumer names its tier" paragraph and the pointer; the mechanism history goes to the decisions log |
| The gate flags | HANDOVER §4.0 (the authority), §9.1.1, `PUBLISHING_A_DRINK.md` "what the flags mean", `CLAUDE.md`, both `INGEST_ONE_*.md` meta rows | as is — these are consistent and each copy serves a different reader | nothing; but §4.0's `BASELINE_COMMIT` history (four moves) belongs in the constant's own comment, where the handover already says to look |
| Rulings tables | `ARCHITECTURE_PLAN.md` §8; `INGEST_INBOX_DESIGN.md` §9; `LETTERING.md` §11; HANDOVER §9.4 "do not re-litigate", §13.12 | — | one decisions log (§4) |
| One-working-copy rule | `PUBLISHING_A_DRINK.md`; HANDOVER §9.1, §11.0.1 | `PUBLISHING_A_DRINK.md` | pointers |

---

## 3. Gaps — nothing says it

### 3.1 The plugins

Four Ruby plugins now decide what the site shows: the publish gate, the cost
and unit arithmetic, and the card's ingredient line. The §2.1 tree does not
list `_plugins/`, and the one architectural fact about them — GitHub Pages'
safe mode silently ignores `_plugins/`, so the gate would vanish and the build
stay green — is stated once, in passing, inside §4.0. A short "plugins"
paragraph in the manual: what each does, that the workflow runs a
plugin-capable build (`test_site_config.py` asserts it), and the safe-mode
trap.

### 3.2 The schema handshake

`SCHEMA_VERSION` in each private repo and `tests/drafts_schema.py` are the
mechanism for every future drink or draft migration ("bump BOTH numbers in the
paired commits"). It is documented only inside a box in §10, under a heading
about CI. It belongs beside the schemas it protects (§4 and §9.3) and in the
migration paragraph of §9.1.1, which describes how to migrate a drink field
and does not mention it.

### 3.3 The header and footer tones for leopard

`LEOPARD.md` §3 gives the header/footer tones for the "sheen" set and says the
others are in `tmp/mock/leopard_v2.py`'s `PATTERNS`. `tmp/` is gitignored and
the file is gone; §4 says so. So the "more shades" and "extreme" chrome tones
exist nowhere. Either tabulate them (they are the page tones plus one step,
which the paragraph states, so they are derivable in a minute) or say plainly
that only the sheen chrome tones are recorded.

### 3.4 Where the pending private-repo work is

`main` fails one cocktails test today: commit accee12 took `I want to faff`
off the Caribbean Sazerac's correction in `taxonomy.yml`, and the drink file
in the private repo still stores it. The fix is on the private remote as
`data/caribbean-sazerac-faff`, unmerged. Nothing in either repo says a public
merge is waiting on a private one — which is #624's class exactly, and the
handshake in §3.2 cannot see it because it is data rather than schema. Worth
one habit in `PUBLISHING_A_DRINK.md` or `ingest.md`: when a public PR needs a
private branch, name the branch in the PR description.

### 3.5 Line numbers in documents

`ARCHITECTURE_PLAN` learned this today; `LETTERING.md` §5 has the same fault
(every row carries a `file:line` that has drifted). A one-line house rule for
`model_instructions/`: name files, never lines.

---

## 4. Delete, or move to a decisions log — the restructure

### 4.1 What the handover is

9,877 lines. Two kinds of sentence are interleaved throughout:

- **Manual**: what a field means, which file owns which vocabulary, how to run
  the thing, what a test guards. Perhaps 2,000 lines.
- **Journal**: what happened on which date, what the document said before it
  said this (42 sentences of the form "this said X until DATE"), what was
  tried and rejected, and the reasoning behind each ruling. The other 7,800.

The journal is valuable and must not be lost — the "why" paragraphs are what
stop a ruling being re-litigated (§11.2's whole complaint). But a reader who
needs the schema has to find it inside the story of how the schema was
argued, and a reader who needs the story cannot tell which sentences still
bind. The header's own reading guide ("read §2.5, §11.-1, §11.0, §4.0, then
§12 — and §10 is worth reading too") is the symptom: there is no page that is
just the rules.

### 4.2 The shape

Two files replace `HANDOVER_v26.md`:

**`MANUAL.md`** — the current state, no dates except where a date is the
rule. Sections roughly as the handover's outline, cut to what binds today:
run it; the repo shape (with a tree that is checked against `ls`); the three
layers; the food schema and gate; the drink schema and gate; house style;
taxonomies and vocabularies (pointers to the data files, which already carry
their own reasoning in comments); the test map; working practices (pointers
to `CLAUDE.md` and the command docs); traps as one line each with a pointer
into the log; the visual design's current shape (one paragraph per surface,
pointing at the SCSS headers, which already carry the anatomy). Target 1,500
to 2,000 lines.

**`DECISIONS.md`** — append-only, dated, grouped by area. Every "Helen ruled X
on DATE because Y", every rejected alternative, every "this said X until
DATE" correction, and the four existing rulings tables merged in. The
handover's own dated boxes lift almost verbatim; the work is deciding which
sentences are the ruling and which are the mechanism.

Everything else stays as it is, because it is already manual-shaped and
current once §1 is applied: `CLAUDE.md`, the three command docs,
`SOURCE_ATTRIBUTION_SPEC.md`, both `INGEST_ONE_*.md`, `PUBLISHING_A_DRINK.md`,
`LETTERING.md`, `LEOPARD.md`. Two retire once the log exists:
`ARCHITECTURE_PLAN_2026-09-02.md` (§8 goes to the log; nothing else binds)
and `INGEST_INBOX_DESIGN.md` (§6 and §8 are the live envelope spec that
`ingest-inbox.md` and both `INGEST_ONE_*.md` cite — move them into
`ingest-inbox.md` or a short `INGEST_ENVELOPE.md`; §9 to the log; the rest is
history).

### 4.3 Sections that are history in full, to move first

These are the largest blocks where nothing binds except a pointer, and moving
them is nearly mechanical:

- §9.9 (already a tombstone), §9.5's retired-square paragraph, §13.10.2's
  `.on-dark` box, §13.9's rejected lettering alternatives, §14's
  "RESTRUCTURED 2026-08-19" box, §10.1 ("CUT HARD" already).
- §13.4.1 and §13.10.2 — superseded by `LETTERING.md` and marked so.
- §9.13 (~1,400 lines) — nine rounds of design in date order. The current
  shape is in the SCSS headers, which the section itself says to read first.
- §11.0.2–§11.0.4, §11.-1, §11.0 — see §2.
- The "THIS PARAGRAPH SAID … UNTIL …" corrections (42) — each is a log entry.

### 4.4 Why this review before the restructure, not after

The restructure is a rewrite of what the manual half says. Four of the nine
contradictions in §1.1 are between a document and a copy of it; a restructure
that started from the handover as-is would carry the wrong copy into the
manual in at least two places (rows 6, 8). Fixing §1 first, in one small PR,
means the restructure starts from documents that agree — and it is the same
PR whether or not the restructure ever happens.

### 4.5 Order

1. §1, one PR in this repo plus one commit each in the two private repos
   (rows 5 and 25). Half a day. Every row is a verified one-line fix.
2. Merge `data/caribbean-sazerac-faff` in the private repo so `main` is green.
3. The restructure, its own session, this document open beside it. Harvest
   `DECISIONS.md` first — it is additive and can be checked (every dated
   ruling in the handover must appear in the log before its source paragraph
   is cut). Then cut `MANUAL.md` down from what is left. One PR; every merge
   is a deploy, and this one changes no page.
4. Delete this file.
