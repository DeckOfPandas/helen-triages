# MANUAL

**Helen Triages** — a Jekyll mono-repo serving two personal decision-support
sites. **Food** answers *what shall we cook*, not *how do I cook*. **Cocktails**
is its sibling: real drinks, a schema, a designed index and drink page, and
**48 drinks live since 2026-09-10** — this said "nothing promoted to the live
site yet" until that day, which was true for the whole life of the collection
and is the single biggest thing to know that has changed.

**This file was `HANDOVER_v26.md` until 2026-09-06**, when it was split. v26
was 9,900 lines: about 2,000 of rules inside 7,800 of dated journal — what was
tried, what Helen ruled and why, what the file used to say before it said
this. Both halves are worth keeping and they wanted different readers:

- **This file is the manual**: what is true today, in the present tense, with
  no dates except where a date is the rule. Section numbers are v26's,
  unchanged, so every `MANUAL §n` in a code comment — and any older comment
  still saying `HANDOVER §n` — resolves here; a section that is now only a
  pointer keeps its number and says where to go.
- **`DECISIONS.md` is the journal**: every ruling with its date, its reason and
  Helen's words; every rejected alternative; every time this file was wrong
  and how it was found. Organised by the same section numbers. **Before
  re-opening anything, read its entry there** — §11.2's whole complaint is a
  settled question asked a third time.

**Do not trust this document over the code.** Verify anything you are about to
act on. If the code and this file disagree, the code wins, and the fix is to
correct this file, not to trust it harder next time (§11.2). Name files, never
line numbers, in any document here — every `file:line` ever written into one
was wrong within days.

**Ask Helen questions inline, in conversation, as they come up.** Do not
batch them, do not park them, do not pick the likely answer and carry on.

**Tag the issue in every commit message** — `Fixes #N` / `Closes #N` when it
resolves one, `Towards #N` / `See #N` when it touches one, the full
`DeckOfPandas/helen-triages#N` form from a nested drafts repo. `CLAUDE.md` is
the authority on git; §11 has what this file adds.

### Read this first, by what you are here to do

**To change the SITE:** §2.5 (one header, one footer — the biggest structural
fact here), §3 (the three layers), §4.0 (the gate flags — every recipe edit
touches them), §12 (the traps, the most re-used section), §13.11 (how a design
decision actually gets made: by Helen looking, never by argument).

**To ingest or fix drafts** — most sessions:

