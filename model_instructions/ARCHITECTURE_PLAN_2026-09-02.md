# Architecture, data model, code and workflow plan — 2026-09-02

Written by Fable 5.1 after a read-only audit of the worktree at commit e31970d.
Audience: an Opus session picking this up, and Helen deciding what to run.
Nothing below has been implemented. Every line number is as of e31970d and
must be re-checked before editing (HANDOVER §11.2: do not trust a document
over the code).

Two rulings from Helen that shape this plan, given 2026-09-02:

- **Cocktails need a PUBLICATION gate, not a promotion gate.** Helen promotes
  by hand (moving a file from `_cocktail_drafts/` to `_cocktail_recipes/`).
  What is needed is the thing that decides whether a promoted drink reaches
  the live site, and the evidence that it was proofread.
- **`tagline` is a real field.** It is not to be dropped. The fact that 120 of
  124 drinks carry the placeholder `"QQ"` is a backlog, not a design smell.

## 0. How to read this

Six workstreams, ordered by value per hour. Each says: goal, why, exact files,
steps, tests that prove it, acceptance, risk, and **who** — Opus, Fable, or
Helen. Workstreams are independent unless a "depends on" line says otherwise.
Each is one PR unless stated (HANDOVER §11.0.0: prefer larger PRs, every merge
is a deploy). Every commit that edits a drink or recipe file sets
`meta.proofread: false` in the same commit (CLAUDE.md, #367).

Summary of who does what:

| # | Workstream | Who | Size |
|---|---|---|---|
| 1 | Cocktail schema guard | Opus | half a day |
| 2 | Cocktail publication gate, and `proofread` now gates food too | Opus (D1–D4 ruled) | one to two days |
| 3 | Port house-style checks to drinks | Opus | half a day |
| 4 | Finish `item` (#544) | Opus mechanical half; Helen rulings | one day + rulings |
| 5 | Ingest spec regeneration + Claude-web inbox | **Fable designs, Opus implements** | 2–3 days |
| 6 | Shared/forked code consolidation | 6a–6b Opus; 6c **Fable**; 6d decision Helen | 1–3 days |
| 7 | Handover hygiene | Opus for the three fixes; **Fable** for the restructure | — |

## 1. Cocktail schema guard (Opus, half a day)

**Goal.** A drink file cannot gain or lose a key silently.

**Why.** The audit found the drink corpus is uniform (12 top-level keys, every
key single-shaped, `meta` is exactly `{ship, date_last_edited}` on all 124),
but nothing enforces it. Nine drinks have no `method` and eleven ingredient
entries have no `amount`, and no test noticed. The "ad hoc" feeling comes from
the absence of a guard, not from the data.

**Files.** `tests/test_cocktails.py` (loader `_load()` at ~L141 reads both
`_cocktail_recipes/` and `_cocktail_drafts/` via `rglob`; use it). Model the
new tests on `tests/test_front_matter.py::test_no_retired_fields` (L217),
`test_meta_block_is_exactly_the_three_flags_in_order` (L262) and
`test_notes_is_a_list` (L404).

**Steps.**

1. Add module constants near `RECIPES`/`DRAFTS` (L47–48):
   - `TOP_LEVEL_KEYS = {title, tagline, glass, garnish, ingredients, method,
     mood, notes, source, source_url, meta, to_serve}` plus whatever
     workstream 2 adds to `meta`.
   - `REQUIRED_TOP_LEVEL = {title, tagline, glass, garnish, ingredients,
     method, mood, notes, source, source_url, meta}`.
   - `INGREDIENT_KEYS = {generic, amount, item, suggestion, note, character,
     optional}` and `REQUIRED_INGREDIENT = {generic}`.
   - `META_KEYS_IN_ORDER = [ship, date_last_edited, ...gate flags from WS2]`.
2. Tests, each parametrised over every drink:
   - `test_no_unknown_top_level_keys` / `test_required_top_level_keys_present`.
   - `test_no_unknown_ingredient_keys`.
   - `test_method_is_a_non_empty_list` — the 9 methodless drinks must be
     fixed first (see step 4) or this is red on day one.
   - `test_every_ingredient_has_an_amount_or_is_added_by_a_method_step` —
     **ruled by Helen (D4): a top-up is a METHOD STEP, not a note, and it
     needs a dictionary entry.** The 11 amount-less entries as of e31970d:
     champagne ×6 (`airmail`, `arrack-christmas-punch-wife-3`, `bali-hai`,
     `drunken-skull`, `green-flash`, `julien-sorel`), soda water ×2
     (`pear-apricot-honey-lemon-and-rosemary-bellini`, `tom-collins`),
     and three that are not top-ups: `man-o-war` salt (a rim?),
     `sazerac-death-and-co` absinthe (a rinse; entry note says the source
     gives no measure), `tailspin` Campari (a rinse, ruled).
     **Helen's second ruling, 2026-09-02: every ingredient HAS an amount,
     and for these it is a verb phrase.** The list should read "champagne,
     to top" and "absinthe, to rinse", so the entries become
     `amount: "to top"` / `amount: "to rinse"`. Campari in `tailspin` is a
     rinse and stays in the list with `amount: "to rinse"`. Mechanics:
     - `test_every_amount_is_readable_as_a_quantity` (L1612) accepts an
       amount only if its unit is declared in `measures:` in
       `_data/cocktails/ingredients.yml`; add `to top` and `to rinse` to
       `non_volumetric` with a comment saying they are actions, not
       counts. Do not special-case them in the test.
     - `tom-collins` says "Top with club soda." while the dictionary has
       "Top with champagne."; add "Top with soda water." to `build` and
       normalise the drink. **Ruled: always soda water, never club soda**
       (Helen is not in the US and doubts the difference is more than
       marketing). Apply the same to any other "club soda" in the corpus.
     - Rinse steps exist in drinks ("Rinse the glass with absinthe and
       dump.", "Rinse the glasses with Campari."); check whether
       `methods.yml` already holds a rinse group (its L48–64 comments
       discuss rinses). If not, add one with those strings as-is unless
       Helen wants them unified.
     - Salt: Helen's method wording is **"Salt a half-rim of the glass."**
       (preferred over "Salt half the rim of the glass"). Add it to the
       dictionary for rimmed drinks. BUT `man-o-war` L23–24 says
       `item: "Tiny pinch of salt"` with no amount, which is salt IN the
       drink, not a rim. **Ruled: `amount: "1 small pinch"`**, no rim
       step. Declare `small pinch` in `measures:` if only `pinch` is
       declared, and drop the `item` line (it restates the amount).
     - Then the WS1 test is simply `test_every_ingredient_has_an_amount`.
     No new front-matter key. Helen has asked for direct questions if
     method-step wording gets complicated.
   - `test_date_last_edited_is_iso_date` (`YYYY-MM-DD` string).
   - `test_meta_keys_are_exactly_and_in_order`.
   - `test_tagline_is_a_non_empty_string` (all drinks) and
     `test_promoted_drinks_have_a_real_tagline` (recipes only: not `"QQ"`).
     A placeholder must not publish; this mirrors
     `test_front_matter.py::test_tagline_is_not_blank` (L66).
3. Add `mood` to the schema block in HANDOVER §9.3 (~L2085). Today it is
   documented only in `INGEST_ONE_COCKTAIL.md` L95 and `taxonomy.yml`.
4. Fix the nine methodless drinks: `biggles-sidecar`, `cobra-effect`,
   `copenhagen-special`, `cynar-toronto`, `georgetown-punch`,
   `milliners-punch`, `gunmetal-blue`, `minty-pentones`, `tiki-max`. If the
   source has no method, write `method: []` is NOT acceptable (fails the
   test by design); write the method from the source or add a `QQ` note and
   hand the list to Helen. These edits go in the private repo on a branch.

**Acceptance.** `pytest tests/test_cocktails.py` green with the drafts
present; the loader's "no drinks on this machine" skip (L113) still fires on
a bare CI checkout. `pytest` run once, alone (never two at once — the gate
test writes files into `_food_recipes/`).

**Risk.** Low. Pure additions. The only judgement call is D4.

## 2. Cocktail publication gate (Opus, one day; Helen decides D1–D3 first)

**What exists today, verified.**

- `_plugins/hide_awaiting_fix.rb` L53: `GATED_COLLECTIONS` already includes
  `cocktail_recipes`. The gate FAILS CLOSED: a promoted drink with no
  `meta.awaiting_fix` is silently held back from production. So promotion
  today would produce a drink that does not publish and no message beyond a
  build-log line. That is safe but invisible.
- `cocktails/index.html` L43 reads `site.cocktail_drafts` only, gated on
  `site.show_drafts` (a `_config_local.yml`-only key). The production drinks
  index is empty by design (comment at L22–25: "an index over nothing").
  A promoted drink would render at `/cocktails/recipes/<slug>/` but never be
  listed.
- `_config.yml` L158–163 and L201–210: both collections exist, both use
  `layout: cocktail`.
- Drinks carry `meta: {ship, date_last_edited}` and nothing else.
- Food's gate tests live in `tests/test_front_matter.py` L1139–1298
  (`test_agent_edited_recipes_are_not_marked_proofread`,
  `test_every_recipe_declares_awaiting_fix`,
  `test_awaiting_fix_is_a_real_boolean`,
  `test_no_recipe_uses_the_old_hyphenated_awaiting_fix_key`) and are scoped
  to food by `tests/conftest.py` L28–32.

**Decisions, RULED by Helen 2026-09-02.**

- **D1. Reuse all three of food's flag names: `meta.rewritten`,
  `meta.awaiting_fix`, `meta.proofread`, in that order.** `rewritten` is
  ported too. Helen: it "shows me if I have rewritten it, not an agent" —
  for a drink that mostly means the notes and the tagline, but her first
  pass also checks ingredients, bottle suggestions and method, before the
  proofread. Only Helen sets `rewritten: true` (HANDOVER §4 L639 says the
  same for food). The migration writes `rewritten: false`.
- **D2. Every draft carries all three flags after migration:
  `rewritten: false`, `awaiting_fix: false`, `proofread: false`.** Helen:
  "this is honest". `output: false` on the drafts collection is what keeps
  them private, not the flags.
- **D3. `proofread` GATES PUBLICATION, on both sites.** Helen: proofread
  "is the very last touch that I, the human, make to the file", and a page
  must not publish while it is `false`. The one exception is a trivial fix
  she requests: Claude makes it and sets `proofread: false` in the same
  commit (existing rule, #367); she re-reads the line or so affected and
  sets it back to `true` herself.

  **This is NOT what the plugin does today, and the plan's first draft was
  wrong to suggest leaving it.** `_plugins/hide_awaiting_fix.rb` publishes
  on `awaiting_fix == false` alone. As of e31970d five recipes in
  `_food_recipes/` are `awaiting_fix: false, proofread: false` and are
  therefore live unproofread: `wagamama-yakitori-sauce`, `youvetsi`,
  `sweet-potato-chocolate-brownies`, `wagamama-teriyaki-sauce`,
  `duck-a-lorange-sanguine`. The plugin header's argument against a second
  field is about `published:` duplicating `awaiting_fix` (two fields, one
  meaning); `proofread` is a different fact, so requiring both is not that
  mistake.

  The change: in the plugin, `flagged = !(meta.is_a?(Hash) &&
  meta["awaiting_fix"] == false && meta["proofread"] == true)`, for all
  three gated collections, with the log line naming which flag held each
  page back. Rename the plugin (and its log prefix) to say what it now
  gates, e.g. `publish_gate.rb`, and update every reference: the header
  comment, HANDOVER §4.0, `tests/test_site_config.py`'s plugin-capable-build
  assertion (search for `hide_awaiting_fix`), and the #331 wording in
  `CLAUDE.md`. Add a rendered-page test that a `proofread: false` recipe is
  absent from the production build, beside the existing `awaiting_fix` one.
  **Deploying this takes the five recipes above off the live site until
  Helen proofreads them.** Tell her the list in the PR description; it is
  her call whether to proofread first or let them drop.

**Steps.**

1. **Migration**, in `_cocktail_drafts/` on a branch: a one-off script in
   this repo's `tmp/` (never `/tmp`) that appends `rewritten: false`,
   `awaiting_fix: false` and `proofread: false` under `meta:` after
   `date_last_edited`, preserving quoting and order, on all 124 files.
   Verify with `git diff --stat` that exactly three lines were added per
   file. Commit in the private repo with
   `Towards DeckOfPandas/helen-triages#<issue>`; push is allowed there.
2. **Schema**: extend `META_KEYS_IN_ORDER` from WS1 to
   `[ship, date_last_edited, rewritten, awaiting_fix, proofread]` — the
   three gate flags in food's order (`test_front_matter.py` L259
   `META_ORDER`), after the two drink-specific keys.
3. **Tests** in `tests/test_cocktails.py`, mirroring the four food tests
   named above, over both collections for the boolean/hyphen checks and
   over `_cocktail_recipes/` only for the git-history proofread check.
   Copy the food test's `BASELINE_COMMIT` mechanism (L554) with its own
   constant, set to the migration commit, and document in the test why.
   Note `_cocktail_recipes/` is in THIS repo, so `git log` runs here; do
   not try to read the private repo's history from the public test.
4. **Index**: change `cocktails/index.html` L43 onwards to food's shape
   (`food/index.html` L34–44): `all_drinks = site.cocktail_recipes`, then
   `concat: site.cocktail_drafts` only under `site.show_drafts`. Every later
   reference to `site.cocktail_drafts` in that file (L131, L146, L223–224,
   L228) must switch to `all_drinks`. Keep the #235 guard comment; update
   its "index over nothing" paragraph because it becomes false the day one
   drink is promoted.
5. **Plugin**: the D3 change above (gate on `awaiting_fix == false` AND
   `proofread == true`, all three collections, rename, log which flag held
   a page back). Also update the comment at L59–62 which says cocktail
   pages carry no flag — after the migration they do. This is the one step
   that changes food's behaviour; it goes in the same PR so the gate lands
   whole, and the PR description lists the five food recipes it takes down.
6. **Rendered-page tests**: `tests/test_rendered_pages.py` has
   `test_every_published_page_links_a_stylesheet` and the chrome identity
   tests. Add a drink to the pages they sample once one exists in
   `_cocktail_recipes/`; until then, add a fixture that copies one draft into
   `_cocktail_recipes/` under a `zzz-gate-` name the way the food gate test
   does, so the plugin path is exercised in CI. Look at how the existing
   gate test writes and removes its `zzz-gate` files before copying the
   pattern, and keep the "never two pytests at once" rule.
7. **Handover**: §9.1 ("nothing about the drinks is public") stays true
   until promotion; add a §9.1.1 describing the gate in the same terms as
   §4.0, and point at it from §4.0.
8. **Badges (D5 ruled yes)**: `_includes/recipe_badges.html` renders food's
   flags on the index. Drink cards get the same three badges, local build
   only, via the same include if it can take the drink's `meta` without a
   `site_key` branch. If it cannot without branching, write a cocktails
   include and note it in WS6. Style it inside `_sass/cocktails/_cards.scss`
   using the card's existing accents; do not import food's `_badges.scss`.

**Acceptance.** With one draft copied into `_cocktail_recipes/` locally:
`awaiting_fix: false` → appears on the built index and at its URL;
missing or `true` → held back and named in the build log; an agent commit
touching it with `proofread: true` → the suite fails. Then remove the copy.

**Risk.** Medium. The index rewrite touches the moods derivation loops and
the count text. The migration is 248 added lines across a private repo;
mechanical, but review the diff by eye on five files before committing.

## 3. Port house-style checks to drinks (Opus, half a day)

**Goal.** The typography rules `INGEST_ONE_COCKTAIL.md` §7 demands (en
dashes, accents, quoted scalars, British spelling) are checked on drinks.

**Files.** `tests/test_style.py` (~40 tests, food-only via `conftest.py`
L28–32). `_data/accented_words.yml` (45 accented, 8 explicit no-accent —
already documented as applying to cocktails, HANDOVER §2.2 L257).

**Steps.** Do not move the food tests. Identify the four to six that are
corpus-agnostic (scalar quoting, hyphen-vs-en-dash in ranges, accented
words and the no-accent list, British spelling list, straight-vs-curly
quotes). Extract each check's core into a helper taking `(path, text)` and
call it from a new parametrised test in `test_cocktails.py` over the drink
loader. Leave food's parametrisation untouched so its failure messages and
counts do not change.

**Acceptance.** Run once; expect real failures in the drink corpus. Fix
mechanical ones in the private repo on a branch (`/tidy-drafts` does the
food equivalent; do not extend that skill in this PR). Anything needing a
ruling goes in the hand-back list to Helen.

**Risk.** Low. Watch for the food tests' reliance on `checkable_raw()`
(conftest L317) which strips code and prose spans; reuse it, do not
reimplement.

## 4. Finish `item` (#544) (Opus mechanical half, Helen rulings)

**Facts.** 282 ingredient entries carry `item`. 118 restate their own
`generic` textually. `_layouts/cocktail.html` L315 reads `item` only as a
fallback for an entry with no `generic`, and zero such entries exist, so
`item` renders nowhere today.

**Steps.**

1. Script in `tmp/` lists every `(file, index, generic, item)` where
   `item.lower() == generic.lower()` after stripping articles. Delete those
   118 `item` lines in the private repo on a branch. Show Helen the diff
   stat, not the diff.
2. The remaining ~164 carry residue (brand, style, "cane" ×31 is #594).
   Produce one table to Helen per family, largest first, asking per line:
   move to `suggestion`, move to `note`, or delete. Do not guess.
3. **Revised by D8 (2026-09-02): `item` is NOT removed from the schema.**
   It becomes a DRAFT-ONLY transcription field: allowed in
   `_cocktail_drafts/`, forbidden in `_cocktail_recipes/` by the WS1 guard
   (split `INGREDIENT_KEYS` into a drafts set and a recipes set). Steps 1
   and 2 still apply to the current backlog of restating and residue
   entries. The fallback at `cocktail.html` L315 can go once no promoted
   drink can carry the key. `INGEST_ONE_COCKTAIL.md` keeps teaching `item`
   and says it is draft-only.

**Depends on.** WS1 for the key list. Does not block anything.

## 5. Ingest spec regeneration and a Claude-web inbox (Fable designs, Opus implements)

**Why Fable.** This crosses the test suite, the two hand-written spec docs,
the issues-only token model, and the git hooks, and the failure modes are
security-shaped (a browser session that cannot run hooks writing into a
private repo). The envelope design and the "what stays local" boundary need
one session that holds all of it. Once the design doc exists, the
implementation is ordinary and Opus can do it.

**Findings the design must respect.**

- `GH_TOKEN` is issues-only on three repos (CLAUDE.md; probed 2026-08-17:
  file write 403, PR 403). Issues are the only sanctioned write channel for
  any token-holding Claude. Private repos have no build, so nothing an
  issue carries can publish.
- The two standalone docs are hand-maintained copies of the contract and
  have drifted: `INGEST_ONE_COCKTAIL.md` §4 omits six garnish strings now in
  `garnish.yml`; it mandates `item:` + `generic: "QQ"` on every pour while
  the corpus writes `generic:` alone and carries `character:` (which the
  doc never mentions); `INGEST_ONE_RECIPE.md` shows only flat `method:`
  while `.claude/commands/ingest.md` TIER 1 and
  `test_method_xor_method_groups` know `method_groups`; the accent list is
  ~12 words against 45 + 8 no-accent in the data.
- Things a browser Claude cannot do and must not pretend to: duplicate
  check against 339 food / 126 drink drafts, slug collision, `main_ingredients`
  case against `proper_nouns`, pytest, `derive_cocktail_moods.py`, git.
- `scripts/ingest_preflight.py` already imports every rule from the test
  suite rather than re-typing it. That is the model.

**DONE 2026-09-02: `model_instructions/INGEST_INBOX_DESIGN.md` on branch
`design/ingest-inbox`.** Read that instead of the outline below; it
supersedes it in two places. First, the documents are NOT regenerated
wholesale — reading them showed they are mostly prose and calibration, and
`tests/test_standalone_docs.py` already guards the dangerous direction
(printed-but-retired); only the vocabulary blocks become generated, between
markers, with a two-way check. Second, the repo-less path already exists in
`.claude/commands/ingest.md` ("A FILE THAT ARRIVES FROM A REPO-LESS
SESSION"); the design changes transport and completeness, not the boundary.
It adds decisions D8–D11 (see the design doc §9). Outline as first written:

1. **Generated specs.** (**What shipped is `scripts/build_ingest_vocab.py`**,
   renaming this and narrowing it to the marked vocabulary blocks alone, per
   the paragraph above. There is no `build_ingest_specs.py`; do not grep for
   one.) A `scripts/build_ingest_specs.py` that renders
   `INGEST_ONE_RECIPE.md` and `INGEST_ONE_COCKTAIL.md` from `_data/*.yml`
   and the constants in `tests/` (allowed keys from WS1, taxonomy tags and
   stars, glass `icons` keys, garnish and method vocabularies, accented and
   no-accent words), with the prose parts kept in a template. A test
   asserts the committed docs equal the generated output, so drift fails
   CI. Decide what is generated and what stays prose.
2. **The envelope.** One GitHub Issue per recipe in the matching private
   repo, label `ingest`, title `ingest: <slug>`, body = a marker line
   (`<!-- ingest v1 food -->` / `cocktail`), one fenced block holding the
   complete file, then a `## What I could not know` list, then a
   fingerprint line (title + ordered amounts) for the local duplicate diff.
   Machine-checkable; the local side parses, never interprets.
3. **The local consumer.** `.claude/commands/ingest-inbox.md` beside
   `ingest.md`: list issues by label → parse → branch in the private repo →
   write file → cocktails: `derive_cocktail_moods.py --write` → `pytest`
   (alone) → food: `/tidy-drafts` → `ingest_preflight.py` → hand-back list
   to Helen as TIER 3 questions → commit with a bare `Fixes #N` (valid
   inside the private repo; a cross-repo trailer would not close it).
   Malformed envelope → comment on the issue, leave open, never guess.
4. **What the browser is told.** A single self-contained prompt file per
   site that a Claude web project can hold, generated by the same script,
   including the hand-back rules and an explicit "you cannot check X; say
   so" list.
5. **Security notes.** Why the issue channel and not a branch; why hooks
   are not bypassed; what a malicious or mistaken issue body could do to
   the parser (nothing more than fail).

**Opus then implements** 1–4 from the doc in two PRs: specs+test first,
then inbox skill.

**Also fix regardless of the design** (Opus, 30 minutes): `_cocktail_drafts/README.md`
is 0 bytes and `_food_drafts/` has no README. Each should say "schema lives
in helen-triages HANDOVER §4 / §9.3; this repo is private; never promote
copyright text" and nothing else. Private repo, branch, push allowed.

## 6. Shared/forked code consolidation (mixed)

**Finding.** Sharing is real: no `if site_key ==` branch exists in layouts,
includes, sass or JS (13 grep hits, all comments except `default.html` L20
and L115 and `back-to-index.html` L30). The two layouts, two palettes and
two index wiring scripts share no text and are forked by design (HANDOVER
§2.2 L287–294); leave them. The costly duplication is narrower:

**6a. Three JS helpers (Opus, 1–2 hours, low risk).**
`escapeHtml` and title highlighting: `filters.js` L466–503 vs
`cocktail-index.js` L273–301 (identical escape; highlight differs only in
mark class). sessionStorage index memory: `filters.js` L235–282 vs
`cocktail-index.js` L755–790. Move `escapeHtml` into `assets/js/assets.js`
(already the shared-helper home) as `HTF.escapeHtml`. Extract index memory
as `HTF.indexMemory.save(key, state)` / `.restore(key)` and have both
callers pass their own key and spec; `filter-state.js` already parameterises
by spec, follow it. Tests: `tests/js/*.test.js` under the stub-DOM harness
(HANDOVER §10.2); add one test per helper. Manually verify the back-button
restore on both indexes (HANDOVER §3 L493–499 records this exact failure).

**6b. Font stacks (Opus, 30 minutes, needs the contract amended).**
`_sass/food/_palette.scss` L34, L73 and `_sass/cocktails/_palette.scss`
L357–358 hold byte-identical `$font-headings` / `$font-body`. Either lift
them to `shared/_fonts.scss` as `!default` and amend
`SHARED_PALETTE_CONTRACT` in `test_site_config.py` (~L1438) so the contract
no longer demands them from each palette, or add a test that the two
strings are equal. The second is smaller and keeps the contract intact;
recommended.

**6c. CLOSED 2026-09-02 by the design session's merged PRs (#663 and
siblings), checked at 8191230.** `shared/_layout.scss` no longer hardcodes
`#dad7d8` anywhere but a history comment (L530); the wordmark reads
`@include lettering(display)`, `cocktails/_rule.scss` re-points the
`--lettering-*` tiers instead of overriding wordmark customs, and Helen
ruled the same day that the header tape word falls through to the shared
four-copy default on both sites (LETTERING.md §8). What remains literal in
the shared partial (`#ECE9EA` and the four-copy shadow defaults at
L704–732) was looked at on both sites and ruled. Do not touch. The
original text is kept below for the record only.

**6c (original). Hardcoded light ground in `shared/_layout.scss` (Fable, half a day, medium-high risk).**
`shared/_layout.scss` hardcodes `#dad7d8` for a light ground, so
`_sass/cocktails/_rule.scss` (126 lines) exists largely to override
`--emboss-shadow`, `--emboss-light`, `--emboss-stroke-w` and five
`--wordmark-*` customs (L60–73). `_sass/food/_rule.scss` (47 lines) exists
for the same reason plus `$color-label-stroke`, which is outside the
ten-variable contract. This is a site assumption inside a shared partial,
the failure shape of #374. Fix: promote the ground-dependent values to
contract variables (or derive them from `$color-bg`), delete the overrides.
Why Fable: `test_the_header_and_footer_are_identical_on_every_page`
compares rendered bytes, the emboss ceiling (§13.10.2) is measured not
argued, and the other session is currently doing design work in this area.
Coordinate with that session before starting.

**6d. Index filter panel — DROPPED, ruled by Helen 2026-09-02: "there
won't be any more panels or indexes."** Kept below for the record only;
do not do it.
`food/index.html` L68–196 uses `_includes/filter_group.html` (root-level,
one consumer). `cocktails/index.html` L101–213 hand-writes six blocks with
`.drink-filter` / `.drink-field-label` / `.btn-clear-filter`, different
label element (`<h2>` vs `<label>`) and different hide mechanism (`hidden`
attribute vs `visibility: hidden`). SCSS: food 1,393 lines across five
partials, cocktails 1,815 across two, bridged by 11 `index-*` mixins in
`shared/_rule.scss` L448–620. Parameterising the include is real work with
a real payoff only if a third index or more panel churn is expected. Helen
decides; if yes, do it after 6c so the mixins are stable, and guard with a
compiled-CSS diff test in the style of
`test_every_chrome_class_has_a_rule_in_every_site_stylesheet`.

**Do not touch:** `_layouts/recipe.html` vs `cocktail.html`;
`_sass/food/` vs `_sass/cocktails/` as directories; `cocktail-search.js`
(it imports from `ingredient-search.js` correctly); the two
`filter-state.js` tables; the second tape in `_cards.scss` L215–435 (§9.8
warns about it, but it is a design call and the design session owns it).

## 7. Handover hygiene

**Opus, one PR, small:**

- §2.3 L311–317 says cocktails' `$color-accent` is a grey placeholder.
  `_sass/cocktails/_palette.scss` L325 is `$color-electric-absinthe-deep`.
  Rewrite the paragraph.
- §2.2 L258 "assets/js/* (no script knows which site it's on)" is true of
  the logic and false of the file names (`cocktail-*.js`). Say so.
- Add `mood` to §9.3's schema block (WS1 step 3).
- `tests/test_cocktails.py` L15 says nothing is promoted; still true, but
  after WS2 the paragraph should describe the gate.
- `ship_tints` in `taxonomy.yml` is read by nothing (the file says so) and
  `test_every_ship_rung_has_a_tint` still enforces it. Retire both, or move
  the reasoning into a comment, once #511/#612 are closed.

**Fable, later, its own conversation:** the handover is 7,734 lines and is
itself the biggest maintenance cost in the repo. It is a journal that has
become a manual. A restructure into a short manual (rules, schemas,
contracts, how to run) plus a dated decisions log (the "why" paragraphs,
which are valuable and should not be lost) is a judgement-heavy rewrite
that should not be attempted by a session that has not read all of it.
Do not start this until WS1–WS5 have landed, because they change what the
manual half says.

## 8. Decisions, collected — RULED by Helen 2026-09-02 unless marked open

| ID | Question | Ruling |
|---|---|---|
| D1 | Flag names for drinks | Reuse all three: `rewritten`, `awaiting_fix`, `proofread`. `rewritten: true` is Helen's own claim that she has done her first pass (notes and tagline mainly; ingredients, suggestions, method too). |
| D2 | What drafts carry | All three, `false`, on every draft. |
| D3 | Does `proofread` gate publication? | **Yes, both sites.** Plugin changes to require `awaiting_fix: false` AND `proofread: true`. Five food recipes drop off live until proofread (named in WS2). |
| D4 | Amount-less ingredients | A top-up is a method step from `methods.yml`, never a note and never a new key. Rinse/rim steps need dictionary wording from Helen. |
| D5 | Drinks index cards show the gate flags locally, as food's cards do? | **Yes.** Same badges as food's cards, local build only (`show_drafts`), production never renders them. Reuse `_includes/recipe_badges.html` if it takes a drink's `meta` without a `site_key` branch; otherwise a cocktails include. |
| D6 | Parameterise the filter panel | **No.** No more panels or indexes. 6d dropped. |
| D7 | `tagline` backlog | Into the ingest hand-back list; a `"QQ"` tagline never publishes. |
| D8–D11 | Ingest inbox questions (draft-only `item`, label name, paste versus connector, `group:` in `garnish.yml`) | **All ruled 2026-09-02**, recorded in `INGEST_INBOX_DESIGN.md` §9: draft-only `item`; `ingest` / `ingest: <slug>`; paste for now; yes to `group:`. |

## 9. Suggested order and PR shape

1. PR A (public repo): WS1 + WS7 small fixes. Half a day.
2. Private-repo branches: WS1 step 4 (nine methods), WS2 migration, WS3
   mechanical fixes, WS4 step 1. Push allowed on those repos' `main` only for
   existing commits; Claude's work still goes on a branch.
3. PR B (public): WS2 gate + plugin change + index + tests. Before merging,
   Helen decides whether to proofread the five food recipes first.
4. PR C (public): WS3 tests + WS6a + WS6b.
5. Fable: WS5 design doc, WS6c. Then Opus: WS5 implementation, two PRs.
6. Helen: D5, WS4 rulings, rinse/rim method wording, `tagline` backlog.
7. Fable, later: handover restructure.