1. `.claude/commands/ingest.md` — the procedure, both sites, and the boundary
   (is the answer in the source, or in Helen's head?). The `QQ` conventions
   live there and nowhere else.
2. §4 for a food recipe's schema, §9.3 for a drink's, §4.0 for the flags either
   way, §5 house style, §7 food's taxonomy.
3. `model_instructions/PUBLISHING_A_DRINK.md` before touching anything in
   `_cocktail_drafts/to-promote/`.
4. §11.0.2 `/tidy-drafts`, §11.0.3 `/ingest`, §11.0.4 `/ingest-inbox` — which
   command fits how the material arrived.

`INGEST_ONE_RECIPE.md` and `INGEST_ONE_COCKTAIL.md` are NOT for you: they are
for a Claude with no repository. Read one only to fix it, or to finish a file
that came back from one (§11.0.3).

### The companion documents

Run `ls model_instructions/` rather than trusting this list.

| file | is |
|---|---|
| `DECISIONS.md` | the journal — see above |
| `START_A_SESSION.md` | the prompt Helen pastes to start a session; points here, at the journal and at `CLAUDE.md` |
| `SOURCE_ATTRIBUTION_SPEC.md` | the full `source` / `source_type` contract; §4 summarises and does not repeat it |
| `INGEST_ONE_RECIPE.md`, `INGEST_ONE_COCKTAIL.md` | for a Claude with NO repository. They stand alone because the closed vocabularies are small enough to print; every vocabulary block in them sits between `<!-- vocab:… -->` markers and is RENDERED from `_data/` by `scripts/build_ingest_vocab.py` (`--check` / `--write`), which `tests/test_standalone_docs.py` enforces. Hand-edit nothing inside a marker pair. Everything outside one is prose and must be kept in step by hand when §4, §5, §7, §9.3 or the attribution spec changes |
| `CLAUDE_WEB_INGEST.md` | the claude.ai Project that holds those two files, and what it is told |
| `INGEST_INBOX_DESIGN.md` | §6 the envelope an ingest issue carries, §8 its security argument, §9 the rulings; the rest is stubs |
| `PUBLISHING_A_DRINK.md` | the six steps a drink goes through from Helen's rewrite to the public repo, the word "final", the one-working-copy rule |
| `LETTERING.md` | the four tiers of punched-tape type; supersedes §13.4.1 and §13.10.2 |
| `LEOPARD.md` | the black-on-black print: generator, tones, Helen's rounds. **She holds it; ship nothing** |

**Three project slash commands, all in `.claude/commands/`**: `/tidy-drafts`
(§11.0.2), `/ingest` (§11.0.3), `/ingest-inbox` (§11.0.4). Each is a procedure
doc over a script in `scripts/` that reports and never writes.

**The cocktail standalone document leaves `generic` and `suggestion` as `QQ`,
always**, because a bottle's category is not derivable from the ingredient
printed beside it (§9.3.1) and because that is Helen's standing ruling for any
ingest; `mood` is `[]` because it is DERIVED (§9.3). The return journey for a
file from such a session is §11.0.3.

---

## 1. How to run it

```
jekyll-local        # port 4001, drafts visible — the working view
jekyll-prod         # port 4002, exactly what deploys — no drafts, no local switches
pytest              # content and structure checks; ONE session at a time
node --test                       # the JS suite, discovered from the root (§10)

python3 scripts/verify.py         # ALL FOUR CHECKS, and prefer this
```

**`scripts/verify.py` runs the two suites AND the two checks that get
forgotten** — `derive_cocktail_moods.py`, the only thing that says whether a
vocabulary edit silently moved a drink's moods, and `build_ingest_vocab.py
--check`, the only thing that says the standalone ingest documents still match
the data they are rendered from. Sessions have run the two test suites, called
the work verified, and missed both. One command, four lines of output, non-zero
exit if anything fails.

**`.node-runtime/` and `.gh-runtime/` do not come with a worktree**; they are
gitignored, like the two drafts repos (§9.1). Use the system `node`. **There is
no `gh` at all in a worktree** — `gh: command not found`, and it is not
installable from here — so anything `CLAUDE.md` describes as a `gh` command
(reading an issue, `gh pr create`) is the REST API instead, called with
`AGENT_GH_TOKEN` from a script in `tmp/`. Measured 2026-09-07, opening PR #808.
**Read the token from the environment at the point of use and never `echo` it
in any form** — not even a probe that cannot leak; the hook refuses all of
them (`CLAUDE.md`). To find out whether a credential works, use it and read
the status code.

**Never run two `pytest` sessions at once.** `test_rendered_pages.py` writes
throwaway `zzz-gate-` recipes into `_food_recipes/` (and drinks into
`_cocktail_recipes/`) to prove the gate fails closed, and deletes them after. A
concurrent run collects them as real files and reports schema failures that
vanish on a clean rerun; the tell is `zzz-gate-` in the test IDs.

Local URL: `http://localhost:4001/helen-triages/`, then `/food/` or `/cocktails/`.

**`jekyll serve` does not reload `_config.yml`.** Restart after any change to
it.

**IT DOES NOT RELOAD `_plugins/` EITHER, AND THAT ONE FAILS SILENTLY.** Ruby
plugins are loaded once at boot; the watcher rebuilds pages without them, for
as long as the server is up, with nothing in the log and no error on the page.
A server started before a plugin existed serves a site where that plugin has
simply never run. Helen lost a round of #801 to exactly this — the food
shopping list showed its number boxes and no totals, because
`_plugins/food_shopping.rb` had hung `shopping` and `portions` on nothing.
**Restart after adding or editing any file in `_plugins/`.** To confirm which
you are looking at, each plugin logs a line at build (`Costs:`, `Shopping:`);
no line means it did not run. Reproduce deliberately with
`--plugins <empty dir>`.

**`_config_local.yml` is where every local-only switch lives, and nowhere
else**: `show_source_wording`, `show_awaiting_fix`, `show_drafts`,
`show_costs`, `show_units` (all `true`), `pdf_downloads: false`, and
`output: true` on the `dev`, `food_drafts` and `cocktail_drafts` collections.
Production declares none of these keys, which is the whole mechanism (§9.1):
a template gates on the key existing, so it can never be true on the live
site. Never put a baseurl in it, and never move one of these keys into
`_config.yml`.

**Never write to machine `/tmp`.** Use this repo's gitignored `tmp/`. See
`CLAUDE.md`.

---

## 2. The mono-repo shape

One Jekyll build, one `_config.yml`, two sites:

```
https://deckofpandas.github.io/helen-triages/food/recipes/<slug>/
https://deckofpandas.github.io/helen-triages/cocktails/recipes/<slug>/
```

### 2.1 Why the collections aren't inside `food/`

Jekyll only discovers a collection at `_<name>` directly under the source root
(or one shared `collections_dir`); `food/_recipes/` is silently ignored. So the
site lives in the collection *name* and `permalink` does the routing. Run `ls`
before trusting this tree.

```
_food_recipes/       output: true    permalink /food/recipes/:path/
_food_magic_bag/     output: true    permalink /food/magic-bag/:path/   §4.3
_food_drafts/        output: false   permalink /food/drafts/:path/       local only; its own private repo
_cocktail_recipes/   output: true    permalink /cocktails/recipes/:path/ empty until a drink is promoted
_cocktail_drafts/    output: false   permalink /cocktails/drafts/:path/  local only; its own private repo

_layouts/     default.html (shared)   recipe.html (food)   cocktail.html (cocktails)
              magic_bag.html (food, §4.3)
_includes/    filter_group.html   recipe_badges.html   cocktails/ship.html
              icons/glasses/ (the published glass artwork, §9.11)   food/ (reference partials, §14)
_plugins/     publish_gate.rb   cocktail_costs.rb   cocktail_units.rb   cocktail_card_ingredients.rb
_sass/        shared/{_tokens,_base,_layout,_rule,_chrome,_fonts}   food/   cocktails/
_data/        sites.yml   accented_words.yml   chrome.yml   food/*.yml
              cocktails/{taxonomy,ingredients,bottles,glasses,methods,garnish,serve,costs,abv}.yml
_design_sources/  Helen's raw Inkscape glass drawings, committed as-is (§9.11, §9.15)
_dev/         local-only pages (output: false in production)
assets/css/   food.scss   cocktails.scss   longform-demo.scss
assets/img/   favicon.svg   chrome/   food/   cocktails/
assets/js/    shared — every script's LOGIC is site-agnostic (§2.2)
scripts/      generators, migrations and measurers, each with its own docstring
tests/        the pytest suite;  tests/js/  the node --test suite (§10)

food/index.html        permalink /food/
food/reference/*.html  permalink /food/reference/...   §14
cocktails/index.html   permalink /cocktails/
index.html             permalink /        a bare redirect to /food/
```

`food/` and `cocktails/` hold each site's **pages**, not their collections.

**Plugins.** Four Ruby plugins decide what a built page shows:
`publish_gate.rb` removes any gated document that does not carry an explicit
pass (§4.0, §9.1.1); `cocktail_costs.rb` and `cocktail_units.rb` do the price
and unit arithmetic once at build time (§9.3.5, §9.3.4);
`cocktail_card_ingredients.rb` builds a card's ordered ingredient line and its
search pool from one list (§9.10.1). **GitHub Pages' safe mode ignores
`_plugins/` entirely, without warning** — the gate would be gone and the build
green — which is why the workflow runs its own plugin-capable build and
`tests/test_site_config.py` asserts that it still does.

**The two drafts collections are each their own nested git repo**, gitignored
here and pushed to a private GitHub repo of their own:
`helen-triages-food-private` and `helen-triages-cocktails-private`. `output:
false` only stops Jekyll rendering them; the repo split is what keeps their
source out of a public repo whatever the build config says. A draft is promoted
to `_food_recipes/` — and so becomes public on the next deploy — only once it
contains no copyright material: Helen's own words, or sufficiently adapted.
The private split is what makes it safe to leave drafts unpromoted for as long
as needed, not a reason to promote them faster.

**Editing a file inside `_food_drafts/` or `_cocktail_drafts/` from this
working tree is normal** — Helen does it constantly — but `git status` here
never shows it and `git add` here cannot capture it. It is a separate, private
history. Do not "fix" the missing tracking and do not report draft edits as
at-risk work in this repo. `git remote -v` in `_food_drafts/` tells you which
remote a clone points at (the food repo was renamed on 2026-08-29 and GitHub
redirects the old name silently).

### 2.2 Shared versus forked

**Shared**, at the root, names neither site: `_layouts/default.html`;
`_sass/shared/` (`_tokens` structural, never a palette reference; `_base`;
`_layout` for `default.html` only; `_rule` the lettering mixins; `_chrome` the
header and footer's colour; `_fonts`); `_data/accented_words.yml` (house style
for both sites); `assets/js/*` (no script's LOGIC knows which site it is on —
it reads the site key from the page, §3); `assets/img/favicon.svg`;
`assets/img/chrome/`; `about.html`.

The JS claim is about logic, not file names: `cocktail-index.js`,
`cocktail-search.js` and `cocktail-make.js` load on cocktails pages only.
`assets/js/assets.js` is the shared one that matters — it loads first on every
page and holds `HTF.escapeHtml` and `HTF.indexMemory`, which both index
scripts use.

**THREE stylesheets import `shared/`**: `assets/css/food.scss`,
`cocktails.scss`, and `longform-demo.scss` — the third is an additive overlay
`<link>`ed by the two `/food/longform-demo/` pages on top of `food.css`, taking
only `shared/tokens` and `shared/rule`. **Grep for every `@import "shared/`
before assuming the count** — it has changed twice, and the one you forget is
the one that fails at the next build of the page you never visit.

**Forked**, because cocktails is philosophically distinct, not a reskin:
`_layouts/recipe.html` vs `cocktail.html` (a recipe is a procedure; a
cocktail is a formula plus a build — a full untriaged spirit bill, a glass,
garnishes, an ORDERED method); `_data/food/*.yml` vs `_data/cocktails/*.yml`;
`_sass/food/` vs `_sass/cocktails/`; `assets/img/food/` vs `/cocktails/`;
`assets/css/food.scss` vs `cocktails.scss`.

### 2.3 The palette contract

Shared partials use palette variables **by name and never define them**. Every
site palette owes all TEN: `$color-accent $color-bg $color-border
$color-clear-text $color-mood-root $color-surface $color-text $color-white
$font-body $font-headings`. Omit one and the build fails with "Undefined
variable" pointing at `_sass/shared/`, and only the short site breaks.
`SHARED_PALETTE_CONTRACT` in `test_site_config.py` checks the list by name;
`test_the_two_palettes_declare_the_SAME_font_stack` keeps the two font stacks
equal without lifting them into `shared/`.

**`$color-accent` means *this site's one "interactive / branded" colour*** and
is what let the chrome stop being forked (§2.5). Food's is
`$color-bright-magenta`; cocktails' is `$color-electric-absinthe-deep`, the
same value as `$color-mood-root`. A grey `$color-accent` is a symptom (the
lightness-only no-op of §12), never a state to leave.

### 2.4 `site_key`

`_config.yml`'s `defaults:` sets `site_key` per collection and directory. It
keys into `_data/sites.yml` (title, word, description, css, home, icon,
reference_links) and `_data/<key>/` (vocabulary). **A root-level page must
declare `site_key` in its own front matter** — the defaults assign it by
directory, and there are only two. A page with no `site_key` gets the
repo-level title and **no stylesheet**, silently:
`test_every_published_page_links_a_stylesheet` is what now notices.

**Decoration is opt-in, absence is silent.** `_data/cocktails/glasses.yml` is
the live example: a glass with no entry renders no icon rather than a broken
one. Missing keys are not 404s; a key pointing at missing artwork would be.

### 2.5 The shared chrome — one header, one footer

Helen's rule (#374): *"I don't want parity between two footers — I want one
footer for the whole site. And one header. Literally the same code and
assets."* "Shared" is a claim about three layers — markup, cascade, assets —
and is only true when all three hold (§12).

| Thing | Where |
|---|---|
| The one header and the one footer | `_layouts/default.html` — **no `site_key` branch anywhere in either** |
| Their structure | `_sass/shared/_layout.scss` |
| Their colour | `_sass/shared/_chrome.scss` — the only shared partial naming `$color-accent` |
| Their artwork | `assets/img/chrome/` (`tape/`, `hearts/`) |
| What is left of chrome config | `_data/chrome.yml` — `tape_count`, and nothing else |
| How a script fetches it | `HTF.chromeAsset(path)` (§3) |

`_data/sites.yml` keeps only what says WHERE YOU ARE. **The test before
adding a key: does this say where you are, or what the chrome is?** The
second belongs in `chrome.yml`, or nowhere. `RETIRED_SITE_KEYS` in
`test_page_links.py` fails if a removed key reappears.

**The nav is one row, the same everywhere**: one icon per site in
`sites.yml`, in that file's order, then the `??` about link at a literal
`/about/`. **The footer's reference block is a column PER SITE, gated on
having material** — food's two links appear on a cocktail page, and since
2026-09-06 (#529) a `[ COCKTAILS ]` column appears beside them, which cost no
template change: the loop always asked every site rather than food. The hearts
are pinned to grid column 2 so a second column cannot push them off centre.

**A link may be `local_only: true`, and it gates the LINK, not the page.** The
template drops such a link unless `show_local_reference_links` is set, which
only `_config_local.yml` declares — so production renders exactly what it did
before the key existed, and a site left with no surviving links draws no column
rather than an empty bracketed word. **It is half a switch and must be set and
cleared with the other half**, `published: false` on the page itself (§14):
a link with no page is a 404 in the one place that matters, and a page with no
link is reachable only by typing the URL. `test_site_nav_links_resolve_to_real_pages`
INVERTS for such a link rather than skipping it — it must point at a page that
IS unpublished — so clearing either flag alone goes red.

**Two guards, and neither substitutes for the other:**
`test_the_header_and_footer_are_identical_on_every_page` compares the
RENDERED HTML of the nav row and the whole footer across a food page, a
cocktails page and a recipe — byte-identical, no normalisation; if it ever
needs an exception carved into it, that exception *is* a second header
arriving. `test_every_chrome_class_has_a_rule_in_every_site_stylesheet`
compares the COMPILED CSS for every class the template and the icon partials
emit, checking divergence only.

**The one thing the chrome varies is the wordmark**, `[ FOOD ]` /
`[ COCKTAILS ]`, in `.site-title-link` above the nav row. §13.8 has its
mechanism and `wordmark_word`, the one page-level override.

---

## 3. The three-layer rule

```
VOCABULARY      what exists          _data/**/*.yml
PRESENTATION    how it looks         _sass/<site>/_palette.scss, _data/food/filter_sections.yml
BEHAVIOUR       what it does         assets/js/*.js
```

Each layer knows nothing about the layer above it. `_sass/<site>/_palette.scss`
is the only place any colour is written down (JS reads custom properties; SVGs
use `currentColor`). `_data/food/taxonomy.yml` is the only place food's tags
and stars are declared. `assets/js/assets.js` is the only place a base URL or
site key is derived, or a file fetched. Helen's principle: *the data model
must not assume anything about or impose anything on the data.*

**Split inside BEHAVIOUR once a module gets non-trivial**: pure algorithm
apart from DOM wiring, so Node can test it.

| Module | Holds | Tested by |
|---|---|---|
| `ingredient-search.js` | matching/ranking; `fold`, `getWords`, `orderByBand` (shared discipline, per-site bands) | `tests/js/ingredient-search.test.js` |
| `recipe-list.js` | shuffle (Fisher-Yates) and pagination maths — used by BOTH indexes since #694 | `recipe-list.test.js` |
| `filter-state.js` | what an index's filter state IS: `create(spec)`, `FOOD_FIELDS`, `COCKTAIL_FIELDS`, `arrivedByGoingBack`, `KINDS` | `filter-state.test.js` |
| `cook-schedule.js` | the timings arithmetic | `cook-schedule.test.js` |
| `back-link.js` | may this arrow use history? (§13.7) | `back-link.test.js` |
| `cocktail-search.js` | the drinks index's pool, ranking and matching (§9.3.3) | `cocktail-search.test.js` |
| `scale.js`, `shopping-list.js` | the scaler's arithmetic and the one amount parser (§9.13, §8.2) | `scale.test.js`, `shopping-list.test.js` |
| `food-shopping-list.js` | food's totals, by aisle, scaled by portions (§8.2) | `food-shopping-list.test.js` |
| `assets.js` | `HTF.escapeHtml`, `HTF.indexMemory`, `HTF.shortlist`, the asset helpers | `escape-html.test.js`, `index-memory.test.js`, `shortlist.test.js` |
| `filters.js` | DOM wiring, food index | `food-index-startup.test.js` (§10.2) |
| `cocktail-index.js` | DOM wiring, drinks index | `tests/js/index-harness.js` (§10.2) |

**`HTF.filterState` is the MODULE and `HTF.filterState.create(SPEC)` is a
BINDING of spec-bound functions**, and reading a name off the wrong one throws
silently in the browser while every pure test stays green.
`test_a_filter_state_binding_is_only_asked_for_what_it_has` reads both export
blocks; §10.2's harness runs the real page.

**`entriesMatchKey` is a word-PREFIX match** (#619): asking for `salt` must
not reach `unsalted butter`. Families that containment used to fake
(`nuts`) are carried by the VOCABULARY in `_data/food/ingredient_words.yml`,
never by loosening the rule; an `aliases:` entry cannot do it, because a row
is matched against raw `main_ingredients` and sees no alias.

**Three asset helpers, and each name carries its claim.** `HTF.asset(path)`
for genuinely shared files; `HTF.siteAsset(path)` for anything under a site's
own image directory (returns `null` on a page belonging to no site);
`HTF.chromeAsset(path)` for the header and footer's artwork, which never
returns `null`. `test_artwork_fetches_go_through_site_asset` bans an image
path built through `asset()`; it greps source and cannot tell a comment from
code, so do not quote the banned call in a comment.

---

## 4. Recipe front matter (food)

```yaml
title: "Lemony Cavolo Nero and Butter Bean Soup"
tagline: "It's fun to have a one-pot stew that is bright and acidic..."
source: "Adapted from Good Food, January 2026"
source_type: publication              # required; see SOURCE_ATTRIBUTION_SPEC.md
serves: "4"                      # xor makes: — never both. QUOTED
serves_estimate: 6               # #815; REQUIRED unless serves: opens with a
                                 # number. An integer, PEOPLE, UNQUOTED
prep_time: "20 mins"
cook_time: "1 hr 30 mins"
main_ingredients: ["cavolo nero", "butter beans", "lemon"]
star_ingredient: "greens"        # optional; ~a quarter are legitimately blank
internal_temp_ref: beef.tender_roast   # optional; see §14
doneness: medium_rare                  # optional, only alongside internal_temp_ref
tags: ["soup"]
ingredient_groups:
  - name: soup                   # bare noun — template adds "For the "
    items:
    - amount: "400 g"
      item: "butter beans, drained"
      note: "Jarred are worth it here."
    - item: "vegetable oil, to fry"
      incidental: true              # optional; see below
method:                          # xor method_groups: — never both
  - "Step text."
  - step: "Step text."
    note: "An aside."
method_short:
  - ""                           # [""] = not written. A block scalar = written.
notes:                           # always a list, never a blob
  - label: "Sinking"              # or a bare string
    text: "If it sinks, you added too much syrup."
meta:                            # EXACTLY these three, in this order — §4.0
  rewritten: false
  awaiting_fix: false
  proofread: false
```

**Every scalar string is quoted, and every list member too.**
`SCALAR_STRING_FIELDS` in `test_front_matter.py` is the list; `/tidy-drafts`
fixes it mechanically. **A schema example is copied more often than it is
checked** — keep this block in step with the tests.

**`meta:` is three flags and nothing else, in that order** (`rewritten ->
awaiting_fix -> proofread`, enforced by
`test_meta_block_is_exactly_the_three_flags_in_order`). `cooked_before` and
`date_last_edited` are retired; `tests/test_front_matter.py` carries a
tombstone for the promotion gate `cooked_before` used to be, and how to
restore it. `meta.claude_rewritten` (optional, #418) may sit alongside the
three on a DRAFT only: it records that Claude took a tidy-up pass, not that
the recipe is rewritten. **Only Helen sets `rewritten: true`.**

**`source_type` is required alongside `source`** — one of exactly eight
values, each dictating the shape `source` takes;
`model_instructions/SOURCE_ATTRIBUTION_SPEC.md` is the contract and
`tests/test_source_attribution.py` enforces it over recipes AND drafts. The
rule most likely to catch you: **the date is what separates a `publication`
from a `website`** — no date, it is the website. `source_type` renders
nowhere, so it is in `INVISIBLE_KEYS` (§4.0) and correcting it does not
invalidate a proofread.

**The staging folders are Helen's** — `_food_drafts/to-rewrite/` →
`to-cook/` → `to-promote/` record where SHE is with a recipe, which no flag
can say; all three are read by the draft suite. **Never move a file between
them unless asked, and never delete a `QQ original` line**: dropping a
superseded original is her own edit, made when she takes a file out of
`to-rewrite/` so what reaches the hob is readable. The folders and the flags
answer different questions and are not expected to agree.

**`short_name`, `instructions`, `published`, `date_added`, `difficulty`,
`nutrition`, `filling_note`, `headline_ingredient` are retired.**
`test_front_matter.py`'s `RETIRED` dict is the authoritative list with what
each was replaced by; do not resurrect one for a gap it used to paper over.

**The ingest contract, the `QQ` conventions and the three tiers live in
`.claude/commands/ingest.md`** and are not restated here. The one line:
*is the answer in the source, or in Helen's head?* `QQ` anywhere is Helen's
placeholder — never flag it, fix it or convert it; `test_no_qq_placeholder`
stops one reaching `_food_recipes/`. **Split `ingredient_groups` and
`method_groups` at ingest, once, and never regroup afterwards** — on a
published recipe regrouping is a content edit and takes `proofread` down
with it.

**Easy to get wrong:**

- `incidental: true` marks a cooking fluid (frying oil, greasing butter) that
  the Ingredients section skips and `main_ingredients` must not list
  (`test_incidental_not_in_main_ingredients`). Whether an oil is core is a
  judgement (unusual oil, stated smoke point, finishing drizzle → core), so it
  is an explicit flag. No published recipe uses it today; the mechanism stays.
- **An ingredient's quantity is its own `amount:` key, never inside `item:`
  text.** The highlighter is driven by `{% if item.amount %}` and never scans
  text, so `item: "~1 tbsp tamarind paste"` renders unstyled with no error.
  No test catches this; it is an authoring habit.
- `serves` **xor** `makes`; values may be prose in Helen's voice ("Depends on
  appetite") — never tidy one into a number. **That is exactly why
  `serves_estimate:` exists** (#815): the scaler needs an integer and her words
  must not be touched, so the estimate is a key of its own and the prose stays
  as written. Required wherever `serves:` does not OPEN with a number — 129 of
  423 files today, which is every `makes:` recipe plus the 20 whose `serves:`
  is prose or `QQ`. **`makes:` is never read as people however numeric it
  looks**: 950 ml is not 950 portions, and "12 slices" is not necessarily
  twelve people. It is an integer and UNQUOTED — a quoted `"6"` is a string
  and the plugin will not read it. **Produced at ingest**; ask Helen rather
  than guess when the source does not support one.
- **A RANGE TAKES ITS LOWER END** — Helen, 2026-09-07: *"when it's a range,
  pick the lower number because under-catering is worse for me than
  over-catering."* This sounds backwards and is not: the scale is portions
  wanted OVER portions made, so a smaller base gives a bigger multiplier and
  more food. It governs `serves: "4–6"` (the plugin already takes 4) and any
  `serves_estimate:` written from a range.
- **A COMPONENT RECIPE CANNOT ALWAYS BE ONE NUMBER, and the truth goes in a
  note.** `chocolate-ganache` glazes an 8-inch cake, drips a tall one, fills
  another, tops a Millionaire's shortbread, ices 12 cupcakes or makes 16
  truffles; `caramel` is 5 servings as a sauce or a 16-cm tin as a filling.
  Helen: *"I have no idea how to model this. Please add all this as a note on
  the recipe and I will tidy up later."* So `serves_estimate:` takes the
  commonest use and the note carries the rest, in her words. **Do not invent a
  schema for this** without her — see `DECISIONS.md` §8.2.
- `method` **xor** `method_groups`; both present means the second is dropped.
  Group names are bare nouns (`dressing`); method group names may be
  narrative phases; the page uppercases both.
- Cross-recipe links are markdown, **relative**: `[text](../slug/)`. Front
  matter is never run through Liquid, so a root-relative link cannot pick up
  the baseurl. `[[wikilinks]]` are retired.
- `notes:` items are `{label, text}` or a bare string; four or more is the
  signal to write body content instead (§4.1).
- `internal_temp_ref` (+ `doneness`) pulls a live figure from
  `_data/food/internal_temperatures.yml` — §14; opt-in, most recipes have
  neither.
- Filenames are stable by default; if a rename is clearly indicated, say so
  and ask.

**This is not the only shape a food document can take.** `_food_magic_bag/`
(§4.3) has its own schema and its own test file, so the rules above can stay
unconditional.

### 4.0 The two gate flags — READ THIS BEFORE EDITING ANY RECIPE

Both live under `meta:`. One decides what reaches the live site, the other
whether Helen's judgement still covers what is in the file (#331, #367, #667).

> ## THE RULE
>
> **If you edit a recipe file, set `meta.proofread: false` in the SAME commit.**
>
> Every edit. A typo, a hyphen, a note, a group rename. The flag does not
> record how big the change was; it records whether Helen has read what is
> now in the file. She is the last human judgement before a recipe publishes.

`test_agent_edited_recipes_are_not_marked_proofread` reads git history: if a
recipe's newest commit carries a `Co-Authored-By: Claude` trailer, the file
must say `proofread: false`. Three things about it:

- **It reads COMMITTED history**, so it fires on the run *after* your commit.
  Set the flag while you edit.
- **`BASELINE_COMMIT` grandfathers everything up to and including itself.**
  Moving it is Helen's to grant, never yours — only after she has reviewed a
  change line by line, and never to make a red test go green. The constant's
  own comment insists on measuring first: how many recipes is the rule
  holding at `proofread: false` right now?
- **Two narrower escape hatches, #417.** `INVISIBLE_KEYS` names keys nothing
  renders (`source_type`, `meta.rewritten`, the two retired meta keys) — a
  commit changing only those, body byte-identical, needs no flip, and
  `test_invisible_keys_are_really_invisible` scans the render surface
  (`_layouts`, `_includes`, `_plugins`, `assets/js`, `scripts` — **not pages**;
  `food/index.html` reads `meta.rewritten`, so a rename of that key WOULD
  invalidate proofreads) to keep the claim honest. `HELEN_CLEARED` names
  individual recipes she has cleared by hand. Read the constants' own
  comments before reaching for either.
- **"Nothing changed" and "I cannot tell what changed" are opposite
  answers.** A commit that reorders the `meta:` block is exempt (same file
  spelled differently); a guard that fails closed is right to only when it
  genuinely does not know.

**Stage explicitly. Never `git add -A`.** The repository cannot tell your edit
from Helen's; only the staging can.

**A recipe publishes only if it says `awaiting_fix: false` AND
`proofread: true`. Nothing else publishes.** Either flag missing, the old
hyphenated name, either value quoted as a string: all held back.
`_plugins/publish_gate.rb` removes the document from its collection at
`:post_read`, so it gets no URL, no sitemap entry and no place in
`site.food_recipes`; its log line names which flag held each page back. It
fails CLOSED — a new recipe does not publish until someone writes both flags,
and that is the right cost. `GATED_COLLECTIONS` is `food_recipes`,
`food_magic_bag` and `cocktail_recipes`; drafts and `dev` pages are protected
by `output: false` and need no gate. `show_awaiting_fix: true` in
`_config_local.yml` keeps flagged pages visible while you work.

The two flags are different facts and requiring both is not the "two fields
that must agree" mistake the plugin header refuses for `published:`. A page is
routinely `proofread: true, awaiting_fix: true` (read, one thing ticketed) or
`awaiting_fix: false, proofread: false` (an agent touched it since she read it).

**What `awaiting_fix: true` means to Helen — a bookmark, not "unfinished":**
*"'awaiting_fix' means I've proofread, but one small thing has been raised as
a ticket, meaning that once that's fixed I can look for just that one thing
rather than having to read the entire file again carefully."* So a flagged page
HAS been read — do not treat the flag as permission for further edits — and
`true` and ABSENT are different states even though both hold a page back:
`scripts/tidy_drafts.py` reports a draft with no flag rather than writing
`false` into it.

**Always `awaiting_fix` with an underscore.** Liquid parses
`page.meta.awaiting-fix` as SUBTRACTION, so the hyphenated spelling publishes
the flagged page; `test_no_recipe_uses_the_old_hyphenated_awaiting_fix_key`
guards `_food_recipes/` and nothing scans drafts, so copying an old draft as
a template is the hazard.

**Guarded from every direction** because every failure mode is silent:
mechanism tests in `test_site_config.py`, data tests in `test_front_matter.py`,
and `test_rendered_pages.py` builds a real production site and asserts
flagged absent AND unflagged present. Jekyll's safe mode (a Pages-native
build) ignores `_plugins/` entirely — §2.1.

The one exception to "she is the last touch": a trivial fix she requests,
which Claude makes with `proofread: false` in the same commit, and she
re-reads the affected line and sets `true` herself. The drink side of the same
rule is §9.1.1.

### 4.1 Body content below the front matter (rare)

The Markdown body after the closing `---` renders verbatim inside
`.recipe-body-content`, between Notes and the source footer. Two published
recipes use it (the ganache, Henry's hollandaise). **It continues the recipe;
it does not become a blog post**: section headings in it are peers of
INGREDIENTS / METHOD / NOTES, which needs the exact raw HTML
`_layouts/recipe.html` generates —

```
<h2 class="recipe-section-heading"><span class="section-heading-text">Tips</span></h2>

- A bullet list here parses as normal markdown again.
```

— blank-line-separated so kramdown parses the surroundings as markdown. A
subtitle under a peer heading is `<p class="recipe-section-subtitle">`. A bare
`## Heading` gets a sane fallback and will not match the page; that mismatch
is what peer status is for. Reading width matches Method (no cap), not Notes.

### 4.2 A bullet list inside one method step

A `|` block scalar with blank lines around the list embeds a real markdown
list inside one step. `.method-full li` is `position: relative` with an
absolutely positioned number (not flex, which lays a nested list beside the
number), and `.method-full ul li` resets `counter-increment` so nested bullets
do not advance the step counter. Grouped methods compose the group indent with
the number column via `calc`.

### 4.3 The magic bag — dishes with no recipe

`_food_magic_bag/`: dishes Helen cooks from memory and will never write up.
Answers the README's problem #1 for the half of the set the site could not
hold.

```yaml
title: "Fridge-end fried rice"
tagline: "The thing that happens to yesterday's rice."   # key required, value may be ""
main_ingredients: ["rice", "eggs", "spring onions"]      # what makes it findable
tags: ["fakeaway"]                                        # OPTIONAL here
ingredients:                                              # flat, bare strings, INCOMPLETE
  - "cold cooked rice"
  - item: "dark soy sauce"
    note: "Light soy makes it taste thin."
notes:                                                    # optional, {label, text}
  - label: "Rice"
    text: "Has to be cold and a day old."
meta:
  awaiting_fix: false                                     # TWO flags, not three
  proofread: false
```

**It is not a variant of the recipe schema.** Every structural guard in
`test_front_matter.py` is unconditional and stays so; this shape gets
`tests/test_magic_bag.py`. Five required keys, and the shortness is the
feature: capturing a dish has to be nearly free. `tags` is optional. `meta:`
is `awaiting_fix` then `proofread` — `rewritten` has no meaning without a
source; `proofread` is required because the gate reads it and the magic bag
must be able to publish. **No standing caveat on the page** — Helen: *"I am
the user, and I know exactly what is going on."*

Four things `food/index.html` handles for it, three of which fail silently:
every row is gated on `recipe.meta.rewritten or site.show_source_wording`, and
the magic bag is exempted in both places (the row `if` and the survivor
count), not papered over with a fake `rewritten`; the derived ingredient
index reads `ingredient_groups`, so a second loop reads `ingredients` (an
empty vocabulary would hand back every dish on an exclusion — *fine to include
ON, dangerous to exclude BY*); a `magic bag` badge on the row, shown in
production, because it says what you are about to CLICK. `test_no_recipe_only_keys`
catches the halfway state of a dish being written up in place — promotion
means moving it to `_food_drafts/` and taking the recipe schema.

**Open**: whether the index needs a way to include or exclude the magic bag in
production (#507 — Helen: *"I need to think about that more"*); whether
`magic bag` is the right reader-facing word and permalink (#508); the README
still describes two collections (#509, her voice).

`.recipe--magic-bag` exists for one spacing consequence (the badges would
otherwise sit against the tagline on a page with no metadata grid) and is not
a hook for making these pages look different.

---

## 5. House style

Unicode fractions (`½`). Em dash for `--` in prose (not commit messages — §11).
**En dash for a number range** — `3–4 mins`, `170–180°C`, `36–40% fat`,
scoped by what a READER SEES, so `cook_time` counts (`test_number_ranges_use_en_dashes`
reads the whole file; ISO dates are blanked first). `→` for arrows. `°C`
always, **fan oven only** — check which figure of a printed pair *is* the fan
one before deleting the other. British spellings. Titles use `and`, never `&`.

**It reaches prose pages, not just recipes** (`tests/test_prose_pages.py`):
the about page, the index pages and the reference pages, including the words
those pages render out of `_data/food/*.yml`.

**It stops at a `QQ` line and does NOT stop at a `QQ Claude` line.** A step
beginning `QQ` is still the SOURCE's wording awaiting a rewrite; correcting
its dash edits someone else's words. `QQ Claude` is our prose and is held to
house style like anything we write. Both `conftest._QQ_LINE` and
`scripts/tidy_drafts.py` match `QQ\b(?!\s+Claude\b)`, as a PREFIX — a finished
step that merely mentions the marker is checked like any other prose.

**Time**: `prep_time`/`cook_time` use `20 mins` / `1 hr 30 mins` / `2 hrs`;
prose uses `mins` / `hours` / `seconds`; only numeric quantities abbreviate.
`cook_time: "Until done"` for family bakes with no stated time. **`Estimated
N mins` must never appear in a published recipe** — a poor estimate
publishes, a `QQ` blocks; if one turns up, leave it for Helen.

**Accents** via `_data/accented_words.yml` (repo root — house style for both
sites): a curated unaccented→accented map plus a `no_accent:` list. Prose
only — never slugs, filenames or `source:` (reproduced as the publication
spells it). The test for a mechanical fix: does it lose information or make a
judgement? `1/2` → `½` does neither; a spelling is a word, not a character,
and is reported rather than fixed.

---

## 6. `main_ingredients`

Unordered set in the data; ordering is presentation (`_data/food/pantry.yml`,
a BARE LIST of pantry staples sunk to the end and dimmed — exact lowercase
match). **Sweet/baking — completeness test**: everything whose absence breaks
the recipe, no cap. **Savoury — substitution test**: would I improvise around
a gap here — the protein, the fat or liquid that defines the character,
anything you would have to go and buy, the vegetable that is the point.

> **THE CAP OF EIGHT IS A FIRST-PASS GUIDE AND HAS BEEN READ AS A BUDGET. BE
> GENEROUS.** Helen's own recipes run to fourteen; ingested ones stop at five
> and she adds to them by hand, *"which is plainly silly"*. The number is an
> OUTPUT of the test, never an input. Not mechanically enforced, deliberately.

Cheeses use the bare name where it stands alone (cheddar, feta, comté); keep
"cheese" only where the qualifier means nothing without it (blue cheese, cream
cheese). Lowercase; `test_no_main_ingredient_spelling_collisions` enforces it
across recipes and drafts.

---

## 7. Taxonomy (food)

Declared in `_data/food/taxonomy.yml`; adding a term there is all that is
needed, and the file's own comments carry the reasoning behind every
retirement and reinstatement.

**Star ingredients** (optional): beef, chocolate, duck, eggs, fruit, game,
greens, lamb, oily fish, pork, poultry, root veg, shellfish, white fish. **It
is the one thing the recipe is ABOUT**; about a quarter of the collection
correctly leaves it blank. Egg as a binder or leavening is not `eggs`; a dish
literally about the egg is. Squash is `root veg`. `retired_star_ingredients`
makes a retired value fail with its reason rather than blend into "not
declared".

**Mood** — *what you feel like eating, a craving*: bakes, carbs party,
cheese-tastic, dessert, drinks, fakeaway, hot snack, ice cream, nibbles,
one-handed food, salad, showstopper, soup, sweets, virtuous.
**Practicalities** — *what the occasion demands of you, regardless*: breakfast,
extras, festive, freezable, make-ahead, no-cook, starter.

**Co-tags.** Only `ice cream → dessert, make-ahead`. Test for adding another:
sound when a ROLLUP or a genuine AFFORDANCE, unsound when DEFINITIONAL.

**Meanings you would not guess:** `one-handed food` — eat curled on the sofa;
anything that rolls, spills or needs chasing is out (thick spoonable soups in,
noodle soups out). `no-cook` answers "can I put this on the table without
cooking?" — a spice blend is uncooked and a useless answer, so it stays
untagged. `make-ahead` — a substantial part is genuinely finished ahead; a
bake that merely keeps is not, and an overnight marinade is not. `freezable`
and `make-ahead` are separate axes. `drinks` is anything drinkable that is not
a cocktail. `virtuous` is narrow: lean protein, or genuinely veg-forward with
a wine or citrus sauce doing the work.

**Standing per-recipe calls, not to be "fixed" for consistency**: the
lemony cavolo nero soup is not tagged `soup` (its own tagline calls it a
stew); `pancetta-white-bean-stew` is not `freezable` though its two sibling
stews are; the griddle cakes are `root veg`. `DECISIONS.md` §7 has each.

**"Declared" and "filterable" are the same thing.** `recipe_badges.html`
builds a recipe page's badges from `_data/food/filter_sections.yml`'s
`tag_groups`, so a tag in `taxonomy.yml` whose group is absent there renders
nowhere. There is no way to keep a tag as page information without a filter
button, and that split was proposed and rejected: if a fact matters while you
READ, a `notes:` line says more than a badge; if it matters while you BROWSE,
it needs the filter. Do not build it to make the ontology tidy.

---

## 8. Ingredient search architecture

Confirmed as earning its complexity: several hundred distinct main
ingredients, most in exactly one recipe — useless as a pantry filter, exactly
what a RECALL lookup needs ("the one with the sorrel"). Title search stays
too.

`_data/food/ingredient_words.yml` is the single source;
`assets/js/ingredient-search.js` the only reader. Six lists, each solving a
different problem: `modifiers` (strip a leading word before matching),
`stopwords`, `never_family` (a head word that never earns an `(all)` button —
a graveyard of near-misses considered and rejected; check the real data
before adding to any list), `family_exceptions`, `singulars`, `synonyms`
(curated families — typing toward the key widens to every member).
`measure_phrases` strips container words and matches `phrase + ' '`, which is
load-bearing (`can ` cannot fire on "cannellini"); `normaliseEntry` runs
trailing → quantity → measure → modifiers, so "juice of 2 lemons" is an
`aliases` job, not a phrase.

**Core ranking rule:** a match at the very start of the whole string outranks
a match real only once you check every word, which outranks one that is real
but not a family match. Get this backwards and "chi" ranks chocolate chips
beside chicken breast.

### 8.1 Two pickers, one code path, very different input

**They are not two implementations.** Both call `IS.buildMasterList` with the
same vocabulary. The **include** picker reads `data-ingredients` ←
`main_ingredients`, clean single words; the **exclude** picker reads
`data-all-ingredients` ← every `ingredient_groups` item, prose written for a
cook. #52 chose the harder source deliberately (`main_ingredients` is a partial
hint), so the answer to a bad exclude candidate is always to teach the
vocabulary, never to fork the logic.

**Measure production, not your local build.** The local build folds in every
draft and every unrewritten recipe, and a draft's `item:` lines are the worst
input the picker ever sees; they are rewritten before publishing, so a
vocabulary entry aimed at one is work done twice. When the exclude picker
"breaks" with dozens of candidates for three letters, it is almost always
drafts Helen added that evening — check mtimes, and leave it. If the working
view ever becomes genuinely unusable, the option costed and NOT taken is to
build the picker's vocabulary from published recipes only; that is Helen's
decision. To measure: build both configs into `tmp/`, pull
`id="ingredient-vocabulary"`'s JSON and every `data-all-ingredients` (split on
**`|`**, not a comma) out of `food/index.html`, and run
`IS.create(vocab).search('chi', IS.buildMasterList(entries))` in Node.

**"One code path" is a claim about the algorithm, not the pickers** (#390):
both builders must apply the word-match class and both call sites pass the
flag; `test_both_ingredient_pickers_mark_their_word_matches` checks it. The
emphasis is a WORD-PREFIX match — the entries you meant, against what the
vocabulary brought along. One treatment, two hues, via `@mixin
word-match-emphasis($colour)`; and the exclude hover is a deeper cut than its
active tone on purpose, guarded by comparing relative luminance so the
DIRECTION is asserted.

### 8.2 The food shopping list and its scaler — #801

**The last thing on the food index, shown only while the shortlisted-only
filter is on** — the same rule the drinks list follows (§9.13), and the literal
reading of *"the food recipe shortlist page"*. It is a deliberate copy of
cocktails' shopping list, class for class, because Helen's brief was *"I would
like all the same features"*. **Costing is the one feature not copied**: she
ruled it out for food.

**THE SCALER COUNTS PORTIONS, NOT BATCHES**, and that is the difference from
the drinks. A drink's box counts glasses; a recipe's counts PEOPLE, so four
portions of a recipe that serves six is ×0.67 and the fractional multiplier the
drink scaler refuses (§9.13, whole recipes only) is ordinary here. That is what
makes the serving size Helen asked to be guessed load-bearing: it is the number
the portions are divided by.

**Nothing is rounded coarser than a gram** — Helen, 2026-09-07: *"don't round
to 10 g or 5 g, round to 1g"*. Two thirds of 200 g is 133 g. Spoons and counts
keep vulgar fractions instead (`⅔ tsp`, `3⅓`), which is NOTATION and not
rounding — ⅔ prints for exactly two thirds and never for 0.7.

**Four files, and the split is the usual one.**

| file | is |
|---|---|
| `_data/food/aisles.yml` | Helen's ten aisles in shop order, and a KEYWORD table. **The longest keyword wins**, matched on whole words — `milk` is dairy and `coconut milk` is a tin, `garlic` is produce and `garlic paste` is a jar. An exception is an entry, never a precedence rule. `never:` (water, cold water, ice) matches the WHOLE name and drops the ingredient |
| `serves_estimate:` in each recipe | how many PEOPLE it feeds, where `serves:` says no number (#815). `_data/food/servings.yml` held these outside the files until 2026-09-07 and is deleted |
| `_plugins/food_shopping.rb` | assigns the aisle and resolves the portion count at BUILD, and hangs `shopping`, `portions`, `portions_estimated` on every document. The page is handed the answer and never the table |
| `assets/js/food-shopping-list.js` | the totals. Pure; the DOM half is `filters.js` |

**Why the guesses are not in the recipes.** A number in 44 files means editing
44 files, and §4.0's rule then un-proofreads more than half the collection to
add a figure Helen never wrote. One reviewable file instead, and not a recipe
touched.

**The amount parser is still the ONE parser** (§9.13). `shoppingList.parseAmount`
learned vulgar fractions, ranges (`30–50 g`), a leading `~`, and plural units
(`2 cloves` → `clove`), plus `splitParenthetical` for `1 tbsp (6 g)`. **Nothing
the cocktails collection writes parses differently**, and a test says so by
name — check it before widening the parser again.

**Grams and millilitres are the only units totalled in**; kg, l and cl fold
into them and come back for display, so `1½ l` plus `500 ml` is `2 l` and a
twelfth of a litre is `125 ml` rather than `0.125 l`. This is NOT the
conversion `shopping-list.js` refuses — that rule is about units with no
defined relationship (a dash is not some number of ml). `tbsp`, `oz` and every
bare count are left where they are, because those would need inventing.

**EVERY RECIPE COUNTS PEOPLE, and that took two goes.** The box is portions:
four portions of a recipe that serves six is ×0.67. A recipe whose `serves:`
states no number carries **`serves_estimate:`** in its own front matter (§4),
produced at ingest from the recipe's own words — 129 of 423 files. An estimate
is printed with a `~`, which is the only thing saying a figure was reasoned
rather than written down.

**WHAT STOOD HERE FOR A FORTNIGHT, so you do not rebuild it.** A recipe with no
portion count got a box counting BATCHES (×1, ×2) with a `×` beside it, on the
reasoning that `makes: "About 750 ml"` cannot become people without inventing a
portion size. Helen killed it: *"increasing it to 50+ does nothing either and
clearly 750 ml of gelato doesn't feed 50."* **It was honest and it was wrong**
— "set all to N portions" could not reach those recipes, and a control that
means something different on some rows is worse than a guessed number.
**Batches were a workaround for missing data, and the fix was the data.**
`_data/food/servings.yml`, which held the estimates outside the recipes for the
same fortnight, is deleted: one home for the figure, beside the words it
estimates from.

**A recipe with NO portion count gets no box at all** — not a box that does
nothing. That is what a new recipe looks like between being written and being
given its estimate, and the panel names the key to add. This feature shipped
three silences in one day before the rule stuck: a control that did nothing, a
total that would not change, and a panel that rendered empty.

**`k` says WHICH KEY the yield came from**, and the blob carries it for the
label: `serves` and `makes` are exclusive (§4), so a page printing the text
behind a fixed word is right for half the collection. It read
`serves About 750 ml` until 2026-09-07.

**Do not print the yield beside the recipe name.** Helen, with a screenshot of
`7  Moules Marinière serves 4`: *"This screenshot makes it look like I'm asking
for 28 portions of mussels."* A number at each END of a short line reads as one
expression however the middle is styled, and this row has to open with a number
— so there is no styling fix, and the yield lives in the input's `title` and
`aria-label`. If it ever has to be seen, it goes on a line of its own.

**Two folds you will trip over.** A plural ingredient NAME folds to its
singular for the grouping key (`onion`/`onions` are one line), reusing
`foldUnit` rather than a second rule; the LABEL is the first spelling seen. And
a cross-recipe link (`[grandma's lemon curd](../…)`) is KEPT here and forced to
`other`, where §12's exclusion index drops it — different questions, different
answers, stated in both files.

**`HTF.shortlist.portions` is a THIRD localStorage key**, not `glasses` renamed:
a missing glasses entry is one glass, a missing portions entry is *however many
this recipe makes*, which only the build knows — so `1` is a real, storable
answer here.

**Where it is tested.** `food-shopping-list.test.js` (the arithmetic),
`shopping-list.test.js` (the parser, including the no-change-for-cocktails
claim), `food-index-startup.test.js` (the wiring, §10.2),
`tests/test_food_shopping.py` (the two data files),
`tests/test_rendered_pages.py` (the **only** place the Ruby matcher can be
checked — it caught `garlic cloves` landing on the spice rack).

---

## 9. Cocktails

**Cocktails does not share food's data model and is not going to.** A food
recipe is a procedure; a cocktail is a formula plus a build. The two share the
outer layout, the type scale, the palette contract and house style, and
nothing else. Read this section, not §4.

### 9.1 Nothing about the DRINKS is public. The shell is.

Two independent mechanisms, and neither is redundant: `_cocktail_drafts/` is
its own git repo (`helen-triages-cocktails-private`), gitignored here; and the
collection is `output: false` in `_config.yml`, `output: true` only in
`_config_local.yml`, so drafts render at `/cocktails/drafts/<slug>/` on :4001
and nowhere else. (#235 is the case where `output: false` held and an index
still LISTED drafts, linking to URLs never written — `output: false` stops
Jekyll writing a document; it does not remove it from `site.<collection>`.
The guard is a key that exists only in `_config_local.yml`, `show_drafts`,
never a check on the collection being non-empty, which is true in production
too.)

**What IS public**: `_layouts/cocktail.html`, `_sass/cocktails/`,
`cocktails/index.html`, every file in `_data/cocktails/`, the glass artwork.
So the field names and the vocabularies are visible even though no drink is.
Helen accepted that trade.

**To get the drinks into a worktree: CLONE.** Helen's SSH key is per-account,
so it reaches the private remote from anywhere:

    git clone git@github.com:DeckOfPandas/helen-triages-cocktails-private.git _cocktail_drafts

A worktree starts blind, and `tests/test_cocktails.py` skips the tests that
read a drink, reporting green. A symlink half-works (the Edit/Write tools
refuse it and writes land in Helen's tree); a copy goes stale silently. **Clone
freely to READ; while a promotion batch is open there is ONE working copy to
WRITE** — `PUBLISHING_A_DRINK.md`. The food repo is
`helen-triages-food-private`, same command.

**Always `git fetch` immediately before any run whose result you will act
on** — before reporting a failure, before calling a change safe, before
pushing. Not at the start of the session: a clone is stale the moment anyone
merges, which with two agents is several times an afternoon, and the symptom
is a handful of `test_cocktails.py` failures naming real drinks that read
exactly like a regression.

    cd _cocktail_drafts && git fetch origin && git rev-list --count HEAD..origin/main

A non-zero answer means the next red test is probably not yours. To bring a
test clone up to date without standing on `main`: `git checkout --detach
origin/main` (or `origin/<branch>` when the public tests want data on an
unmerged private branch). `git fetch origin main:main` refuses on a
checked-out branch and a merge onto `main` is refused by the hook.

**The API token is a different channel.** `AGENT_GH_TOKEN` — the only one
since `GH_TOKEN` was deleted on 2026-09-09 — carries Issues, pull requests
and contents on all three repos. **The old asymmetry is gone**: the retired
fine-grained token read file contents on neither private repo (403), which is
why several rules here used to say "git can, the API can't". They now reach
the same places. **Pushing needs no ask in any of the three repos**
(`CLAUDE.md`, 2026-09-07); committing or merging onto any `main` is still
forbidden, hook-enforced. **MERGING A PR IS STILL NEVER YOURS — but it is no
longer the token that stops you**, it is the rule, because a classic
`repo`-scoped token can merge. Treat it as absolute.

**The naming trap**: `.gitignore` matches by directory name, so a renamed
drafts directory is un-ignored and stageable in the public repo.
`test_every_drafts_collection_is_gitignored` derives its patterns from
`_config.yml`.

**`_cocktail_recipes/` HOLDS 48 DRINKS SINCE 2026-09-10, AND IS PUBLIC.** This
paragraph said the directory "does not exist on disk" and that "nothing is
promoted into it yet" for the whole life of the collection; both were true
until the deployment and neither is now. §9.1.1 is the gate that let them
through, and it is no longer a formality — every one of those 48 is
`proofread: true`, so **an agent editing one takes it off the live site** in
the same commit that sets the flag back (#367).

**`_cocktail_drafts/to-promote/` IS EMPTY**, which is the other half of the
same fact and the more useful one day to day: everything Helen has read has
moved out, so anything that appears in that folder is genuinely waiting for
her. She asked for it in exactly those terms — *"then I don't have to fish
through one by one to find out which I still need to proofread"*.

**A PROMOTED DRINK IS READABLE BY A PUBLIC TEST, which several tests were
written to survive not having.** `_load_published()` and
`test_agent_edited_drinks_are_not_marked_proofread` both skip while the
collection is empty; they run for real now. If one of them starts failing, it
is not necessarily new — it may be a check reaching data for the first time.

### 9.1.1 The drinks publication gate — three flags, and the index that reads them

**§4.0 is the authority on what the flags MEAN**; this is what differs for
drinks (#668). Every drink carries `meta.rewritten`, `meta.awaiting_fix` and
`meta.proofread` — food's names, in food's order, after the two drink-specific
keys — so a drink's `meta:` block is exactly:

    meta:
      made_before: true
      ship: "yes"
      rewritten: false
      awaiting_fix: false
      proofread: false

**`rewritten: true` is Helen's CLAIM, not Helen's keystroke** — it *"shows me if
I have rewritten it, not an agent"*: the notes and the tagline mainly, though
her first pass also checks ingredients, bottles and method. **The one place an
agent may type it is `_cocktail_drafts/to-promote/`**, where the MOVE is how she
claims it (`PUBLISHING_A_DRINK.md` step 2). Nowhere else, on either site.
What keeps a draft private is `output: false`, not these flags. The counts
(how many `rewritten: true`, how many staged) are a worklist — re-count, do
not quote.

**Migrating a drink field**: a textual insertion by script (never a YAML
round-trip), so `git diff --numstat` reads N/0 on every file — and bump
`SCHEMA_VERSION` in the drafts repo in the migration commit and `REQUIRED` in
`tests/drafts_schema.py` in the commit that tightens the rule (§10, #624), so
a mismatch is one failure naming which side is behind.

**The gate itself needed no change**: `cocktail_recipes` was always in
`GATED_COLLECTIONS`. `tests/test_cocktails.py` guards the data —
`test_the_gate_flags_are_real_booleans` and
`test_no_drink_uses_the_old_hyphenated_awaiting_fix_key` over both
collections; `test_agent_edited_drinks_are_not_marked_proofread` over
`_cocktail_recipes/` alone, importing `_git`, `AGENT_TRAILER` and
`_only_invisible_keys_changed` from `test_front_matter.py` rather than
copying them. Its `COCKTAIL_BASELINE_COMMIT` grandfathers nothing by
construction while the collection is empty.

**`cocktails/index.html` has food's shape**: `all_drinks =
site.cocktail_recipes`, the drafts concatenated only under `site.show_drafts`,
and every mood loop, the count and the sort read `all_drinks`. Production
renders "Nothing to see here yet" because the collection is empty, not
because the template refuses to look.

**The cards do NOT show the flags** — the same ruling as food's #562: a
work-state note on every unfinished row is a to-do list down the side of the
page you use to decide what to drink. The flags live in the file and in the
build log. `test_the_gate_covers_a_promoted_drink` in `test_rendered_pages.py`
writes two `zzz-gate-` drinks into `_cocktail_recipes/` differing only in
`proofread`, builds, and asserts one URL exists and the other does not — so
the drink leg is exercised on a bare CI checkout with no private data (#624).

### 9.2 The source data

`tmp/2021-01-29 Cocktails - Book.csv`, one row per ingredient, drink-level
values on the drink's first row except multi-value ones (method, garnish,
notes, serve) which spill down. **Read it with a CSV parser, not by eye**; it
is a starting point, not a source of truth, and it is not uniform. Its
truncations are missing text, not mysteries: the fastest route to one is a
second source (§9.2.1).

### 9.2.1 Ingesting from photographs — the second source

Helen photographs book pages into `tmp/inbox-cocktail-recipes/` (and
`tmp/inbox-food-recipes/`) and a session transcribes them; `/ingest` (§11.0.3)
is the procedure. Four rules that came out of the first batches and still
bind:

- **Resolve every recipe by opening its photo.** Do not infer a batch's
  contents from its folder; batches hold pages from several books and
  edge-of-frame captures Helen did not mean to include.
- **A drink already in the collection may share a name and not be the same
  drink.** `sazerac` and `sazerac-death-and-co` live side by side — Helen:
  *"name it 'Sazerac (Death & Co)', leaving mine as simply 'Sazerac'."*
  **Compare the formula, never the title.**
- **The source is the best audit the collection ever gets, and none of it is
  changed.** A citation missing, an ice instruction that disagrees, an amount
  out by a factor of 24: recorded beside her figure, never applied — §9.4.1,
  the site is canon. And once she has ruled, stop tracking it: a QQ that has
  been ANSWERED becomes a plain note recording the answer; only a QQ that was
  wrong to ask gets deleted.
- **Hand back the bottles.** A bottle the book names that `bottles.yml` does
  not declare is a note, never a declaration (§9.3.2). What a photograph
  cannot give you — a method cut off mid-sentence, an infusion on a page
  nobody shot — is flagged in the drink and raised as an issue, never
  reconstructed.

**A photograph is not the only way in.** Helen also hands a source to the
claude.ai Project (`CLAUDE_WEB_INGEST.md`) and pastes what comes back into an
`ingest` issue on the private repo; `/ingest-inbox` (§11.0.4) is the consumer,
and it enforces the Sazerac rule mechanically by comparing a fingerprint of
the amounts.

### 9.3 Cocktail front matter

```yaml
title: "Sazerac"
tagline: "QQ"                    # the one line of prose; QQ until written
glass:                           # LIST, not scalar
  - "old fashioned"              # canonical spelling; `rocks` fails a test — §9.11.1
garnish: []                      # LIST, declared vocabulary — §9.12.1
  # ["no garnish"] = decided, [] = unfilled.
ingredients:                     # FULL list, untriaged, in build order
  - amount: "15 ml"              # the ONLY quantity field, NO US UNITS, and
                                 # NEVER a bare number — the unit is required
    generic: "moderately aged Jamaican rum"  # the vocabulary; see §9.3.1
    suggestion: ["Appleton Estate Signature"]  # the bottle. ALWAYS A LIST — §9.10
                                 # (`item` goes here on a FRESH ingest, beside
                                 #  generic: "QQ", and goes when the category is
                                 #  filled in — §9.10)
  - amount: "15 ml"
    generic:                     # a LIST means "or", never "and" — §9.3.1
      - "lightly aged and filtered rum"
      - "clear blended multi-region rum"
    suggestion: ["Havana Club 3"]
    note: "Whichever you prefer or are trying to use up"   # the REASON (#457)
  - amount: "15 ml"
    generic: "moderately aged rum"
    character:                   # a property of THIS RECIPE'S use of the
      - "blackstrap"             # bottle, not of the bottle in the abstract — §9.3.1
    suggestion: ["Gosling's Black Seal"]
    optional: true               # BOOLEAN, absent means required — #570
  - amount: "half"               # `half` and `whole` are UNITS.
    generic: "lime"              # A whole fruit is counted, never measured.
serve:                           # OPTIONAL — omit the key entirely if nobody
  ice: "large cube"              # has decided. `ice: "none"` means served UP — §9.10a
  rim: "sugar half-rim"          # free text, and rare
serves: 8                        # OPTIONAL, punch bowls only; absent means one
method:                          # ORDERED LIST — the steps are sequential
  - "Pour absinthe into ice-filled glass."
  - step: "Muddle the lime chunks hard with the sugar."  # a step is a string OR
    note: "my giant spiky muddler not the polite smooth one"   # a {step, note} pair
to_serve: ""                     # SERVEWARE, not a further instruction — §9.4
mood:                            # LIST, DERIVED and then stored — see below
  - "sharp"
  - "aperitivo"
notes:                           # {label, text} or a bare string, as food.
  - label: "QQ"                  # a note an INGEST adds is always {label, text},
    text: "QQ - `generic` values INFERRED, not confirmed: ..."   # both beginning QQ
source: ""                       # free text, unlike food
source_url: ""                   # external; nothing verifies it
meta:                            # FIVE keys, in this order — §9.1.1
  made_before: true              # BOOLEAN, gates nothing; first because you
                                 # make a drink and then have an opinion — #722
  ship: "oh gods yes"            # a closed ordered vocabulary — §9.5
  rewritten: false               # the three gate flags, food's names, food's
  awaiting_fix: false            # order. §4.0 is what they MEAN.
  proofread: false
```

`TOP_LEVEL_KEYS`, `REQUIRED_TOP_LEVEL`, `INGREDIENT_KEYS_*` and
`META_KEYS_IN_ORDER` at the top of `tests/test_cocktails.py` are the schema;
a key not listed there fails `test_no_unknown_top_level_keys`, and having to
write that line is the point.

**`mood` is derived and then stored.** `scripts/derive_cocktail_moods.py
--write` computes it from generics, characters, glass, amounts and method
steps against `mood_ingredients` in `taxonomy.yml`; the stored list is what
the index filters on. **Change a drink's ingredients and the moods may move**:
run the script dry after any such edit, `--write` only if it reports a
difference. `test_every_drinks_moods_match_the_derivation` re-derives every
drink, so a hand-edited mood cannot outlive the rule. Helen's own rulings
override the derivation through `mood_include` / `mood_exclude`, each naming
the single mood it is about. Nine moods are derived; **ten are hers alone**
(`moods_by_hand`) and no rule produces them — a newly ingested drink is
missing half its browse axes until she is asked (§9.13).

**`amount` is the only quantity field.** `ml:` is retired (#571).
Conversions and non-volumetric units live in `measures:` in
`ingredients.yml` — 1 oz → 30 ml, 1 tsp → 5 ml, 1 cl → 10 ml, bar-standard
rounding by decision; a dash is *known* to have no millilitre figure.
`test_every_amount_is_readable_as_a_quantity` accepts an amount only if its
unit is declared there. **No drink may use a US unit** (`US_UNITS`,
`test_no_amount_uses_a_us_unit`); `oz` and `tsp` stay DECLARED in `measures:`
because the dictionary is what makes a conversion checkable. Convert at
ingest from the source's own figure; the site is canon (§9.4.1). **A bare
number is never guessed** — 30/22.5/15/7.5 and 0.75/0.5 are thirty times
apart — and carries a `QQ - no unit in the source` note that the guard reads.

**Every ingredient has an amount, and for some it is a verb** (#669): a top-up
is `amount: "to top"`, a rinse `"to rinse"`, salt in the drink `"1 small
pinch"`, each declared in `measures:` `non_volumetric` and each with a method
step saying WHEN (`Top with champagne.` / `Top with soda water.` / `Rinse the
glass with absinthe and dump.`). The two strings appear nowhere in the test.
**Soda water, never club soda.** **`half` and `whole` are units** — a whole
fruit is counted, never measured, because the juice a lime gives is a range.

**The rim wording is the Margarita's own sentence**: `methods.yml` says *"Dip
only half the rim in water (or tequila) then coarse salt."*, with the drink's
LEADING spirit swapped in where it is not tequila (the file cannot
parameterise a step, so a non-tequila drink writes the sentence with its own
spirit and lives in the informative tail).

**The twist step is the layout's, and the SENTENCE is `methods.yml`'s.** A
garnish naming a citrus twist makes `_layouts/cocktail.html` append *"Express
the twist over the drink then drop it in."* (or *"…then discard it."* for
`(discarded)`) as the last step. No drink writes it;
`test_no_method_step_opens_with_express` refuses one that does. **The template
READS `canonical.express` rather than spelling it out — since 2026-09-09, when
the two drifted**: the strings were in both places, Helen changed the wording
(#880, `and` → `then`), and editing the declaration left the page emitting the
old one with nothing watching the pair.
`test_the_layout_takes_the_twist_step_from_methods_yml` watches it now, and
also pins the list's ORDER, which the template indexes.

**`item` may exist only beside `generic: "QQ"`.** It holds what the SOURCE
called the pour until the category is known, and goes when the generic is
filled in, wherever the file is (`test_item_is_gone_once_the_generic_is_filled_in`),
so a staged or published drink never carries one. Nothing renders it. Before
deleting one, check whether it says something `generic`, `suggestion` and
`amount` do not — a bottle nobody has declared, "brewed strong, from breakfast
tea, and cold" — and move that to a `note:`; **a field nothing renders can
still be hoarding facts** (23 real bottles came out of it once).

**`generic` is fully typed and is what the index browses by.** An untyped
ingredient is always a visible `QQ`, never an absent key
(`test_every_ingredient_has_a_generic_or_a_qq`). Since #501 it is also what a
card shows — §9.10.1. There is no star axis: the index filters and excludes
by ingredient, it does not browse by spirit.

**Sugar is in the generic, and so is the RATIO** (#594): `cane sugar syrup 1:1`,
`cane sugar syrup 2:1`, `demerara sugar syrup 2:1`, `turbinado sugar syrup 2:1`.
Both cane forms read `sugar syrup` on a card; the other two read `demerara
syrup` and `turbinado syrup`. **Type + ratio only where the difference is
real** — Helen, 2026-09-06 — which is why there is one demerara and one
turbinado and not six permutations.

Three honey waters are declared (`honey water`, `1:1`, `2:1`) and share one card
name, but **no drink uses the bare one** since 2026-09-07: it is kept as the
default for a drink whose ratio does not matter, and because `Acacia honey` in
`bottles.yml` needs a category. The five drinks that sat on it were split
2:1/1:1 on Helen's word, with `chartreuse-daiquiri` at 1:1 because its own note
says *"equal parts honey and water"*.

### 9.3.1 The ingredient vocabulary — `_data/cocktails/ingredients.yml`

**The file is the source of truth for what a `generic` may be**, and its own
comments carry every ruling; treat it as more current than this section.

**Two layers.** `generic` is the precise category on each entry — Campari,
Aperol, Cynar and Fernet are four generics, not one "amaro", because they are
not substitutable. `family` is a roll-up used ONLY for search and exclusion
("no whisky tonight"), never a browse axis.

**`generic` is stored, never derived** — most brand-named ingredients have no
rule that recovers the category. **A preferred bottle is a `suggestion`,
never a `generic`** (Velvet Falernum → `falernum`, with the bottle in
`suggestion`) — and the mirror rule: **when nothing generalises a bottle, the
bottle IS the generic** (Campari, Cynar, Becherovka; every member of
`herbal_liqueurs` is a proper noun and the family is a filing drawer).

**`generic` as a list means OR, and only OR** (#441). Daisy de Santiago's two
rums: either makes the drink, so an exclusion on one must not drop it.
Gosling's Black Seal, moderately aged AND blackstrap: one bottle, two
properties — that is `character`, never a second list member. Multi-value
only when both bottles can be named and a reason given for each; "I don't
know which" stays `QQ`.

**`character` lives on the recipe, not a bottle dictionary** (#441, Helen
overturning the first draft): it is *why this drink wants this bottle*, a
property of the recipe's use of it, so restating it across recipes is each
recipe correctly stating its own reasoning. `blackstrap` and `peated` are
characters and never generics. Rum's characters are a closed declared list
(`rum_characters`); gin's are free text by Helen's call. **Any
`<family>_characters` list is excluded from the declared-generic set by its
suffix and enforced by `test_a_declared_character_vocabulary_is_enforced`** —
declaring a list is what switches enforcement on.

**Naming**: every generic reads as an ingredient, natural word order, spirit
word on the end, no inverted commas — `moderately aged Jamaican rum`, `London
dry gin`, `rhum agricole blanc`. `rye` and `bourbon` stay bare because that is
the name you would say; `bonded rye` is a real style. Scotch and Japanese
take *whisky*, Irish and American *whiskey*. Generics are named by what
substitutes for what: never a `flavoured X` spanning non-substitutable
members (`vanilla vodka`, `pineapple vodka`; `sloe gin` its own generic);
`lavender-forward bitters` not `lavender bitters`; `apple brandy` by the
FRUIT so an applejack and a Spanish apple brandy share it, and it is not
`calvados`; `cucumber` and `kaffir lime leaves` bare — the leaf is not a
variety of lime. The three brand-generics (Planteray Stiggins', O.F.T.D.,
Malibu) are generalised (`pineapple rum`, `blended overproof rum`,
`coconut rum`). `Chartreuse Verte` / `Jaune`, not green / yellow. "Pernod"
names two bottles: write the PRODUCT, not the house.

**Renaming a generic is quote-anchored**: every occurrence is quoted, so match
`"<old>"` exactly, and never rewrite a quoted decision to match a later
rename — that falsifies it.

**`hers_to_apply`** lists styles that have bottles and no drink, which are
Helen's to apply and never to be retyped into from `item` text
(`caramel-forward Jamaican rum` is the case that earned it). Removing a line
is her grant, in the same commit as the drink that earns the style.
`test_no_drink_uses_a_generic_that_is_helens_to_apply` enforces it.

**The governing principle (#459)**: *"everything we do is focused on the user
(i.e. Helen), and making sure the user gets the drink she wants. Being an
encyclopaedia of drinks sounds like busywork and it's not for me."* Apply it
to any feature that describes a bottle in the abstract rather than in service
of one recipe decision.

**Every rum generic has a card name**, `card_names` — §9.10.1.

### 9.3.2 The bottle dictionary — `_data/cocktails/bottles.yml`

A third string per ingredient after the generic and the card name: which
BOTTLE, and its category, plus its alias spellings (#529). **Every named
bottle is in it and classified** — `test_every_suggested_bottle_resolves` is
not rum-only. **It means what Helen would POUR, not what qualifies**; a bottle
she no longer reaches for is MOVED to `not_reached_for` with her reason,
never deleted. `unresolved_suggestions` holds any suggestion string that
names no bottle, with a reason, so the test bites on the NEXT one; a row whose
string no drink says any more fails its own staleness guard. **Count it, do
not quote it** — it is a worklist and is empty as of 2026-09-04.

**The standing rulings for any ingest:**

- **A house is not a bottle.** Briottet, Monin, Gabriel Boudier: declare each
  PRODUCT she owns by name and retype the drink to it; a house is an alias
  only where it can mean one thing here (Luxardo → Luxardo Maraschino).
  Never add a bare brand as an alias — Bulleit makes a bourbon and a rye.
- **A spirit type beside its own generic is not a suggestion**; it goes.
- **A syrup's suggestion may name what it is made from** ("Acacia honey").
- **Spelling: in the POOL, leave the drink as she wrote it and add the
  spelling as an alias.** In `to-promote/` and `_cocktail_recipes/` the rule
  inverts and every `suggestion` is the bottle's CANONICAL name
  (`test_a_staged_drink_writes_a_bottles_canonical_name`): an alias is a
  reading convenience, a finished drink has had time to write the real name.
- **Do not derive a bottle's category from the ingredient it sits beside.**
  Helen: *"keep only what the collection already spells out; hand me back the
  rest."* A bottle she NAMES is hers to add and always was; what is banned is
  inference. Every declared bottle carries a price in `costs.yml` and a
  strength in `abv.yml`, and the tests fail in both directions.
- **A suggestion's bottle need not be in the ingredient's category** — that
  is the feature (cherry brandy → Cherry Heering or Briottet cerise) — but
  #534 requires a `note` when it crosses, and `QQ` counts: the substitution
  must be VISIBLE, not explained. A disjunctive `generic` crosses only if the
  bottle matches none of its options.
- **An absent suggestion is a real answer**: what is cheap and what needs
  using up are facts about the shelf on the day, never about the drink.
- **Aliases are how a bottle keeps one identity** (Planteray = Plantation
  renamed; canonical is Planteray, old spellings stay as aliases). The rule
  governs what is WRITTEN, the alias map what can be READ.

**Why a bottle table is allowed when #441 rejected one for `character`**: a
bottle's CATEGORY is bottle-invariant — Appleton 12 is a moderately aged
Jamaican in every drink — where `character` is why THIS drink wants it.
`Demerara, aged` and `Demerara, overproof` are APPELLATIONS (100% DDL,
Guyana), checkable against a fact about the bottle rather than argued from
the glass. Jack Daniels is a bourbon here.

### 9.3.3 The drinks index's search — three modules

`cocktail-index.js` is DOM wiring only; `assets/js/cocktail-search.js` holds
the pool, ranking, families and the two matching rules (pure, tested);
`filter-state.js` holds `COCKTAIL_FIELDS`; `ingredient-search.js` lends
`fold`, `getWords`, `orderByBand` — the DISCIPLINE, not the bands.

- **Fuzzy to find, fuzzy to include, exact-or-declared-family to exclude.**
  Over-including shows you a drink and the card says why; over-excluding
  hides one and you never learn it existed.
- **Four bands, in Helen's order**: prefix of the first word, prefix of any
  word, prefix of any word in a BOTTLE name, then substring. Visible beats
  hidden at equal strength; any real word beats a substring.
- **A chip must be able to explain itself** (#603): a chip found through a
  name it does not show carries that name — the containing name alone where
  the card name is a strict abbreviation of its generic (`clear blended
  multi-region rum`), a bracket otherwise (`cachaça (Sagatiba)`), in whichever
  spelling carried the query. The chip's VALUE never moves, only its label.
- **A multi-word query matches a hidden name from its start** ("el d" finds
  El Dorado).
- **An umbrella suppresses its own bare word**: `gin (all)` takes `gin` off
  the list beside it and leaves `sloe gin` and every ginger. In the pure
  module here; in `filters.js`, at render time, on food.
- **One chip per category, wearing the card's name**; a bottle is a way IN to
  its category, not a chip beside it, which needs the pool built PER
  INGREDIENT from `data-ing`.
- **Three characters before the picker answers** (`min_query_chars` in
  `ingredients.yml`); food keeps no minimum because its picker sits above a
  list that stays on screen.
- **Prose is not a bottle name** (`search.prose_words` / `prose_marks`; `and`
  deliberately absent — Wray and Nephew is one bottle). `family_aliases` /
  `family_labels` make a family reachable however it is spelled (`whisk(e)y`).
  `not_on_cards` keeps the bare sugars, salt, water, zest and honey off a card
  AND out of the search (#580, #640); every syrup stays.

### 9.3.4 Units of alcohol — #297

**Local only** (`show_units` in `_config_local.yml`). **Helen wants UK units,
not the strength of the finished drink** — `ml × ABV% ÷ 1000`, so water and
dilution do not matter and nothing needs modelling. `_data/cocktails/abv.yml`
holds a strength per BOTTLE (invariant, like the appellations, and a separate
file from `costs.yml` because a price decays and a strength does not) plus
per-generic figures where no bottle is named and `abv: 0` declared for every
non-alcoholic pour — **a missing key is a test failure; a zero is a
statement**. `_plugins/cocktail_units.rb` renders one line under the cost
line. Dashes do not count (asked, and Helen chose the same rule as costing;
the exclusion list is read out of `costs.yml`, never restated). A zero is
withheld rather than printed as "alcohol-free". Per serving, divided by
`serves:` where present, and no data attributes for the scaler on purpose.
`grep -n 'qq:' _data/cocktails/abv.yml` is the worklist of strengths only
Helen's shelf can settle; publishing would need it cleared.

### 9.3.5 What a drink costs — #547

**Local only and an incidental** (`show_costs`): one quiet sentence in the
drink footer under the source line, and a price in the shortlist. Data in
`_data/cocktails/costs.yml` (public either way), arithmetic in
`_plugins/cocktail_costs.rb` once at build. **Two layers, and a pour takes
whichever answers**: a bottle's own price where the pour names one, a
per-generic figure where it does not — the four most-poured things are lime
juice, lemon juice, sugar syrup and pineapple juice and none will ever be a
bottle. **`default_bottles` is a pricing fact and never a suggestion**
("gin means Tanqueray unless I say otherwise" is a fact about her shelf).
**Only a VOLUME counts** — no dashes, garnishes, muddled fruit, ice, salt or
sugar (*"I'm catering for family, not running a bar"*); the excluded list
lives in the data. `to top` is the one exception, as a declared RANGE
(`top_up_ml`), and the shopping list does not spend it yet. **The figure is
per glass and does not move with the scaler.** `cost.complete` withholds a
figure known to be wrong (the pear Bellini, the Caipirinha). `checked:` is
the file's honesty and the field to distrust first. Master of Malt returns 429
to every automated request; Helen reads it herself. Apply her corrections by
script against the parsed YAML, refusing on any name not found; a regex over
this file matches the wrong block.

### 9.4 Decided — do not re-litigate

- **Ingredients are additive, never a choose-one.** The Sazerac takes cognac
  AND rye AND bourbon. A flat list is enough.
- **`amount:` is the only quantity field** (§9.3; the "store it both ways"
  decision was reversed by #571 and is struck in `DECISIONS.md`).
- **`to_serve` is SERVEWARE and nothing else** — "Straw.", "Ladle and punch
  glasses.", plastic giraffes. Finishing ACTIONS are method steps; the ice is
  `serve.ice` (§9.10a). `test_to_serve_is_serveware_and_not_the_ice`,
  `test_to_serve_is_a_string`, and `test_no_method_step_restates_to_serve_or_garnish`
  (keyed on the leading VERB: "Serve"/"Garnish" steps go; "Float the…" /
  "Express…" instruct and stay).
- **Both brand and generic** are stored per ingredient.

### 9.4.1 The site is canon. Deviation happens in the kitchen.

Helen: *"With iPad in hand, I'd rather take the site as canon, then happily
break rules from there."* A cocktail page states ONE figure; it does not model
that she sweetens to taste. When a figure looks imprecise, the question is
never "how do we capture the imprecision" but "what single figure is the right
thing to print". A drink whose sugar is genuinely undecided gets a `QQ`, not
a range. A qualified measure (a scant or heaping ounce) keeps its figure and
loses its adjective to a note.

### 9.5 Settled apparatus

- **`garnish`**: `["no garnish"]` means DECIDED, `[]` means unfilled — §9.12.1.
- **`meta.ship` is an ordered, tested, CLOSED vocabulary** — `ship_scale` in
  `taxonomy.yml`: `not really` < `meh` < `sure` < `yes` < `oh gods yes`, with
  `who knows` deliberately OFF the scale and rendered as `???`
  (`ship_unrated_word`; the include never names a vocabulary value).
  **`QQ` is not a ship value**: an unmade drink says `who knows`, and the
  "nobody has asked" that `QQ` used to carry is `made_before: false`.
  `test_meta_ship_is_a_rung_or_who_knows`.
- **`meta.made_before` is a boolean and gates nothing** (#722). First in
  `meta:` because you make a drink and then have an opinion. **An unmade drink
  MAY publish** — Helen: there is no prose but the tagline, which she writes
  from scratch, and browsing drinks to try from the live site beats a local
  build. The `chaos only` filter reads it (§9.13). `_dev/no-verdict.html` is
  the worklist of drinks she has made with no rating.
- **`meta.status` is retired.**
- **`tests/test_cocktails.py` is the cocktails suite** and carries its own
  fixtures and marker; `conftest.py` is explicitly the FOOD suite. A cocktails
  test must ASSERT its corpus is non-empty rather than skip mid-run. The
  corpus is `_cocktail_recipes/` + `_cocktail_drafts/` through `_load()`, the
  only door (§10).

### 9.7 Two traps this layout hit on its first day

Liquid parses tag delimiters INSIDE a `comment` block, so quoting an if-tag
in an explanatory comment is a build error — describe the bad pattern in
prose. And an empty string is truthy: `source: ""` gated a "Source:" line
with nothing after it; every list-gated section tests `.size > 0` and every
scalar-gated one tests the value.

### 9.8 What cocktails borrows, and the tape

Cocktails shares food's two font stacks: colour and decoration separate the
sites, typography is the family resemblance. The tape and the footer are
shared chrome (§2.5) — one directory, `assets/img/chrome/`, cannot drift from
itself. Giving cocktails its own tape now means giving it its own header,
which #374 exists to prevent; argue it out rather than adding a directory.

### 9.9 `meta.ship` IS the rating

The vocabulary was there before anyone asked for a rating — "oh gods yes" was
on 18 drinks — and the feature was a template and a stylesheet. **Look for
the vocabulary before inventing one.** Buckets and words are derived from
`taxonomy.yml`, never hardcoded in a template: a hardcoded ordering string
and the vocabulary it enumerates drift silently, and each branch's tests are
green in isolation.

### 9.10 The drink page's ingredient line

**The line is the GENERIC, with the bottle in brackets**, then `character` on
its own quiet line, then `note`:

    45 ml   London dry gin (Tanqueray)
    15 ml   moderately aged rum (Gosling's Black Seal)
              character: blackstrap
    22.5 ml lime juice

**`item` does not render** — that is the whole fix for #513 (item and
generic restating each other on two lines). **A card name may be lossy; a
recipe line may not** (#561 is why the page was possible). `character` gets a
LINE, not a parenthetical, because "moderately aged rum (blackstrap)" reads
as a TYPE of rum. `.cocktail-suggestion` is quieter than the class it
follows: the class is what the drink REQUIRES, the bottle what Helen reaches
for. `generic`/`suggestion` may be a string or a list — Liquid's `for` treats a
bare string as a one-item sequence — and a list `generic` joins with a quiet
italic "or". `optional: true` renders as a plain word after the name; it is
not food's `incidental` (that HIDES a line; this shows and marks it).

### 9.10.1 Cards and search read the VOCABULARY, never the transcription

`card_names` in `ingredients.yml` maps a generic to its card name; the
template renders `card_names[g] | default: g` PER GENERIC, so a generic with no
card name prints itself. **Category ALWAYS, including where the recipe names a
real bottle** — Helen's call with `El Dorado 12` → `Demerara rum` in front of
her. **The card shows the shortest name that tells you what the drink is
LIKE**: `gin` (London dry versus Plymouth does not change your evening),
`bourbon` and `blanco tequila` (rye versus bourbon does). No brand on a card.
A collapse must be declared (`card_names_may_collide`); an undeclared
duplicate fails. `card_name_joins` rewrites a disjunctive pair that reads
badly, keyed on the default join. Two pours of the same rum print the name
twice, correctly. `character` is recipe-only. **The drink page prints the
generic verbatim and reads `card_names` nowhere** — so a Sazerac's line reads
`cane sugar syrup 2:1` and its card `sugar syrup`. Cards are lowercased in
CSS, not in the markup.

**The highlight reads a build-time `data-ing` attribute, never rendered
text** — whenever a template stops rendering the string a script matched on,
the script is already broken and nothing looks wrong. The search pool is
`generic + card name + suggestion`, built at build time, with alias spellings
resolved through `bottles.yml` and the canonical name JOINING the terms rather
than replacing them.

**The card's ingredient line is a plugin**, `_plugins/cocktail_card_ingredients.rb`
(#567, #640, #691): hiding, labelling, joining and emitting search data from
ONE list per drink, so the pool and the visible line cannot drift. **The order
is Helen's**: base spirits, then lower-proof, then citrus and juice, then
syrups, then everything else, then bitters; largest volume first inside a
tier; the recipe's own order breaks ties. **The sections of `ingredients.yml`
are the classifier**; a generic in no section warns at build and fails a test.
**Tier 7 is built** (#754, 2026-09-07): `as:` on an ingredient records how a
pour is USED — `float`, `rinse` or `muddle`, a closed vocabulary in
`ingredient_as`, guarded the way `rum_characters` is. `float` and `rinse` both
sort last, Helen's ruling that a rinse joins the floats; **`muddle` sorts
nothing**. #567's muddle clause was built, looked at and dropped — grouping
muddled ingredients first put Ti' Punch's rhum last on a rhum drink, because a
muddle covers both expressing a lime and dissolving a sugar. The value is still
recorded because it is true; the plugin header has the finding.

**`card_order:` has its first user**, Port Authority's blackberries — they are
`fruit_and_herbs`, so the default rule sorted them fifth on a drink they are
the point of. `0` is legal and means "before tier 1"; test it with `is not
None`, because Ruby's `||` treats 0 as truthy and a Python mirror of this sort
did not.

**The card's three stacks share one budget** (#776): a wrapped name caps the
ingredients and the chips at two, and three rendered ingredient lines cap the
chips. Half of it is CSS — `.drink-card-name--wrap` is a sibling — and half is
`card-line-budget.js`, because CSS can ask how many lines are ALLOWED and never
how many rendered. **A hidden card measures zero**, so anything measuring cards
must re-run when pagination changes what is visible; `cocktail-index.js` does,
ahead of `markChipRows()`.

### 9.10a `serve` — where the ice lives

A drink has a BUILD and a SERVE. The serve is the vessel (`glass`), the
garnish, the serveware (`to_serve`), and THE ICE IN THE GLASS:

```yaml
serve:
  ice: "large cube"   # none | cubed | crushed | large cube | block | blended
  rim: "sugar half-rim"
```

**Absent means nobody has decided; `ice: "none"` means served UP** — the same
distinction `garnish` draws. **The ice in the glass, never the ice in the
shaker.** **There is no `chill` key** — a chilled glass is assumed (*"I am the
user after all"*); freezing or rinsing a glass is a method step in its own
right. **The page COMPOSES the strain step** — `"Strain."` + the glass's
`serving` phrase in `glasses.yml` + the ice's `in_the_glass` clause in
`serve.yml` → *"Strain into an old fashioned glass, over a large ice cube."* —
so each fact is stored once and a drink that changes glass gets a corrected
method for free. Ice you pour ONTO takes a comma and "over"; ice the glass is
FULL of takes "filled with". **The rim rides on the glass, before the ice.**
**A garnish step closes the method** (excluding twists, which have the better
express step); "To serve" is what happens to a drink that is already
finished. `test_serve_ice_is_not_restated_in_the_method` and
`test_no_method_step_ends_on_a_dangling_word` are the ratchets.

### 9.11 Glass icons — real relative height, and a UA-stylesheet trap

`_layouts/cocktail.html` computes `--glass-icon-height` per drink from
`glasses.yml`'s `heights_mm` against the tallest real glass (counted live);
the scale is 10.4rem on the drink page since the glass became its hero, with
the width cap in the same proportion. **The card is a different calculation**
— §9.13's curve and headroom. `_dev/glasses.html` is the comparison page.

**Fill-only artwork: ask "must this be redrawn" before "can this be traced".**
`glass-icon-solid` fills with `currentColor` (heavier, and scales WITH the
icon); `scripts/trace_centrelines.py` derives real centrelines, valid only for
UNIFORM-WIDTH ink (measure with a distance transform along the skeleton), and
tracing is a lossy redraw. **The whole published set is line art** (#738) —
`SOLID` in the normaliser and `.glass-icon-solid` are both empty and both
kept as two halves of one switch. `scripts/glass_ink_coverage.py` measures
density; compare ratios within one run.

**Open stroke ends: the site draws 4–6× thinner than Helen edits.** Her
sources carry ~2.8-unit strokes; the published icons use `vector-effect:
non-scaling-stroke` at 0.35–0.66 units, so a gap invisible while drawing is
open on the page. `scripts/glass_stroke_gaps.py` finds them in RENDERED
pixels; measure ends against STROKES, not other ends. Deliberately no guard —
her call: the set is replaced wholesale if at all.

**`heights_mm` is unmeasured** (#295 open) and stem/base proportions genuinely
differ glass to glass (#299, parked — *"these graphics are the thing on the
site that the least serves function over form"*). `rocks` is a plain alias to
`old-fashioned`; the double is the same body scaled up. `mug` is the plain
mug (a Moscow Mule's is copper, which a line icon cannot say; `mule mug` is
an alias). `any` is retired and `todo`/`long` became `highball`; an unmapped
glass is now far likelier a typo than a decision.

**A root `<svg>` defaults to `overflow: hidden` in every browser's UA
stylesheet**, shearing a stroke on the viewBox edge; every icon renders with
an explicit `overflow: visible`.

**Helen's raw Inkscape sources are in `_design_sources/cocktails/glasses/`**,
committed as-is, underscore-prefixed so Jekyll ignores them. Nothing reads the
directory; normalising a drawing into `_includes/icons/glasses/` is a manual
step through `scripts/normalise_glass_icons.py`, and a rename there is TWO
edits — the script's `RENAME` map is the one that sticks.

### 9.11.1 The canonical glass vocabulary is a RULE

`canonical_glasses` in `glasses.yml` maps alias → the spelling a drink must
use, and `test_drinks_use_the_canonical_glass_spelling` reads its whole
vocabulary from it; adding a pair is what makes it enforced. **The aliases in
`icons:` stay** — they keep a drink rendering if one slips through and absorb
a source's spellings on ingest. The rule governs what is WRITTEN; the alias
map what can be READ. `martini` vs `martini glass` is deliberately not in the
map: an alias absent from it is permitted, so silence means "not asked yet".

### 9.12 The method-step dictionary — `_data/cocktails/methods.yml`

**A closed vocabulary for the mechanical spine, free text for everything
else.** The argument is #290's (and §13.1's): a shape that changes every time
has to be RE-READ, an identical repeated one becomes something you
RECOGNISE. **The test for whether a step belongs in the dictionary: does its
phrasing carry information?** "with ice" versus "over ice" carries none;
"other than the champagne" carries all of it. The tail is never
canonicalised.

**The strain group is five strings** — `Strain.` `Fine strain.` `Double
strain.` `Dump.` `Pour.` — because the ice has a field now (§9.10a). **A
vocabulary that keeps growing is usually absorbing a fact that belongs in a
field.** "Shake all ingredients with ice." and "Shake with ice." mean
different things; **the preceding step is the whole question** for any short
verb form — two identical-looking strings went opposite ways on nothing but
the line above them. And when a step is incoherent, ask which FIELD is wrong:
"fine strain with ice" into a `coupe` was a wrong glass.

**Changing a canonical step is propose-then-let-Helen-delete**: `proposals:`
holds her exact string on the left and the suggested form on the right,
deleting a row is how a suggestion is rejected, and the pass applies only what
survives. `proposals: {}` is the settled state and its guard asserts the KEY
exists, not that it has rows — a ratchet list and a worklist look identical
and want opposite assertions (§12). Three tests keep the map honest (a
proposal points at a real step, nothing is both canonical and replaced, every
left-hand string still exists). Do not turn this into an enforcing test
without asking.

### 9.12.1 The garnish vocabulary — `_data/cocktails/garnish.yml`

`methods.yml`'s sibling: same argument, same shape, same bargain. **It is not
for filtering** — there is no garnish filter and this is not a step towards
one. `test_every_garnish_is_declared` is a RATCHET seeded from the real
strings. Every entry carries a `group:` (D11) that the standalone document's
grouping is generated from. The rules that decide the awkward cases: a twist
IS a strip of zest (`lemon twist`, never `lemon zest twist`, but keep the tail
— `(discarded)` is information); the list is CONJUNCTIVE, so *"either, the
maker chooses"* is ONE STRING (`orange or lemon twist`) — `generic` solved the
identical problem from the opposite default and the two fields cannot share a
convention; a count stays only where the count is the spec (`three coffee
beans`); `["no garnish"]` means decided and may only appear alone; a garnish
is not a pour (anything with an amount is an ingredient), a rim (`serve.rim`)
or serveware (`to_serve`), and must not restate a method step.

### 9.13 The cocktails visual language, and the index and drink page built from it

**"Ink, paper and glass"**, and **the paper is black** (#469): `$color-paper`
`#0e0e10`, `$color-ink` `#e8e6e2`, and **a card is DARKER than the page**
(`#17171a`) — it recedes rather than floats; the border at L* 18 holds its
shape however close the fills get. The names keep their jobs, not their
literal meanings. Every `-deep` and `-wash` was re-solved for the inversion
(on black a hue is LIGHTENED to carry text; washes are 14% over a card); the
emboss is re-pointed in `_sass/cocktails/_rule.scss` (`LETTERING.md`);
**food is untouched**, verified in the compiled CSS.

**The five accents — "neon bar sign"** — bare = the RULE, a vivid band under a
heading, never text; `-deep` = safe as type; `-wash` = a tint for something
matched:

| variable | job | where |
|---|---|---|
| `$color-electric-absinthe` | MOOD, **and the home colour** | the glass on a card, hover, nav/footer chrome, the drink page's title border and toggle |
| `$color-radiant-reposado` | YOLO / GOODNESS | the ship mark |
| `$color-ultra-yvette` | HASSLE; INGREDIENTS and METHOD on the drink page | section rules |
| `$color-cosmic-cosmopolitan` | HAS TO HAVE; the bottle suggestion | the matched-ingredient band |
| `$color-luminous-lagoon` | I KNOW WHAT I WANT; NOTES on the drink page | title hits |

**LEAVE OUT has no hue at all**, deliberately. **A heading's colour is a
promise the card already keeps** — nothing was assigned by taste alone. **The
index headings are a ramp, one bar each**: reposado → coral → hot pink →
cosmopolitan → yvette, top to bottom, single solid bar, weight 400 (bold
light-on-dark stems bloom). **The section's colour reaches the card**: a
chosen filter word underlines in its section's colour, a matched mood chip
lights coral, a matched hassle chip hot pink, a matched ingredient
cosmopolitan, the title hit yvette; a matched chip keeps its section colour
(never white) and moves to the FRONT of the row in the DOM (#756, #757).
**Magenta means "this one" on hover, and it is the only thing hover changes**:
nothing moves, nothing resizes; a chip moves its box, a bare word its text;
`:hover` and `.is-on` are the same specificity so hover carries `:not(.is-on)`.
`scripts/palette_measure.py` is the contrast / dichromacy / CIEDE2000 tool;
the dichromacy bar applies only where colour carries meaning ALONE (the
goodness mark and the matched ingredient). **Text on a wash is ink, never the
`-deep`**; **bands and washes, not fills** — the goodness mark is the only fill
left on a card. **The names are the bottles** (#555).

**The index** (`cocktails/index.html`, `_filters.scss`, `cocktail-index.js`):

- **The universe says…** sits above the five questions, one line, not a card
  (#719, #714, #693, #692): label, a tiny glass at a fixed 1.4rem in a fixed
  2.3rem slot (so a redeal never jumps), the name on its tape, the ingredients
  in round brackets with the closing bracket as a separate flex item, `deal
  again` at the END of the row. Deals from ship `yes` and `oh gods yes`,
  naming the two rungs rather than borrowing `data-chaos`. No box, no ship
  mark, no mood chips, no square brackets, no full width — each Helen's call.
  `data-universe-parts` names the child classes so the glass can sit on
  either side of the tape. Food turned the feature down (§13.4).
- **Five named questions, in Helen's order**: YOLO? (`no chaos please` / `I'm
  open to chaos` / `chaos only` — the third reads `made_before: false`, never
  `ship`, because the two come apart the day she makes one), Mood (what the
  drink IS), Hassle (what it COSTS), Has to have / Leave out, I know what I
  want (last on purpose). **`open` applies no filter at all** — the button for
  "I'll try anything" must never narrow. Taste and style are NOT split.
- **Mood and Hassle share one `state.moods` Set** (ORed), and ranking counts
  SECTIONS matched (#695); the narrowing sections score identically for
  everyone, so mood is the only place a rank has anything to rank. OR within a
  section, AND between sections, more matched moods rank first. Include chips
  are AND.
- **Pagination, twenty a page** (#694), food's control and arithmetic; paging
  happens AFTER the reorder; the page joins the back-navigation memory.
- **Randomised order, shuffled once per page load**; filtering re-ranks
  against fixed keys. **Going back restores the list you left** (#595; food
  restores an ARRAY, cocktails restores SORT KEYS).
- **`mood_groups` in `taxonomy.yml` is the split**, with
  `test_every_mood_belongs_to_exactly_one_group`; a mood with no drinks
  renders no button; **nineteen moods, nine derived, ten Helen's**
  (`moods_by_hand`) — a tag meaning "contains one of these bottles" is a
  worse copy of HAS TO HAVE and was refused (*"I'd hoped for more evocative
  moods"*); `test_no_mood_covers_more_than_half_the_collection` is the guard
  that killed `up`. Narrow rules plus recorded exceptions beat loose rules.
- **There is no glass filter and no spirit filter**, and there must not be.
- **Filtering reads data- attributes, never rendered text.** Headings must
  not be outranked by their buttons — a control must not dress as a label.

**The card** (`_cards.scss`): horizontal, the glass drawn large down a fixed
left column (`$card-text-x`, 6.5rem, a custom property as well as a Sass
variable so five rules cannot bake their own copy), words beside it. **Every
anchor is fixed** — fixed height, body anchored top-left, foot pinned — and
the cost is clamping: three lines of ingredients and up to three rows of mood
chip (#552 — the tiki drinks needed the third line); the foot lays chips and
ship side by side, bottom-aligned. **No panel behind the glass**; the drawing
is absinthe and the card shows through. Hover brackets the column with two
painted strips (never borders — nothing moves). **The title sits on punched
tape** (§13.4.1's device at card size): two near-whites, one tight pair, no
softening; the band is centred by moving the ARTWORK (`top: -1.765%`), the
geometry solved for the name's width (padding costs the name twice, a bleed
pays it back once; the `em` numbers follow the title, the gutter does not).
**A name that does not fit shrinks one step (0.86) or wraps, never
ellipsises** (`card-name-fit.js`; with no JS the ellipsis stays). **The mood
chips are bare words**, Courier, lowercase, a middle dot between them drawn
on the PRECEDING chip's `::after`, so a chip ending a line keeps its dot and
none can ever lead a row (#846, which satisfies #698 by construction and
deleted the `chip-rows.js` measurement pass that used to); they are real
`<button>`s that filter the index through one delegated listener, painted from
state. **The goodness
mark is a ship and a word** (`_includes/cocktails/ship.html`, the same include
the drink page calls; the card passes `short=true` for `ship_card_names`, the
page says the rung's own words). **How tall a glass is drawn**: the curve
`ratio × 0.5 + 0.5` lifts the short end, `$card-glass-scale` caps the tall
end, `display_scale` is the per-glass cheat, kept and empty; eight wide
glasses are capped by width before height. `/dev/card-glasses/` is kept as
the instrument and its defaults must stay the shipped values. Below 400px
the card un-columns (`stack`).

**The drink page — two states, one page.** Read
`_sass/cocktails/_cocktail.scss`'s header first; it carries the anatomy and
the colour jobs in full. The glass sits INSIDE the content column at the
head's left edge (a flat 7rem column; the margin layout is gone), CENTRED in
the head, absinthe, stroke 2, never shorter than `$glass-min`. The name is on
the card's tape (2.6rem, 1.6em horizontal padding) with a real `<h1>` inside
at `display: contents` and `font-size: 1em` (the UA's `h1 { 2em }` doubled it
once). Meta is a `<dl>` of GLASS / GARNISH / SHIP IT?; mood chips are LINKS
to the index with `?mood=`. INGREDIENTS / METHOD / NOTES headings are 1.5rem,
weight 400, absinthe over yvette (NOTES over lagoon); ingredient names carry
no underline (they looked like links). **`make it`** (`cocktail-make.js`, a
three-part toggle) is one class, `is-making`; nothing leaves the DOM; SHIP IT?,
the tagline and the chips are read-mode only; **print is the FULL page**,
forced by `_print.scss`. **The scaler is one box and a `×` under the
ingredients list**, **whole recipes only** (integer multiples, clamped at ×1
— every written amount is on the 2.5 ml grid, so nothing ever needs
rounding); counts multiply and re-pluralise, `to top` / `to rinse` pass
through; the floor is a REFUSAL naming the ingredient; ONE parser
(`shoppingList.parseAmount`) across `shopping-list.js` → `scale.js` →
`cocktail-scale.js`, guarded by `test_the_scaler_scripts_load_in_dependency_order`.
`serves:` exists on nine punch-bowl drinks and the scaler does not read it —
*how many does this make* and *how much am I making* are different questions.
A `{step, note}` pair renders the note under its step and stays visible in
`make it`. The amount column has two widths, counted in Plex Mono characters.
**Not yet seen on an iPad.**

**Every drink names a glass** (`test_every_drink_names_a_glass`; the
`GLASSLESS_ON_2026_08_27` ratchet is empty and asserted so). What made Helen's
sixteen quick was showing the TOTAL VOLUME. `any` is retired: the freedom it
encoded is one she applies to every glass.

**Tracing a filled icon into strokes**: `scripts/trace_centrelines.py`
(rasterise filled, Zhang-Suen skeleton, walk greedily preferring the
neighbour that continues the direction — a degree-based split returns
thousands of fragments on an 8-connected skeleton) and `scripts/svgrender.py`
(the rasteriser, validated against known-good icons, imported by two tests).

### 9.14 `heights_mm` sizes the CANVAS

An icon renders at the height `heights_mm` gives its **viewBox**; a drawing
with empty margin renders SMALLER than one without, and Inkscape keeps the
previous canvas silently when a glass is built by editing another — which is
the only way Helen can make one. So `scripts/normalise_glass_icons.py` **fits
every icon's viewBox to its own artwork** as its last step, measuring ALL the
ink with the whole ancestor transform stack composed (a nested `matrix()`
was once dropped and four icons hung outside their frames), growing as well
as shrinking, with a 1.4-unit margin (not a percentage — `non-scaling-stroke`
needs more units the smaller it renders). Three guards face three ways:
`test_no_glass_artwork_has_a_slack_viewbox` (canvas bigger than drawing),
`test_no_glass_artwork_is_drawn_outside_its_viewbox` (the reverse), and
`test_the_icon_parser_applies_nested_transforms`. **The normaliser refuses
unless it has usable input, BEFORE deleting anything** — its `SRC` is a
gitignored inbox that is empty in a fresh worktree, and it emptied the
published set twice. Recover with `git show HEAD:<path>`, never `git checkout
--` on a dirty tree.

### 9.15 Never save a redraw over its predecessor

`_design_sources/` is the record of what was tried; base name is the
original, a numeric suffix is the redraw, both stay on disk. Which one
publishes is a NAMED SWITCH in the normaliser — `RENAME` points the suffixed
name at the published name, `SKIP` holds back the one it supersedes — never
the highest number and never `sorted()` order (`-` sorts before `.`, so the
bare name wins by being written last). `python3 scripts/check_glass_regen.py`
resolves every source through the registries, normalises in memory and diffs
against the published set without deleting anything; run it after touching
any registry.

### 9.16 The candidate drawer — `/dev/glasses/` sections 5 and 6

Every drawing in `_design_sources/`, normalised into
`_includes/icons/glass-candidates/` and listed in
`_data/dev_glass_candidates.yml`, both written by
`scripts/build_glass_candidates.py` in one run so they cannot drift. Not in
`_includes/icons/glasses/` (the published set, asserted to match `all_icons`
both ways) and not in `_data/cocktails/` (the site's vocabulary).

---

## 10. Validation — run `pytest`, don't read this

**The suite gates the deploy** (#369): `.github/workflows/build-and-deploy.yml`
has a `test` job and `build` declares `needs: test`, so every guard here is a
build stop rather than a report. Three things are load-bearing:

- **`fetch-depth: 0`** — in a shallow clone `git log -- <file>` reports one
  commit for every file and §4.0's provenance test would pass over nothing.
- **Run the JS suite as bare `node --test` from the repo root.** It discovers
  every `*.test.js` on its own. Passing the DIRECTORY (`node --test tests/js/`)
  treats it as one module and reports "tests 1, fail 1", which is what the old
  glob form was working around — but a glob in a file-path argument now costs a
  permission prompt on every run (`CLAUDE.md`: the checker cannot verify a file
  list the shell has not expanded yet), and the bare form has neither problem.
- **CI has no private drafts, and every test that reads them says what it
  does about that.** `SKIPS_WITHOUT_DRAFTS` and `PARTIAL_IN_CI` in
  `test_suite_hygiene.py` are the registries, enforced by
  `test_every_draft_reading_test_says_what_it_does_without_drafts`; a
  draft-reading test in neither set fails. Per-draft parametrised tests need
  no entry (an empty parametrisation is a visible skip).

**The cocktail corpus is `_cocktail_recipes/` + `_cocktail_drafts/` through
`_load()`, the only door** (#540; `test_every_drink_reading_test_goes_through_the_loader`).
So a PROMOTED drink is checked everywhere including CI; the drafts remain a
local concern by Helen's decision. **CI CHECKS 48 DRINKS SINCE 2026-09-10** —
this sentence read "with nothing promoted, CI still checks no drink" for the
whole life of the collection, and the deployment is what changed it. Every
guard that has only ever run against drafts on Helen's machine now runs
against those 48 in CI as well, which is coverage arriving rather than
coverage changing. **The staleness half of a guard is unanswerable on a partial corpus**
— a drink merely ABSENT looks exactly like a drink FIXED — so every check
that hangs on a shrink-only registry or a mood's share of the book calls
`_require_whole_collection` and skips with a reason; `WHOLE_COLLECTION_ONLY`
is that registry and `test_whole_collection_only_says_what_it_does` keeps it
true both ways. At one promoted drink four anti-vacuity asserts will fire,
correctly, and self-resolve by five.

**A public test can need private data, and nothing makes the two merges
arrive together** (#624). The tell is both directions failing at once ("39
garnishes not declared" AND "the vocabulary proposes changes to strings no
drink says"): two files at different commits, a synchronisation fault, not a
data fault. **The answer is a schema handshake**: each private repo carries a
`SCHEMA_VERSION` file; `tests/drafts_schema.py` declares the version this
checkout's rules need with a changelog; `test_the_cocktail_drafts_clone_is_in_step`
and its food twin compare them and skip when the repo is absent. **Bump BOTH
in the paired commits.** It diagnoses, it does not prevent: one failure says
which side is behind, as the FIRST line of its message because `pytest.ini`
runs `--tb=line`. A hand-maintained integer, not a fingerprint — not every
schema change needs a data migration. When a public PR depends on a private
branch, name the branch in the PR description (`PUBLISHING_A_DRINK.md`).

**Before pushing anything CI will run, simulate it**: move both private
draft directories aside, run the full suite, move them back.

Counts move — run the suites, don't quote numbers from here.

| File | Covers |
|---|---|
| `test_front_matter.py` | required and retired fields, xor rules, group names, the gate flags and their provenance |
| `test_style.py` | typography, spellings, accents, time formats, `Estimated` |
| `test_taxonomy.py` | declared tags/stars, co-tags, links, spelling collisions |
| `test_site_config.py` | architecture guards, not recipes — every check exists because something went wrong at least once |
| `test_drafts.py` | the `_food_drafts/`-scoped subset via its own `draft` fixture; `NOT_FOR_DRAFTS` is the registry of rules deliberately not applied, with a reason each — read a "GAP" label as a claim to check |
| `test_reference_data.py` | `internal_temperatures.yml`'s invariants (§14) |
| `test_suite_hygiene.py` | tests about the tests: the one failure mode whose symptom is green |
| `test_cocktails.py` | the drinks' own spec, and the glass ARTWORK's |
| `test_page_links.py` | every `<a href>` in every template, traced to a literal path; `published: false` pages are excluded from BOTH sides |
| `test_rendered_pages.py` | assertions about BUILT html: the chrome guards, the stylesheet guard, the gate in both directions on both sites, `test_every_icon_partial_class_has_a_styled_base`, `test_every_text_input_on_the_index_has_state_behind_it` |
| `test_source_attribution.py` | the citation rules over recipes and drafts |
| `test_prose_pages.py` | house typography on the non-recipe pages and their data |
| `test_magic_bag.py` | `_food_magic_bag/`'s own schema |
| `test_standalone_docs.py` | the two repo-less documents: every YAML block parses, every example obeys its own rules, every printed vocabulary value is declared, every generated block matches its generator |
| `test_ingest_inbox.py` | the envelope parser over fixture envelopes; never the network |
| `test_tidy_drafts.py` | the tidy pass, byte for byte, on a fixture |

`pytest.ini` declares three markers — `pytest -m food`, `-m cocktails`, `-m
shared` — for signal, not speed: a red food half hides a real cocktails
regression. Every module declares one.

### 10.1 Standing rules

- **The audit is repeatable in three steps**: grep every test for `issue
  #NNN`, diff against the closed list from the API, check each gap against the
  data before calling it a gap.
- **`test_oven_temperature_says_fan` (#146) and `test_milk_specifies_type`
  (#167) are ex-checklists** worked through by hand; a red in either is a real
  regression, and neither is fixable blind — which figure is the fan one and
  which milk a recipe used are only in the source.
- **`test_ingredient_notes_are_lowercase_fragments` FLAGS AND NEVER FIXES.**
  Helen: *"I'll look at violations myself because I care about tone of
  voice."* Whether a capital belongs in `proper_nouns` is her call.
- **There is one draft marker, `QQ`. Never add a third** (`PLACEHOLDER` lived
  for a day).
- **Which checks read `_food_drafts/` — ask the registry**, not this file.
  The one that fires in practice is `test_no_main_ingredient_spelling_collisions`,
  when a new draft's spelling collides with an existing ingredient. Before
  reporting a new failure: `find _food_drafts -name '*.md' -mmin -120`.

### 10.2 The stub-DOM harness — `tests/js/dom-stub.js`, `tests/js/index-harness.js`

The fault it exists to catch: a name read off the wrong object takes out the
whole tail of `cocktail-index.js` while every pure test stays green, because
each asks a pure module a question and the fault is in the WIRING (#633).
**The canary is the `pagehide` listener**, the last statement in the file.
**Nothing is mocked that the page does not mock**: the real scripts run in the
real order via `vm.runInContext`; only the DOM and `localStorage` are
stand-ins; the script list is compared against the `<script src>` tags in
`cocktails/index.html` and every id the script reaches for must exist in the
fixture. No jsdom, no `package.json`, no `node_modules` — `node:test` and
`node:assert` alone. Pagination and the chip reorder have behavioural tests
through it. For `decorations.js`, which has none, copy the harness — and read
the script order from `_site/`, not the layouts, because a layout's scripts
land inside `{{ content }}`.

**FOOD HAS ITS OWN, `food-index-startup.test.js`** (#801), built the same way
but self-contained rather than sharing `index-harness.js` — one consumer, and
the fixture is a different page. Two things to know before extending it. The
whole of `filters.js` is inside a single `DOMContentLoaded` handler, so the
harness has to `doc.dispatch('DOMContentLoaded')` after loading the scripts or
nothing runs at all and every assertion is about an untouched page; and the
canary is `.recipe-list` becoming `visibility: visible`, which is near the end
of that handler, so anything throwing above it fails one assertion. The stub
stores `innerHTML` as a STRING and does not parse it, so a control the page
writes that way cannot be found with `querySelector` — dispatch at the
delegating parent with a stand-in `target` instead, which is the object the
listener actually reads.

---

## 11. Working practices

> **THE FOUR PROCEDURE DOCUMENTS, and each is the authority on its own half:**
> getting material IN — `.claude/commands/ingest.md` (§11.0.3); when it
> arrived as a GitHub Issue — `ingest-inbox.md` (§11.0.4); the mechanical half
> of a drafts pass, either collection — `tidy-drafts.md` (§11.0.2); getting a
> DRINK OUT, and what "mechanical" means — `model_instructions/PUBLISHING_A_DRINK.md`.
> The last is the one a session is most likely not to know exists, because it
> is not a slash command. Read it before touching `_cocktail_drafts/to-promote/`.

**Git is `CLAUDE.md`'s.** Branch, never commit or merge onto `main` in any
repo in the tree, never `git reset --hard` or discard over a dirty tree, check
`git branch --show-current` in its own tool call immediately before every
commit. **Push with no ask in all three repos since 2026-09-07, and OPEN THE PR with
no ask in all three since 2026-09-09** (§11.-1), when `GH_TOKEN` was deleted
and `AGENT_GH_TOKEN` — which has the `Contents` permission the old one lacked
on the private repos — became the only credential. **Merging is hers, always,
everywhere**, and note that this is now the RULE holding rather than the
token, which can merge.
**Five hooks in `.claude/hooks/`** enforce the five rules that were read and
broken anyway — `guard-main-branch.py`, `guard-destructive-git.py`,
`guard-sed.py`, `guard-token-expansion.py` and `guard-inline-script.py` — and
**there are exactly five**, so do not assume a rule is mechanically enforced
because this file states it firmly. **This paragraph said "exactly two" until
2026-09-09**, having been written when there were two and not revisited as
three more arrived; a count in prose is a fact that rots, and the only honest
version of this sentence is one that names them. `ls .claude/hooks/` settles
it. `DECISIONS.md` §11 has why each exists and what each deliberately allows;
`CLAUDE.md` has the workflow.

**Branch names:** `<type>/<what-its-about>`, lowercase, hyphens; one concern;
deleted after merge, local and remote. **Commit subjects:** `(type) lowercase
description`, no full stop, the type words in use derived by `git log main
--format='%s' | grep -oE '^\([a-z]+\)' | sort | uniq -c`. Write what the
change *does*. ASCII `--` in commit messages, not an em dash. **Commit
bodies**: why not what; how you know it works; whether a fix predates the
branch; what you ruled out; guards added and that you broke them to prove
they bite. End every commit with the `Co-Authored-By: Claude …
<noreply@anthropic.com>` trailer the harness supplies.

> ## TAG THE ISSUE. EVERY COMMIT, NO EXCEPTIONS.
>
> `Fixes #N` / `Closes #N` on its own line when a commit resolves one; `Towards
> #N` / `See #N` in the body when it touches one; the full
> `DeckOfPandas/helen-triages#N` form from a nested repo — and note that such
> a trailer from a PRIVATE repo closes and cross-references NOTHING, so
> closing a public issue from work done there is a separate deliberate step.
> Do it AT COMMIT TIME; after a push it is fixed. Helen's standing preference:
> close via commit message whenever a trailer can; the `AGENT_GH_TOKEN` API is
> for the cases it cannot reach. Before reporting an issue as done:
> `git log main --grep="#N"`.

**Helen** writes no code by choice, has strong systems judgement, wants
explanations that assume both. Offer aesthetic opinions — she asks for them.
Disagree with her when you think she is wrong; say plainly when you were
wrong yourself. **Her hours are hers: never remark on the time, suggest
stopping, or wonder whether something should wait until tomorrow.** **Ask her
the decisions as you hit them, not in a batch at the end**, and bring her the
fact that forces the decision, not the options in the abstract.

**Four things about the interaction that no file teaches:**

- **Show, don't describe.** For anything debatable, build it at a throwaway
  URL and hand her the link. §13.11.
- **She reports symptoms, not diagnoses — and reports them accurately.**
  Treat the observation as exact and go and find the cause; do not treat her
  wording as the brief, and do not stop at the thing she described.
- **An aesthetic objection usually has a structural reason under it.** Look
  for the reason before complying, because the reason is generally the
  better fix.
- **UAT is a first-class method here, and she is the only user.** She finds
  rendering faults no test can see. When you cannot see something yourself,
  say so and hand it over. Then write the test her eye just stood in for.

**The test suite is self-sufficient by design — GitHub Issues are provenance,
never a dependency.** You should be able to bring the recipes and drafts into
shape from `pytest` output and this file alone. **Test names and assert
messages are both expressive**: name the rule (`test_egg_size_is_stated`),
and let the message name the actual fix — the offending value, the allowed
list, why it is not safe to fix blind. A docstring that only makes sense after
reading the issue it cites is a gap to close.

**One agent at a time in this working tree, and never one that switches
branches.** Delegate the reading and the scanning; keep the branching in the
foreground. More than one agent means a worktree (§11.0.1).

### 11.-1 The branch workflow, and the second hook

`CLAUDE.md`. Four steps, one of them Helen's: Claude works on a branch, then
pushes it and opens the PR **with no ask**; **Helen reviews and merges — and
nothing else**; Claude fast-forwards `main` without checking it out
(`git fetch origin main:main`, or plain `git fetch origin` from a worktree,
where the first form refuses and that is not a problem to solve), deletes the
merged branch, branches afresh. `guard-main-branch.py` refuses `git commit`
and `git merge` when the target repo — read from a leading `cd` — is on
`main`. Everything else on `main` is allowed.

**Step 1 widened TWICE on 2026-09-07, hours apart, and the second is the
bigger one.** First: Claude pushed and Helen opened the PR; she handed the PR
step over as manual overhead, folding two asks into one. Then she removed the
ask altogether — *"push no longer needs my say so. I had this rule because
multiple Claudes were trampling each other and it's easier to fix that
locally, but I now get Claudes to run Claudes and everything is less
chaotic!"*

**The confirmation was never about the risk of pushing.** It was a lock
against parallel sessions fighting over one checkout, and worktrees (§11.0.1)
plus an orchestrating Claude solved that at the root — so the lock was cost
with nothing left behind it. Read it that way before proposing a new ask
anywhere: a confirmation step is worth keeping only while the thing it
guards against is still possible.

**What did NOT move, and asking again is the §11.2 mistake.** Merging is
Helen's in all three repos. Committing or merging onto `main` is refused by
the hook. Opening a PR is never authority to merge one. Adding
`Pull requests: Read and write` to the PAT was hers to do, and "never broaden
access" is unchanged — that rule is about a session asking for scope
unprompted, not about recording a widening she has made. The token also
cannot delete a ref, so a merged branch goes with `git push origin --delete`,
never `gh pr close --delete-branch` (403).

**A worktree has no `gh`** (§1), so the PR is opened through the REST API,
`POST /repos/DeckOfPandas/helen-triages/pulls`, from a script in `tmp/`.
Measured 201 on 2026-09-07.

**AND SINCE 2026-09-09, ALL THREE REPOS.** This section used to read "AND ONLY
THAT REPO": the same call against either private repo returned 422 `not all
refs are readable`, because creating a PR must read the head ref — a
`Contents` operation — and Helen's fine-grained token carried Issues and Pull
requests but not Contents. **She deleted that token on 2026-09-09**, leaving
`AGENT_GH_TOKEN`, which is classic `repo`-scoped and has Contents everywhere;
a PR on `helen-triages-food-private` was measured working on 2026-09-08 (#25,
closed unmerged). So the old instruction to "say so and let Helen open it" on
a private repo is dead — open it yourself, in any of the three.
`DECISIONS.md` §11 has the retired token's scope tables and why the gap
existed; they describe a credential that no longer exists, so do not re-derive
them.

**Name the issues a PR will close before opening it**, the same rule that
already governs a `Closes #N` trailer: a PR body is the last place the
closure can still be reworded.

### 11.0 The destructive-git hook

`guard-destructive-git.py` refuses `git checkout -- <paths>`, `git checkout
<path>` (it asks the filesystem whether the argument names a file, because no
pattern can tell a path from a branch), `git checkout .`, `git reset --hard`,
`git clean -f`, `git restore` — **when and only when the tree is dirty**.
Clean-tree no-ops, `git stash`, `git restore --staged`, quoted mentions and
heredoc bodies are all allowed, deliberately: a guard that fires on harmless
invocations is one you learn to route around. Known limits: it cannot see a
`cd` earlier in the line; `bash -c "…"` slips through; untracked files count
as dirty. `python3`, no execute bit, because `CLAUDE.md` forbids `chmod`. If
it blocks you, read the refusal: the commonest legitimate case is undoing an
edit you just made, and the answer is to re-edit the file.

### 11.0.0 Prefer LARGER pull requests — every merge is a deploy

Helen: *"I have a soft limit on deploys per hour, so I prefer larger pull
requests where that's practical."* Accumulate related work on one branch, push
once and open ONE PR; keep separate COMMITS per concern. Do not batch when
batching is wrong — an urgent fix, genuinely unrelated changes, another
agent's area — and say what is being held back. **This became a rule Claude
executes rather than one it respects on 2026-09-07** (§11.-1): the number of
PRs is now a session's own choice, so "prefer larger" is an instruction and no
longer an observation about how Helen works.

### 11.0.1 More than one agent shares this checkout — use a worktree

`git worktree add .claude/worktrees/<name> -b <branch> main`. A fresh worktree
has no drafts and no runtimes (§1, §9.1): **CLONE the private repo you need**
into it — never symlink — and, if a promotion batch is open, do not open a
second writable copy (`PUBLISHING_A_DRINK.md`). Never stash, move or commit
another agent's uncommitted work.

### 11.0.2 `/tidy-drafts`

`.claude/commands/tidy-drafts.md` over `scripts/tidy_drafts.py`, both
collections. It fixes FORMATTING — quoting, en dashes, `--`/`->`, accents, the
food `meta:` migration — and never a JUDGEMENT; it never touches a `QQ` line;
every rule is imported from the test suite, never re-typed. On a drink it
touches only Helen's own prose fields (`title`, `tagline`, `to_serve`, a note's
`label`/`text`, an ingredient's `note`) and reports the rest, because four
fifths of a drink's front matter is a closed vocabulary, somebody else's words
or a number. `tests/test_tidy_drafts.py` asserts the whole output byte for
byte on a fixture. A title diverging from its slug is NOT a finding on a draft.

### 11.0.3 `/ingest`

`.claude/commands/ingest.md` over `scripts/ingest_preflight.py`: one list,
grouped by DECISION not by file, so the same ruling arrives once rather than
eleven times. **The return journey for a file from a repo-less session** is
the second section of that command — save on a branch, derive moods for a
drink (it fails exactly one test until then, expected), pytest, `/tidy-drafts`,
work the hand-back list as TIER 3 questions, pre-flight — and **do not redo
the parts that are done**: its prose has been rewritten once already.
`CLAUDE_WEB_INGEST.md` is the web side.

### 11.0.4 `/ingest-inbox`

`.claude/commands/ingest-inbox.md` over `scripts/ingest_inbox.py`
(`INGEST_INBOX_DESIGN.md` §6 is the envelope). The gap it closes is
TRANSPORT: an envelope titled `ingest: <slug>`, labelled `ingest`, on the
PRIVATE repo, pasted by Helen herself (D10). **The parser rejects, it never
repairs**; a matching fingerprint is reported and not written; a matching
title with a different fingerprint is written under its own slug (the
Sazerac case); the version marker is a handshake with a test on both ends
(`SUPPORTED_VERSIONS`). Tested without the network and without her drafts;
an absent drafts repo is a refusal, not a clean inbox.

### 11.1 A file with a colon in its name will crash the whole build

WSL writes `<name>:Zone.Identifier` beside anything dragged in from Windows;
`jekyll-sitemap` dies in `addressable` with `Invalid scheme format` and never
names the file. `_config.yml` excludes `"*Zone.Identifier"`; otherwise
`find . -name "*:*"`.

### 11.2 Do not trust this document over the code

Past versions have been wrong in specific, costly ways, and `DECISIONS.md`
§11.2 is the list. **If the code and this file disagree, the code wins**, and
the fix is to correct this file. **Name files, never line numbers.**

> **AN OPEN ISSUE IS A DOCUMENT TOO, AND IT ROTS FASTER.** Measure any issue
> older than a day before acting on it or repeating it — run the numbers in
> it against the data. Nothing re-reads an issue body; its age is the only
> warning you get. Helen: *"have we not settled this? Now three times or
> more?"* A mechanism stops the data regressing and does nothing about an
> agent re-raising the question in words.

### 11.2.1 Do not ship a layout at a size you cannot look at

If a change only manifests at a size, state or device you cannot produce,
building a way to SEE it is part of the work (#539). A dev page of iframes at
fixed CSS widths (360 / 390 / 320) puts narrow candidates side by side on any
screen, including Helen's iPad, where a 400px breakpoint never fires. Then
delete the losers and the switch. There is no browser in this environment,
which is what makes this a rule.

### 11.3 CSS naming — flat noun for the thing, `--modifier` for its state

Two registers, both deliberate: flat hyphenation names the thing
(`recipe-meta`, `btn-ingredient`); a trailing `--modifier` flags state or
variant, real BEM, base class always present (`badge.badge--matched`). This
is why `test_every_icon_partial_class_has_a_styled_base` checks only the
part before `--`. BEM element syntax (`__content`) is not used. **Do not
attempt a big-bang rename** — apply opportunistically.

---

## 12. Traps you will fall into

One paragraph each here; the story behind each is in `DECISIONS.md` §12.

**You will flag `QQ` as an error.** It is Helen's deliberate placeholder.
Never flag it, never fix it, never convert it.

**You will WRITE DOWN a rule instead of following it**, in the same file, in
the same minute — a four-sentence comment saying `site_key` must be set by
hand, and the line never added. Writing an explanation of a constraint feels
like satisfying it. Do it first, then write the comment; and if the
constraint is worth four sentences, ask what would fail if it were violated,
because that question is a test.

**You will make markup shared and leave its CSS forked.** "Shared" is a claim
about three layers — markup, cascade, assets — and is only true when all
three hold (§2.5).

**You will measure the wrong layer and report the answer as a fact.** A
measurement is only evidence about the layer it ran through; the page is the
only layer that settles anything. Before reporting that a behaviour does not
exist, ask which file would implement it if it did — and if the answer is
DOM wiring, §10.2's harness or a screenshot is the check, not a module call.

**A source-scanning guard will be fooled by the prose explaining it** — six
times in a fortnight, including the destructive-git hook refusing the commit
that introduced it. The vocabulary of a rule is densest in the comment
explaining it. Strip comments and quoted spans before counting; match a call
SHAPE; or parse the AST. **But strip strings only when the guard's failure
direction allows it** — a key is read through a string literal, so
`test_invisible_keys_are_really_invisible` keeps them. Every one was caught by
breaking the thing on purpose and reading the OUTPUT, not the exit status.

**And a parser will read your documentation as code.** Liquid tokenises tags
inside `{% comment %}`; name a tag rather than writing it out. Before quoting
syntax inside a comment, ask whether the thing that reads this file parses
comments or skips them.

**You will add a new link shape and nothing will be watching it.** Recipes
had two guarded link shapes; `](#fragment)` was a third and the suite passed
over a tagline pointing at nothing. `test_same_page_fragment_links_land_somewhere`;
ids flood outward along layout and include edges.

**You will trust a corpus glob that names files instead of finding them.** A
page the corpus cannot see is also a page whose outbound links are never
scanned, silently.

**You will re-add a hardcoded search threshold.** `FAMILY_BUTTON_MIN_CHARS`
is read from `ingredient_words.yml`; a test fails on a literal.

**You will scope a guard by the value it is policing, and it will not see the
rival value.** A guard that filters on the canonical spelling can only ever
see drinks that are already right. Anchor on the FIELD and ask what it holds.

**You will assert a registry is non-empty when emptying it is the goal.** A
ratchet list (`GLASSLESS_ON_2026_08_27`) empties and must STAY empty, so
assert emptiness; a worklist (`proposals`) empties and refills, so assert
only that the KEY exists. Ask which you have before writing `assert thing`.

**A declared exception silences every check downstream of it**, not only the
one it was declared against: a suggestion string that resolves to no bottle
also resolves to no CATEGORY, so the cross-category check skipped it. When
you retire an exemption, expect something unrelated to go red — that is
coverage coming back. **And a registry of declared failures needs a
staleness guard or it rots silently** — a convention stated in a docstring is
not a convention anybody follows.

**You will exempt your own work from a rule written for somebody else's.** A
prefix rule silently widens to cover whatever is added after it (`QQ` grew
`QQ Claude`). When a marker gains a second meaning, revisit every pattern
that matches the first. **And a guard that has never fired may only be
starved**: coverage is proportional to traffic, so before scaling an
operation tenfold, ask which guard is about to see real volume for the first
time.

**A `git fetch` is only good for the moment you ran it.** Re-fetch
immediately before reporting, and say what the fetch showed. `git log
--branches --not --remotes --oneline` is the sweep for unpushed work on ANY
branch; `git log @{u}..HEAD` asks only the branch you happen to be on, which
is how one of Helen's own edits was lost.

**You will write a test that cannot fail and not notice** — the most
dangerous trap because the symptom is green. A stale path, a non-recursive
glob, a shape the regex never considered, a matcher that could not see a bare
element selector stacked on an early return. **When you add a guard, break the
thing it guards and watch it fail.** **Never `return` early because a scan came
back empty — assert it is non-empty**, with a message saying what to do if the
emptiness is legitimate; `test_suite_hygiene.py` enforces it for
non-parametrised tests. **Removing an override is not overriding.**

**You will assume "end of `<body>`" means "loads first".** A page layout's
scripts land inside `{{ content }}`, above `default.html`'s own. `assets.js`
loads at the end of `<head>`; guards exist for the load order.

**You will assume you know how many stylesheets import `shared/`.** Grep.

**You will move a colour and strand the numbers tuned against it.** A number
tuned for a colour belongs to the colour; `-active` tokens are for text on a
fill, not a bare swatch; darkening several warm hues together pulls them to
one muddy brown.

**You will give an element asymmetric padding to compensate for something,
and it is invisible until a later change makes it not.** Any asymmetry "to
compensate for X" is verified only against what is true today.

**You will assume every SVG is formatted the way the last one was.** Match
`<svg` plus whitespace. **And you will read one transform where there are
two** — a transform is a stack; compose the ancestors and bake the result into
the geometry.

**A cross-reference to another file's behaviour is a claim nothing
re-checks.** Three comments said the card template "raises every ratio to a
power"; it never had. `git log -S` over the file that would implement it is
the check.

**You will rename something and silently un-ignore it.** `.gitignore` matches
by name; `test_every_drafts_collection_is_gitignored` derives its patterns
from `_config.yml`.

**A "generator" may have stopped generating, and its own docstring may not
know.** Before running anything that writes a tracked file, run it once and
diff, or copy the file to `tmp/` first; when a generator's output becomes
hand-editable, fix the comment in the GENERATOR.

**You will read the patch and think you have checked the output.** For
anything that rewrites structured text, load the result and diff the PARSED
form; verify against a COPY. **You will rewrite YAML you were only asked to
edit** — parse to check, edit as text; a `yaml.dump()` round-trip loses
comments, order, quoting and the `[""]` `method_short` depends on.

**You will see a force-push rejection and assume something is badly wrong.**
Fetch, diff each "diverged" commit against its counterpart by message; if the
diffs are empty it is a rebase artefact and `--force-with-lease` of the
correct side is the fix.

**The data is cleaner than you think.** If a scan finds "lots of problems",
suspect your findings first — a blank `star_ingredient` is correct for a plain
sponge. **Helen adds drafts while you work** — a failure between two runs is
more likely a new draft; check mtimes. **You will suggest tooling that has
already been rejected** (`jekyll-seo-tag`, Stylelint, a bundler, a CSS
framework, schema.org/Recipe): argue against the recorded reason, in
`DECISIONS.md`, not as if it were never written down.

**You will use `display: flex` for a simple two-part row, then break it the
day one part needs more than one line.** Prefer `position: relative` plus an
absolutely positioned label for "a label plus arbitrary content".

**You will write a bare element selector inside a component, and it will
capture something that does not exist yet.** When a component rule targets a
bare element, ask whether the container will only ever hold one; if "one
today", name the class. No test can catch it (#259, closed rather than
half-built).

**You will forget an element inherits from its parent when nesting inside a
styled heading.** An interactive element inside a punched heading needs
`lettering(plain)`.

**A rule nested under a parent is a bet on where the element lives, and
moving the markup silently voids it.** When you move an element, grep the
compiled CSS for every rule that named its old ancestor. **A condition is a
bet on which field carries the content** — `{% if item.item %}` voided when
`item` stopped rendering.

**You will write a `:not(...)` rule to take space away, and it can only ever
add.** To make a state cost NOTHING, the base must declare nothing.

**A lightness-only colour change is not a state change at small type.** At
small sizes the eye reads hue, not lightness; every interaction state that
works here moves hue.

**A generated sweep over a table proves the predicate, not the table.** When
a generated test keeps missing the same bug, generate the next one from the
other end (`test_every_text_input_on_the_index_has_state_behind_it` reads the
BUILT page).

**A photo "batch" is not one source, and an ordinal count of photos is not a
filename.** Open every photo. **And a capture that ends mid-recipe looks
exactly like a complete one**: transcribe what is in frame and say where it
ended.

**"Lost work" after a disconnect may be sitting in a `git worktree` you have
not looked in.** `git branch -a -v` and `git worktree list` before reporting
anything as lost.

**A `Fixes owner/repo#N` trailer in a PRIVATE repo's commit does not close,
comment on, or even cross-reference the issue** — measured. Still write it;
close the public issue by hand.

**You will loop a collection that `output: false` did not empty.** §9.1.

**You will check one element's width and call the row safe.** Overflow is a
property of the ROW; three sub-320px tracks side by side overflow a phone.
The site has media queries (three, counting print).

**You will assume DOM order decides what paints on top.** It decides only
among peers at the same level; `position` or `transform` promotes an element
into the positioned layer. Reach for `order` rather than moving markup when
the DOM order carries tab order.

**An inline `<svg>` clips its own content by default.** `overflow: visible` on
any icon that touches its own edges.

**Four things the browser does that no test can see** (all found by Helen
looking): an `<input>` does not inherit `color`, `background`, `font-family`
or `font-size` — set them explicitly; `text-shadow` paints under text
decorations, so a mark that must not carry a shadow is a `linear-gradient`
background, not a decoration; `<mark>` arrives with a UA background and
colour, and only the `background` SHORTHAND resets it; a property declared
twice in one block is invisible to `test_no_selector_declares_the_same_property_twice`,
so a mixin takes arguments rather than being overridden after the include.

**Five traps from one design session, and they share a shape** — every one
was in a hand-built replica of the real CSS in a dev page: a stray `*/` in
an inline `<style>` fails silently (a `.scss` file would shout); give every
`var()` in a shorthand a fallback (one unresolvable property invalidates the
whole declaration); a custom property containing `var()` is substituted where
it is DECLARED, not where it is used; retyping a working line is not copying
it; compensate for a fact about object A on object A. **And when the person
who can see it says the same thing twice, stop defending the measurement**
— every number about the box was right and none was about what was painted
in it. The answer to all five: stop replicating and build it for real
(§13.11).

---

## 13. The site's visual design

**The one-line summary:** both food pages use one decorative device — a
blocky two-colour bar overlapping the base of a heading, lettering in front
of it — and differ deliberately on how much COLOUR they spend. Cocktails is
§9.13. The road to every value below is in `DECISIONS.md` §13 and in git.

### 13.1 The mark

`box-decoration-break: clone` on an inline element with a per-line
`linear-gradient` background — not `border-bottom` (draws on the box) and not
`text-decoration` (paints over glyphs). Dials at the top of
`_sass/food/_rule.scss`: `$rule-thickness`, `$rule-drop` (bigger = lower =
less overlap; the single most character-defining value), `$rule-indent`,
`$rule-overhang`, and a second thinner rule beneath sharing the right edge.
**The violet (under) rule is flush with the lettering; the green (top) rule is
inset** — a mark hanging into the left margin reads as broken alignment.

**The mark sits under the LAST LINE only** (design audit critical #7; Helen:
*"Last line only please, 10000%."*). `assets/js/last-line-rule.js` wraps
each word, finds the first word of the last line, and rebuilds the element as
`.rule-lines` + `.rule-last` with `rule-split` on the element; the double
rule is emitted on the ELEMENT first, so with JavaScript off the title still
wears the mark (stacked). `box-decoration-break: slice` is not the fix
(bottom-anchored bars land under the first line); there is no `::last-line`.
Targets are `.recipe-title-text` and `.section-heading-text`; an element
whose text another script rewrites opts out with
`data-last-line-rule="skip"`.

It replaced watercolour washes because an identical repeated mark becomes
something you RECOGNISE rather than READ. Do not re-open this with "a filled
field is more visible" — that argument was made, and lost.

### 13.2 The recipe page's colour budget

Four hues, and the count is the design: `$color-bright-magenta` (title rule,
footer hearts, method toggle, and as `$color-recipe-link` every cross-recipe
link); the two rule colours, spring green and violet, which only ever appear
together inside one mark — and violet's second job, the annotation arrow
beside a note; `$color-aureolin` (the ingredient-amount highlighter).
Everything else is `$color-clear-text` or `$color-border`. **Colour is on what
you navigate by, off what you read.** Magenta carries three jobs and doubles as
`$color-star-root` — one rhyme, not four coincidences: the site's one
"interactive/branded" colour. If a fifth colour is ever proposed, that is the
point to ask whether an existing hue could do the job.

### 13.3 Spacing

A named scale: `$spacing-block-gap` (1.75rem, within a section),
`$spacing-section-gap` (3rem, below a section), `$spacing-section-top`
(4.5rem, above a heading) — deliberately far apart, because a gap only reads
as hierarchy if it is obviously bigger than the one below it. `padding` does
not collapse, `margin` does; **a flex item's margins never collapse**, which
once cost 36px on every drink page.

### 13.4 The index page

Five sections in page order — STAR INGREDIENT, MOOD, PRACTICALITIES, **HAS TO
HAVE / LEAVE OUT** side by side (`.search-pair`), I KNOW WHAT I WANT (the
escape hatch, last on purpose). **META FILTERS is gone entirely**: the
work-state buttons went because Helen does not need the page to ask whether a
recipe is finished, and `draft` went because the ingest phase is largely
done. The `draft` and `magic bag` BADGES on a row stay — they say what you
are about to CLICK. **The universe says… is gone from food** (Helen: *"On a
triage site the panel of choices IS the fold"*; *"I don't think anyone opens a
triage website to click on a random recipe"*); it stays on cocktails.
**Density is the index's own** (`$index-section-gap`, `$index-label-gap` in
`_tokens.scss`), tightened for the fold: the index is a control panel, the
recipe page a document.

#### 13.4.1 The punched-tape effect

**`model_instructions/LETTERING.md` is the reference**: the physics (stroke
sets weight, shadow sets direction, both proportions of the type), the four
tiers, every consumer, the traps. **To extend the device: say the tier** —
`@include lettering(display | heading | label | plain)` — and never write
`-webkit-text-stroke` or `text-shadow` by hand. It is applied from one place,
the `h1, h2, h3` rule in `_sass/shared/_base.scss`; components override
colour and size, none opts in. Two things on the index deliberately do NOT
wear it: the "N survivors" count (plain body text — *"I liked it bare"*) and
the active states of filter buttons and row tags, which are §13.4.2. **`[ FOOD
]` / `[ COCKTAILS ]` (`.site-logo-word`) carries its own four-copy shadow and
no tier** — light type on black tape is a different physical case
(`LETTERING.md` §7–§8). **No square brackets around punched-tape text**:
brackets are the wordmark's device, naming a SITE from `sites.yml`; the
footer's reference block is the one other legitimate use. The test for a
third: *"is it naming a SITE, from `sites.yml`, or is it reaching for
brackets because capitals look like they want some?"*

#### 13.4.2 The other `-webkit-text-stroke` — faux-bold, not an edge

Check the stroke's COLOUR: lighter than the letter is an edge (`LETTERING.md`);
**the same colour as the letter is a faux-bold**, and wants to stay heavy.
Courier Prime ships only Regular and Bold, so `font-weight: 900` is already
Bold and a same-colour stroke is the only way to get "heavier than bold" —
which is what an active filter button needs. They set `text-shadow: none`
explicitly: the punched treatment means "landmark" everywhere else. **An
active filter rule may change colour, `.tag-shape` fill and stroke, and
nothing that changes a box's size** (#389 — letter-spacing on the active
state shifted every tag to its right);
`test_no_active_filter_button_changes_its_own_width` reads the compiled CSS.

### 13.5 The colour contract, and why the two pages differ

**Index: five hues, one per filter section, in page order** —
`$color-bright-magenta` (STAR), `$color-pure-lime-green` (MOOD),
`$color-vivid-cerulean` (PRACTICALITIES), `$color-hot-orange` (HAS TO HAVE —
the variable still says ingredient), `$color-aureolin` (I KNOW WHAT I WANT).
Helen's order, against her own tests: pink first, no two blues adjacent, not
a rainbow. **LEAVE OUT takes no code colour**. On the index colour is a CODE
and must be learned; on the recipe page it is decoration and must be
rationed. **A principled divergence — do not equalise the counts.** One
source: `$color-star-root` and its siblings in `_sass/food/_palette.scss`.

### 13.6 The recipe list

Each row: title, ingredient line, then pills, in that order (§13.6.1). Title
is Courier Prime, lowercase, weight 700, 1.2rem; weights 400 and 500 render
identically (two static faces). **The pills rest MUTED** — a 14% hint of the
hue, grey text — and climb Helen's three-rung ladder: muted → matched (the
middle saturation) → hover (the lightened full hue, louder than matched).
Ingredient line clamped to one line (two below 600px) with a JS-set
`.is-clamped` fade, because CSS has no selector for "this box overflowed".
The category-code bar is gone (four rounds of tuning and Helen still did not
love it; git history if reviving).

#### 13.6.1 Row order and why

Ingredients outrank pills because they carry the recall-lookup case the
search exists to serve — the scan *"makes the decision about opening the page
or not"*.

### 13.7 Results heading, pagination, shuffle

**"N survivors"**, left-aligned, plain body text, no punched treatment —
`.results-heading .category-label` sets every value back to the body default
on purpose. **Pagination**, 20 per page, prev/next, a status label, `(see
all)`; the maths in `recipe-list.js`. **Shuffle** (Fisher-Yates) on clear-all
and on every fresh load; `.recipe-list` starts `visibility: hidden` and is
revealed after the first render, trading a visible flip for a blank instant.
**One arrival is exempt: going back** (#387) restores shuffle order, filters,
page, see-all and scroll from `sessionStorage`, gated on
`performance.getEntriesByType('navigation')[0].type === 'back_forward'` — a
FACT, where the back/forward cache is a favour a browser may decline (and
does, on `jekyll serve`, which sends `no-store`). Half-finished searches are
not restored; a chosen result is. `toQuery()` in `filter-state.js` is still
unwritten because the thing that would have called it did not want it.
`back-link.js`'s one predicate: may this arrow call `history.back()` — a
recipe opened in a new tab carries the index as referrer and no history.

### 13.8 The wordmark

HELEN TRIAGES (display tier) and the bracketed site word on black tape, the
tape sized to the lettering. **Whichever row is naturally wider defines the
width, via CSS Grid, not JS**: `.site-logo` is `inline-grid;
grid-template-columns: max-content; justify-items: center`, both rows in the
one column. On food HELEN TRIAGES is wider; on cocktails `[ COCKTAILS ]` is,
and the tape adapts rather than the word shrinking (Helen's preference).
`$tape-protrusion` (0.2rem) is how far the graphic extends past that core.
`.site-logo-word`'s padding is `em`, because percentage padding here would be
circular. **The shared column must contain ONLY the two things being centred
on each other** — a spanning grid item still contributes to an intrinsic
track's size. **The about page belongs to no site and says so twice**:
`wordmark_word: "??"` and `site_neutral: true` in its front matter (#395,
#398; Helen: *"The name of that page is '??', so wherever a title would
appear it should read '??'."*), while
carrying `site_key: food` for a stylesheet — belonging to no site for DISPLAY
and borrowing one site's CSS are different claims.

### 13.9 The tape background

Seven SVGs in `assets/img/chrome/tape/`, generated by `scripts/generate_tape.py`
(its docstring is the spec): corner shape (`--corner-mode both_acute |
both_obtuse | mixed`, `--seed`), machine marks in 5–7 clusters with at least
one per zone and the two clearest one per flank (`--marks-seed`), an edge
bevel with the same top-left light source as the lettering. No "good one
automatically" mode: generate a batch, look at them against the real header,
hand-pick. `_data/chrome.yml`'s `tape_count` must match the directory and the
run must be gapless (`test_tape_count_matches_the_tape_directory`) —
`decorations.js` rolls a random n. Provenance of the seven (seed / mode) is in
`DECISIONS.md` §13.9. **Still open**: `tape()` picks one of the seven at
random on every load, the exact pattern §13.1 rejects for wayfinding marks,
never revisited for a background texture. Worth deciding out loud.

### 13.10 Typography — three fonts, and the rule for which goes where

Self-hosted, latin subset, relative urls from `assets/fonts/`
(`_sass/shared/_fonts.scss`):

    Selawik        300 350 400 600 700    $font-body      (metric-compatible Segoe UI)
    Courier Prime  400 700                $font-headings  (two weights, like Courier New)
    IBM Plex Mono  600                    $font-label

Every stack keeps the old system font as fallback. The cause was never really
PDFs (#373): with no `@font-face`, every reader saw a different typeface.

#### 13.10.1 `$font-label` — the rule

**IBM Plex Mono is for numbers you act on**: ingredient amounts on food,
drink amounts, the temperature readouts and axis ticks, the timings
calculator's inputs and results. Nothing else — not labels, not badges, not
buttons, not note labels. The rule is not "is this a label" and not "is this
on a recipe page"; both lost to the plainer question underneath. The clash
only works while Plex stays the minority face. `DECISIONS.md` §13.10.1 has the
five elements that held it and came back.

#### 13.10.2 The emboss

`LETTERING.md` §3 has the values. What survives here: `$emboss-stroke` is
0.016em and the offsets are hard whole pixels (a fractional offset
antialiases the whole duplicate glyph into the floating read the no-blur
rule exists to prevent); dark type on a near-white ground has about 3% of
headroom above it, so a light-ground highlight cannot be white and the raised
read comes from the shadow; the tier values are custom properties, not Sass
variables, so a site's `_rule.scss` can re-point them without a specificity
fight. `.on-dark` is deleted: a dark SECTION on a light site wants a context
class, a dark SITE wants its palette inverted, after which every shared
partial follows for free (`git show 0b350c3:_sass/shared/_rule.scss` to
recover the mechanism).

#### 13.10.3 `/dev/emboss/` — tune here, not in a mock

Local only. It tunes the tape wordmark's own four copies by overriding the
live element at the top of the page, and writes the settled values out as
SCSS. A reproduction in a scratch file is a second thing to keep in step with
the first.

### 13.11 How a design decision actually gets made here

**Helen decides by looking, never by argument.** Every visual decision was
made on a CANDIDATES PAGE: the real page, the real compiled CSS, fonts and
artwork, two to five treatments switchable from a bar at the top. Build the
candidates, publish them, let her pick. Do not write a paragraph arguing for
one.

- **`scripts/mock_bundle.py`** bundles a page from a local build into one
  self-contained HTML file (CSS with fonts inlined, scripts inlined, every
  SVG embedded). Build first with `bundle exec jekyll build --config
  _config.yml,_config_local.yml -d tmp/site-mock`; add candidate CSS keyed off
  `html[data-x="…"]`, a switcher, publish as an Artifact.
- **Syntax-check the switcher before publishing** (`node -e` with `new
  Function(src)`); use `json.dumps` for any text going into it; skip
  `type="application/json"` blocks.
- The bundler pins `<main>` to the site's 900px column; measure her
  screenshots against that, not the viewport.
- **Put the real state on the page, not a picture of it**: seed
  `localStorage` for a hidden control; put the object a control is judged
  against on screen.
- **One round settles one question.** Lock what she has decided into the page
  as base CSS; say which questions are still open.
- **Derive numbers, do not pick them, and keep the derivation in `scripts/`**
  (`universe_glass_slot.py`, `universe_line_width.py`); a number derived in
  `tmp/` is one nobody can reproduce.
- **A worktree has no drafts** — clone, or the index renders nothing.
- **Delegation**: a precise spec, reviewed by diff. Tell agents to delete only
  what they created.

### 13.12 Decisions that are Helen's, not yours

Build these when she rules; do not decide them, and do not re-open a ruling by
re-arguing it.

- **Leopard.** `LEOPARD.md`; she holds it. Ship nothing.
- **Any new hue.** Both palettes argue at length that the COUNT is the design.
- **The voice.** Do not touch a word of copy; where a feature needs a string,
  ship a marked PLACEHOLDER — the bitters caveat (#713) is the pattern, and
  the units line (#753) followed it.
- **Whether the recipe title takes the tape.** Offered and declined.
- **Which drinks are faffy, rich, or otherwise judged.** Moods are DERIVED; a
  disagreement goes in `mood_include` / `mood_exclude` with its reason.
- **The `qq:` rows in `abv.yml`.** Only the label on her shelf.

**A ruling is not permanent.** Two were reversed on 2026-09-06 (three
ingredient lines on a card; matched chips keeping their colour) — neither
re-argued into existence; she looked at the built page and changed her mind.
Showing her the thing is always allowed, and is how rulings move.

---

## 14. Reference pages and the internal-temperatures data layer

**BOTH SITES HAVE A REFERENCE LAYER SINCE 2026-09-06.** Most of this section is
food's, which is the older and much larger half; §14.6 is cocktails'. What the
two share is the entry route — a footer column per site, no nav link, no
`index.html` — and nothing else: they do not share a page anatomy, a stylesheet
or a data shape, and "The cocktails reference layer" below says why that is
correct rather than unfinished.

### What exists (food)

`food/reference/` holds two pages: `internal-temperatures.html` (the charts)
and `cooking-methods-and-timings.html` (a weight → schedule calculator plus
the fish and shellfish tables, which are ON the page but not OF it — no
weight to schedule from, and the page says so in a line of its own). No
`index.html` and no nav link — Helen's call; the two footer links
(`reference_links` in `sites.yml`) are the way in, because these pages are
look-up material for someone who already cooks, not a peer of the two sites.
`cooking-methods-prose-archive.html` is committed but not built
(`published: false`): 35 paragraphs of sourcing notes that used to sit in the
data as dead JSON, moved before they were deleted.

Page pattern: `.recipe` / `.recipe-body-content`, the same wrapper as
`about.html`. Tables are `<table>` markup — `food/*.html` is not run through
kramdown. The charts page holds no `<table>` at all: every figure is a
div-based chart drawn by `_includes/food/temp_row.html` from the data.

### The data layer — two datasets

`_data/food/internal_temperatures.yml` is the single source for out-at
temperatures, endpoints and carryover — VOCABULARY layer. **"Out at", never
"pull at"** (pull is American; `test_style.py` knows the phrase). Every figure
is numeric AND a display string, because the strings carry words a number
cannot ("74–75°C in the thigh"); `tests/test_reference_data.py` holds the
invariants, axis bounds, safety-threshold spec and note integrity. Four
shapes: `endpoint` + `carryover` (whole poultry); `doneness: {level: {out_at,
rested}}` + `carryover` (tender roasts, steak, salmon, tuna); `tender_at`
alone (tough cuts); `target` + `carryover` (cured ham). A consumer checks
which keys exist on the resolved node.

`_data/food/cooking_methods.yml` **is the source of truth and is edited by
hand.** `scripts/build_cooking_methods.py` and
`build_cooking_methods_prose.py` are MIGRATION TOOLS pinned to an old commit;
**do not re-run them** — the data has been hand-edited since (the whole
`venison` section) and a re-run overwrites 166 lines. Steak, fish and
shellfish stay hand-written tables (eleven rowspans a generic loop would
flatten).

### Recipe wiring

`internal_temp_ref` is a dot-path (`beef.tender_roast`); `doneness` picks a
level. The resolved figure renders **below Notes, at `#doneness`**, never in
the metadata grid (Helen: *"it's nowhere in sight when you're actually
cooking"*), and the Cook line carries a link. **A live number can only render
somewhere the layout controls** — front matter is never Liquid-templated.
Opt-in per recipe; **a recipe that should be wired and isn't is a test
failure**: `test_every_recipe_with_a_known_protein_has_a_temperature_or_a_reason`
demands a ref or an entry in `NO_TEMPERATURE_BECAUSE` — three kinds: not the
dish, a cut the data does not cover, and (`youvetsi`) a figure that is right
about the cut and useless in the method. Drafts are exempt. `test_internal_temp_ref_resolves`
catches a typo'd path, which Liquid otherwise renders as no section at all.
`safety_min` / `safety_label` / `safety_summary` shade below cited guidance on
`fish.salmon`, `pork.roasting`, `ham.fresh` only.

### Fact-checking status

Every figure has been checked at least once against real sources, cited
under each table. A systematic ~2× error (500g/lb timings muddled with 1kg)
was found and corrected; if a row looks suspiciously fast, suspect that
first. **The "checked once… remove once confirmed" notes are Helen's own
scaffolding**, not errors to fix. **Two flagged food-safety gaps** — pork's
"medium" and fresh ham's "hint of pink" do not clear the FSA's pork figure —
are deliberately not "corrected"; whether to serve pork pink is Helen's call.

### The timings calculator and doneness

Only 2 of 73 methods have the `by_doneness` shape, so there is no page-level
rare/medium control (a control that usually does nothing reads as broken);
both figures render on those two cards. `resolve()` returns a `levels` array
alongside `lo`/`hi`, additive, in data order.

### What's not done

Venison and braised/confit duck legs have no temperature data (four recipes
deliberately unwired). Almost nothing links recipes to the methods page —
temperatures are wired both ways; exactly one recipe links the calculator.
The tables page is gone (#382) and the lesson from its predecessor is about
crosslinks: two views of one dataset must point at each other well, which is
why every protein section on the charts carries a `?protein=` link into the
calculator.

### The cocktails reference layer

One page, `cocktails/reference/rum-categories.html` (#529), built 2026-09-06.
**It is `published: false` and local-only** until Helen signs the copy off; see
§2.5 for the other half of that switch and why both halves must move together.
Deleting the `published: false` line and the `local_only: true` flag is the
whole of shipping it.

**Why it is not the encyclopaedia #459 rules out.** A bare list of the fourteen
categories would be `rum_styles` reprinted. #501 moved a question from the card
to the reader — cards stopped naming bottles and started naming categories — so
*"which of mine is a Demerara rum?"* had nowhere to be answered. **The bottles
column is what carries the justification**, not the category list, and that is
the test to apply to any second page here.

**Every string on it is a lookup.** Categories are `rum_styles`; the short names
are `card_names`; the bottles are the `bottles.yml` entries whose `generic` is
that category; the retired words AND their reasons are `retired_rum_styles`;
Ceylon arrack's note is `family_less`; the sipping shelf is `bottles.yml`'s
`sipping`. Nothing on the page restates a fact the data holds — which is the
failure #314's own closing comment fell into three times over, a rule written
once as a list and going stale with nothing looking.

**Two things it reads that no rule derives, so both are declared and both have
guards:**

| Declared in | What it is | Guard |
|---|---|---|
| `rum_groups` (`ingredients.yml`) | Helen's five shelves — Jamaican rum, Demerara rum, Cane juice, Non-geographical, Flavoured | `test_rum_groups_partition_the_styles`: every style in exactly one group |
| the CASE of a `retired_rum_styles` key | lowercase = a WORD a recipe asks for (shown); capitalised = a BOTTLE whose brand-generic was retired (hidden) | `test_retired_rum_style_keys_split_by_case` |

The first is the important one. **The page walks the GROUPS, not `rum_styles`**,
so a fifteenth style added and not placed would be invisible with nothing else
failing.

**`.ref-*` is its own page anatomy, and food's trick was not available.** Food's
reference pages reuse `.recipe`/`.recipe-body-content` and the only table CSS on
the site — all of it in `_sass/food/`. This site's own anatomy is a DRINK's: a
title block reserving a column for a glass drawing, an ingredients grid built
round an amount column. So `_sass/cocktails/_reference.scss` borrows where there
is something to borrow (the drink page's absinthe-over-violette heading mark;
`.cocktail-suggestion`'s wicked-woowoo for a bottle name, because woowoo means
ASKED FOR and a bottle name here is literally the same value as one in brackets
on a drink page) and draws the rest. **One hue, deliberately** — a second is a
new-hue decision, which is Helen's (§13.12).

**A category with no bottle is correct and is not a gap to fill.** `overproof
Demerara rum, lightly aged` has none since El Dorado 151 came off on 2026-09-05
(*"I don't own it, I just wanted to"*). The generic stays because a drink still
asks for it.

**The prose is not the site's voice yet.** The retired-word reasons were written
for the next Claude — they cite issue numbers and name YAML keys — and render in
full at Helen's instruction (*"I'll copyedit when I get to it"*). That, and five
short strings on the page, are tracked at **#784**. Do not polish them.
