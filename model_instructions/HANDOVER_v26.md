# HANDOVER v26

**Helen Triages** — a Jekyll mono-repo serving two personal decision-support
sites. **Food** answers *what shall we cook*, not *how do I cook*. **Cocktails**
is its sibling: it has real drinks and a schema now, and almost no styling.
Written 2026-08-02, revised 2026-09-01. Supersedes v25 — deleted, not kept, per
house practice: this file has no back-catalogue, only the current version.

**Three things to read before you start.**

**§2.5, the shared chrome** — the biggest structural change since this file was
written: the header and the footer stopped being per-site configuration and
became one artefact. §2.2, §2.3, §9.8, §13.8 and §13.9 all changed with it, and
§12 gained three traps. Read it before touching anything in `_layouts/` or
`_sass/shared/`.

**§11.-1 and §11.0, the two hooks.** These are the executable rules here that
govern the AGENT rather than the site, and you will meet them before you read
about them if you are not careful. `.claude/hooks/guard-destructive-git.py`
refuses `git reset --hard`, `git checkout -- `, `git restore` and `git clean -f`
whenever the tree is dirty; `.claude/hooks/guard-main-branch.py` refuses
`git commit` and `git merge` when the target repo is on `main`. **Two hooks, no
more** — nothing else in `.claude/hooks/` — so do not assume a rule is
mechanically enforced just because this file states it firmly.

**§4.0, the two gate flags.** They decide what publishes and whether Helen's
judgement still covers what is in a file. Every recipe edit touches them.

**This is a rewrite, not a revision**, at Helen's explicit request: "precise
rather than verbose", "strongly consider deleting rather than automatically
appending". v25 was ~1300 lines and had accumulated real bloat — narrated
iteration histories, evidence tables for decisions already made, a 40-row
closed-jobs log going back to v22. Cut hard. If something you expected isn't
here, check git log and git blame before assuming it's missing by accident —
almost everything cut was either resolved, superseded, or fully recoverable
from a commit message written for exactly this purpose.

> ## ⚠ READ THIS FIRST
>
> **Ask Helen questions inline, in conversation, as they come up.** Do not
> batch them, do not park them, do not pick the likely answer and carry on.
>
> **Do not trust this document over the code.** Verify anything you're about
> to act on. Past versions have been wrong — see §11.2. If this file and the
> code disagree, the code wins and this file needs fixing.
>
> **TAG THE ISSUE IN EVERY COMMIT MESSAGE.** `Fixes #N` / `Closes #N` when it
> resolves one, `Towards #N` / `See #N` when it merely touches one, and the full
> `DeckOfPandas/helen-triages#N` form from a nested drafts repo. The rule and
> the reasoning are boxed in §11; it is here as well because it is the one that
> gets forgotten most, and a missed trailer is unfixable after a push.
>
> **§12 is the traps section.** Read it before you touch anything — it is the
> most re-used part of this document. (This box said "§10" from v26's first
> draft until 2026-08-21, pointing every reader at the validation section
> instead. §10 is worth reading too, but it is not the one being recommended
> here.)

**Three companion documents in two kinds, and the kinds point in opposite
directions.** Run `ls model_instructions/` rather than trusting this sentence —
it has been wrong before, and the count is a fact about the repo today.

**`SOURCE_ATTRIBUTION_SPEC.md`** is the full contract for `source` and
`source_type` — the eight types, the exact string shape each one dictates, and
the date rule that separates a `publication` from a `website`. §4 summarises it
and deliberately does not repeat it. It exists because ingestion sessions need
the citation rules without reading 3,500 lines of this.

**`INGEST_ONE_RECIPE.md` and `INGEST_ONE_COCKTAIL.md` are written for a Claude
that does NOT have this repository** — added 2026-09-01 and 2026-09-02, at
Helen's request, for the case where she finds something in the wild and pastes
it into claude.ai with no checkout, no tests and no `_data/`. Each hands back a
draft file plus a short "what I could not know" list.

They stand alone because the closed vocabularies are small: 22 tags and 14 star
ingredients for food; 23 glasses, 42 garnishes and 28 canonical method steps
for drinks. Everything else either file needs is a rule rather than a lookup.

**THE COCKTAIL ONE LEAVES `generic` AND `suggestion` AS `QQ`, ALWAYS, and the
reason is not size.** 224 generics would embed fine. It is that **a bottle's
category is not derivable from the ingredient printed beside it** (§9.3.1,
#314), so a guess is an invention in the field the cards, the search and the
drink page all read. It is also already Helen's standing ruling for a photo
ingest: *"I will update these when I make the drinks, so QQ is right."*
`mood` is `[]` for a different reason — it is DERIVED, by
`scripts/derive_cocktail_moods.py --write`, so hand-writing one is reverted on
the next run.

**THIS PARAGRAPH SAID COCKTAILS WERE OUT OF SCOPE BECAUSE FIVE DATA FILES "DO
NOT EMBED", AND THAT WAS WRONG — measured 2026-09-02 rather than assumed.**
Four of the five are between 41 and 1,034 characters. Only `bottles.yml` and
the generics are large, and those two were never candidates anyway for the
reason above. **The estimate was made from the number of files rather than
their size**, which is §11.2 in one line.

**THE RETURN JOURNEY IS IN §11.0.3**, not here: what to do with a file that
comes back from one of these sessions, including the one command a cocktail
needs before the suite goes green.

**`tests/test_standalone_docs.py` IS THE GUARD, since 2026-09-02.** Nine checks:
every fenced YAML block parses, each worked example obeys the rules its own
document states, and — the half that matters — every garnish, glass, method
step, tag and star ingredient the documents PRINT is still declared in
`_data/`. It runs in one direction on purpose: a retired term left in a
document teaches a value the suite rejects, to a reader who cannot run the
suite, whereas a newly declared term the document has not caught up with merely
under-serves. Helen, on the two `tmp/` scripts it grew from: *"It sounds very
much like they should form part of our suite."*

**Do not let the three drift.** If §4's schema, §5's house style, §7's taxonomy,
§9.3's schema, the garnish or method vocabularies, or the attribution spec
changes, the standalone docs need the same edit — they are the only place in
the repo where those rules are written out a second time, and they were built
that way knowingly, because the alternative was that Helen gets nothing useful
back from a session with no repo. **`tmp/check_doc_example.py` and
`tmp/check_cocktail_doc.py` are the guard**: each extracts the worked example
from its document, parses it, checks it against the live `_data/` vocabularies,
and (for the cocktail one) re-checks every garnish, glass and method step the
document PRINTS against what the collection declares. Both found real faults on
their first run. Neither is in `tests/`, which is a gap worth closing the day
either document is edited by someone who did not write it.

**This paragraph said "No companion documents" until 2026-08-21**, having been
written before the first spec existed and never revisited — while §4, four
hundred lines later, cited the file by name. Its own last sentence said to run
`ls model_instructions/` before trusting it, and nobody did, which is the
smaller lesson inside the larger one: **an instruction to verify is not
verification.**

Two older companions are genuinely retired. `RECIPES_SEEN_v23.md`, a
slug/publish-status inventory, went on 2026-08-11: it saved compute during large
batch ingests from photos, back before the Max plan made that a non-issue.
`DEV_JOBS_v26.md` went on 2026-08-10; the backlog is on GitHub Issues now. Run
`ls model_instructions/` anyway — and this time actually run it.

**Two project slash commands, both in `.claude/commands/`**: `/tidy-drafts`
(§11.0.2) and `/ingest` (§11.0.3). Each is a procedure doc over a script in
`scripts/` that reports and never writes. `/ingest` is the IN-REPO batch
procedure and is a different thing from `INGEST_ONE_RECIPE.md` above, which is
for a Claude with no repo at all.

---

## 1. How to run it

```
jekyll-local        # port 4001, drafts visible — the working view
jekyll-prod         # port 4002, exactly what deploys — no drafts, no meta filters
pytest              # content and structure checks
.node-runtime/node/bin/node --test     # tests/js/*.test.js — no arguments, not system node
```

**`.node-runtime/` DOES NOT COME WITH A WORKTREE**, and neither does
`.gh-runtime/`. They are gitignored, exactly like the two drafts repos (§9.1),
so the line above is "No such file or directory" in a worktree and reads as a
broken checkout. Use the system `node` there — `node --test tests/js/*.test.js`
runs the whole suite. Cost time on 2026-08-29; §9.1 tells you to clone the
drafts and says nothing about the runtimes.

**NEVER RUN TWO `pytest` SESSIONS AT ONCE.** `test_rendered_pages.py` writes two
throwaway recipes into `_food_recipes/` (`zzz-gate-no-flag`, `zzz-gate-old-key`)
to prove the publish gate fails closed, and deletes them after. A concurrent run
collects them as real recipes and reports **14 failures that look like genuine
schema breakage** and vanish on a clean rerun. The tell is `zzz-gate-` in the
parametrised test IDs.

Local URL: `http://localhost:4001/helen-triages/`, then `/food/` or `/cocktails/`.

**`jekyll serve` does not reload `_config.yml`.** Config is read once at
startup — restart the server after any change to it, or you'll debug a site
that's actually fine for an hour.

`_config_local.yml` overrides two things: `show_source_wording: true` and the
`food_drafts` collection. Never put a baseurl in it.

**Never write to machine `/tmp`.** Use a `tmp/` folder inside this repo — it's
gitignored — if you need scratch space. See `CLAUDE.md`.

---

## 2. The mono-repo shape

One Jekyll build, one `_config.yml`, two sites:

```
https://deckofpandas.github.io/helen-triages/food/recipes/<slug>/
https://deckofpandas.github.io/helen-triages/cocktails/recipes/<slug>/
```

### 2.1 Why the collections aren't inside `food/`

Jekyll only discovers a collection at `_<name>` directly under the source
root, or under one shared `collections_dir`. A collection source at
`food/_recipes/` is silently ignored — no error, no output. **Tested, not
assumed.** So the site lives in the collection *name*, and `permalink` does
the routing:

```
_food_recipes/       output: true    permalink /food/recipes/:path/
_food_magic_bag/     output: true    permalink /food/magic-bag/:path/   see §4.3
_food_drafts/        output: false   permalink /food/drafts/:path/  (local only)
_cocktail_recipes/   output: true    permalink /cocktails/recipes/:path/

_layouts/     default.html (shared)   recipe.html (food)   cocktail.html (cocktails)
              magic_bag.html (food, §4.3)
_includes/    filter_group.html   recipe_badges.html
_sass/        shared/{_tokens,_base,_layout}   food/   cocktails/
_data/        sites.yml   accented_words.yml   chrome.yml   food/*.yml
              cocktails/{taxonomy,ingredients,bottles,glasses,methods,garnish}.yml
assets/css/   food.scss   cocktails.scss
assets/img/   favicon.svg   food/   cocktails/
assets/js/    (shared — every script is site-agnostic)

food/index.html        permalink /food/
food/reference/*.html  permalink /food/reference/...   see §14
cocktails/index.html   permalink /cocktails/
index.html              permalink /        a bare redirect to /food/
```

`food/` and `cocktails/` hold each site's **pages**, not their collections.

`_food_drafts/` and `_cocktail_drafts/` are each their own nested git repo
(gitignored from this one — see `.gitignore`), pushed to a private GitHub repo
of its own: **`helen-triages-food-private`** and
**`helen-triages-cocktails-private`**. The food one was `helen-triages-private`
until 2026-08-29 and the pairing was the reason for renaming it — one name said
which site it belonged to and the other did not. GitHub redirects the old name,
so an un-updated remote keeps working and will not tell you it is stale; run
`git remote -v` in `_food_drafts/` rather than assuming. A fine-grained token's
repository selection follows a rename automatically (it is by repo ID, not by
name), so `GH_TOKEN` needs nothing doing to it. `output: false` only stops Jekyll rendering them; the repo
split is what keeps their source out of a public repo regardless of build
config. A draft is promoted to `_food_recipes/` — and so becomes public the
moment this repo deploys — only once it contains no copyright material
(Helen's own words/sufficiently adapted, not lifted verbatim from a
source). This is the actual gate; the private-repo split is what makes it
safe to leave drafts sitting there unpromoted for as long as needed rather
than a reason to promote them faster.

**Practical consequence**: editing a file inside `_food_drafts/` or
`_cocktail_drafts/` from *this* repo's working tree is completely normal
and expected — Helen does it routinely — but `git status`/`git diff` in
*this* repo will never show it, and `git add`/`git commit` here can't
capture it either, because it's a different repo. That's not a sign
anything went wrong or got lost; it's a separate, private history Helen
manages on her own. Don't try to "fix" the missing tracking, and don't
report draft edits as uncommitted/at-risk work in this repo.

### 2.2 Shared versus forked

**Shared**, at the root, names neither site: `_layouts/default.html`;
`_sass/shared/_tokens.scss` (structural, never a palette reference);
`_sass/shared/_base.scss`; `_sass/shared/_layout.scss` (default.html only);
`_sass/shared/_rule.scss` (the punched-tape mixin — moved here 2026-08-02 once
the shared wordmark started using it; see §13.8); `_sass/shared/_chrome.scss`
(the header and footer's colour — added 2026-08-19, see §2.5);
`_data/accented_words.yml` (house style, applies to cocktails too);
`assets/js/*` (no script knows which site it's on); `assets/img/favicon.svg`;
`assets/img/chrome/` (the header and footer's artwork, §2.5); `about.html`.

**THREE files import `shared/`, not two.** `assets/css/food.scss`,
`cocktails.scss`, and `assets/css/longform-demo.scss`. This section said "two,
and that is now the whole list" until 2026-08-19, which was wrong — checked by
grep, not by memory. The third is not a fourth site: it is an additive overlay
`<link>`ed by the two `/food/longform-demo/` pages on top of `food.css`, and it
takes only `shared/tokens` and `shared/rule`, no chrome. So it needed nothing
when the chrome moved. **Grep before you assume the count**, which is what the
next paragraph has always said and what nobody did.

**This used to be three, and the third was a genuine trap** worth knowing
about because it is the shape of the problem rather than the specific file:
`root.scss` styled the two-door landing page at `/`, belonged to neither
site, and was therefore the one nobody thought to check. It broke exactly
that way once, when the punched-tape mixin moved into `shared/_rule.scss`
(§13.4.1) and the first pass updated food and cocktails only. A stylesheet
that compiles for the two sites you look at and fails for the one you never
visit fails silently until someone visits it.

It is gone as of 2026-08-15, issue #204: the landing page is now a bare
redirect to `/food/` with no layout and no stylesheet, so `root.scss` and
`_sass/root/` were deleted with it and `PALETTE_OWNERS` in
`test_site_config.py` is down to two. **The general lesson survives the
specific file**: grep for every `@import "shared/` site before assuming you
have covered them all, because the count is a fact about the repo today and
not a constant.

**Forked**, because cocktails is philosophically distinct, not a reskin:
`_layouts/recipe.html` vs `cocktail.html` (food is a procedure — steps,
prep/cook split, triaged ingredients; a cocktail is a formula plus a build —
a full untriaged spirit bill, a glass, garnishes, an ordered method. **Not
"one method line"**, as this document said until 2026-08-16 — the Sazerac's five steps make a different drink if reordered); `_data/food/*.yml` vs `_data/cocktails/*.yml`;
`_sass/food/` vs `_sass/cocktails/`; `assets/img/food/` vs `/cocktails/`;
`assets/css/food.scss` vs `cocktails.scss` (no shared class names to fight
over).

### 2.3 The palette contract

Shared partials use palette variables **by name and never define them**.
Every site palette owes all TEN: `$color-accent $color-bg $color-border
$color-clear-text $color-mood-root $color-surface $color-text $color-white
$font-body $font-headings`. Omit one and the build fails with "Undefined
variable" pointing at `_sass/shared/`, not the palette that's short one — and it
only breaks the site whose palette is short. `test_site_config.py`'s
`SHARED_PALETTE_CONTRACT` checks the list by name.

**`$color-accent` is the tenth, added 2026-08-19 (§2.5), and it is what let the
chrome stop being forked.** It means *this site's one "interactive / branded"
colour*. Food's resolves to `$color-bright-magenta`, which HANDOVER §13.2
already describes as exactly that job — the title rule, the toggle, every
cross-recipe link and `$color-star-root` are one rhyme, not four coincidences —
so naming it costs nothing and changed no pixel. Cocktails' is a documented
placeholder: that palette is all neutrals until it is argued from real drinks,
so its accent is grey on grey, which at footer size is the lightness-only no-op
§12 warns about. Helen, asked directly: "Cocktail styling is almost totally
unstarted, so this doesn't matter." **When cocktails gets a hue, that one line
is where it goes**, and the footer and nav start working on that site the moment
it does.

### 2.4 `site_key`

`_config.yml`'s `defaults:` sets `site_key` per collection/directory. It keys
into `_data/sites.yml` (title, wordmark, stylesheet, `home`, decoration) and
`_data/<key>/` (vocabulary). A page with no `site_key` belongs to neither
site. **As of 2026-08-15 no such page exists** — the landing page that used
to be the one example is now a bare redirect (§2.1) with no layout at all,
so it never reaches this lookup. `default.html`'s fallback branch went with
it: a future page with no `site_key` gets the repo-level
`title`/`description` and **no stylesheet**, which is a thing to know before
adding one rather than to discover afterwards.

**A PAGE WITH NO `site_key` GETS NO STYLESHEET, AND THIS BIT FOR REAL ON
2026-08-19.** The paragraph above used to end "which is a thing to know before
adding one rather than to discover afterwards". It was discovered afterwards,
within one commit of a root-level page existing.

`about.html` moved from `food/` to the repo root (§2.5), out of the
`path: "food"` default that had been supplying its `site_key`. Its front matter
carries a long comment explaining that the key must therefore be set by hand.
**The line itself was never written.** `default.html` links the stylesheet
inside `{% if this_site %}`, so the tag simply did not render: no fallback, no
broken href, no warning. `/about/` published as raw unstyled HTML and 17,529
checks passed over it, including a full production build and a scan of every
link in that build.

`test_every_published_page_links_a_stylesheet` (`test_rendered_pages.py`) is now
looking, and the reason nothing was is worth carrying: every other assertion in
that file asks about something INSIDE a page. None asked whether the page got
dressed at all. **A root-level page must declare `site_key` in its own front
matter** — the defaults assign it by directory, and there are only two.

**Decoration is opt-in, absence is silent** — still true, but it is no longer
the header and footer that demonstrate it, since those are unconditional now
(§2.5). The live example is `_data/cocktails/glasses.yml`: a glass with no entry
renders no icon rather than a broken one. Missing keys aren't 404s; a key
pointing at missing artwork would be.

---

### 2.5 The shared chrome — one header, one footer

**Settled 2026-08-19, issue #374** (closing #288 and #289 with it). Helen: *"I
don't want parity between two footers — I want one footer for the whole site.
And one header. Literally the same code and assets."*

**That is a stronger claim than "both sites render the same partial", and the
gap between the two is the whole point.** The chrome was already emitted by one
shared template and was still three different things by the time it reached a
page:

- **Markup.** The nav was built from per-site keys (`home_icon`,
  `switch_site`/`switch_icon`, `about_url`), each independently optional. Food
  declared all of them; cocktails declared none, so **cocktails rendered no
  header nav at all**, for weeks, with a green suite.
- **Cascade, and this is the half nothing could see.** Rules for classes the
  *shared* template emits lived in `_sass/food/`: the footer's four link
  hovers, the nav row's hover, and the two nav **icon shapes**. So on every
  cocktails page the cloche and the martini in the shared header had no rules
  whatsoever and rendered as raw unstyled SVG. Each rule carried a comment
  explaining why it had to be food-only, and each reason was true — they want
  the hot magenta, which was not a contract variable. The conclusion drawn from
  it ("cocktails gets a plainer version until it wants its own") was the bug.
- **Assets.** `assets/img/food/tape/` and `assets/img/cocktails/tape/` held
  seven byte-identical files, kept in step by hand as a standing rule after
  they drifted for five days (#223).

Where it all lives now:

| Thing | Where |
|---|---|
| The one header and the one footer | `_layouts/default.html` — **no `site_key` branch anywhere in either** |
| Their structure | `_sass/shared/_layout.scss` |
| Their colour | `_sass/shared/_chrome.scss` — the only shared partial naming `$color-accent` |
| Their artwork | `assets/img/chrome/` (`tape/`, `hearts/`) |
| What is left of chrome config | `_data/chrome.yml` — which is `tape_count`, and nothing else |
| How a script fetches it | `HTF.chromeAsset(path)`, a third helper beside `asset`/`siteAsset` (§3) |

`_data/sites.yml` keeps only what says WHERE YOU ARE: `title`, `word`,
`description`, `css`, `home`, `icon`, `reference_links`. **The test to apply
before adding a key: does this say where you are, or does it say what the chrome
is?** The second belongs in `chrome.yml`, or nowhere. `RETIRED_SITE_KEYS` in
`test_page_links.py` fails if any of the seven removed keys reappears, because
the template no longer reads them — a silently-ignored key is worse than a
missing one.

**The nav is one row, the same everywhere**: one icon per site in `sites.yml`,
in that file's own order, then the `??` about link at a literal `/about/`.
Reordering `sites.yml` reorders the row; there is no second place to change.

**The footer's reference block is a column PER SITE, gated on having material**
— Helen's call, not "the current site's column". So food's two links appear in
the footer of a cocktail page today, and a `[ COCKTAILS ]` column appears the
day cocktails has reference pages of its own, with no template change. The
hearts are pinned to grid column 2 for exactly this reason: under auto
placement a second column would push the graphic out of the centre, which is a
layout break arriving with a *data* edit.

**Two guards, and neither substitutes for the other:**

- `test_the_header_and_footer_are_identical_on_every_page` compares the
  **rendered HTML** of the nav row and the whole footer across a food page, a
  cocktails page and a recipe. Byte-identical, no normalisation — anything a
  page may vary is by definition not chrome, so if this ever needs an exception
  carved into it, that exception *is* a second header arriving.
- `test_every_chrome_class_has_a_rule_in_every_site_stylesheet` compares the
  **compiled CSS**, derived from the template *and* the icon `.svg` partials,
  since five of the eight missing rules were inside those. It checks divergence
  only, not "styled somewhere" — that is a different claim, and the one #396
  went on to make separately (below).

The markup guard would not have caught the cascade fork, and the CSS guard
would not have caught the missing nav. **"Byte-identical" is a claim about the
built output, not the source** — Jekyll runs the template once per page and
writes ~90 separate files, so one template can still produce divergent pages,
and the output is the only place that shows.

**The one thing the chrome still varies is the wordmark**, which is its job:
`[ FOOD ]` / `[ COCKTAILS ]` says where you are. It sits in `.site-title-link`,
above the nav row, so it is already separated in the markup from everything the
guards compare. See §13.8 for `wordmark_word`, the one page-level override.

---

## 3. The three-layer rule

```
VOCABULARY      what exists          _data/**/*.yml
PRESENTATION    how it looks         _sass/<site>/_palette.scss, _data/food/filter_sections.yml
BEHAVIOUR       what it does         assets/js/*.js
```

Each layer knows nothing about the layer above it:

- **`_sass/<site>/_palette.scss` is the only place any colour is written
  down.** JS reads the palette from CSS custom properties; SVGs use
  `currentColor`.
- **`_data/food/taxonomy.yml` is the only place food's tags and star
  ingredients are declared.** An undeclared tag renders nowhere and fails the
  suite.
- **`assets/js/assets.js` is the only place a base URL or site key is derived,
  or a file fetched.**

Helen's underlying principle: *the data model must not assume anything about
or impose anything on the data.* Manipulation belongs in another layer or the
front end.

**Split inside BEHAVIOUR, once a module gets non-trivial:** pure algorithm
apart from DOM wiring, so it can be tested with Node directly. Counts move —
run `.node-runtime/node/bin/node --test tests/js/*.test.js` rather than quoting
from here.

| Module | Holds | Tested by |
|---|---|---|
| `assets/js/ingredient-search.js` | The matching/ranking algorithm | `tests/js/ingredient-search.test.js` |
| `assets/js/recipe-list.js` | Shuffle (Fisher-Yates) and pagination maths | `tests/js/recipe-list.test.js` |
| `assets/js/filter-state.js` | What the index's filter state IS, and serialising it | `tests/js/filter-state.test.js` |
| `assets/js/cook-schedule.js` | The timings arithmetic | `tests/js/cook-schedule.test.js` |
| `assets/js/back-link.js` | Whether the back arrow may use history (§13.7) | `tests/js/back-link.test.js` |
| `assets/js/cocktail-search.js` | The drinks index's pool, ranking and matching (§9.3.3) | `tests/js/cocktail-search.test.js` |
| `assets/js/filters.js` | DOM wiring, food index — its two DECISIONS moved out, #506 | wiring not directly tested |
| `assets/js/cocktail-index.js` | DOM wiring, drinks index | Not directly tested |

**`filter-state.js` HOLDS TWO TABLES, NOT ONE, since #579.** `create(spec)`
binds the mechanism to a spec; `FOOD_FIELDS` and `COCKTAIL_FIELDS` are the two,
and the food-shaped exports are that binding over the first, so `filters.js` is
untouched by the parameterisation. `orderByBand` in `ingredient-search.js` is
shared the same way — the ordering discipline, not the bands.

**IT ALSO HOLDS TWO SHAPES, AND TAKING A NAME OFF THE WRONG ONE THROWS.**
`HTF.filterState` is the MODULE (`parseQuery`, `excludesRow`,
`rowMatchesFilters`, `arrivedByGoingBack`, `create`, the two tables);
`HTF.filterState.create(SPEC)` returns a BINDING of seven spec-bound functions
and nothing else. `filters.js` holds the first, `cocktail-index.js` the second.
On 2026-08-31 the drinks index read `arrivedByGoingBack` off the binding —
`undefined`, and calling it took out the whole tail of that file: the restore,
`apply()` at startup (so the index stopped filtering and shuffling), and the
save listener. **Every JS test stayed green**, because each asks a pure module a
question and the fault was in the wiring between two.
`test_a_filter_state_binding_is_only_asked_for_what_it_has` reads both export
blocks and fails on any name read off the shape that lacks it.

**#506 MOVED THE FOOD INDEX'S TWO DECISIONS OUT OF `filters.js`**, which had no
tests at all: `FilterState.rowMatchesFilters` (is this row one you asked for?)
and `IS.entriesMatchKey` (does a row answer a picked ingredient — asked by both
the include filter and the exclude umbrella, so it is one function). The
EXCLUSION deliberately stayed a second call at the call site: `filters.js` runs
it last on purpose, and that ordering is what makes the excluded COUNT mean
"survived everything else and was dropped only for what it lists".

**Behaviour-preservation was checked, not asserted**: the old predicate was
re-implemented from git and run against the new one over a real build — 429 rows
× 890 filter states, 381,810 decisions, identical on every pair — and then the
check was broken on purpose to confirm it could see a difference.

**`back-link.js` is the clearest argument for this split in the repo**, and it
earned the place within an hour of being written. Its whole content is one
predicate — may this arrow call `history.back()`? — and the first version got
the new-tab case wrong: a recipe opened in a new tab still carries the index as
its referrer, so the check passed while the tab's history held one entry and
`back()` did nothing at all. Invisible to every other kind of check here (the
markup is right, the href resolves, the class has a rule, the build is green),
and trivial to pose once the decision takes its inputs as arguments: "came from
the index, but this tab has no history". A browser cannot be asked that
question; a pure function can.

**Three asset helpers, and each name carries the claim it is making.**
`HTF.asset(path)` is for genuinely shared files. Anything under a *site's own*
image directory goes through `HTF.siteAsset(path)`, which builds the path from
the page's site key and returns `null` on a page belonging to no site. The
header and footer's artwork goes through `HTF.chromeAsset(path)` (added
2026-08-19, §2.5), which never returns `null`, because chrome renders on every
page including one belonging to no site.

A script may not know which site it's on — a test forbids reaching into
`assets/img/food/` from JS directly. `chromeAsset` is deliberately a third
function rather than a call to `asset()`, so that
`test_artwork_fetches_go_through_site_asset` can keep banning any image path
built through `asset()`, with no exception carved out. (That test greps source
text and cannot tell a comment from code, so a comment quoting the banned call
literally will fail it. Ask how a guard works before rewording around it.)

---

## 4. Recipe front matter (food)

```yaml
title: "Lemony Cavolo Nero and Butter Bean Soup"
tagline: "It's fun to have a one-pot stew that is bright and acidic..."
source: "Adapted from Good Food, January 2026"
source_type: publication              # required; see SOURCE_ATTRIBUTION_SPEC.md
serves: "4"                      # xor makes: — never both. QUOTED, see below
prep_time: "20 mins"
cook_time: "1 hr 30 mins"
main_ingredients: ["cavolo nero", "butter beans", "lemon"]
star_ingredient: "greens"        # optional; ~a quarter are legitimately blank
internal_temp_ref: beef.tender_roast   # optional; see §14 — most recipes have neither this nor doneness
doneness: medium_rare                  # optional, only alongside internal_temp_ref; see §14
tags: ["soup"]
ingredient_groups:
  - name: soup                   # bare noun — template adds "For the "
    items:
    - amount: "400 g"
      item: "butter beans, drained"
      note: "Jarred are worth it here."
    - item: "vegetable oil, to fry"
      incidental: true              # optional; see "Easy to get wrong" below
method:                          # xor method_groups: — never both
  - "Step text."
  - step: "Step text."
    note: "An aside."
method_short:
  - ""                           # [""] = not written. A block scalar = written.
notes:                           # always a list, never a blob
  - label: "Sinking"              # or a bare string — see below
    text: "If it sinks, you added too much syrup."
meta:                            # EXACTLY these three, in this order — see §4.0
  rewritten: false
  awaiting_fix: false            # true  = held back, and Helen HAS read it — §4.0
  proofread: false               # false = Helen has not blessed THIS text
```

**EVERY SCALAR STRING IS QUOTED, AND EVERY LIST MEMBER TOO.**
`SCALAR_STRING_FIELDS` in `test_front_matter.py` is the list — `title`,
`tagline`, `source`, `prep_time`, `cook_time`, `star_ingredient`, `makes`,
`serves` — and `main_ingredients`/`tags` members are checked as well. The block
above showed `serves: 4`, a bare `lemon` and the retired tag `one-pot` until
2026-09-01, having been written before the quoting rule and never re-read
against the corpus, where all 86 recipes quote every one. **A schema example is
copied more often than it is checked**; `/tidy-drafts` fixes the quoting
mechanically, which is exactly why it went nine days unnoticed here.

**`meta:` is three flags and nothing else, since 2026-08-21 (issue #429), and
the ORDER is enforced.** `test_meta_block_is_exactly_the_three_flags_in_order`
requires `rewritten -> awaiting_fix -> proofread`, which is the order a recipe
actually moves through them. `cooked_before` and `date_last_edited` were
retired in the same pass — both were read by nothing, and `date_last_edited`
was a hand-maintained date git already knew exactly. `meta.claude_rewritten`
(§4, below) is optional and additive and is the one thing that may legitimately
appear alongside the three on a DRAFT; no published recipe carries it today.

**`cooked_before` took a real guard with it, and the reasoning is worth
knowing** rather than rediscovering. `test_cooked_before_is_true` required it
`true` on every published recipe, enforcing "I never want to publish anything I
haven't tested". It looked like a test asserting a constant — all 82 said
`true`, it had never fired — but 330 of the 344 drafts said `false`, so it sat
exactly on the boundary those files cross: it was a promotion gate. Helen's
ruling, asked directly: promotion is not a step where the question can be open.
Every recipe is cooked-and-liked (she promotes it), cooked-and-disliked (she
deletes it), or not cooked ("why would I put it on my battle tested site?").
The field recorded an answer that promotion itself already gives. There is a
tombstone in `tests/test_front_matter.py` with the full story and how to
restore the check if it is ever wanted back.

**`source_type` is required alongside `source` (issue #406) — the full contract
is `model_instructions/SOURCE_ATTRIBUTION_SPEC.md`, not repeated here.** One of
exactly eight values (`publication`, `book`, `website`, `author`, `person`,
`place`, `joke`, `unknown`), each dictating the exact shape `source` must take
— page numbers, publisher parentheticals and series-name asides are never part
of any shape, so don't add them. `source_type` renders nowhere — it's listed in
`INVISIBLE_KEYS` (see §4.0), so setting or correcting it never invalidates
`proofread`.

**Enforced since 2026-08-20 by `tests/test_source_attribution.py`** (this
paragraph said "no test enforces any of this yet" until then, and that was the
gap). Six rules, over every recipe *and* every draft — drafts deliberately
included, because a draft that drifts is a promotion that drifts. `source_type`
is also in `REQUIRED`, so a recipe without one fails.

The rule most likely to catch you out, and the only one worth repeating here:
**the date is what separates a `publication` from a `website`.** A publication
must carry a date; a website must not. A year alone is a complete date, because
an online magazine has no publication schedule. `Good Food` is genuinely both —
some drafts cite the October 2025 print issue, others the site with no date at
all — so *if you have no date, it is the website*. Sixty-four drafts were
retyped on that rule.

**`meta.claude_rewritten` (optional, issue #418) records that Claude took a tidy-up
pass at a draft — suggesting `main_ingredients`, ingredient/method groups, and
smoothing wording toward Helen's voice — not that the recipe is actually
rewritten.** `meta.rewritten` is the real claim, and only Helen sets it true.
Request a pass either directly ("tidy this one up for me") or by dropping
drafts into `_food_drafts/to-rewrite/`. Helen built out a full three-stage
staging pipeline the same day this landed: `to-rewrite/` (waiting for a
Claude pass) → `to-cook/` (tidied, good enough to actually cook from) →
`to-promote/` (schema-clean, ready to move to `_food_recipes/`) — after
finishing a pass, move the file into `to-cook/` yourself rather than leaving
it in `to-rewrite/`. **All three subfolders ARE read by the draft test suite,
since 2026-08-20.** `conftest._load` used `glob("*.md")`, which was right while
`_food_drafts/` was flat and meant the staged files were silently unscanned the
moment the pipeline existed — seven of them, and they are the ones *closest* to
publication. It now uses `rglob`, so a staged draft is held to every draft rule
like any other. Issue #418 says the opposite and predates the change; Helen's
ruling on 2026-08-20: *"your system is fine with to-rewrite, and I'll use it
properly"* — i.e. staged files are expected to be suite-clean, and anything too
raw to pass stays out of the pipeline rather than the pipeline staying out of
the suite. **`QQ PLACEHOLDER` survives a
Claude-assisted pass.** Tidying structure and wording is not the same thing as
Helen actually rewriting a step in her own voice — the marker only comes off
once she says so, same reasoning as the `proofread` rule in §4.0.

**THE PIPELINE STILL STANDS AFTER THE 2026-08-31 UNIVERSAL REWRITE PASS. ITS
ENTRY LEVEL JUST WENT UP.** Every draft that can carry a `QQ Claude` line now
has one (264 of 267 — the three exceptions are #637/#638/#639), so `to-rewrite/`
no longer means "waiting for a Claude pass": the pass has happened everywhere.
I read that as making the folder redundant and said so, and Helen corrected me
on 2026-09-01 — she needs it, for two reasons a flag has no word for:

> "with all the love in the world, I'm likely to want to cast my eyes over what
> you've rewritten for me even though I predict it will be pretty good. At the
> point of being about to cook I'll also delete any original lines that have
> been totally superseded by yours, leaving me less to pick through in the
> kitchen."

So `to-rewrite/` is where she reviews **your** prose, and the transition out of
it is a real edit she makes: dropping the `QQ original` line wherever the
`QQ Claude` line has fully replaced it, so what reaches `to-cook/` is a method
she can read at the hob without stepping over the source. That is a judgement
about her own kitchen and is not automatable — **never delete a `QQ original`
line yourself.** The correction generalises: the folders are how Helen tracks
*her* work, and reading them as duplicating the flags gets it backwards (§11.0.2
records the same mistake made about `to-cook/` two days earlier). Considered
and rejected for now: renaming `rewritten` → `human_rewritten` for symmetry —
would touch every file in `_food_recipes/` and interact with the
`proofread`-invalidation rule.

**That rename is UNBLOCKED as of 2026-08-21 (issue #428), and the two-day story
of why it was blocked is the useful part.** Nothing reads `meta.rewritten` — no
layout, include, plugin or script. It is render-inert exactly like
`source_type`, so on the merits it always belonged in `INVISIBLE_KEYS`, and the
rename always would have invalidated no proofread.

What actually stood in the way was the GUARD, not the key.
`test_invisible_keys_are_really_invisible` word-grepped the render surface, and
one COMMENT in `assets/js/ingredient-search.js` contains the English word
"rewritten" — about ingredient text, nothing to do with the key. So a key that
qualified could not be listed. That guard now strips comments per language
before matching (§12, and the constant's own comment), `meta.rewritten` went on
the list, and **the measurement taken before adding it was that it releases
ZERO recipes from `proofread: false` today** — it was purely forward-looking,
which is exactly the condition under which widening that list is safe.

**IT CAME OFF FOR ONE COMMIT ON 2026-09-02, AND WENT BACK THE SAME DAY.** A
local-only drinks include drew a `needs rewrite` badge off it, so the key was
read on the render surface and the guard said so in the very next run; the
entry was removed, the measurement taken first was again ZERO recipes affected.
Then the include itself was reverted (#562's argument applies to drink cards
too — §9.1.1) and the entry was restored. Note what the episode exposed, which
outlives it: food's own `food/index.html` has read `recipe.meta.rewritten` all
along — twice, once deciding whether a row renders at all — and the scanner
never saw it because `RENDER_SURFACE` covers `_layouts`, `_includes`,
`_plugins`, `assets/js` and `scripts`, **not pages**. So the paragraph above
("nothing reads it — no layout, include, plugin or script") is true only of
the four directories it names. A `rewritten` → `<something>` rename would
invalidate proofreads, and the honest fix if that rename is ever wanted is to
widen `RENDER_SURFACE` to pages and see what else falls out.

`show_source_wording` in `_config.yml` is an unrelated CONFIG flag governing
whether unrewritten recipes publish at all. It shares a substring and nothing
else, and it is the obvious trap for anyone grepping this out.

**Three earlier accounts of this were confidently wrong**: that the rename was
cheap because `INVISIBLE_KEYS` exists (it was not, but not for the stated
reason); that `meta.rewritten` is read by two files (it is not — both hits were
comments); and this paragraph's own previous version, which named the guard's
bluntness as a permanent blocker rather than a bug to fix. Run the greps
yourself before acting on any of it.

**`short_name` retired 2026-08-12, GitHub issue #169.** Confirmed zero
references anywhere in `_layouts/`, `_includes/`, `assets/js/`, or `food/`
before removal — every recipe carried the field, nothing ever read it. All
~90 `_food_recipes/` files and ~310 `_food_drafts/` files had the line
removed in one pass; `test_no_retired_fields` (test_front_matter.py,
test_drafts.py) now guards against it reappearing, same as `published`/
`date_added`/`difficulty`/`nutrition`/`filling_note`/`headline_ingredient`.
If you find yourself wanting a shortened display title somewhere, that's a
real gap the field used to paper over without actually filling it — raise
it fresh, don't resurrect the old field.

### 4.0 The two gate flags — READ THIS BEFORE EDITING ANY RECIPE

Both live under `meta:`. They look like bookkeeping. They are not: one decides
what reaches the live site, the other decides whether Helen's judgement still
covers what is in the file. Hardened 2026-08-18; issues #331, #367.

---

> ## THE RULE
>
> **If you edit a recipe file, set `meta.proofread: false` in the SAME commit.**
>
> Every edit. A typo, a hyphen, a wording tweak, a note, an ingredient group
> rename. There is no "too small to matter" — the flag does not record how big
> the change was, it records whether Helen has read what is now in the file.
>
> She is the last human judgement before a recipe publishes. The moment an agent
> changes the bytes, her proofread describes a file that no longer exists.

---

**Why the rule needs stating this plainly:** on 2026-08-18 twelve proofread
recipes were edited in one commit — a wording change to eight of them, a note
added to two, an ingredient group renamed — and not one flag was touched. Every
one of those edits was defensible. None of them was flagged, because each looked
too small to bother with, and nothing was looking.

`tests/test_front_matter.py::test_agent_edited_recipes_are_not_marked_proofread`
is now looking. It reads git history: if a recipe's newest commit carries a
`Co-Authored-By: Claude` trailer, that file must say `proofread: false`.

Three things about it that will otherwise waste your time:

- **It reads COMMITTED history**, so it fires on the run *after* your commit,
  not before it. It will stop a bad merge; it will **not** stop you committing
  the omission. Set the flag while you edit, not when the suite complains.
- **`BASELINE_COMMIT` grandfathers everything up to and including itself** —
  currently `9306cef`, moved there 2026-08-20 (from `366f392` earlier the same
  day, from `9c70675` before that, from `dc2a7bf` before that — check the
  constant itself rather than trust a number quoted here, it moves and it has
  moved four times). Each move was Helen reviewing the change herself and saying
  so: the first three were sweeping and content-free, and the latest was the
  opposite shape — she asked to be walked through a nine-recipe citation backlog
  one file at a time, was shown the old line, the new line and the reason for
  each, and answered each individually. Two she changed rather than approved.
  **Measure before moving it.** The constant's own comment now insists on the
  question "how many recipes is this rule currently holding at `proofread:
  false`?" — the answer was zero both times on 2026-08-20, which is what made
  the moves cheap; the identical move a week earlier, over eight held recipes,
  would have quietly asserted something false about all eight.
- **Moving that baseline forward is Helen's to grant, never yours.** If she has
  reviewed a change line by line, move it and say so in the commit message.
  Never move it to make a red test go green.
- **Two narrower escape hatches exist besides the baseline, added #417.**
  `INVISIBLE_KEYS` names front-matter keys nothing ever renders — four today:
  `source_type`, `meta.rewritten`, `meta.cooked_before`, `meta.date_last_edited`.
  (`meta.rewritten` left the list for one commit on 2026-09-02, when a
  local-only drinks include drew a badge off it and the guard threw the entry
  out; the include was removed the same day per #562 and the entry restored —
  which is the guard doing its job in both directions.)
  A commit that changes ONLY those keys, with the body byte-identical, doesn't
  need `proofread: false`, and `test_invisible_keys_are_really_invisible` scans
  the actual render surface to keep that claim honest rather than trusting it.
  `HELEN_CLEARED` names individual recipes Helen has cleared by hand when the
  baseline would be too blunt (it grandfathers EVERYTHING at or before a commit,
  which is wrong when some recipes need releasing and others are deliberately
  still held) — 14 entries today, 13 of them from one 2026-08-21 session where
  she reviewed 14 en-dash edits line by line before any was made. Both are for
  cases the baseline doesn't fit, not a way round it — read the constants' own
  comments in `tests/test_front_matter.py` before reaching for either.
- **"Nothing changed" and "I cannot tell what changed" are opposite answers**,
  and conflating them cost 86 recipes their proofread flags until 2026-08-21
  (#429). `_only_invisible_keys_changed` compared parsed VALUES and then asked
  `bool(changed) and changed <= INVISIBLE_KEYS`, so a commit that changed no
  value at all — reordering the `meta:` block for legibility, say, since YAML key
  order is not a value — produced an empty set and fell through to "not exempt".
  The body is compared byte-for-byte and returns early, and any value that really
  differs still lands in `changed`, so an empty set can only mean the same file
  spelled differently. It is exempt now. **The general shape is worth carrying:
  a guard that fails closed is right to, but only when it genuinely does not
  know.**

**Stage explicitly. Never `git add -A`.** A sweeping add swept up one of Helen's
own uncommitted typo fixes on 2026-08-18, which put *her* edit inside an
agent-co-authored commit and correctly tripped the rule. The repository cannot
tell your edit from hers; only the staging can.

**A recipe publishes only if it says `awaiting_fix: false` AND
`proofread: true`. Nothing else publishes.**

Not "true hides it" — **an explicit pass on BOTH flags is the only thing that
lets a page through.** Either flag missing, `awaiting_fix` left under its old
hyphenated name, either value quoted as a string: all held back.
`_plugins/publish_gate.rb` removes the document from its collection at
`:post_read`, so it gets no URL, no sitemap entry and no place in
`site.food_recipes`. Its log line names which flag held each page back
(`slug (proofread)`, `slug (awaiting_fix)`, `slug (no meta)`), because "held
back 6 pages" leaves you diffing front matter to find out why.

The two flags are not one fact spelled twice, which is why requiring both is
not the mistake the `published:` paragraph below refuses. `awaiting_fix` is a
bookmark in Helen's own review — see her words further down — and `proofread`
is whether that review still describes the bytes. A page is routinely
`proofread: true, awaiting_fix: true` (read, one thing ticketed) or
`awaiting_fix: false, proofread: false` (no ticket, and an agent has touched it
since she read it). Neither value can be derived from the other.

**It fails CLOSED, and it used to fail open.** Helen's call, 2026-08-18. The
first version hid a document only on an explicit `true`, which meant every way
of getting the flag wrong ended with the page live — a missing key was
indistinguishable from a deliberate clearance, and `awaiting_fix: "true"` is a
string that never equals Ruby's `true`, so it published the page you had just
flagged. This is the gate that decides what the world sees; the cost of failing
closed is that a new recipe does not publish until someone writes
`awaiting_fix: false`, and that is the right cost.

**IMPLEMENTED 2026-09-02, issue #667: `proofread` GATES PUBLICATION.** Helen's
intent had always been that `proofread: false` blocks a page from the live
site, on both sites — *"this is the very last touch that I, the human, make to
the file"* — and the plugin did not do it: it published on `awaiting_fix: false`
alone and never read `proofread`. The audit earlier the same day recommended
leaving the one-field gate, citing the plugin header's "two fields that must
agree will disagree" argument, and that was wrong: that argument is about a
`published:` key duplicating `awaiting_fix` — two fields, one meaning — and
`proofread` is a *different fact*.

`_plugins/hide_awaiting_fix.rb` is now **`_plugins/publish_gate.rb`**, renamed
because a name describing half a rule is worse than no name.

**What the change took off the live site, and it was the point rather than a
side-effect.** Five food recipes were live unproofread and are now held back
until Helen reads them: `wagamama-yakitori-sauce`, `youvetsi`,
`sweet-potato-chocolate-brownies`, `wagamama-teriyaki-sauce`,
`duck-a-lorange-sanguine`. Six pages appear in the build log, not five — the
sixth is `_food_magic_bag/fridge-end-fried-rice.md`, and it exposed a hole:
the magic-bag schema was `meta: {awaiting_fix}` and deliberately nothing else,
so that collection could not publish at all once the gate asked for a key its
own schema forbade. **Helen's ruling, 2026-09-03: the magic bag must be able
to publish, so `proofread` joins its schema** — required, `false` by default
on a new entry like everything else at ingest, hers to flip once she has read
the built page. `rewritten` stays out of the magic bag (no source to rewrite
from). §4.3 and `tests/test_magic_bag.py`'s `META_KEYS` carry the two-flag
shape; the one existing entry says `proofread: false` and is held back until
she reads it.

The one exception to "she is the last touch" is unchanged: a trivial fix she
requests, which Claude makes with `proofread: false` in the same commit, and
she re-reads the affected line and sets `true` herself.

The cocktail side of the same ruling — all three flags, same names, same order,
on every drink — is **§9.1.1**, and landed with this.

**WHAT `awaiting_fix: true` MEANS TO HELEN, in her own words, 2026-09-01 —
and it is not what "unfinished" would suggest.** It means she **has** proofread
the page, found one small thing wrong, and raised it as a ticket:

> "'awaiting_fix' means I've proofread, but one small thing has been raised as
> a ticket, meaning that once that's fixed I can look for just that one thing
> rather than having to read the entire file again carefully."

So the flag is a **bookmark in her own review**, not a marker of incompleteness.
Its whole value is that it survives the fix: when the ticket is closed she reads
one line instead of the file. Two consequences that bite:

- **A flagged page has been read.** Do not treat `awaiting_fix: true` as
  permission to make further edits to the file "since it's held back anyway" —
  every edit past her proofread costs her the saving the flag exists to give
  her, and `meta.proofread` must go `false` in that same commit regardless
  (§4.0, issue #367).
- **`true` and ABSENT are not the same state**, even though both hold the page
  back. `true` says she has read it; absent says nobody has. This is exactly
  why `scripts/tidy_drafts.py` reports the two drafts with no flag rather than
  writing `false` into them — writing a value in asserts something about her
  reading that no script can know.

**`GATED_COLLECTIONS` is `food_recipes`, `food_magic_bag` and
`cocktail_recipes`, and the scoping is not optional.** It has been three
collections since `food_magic_bag` joined on 2026-08-26 with the collection
itself; this paragraph said two until 2026-09-02. Fail-closed applied to every
collection would delete the entire site: `dev` pages carry no `meta` block at
all. Drafts and dev pages have their own `output: false` protection and need no
gate regardless of whether they happen to carry the keys. (Every food draft
carries `awaiting_fix` and every cocktail draft has carried all three since the
#668 migration — no plugin reads them there, so on a draft they are purely the
bookmark and the work-state note, not enforcement.)

`_config.yml` sets `show_awaiting_fix: false`; `_config_local.yml` sets it
`true`, so flagged pages stay visible while you work on them and vanish from
production.

The point is that **one broken page stops blocking the site**. Flag it, ship
everything else, fix it, unflag it. Before this existed the field sat on all 82
recipes and nothing read it, so the only way to hold one page back was to hold
the whole site back.

**It removes the document rather than hiding it from the index, and that is the
whole feature.** Issue #276 is the precedent and it cost two pages:
`food/swatch.html` and `food/swatch-scribbles.html` were linked from nowhere and
were published anyway, because Jekyll gives every document it renders a URL
whether or not an `<a href>` points at it. **Unlinked is not unpublished.** A
recipe merely dropped from the index still sits at its permalink and still
appears in `sitemap.xml` — the last place you want a page you have flagged as
wrong.

There is deliberately no second field. Jekyll's own `published: false` would do
the same job, but two fields that must agree eventually disagree — silently, and
in the direction that publishes the broken page.

**THE HYPHEN WAS A HAZARD, WHICH IS WHY THE FIELD WAS RENAMED.** It was
`awaiting-fix` until 2026-08-18. Ruby reads `meta["awaiting-fix"]` happily, so
the plugin never minded — but **Liquid parses `page.meta.awaiting-fix` as
SUBTRACTION.** The first template or index filter to ask whether a page was
flagged would have got arithmetic instead of a boolean, evaluated it as false,
and published the flagged page. `tests/test_front_matter.py` fails on the old
spelling anywhere in `_food_recipes/`.

**The test's scope is `_food_recipes/` only, and nothing scans drafts for the
old spelling.** This paragraph said "roughly 90 pre-existing drafts still carry
the old hyphenated `awaiting-fix`" from 2026-08-21 until 2026-08-29, when it was
measured: **zero, across all 342 drafts.** Either the propagation happened and
nobody updated this, or the estimate was wrong when written. Both are the same
lesson and it is §11.2's: `grep -rn 'awaiting-fix' _food_drafts` takes a second
and this file went eight days asserting the opposite.

The hazard the paragraph describes is still real even at zero, because nothing
is watching: copying an existing draft as a template silently copies whichever
spelling that draft happened to have, and a 2026-08-21 ingestion session did
exactly that across 34 new files before catching it. Always write
`awaiting_fix` (underscore) on any new draft — it costs nothing now and it is
the only spelling that still works once the file is promoted.

**Six tests guard this, because every failure mode is silent** — the page
publishes, the build is green, and nothing says why. Three on the mechanism
(`tests/test_site_config.py`: the plugin exists and reads the right key; the two
configs disagree in the right direction; the workflow still runs a
plugin-capable build). Two on the data (`tests/test_front_matter.py`: every
recipe declares the flag; the value is a real boolean, never a quoted string).
One behavioural (`tests/test_rendered_pages.py`), which builds a real production
site and asserts both directions — flagged absent AND unflagged present, because
a plugin that dropped every document would satisfy the first assertion perfectly
and take the site down. A seventh writes two throwaway recipes, one with no flag
and one with the old spelling, and proves neither reaches the build.

Since the suite gates the deploy (§10), every one of those is also a build stop
rather than a report.

The quietest mechanism failure is worth naming: Jekyll's safe mode — what a
Pages-native build uses — ignores `_plugins/` entirely, without warning. The
gate would be gone and the build green.

**Easy to get wrong:**

- `QQ` anywhere is Helen's placeholder. **Never flag it as an error.**

  **INGESTING A RECIPE THAT IS NOT IN HELEN'S OWN VOICE — a magazine scan, a
  website, a transcript, anything transcribed rather than written — every
  method step is marked, and since 2026-08-31 every one is also PAIRED with a
  rewrite.** The marked form below is the older half of the convention and
  still describes what the marker means; the pair is the format to write.

      method:
        - "QQ original Heat the oven to 180C fan and grease a 20cm tin."
        - "QQ Claude Heat the oven to 180°C fan and grease a 20cm tin."

  The point is that a transcribed step is not a finished step even when it
  reads perfectly well. Helen rewrites every one into her own voice, and
  ingested text that happens to scan cleanly is exactly the kind that slips
  through un-rewritten — so the marker goes on at ingest time, on all of
  them, and comes off one at a time as she rewrites. The marker goes on the
  METHOD STEPS, not just on the odd field somebody noticed was rough.

  `test_no_qq_placeholder` (§10) catches any that reach `_food_recipes/`.
  Drafts may carry it indefinitely; that is what drafts are for.

  **ONE MARKER SPELLING, AND SINCE 2026-08-31 IT IS `QQ original`.** This
  paragraph used to describe two — `QQ PLACEHOLDER ` for new ingests and a
  legacy `PLACEHOLDER - rewrite: ` on roughly 190 older drafts, with an
  instruction to leave the legacy ones alone. Helen asked for the whole
  corpus to be paired instead, so `tmp/rename_markers.py` renamed all 1,074
  markers in place — 270 `QQ PLACEHOLDER` and 804 `PLACEHOLDER - rewrite:`,
  across 236 files — and the drafts folder now spells it exactly one way.
  Never introduce a third.

  **THE INTERLEAVED PAIR IS THE STANDARD FORMAT, NOT A PER-BATCH ASK.**
  Established 2026-08-21 as a variant Helen would opt into; universal as of
  2026-08-31, when she asked for a rewrite on every draft she had. Each
  method step is a PAIR of consecutive entries:

      method:
        - "QQ original Heat the oven to 180C fan and grease a 20cm tin."
        - "QQ Claude Heat the oven to 180°C fan and grease a 20cm tin."

  `QQ original` is copied verbatim — same source punctuation, degree-sign
  habits, "minutes" instead of "mins", everything — because the whole point
  is an unedited comparison. Never tidy or house-style a `QQ original` line;
  it will read as broken house style and that's expected, not a bug to fix.
  **Never DELETE one either** — dropping a superseded original is Helen's own
  edit, made when she takes a file out of `to-rewrite/` (see the pipeline
  above).

  `QQ Claude` is Claude's own paraphrase and IS held to normal house style,
  same as any other prose it writes. **That sentence was written correctly
  here and implemented wrongly for eleven days — see §5.**

  **264 of 267 drafts are paired.** The three that are not are #637, #638 and
  #639: sources corrupted badly enough that paraphrasing them means inventing
  a recipe. A source too broken to rewrite is flagged and raised, never
  reconstructed.

  **WRITE THE PAIRS WITH A SCRIPT, NOT BY HAND, AT ANY SCALE.**
  `tmp/insert_rewrites.py` takes `{slug: [paraphrase, ...]}` and places each
  `QQ Claude` line after its `QQ original`. It never reproduces source text —
  which is what sidesteps the content-filter refusal below — refuses on a
  per-file count mismatch, and is idempotent, so a re-run replaces an existing
  paraphrase rather than doubling it. Over a thousand rewrites were placed
  this way without a hand-edited `method:` block.

  **Generating a `QQ original` line risks "API Error: 400 Output blocked by
  content filtering policy."** Seen twice on 2026-08-21, both times from a
  single large `Write` containing a full method's worth of verbatim
  copyrighted book prose at once. Building the file incrementally instead —
  one step, or one step-pair, per `Edit` call, never the whole `method:`
  block in one shot — avoided it completely across the rest of that session's
  ~30 recipes. Keep the same discipline in any commentary/reasoning that
  quotes the source at length; the trigger isn't obviously scoped to file
  writes alone.
- > ## THE INGEST CONTRACT — settled with Helen 2026-08-29
  >
  > **The line is not "how much help is too much". It is one question, asked of
  > every field: IS THE ANSWER IN THE SOURCE DOCUMENT, OR IN HELEN'S HEAD?**
  >
  > In the source — the fan figure, "large eggs", "unsalted butter", "golden
  > caster" — writing it down is READING, not judgement, and an ingest session
  > is the only one that will ever have the page open. Do it, unasked.
  >
  > In her head — her voice, her palate, whether she liked it — leave it, and
  > write `QQ`.
  >
  > **A silence in the source is never filled from general cooking knowledge.**
  > A wrong "whole milk" looks exactly as confident as a right one, and that,
  > not ambition, is the whole garbling risk. `QQ` is the existing answer and
  > costs nothing.

  **WHY THIS EARNED A CONTRACT: 266 of 342 drafts (77%) carry at least one gap
  whose answer was printed on the page**, 675 hits in total, measured
  2026-08-29. Sugar type 117, egg size 103, butter salted/unsalted 92, ginger
  form 58, warm spices 42, **fan oven 39**, milk 36, garlic 33, flour 30, and
  nine more rules behind those.

  **The fan temperature is the case that proves the timing matters.** §10 says
  it "could never have been guessed or bulk-fixed from the file alone" —
  entirely true *afterwards*, which is why it sat as a hand-worked backlog. At
  ingest the page is open and prints the pair. The information is not hard to
  get; it is only hard to get **later**.

  **TIER 1 — do it at ingest, unasked.**

  - **Every qualifier the source states.** Sugar, butter, flour, milk, eggs,
    garlic, ginger, warm spices, vinegar, mustard, chocolate. Source silent →
    `QQ`, never a default.
  - **The fan oven temperature**, taken from the printed pair. Check which of
    the two *is* the fan figure — they are not always in the same order (§5).
  - **Quantities in their own `amount:` key, never inside `item:` text.** §4
    below records the real bug: `item: "~1 tbsp tamarind paste"` renders
    unstyled because the highlighter is driven by `{% if item.amount %}` and
    never scans text for a leading number. **No test catches this**, so it is
    ingest-time or never.
  - **Size words with the count, not the item** — `amount: "2 large"`, not
    `item: "large onions"` (108 drafts carry the other shape).
  - **Split `ingredient_groups` and `method_groups`** — see below.
  - **Name the file from the title's head clause**, so slug and title cannot
    diverge (19 drafts already have; each is then a rename-or-retitle decision
    only Helen can make).
  - **House style right the first time** — en dashes, `°C`, unicode fractions,
    quoting, accents. Outside `QQ` lines, always. `/tidy-drafts` (§11.0.2) can
    clean these up afterwards, so this saves a pass rather than a decision.
  - **The citation**, per `SOURCE_ATTRIBUTION_SPEC.md`.

  **TIER 2 — fill in at ingest, say plainly they are proposals.**
  `main_ingredients`, `tags`, `star_ingredient`. Cheap for Helen to correct and
  expensive for her to originate. The vocabulary is declared, so nothing can be
  invented: an undeclared tag or star fails the suite. **Be generous with
  `main_ingredients`** — see §6, where the measured evidence is that ingest
  sessions read the cap of eight as a budget and stop at five while Helen's own
  recipes run to fourteen.

  **TIER 3 — never, at ingest or after.** Rewriting a method step into her voice
  (that is what `QQ PLACEHOLDER ` exists for), `incidental:`, the case-by-case
  tag calls (`freezable`, `virtuous`, `one-handed food`), inventing a time or a
  temperature (`Estimated N mins` is banned outright, §5), `meta.rewritten`,
  `meta.proofread`.

- **SPLIT `ingredient_groups` AND `method_groups` AT INGEST, ONCE — and never
  again afterwards.** Helen's request, restated 2026-08-29 when she found it was
  not written down anywhere: *"Claude is requested to split out ingredient and
  method groups at ingest to help me, then not again after that."*

  **The two halves are one instruction and neither works alone.**

  AT INGEST, do it unasked. A transcribed recipe arrives as a flat
  `ingredient_groups` with one unnamed group and a flat `method:`, and phases
  are usually obvious from the source — a custard, then a meringue, then the
  assembly. Splitting them is cheap while you already have the whole recipe in
  front of you and expensive later, because it means re-reading it. Group names
  are bare nouns for ingredients (`dressing`, never `for the dressing`); method
  group names render bare and MAY be narrative phases (`day before: prepare the
  beef`). Stored casing does not matter — the template uppercases both.

  AFTER INGEST, never regroup unprompted. This is §12's "don't tidy a draft you
  were not asked to tidy" applied to the one edit most likely to look like an
  improvement, and on a published recipe it is worse than untidy: regrouping is
  a real content edit and takes `meta.proofread` down with it (§4.0). If a draft
  looks like it wants groups, say so and leave it.

  **THIS WAS NOT WRITTEN ANYWHERE UNTIL NOW, AND THE COST WAS VISIBLE.** The
  only mention in this file was one clause inside the `meta.claude_rewritten`
  paragraph above, describing what a *requested* tidy-up pass does — not an
  ingest instruction, and silent on the once-only half. Checked with `git log
  -S` rather than assumed: that clause arrived with #418 and no ingest-time
  version has ever existed. So Helen had been typing
  `CLAUDE THIS IS A METHOD GROUP` into draft method steps by hand — three times
  in `meringue-swans-with-diplomat-cream.md` alone, which is exactly the work
  this instruction exists to have already done.

  `test_no_claude_markers_left` catches those markers, so the workaround at
  least fails loudly rather than shipping. It is still a workaround for a
  missing instruction.
- `incidental: true` on an ingredient item (e.g. frying oil, greasing
  butter) marks it as a cooking fluid rather than a real recipe component —
  Helen: "It's silly to write '2 tbsp olive oil' for a sear, when people
  will obviously use as much as they like. Whereas in a salad dressing, an
  amount is needed." Whether an oil is core or incidental is a judgement
  call (unusual oil, a stated high smoke point, searing for flavour, or a
  finishing drizzle all argue for core) that can't be inferred from the
  text alone, so it's an explicit flag, not a heuristic. Default is core
  (omit the key). `test_incidental_not_in_main_ingredients`
  (test_taxonomy.py) keeps it consistent with `main_ingredients`, which
  both the recipe-row ingredient pills and ingredient-search matching on
  the index page read from — an incidental oil should appear in neither.
  `_layouts/recipe.html` also skips it entirely when rendering the recipe
  page's own Ingredients section — it's still mentioned in the method
  text wherever it's actually used (or, per Helen, not, when the
  technique is assumed knowledge — searing beef in oil doesn't need
  spelling out), just not itemised as its own line. **Resolved 2026-08-09,
  issue #75, Helen's interactive pass**: no recipe in `_food_recipes/`
  currently uses `incidental: true` — five files had their generic
  frying/searing oil line deleted outright rather than kept hidden behind
  the flag (her call: nobody starting toad in the hole lacks a normal
  frying oil), and one (the finishing butter in `plum-sauce-for-duck.md`)
  was un-flagged back to a visible ingredient because it's specific enough
  to be worth buying. The mechanism itself stays for a future finishing
  drizzle or unusual oil — don't go looking for a live example of the flag
  in the current collection, there isn't one.
- **An ingredient's quantity must be its own `amount:` key, never embedded in
  `item:` text.** The highlighter treatment (`.ingredient-amount-number
  highlighted` in `_layouts/recipe.html`) is driven entirely by `{% if
  item.amount %}` — it does not scan `item:` text for a leading number, so
  `item: "~1 tbsp tamarind paste"` or `item: "zest and juice of 1 lime"`
  render as plain unstyled text with no error anywhere. Real bug, issue #111
  (2026-08-10): five `~`-prefixed quantities in `thai-green-chicken-curry.md`,
  plus a "zest and juice of N" pattern repeated in that file and in
  `lemon-feather-sponge.md`, were all silently unhighlighted this way. No
  test catches this — it's a content-authoring habit to watch for, not a
  guarded rule.
- `serves` **xor** `makes` — `makes` for quantities you produce (bakes,
  sauces, base recipes; `makes: QQ` for base recipes), `serves` for what you
  portion out. **Values aren't always numeric** — both are free descriptive
  text where a number doesn't fit ("Depends on appetite", "N/A, bring a
  spoon", "6–8 as a condiment", "However many people want to eat 150 g
  rice"). This is intentional, in Helen's own voice — don't "tidy" a prose
  value into a number.
- `method` **xor** `method_groups`. Both present means the second is dropped.
- Group names are bare nouns (`dressing`, not `for the dressing`). Method
  group names render bare and may be narrative phases. **Stored casing
  doesn't matter for display** — both ingredient and method group headings
  render through `.recipe-group-heading`, which inherits `text-transform:
  uppercase` from the shared `%heading-base` placeholder
  (`_sass/food/_recipe.scss`), the same mechanism as the INGREDIENTS/METHOD/
  NOTES headings. Write group names in whatever case reads naturally as data
  (lowercase bare nouns, per the rule above); the page uppercases them
  regardless.
- Cross-recipe links are markdown, **relative, not root-relative**:
  `[display text](../slug/)`. Front-matter string values are never run
  through Liquid, so a literal `/recipes/slug/` link can't pick up
  `site.baseurl` and is simply wrong on this site (served at
  `/helen-triages/food/recipes/slug/`, not `/recipes/slug/`) — this was a
  real, live bug until 2026-08-02, silently broken both locally and once
  deployed, because the test suite only checked that the target slug existed,
  not that the URL resolved. `../slug/` resolves against the *current page's*
  URL, which already includes the baseurl, so it's correct regardless of
  where the site is hosted. `[[wikilinks]]` don't render and are retired.
- `notes:` items are `{label, text}` (added 2026-08-03) or a bare string —
  same polymorphism as `method`/ingredient items (`step.get("step") if
  isinstance(step, dict) else step`, `tests/conftest.py`), for the same
  reason: a note jotted in `_food_drafts/` doesn't have to carry a label
  immediately. `label` renders as the small tab at the top of the box
  (`.note-label` in `_recipe.scss`); a bare string, or a dict missing
  `label`, falls back to the literal word "note". Notes render two per row
  (`.notes` grid, `_recipe.scss`) rather than stacked — a lone note stays
  full width (`.notes--single`). Nobody has needed more than 3 on one
  recipe; 4+ is the signal to write `{{ content }}` prose instead (§4.1),
  the way `chocolate-ganache.md`'s Troubleshooting section does.
- `internal_temp_ref` (+ optional `doneness`) is how a recipe pulls a live
  figure from `_data/food/internal_temperatures.yml` — see §14 for the
  mechanism and why it can only render in `recipe-meta`, never inline in a
  method step. Opt-in, not rolled out: most recipes have neither field, and
  that's correct, not a gap to fill in.
- `instructions:` is retired — it's `method:`, no fallback. Several other
  fields are retired too (`published`, `date_added`, `difficulty`,
  `nutrition`, `filling_note`, `headline_ingredient`) — `tests/
  test_front_matter.py`'s `RETIRED` dict is the authoritative list with what
  each was replaced by; not duplicated here to avoid the two drifting apart.
- Filenames are stable by default; if a rename is clearly indicated, say so
  and ask. Don't rename unasked; don't assume it's forbidden.

**Cocktails front matter does not exist yet and must not be invented.** See §9.

**This is not the only shape a food document can take.** `_food_magic_bag/`
(§4.3, added 2026-08-26) holds dishes Helen makes without a recipe — no method,
no source, an explicitly incomplete ingredient list. Everything above applies to
`_food_recipes/` and `_food_drafts/` and none of it applies there; the two
schemas are deliberately separate so the rules on this page can stay
unconditional.

### 4.1 Body content below the front matter (rare)

A recipe file's Markdown body — the content *after* the closing `---` — is
not part of the schema above, but isn't ignored either: `_layouts/
recipe.html` renders it verbatim (`{{ content }}`) inside `.recipe-body-
content`, between Notes and the source footer, if it's non-empty. **Two
published recipes use it**, checked 2026-08-20 rather than assumed:
`chocolate-ganache.md` (~2,900 characters of Tips and Troubleshooting) and
`henrys-quick-bulletproof-hollandaise-sauce.md` (~3,600). This said "exactly
one file" and named the ganache by its old slug until then — it was renamed
from `dark-chocolate-ganache.md` at some point and this file did not follow.

**Decided 2026-08-02: this content continues the recipe, it does not become
a blog post.** Helen considered three options — style it as a blog post with
its own title; treat it as more recipe sections; or move it to a standalone
page (a different problem: reference material multiple recipes would link
*to*, versus content that only makes sense in the context of one specific
recipe — built 2026-08-11, see §14, not hypothetical any more if you're
reading this after that date). Her call, "least jar": section headings in
body content are now **peers of
INGREDIENTS/METHOD/NOTES**, not a quieter sub-level treatment — same size,
same punched-tape mark, same `$spacing-section-top` rhythm as the rest of
the page.

**Peer headings need raw HTML, not `## Heading`.** Kramdown gives a plain
markdown heading no class and no nested span, and `.recipe-section-heading`
needs both — the span is what `overlapping-rule-double`'s background hugs.
Write the exact markup `_layouts/recipe.html` generates directly in the body
instead, blank-line-separated above and below so kramdown still parses the
surrounding markdown as markdown rather than folding it into the HTML block:

```
<h2 class="recipe-section-heading"><span class="section-heading-text">Tips</span></h2>

- A bullet list here parses as normal markdown again.
```

A subtitle directly under a peer heading (ganache's own "a.k.a. ganache is
the worst", split out of the heading text itself so TROUBLESHOOTING reads
clean) is `<p class="recipe-section-subtitle">`, same raw-HTML approach,
placed right after the heading with no blank line between them. A bare `##
Heading` still gets a sane fallback (`.recipe-body-content h2
:not(.recipe-section-heading)` in `_recipe.scss`) rather than unstyled
browser default, but it will not match the rest of the page — that
mismatch is what peer status is for, not a bug to fix if you see it.

**Reading width matches Method, not Notes.** Body content's `p`/`ul`/`ol`
used to inherit the shared `article.recipe p { max-width: 65ch }`
(`_layout.scss`) — the same cap Notes uses, only because both happen to be
plain `<p>` tags, not because anyone decided body content should read at
Notes' width. Helen's call: match Method instead, which has no cap at all.
`.recipe-body-content p` now sets `max-width: none` to override the shared
rule; `ul`/`ol` were never covered by it and just don't set one.

MVP styling for this area is done (closed 2026-08-02) — headings and width
match the rest of the page now, this isn't
a placeholder pending a "real" pass. Whether the peer-heading pattern
generalises further (more recipes writing body content this way) is still
open, but the pattern itself — raw HTML for peer headings, Method's reading
width — is the decided shape, not provisional.

### 4.2 A bullet list inside one method step

Every `method:` step is markdownified (`_layouts/recipe.html`, same as
tagline/notes) — a multi-line YAML block scalar can embed a genuine
markdown list inside a single step, not just one line of prose. Write it as
`|`, blank-line-separated around the list so kramdown parses it as an actual
list rather than folding it into the surrounding paragraph:

```yaml
method:
  - |
    Leave to cool at room temperature to your working temperature:

    - Pouring/glazing: 32–35°C
    - Drip cakes: 29–32°C
    - Piping/filling: 20–24°C

    Cool completely, then beat until light and fluffy.
```

This needed a real fix, not just a content change, to work at all:
`.method-full li` was `display: flex` (number and step text as two flex
items, side by side) — flex turns each run of inline content *and* a nested
block-level `<ul>` into separate items laid out in a row, so a list inside a
step would have rendered beside the step number instead of underneath the
step's own text. `.method-full li` now uses `position: relative` +
`position: absolute` on the `::before` number instead (`_recipe.scss`), the
same technique `.recipe-body-content`'s numbered list and `.method-short`'s
bullets already used — whatever a step contains, one line or a paragraph
plus a list plus another paragraph, stacks normally underneath the number.

**Nested `<li>`s must not increment the step counter.** `.method-full li`'s
`counter-increment: step-counter` is a descendant selector — it matches a
bullet nested inside a step too, unless overridden. `.method-full ul li`
explicitly resets `counter-increment: none` (and the number-column
padding/`::before`) for exactly this reason; break it and every step number
after the first list-containing one goes wrong silently, since nothing
fails loudly when a counter just increments an extra few times.

Grouped methods add a second wrinkle: `.method-full li.method-group-
heading-item ~ li.step` indents grouped steps by `$space-xxl`, and now has
to compose that with the number column (`$method-step-number-column`)
rather than replace it — `calc($space-xxl + $method-step-number-column)`
for the padding, and the `::before`'s own `left` shifted to `$space-xxl` too
(`position: absolute`'s `left` is relative to the li's padding *edge*, fixed
at the border, so padding-left alone only moves where the text starts, never
the number). Verified against `beef-wellington.md` (one of six recipes using
`method_groups`) after this change, not assumed safe by inspection alone.

`chocolate-ganache.md`'s own cooling step is the first (only, as of
2026-08-02) real example.

### 4.3 The magic bag — dishes with no recipe

**A separate collection, `_food_magic_bag/`, added 2026-08-26.** Helen's own
name for her brain, and the collection is named after it because that is
genuinely where these live: in her head, not on the site. A magic-bag entry is
a dish she cooks from memory and has no intention of writing up.

This answers the README's problem #1 — *"what shall I cook, out of everything I
already know how to make?"* — for the half of that set the site could not hold,
because those dishes were never written down and never will be.

```yaml
title: "Fridge-end fried rice"
tagline: "The thing that happens to yesterday's rice."   # key required, value may be ""
main_ingredients: ["rice", "eggs", "spring onions"]      # what makes it findable
tags: ["fakeaway"]                                        # OPTIONAL here, unlike a recipe
ingredients:                                              # flat, bare strings, INCOMPLETE
  - "cold cooked rice"
  - item: "dark soy sauce"
    note: "Light soy makes it taste thin."
notes:                                                    # optional, {label, text} as a recipe
  - label: "Rice"
    text: "Has to be cold and a day old."
meta:
  awaiting_fix: false                                     # the publish gate, and nothing else --
  proofread: false                                        # both its flags, since #667
---
```

**It is NOT a variant of the recipe schema, and that was the whole design
decision.** Every structural guard in `test_front_matter.py` is unconditional,
which is what makes them worth having — `test_method_xor_method_groups` treats
"neither" as an error, a real catch across 86 recipes. A magic-bag entry has no
method *by definition*, so folding it in would have forced that guard, the
required-field list and every source-attribution rule to grow an `if`.
Weakening a live guard to admit a new shape is the wrong trade. The recipe
rules stay absolute; the new shape gets `tests/test_magic_bag.py`.

**The required set is five keys and the shortness is the feature.** Capturing a
dish has to be nearly free, or Helen won't, and the collection stays empty.
`tags` is *not* required, unlike on a recipe: a magic-bag dish is found by its
ingredients, and forcing a taxonomy decision at jot-down time is exactly the
friction that stops the note being written. Tags are validated when present.

**`meta:` is TWO flags here, not three — `awaiting_fix` then `proofread`.**
`rewritten` is a recipe flag with no meaning for a dish that has no source and
never left Helen's own head — and a flag that can only ever hold one value is
precisely what `test_front_matter.py`'s `cooked_before` tombstone warns
against. Until 2026-09-02 this paragraph said the same of `proofread`, and it
was true until the gate started reading it (§4.0, #667): the plugin publishes
only on `awaiting_fix: false` AND `proofread: true`, and a collection whose
schema forbids a required key cannot publish at all. Helen's ruling
(2026-09-03): the magic bag must publish, so `proofread` is required here,
`false` by default on a new entry, hers to flip once she has read the built
page. `food_magic_bag` is in the plugin's `GATED_COLLECTIONS` because the
collection is `output: true` and the gate is about what the world sees.

**The incompleteness is enforced by the schema, not announced on the page.**
There is nowhere in this shape to put a method and `test_no_recipe_only_keys`
rejects one, so a magic-bag list is one that *cannot* be completed there —
a stronger statement than prose saying it might not be. A standing caveat WAS
rendered on every page for about an hour on the day this was built, and Helen
had it removed on sight: *"I am the user, and I know exactly what is going
on."* It explained the collection to a reader who does not exist on this site.
Don't reinstate it on the reasoning that the pages should explain themselves.

#### Four things in `food/index.html` needed handling, and three fail SILENTLY

This is the part worth reading before touching the index again.

- **The `meta.rewritten` gate.** Every row is gated on `recipe.meta.rewritten or
  site.show_source_wording`, and that config flag is `true` in
  `_config_local.yml` and `false` in `_config.yml`. So an entry without
  `meta.rewritten` renders perfectly while you build it and **vanishes when it
  deploys**, green build, nothing in the log. The magic bag is exempted in both
  places that apply the gate — the row `if` and the `_rendered_recipes`
  `where_exp` that feeds the survivor count. Exempted rather than papered over
  with `rewritten: true`: that gate exists because an un-rewritten recipe still
  carries someone else's words, and these have no source to rewrite from.
- **The derived ingredient index** (the "they hate peas" exclude filter, #52)
  reads `ingredient_groups`, which these don't have — so their vocabulary would
  have been empty, and an empty vocabulary means *"no mushrooms please"* hands
  back every magic-bag dish containing mushrooms. That loop's own comment states
  the rule it would have broken: **fine to include ON, dangerous to exclude BY.**
  A second loop reads `ingredients`. There is deliberately no branch on the
  collection — a recipe has no `ingredients` and an entry has no
  `ingredient_groups`, so each loop is simply a no-op for the other shape.
- ~~**The three meta filters.**~~ **GONE, 2026-08-30, issue #562** — and the
  care they needed is worth reading once even though the code is deleted, because
  it is the sharpest example on the page of a default that lies. "needs rewrite",
  "needs proofread" and "no short method" all mean *this recipe isn't finished
  yet*, and on the defaults a magic-bag entry answers TRUE to all three (no
  `meta.rewritten`, no `meta.proofread`, no `method_short`), padding three
  working lists with dishes that can never leave them. `data-meta-short` was
  therefore **three-valued** — `'true'`, `'false'`, `'n/a'` — because that filter
  was a PAIR whose halves want opposite answers, and only a third value fails
  both; reading the no-short branch as `!== 'true'` was the natural spelling and
  the bug. **All of it is deleted**: Helen reduced the meta filters to `draft`
  alone (§13.4), so the attribute, the Liquid deriving it and the branches
  reading it went together rather than being left as data nothing reads.
- **A `magic bag` badge on the row, shown in production.** Without it a
  magic-bag row is indistinguishable from a recipe row until the page loads and
  there is no method on it. It used to be the exception among three badges;
  since #562 there are two, `magic bag` and `draft`, and they are the same kind
  of statement — **what you are about to CLICK**, not what state it is in.

**`filters.js`'s two DECISIONS are covered now — #506, 2026-08-31 — and its
wiring still is not.** The issue was raised about the three-valued branch above,
which no longer exists; its argument stood anyway, and the answer was §3's
split: `FilterState.rowMatchesFilters` and `IS.entriesMatchKey` moved out with
tests, the DOM wiring stayed. See §3 for what deliberately did NOT move and for
how the extraction was proved behaviour-preserving.

**The class of fault that file harbours is still open, and it bit the same
day.** Two hours after the extraction, a name read off the wrong object took
out the whole of `cocktail-index.js`'s startup while every JS test stayed green
— because they ask pure modules questions, and wiring is the gap between them.
§10.2's stub-DOM harness is the tool for that, and it had never been used on
either index. Use it before believing a green suite about a file that touches
the DOM.

**A trap paid for while building it:** Liquid **tokenises tags inside a
`{% comment %}` block** rather than treating the body as text, so an
illustrative bare `if` tag written out in full inside a comment is a real parse
error that takes the whole build down. It did. This is the same family as §12's
"prose defeats a source-scanning guard", from the other direction: here the
parser reads documentation as code.

**Promotion is a real path, not a dead end.** A dish that earns a full write-up
moves to `_food_drafts/` and takes the recipe schema. `test_no_recipe_only_keys`
exists to catch the halfway state — the realistic failure is not a stray key but
Helen starting to write one up in place, until the file is a recipe living in
the wrong collection rendered by a layout that shows none of it. Its failure
message says "promote it", because wanting to write one up is a good outcome
that has outgrown the shape.

**Open, and deliberately not decided on the way past:** whether the index needs
a way to include or exclude the magic bag in production (**#507** — note the
META FILTERS block is local-only, and "has a written method" is a fact about a
dish rather than a state of completion, so it may not belong there at all);
whether `magic bag` is the right reader-facing word, in the badge and in the
`/food/magic-bag/` permalink (**#508** — the permalink is the half worth
settling early, since changing it later breaks shared links); and the README,
which still describes two collections (**#509**, and it wants Helen's own voice,
not an imitation of it).

**`.recipe--magic-bag`** exists for exactly one spacing consequence and nothing
else. `.recipe-tagline` deliberately carries no margins (§13.3's reasoning: the
gap beneath it comes from `.recipe-meta`, which is what keeps title-to-meta
distance constant whether or not a tagline exists), and a magic-bag page has no
metadata grid — so its badges sat against the tagline. The margin is on
`.recipe-badges`, scoped, so no recipe page moves; and on the badges rather than
the tagline because the tagline is optional here and an empty one renders
nothing at all, which would drop the gap exactly when it is still needed. It is
not a hook for making these pages look different on purpose.

---

## 5. House style

Unicode fractions (`½`). Em dash for `--` in prose (not commit messages — see
§11). **En dash for a number range** — `3–4 mins`, `170–180°C`, `36–40% fat`.
`→` for arrows. `°C` always, **fan oven only**, never conventional or
gas mark — check which of a pair *is* the fan figure before deleting one, they
aren't always in the same order. British spellings. Titles use `and`, never
`&`.

**The en-dash rule is new on 2026-08-21 (issue #413) and it is scoped by what a
READER SEES, not by whether a field is prose.** `test_number_ranges_use_en_dashes`
reads the whole recipe file, on Helen's ruling about a `cook_time: "20-25 mins"`:
"These still render to the user, so correct to en dash please." The pattern needs
a digit on both sides and nothing cleverer, so `1-inch balls`, `criss-cross` and
`half- or quarter-cylinder` are untouched; ISO dates are blanked before matching,
because `2026-08-12` matches a range rule perfectly and was every single "hit" in
the first measurement of the data files.

**Two scoping facts about house style that are easy to get backwards:**

- **It reaches prose pages now, not just recipes** (§13 is design; this is text).
  `tests/test_prose_pages.py`, 2026-08-21, issue #413. Until it existed, the
  about page, all three index pages and both reference pages had NO typography
  coverage at all — and the about page is the most-read prose on the site after
  the recipes. It checks two surfaces, because the pages' words are not all in
  the pages: the reference pages render most of their prose out of
  `_data/food/*.yml`, and checking only the `.html` found 0 of the 4 real
  violations that were actually there.
- **It stops at a `QQ` line** (issue #426, 2026-08-21). A step beginning `QQ` is
  still the SOURCE's wording awaiting a rewrite, so correcting its degree sign or
  its dash tidies text about to be deleted, by editing someone else's words.
  Matched as a PREFIX, never a substring, so a finished step that merely mentions
  the marker is checked like any other prose. This was worth 66 of the 67
  house-style violations in the drafts folder.

  **BUT IT MUST NOT STOP AT A `QQ Claude` LINE, AND IT DID, FOR ELEVEN DAYS.**
  Fixed 2026-08-31. `conftest._QQ_LINE` and `scripts/tidy_drafts.py`'s
  `QQ_LINE` both matched *any* line starting `QQ`, so the interleaved format
  (§4) put Claude's own prose behind the exemption written for somebody
  else's. **The exemption was never wrong; the pattern was.** `QQ` means text
  awaiting a rewrite, and correcting its dash edits words about to be deleted.
  `QQ Claude` is the exact opposite — our prose, held to house style like
  anything else we write, and this section already said so.

  Both patterns now carry a negative lookahead, `QQ\b(?!\s+Claude\b)`. The
  15 hyphenated number ranges that had been hiding were then fixed by
  `/tidy-drafts` — the script that should always have fixed them, fixing them.

  **WHAT MADE IT INVISIBLE IS THE PART WORTH CARRYING.** The format existed
  for eleven days on 32 drafts and never showed. Adding ~1,000 `QQ Claude`
  lines in a day exposed it immediately. **A hole in a guard is proportional
  to the data flowing through it**, so a rule that has been quiet since it
  was written is not thereby proven — it may only be starved. Before scaling
  up any operation tenfold, ask which guard is about to see its first real
  traffic.

**Time** — tighter for metadata than prose: `prep_time`/`cook_time` use `20
mins`/`1 hr 30 mins`/`2 hrs`; prose uses `mins`/`hours`/`seconds`. Only
numeric quantities are abbreviated — "ten minutes of glory" stays as written.
`cook_time: "Until done"` for family bakes with no stated time.

**`Estimated N mins` must never appear in a published recipe.** All nine that
an earlier Claude had invented are gone as of 2026-08-09 — Helen replaced
them by hand rather than have them converted to `QQ` (a poor estimate
publishes, a `QQ` blocks). If one turns up again, same rule: leave it for
her, don't convert it yourself.

**Accents** via `_data/accented_words.yml` (repo root, not `_data/food/` —
it's house style, applies to cocktails too): a curated unaccented→accented
map plus a `no_accent:` list (`echalion` is a UK trade name, stays plain).
Prose only — never slugs/filenames (must stay ASCII) or `source:` (reproduced
as the publication spells it). Test: does the transformation lose information
or make a judgement? `1/2` → `½` does neither.

---

## 6. `main_ingredients`

Unordered set in the data; ordering is presentation (`_data/food/pantry.yml`
sinks 34 pantry staples to the end, dimmed — exact, lowercase match, so
`onion` demotes but `red onions` doesn't). **That file is a BARE LIST**, so
the Liquid reads `site.data.food.pantry`, not `.pantry.pantry`: it was
`common_ingredients.yml` wrapping a single `pantry:` key until 2026-08-15,
issue #130, and the key was flattened out in the same pass rather than
leave the rename reading badly. Adding a second top-level key means
un-flattening this file and `food/index.html`'s `assign` together.

**Sweet/baking — completeness test.** Everything whose absence breaks the
recipe. No cap.

**Savoury — substitution test.** Not "would this fail" but "would I improvise
around a gap": the protein, the liquid/fat that defines the character, anything
you'd have to go buy, the vegetable that's the point.

> **THE CAP OF EIGHT IS A FIRST-PASS GUIDE AND IT HAS BEEN READ AS A BUDGET.
> BE GENEROUS.** Helen, 2026-08-29: *"we have generally shifted to allowing more
> main ingredients where they define a dish, for example the long list of spices
> in gulai ayam... I do often find myself adding to that array by hand, which is
> plainly silly."*

**Measured 2026-08-29, and the two halves of the corpus disagree in exactly the
way that complaint predicts:**

| | files | median | max | over eight |
|---|---|---|---|---|
| `_food_recipes/` — curated by Helen | 86 | 6 | **14** | **16 (18%)** |
| `_food_drafts/` — written at ingest | 342 | 5 | 9 | **1 (0.3%)** |

The one draft over eight is `meringue-swans-with-diplomat-cream.md`, which Helen
wrote herself. **So the published half spreads to fourteen and the ingested half
stops at five**, and the difference is her, by hand, one file at a time. Nothing
about the substitution test changes at promotion; only who applied it does.

**The number is an OUTPUT of the test, never an input to it.** Ask of each
ingredient "would I improvise around a gap here" and write down every one that
answers no — then count, if you like. Never cut a genuine substitution-test
ingredient to reach a number, and never stop adding because you have reached
one. **Not mechanically enforced**: no test checks the count, deliberately.

`indonesian-chicken-curry-gulai-ayam.md` is the worked example Helen reaches
for, and it has **fourteen** — this section said eleven from 2026-08-02 until
2026-08-29, having recorded the figure once and never re-measured it, which is
§11.2 again. `miso-cashew-butter-vegetable-ramen.md` has 13,
`indian-mutton-raan-roast.md`, `garam-masala-powder.md` and
`citrus-soy-salmon-sticky-rice.md` 12 each. Don't flag any of them as a
violation, and expect the list to keep growing.

**Cheeses** use the bare name where it stands alone (cheddar, feta, comté) —
keep "cheese" only where the qualifier is meaningless without it (blue cheese,
cream cheese). Lowercase; `test_no_main_ingredient_spelling_collisions`
enforces it across recipes *and* drafts.

---

## 7. Taxonomy (food)

Declared in `_data/food/taxonomy.yml`. Adding a term there is all that's
needed.

**Star ingredients** (14, optional): beef, chocolate, duck, eggs, fruit,
game, greens, lamb, oily fish, pork, poultry, root veg, shellfish, white
fish. `something unusual` retired 2026-08-09 -- see `_data/food/
taxonomy.yml`'s own comment for the reasoning (culturally relative, not a
real craving, barely and inconsistently used). `legumes` considered the
same day and not added: only two candidate recipes across the whole
collection, both already adequately covered by an existing star -- not
revisited unless that changes.

`eggs` retired 2026-08-09, **reinstated 2026-08-12, issue #187, Helen's
explicit call.** The 2026-08-09 retirement was sound for the six recipes it
covered then (asparagus-gruyere-quiche, ben-jerrys-sweet-cream-base-1,
delias-classic-pancakes, henrys-quick-bulletproof-hollandaise-sauce,
henrys-sunday-waffles, mrs-nicholsons-yorkshire-puddings) -- every one used
egg as a technique or structural ingredient, not the thing the dish is
actually about, and all six stayed blank, still correct. But by 2026-08-12
eight `_food_drafts/` recipes had `star_ingredient: eggs` sitting invalid
against the retirement (not blank, contrary to what a previous version of
this paragraph claimed -- checked directly against the files, not assumed).
That's what turned this from hypothetical into a real decision: checked
each of the eight against the same test as the original retirement ("is
egg the craving, or just doing technique/structural work"), not reinstated
wholesale. Kept `eggs`: `ajitsuke-tamago.md` (literally "seasoned egg",
nothing else in the dish), `green-baked-eggs.md`, `pink-eggs-beetroot-
yogurt-chilli-butter.md` (the poached eggs' colour is the tagline's own
selling point), `spring-onion-feta-frittata.md` (the literal frittata
example this paragraph used to cite as hypothetical). Blanked, the original
retirement reasoning applied to them specifically: `quick-creme-
brulees.md`, `spring-herb-goats-cheese-souffle.md` (egg whites are the
leavening mechanism -- same reasoning that already correctly keeps
`dark-chocolate-souffles.md` on "chocolate", not eggs), `caramelised-leek-
udon-sesame-fried-eggs.md` (title's own head clause, before "with", is
"Caramelised Leek Udon"), `broad-bean-herb-and-ricotta-fritters.md` (egg as
fritter binder). See `_data/food/taxonomy.yml`'s own comment for the same
reasoning inline with the data.

**Retired star values need actively removing, not just retiring -- caught
for real, 2026-08-12.** `_data/food/taxonomy.yml`'s `retired_star_
ingredients` dict (added the same day) is the enforcement half of this:
`test_star_ingredient_is_declared` (`test_taxonomy.py`, `test_drafts.py`)
checks it first and fails with the retirement reason, rather than a value
that used to mean something silently blending into the generic "not
declared" pile. Five drafts (hazelnut-paris-brest, leratos-tanzanian-
banana-curry, matcha-white-chocolate-blondies, ukrainian-dumplings-
chestnuts-kraut-filling, zucchini-orange-cake-with-pistachios) were still
carrying `something unusual` three days after its retirement note above was
written -- the note recorded the *decision*, but nothing enforced it
against existing files, so it was only found by reading test output rather
than trusting a green run. All five are blank now. Unlike `eggs`, Helen
confirmed `something unusual` has nothing left to reconsider -- it's gone,
don't reintroduce it.

**`goats-cheese-squash-rosemary-griddle-cakes.md` is `root veg`**
(2026-08-09) — squash counts, per Helen. First (and so far only) recipe
using this star; check against it, not just the bare word list, when
deciding whether a future squash/parsnip/swede/carrot-forward dish
qualifies.

**Mood** (15) — *what you feel like eating, a craving*: bakes, carbs party,
cheese-tastic, dessert, drinks, fakeaway, hot snack, ice cream, nibbles,
one-handed food, salad, showstopper, soup, sweets, virtuous.

**Practicalities** (7) — *what the occasion or the recipe demands of you,
regardless of what you feel like*: breakfast, extras, festive, freezable,
make-ahead, no-cook, starter.

**Co-tags.** Only `ice cream → dessert, make-ahead` survives. Test for adding
another: sound when a ROLLUP or a genuine AFFORDANCE, unsound when
DEFINITIONAL (true by the words' own meaning, so carrying no information).

**Reclassified 2026-08-01–02, Helen's calls, recorded so they aren't
re-litigated:**

- `one-pot` and `scalable` retired — both guessable from reading the recipe
  and too common to narrow anything (one-pot would cover 57% of the
  collection honestly tagged).
- `breakfast`, `extras`, `festive`, `starter` moved mood → practicalities:
  none of them are a craving, all are dictated by an external structure (time
  of day, a menu, a calendar). `showstopper` stayed in mood on the same
  test — checked against every beef/lamb/pork/poultry/duck/game recipe in the
  collection, and it *is* a craving, for Helen specifically.
- `virtuous` added to mood: "fun to cook and eat, and pleasingly virtuous."
  Deliberately narrow, applied case by case rather than by category — lean
  protein or a genuinely veg/fruit-forward dish where a wine- or
  citrus-based sauce is doing the work, not cream or butter. Not "contains a
  vegetable."
- `freezable` kept — the one of the three retired candidates that's genuinely
  unguessable from reading a recipe.

**Two tags with meanings you wouldn't guess:**

- **`one-handed food`** — eat curled on the sofa. Rolls/spills/needs
  chasing disqualifies it (noodle soups are out, thick spoonable soups are
  in).
- **`no-cook`** implies `cook_time: "None"`, not the reverse — `cook_time` is
  a fact, `no-cook` answers "can I put this on the table without cooking?" A
  spice blend is honestly uncooked but a useless answer to that question, so
  it stays untagged.

**Freezable calls, issue #72, 2026-08-09:** `chicken-cider-stew.md` and
`chicken-sorrel-potato-stew.md` get `freezable`; `pancetta-white-bean-stew.md`
does not — Helen's explicit case-by-case call, don't add it there to "match
the other two".

**`lemony-cavolo-nero-butter-bean-soup.md` isn't tagged `soup`, on purpose**
(2026-08-09) — its own tagline calls it "a one-pot stew", and Helen considers
the dish more stew than soup despite the title. Don't add `soup` to "fix"
this.

**`drinks`** = anything drinkable that isn't a cocktail (frappé, cordial, hot
chocolate). Cocktails belong to the sibling site.

**"Declared" and "filterable" are the same thing.** `_includes/
recipe_badges.html` builds a recipe page's badges by iterating `_data/food/
filter_sections.yml`'s `tag_groups`, looking each group up in
`taxonomy.tags`. A tag in neither file renders nowhere and fails
`test_tags_are_declared`. A tag in `taxonomy.yml` whose group is absent from
`filter_sections.yml` also renders nowhere — both the badge and the filter
button come from that one list. There's no way today to keep a tag as
recipe-page information without also giving it a filter button. Splitting
that is one line (point `recipe_badges.html` at `taxonomy.tags` instead) and
was proposed and rejected: if a fact matters while you *read* a recipe, a
`notes:` line says more than a badge ("freezes well for 3 months" beats
"freezable"); if it only matters while you *browse*, it needs the filter. No
user stands in the gap. Don't build it to make the ontology tidy.

---

## 8. Ingredient search architecture

**Confirmed as staying**, 2026-08-01 — Helen asked whether it earned its
complexity; the answer is scale. 600 distinct main ingredients across 300+
files, 54% in exactly one recipe: useless as a *pantry* filter but exactly
what a *recall* lookup needs ("the one with the sorrel", no name to search
by). 26–29% of recipes have no `star_ingredient`, so star can't reach them by
any other route. Title search stays too, confirmed the same day.

`_data/food/ingredient_words.yml` is the single source; `assets/js/
ingredient-search.js` is the only code that reads it. Six lists, each solving
a genuinely different problem:

| List | Does |
|---|---|
| `modifiers` | Strips a leading word before matching (`chopped`, `dried`...) — changes the canonical entry everywhere |
| `stopwords` | `and`/`or`/`of`/`with` never count as a match target |
| `never_family` | A word heading 2+ entries that never earns an `(all)` button, because the entries sharing it aren't a real family (colour/variety coincidence) |
| `family_exceptions` | One entry excluded from its head word's family without blocking the whole word |
| `singulars` | Irregular plural → singular, where the plural doesn't contain the singular as a substring |
| `synonyms` | Curated families (cheese, pasta, stock) — typing toward the key widens to every member, even ones with no literal text relationship |

**Core ranking rule:** a match at the very start of the whole string
outranks a match that's only real once you check every word, which outranks
one that's real but not a family match. Get this backwards and "chi" ranks
chocolate chips next to chicken breast — see `ingredient-search.test.js`.

Before adding a word to any list, check it against the real data first —
`never_family` especially is a graveyard of near-misses considered and
rejected.

---

### 8.1 Two pickers, one code path, very different input

Asked directly, 2026-08-16 (issue #281): why are the exclude picker's words
worse than the ingredient search's? **They are not two implementations.** Both
call the same `IS.buildMasterList` with the same `ingredient_words.yml`. What
differs is what is handed to it:

- the **include** picker reads `data-ingredients` ← `main_ingredients`, a
  curated list of clean single words;
- the **exclude** picker reads `data-all-ingredients` ← every
  `ingredient_groups` item, which is prose written for a cook — portions,
  containers, brands, alternatives ("a knob of butter", "about 200 g raw king
  prawns").

Issue #52 chose that harder source deliberately and correctly, because
`main_ingredients` is a partial hint: nine rows list an olive oil that none of
them names in `main_ingredients`. So the answer is always to teach the
vocabulary, never to fork the logic or change the source.

**Measure production, not your local build.** The local build folds in ~254
drafts and every unrewritten recipe. On 2026-08-16 the derived vocabulary read
402 bad entries of 1421 locally against 28 of 348 in what actually ships, and
all six source-data bugs found on the way (`"and ½ tsp sugar"`, `"or 300 ml
soured cream"`, `"g-900 g damsons"` — continuation fragments that leaked into
`item:`) were in `_food_drafts/`. Helen's call, and the right default: fix
what ships, and revisit drafts as they are proofread, because a draft's
`item:` lines are rewritten before publishing and a vocabulary entry aimed at
one today is work done twice.

**RE-AFFIRMED 2026-08-20, and this is the paragraph to reach for when the
exclude picker "breaks" again.** It will look broken, it will look like a
regression, and it will not be one. Helen, seeing 73 candidates for `chi` in
LEAVE OUT: "The synonym collapse on the exclude filter has gone wrong again...
This was definitely working properly earlier today." She was right that it had
been, and right that it was not the code:

| | production (ships) | local (:4001) |
|---|---|---|
| rows | 82 | 369 |
| raw `item:` entries | 719 | 3,973 |
| derived vocabulary | 317 | 1,198 |
| `chi` family buttons | 2 | 5 |
| **`chi` candidates** | **10** | **73** |

63 of the 73 were draft-only, and the worst of them are exactly what a draft's
`item:` line looks like before it is rewritten: `chicken bouillon powder or ½
tsp crumbled chicken stock cube`, `hot low-salt vegetable or chicken stock`,
`large or 4 small chicken thighs`. **Nine drafts added at 22:06 and 22:54 that
same evening supplied them** — which is precisely why it had been fine earlier
in the session. The ruling above was upheld: cosmetic, local-only, leave it.

**The ratio has moved a long way since the ruling was made** — 287 drafts to 82
recipes, about 3.5:1, where §8.1 was written at roughly 3:1 with a much smaller
absolute backlog. If the working view ever becomes genuinely unusable rather
than merely noisy, the option that was costed and NOT taken is to build the
picker's vocabulary from published recipes only, leaving draft rows in the list
and still filterable. That is a real design change and needs Helen, not a
session deciding the noise has finally got bad enough.

**HOW TO MEASURE IT, so nobody re-derives this at midnight.** The vocabulary is
emitted into the built page as JSON, and `ingredient-search.js` is a pure module
Node can require — so both halves can be run outside a browser:

```
bundle exec jekyll build --config _config.yml               --destination tmp/prod
bundle exec jekyll build --config _config.yml,_config_local.yml --destination tmp/local
```

then, for each build, pull `id="ingredient-vocabulary"`'s JSON and every
`data-all-ingredients` attribute out of `food/index.html`, split the attribute
on **`|`** (not a comma — filters.js does, and getting this wrong makes each
whole row look like one entry and the numbers meaningless), and run
`IS.create(vocab).search('chi', IS.buildMasterList(entries))`. Compare the two
counts before concluding anything.

**"ONE CODE PATH" IS A CLAIM ABOUT THE ALGORITHM, NOT ABOUT THE PICKERS.**
Issue #390, 2026-08-19, and it is the counter-example this section needed.
Everything above is true — same search, same ranked results, same
`hasWordMatch` flag on each — and the two pickers still looked different,
because `makeExcludeButton` took no `wordMatch` argument at all. The flag was
computed, carried to the call site, and dropped on the floor. Helen found it by
looking at the two boxes stacked on one screen with the same three letters in
both: SEARCH MAIN INGREDIENTS picked out the genuine matches, LEAVE OUT rendered
forty candidates identically.

So the shared algorithm guarantees the same ANSWER, and guarantees nothing about
what either picker does with it. `test_both_ingredient_pickers_mark_their_word_matches`
now checks that both builders apply a class, both call sites pass the flag, and
both classes have a rule in the compiled CSS.

**What the emphasis means, because it is easy to misread as "matches".** It is a
WORD-PREFIX match. Typing `pas` marks `anchovy paste` and `choux pastry`; it
does not mark `antipasti vegetables`, which is correctly in the list on a
substring match, nor `farfalle`, which is there as a member of the `pasta`
family and contains no `pas` at all. Marked entries are the ones you meant; the
plain ones are what the vocabulary brought along.

**One treatment, two hues, via `@mixin word-match-emphasis($colour)` in
`_sass/food/_buttons.scss`** — each picker passes its own section's active tone.
A second rule that happened to look like the first is what drifts; §2.5 is the
same lesson at chrome scale.

**And the hover has to go the same way as everything else on the page.** Issue
#403: once matched candidates rested at `$color-exclude-active`, the pool's
existing bright-cobalt hover (asked for in #365, "a lighter shade") became a
LIGHTENING while every other filter section darkens. `$color-exclude-hover` is
a deeper cut than `$color-exclude-active` **deliberately** — hovering a matched
candidate to the tone it already rests at is not §12's "lightness-only change
reads as nothing", it is no change whatsoever. Guarded by comparing relative
luminance of the two compiled colours, which asserts the DIRECTION and not
merely that they differ.

**Read the whole list before adding to `measure_phrases`.** The section header
in `ingredient_words.yml` already says to derive phrases from real entries;
these are the traps that rule exists for. `bicarbonate of` and `cream of` both
end in "of" and both lead real entries — stripping them yields "soda" and
"tartar". A bare `little` would turn all three "little gem lettuce" entries
into "gem lettuce", which is why `a little` and `a little extra` keep their
article. The container words without an "of" ("can chickpeas") are only safe
because **`stripMeasurePhrase` matches `phrase + ' '`**: `can ` cannot fire on
"cannellini beans", and the spice `cloves` survives untouched because a bare
entry has no trailing space to match, while `cloves garlic` strips correctly.
That trailing space is load-bearing; a word-list version of this destroys both.

**Order of operations decides whether a phrase or an alias is the right tool.**
`normaliseEntry` runs trailing → quantity → measure → modifiers, so a measure
phrase strips AFTER the quantity strip has already run. "juice of 2 lemons"
therefore cannot be fixed with a `juice of` phrase — it would be left as "2
lemons". Those go in `aliases`, whose keys are the post-strip forms.

## 9. Cocktails

**No longer scaffolded-and-empty.** The first three drinks were ingested
2026-08-16 (Julien Sorel, Sazerac, Cobra's Fang) and a front matter schema
was derived from them, the way food's was derived from real recipes rather
than designed up front. Everything below dates from that session unless it
says otherwise.

**Cocktails does not share food's data model and is not going to.** Read this
section, not §4. A food recipe is a procedure; a cocktail is a formula plus a
build. The two collections share the outer layout, the type scale, the palette
contract and house style, and nothing else.

### 9.1 Nothing about the DRINKS is public. The shell is.

Two independent mechanisms, and neither is redundant:

1. **`_cocktail_drafts/` is its own git repo**, pushed to
   `helen-triages-cocktails-private`, and gitignored from this one. The source
   never reaches a public repo whatever the build config says.
2. **`output: false` in `_config.yml`, `output: true` in `_config_local.yml`.**
   They render at `/cocktails/drafts/<slug>/` on :4001 and nowhere else.

The second has failed before: issue #235 is the case where `output: false`
held and `food/index.html` still listed ten drafts, linking to URLs Jekyll had
never written. The config stopped the pages; the repo split stopped the
source. Keep both.

**HOW TO GET THE DRINKS INTO A WORKTREE: CLONE IT.** Git access already works
and always did — Helen's SSH key is per-ACCOUNT, not per-repo, so it reaches the
private remote from a worktree exactly as it does from anywhere else:

    git clone git@github.com:DeckOfPandas/helen-triages-cocktails-private.git _cocktail_drafts

A worktree starts blind, because `_cocktail_drafts/` is gitignored and
`git worktree add` therefore never brings it along — and
`tests/test_cocktails.py` SKIPS the 24 tests that read a drink, reporting green.
A symlink into the main checkout half-works (the Edit/Write tools refuse it, and
writes land in Helen's tree); a copy or a zip goes stale silently. A clone gives
history, branches and somewhere to commit.

**ALWAYS `git fetch` BEFORE CONCLUDING ANYTHING ABOUT ITS STATE**, and this cost
a session on 2026-08-29. A zip of Helen's local checkout was two merges behind,
so five red tests read as work that "had never been done", and an entire day of
retyping was redone from scratch — including DELETING a drink the remote had
merely replaced. Local branches, the reflog and the working tree all agreed with
each other and all were stale. **One clone is not the repo.**

**IT FIRES ONCE PER MERGE, NOT ONCE PER SESSION, AND IT CAUGHT THE SAME SESSION
THREE TIMES ON 2026-08-30.** A clone fetched at the start of a session is stale
the moment anyone merges into the drafts repo, and while two agents are working
that is several times an afternoon. Each time the symptom was identical and
completely convincing: a handful of `test_cocktails.py` failures naming real
drinks and real fields, reading exactly like a regression in whatever had just
been changed. Each time the fix was `git fetch` and a fast-forward, and the
failures were work someone else had already done.

**So fetch it immediately before any run whose result you are going to act on**
— before reporting a failure, before concluding a change is safe, and before
pushing. Not at the start of the session. The cheap version:

    cd _cocktail_drafts && git fetch origin && git rev-list --count HEAD..origin/main

A non-zero answer means the next red test is probably not yours.

**AND YOU CANNOT FAST-FORWARD IT THE OBVIOUS WAY — `git checkout --detach
origin/main`.** Added 2026-09-01, having cost a detour. A test clone sits on
`main`, so `git merge`/`git pull` there is *a merge onto `main`* and
`guard-main-branch.py` refuses it, correctly and in every repo in the tree.
`git fetch origin main:main` is the usual answer and does not work either: git
refuses to update the ref of the branch you have checked out. Detaching takes
neither path — it is a checkout, the destructive-git hook allows it on a clean
tree, and a detached HEAD is not `main`, so nothing can be written to `main` by
accident.

**Detach onto the BRANCH you need, not only onto `main`.** The same day, the
public repo's tests wanted drink data sitting on an unmerged drafts branch
(§10), and `git checkout --detach origin/<branch>` is how you get a corpus that
matches what you are testing.

**The API token is a different channel and does not cover file contents.**
`GH_TOKEN` selects all three repos and carries Issues; probed 2026-08-29,
`contents` returns **403** on both private repos and 200 on the public one. So
the API can read and write issues anywhere and read drink files nowhere. Git
can. Push access to the private repos exists — policy still says ask Helen every
time, per CLAUDE.md.

**What IS public**: `_layouts/cocktail.html`, `_sass/cocktails/`,
`assets/css/cocktails.scss`, `cocktails/index.html`,
`_data/cocktails/taxonomy.yml`, the tape artwork, and the `cocktails:` block
in `sites.yml`. So the field NAMES and the tag vocabulary are visible even
though no drink is. Helen accepted that trade explicitly, 2026-08-16, after
the fully-private alternative was costed: it needs a single private clone
plus symlinks into eight canonical paths, because Jekyll will only discover a
collection at `_<name>` under the source root and a layout in `_layouts/`.

**The naming trap fired immediately.** The directory was created as
`_cocktails_drafts` (plural) and `.gitignore` line 14 says `_cocktail_drafts/`
(singular, matching `cocktail_recipes`), so the drafts sat UNIGNORED and
stageable in the public repo until it was spotted. This is §12's
"rename something and silently un-ignore it" arriving on day one.
`test_every_drafts_collection_is_gitignored` derives its patterns from
`_config.yml`, so declaring the collection is what switched the guard on —
it was broken on purpose to confirm it bites.

`_cocktail_recipes/` is declared `output: true` but **does not exist on
disk**. That is fine and deliberate: Jekyll builds the collection empty and
`cocktails/index.html` shows its empty state. Nothing is promoted into it
yet, and the promotion gate is the same as food's — Helen's own words, no
lifted copy. §9.1.1 is that gate.

### 9.1.1 The drinks publication gate — three flags, and the index that reads them

Landed 2026-09-02, issue #668, ruled by Helen the same day (D1–D3 in
`model_instructions/ARCHITECTURE_PLAN_2026-09-02.md` §8). **§4.0 is the
authority on what the two gate flags MEAN**; this section is only what is
different about drinks.

**Every drink carries `meta.rewritten`, `meta.awaiting_fix` and
`meta.proofread`** — food's names, in food's order, after the two
drink-specific keys. A drink's `meta:` block is now exactly:

    meta:
      ship: "yes"
      date_last_edited: "2026-08-16"
      rewritten: false
      awaiting_fix: false
      proofread: false

Same names deliberately, and D1 is the ruling: they are the same three
questions, and a second vocabulary for them would be two things to keep in step
for no gain. **Only Helen writes `rewritten: true`** — it "shows me if I have
rewritten it, not an agent", which for a drink mostly means the notes and the
tagline, though her first pass also checks ingredients, bottle suggestions and
method before the proofread.

**All 124 drafts say `false` to all three, and that is honest rather than a
placeholder** (D2). What keeps a draft private is `output: false` on the
collection, not these flags. The migration is one commit in
`_cocktail_drafts/`, written by `tmp/migrate_drink_gate_flags.py` in this repo:
textual insertion of three lines after `date_last_edited:`, never a YAML
round-trip, so `git diff --numstat` reads `3/0` on every file and the diff is
readable. If you ever migrate a drink field again, do it that way.

**The gate itself needed no change.** `cocktail_recipes` has been in
`GATED_COLLECTIONS` since `_plugins/publish_gate.rb` existed. What changed is
that drinks now carry the keys it reads: before the migration a promoted drink
would have been held back silently by the fail-closed rule, which is safe and
completely invisible — a drink that simply is not there.

**`tests/test_cocktails.py` guards the data**, mirroring food's four:
`test_the_gate_flags_are_real_booleans` and
`test_no_drink_uses_the_old_hyphenated_awaiting_fix_key` run over both
collections; `test_agent_edited_drinks_are_not_marked_proofread` runs over
`_cocktail_recipes/` alone and skips, with a reason, while nothing is promoted.
It imports `_git`, `AGENT_TRAILER` and `_only_invisible_keys_changed` from
`tests/test_front_matter.py` rather than copying them — that last one is 150
lines of reasoning about what "nothing a reader could see changed" means (#417,
#429) and two copies would drift the first time one was fixed. Its
`COCKTAIL_BASELINE_COMMIT` grandfathers nothing by construction: the collection
is empty, so every commit at or before it touched zero published drinks. It is
not the migration commit and cannot be — that lives in a different repository.

**`cocktails/index.html` now has food's shape**, and this is the part that was
quietly broken before: it read `site.cocktail_drafts` and nothing else, gated on
`site.show_drafts`, so a promoted drink would have rendered at
`/cocktails/recipes/<slug>/` and been listed **nowhere**. It now assigns
`all_drinks = site.cocktail_recipes`, concatenates the drafts only under
`site.show_drafts`, and every mood loop, the count and the card sort read
`all_drinks`. The #235 guard is unchanged in substance — the drafts, and only
the drafts, are behind the local-only key — and the empty-state test moved onto
`all_drinks`, which is the variable that has already had the draft question
asked of it. **Production still renders "Nothing to see here yet" because the
collection is empty, not because the template refuses to look at it.**

**The cards do NOT show the flags, and that was built and removed within the
same day.** The plan's D5 said "the same badges as food's cards", on the
premise that food's cards showed gate state. They do not: `needs rewrite` and
`needs proofread` stood on a recipe row until #562, when Helen asked for "all
metadata chips" off the rows — a work-state note on every unfinished row is a
to-do list down the side of the page you use to decide what to cook. A
local-only `_includes/cocktails/gate_badges.html` existed for one commit; shown
the #562 argument, Helen ruled the same for drinks and it was reverted. Two
things survive from it: `_includes/recipe_badges.html` renders TAXONOMY badges
(star ingredient, tag groups) and could never have served a drink; and
`meta.rewritten` briefly left `INVISIBLE_KEYS` because that include read it,
and went back when the include did (§4.0). The flags live in the file and in
the build log.

**One rendered-page test exercises the drink leg on a bare CI checkout**
(`test_the_gate_covers_a_promoted_drink` in `tests/test_rendered_pages.py`). It
writes two `zzz-gate-` drinks into `_cocktail_recipes/`, differing only in
`proofread`, builds, asserts one URL exists and the other does not, and asserts
the index lists one and not the other. That shape is issue #624's requirement:
a public test must never REQUIRE private drink data, because nothing
coordinates a public merge with a private one. It creates `_cocktail_recipes/`
and removes it again if it did — an empty directory left behind changes what
`_load_published` does on the next run.

### 9.2 The source data

`tmp/2021-01-29 Cocktails - Book.csv` — **118 drinks over 656 rows**,
gitignored and Jekyll-excluded. It is a starting point, not a source of
truth, and it is not uniform; do not write a parser that assumes it is.

Shape: **one row per ingredient**. Drink-level values sit on the drink's
first row, EXCEPT multi-value ones (method, garnish, notes, serve), which
spill down the following rows and still belong to the drink, not to the
ingredient beside them. Columns, in order: (unnamed name), `Ingredients`,
`Amount`, `Unit`, `Suggestion 1`, `Garnish`, `Method`, `Glass`, `Serve`,
`Notes`, `Source`, `Source URL`, `Status`, `Ship?`.

**Read it with a CSV parser, not by eye.** Pasted into a chat the empty tabs
collapse and free text lands in the wrong column — that happened, and it put
Cobra's Fang's "Honestly this just gets better and better" in `Notes` when
the file has it in `Method`. It is kept as a note anyway, flagged rather than
silently decided, because it plainly is not a step.

Known defects in the source, to expect rather than be surprised by:
`Corvoisier` should be Courvoisier; `La Fee Parisienne` and `Creme de Pêche`
are missing accents that `_data/accented_words.yml` covers (it lives at
`_data/` root precisely because it is house style for both sites, and `crème`
is its own worked example).

**The Sazerac's truncated last step is FIXED, 2026-08-31**, and how says
something about the CSV generally. It read "Strain the shaken drink into the
absinthe-coated" and stopped, carried as a `QQ` since 2026-08-16 — for fifteen
days, because nobody could complete somebody else's sentence. A photo ingest of
Death & Co put the same instruction in front of Helen in another book's words,
and she confirmed the ending in one line. **The CSV's truncations are not
mysteries, they are just missing text**, and the fastest route to one is
usually a second source rather than harder thinking.

### 9.2.1 Ingesting from photographs — the second source

**2026-08-31, the Death & Co batch**, and the shape recurs: Helen photographs
book pages into `tmp/inbox-cocktail-recipes/` (and `tmp/inbox-food-recipes/`)
and a session transcribes them. Ten drinks landed from fifteen photographs.

**RESOLVE EVERY RECIPE BY OPENING ITS PHOTO.** §12 already carries this from a
43-photo food batch, and it held again: two photographs caught only a title and
half an intro, from pages Helen had not meant to include. She said so and they
were dropped. **Do not infer a batch's contents from its folder.**

**A DRINK ALREADY IN THE COLLECTION MAY SHARE A NAME AND NOT BE THE SAME
DRINK.** Four of the ten were already here from the CSV. Three matched the book
exactly and gained the citation they had always lacked. The fourth was the
Sazerac, and it is **a different drink**: Helen's pours absinthe and chilled
water into the glass and splits the spirit three ways across rye, bourbon and
cognac; Death & Co's rinses and discards the absinthe, has no bourbon and no
water, runs 3:1 rye to cognac, and sweetens with demerara syrup. Two of *her*
suggestions are *its* bottles, which is what made them look like one recipe.
They live side by side now as `sazerac` and `sazerac-death-and-co` — her call:
*"name it 'Sazerac (Death & Co)', leaving mine as simply 'Sazerac'."*
**Compare the formula, never the title.**

**THE SOURCE IS THE BEST AUDIT THE COLLECTION EVER GETS.** Transcribing a page
beside a drink already derived from it found, in one pass: a citation missing on
four drinks, an ice instruction that said half where the book says
three-quarters, a serving count, and one amount out by a factor of 24
(`pic-a-de-crop-punch`'s 12 oz of overproof Demerara against half an ounce).
**Every one was recorded and none was changed** — §9.4.1, the site is canon, and
Georgetown Punch is the precedent: her figures stand and the source is noted
beside them.

> **AND THEN STOP TRACKING IT ONCE SHE HAS RULED.** Helen, on the 12 oz: *"we've
> agreed this twice now, so stop tracking it."* The note came off. A settled
> question left sitting in a `QQ` is a standing invitation to raise it a third
> time, which is §11.2's whole complaint. **A QQ that has been ANSWERED becomes a
> plain note recording the answer; only a QQ that was wrong to ask gets
> deleted.** The measurement survives in the commit that made it.

**HAND BACK THE BOTTLES.** Eleven bottles the book named were absent from
`bottles.yml` and none was declared, per §9.3.2 — a bottle's category is not
derived from the ingredient beside it. Helen's ruling: *"I will update these
when I make the drinks, so QQ is right. These won't get promoted until I've made
them."* She took exactly one, Dolin Blanc, because she already knew it.

**WHAT A PHOTOGRAPH CANNOT GIVE YOU, flag and raise.** Two drinks are unmakeable
from what was photographed — a method cut off mid-sentence (#627) and an
infusion recipe on a page nobody shot (#628). Both are flagged in the drink and
tracked as issues, deliberately paired so one trip to the book answers both:
*"I'm not digging the book out for just two!"* Truncations are never
reconstructed, even when the sibling recipes on the same page all end the same
way.

### 9.3 Cocktail front matter

```yaml
title: "Sazerac"
tagline: "QQ"                    # the one line of prose; QQ until written
glass:                           # LIST, not scalar — corrected 2026-08-17
  - "old fashioned"              # canonical spelling; `rocks` fails a test — §9.11.1
garnish: []                      # LIST, declared vocabulary — §9.12.1
  # ["no garnish"] = decided, [] = unfilled. Cobra's Fang has two.
ingredients:                     # FULL list, untriaged, in build order
  - amount: "15 ml"              # the ONLY quantity field, and NO US UNITS
    generic: "moderately aged Jamaican rum"  # the #314 vocabulary; see §9.3.1
    suggestion: "Appleton Estate Signature"  # the bottle, NAME(S) ONLY — §9.3.1
  - amount: "15 ml"
    generic:                     # a LIST means "or", never "and" — §9.3.1
      - "lightly aged and filtered rum"
      - "clear blended multi-region rum"
    suggestion: "Havana Club 3"
    note: "Whichever you prefer or are trying to use up"   # the REASON, resolving #457
  - amount: "15 ml"
    generic: "moderately aged rum"
    character:                   # a property of THIS RECIPE'S use of the
      - "blackstrap"             # bottle, not of the bottle in the abstract — #441, §9.3.1
    suggestion: "Gosling's Black Seal"
    optional: true               # BOOLEAN, absent means required — #570
method:                          # ORDERED LIST — the steps are sequential
  - "Pour absinthe into ice-filled glass."
to_serve: ""                     # PRESENTATION, not a further instruction
mood:                            # LIST, DERIVED and then stored — see below
  - "sharp"
  - "aperitivo"
notes:                           # {label, text} or a bare string, as food
  - "This is much less sugar than many recipes"
  - label: "QQ"                  # 81 of the 170 are the ingest audit
    text: "QQ - `generic` values INFERRED, not confirmed: ..."   # trail — #572
source: ""
source_url: ""                   # external; nothing verifies it
meta:
  ship: "oh gods yes"            # a real ordered vocabulary now — see §9.5
  date_last_edited: "2026-08-16"
```

**`mood` IS DERIVED AND THEN STORED, and this document had never said so** —
until 2026-09-02 it was written down only in `INGEST_ONE_COCKTAIL.md` L95 and in
`taxonomy.yml`, which is how a key on all 124 drinks stayed absent from the
schema block above. `scripts/derive_cocktail_moods.py --write` computes it from
the drink's generics, characters, glass, amounts and method steps against
`mood_ingredients` in `taxonomy.yml`, and writes the result into the file; the
stored list is what the index filters on, so the derivation runs at ingest
rather than at build time. **Change a drink's ingredients and the moods may
move**, which is why the script is run dry after any such edit and `--write`
only if it reports a difference.
`test_every_drinks_moods_match_the_derivation` is what keeps the stored value
honest: it re-derives all 124 and fails on any drink whose file disagrees, so a
hand-edited mood list cannot quietly outlive the rule that produced it. Helen's
own rulings override the derivation and always win — `mood_include` /
`mood_exclude` in `taxonomy.yml`, each naming the single mood it is about, with
`test_every_mood_correction_is_reachable_and_needed` as their guard.

**`amount` IS THE ONLY QUANTITY FIELD. `ml:` is retired — #571, 2026-08-30.**
Every entry used to carry the same quantity twice, `amount: "25 ml"` beside
`ml: 25`. Helen: *"Food YAML has this structure, and I'd like cocktails to
match."*

**Measured before deleting**, because the pair had a stated justification —
"the string carries units a number cannot", true of `0.5 oz` and `3 dashes` and
false of `25 ml`, which was 376 of the 619 entries. **521 entries carried both
and all 521 derive exactly** from `measures:` in `ingredients.yml`; the other 98
are non-volumetric and not one of them carried an `ml` at all. The data already
obeyed the rule and was writing the answer down twice.

**What the key was actually buying was the GUARANTEE that a number exists** —
which #545, #294/#297 and #547 all need, and which it never delivered: it could
simply be absent, and on all 19 unitless amounts it was.
`test_every_amount_is_readable_as_a_quantity` is that guarantee now, and it is
stronger, because an amount nothing can read fails instead of shrugging.

Conversions live in `measures:`: 1 oz → 30 ml, 1 tsp → 5 ml, 1 cl → 10 ml. That
is bar-standard rounding, not 29.5735; it keeps ratios clean and it is a
decision, not an accident. Non-volumetric units are declared there too, so a
dash is *known* to have no millilitre figure rather than merely lacking one.

**NO DRINK MAY USE A US UNIT. Helen's ruling, 2026-08-31:** *"I don't want any
US units, just ml, so please convert for me as part of ingestion. 1 oz = 30
ml."* Extended to `tsp` in the same breath. 191 amounts across 44 drinks were
converted; `test_no_amount_uses_a_us_unit` is the guard, and `US_UNITS` is its
list (oz, tsp, tbsp, cup, and their long forms).

**`oz` AND `tsp` STAY DECLARED IN `measures:`, AND THAT IS NOT AN OVERSIGHT.**
`test_the_declared_measures_produce_the_figures_the_data_used_to_store` anchors
on `("0.5 oz", 15.0)` — the dictionary is what makes a conversion *checkable*,
so deleting the entries would delete the arithmetic that proves the conversion
was right. The dictionary says what a unit MEANS; the new test says which units
the collection may USE. Those are different claims and want different homes.

**CONVERT AT INGEST, from the source's own figure** — an American book prints
ounces and the drink stores millilitres. §9.4.1 still holds: the site is canon,
so a converted figure is the site's, and the source's own is worth a note only
where it disagrees with something already stored.

**NINETEEN AMOUNTS ARE A BARE NUMBER AND MUST NOT BE GUESSED.**
Port-au-Prince's ladder (30, 22.5, 15, 7.5) is plainly millilitres and Drunken
Skull's (0.75, 0.5) is just as plainly ounces — thirty times apart, and a wrong
guess looks exactly as confident as a right one. All nineteen carry a
`QQ - no unit in the source` note, and the guard reads that note rather than a
registry of slugs, so filling one in without removing the note fails too.

**EVERY INGREDIENT HAS AN AMOUNT, AND FOR SOME IT IS A VERB — Helen, 2026-09-02,
#669.** Eleven entries carried no `amount` at all and no test noticed. Her
ruling is that there is no amount-less case: an ingredient the method ADDS
rather than measures still says how much, and the list reads "champagne, to
top" and "absinthe, to rinse". So six champagnes and two soda waters became
`amount: "to top"`, `sazerac-death-and-co`'s absinthe and `tailspin`'s Campari
became `amount: "to rinse"`, and `man-o-war`'s salt — which goes IN the drink
and is **not** a rim — became `amount: "1 small pinch"`, its `item: "Tiny pinch
of salt"` deleted for restating the quantity. `to top`, `to rinse` and `small
pinch` are declared in `measures:` `non_volumetric` alongside `dash`, and
`_millilitres` reads them by that same path: **the two strings appear nowhere
in the test**, because special-casing them there would move the vocabulary out
of the data. The matching method steps are `Top with champagne.` / `Top with
soda water.` / `Rinse the glass with absinthe and dump.` — the amount says how
much, the step says when.

**SODA WATER, NEVER CLUB SODA**, same ruling: she is not in the US and doubts
the difference is more than marketing. Eight drinks said club soda in a step or
an `item` and were normalised; the one surviving mention is inside a `QQ` note
on `la-fee-noir-punch` recording what a source said, and a QQ is never rewritten
to match a later decision. And the rim wording is hers: **"Salt a half-rim of
the glass."**, preferred over "Salt half the rim of the glass" — canonical in
`methods.yml`, with `margarita-classic`'s "Dip only half the rim in salt."
proposed for it rather than rewritten, because this file proposes and never
applies.

**`item` IS BEING RETIRED — #544, and it is most of the way gone.** It held
what the SOURCE called the ingredient, brand-led; `generic` is the category, and
no rule derives the second from the first, which is why that one is stored.
619 entries carried an `item`; **282 still do** — re-measured 2026-08-31 and
unchanged, though the collection is 682 entries across 124 drinks now, so the
migration has stalled rather than progressed. New drinks are written without
`item` at all, which is why the absolute figure holds while the share falls.

What has gone, and why each was safe rather than judged:

| | |
|---|---|
| **177** | every word already in the entry's own generic or suggestion — `Prosecco`/`prosecco` |
| **106** | the only addition was `fresh`, which `ingredients.yml` bans in its own capitals |
| **61** | the item WAS a bottle, promoted to `suggestion` on Helen's ruling — see below |

**The 61 were 26 bottles, not 61 decisions**, and she ruled on them from a
review page: Angostura alone was 16 entries, Velvet Falernum 9. Two came off
rather than being promoted (Flor de Caña Extra Dry, Ron del Barrito). The
evidence that made it quick was that **14 of the 26 were already named as a
`suggestion` on another drink** — her reaching for the bottle in writing,
elsewhere.

**What is left is 269 entries with real residue plus 19 parentheticals**, and
two of Helen's own issues sit inside it: `cane` ×31 is #594 (cane vs demerara vs
turbinado syrup) and the retired colour vocabulary is #542's territory.

**THE GATE IS THE TRAP HERE, and it fired for real.** The drink page's
ingredient line was `{% raw %}{% if item.item %}{% endraw %}` — the one field
#544 move 1 stopped rendering — so removing an `item` printed
`{"amount"=>"90 ml", "generic"=>"prosecco"}` on the page, clean build, nothing
in the log. Four guards in the test suite had the same stale gate. Both fixed
*before* any deletion, with the whole suite run green first to prove the repoint
changed nothing. **A condition is a bet on which field carries the content, and
moving the content silently voids it** — §12's nested-CSS-rule trap, in Liquid.

**`generic` is fully typed, and it is what the index browses by.** Re-measured
2026-08-29 by parsing every drink rather than grepping: **619 ingredient
entries, 0 untyped and 0 carrying a `QQ` generic.** #335 ("type the remaining 68
QQ generics") was therefore complete and stayed open — closed on that
measurement. The "526+ of 594, #335 tracks the rest" figure that stood here was
two coverage passes out of date, and the issue itself was one more behind that.
Coverage stays honest on its own: `test_every_ingredient_has_a_generic_or_a_qq`
means an untyped ingredient is always a visible `QQ`, never an absent key, so
this backlog cannot quietly regrow. It is still
the cocktails analogue of food's `main_ingredients` rather than a copy, and
**since #501 it is also what a rum shows on a card** — see §9.10.1. §9.1's "no
star axis" rule still holds: the index filters and excludes by ingredient, it
does not browse by spirit.

### 9.3.1 The ingredient vocabulary — `_data/cocktails/ingredients.yml`

Spec: #322 (closed once delivered — the spec/backlog split, same shape as
food's taxonomy work). Rum half: #314. This file is the actual source of
truth for what a `generic` is allowed to be; treat it as more current than
this document if the two ever disagree.

**Two layers, and the distinction is the whole design.** `generic` is the
precise category on each ingredient entry — Campari, Aperol, Cynar and
Fernet are four generics, not one "amaro", because they taste nothing alike
and are not substitutable. `family` is a roll-up used ONLY for search and
exclusion ("no whisky tonight"), never a browse axis — see the file's own
comment for why food's family-derivation mechanism can't be reused here
(the rum styles share no common word to derive an `(all)` button from).

**`generic` IS STORED, NEVER DERIVED.** 61+ ingredients in the collection
are named only by brand (Campari, Cointreau, Kahlua…) with no rule able to
recover the category from the name.

**A preferred bottle is a `suggestion`, never a `generic`.** Helen,
2026-08-17, on Cherry Heering: "I'd note my preference as the example not
the category." So Velvet Falernum → `falernum`, Luxardo → `maraschino
liqueur`, with the bottle in `suggestion`. `suggestion` can also be a LIST
when there's more than one live candidate (e.g. Cynar Toronto's bitters:
`["(Mrs Betters Lime Leaf bitters)", "Bob's Margarita bitters"]` before it
was resolved) — this is presentation, not a filter, so it has no
disjunctive/conjunctive rule the way `generic` does.

**`generic` as a list means OR, and ONLY or — settled by #441, 2026-08-21.**
This mattered enough to need its own issue because the same YAML shape
(`generic:` followed by a list) was about to mean two different things:

| | means | exclusion should |
|---|---|---|
| a genuinely interchangeable rum (Daisy de Santiago: Havana 3 **or** Clément Agricole Blanc) | either bottle makes the drink | **not** drop the drink — pour the other one |
| Gosling's Black Seal: `moderately aged` **and** blackstrap | one bottle, two properties at once | **drop** the drink — there is no escape route |

The fix: `generic` stays disjunctive-only. A list is always "any of these
would do." A single bottle that carries an extra flavour property alongside
its style (blackstrap, a sherry-cask character) does NOT go in `generic` —
that's `character`, and **where `character` belongs is still open**, see
below. Getting this distinction right the first time mattered because #292's
exclusion logic ("no whisky tonight") would silently misbehave on whichever
one was encoded wrong.

**`character` — RESOLVED, #441, 2026-08-23. It lives on the recipe, not a
bottle dictionary.** The issue's first draft argued the opposite — a shared
bottle table (name → generic, ABV, character), because `character` "must
not be repeated across 594 recipe entries." Helen, walked through from
scratch, overturned that premise: `character` isn't a bottle-invariant fact
the way ABV genuinely is — it's *why this drink wants this bottle*, which is
inherently a property of the recipe's use of it. So restating it across
recipes that happen to suggest the same bottle for the same reason isn't
duplication of one fact, it's each recipe independently and correctly
stating its own reasoning. Airmail's original structured field —
`character: [sherry, "Spanish-style"]`, plus `rum_characters` in
`ingredients.yml` — was therefore right; Georgetown Punch and Don's Own
Grog's plain-note interim ("becomes a `character` once that layer exists")
was the thing that got fixed, brought in line with Airmail's shape. #297
(ABV) and #295 (glass volumes) explicitly do NOT get the same free pass —
they're genuinely bottle-invariant, so this reasoning doesn't extend to
them.

**`blackstrap` IS A CHARACTER AND NEVER A GENERIC — #314, Helen,
2026-08-24.** "Blackstrap is only ever given as a character for another rum,
like this: Moderately aged (character: blackstrap)." So the rum still needs a
real style of its own and blackstrap rides alongside it. This took two days to
reach the vocabulary: `ingredients.yml` was written 2026-08-22 and listed
blackstrap under `rum_untyped` with a comment saying it could be **either**
field. Applied 2026-08-26, along with Jungle Bird — the one drink using it as
a generic. Don's Own Grog, Georgetown Punch and Jungle Bird now all carry
`moderately aged` + `character: [blackstrap]` + Gosling's.

**And until the same day, `character` WAS GUARDED BY NOTHING.** Every check in
`tests/test_cocktails.py` pointed at `generic`, so a typo in the field this
whole section exists to separate out minted a value in silence. Worse, the
excluding of `rum_characters` from the declared-generic set — correct in
itself, since `sherry` and `Spanish-style` had been silently passing AS
generics on any ingredient — left that list declared and consumed by nothing
at all. `test_rum_character_is_declared` closes it. **Only rum's characters
are checked**: gin's are free text by Helen's explicit call, because a rum's
come from a handful of production traits and close into a list while a gin's
is whatever the distiller reached for.

**The governing principle behind that call, #459**: "everything we do is
focused on the user (i.e. Helen), and making sure the user gets the drink
she wants. Being an encyclopaedia of drinks sounds like busywork and it's
not for me." A shared bottle-reference table would have been exactly that
busywork. Apply the same test forward, to any future feature that describes
a bottle or spirit in the abstract rather than in service of one recipe
decision.

**`suggestion` vs. a new per-ingredient `note` — RESOLVED, #457,
2026-08-23.** Six suggestions had drifted into full sentences carrying
reasoning ("Beefeater is nice for a brighter drink against the mint"), not
just a bottle name. Same argument as `character`: the reasoning belongs on
the recipe, but not smuggled into `suggestion` — it gets its own `note` key
per ingredient, mirroring food's existing `item.note`
(`_layouts/recipe.html`, rendered inline with a small annotation mark).
`suggestion` goes back to being name(s) only, string or list. One
exception: Caipirinha's cachaça ranking ("Sagatiba = Leblon > Viero
Barriero > Abelho > Yaguara Organic") stayed a single string rather than
being forced into the list shape, because the `=`/`>` notation IS the
content, not decoration on top of a name — `suggestion` became the tied
top pick (`[Sagatiba, Leblon]`) and the full ranking moved to a drink-level
note verbatim, no explanation added, at Helen's explicit request ("Future
Helen will know exactly what I mean").

~~**Neither `character` nor `note` render on the page yet, and neither
does a list-form `generic`/`suggestion` — #460.**~~ **RESOLVED,
2026-08-25.** `_layouts/cocktail.html` now renders all four correctly —
see §9.10 for the shape. #460 stays open for the REST of the page (method,
notes, meta), which still hasn't had a design pass — this was the
ingredient list specifically.

**EVERY GENERIC NOW READS AS AN INGREDIENT — #561, 2026-08-29.** Ten did not,
and that is what blocked the drink page: a card name may be lossy (`gin` is right
for London dry at card distance), a recipe line may not. Helen's pattern, given
as two examples and extended across — **natural word order, spirit word on the
end, no inverted commas**:

| was | is |
|---|---|
| `Jamaican, moderately aged` | moderately aged Jamaican rum |
| `Jamaican, caramel forward` | caramel-forward Jamaican rum |
| `Jamaican, overproof, unaged` | unaged overproof Jamaican rum |
| `Demerara, aged` / `Demerara, overproof` | aged / overproof Demerara rum |
| `moderately aged` | moderately aged rum |
| `lightly aged and filtered` | lightly aged and filtered rum |
| `blended multi-region rum, clear` | clear blended multi-region rum |
| `cane juice (agricole) rum, unaged` / `, aged` | rhum agricole blanc / vieux |
| `London dry` / `navy strength` | London dry gin / navy strength gin |

The agricoles take their real French names at Helen's direction. On the
mouthfuls: *"they're almost always going to be on their own line, so eminently
skippable if wanted, and I don't want to do the cognitive work of mapping to
Minimalist Tiki every time I read them."* The card names carry the short forms,
which is exactly the division those two strings exist for.

**Renaming a generic is quote-anchored, and must be.** `moderately aged` is a
substring of `Jamaican, moderately aged`, so a bare replace corrupts the longer
one. Every occurrence in front matter and in the data files is quoted, so
matching `"<old>"` is exact — and the inference notes (`-> <generic>`) want the
same treatment, while narrative prose and quoted decisions must be left alone.
**Rewriting a quote to match a later rename falsifies it.**

**THE THREE BRAND-GENERICS ARE GONE — #314's amendment, same day.** `Planteray
Stiggins' Fancy`, `Planteray O.F.T.D. Overproof` and `Malibu` were permitted as
generics *"because nothing generalises them"*. All three have been generalised —
`pineapple rum`, `blended overproof rum`, `coconut rum` — so the exception lost
its reason, and dissolving it RESTORES this file's primary rule rather than
weakening it: a preferred bottle is a `suggestion`, never a `generic`. `rum_untyped`
is now an empty declaration, kept so the next reader learns the group existed.

It also housed something homeless: Pusser's 151 fails the DDL rule and
`moderately aged rum` says nothing about strength, so `blended overproof rum` is
the first category it fits. **Second time a naming decision fixed a data gap it
was not aimed at** — and the data had already said so, since both Malibu drinks
wrote `Coconut rum` in their `item`.

**`peated Scotch` is retired; peat is a `character`.** Orthogonal to
single-malt-versus-blended, so a peated single malt is both and one field could
not hold it. Both drinks that used it proved the point — their items read "Peated
single malt whisky" and "Peated Scotch whisky". They are `single malt scotch
whisky` + `character: [peated]` now.

**Whisky is named correctly rather than dodged, and peat is a character** —
2026-08-27/29. Scotch and Japanese take *whisky*, Irish and American take
*whiskey*; `blended Scotch`, `Irish` and `Japanese` said neither, which looked
tidy and was an unmade decision. All three were used by zero drinks, so the fix
was free. `bonded rye` joined as a real style rather than a strength — Helen:
"bonded rye is a different thing, like overproof demerara rum", and five of the
seven rye entries already say bonded or 100 proof in their item text, so plain
`rye` was the exception wearing the default's clothes. `rye` and `bourbon` stay
BARE, because the test is the name you would say out loud.

**`peated` is a `character`, not a style**, for #441's reason: peat is
orthogonal to single-malt-versus-blended, so a peated single malt is both. Both
drinks using `peated Scotch` prove it — their items read "Peated single malt
whisky" and "Peated Scotch whisky", one field carrying two facts.

**The GUARD is the load-bearing half, and it is derived from the suffix now.**
Adding `whisky_characters` alone would have made `peated` a permitted GENERIC,
because the declared-generic set is every top-level list minus a hand-written
exclusion — the precise hole `rum_characters` sat in for four days while
`sherry` and `Spanish-style` passed as generics. Any `<family>_characters` list
is now excluded by its name, and `test_a_declared_character_vocabulary_is_enforced`
checks every family that declares one. **Declaring a list is what switches
enforcement on**, so gin's free-text characters stay correctly unchecked and a
vocabulary can no longer outrun its guard.

**Every rum generic also has a CARD NAME, `card_names` — #501,
2026-08-27.** A third string per rum category, beside the generic and the
family, and it exists because the index cannot show the full name and must not
show the item. See §9.10.1; that section is where the reasoning lives.

**Disjunctive `generic` has an agreed threshold, not a free-for-all.**
Helen, 2026-08-21: multi-value only when both bottles can actually be named
and a reason given for each — "I don't know which" stays a plain `QQ`, it
does not become a two-item guess.

**FIVE VOCABULARY RULINGS FROM 2026-08-30, all Helen's, all recorded because
the chartreuse one below proves what happens otherwise.**

- **`Chartreuse Verte` / `Chartreuse Jaune`**, not green/yellow. She and an
  earlier session had agreed this and it was **written down nowhere** — not in
  the data, the handover, or either repo's history, all four checked. So it was
  decided, never applied, and had no way of surviving the session it happened
  in. That is §11.2 in its purest form and the reason the other four are here.
- **`sloe gin` is its own generic**, split out of `gin liqueur`. That name had
  the identical fault `flavoured` was retired for — "covered everything from
  sloe to rhubarb to cucumber" — and unlike `speciality` it carried no
  `character` to say which. Both its members were sloe. **No guard could catch
  it**: every value involved was declared and valid. Helen found it looking at a
  card.
- **Five aromatised-wine generics** (#568): the three vermouths, `quinquina`,
  `americano`. Helen: *"I would never write 'aromatised wine' as a cocktail
  ingredient or generic, because it suggests some equivalence between the types
  where none or very little exists."* The roll-up is a FAMILY and already
  exists as `fortified`, so nothing needed building. `americano` was the only
  addition and was overdue — `quinquina`'s own comment covered Cocchi Americano
  too.
- **`Punt e Mes` stays a generic**, proposed for retirement and saved by the
  data: The Ridgwell pours 12.5 ml of it AND 12.5 ml of Martini Rosso. Collapse
  them and that drink asks for 25 ml of one thing. **The retirement was proposed
  on a bad measurement of mine** — a scan matching generics containing
  "vermouth"/"sherry"/"quinquina", and this one contains none of those words.
- **`pastis` retired**, and as a CONSEQUENCE rather than a judgement about
  pastis: its stated reason was the Swizzle's "6 drops of Pernod or absinthe",
  and that drink became the Martinique Swizzle the same day. Re-declare it when
  a drink wants one.

**FOUR MORE FROM 2026-08-31, all Helen's, all forced by one photo ingest** — the
Death & Co batch in §9.2.1 hit each of them as an untyped ingredient.

- **`apple brandy` added.** Pink Lady pours Laird's Bonded, an American
  applejack. **It is not `calvados`**, which names a French appellation — the
  same kind of category as the two Demeraras, checkable against a fact about the
  bottle. Naming it after the FRUIT rather than the country is what lets an
  applejack and a Spanish apple brandy share it honestly.
- **`Becherovka` added, and the reasoning generalises to every future case.**
  Helen's worry was that filing it under herbal liqueurs would claim it swaps
  for Chartreuse: *"'Herbal liqueur (Becherovka)' would be misleading. This will
  come up over and over and I don't know what to do about it."* **It never
  renders that way.** Every member of `herbal_liqueurs` is already a proper
  noun, for exactly her reason — nothing generalises them and none is
  substitutable — so the group is a filing drawer and the recipe line shows the
  GENERIC, which is `Becherovka`. `herbal` is the family, and a family is a
  search-and-exclusion roll-up, never a browse axis. Same shape as the amari.
  **The rule: when nothing generalises a bottle, the bottle IS the generic.**
  That is not an exception to §9.3.1's "a preferred bottle is a `suggestion`,
  never a `generic`" — it is what that rule already does for Campari and Cynar.
  Her *"cinnamon- or ginger-forward"* went where such things go: a per-ingredient
  `note` on the drink, per #457. Its `warming` entry executed a standing
  instruction rather than making a call — `taxonomy.yml` had said since
  2026-08-30 *"Becherovka is the third and the collection has none; add it here
  the day a drink does"*, and she described it in those terms before seeing that.
- **`cucumber` and `kaffir lime leaves` added, bare.** Helen: *"will need to go
  in the dictionary naked."* **The leaf is not a variety of `lime`** — it is an
  aromatic that tastes nothing like the fruit, so collapsing them would let an
  exclusion on one silently drop drinks built on the other.

**"Pernod" NAMES TWO BOTTLES** — Absinthe at 68% and Anise at 40%, which is the
pastis. That ambiguity misled twice in two days: once as a note on Don's Mai Tai
claiming a substitution, once as a declaration derived from the generic beside
it. Helen pours the absinthe, so there was never a substitution. **Write the
product, not the house.**

### 9.3.2 The bottle dictionary — `_data/cocktails/bottles.yml`, #529

**A third string per ingredient, after the generic and the card name: which
BOTTLE, and what category it is.** Added 2026-08-27, and each bottle has one
generic plus its alias spellings.

**IT STOPPED BEING RUM-ONLY ON 2026-08-30 AND SO DID THE TWO TESTS THAT MADE IT
WORTH HAVING**, which is the more important half. `test_every_suggested_bottle_resolves`
and `_cross_category_scan` both skipped any ingredient whose generic was not in
the rum family — so of the collection's 91 distinct suggestions, **54 resolved to
nothing and no test minded**. Beefeater, Cointreau, Tanqueray, Luxardo, Suze,
Punt e Mes: all invisible. Helen: *"are we now assuming every named bottle
should be in it, and classified? That feels right to me."* On the day: 57
resolve, 34 declared debt in `unresolved_suggestions`, none unchecked. **Those
are the figures for 2026-08-30 and are kept as a snapshot rather than a
count** — the debt block is a worklist and is 16 as of 2026-09-02; see §9.3.2.

**The suggestion count moves with every ingest — 91 then, 103 on 2026-08-31 —
so count them rather than quoting a figure from here.** What does not move is
the rule: a bottle the collection does not already spell out is handed back
rather than declared (§9.3.2 below), so a photo ingest adds QQ notes, not
entries.

**A SUGGESTION'S BOTTLE NEED NOT BE IN THE INGREDIENT'S CATEGORY, and that is
the feature.** Helen: *"a recipe might call for cherry brandy, and I suggest
Cherry Heering OR Briottet cerise even though that's a cherry liqueur not a
brandy, leaving it to future Helen to choose what kind of drink I want at the
time."* #534 requires a note when it happens, and `QQ` counts — the substitution
must be VISIBLE, not explained.

**DO NOT DERIVE A BOTTLE'S CATEGORY FROM THE INGREDIENT IT SITS BESIDE.** It is
a good default and it is not a rule, and the 2026-08-30 session declared 43
bottles that way before Helen stopped it: *"keep only what the collection
already spells out; hand me back the rest."* One was outright wrong (`Pernod`
declared an absinthe), and the failure mode is the one #542 warns about — a
plausible declaration teaches #534's check a false fact and blinds it to the
substitution it exists to catch. Nine more were fragments completed from memory:
the collection wrote `Portobello`, `Luxardo`, `Bob's`, and a full product name
was supplied that appears nowhere in the data.

**A BRAND IS NOT A BOTTLE.** `Briottet` sits beside six different generics and
`Monin` beside four, so those strings name a house and the drink names the
product. Helen: *"Briottet creme de peche is the bottle, that's its name."* They
stay in `unresolved_suggestions` until the drink says which.

**Why this is allowed when #441 rejected a bottle table.** That issue killed a
shared table for `character`, because character is why THIS DRINK wants THIS
BOTTLE — a property of the recipe's use. A bottle's CATEGORY is
bottle-invariant: Appleton 12 is a moderately-aged Jamaican in every drink that
pours it. Helen settled it by writing eight rulings in #314 in exactly that
shape ("Blackwell is Jamaican, caramel forward"). #297 (ABV) is on the same
invariant side; do not read this as reopening `character`.

**It means what Helen would POUR, not what qualifies.** The case that separates
them: Lemon Hart 151 clears the Demerara appellation and is deliberately absent
because she does not like it. `not_reached_for` holds the exclusions with
reasons, the `family_less` idiom. A list of everything that qualifies is the
busywork #459 rules out.

**`Demerara, aged` and `Demerara, overproof` are APPELLATIONS.** Helen,
2026-08-27, from *Minimalist Tiki*: 100% of the distillate must come from DDL
in Guyana. **Two of the eleven rum styles are therefore a different KIND of
category from the other nine** — checkable against a fact about the bottle
rather than argued from the glass. It is why both Pusser's are `moderately
aged` despite tasting Demerara, and why Skipper's needed her rather than
inference ("all seven distinct rums blended into it are by DDL" — a Halewood
bottling of Guyanese rum *very probably* qualifies, and that is not what a 100%
rule asserts). Wood's is `Demerara, aged` and not overproof: 57% is AT proof,
which begins above 57.15%.

**Aliases are how a bottle keeps one identity**, and they are load-bearing:
twelve suggestion strings collapse to about five bottles, and **Planteray and
Plantation are one brand renamed**, which no string comparison recovers.
Planteray is canonical (Helen, 2026-08-27) and the old spellings STAY as
aliases — not a half-finished rename, but the same division `canonical_glasses`
draws: **the rule governs what is WRITTEN, the alias map governs what can be
READ.** The drinks predate the rebrand, so a suggestion has to keep resolving
whether or not its drink has been retyped.

**`unresolved_suggestions` is the interesting block.** It holds every suggestion
string that names no bottle — prose (#457 again, drifted back), or two bottles
in one comma-joined string where a list is wanted. They are declared with
reasons so `test_every_suggested_bottle_resolves` bites on the NEXT one rather
than being switched off; deleting a line retires it.

**COUNT IT, DO NOT QUOTE IT.** This paragraph said "eleven" from 2026-08-27
until 2026-09-02, and the block has been 34, 30 and 16 since — it is a WORKLIST,
so its number is a fact about the day it was written and moves every time Helen
rules on a row. It has its own staleness guard now, added with #585's pass: a
declared row whose string no longer appears in any drink is a row claiming debt
that has been paid, and seven of them were exactly that.

**A BARE BRAND IS NOT A BOTTLE, and #585 made this a rule rather than a
recurring surprise.** `Planteray` names four products here; `Bulleit` makes a
bourbon and a rye, both of which Helen owns; `Briottet` makes six things this
collection pours. So a suggestion naming only the house resolves to nothing
useful, and completing it is Helen's — she chose `Planteray 3 Stars` and
`Bulleit Bourbon` on 2026-09-02. **Declare the PRODUCT, and do not add the bare
name as an alias**: a later drink meaning the rye would resolve to the bourbon
silently, which is the exact failure this file exists to prevent.

**JACK DANIELS IS A BOURBON HERE, and the story is a correction of mine.** #585
held eight bottles back rather than declaring them, on the sound rule that a
category must never be derived from the generic beside it — and offered Jack
Daniels as the proof, saying it "is Tennessee whiskey, which is a different
legal category". **That was wrong.** Tennessee whiskey meets the bourbon
standard in full; the Lincoln County Process is an addition on top, not an
exemption from it. Helen: *"It meets all the legal requirements for being
called that, and their own decision to apply a further qualifier on top is...
vain!"* **The rule stands and the example did not** — the eleven bottles handed
back on 2026-08-30 are still the reason for it.

**ONE DRINK CHANGED SHAPE BECAUSE A BOTTLE BECAME READABLE.** Royal Bermuda
Yacht Club suggested `ED3, Planteray` as one unresolvable string; splitting it
and resolving the second half made #534's cross-category check fire, because
Planteray 3 Stars is a `clear blended multi-region rum` and the drink's
`generic` asked only for `lightly aged and filtered rum`. Helen's answer widened
the recipe rather than the note: *"the generic wants two categories. Both make
excellent drinks, just quite different ones."* So the generic is a disjunctive
pair now and the suggestion crosses nothing. See §12 for the general form,
which is the more useful half.

**Smith & Cross moved to `Jamaican, moderately aged`** from `Jamaican,
overproof, unaged` (2026-08-27), which resolved the one bottle that had been
sitting under two generics. It is aged; 57% is what made it look unaged, and
strength is not what that category names. It carries the collection's first
BOTTLE-level `note` ("be sensible about how much you use") — bottle-invariant
in the way #297's ABV is, so it does **not** reopen #441.

**#534's check is built, and it is deliberately permissive.** A `suggestion`
whose bottle sits in a different category than that ingredient's `generic` must
carry a `note`, and **`QQ` counts** — Helen: "be permissive with the test, but
given we're pre-first-human-read please add the note field with QQ in it if we
don't have anything else." So a substitution can never ship silently while
nothing demands prose she has not written. A disjunctive `generic` crosses only
if the bottle matches NONE of its options.

**What it found on its first run is the useful part: four of six were not
substitutions at all**, they were #314's rulings not yet applied to the drinks —
a suggestion naming a bottle from the category the generic *should* have been.
The check cannot tell those apart from a real substitution and should not try:
for a mistype the answer is to fix the type, not to explain it. Helen's call was
to drop those four suggestions, which **silences the check without changing the
generic** — hurricane-classic and tiki-max still say `Demerara, aged` on items
called `Overproof Navy rum` and `Navy rum`. Knowingly accepted, pending her
classification pass; the bottle was the last trace of which rum each meant and
that trace is now only in git history.

**An absent suggestion is a real answer**, and 2026-08-27 produced the first
two: Long Island Iced Tea's rum and Milliners Punch's "cheapest white rum to
hand; sometimes JW Spicers". Both came off rather than being corrected, and the
rule underneath is one rule, not two coincidences: **what is cheap and what
needs using up are facts about the shelf on the day, never about the drink.**

The line that test sits on: Frozen Fruit Daiquiri's `"Best with ED3, Havana 3
is fine"` STAYS. It is prose and wants reshaping into a list plus a note, but a
ranked preference between two bottles she owns *is* a fact about the drink.
**An earlier draft of this section had that drink dropping its suggestion**,
because the Spicers string was misattributed to it rather than to Milliners
Punch; `test_every_suggested_bottle_resolves` caught the edit, not a reader.

**`caramel-forward Jamaican rum` still has no drink**, and did not gain two as an
earlier session note claimed. Blackwell was going to bring cobra-effect and
georgetown-punch into it; Helen dropped both suggestions instead ("I never use
Blackwell there"). The style has bottles — Blackwell, Myers — and no user, and
**it is hers to apply**: never retype a drink into it from item text.

> ### THAT PARAGRAPH WAS ALREADY HERE AND DID NOT HOLD. IT IS A TEST NOW.
>
> Between it being written and 2026-08-30, a session put cobra-effect into
> `caramel-forward Jamaican rum` from its own `item` text, with a Blackwell
> suggestion — the exact thing the sentence above forbids. Helen: *"I remain
> annoyed about this. I have discussed this at least twice… If I have to deal
> with this again I will simply delete those recipes."*
>
> **`hers_to_apply` in `ingredients.yml` is the mechanism**, checked by
> `test_no_drink_uses_a_generic_that_is_helens_to_apply`. Adding a line
> switches enforcement on; **removing one is Helen's grant**, made in the same
> commit as the drink that earns the style, and never to turn a red green.
>
> **#542 diagnosed its own invisibility and nobody built the answer**, which is
> the part to carry. Its own text says "a wrong-but-declared value with no
> contradicting evidence is invisible to every guard in the suite" — every
> value declared, `test_every_generic_is_declared` green, and the suggestion
> that would have disagreed already dropped, so #534 green too. Writing that
> diagnosis down felt like handling it. It is §12's "you will write down a rule
> instead of following it", one level up: **stating why nothing can catch
> something is not catching it.**

**THE FOUR #542 RULINGS, Helen 2026-08-30, applied the same day.** Recorded here
because the last set was recorded only in an issue comment and was reversed
inside three days. Names are the post-#561 ones; she wrote the older shorthand.

| drink | generic | suggestion |
|---|---|---|
| `hurricane-classic` | `moderately aged rum` | **Pusser's Gunpowder** |
| `tiki-max` | `moderately aged rum` | **Pusser's Blue Label** |
| `cobra-effect` | `moderately aged Jamaican rum` | **none, deliberately** |
| `georgetown-punch` | `lightly aged and filtered rum`, then `moderately aged rum` + `character: [blackstrap]` | Gosling's |

Both Pusser's are already declared `moderately aged rum` in `bottles.yml`, so
these two restore the evidence #542 says was deleted, and neither crosses a
category or needs a #534 note. Georgetown Punch already matched her ruling; what
it gained is a note carrying the source's own figures, which differ from hers in
two amounts (22.5 ml against 20 ml of each juice) and name Koko Kanu rather than
Malibu. Her figures stand — §9.4.1, the site is canon — and the source is
recorded beside them rather than argued with.

### 9.3.3 The drinks index's search — three modules, and what each ruling was

**#579, 2026-08-29/30.** `cocktail-index.js` was 428 lines that reused nothing
from the food index and hand-rolled vocabulary derivation, ranked matching and
filter state. It is DOM wiring now and nothing else.

| | |
|---|---|
| `assets/js/cocktail-search.js` | pool, ranking, families, the two matching rules. Pure. `tests/js/cocktail-search.test.js` |
| `assets/js/filter-state.js` | `COCKTAIL_FIELDS` — one mechanism, two tables, food's untouched |
| `assets/js/ingredient-search.js` | `fold`, `getWords`, `orderByBand` — shared |

**What is shared is the DISCIPLINE, not the bands.** `orderByBand` takes a band
function: food has three bands, cocktails four. Read its own comment before
merging anything else — the predicates are answered in different vocabularies
and were never the same question.

**FUZZY TO FIND, FUZZY TO INCLUDE, EXACT-OR-DECLARED-FAMILY TO EXCLUDE.** Food's
rule, adopted here, and the asymmetry is the cost of being wrong in each
direction: over-including shows you a drink and the card says why; over-excluding
hides one and you never learn it existed. Before this, BOTH directions were a
substring test against the joined attribute — `gin` hid twelve drinks whose only
gin-shaped ingredient was ginger, `apple juice` matched fifteen with PINEapple.

**FOUR BANDS, IN HELEN'S ORDER.** *"It should be prefix matching of first word,
prefix matching of any word, then prefix matching of any word in the bottle name,
then substring."* Visible beats hidden at equal strength; any real word beats a
substring. Band 3 exists only because a bottle stopped being its own chip.

**A CHIP MUST BE ABLE TO EXPLAIN ITSELF**, and this took five passes over three
sessions. Helen: *"'el' returns both 'aged rum' and 'jamaican rum', which is
counterintuitive."* Neither label contains "el" — it was mid-word inside
"moderat(el)y" and "caram(el)-forward". Banning band 3 on hidden terms was not
enough: sweeping all 676 two-letter queries still found 25 chips that could not
explain themselves, band 2 on a CONNECTOR (`an` → `Smith & Cross`, via "Smith
AND Cross"). **The sweep is the technique worth keeping** — it is only possible
because the module is pure, and each time the obvious fix was not the whole fix.

**THE CONNECTOR HALF IS NARROWER THAN IT READS, and this paragraph claimed
otherwise for two days.** The check refuses a hidden match only when the matched
WORD is itself in the prose list — so `an` was stopped by `an` being a prose
word, and nothing about "and" was ever involved. `and` is deliberately absent
from that list, because `Wray and Nephew` is one bottle, so it still reaches a
category through an alias. Two things make that harmless rather than a hole:
`min_query_chars` is 3, so `an` cannot be typed at all, and a band-3 chip now
prints the name that found it.

**AND THAT IS THE ANSWER THAT FINALLY HELD — #603, 2026-08-31.** Helen typed
three letters three times and got three chips that could not say why they were
there: `mu` → `clear blended rum` (inside "clear blended MUlti-region rum"),
`sa` → `cachaça` (the bottle Sagatiba), `wr` → `Jamaican overproof rum`. All
three were band 3 working exactly as designed — the rule that makes "velvet"
reach `falernum`. Four candidates were built side by side on a dev page and she
picked: **a chip found through a name it does not show carries that name.**

Three shapes, one rule — show the name that answers the question:

| matched on | the chip reads |
|---|---|
| its own name | the chip, nothing added |
| a name CONTAINING the chip's | that name alone — `clear blended multi-region rum` |
| a genuinely other name | the chip plus a bracket — `cachaça (Sagatiba)` |

The middle row is a principle, not a one-off: **15 of the 27 card names are
strict abbreviations of their own generic**, so a bracket in all fifteen would
print the chip to itself and append the bit the card name dropped
(`gin (London dry gin)`). **The chip's VALUE never moves** — only the label —
because an annotation folded into the value would become part of the filter and
match nothing.

**The bracket shows whichever spelling carries the query.** Canonicalising it
was right until it was not: "and" matches the alias `Wray and Nephew` and
printing the canonical `Wray & Nephew` gave a bracket with none of the typed
letters in it — #603 arriving through its own fix.

**A MULTI-WORD QUERY MATCHES A HIDDEN NAME FROM ITS START**, Helen 2026-08-31:
*"I do want to be able to type 'el d' and see el dorado."* `hasWordMatch` asks
whether one WORD begins with the whole query, so it is never true of a query
containing a space — typing a bottle's real name found nothing at all. A match
at position 0 is at a word boundary by definition, so it cannot be the mid-word
accident band 3 was narrowed for.

**AN UMBRELLA SUPPRESSES ITS OWN BARE WORD — #51's rule, ported here
2026-08-31.** `gin (all)` takes `gin` off the list beside it and leaves `sloe
gin`, `navy strength gin` and every ginger entry. Helen was sure this was
already a food rule and was told it was not, on a measurement that called
`ingredient-search.js` directly — **the suppression is in `filters.js`, at
render time**, so the check exercised the layer that does not implement the rule
and reported its absence as a fact. **A measurement is only evidence about the
layer it ran through.** Cocktails keeps the rule in the pure module rather than
the wiring, on the same day the wiring shipped a startup crash no pure test
could see.

**ONE CHIP PER CATEGORY, WEARING THE CARD'S NAME.** Fifteen generics also had
their card name in the pool as a chip of its own and eleven of those pairs
selected identical drinks. The generic stays searchable; only the button goes.
The three declared collisions collapse with it — one `sugar syrup` chip covering
both ratios, which is §9.10.1's "a ratio is a MAKING fact" arriving in the picker.

**A BOTTLE IS A WAY IN TO ITS CATEGORY, NOT A CHIP BESIDE IT.** Measured before
deciding: 14 of the 15 bottle/category pairs are strictly nested, so the two
chips were never alternatives. Typing "velvet" or "portobello" returns
`falernum` and `gin`. **This needs the pool built PER INGREDIENT** — a
suggestion belongs to the generic written beside it and the card-level
`data-ingredients` has flattened that away, so `data-ing` is the only attribute
that still knows.

**THE PICKER WAITS FOR THREE CHARACTERS — #584, 2026-08-31.** It was 2, which
was what the page did before the search became a module, and the numbers settled
it: at two characters **31% of queries overflow the cap of 8**, so the answer is
eight arbitrary chips and "+21 more — keep typing"; at three it is 3%, median 2.
Four buys 2% for a keystroke on every search. **Food keeps no minimum at all**
and that is not an inconsistency to tidy: its picker sits above a list that
stays on screen, so a wide pool is noise BESIDE the answer, where this one
replaces the whole result area. One line in `ingredients.yml`; no code.

**The first measurement of it was taken with the new minimum already live**, so
the two-character row reported a tidy zero candidates — a check measuring its
own change, and it read as a clean result. Lift the thing under test before
measuring it.

**PROSE IS NOT A BOTTLE NAME**, and it is a rule rather than a list because
Helen met four one at a time. `search.prose_words` / `prose_marks`, measured
against all 87 suggestions before being trusted: flags 17, catches no bottle
name. `and` is deliberately absent — `Wray and Nephew` is one bottle.

**`family_aliases` and `family_labels`.** A family nobody spells that way is a
family nobody can reach: `whiskey` found nothing while the family held bourbon
and rye. The button always carries the canonical name, and `whisky` is labelled
`whisk(e)y` — Helen: *"even though it's clunky, to avoid ever having to split or
claim they combine."*

**`not_on_cards`** keeps bare `water` off a card and out of the search (#580).
Exact matches only: `honey water` and `soda water` are real choosing facts.


### 9.4 Decided 2026-08-16 — do not re-litigate

- **Ingredients are additive, never a choose-one.** The Sazerac really does
  take cognac AND rye AND bourbon; it is not offering three bases. So a flat
  list is enough, and the schema needs no "one of these" grouping. This was
  asked directly because guessing wrong would have shaped the whole model.
- **Store the quantity both ways** (as-written string plus numeric ml),
  rather than canonicalising to ml or keeping free text only.
- **`to_serve` is presentation, not steps** — "over crushed ice, with a
  straw". Finishing ACTIONS ("top with champagne", "squeeze the twist over
  the drink") are method steps. The CSV's `Serve` column holds actions, so
  its contents move into `method` on ingest.

  **LIVE SINCE 2026-08-26, AND EMPTY ON EVERY DRINK BEFORE THAT.** This bullet
  used to end "none of the first three drinks has a real `to_serve`" — true,
  and it stayed true for all 115: not one drink set the field until #291's
  three fragments moved into it (Caipirinha "Stirrer.", Mastiha Mojito
  "Straw.", Gin Sour "Without ice."). Check `_layouts/cocktail.html` renders
  it before moving anything else in — it does, but a field documented for ten
  days and used by nothing is exactly the kind that turns out not to.
  `test_to_serve_is_a_string` now guards the shape, which nothing did while
  there was no data: a list would NOT fail loudly, because the layout pipes it
  through `markdownify`, which stringifies rather than raises.

  **SEVEN DRINKS USE IT NOW, and #573 was the other half of the same fact.**
  While three drinks said `to_serve: "Straw."`, four others wrote the identical
  thing into `method` as "Serve with a straw." — one fact in two fields, decided
  per drink by whichever session last touched it. The four moved; the wording
  follows the terse noun phrase the original three already used, because the
  field name supplies the verb.

  **`test_no_method_step_restates_to_serve_or_garnish` keys on the VERB**, and
  that is the whole rule rather than a judgement per step. Two more steps
  restated `garnish:` outright and were deleted. But a step that DOES something
  to a garnish stays: "Float the dehydrated lime slice wheel" and "Express lemon
  zest twist" both name a garnish and both instruct. Word-matching cannot tell
  those apart; the leading verb can.
- **Both brand and generic** are stored per ingredient.

### 9.4.1 The site is canon. Deviation happens in the kitchen.

**Helen, 2026-08-17, and it settles a whole class of questions rather than
one:** "With iPad in hand, I'd rather take the site as canon, then happily
break rules from there."

So a cocktail page states ONE figure. It does not model the fact that she
sweetens to taste, that she "often like[s] different amounts of sugar
depending on the weather", or that "some friends have a sweeter tooth than
others". All of that is true and none of it belongs in the data.

**This came up as a real proposal and was declined.** The sugar-syrup ratios
are only stated on 2 of 27 entries, and the obvious response is to model
adjustability — a range, a tolerance, an "approximate" flag. Her answer is
that the page is the reference she deviates FROM, and a page that hedges is
no longer a reference. Do not reintroduce it.

**The generalisation, which is the useful part:** when a figure in this
collection looks imprecise, the question is not "how do we capture the
imprecision" but "what single figure is the right thing to print". A drink
whose sugar is genuinely undecided gets a `QQ`, not a range.

This is also why the syrup-to-citrus ratio (§9.5) can only ever FLAG, never
classify — the variation it detects is often Helen adjusting a drink on
purpose, which is indistinguishable from a transcription error by volume
alone. See the note there.

### 9.5 Settled apparatus — was "Open, and worth deciding out loud"

**RETITLED 2026-08-31 because nothing in it was open any more.** Every bullet
had become a settled fact, and a section promising open questions to a reader
looking for them is worse than no section. Where an item grew a data file of its
own it now lives beside that file instead.

- ~~**`garnish: []` versus stating "none".**~~ **CLOSED — §9.12.1**, which is
  where `garnish.yml` and its rules are. `["no garnish"]` means DECIDED, `[]`
  means unfilled; the marker is spelled `no garnish`, not `none`, since
  2026-08-31.
- **`meta.ship` is an ordered, tested vocabulary** — `ship_scale` in
  `_data/cocktails/taxonomy.yml`: `not really` < `meh` < `sure` < `yes` <
  `oh gods yes`, with `who knows` and `QQ` deliberately OFF the scale (see the
  file's own comment). `meta.status` is retired entirely; its only consumer
  anywhere was `chaos`'s `haven't tried` bucket, and an untried drink never
  publishes. §9.9 is where this vocabulary turned into a feature.
- **`tests/test_cocktails.py` is the cocktails suite** — glasses, generics,
  bottles, moods, methods, garnishes, the `measures:` amount table.
  `tests/conftest.py`
  is explicitly the FOOD suite; this module carries its own fixtures and its own
  `cocktails` marker. A cocktails test must ASSERT its corpus is non-empty
  rather than skipping mid-run, or it passes vacuously.

  **That requirement did not protect the collection where it mattered most, and
  #540 is now half-answered.** The module used to skip wholesale when
  `_cocktail_drafts/` was absent — always the case in CI — so 24 of its tests
  never ran on `main`. Since 2026-08-29 the corpus is `_cocktail_recipes/` +
  `_cocktail_drafts/`, so a PROMOTED drink is checked everywhere including CI,
  and `_load()` is the only door into either. The drafts remain a local
  concern by Helen's decision. **Read the box in §10 before relying on a green
  cocktails run**: with nothing promoted yet, CI still checks no drink, and the
  difference is only that this is now a fact about the collection rather than
  about the loader.

### 9.7 Two traps this layout hit on its first day

- **Liquid parses tag delimiters INSIDE a `comment` block.** Quoting an
  if-tag in an explanatory comment is a build-breaking syntax error, not
  documentation. `_layouts/recipe.html` already knew this and says so;
  `cocktail.html` learned it the hard way. Describe the bad pattern in prose.
- **An empty string is truthy, not just an empty array.** Every list-gated
  section here tests `.size > 0`, which is the well-known half — but
  `source: ""` is truthy too, and gating the footer on the bare value drew a
  "Source:" line with nothing after it on all three drinks.

### 9.8 What cocktails borrows, and the tape

One deliberate borrowing: cocktails shares food's two font stacks. Colour and
decoration are what separate the sites; typography is the family resemblance.

**The tape is no longer cocktails' business at all, and neither is the
footer.** Both are shared chrome as of 2026-08-19 (§2.5): one directory,
`assets/img/chrome/`, for the whole repo, and `_layouts/default.html` draws
the same wordmark tape on every page in either site.

This section used to set out a standing PARITY rule. `assets/img/cocktails/
tape/` held a copy of food's seven files, and "regenerate food's set and copy
it across in the same pass" was the instruction — written after the two
directories drifted for five days with nothing but a note in this document
watching (issue #223). **That rule is retired, and so is the chore.** One
directory cannot drift from itself.

The consequence for a future cocktails visual language is worth stating
plainly, because it is a bigger decision than it was: giving cocktails its own
tape now means giving it its own *header*, which is the thing #374 exists to
prevent. Argue it out rather than adding a directory. See §13.9 for the
generator, §13.8 for the sizing mechanism, and the note at the top of
`_sass/cocktails/_decoration.scss` for the same context in code.

---

### 9.9 `meta.ship` IS the rating, and the vocabulary outlived the feature

**CUT 2026-08-29.** This section described a goodness-only filter built in
twenty minutes on 2026-08-23, which §9.13's designed index replaced three days
later (`_sass/cocktails/_goodness.scss` is deleted). The UI description was
already flagged superseded and is now gone; three lessons survive it, and the
first is the one that made the replacement cheap.

**Look for the vocabulary before inventing one.** `meta.ship` already held
Helen's own verdict in her own words — "oh gods yes" was on 18 drinks before
anyone asked for a rating. The whole feature was a template and a stylesheet: no
new field, no migration, nothing for her to fill in. A scale designed from
scratch would have been worse AND needed 115 decisions from her. `ship_scale` in
`_data/cocktails/taxonomy.yml` is the order; `who knows` and `QQ` sit off it
deliberately (see the file's own comment).

**A HARDCODED VALUE LIST AND THE VOCABULARY IT ENUMERATES WILL DRIFT, AND THE
BREAK IS SILENT.** That template hardcoded its own ordering string, and the
`meh` collapse landed in a *different, still-unmerged* PR the same day. Nothing
would have crashed — an unlisted value "just sorts last" by design — so 17
drinks, the biggest bucket after yes/QQ/oh-gods-yes, would have sorted dead last
the moment both PRs merged. **Neither branch's own tests could have caught it,
because each was green in isolation**; it took rebuilding the combined state of
both locally. The new index derives its buckets and tint from `taxonomy.yml`
instead, which is the enforcement version of this paragraph.

**The index reads DRAFTS, not recipes.** `_cocktail_recipes/` is still empty and
every drink is a draft, so the index before this one looped
`site.cocktail_recipes` — an empty collection — and had done since it was
written. (The draft count moves with every ingest; count them rather than
quoting a figure from here.)


### 9.10 The drink page's ingredient line — #544/#513, 2026-08-29

**The line is the GENERIC, with the bottle in brackets.** Helen's own worked
example: `London dry gin (Beefeater)`. Then `character` on its own quiet line,
then `note`.

    45 ml   London dry gin (Tanqueray)
    15 ml   moderately aged rum (Gosling's Black Seal)
              character: blackstrap
    30 ml   coconut rum (Malibu)
    22.5 ml lime juice

**`item` DOES NOT RENDER, and that is the whole fix.** The page used to show
`item` as the headline with `generic` beneath it, which meant printing the
source's words and the vocabulary on top of each other. Measured across all 617
entries, **385 of those pairs restated one another** — 241 where the item
contains its generic, 124 differing only by case, 20 identical. `Malibu /
Malibu` was #513 in two words, and `fresh lime juice / lime juice` was Helen's
own complaint. Removing the field makes the duplication IMPOSSIBLE rather than
suppressed, which is why #513 closed here rather than acquiring a rule about
when to hide the second line.

**It only became readable after #561.** The same change a week earlier would
have produced `moderately aged (Gosling's Black Seal)` and `London dry
(Tanqueray)`. **A card name may be lossy; a recipe line may not.** Ten generics
had to gain their spirit word first — see §9.3.1.

**`character` gets a LINE now, not a parenthetical, and that is a deliberate
revision of #441.** That issue banned the bare form because "moderately aged rum
(blackstrap)" reads as a TYPE of moderately-aged rum, real confusion with black
rum; it folded onto the class line instead. The class line no longer exists, and
a LABELLED line of its own carries none of that risk. The rule is still
`.cocktail-type-line` — kept rather than renamed, because its position, indent
and quiet tone are all still right for what sits there.

**`.cocktail-suggestion` is quieter than the class it follows**, deliberately:
the class is what the drink REQUIRES, the bottle is what Helen happens to reach
for. It must not read as though an entry without one were missing something —
though that argument has weakened: #544 promoted 61 bottles out of `item` on
2026-08-30 and coverage went from 18% of entries to 29%.

**`generic`/`suggestion` can be a string or a list**, and Liquid's `for` quietly
treats a bare string as a one-item sequence — checked against the real `liquid`
gem, not assumed. One loop handles both shapes with no type-detection. A list
`generic` joins with a quiet italic "or": it means "either would do" (#441),
never "and".

**`optional: true` is the field the two `(optional)`s used to hide inside
`item`** — #570, and it renders as a plain word after the name rather than a
parenthetical, because the brackets on that line already mean "the bottle".
It is NOT food's `incidental`, despite the matching shape: that one HIDES a
line, this one shows it and marks it.

**The rest of `item`'s redistribution is #544 move 2 and is most of the way
done — see §9.3 for what has gone and what is left.**

### 9.10.1 Cards and search read the VOCABULARY, never the transcription — #501/#544/#558

**The card used to render `item`, and the problem was not that the words were
long. It was that they were ambiguous.** Eight item strings in the collection
each name two or three *different* rums:

| the card said | the drink actually wanted |
|---|---|
| `Overproof Navy rum` | Demerara aged · Jamaican moderately aged · Planteray O.F.T.D. |
| `Light aged rum` | Demerara aged · blended multi-region clear · lightly aged and filtered |
| `Demerara rum` | Demerara aged · Demerara overproof |
| `White rum` | agricole unaged · lightly aged and filtered |
| `Gold rum`, `Navy rum`, `Light rum`, `Lightly aged rum` | two each |

So the colour vocabulary #314 retired was not merely unfashionable on the
index — it was the one thing on the card a reader could not rely on, and the
`generic` beside it was the only correct name available. #501 read as a
length problem ("the real category name is obviously too long") and the
measurement said otherwise; **it was a correctness problem that happened to
also cost room.**

**`card_names` in `ingredients.yml`** maps a generic to its card name.
The rule in `cocktails/index.html` is "substitute when every generic on the
entry has a card name, else fall back to `item`" — the all-or-nothing half
matters because a list `generic` means "either would do" (#441) and ten rum
entries carry one; a mixed list would otherwise print half a fact.

**The map is not rum-only and is not named as if it were** — renamed to
`card_names` on 2026-08-29. Ceylon arrack was its first non-rum member; Helen:
"is that a rum? Doesn't matter, the category list should eventually contain
everything." It has no `family` and must not get one (coconut flower sap;
`family_less` carries the reason), which is exactly why its card would otherwise
fall back to raw item text. A card name must still be a DECLARED generic — the
typo case — but deliberate widening no longer fails.

**Helen's call, asked with `El Dorado 12 year old rum` → `Demerara rum` in
front of her: category ALWAYS, including where the recipe names a real
bottle.** 43 of 91 rum entries do name one. The alternative — bottle where
known, category where vague — needs a mechanical "is this a bottle" test on
the string, which is exactly the fragile rule #513 objects to, and it would
have made the card's rum word mean two different kinds of thing depending on
a drink you cannot see. The bottle is still the drink page's headline.

**Her names say the spirit word out loud**, which reversed two of the drafting
assumptions: `filtered rum` became `lightly aged rum`, `clear blend` became
`clear blended rum`, and both overproofs gained a trailing "rum". Two names
are consequently LONGER than the generic they abbreviate. A first version of
the test asserted a card name is never longer than its generic — obvious,
and wrong within a day. **Brevity was the means; legibility was the point.**

**The measured claim, and what guards it.** 39 rum cards shorter, 4 unchanged,
19 longer, median −8; the collection's median card line 98 → 94. The 19 are
almost all the nine cards carrying a disjunctive rum, which is where the
category does the MOST work — `White rum` concealing a choice between a
filtered rum and an agricole blanc. So the guard is aggregate
(`test_showing_categories_still_shortens_the_index`), not per-card: a per-card
rule would have failed the feature's best cases.

**A collapse is permitted but must be declared.** Helen collapsed both
Jamaicans to `Jamaican rum`, on the principle that the funk is the shared
trait and caramel is a nuance of the same rum, where both Demeraras and both
agricoles keep their own names because proof and age change what you are
making. `card_names_may_collide` carries the reason — the `family_less`
idiom — and an *undeclared* duplicate still fails, because two rums reading
alike is the precise fault this map removed.

**The highlight had to move with it**, and this is the transferable half.
`cocktail-index.js` lit a matched ingredient by reading the span's rendered
text, which was fine while the card printed the item. Now a card found by
typing "El Dorado" prints no such words, so it would have survived the filter
with nothing lit — unable to say why it was there, which §9.13 makes the
card's job. It reads a build-time `data-ing` attribute instead. **Whenever a
template stops rendering the string a script was matching on, the script is
already broken and nothing about the page looks wrong.**

**A disjunctive pair sharing a head word gets an EXPLICIT replacement, not a
rule.** `card_name_joins` is keyed on the default join, so the before and
after read together: Swizzle's `Demerara overproof rum or Demerara rum` is
Helen's `Demerara rum or overproof`. Her form drops two words from the second
option and reorders the pair, which is why it is stored — she expects more
cases and named the shape herself: "I expect we'll need an explicit mapping of
cases like this." Six of the seven pairs need nothing.
`test_every_card_name_join_is_reachable` keeps the keys honest, the bargain
`methods.yml`'s proposals strike.

**Two pours of the same rum is a DIFFERENT case and needs nothing.** Each
ingredient entry renders its own card name, so a drink genuinely wanting two
Demeraras prints the name twice, correctly — Helen: "where a recipe wants more
than one kind of the same rum we obviously should write the display name
twice." The first version of the duplicate test forbade any repeat on a card
and would have failed a correct drink the day one was written. It now fires
only when two DIFFERENT generics arrive at one name, which is #501's original
fault rebuilt inside the fix for it.

**`character` is recipe-only.** Helen, 2026-08-27, asked directly about
blackstrap on a card: "character only on the recipe." So Don's Own Grog's
Gosling's reads `aged rum` on the index and carries `(character: blackstrap)`
on the drink page, and that is settled rather than parked. #530 is the
follow-on she asked for: note `character: hogo` on the drinks that want a
bottle for it, which needs `hogo` adding to `rum_characters` first or
`test_rum_character_is_declared` goes red.

**Card names are not rum-only and the maps are no longer named as if they
were** — `card_names`, `card_name_joins`, `card_names_may_collide` since
2026-08-29. Gin, whisky and the syrups have entries; Ceylon arrack was the first
non-rum member.

**Helen's model, given as six worked examples rather than a rule: the card shows
the shortest name that tells you what the drink is LIKE.** Not the family, not
the style, but whichever of those matters — `gin`, because London dry versus
Plymouth does not change your evening; `bourbon` and `blanco tequila`, because
bourbon versus rye and blanco versus añejo do. That is the same judgement the
rum names already encoded, so rum was never a special case, only the first
place it hurt.

**No brand appears on a card any more.** The three brand-generics #314 permits
because nothing generalises the bottle -- Planteray O.F.T.D., Stiggins' Fancy,
Malibu -- now carry DESCRIPTIVE card names: `blended overproof`, `pineapple
rum`, `coconut rum`. That ruling is untouched; only the label changed, which is
what card names are for. They were the only three brands on any card, so a
reader met `O.F.T.D.` among `gin`, `cognac` and `sugar syrup` and learned
nothing (#556 exactly). **Lowercasing is what surfaced it** -- `o.f.t.d.` reads
badly in a way the capitalised form hid. Two of the three got LONGER; this buys
legibility, not width.

**Adding an entry changes what cards show with NO template edit**, because the
template only ever looks a generic up in the map. That is worth knowing: card
display is a data-layer change, which is how gin and syrup cards landed while
another agent had `cocktails/index.html` open.

**The card falls back to the GENERIC, never to `item` — #544 move 1, and it is
what made the card line honest.** Sazerac went from `La Fée Parisienne absinthe
· chilled water · Camus VSOP cognac · straight bottled-in-bond rye whiskey · …`
to `absinthe · water · cognac · rye · bourbon · sugar syrup · …`. The
all-or-nothing rule for a disjunctive generic DISSOLVED rather than being
maintained: it existed so a mixed list could not print half a fact, and with a
per-option fallback there is no half fact left to print.

**The search pool dropped `item` too — #558.** It is `generic + card name +
suggestion`, built at build time. 380 terms → 239; typing "li" offers 23 options
instead of 63. **This was never a search bug**: Helen's nine "light…" options
were nine `item` strings for what is mostly one rum, which is #544 seen from the
other end.

**The alias gap this paragraph used to describe is CLOSED, 2026-08-30.** It read
"suggestions go in raw rather than resolved through `bottles.yml`'s aliases, so
`Havana 3` and `Havana Club 3` can both appear" — the search reads that file
now, so they collapse. 240 pool terms → 142, because a bottle is no longer
offered a chip at all when its category is; see §9.3.3.

**IT WAS TRUE OF CHIPS ONLY, and the other half closed 2026-08-31.** A bottle
sitting beside a generic never became a chip, so it never went through that
resolution: 14 alias spellings were searched as themselves, and 14 prose strings
`bottles.yml` calls unusable were searchable too — printable, once #603 started
rendering the name that matched. Hidden terms go through the same door now.
**The canonical name JOINS the terms rather than replacing them**, because `ED3`
shares not one letter with `El Dorado 3` and collapsing would delete a way in
that works.

**Two declared collapses that lose information ON PURPOSE**: both syrup ratios
read `sugar syrup` on a card, both honey ratios read `honey water`. Helen: "On
the card I would expect to see sugar syrup, and on the recipe ingredient line
cane sugar syrup, 2:1." **A ratio is a MAKING fact, not a CHOOSING fact** — at
card distance it is not being used. Checked before declaring: no drink carries
both ratios of the same syrup.

**Cards are lowercased in CSS, not in the markup** (`text-transform` on
`.drink-card-ingredients`, #543/#553). The DOM keeps its capitals, so
copy-paste, screen readers and the drink page are untouched — and the drink page
needs them, since a recipe line reads `London dry gin (Beefeater)`. Worth
re-looking at: when Helen asked, cards rendered `item` and the line really was a
jumble; they now render vocabulary, and the 37 surviving capitals were all real
proper nouns before this rule lowercased them too.

**A CARD NAME MAY BE LOSSY; A RECIPE LINE MAY NOT** — the rule that survives
this, and #561 is what made the drink page possible. Ten generics were named
after production traits rather than after the drink they make, so #544's
ingredient line would have read `moderately aged (Gosling's Black Seal)` until
they were renamed. They were; the drink page followed; #513 closed with it.

The bottle side of all this is §9.3.2.

### 9.11 Glass icons — real relative height, and a UA-stylesheet trap

**Sized by real height, not a common rendered height, since 2026-08-25
(#298).** `_layouts/cocktail.html` computes `--glass-icon-height` per drink
from `_data/cocktails/glasses.yml`'s `heights_mm` against the tallest real
glass (counted live every render, not hardcoded), and
`_sass/cocktails/_cocktail.scss` consumes it with a fallback for a glass with
no entry. **The scale was 2.6rem and is 10.4rem since 2026-08-26**, when the
glass stopped being an icon beside a title and became the drink page's hero;
the width cap moved with it in the same proportion (3.2 : 2.6 became 12.8 :
10.4) rather than being re-guessed, since its job — stopping a punch bowl
shouldering the title along — is unchanged. **The card is a different
calculation, not the same one at another scale** — its own curve and its own
headroom, both in §9.13 — and it alone applies `display_scale`, which is empty
today. `_dev/glasses.html`'s section 2 proved the calculation
out before it reached the real page; section 1 is now the honest "as the
site actually shows it" view, height AND the real 3.2rem width cap together
— it was quietly stale for a day, still claiming "every icon is the same
height here" after #298 shipped, a live instance of §11.2.

> #### FILL-ONLY ARTWORK: ASK "MUST THIS BE REDRAWN" BEFORE "CAN THIS BE TRACED"
>
> **2026-08-31, and it is a mistake to learn from rather than a mechanism.**
> Stock and hand-made glass artwork very often arrives fill-only — the ink is a
> filled compound path with `stroke: none`, so there is no centreline to give a
> stroke width to. Two ways to publish it, and the repo has both:
>
> - **`glass-icon-solid`** (`_sass/cocktails/_cocktail.scss`) fills with
>   `currentColor`. The drawing is exactly what was drawn. It reads HEAVIER,
>   and its ink scales WITH the icon where `non-scaling-stroke` holds the rest
>   of the set at a constant screen weight.
> - **`scripts/trace_centrelines.py`** derives real centrelines so the drawing
>   joins the stroked set. **Tracing is a redraw**, and it is lossy: on Helen's
>   three it broke lines at junctions and lost the pineapple's umbrella stem,
>   and retracing finer recovered neither (#355's stated cost).
>
> **Two different questions decide it, and a drawing can fail both.** Whether
> the ink is UNIFORM WIDTH decides whether tracing is *valid* — measure it, do
> not eyeball it: a distance transform read along the skeleton is tight for a
> constant-width stroke (pineapple 1.27×, coconut 1.33×) and long-tailed for one
> with solid regions (the tiki mug, 2.92×). Ink width as a fraction of canvas
> height decides whether filling is *bearable* — against a stroked icon's ~0.65%
> at card size, the three ran 1.3%, 2.5% and 4.2%.
>
> **All three were traced first and Helen stopped it:** *"you redrew these three
> new ones, right? They're not right."* She was correct twice over — a fill
> renders fine and is only heavier, so the transformation bought nothing she had
> asked for. They are published solid. Weight is a thing to LOOK at, never a
> reason to transform someone's artwork unasked.
>
> **Ink can be thinned without touching a path**: an `<feMorphology
> operator="erode">` filter shrinks the painted region at render time, and the
> radius is one attribute that returns to 0. The three carry one (tiki 1.20,
> pineapple 0.25, coconut 0.35 — interim, Helen is redrawing them). Not a
> background-coloured stroke, which does the same job while hardcoding whatever
> sits behind the icon.

> #### OPEN STROKE ENDS: THE SITE DRAWS 4–6× THINNER THAN HELEN EDITS
>
> **2026-08-31, nine glasses, and it is a class rather than an incident.** Her
> sources carry `stroke-width` ~2.8 user units and a round cap bridges one
> stroke width, so a 1-unit gap between two line ends is **invisible while
> drawing**. The published icons use `vector-effect: non-scaling-stroke` — a
> fixed number of SCREEN pixels — which works out at 0.35–0.66 user units. **Any
> gap between about 0.7 and 2.8 units is hidden at edit time and open on the
> page.**
>
> Helen diagnosed it unprompted and exactly: *"I assume this is because you're
> drawing them with a different stroke width than when I edited the files,
> meaning my lines didn't quite go far enough."* She then closed 25 of the 27
> open ends across eight glasses in an afternoon.
>
> **Measure ends against STROKES, not against other ends.** The goblet's
> endpoints all met within 0.26 units; its one fault was a line stopping 1.56
> units short of the MIDDLE of another line. An end-to-end scan reports it clean.
>
> **A wand was built and is not good enough** (`git log -S wand`): appending a
> stub along each short stroke's own tangent closed 4 of 6 on the coupe, refused
> 2 where the tangent was 90° off the join, and left 3 open. Hand-editing wins.
>
> **A gap is not automatically a fault.** `old-fashioned-double` carries the
> set's two largest (3.92 units each) and Helen ruled it correct as drawn.
> **There is deliberately no guard** — her call, 2026-08-31: the set will be
> replaced wholesale if it changes at all, so a per-drawing check protects
> against something that would bypass it anyway.

**The width cap matters as much as the height, and can make a correctly-sized
glass look wrong without it.** Helen, 2026-08-26, on `_dev/glasses.html`
section 2 (which has no width cap): goblet and mule-mug (renamed `mug`
2026-08-26, see below) both looked
oversized. Mule-mug's own drawing is wider than tall (1.25:1 viewBox); at
section 2's uncapped 9rem scale its natural width would be ~5.1rem, half
again over the real site's 3.2rem cap — a size it never actually reaches at
the real 2.6rem scale. Some of what looks like a bad proportion on an
uncapped comparison page is really just that page choosing not to show the
constraint the real site always applies.

**`heights_mm` is unmeasured, and it shows.** Its own comment already said
so ("typical values... pending issue #295"); #295 is still open. A capacity
(volume) based scaling was floated as an alternative and shelved for the
identical reason — no real numbers exist for either axis yet, so it would
trade one set of guesses for another, not fix anything.

**Stem/base proportions genuinely differ glass to glass** — confirmed by
screenshot, martini vs. goblet, each hand-drawn with its own stem length and
base-flare ratio. Real vector work to fix (pick one drawing as canonical,
adapt it to each glass's own bowl width across ~7 stemmed glasses), not a
data or CSS change. **Deliberately parked, 2026-08-26** — Helen: "these
graphics are the thing on the site that the least serves function over
form... let's leave things as they are." Logged on #299 so it isn't
rediscovered from scratch later.

**The four-tumbler-icon problem (#347) is resolved, differently than any of
the three ways originally floated.** `old-fashioned.svg`, `rocks.svg`,
`rocks-tall.svg` and the old `old-fashioned-double.svg` all got replaced by
one fresh redraw; `rocks` is now a plain alias to `old-fashioned` rather than
its own drawing. The double variant followed on 2026-08-26 —
`old-fashioned-double.svg` redrawn as the same body, uniformly scaled up —
and `double rocks`/`double old fashioned`/`double old-fashioned` are mapped
to it now, so Fancy-Free, Vieux Carré and Ti Punch render an icon again
(verified against a build). Full story is in `glasses.yml`'s own retirement
note — treat that file as more current than this paragraph if they disagree.

**A root `<svg>` element defaults to `overflow: hidden` in every browser's
own UA stylesheet — not a CSS property default, a default for that specific
element.** Found 2026-08-26: a stroke whose rounded join or cap sits right on
the viewBox edge (a glass belly, a stemmed glass's top corners) was getting
silently sheared off, on the real site as well as the dev page — `.dev-strip`
and `.dev-card-big` on `_dev/glasses.html` had it too, it just took a
side-by-side comparison to notice. Fixed with an explicit
`overflow: visible` everywhere an icon renders (`.cocktail-glass-icon` in
`_cocktail.scss`, so every real cocktail page, plus the dev page's own
scale/card rules). Worth remembering generally: an inline `<svg>` clips its
own content by default, the same way `overflow: hidden` on any other element
would, and it is not obvious from reading the SVG or the surrounding layout
CSS that this is happening — only from a stroke that touches the edge.

**Helen's raw Inkscape sources are backed up in git now, at
`_design_sources/cocktails/glasses/`, committed as-is.** Before this they only
existed in `tmp/inbox-cocktail-glasses/`, which is gitignored — every
normalised production icon was tracked, but the drawings behind them had no
backup at all. Underscore-prefixed on purpose, the same reason `_includes`/
`_data`/`_sass` are excluded from the build by default; it is not `assets/`
because that directory IS copied into `_site/`, and a folder of un-served
Inkscape XML with full editor metadata has no business in the deployed site.
Nothing reads this directory and nothing should point a template at a file in
it — nor is it kept in sync automatically: when a drawing here gets adopted,
normalising it into `_includes/icons/glasses/` is still a manual step. It also
holds superseded options and rejects (old candidate old-fashioneds, the
pre-fix collins/coupe), not the current state of any one glass — that's what
`glasses.yml` is for.

**Two of the "genuinely differ" stemmed glasses got redrawn anyway, 2026-08-26,
despite the proportion PASS staying parked.** Goblet and nick-and-nora both
have new bowl proportions from Helen — goblet narrower and shorter
(viewBox 68.5×90.5 → 54.4×82.2), nick-and-nora wider (37.3×91.0 → 44.9×90.7).
This is not #299 reopening: it's Helen fixing individual drawings she wasn't
happy with, same as the old-fashioned/collins/coupe redraws earlier in this
same arc, and #299's own systematic "make every stem/base consistent" pass is
still exactly as parked as the paragraph above says. Worth noting because
goblet was one of the two examples that paragraph names — if a proportion
complaint about goblet specifically resurfaces, check whether this redraw
already addressed it before assuming #299 needs unparking.

**`mule-mug.svg` is `mug.svg` now, 2026-08-26, and no new drawing was needed.**
Apple and Ginger Mulled Wine's glass was the bare word `mug`, which
`glasses.yml` had flagged QQ between `mule mug` and `hot toddy`. Helen, asked
whether to draw a third: "I actually use a mug for this like I do for tea!" —
and the mule mug's drawing already IS a plain tapered mug with a handle. The
only thing that ever made it a *Moscow Mule's* is that a real one is copper,
which a monochrome line icon cannot say. It had no drink using it, so the
rename cost nothing; `mule mug` stays as an alias for the Mule that will want
it one day. `hot-toddy` was considered and rejected — that drawing is a footed
handled glass, not a mug.

**The load-bearing half was the SCRIPT, not the `git mv`.**
`scripts/normalise_glass_icons.py` regenerates icons wholesale from
`tmp/cocktail-glasses/`, so renaming only the published file would have
resurrected `mule-mug.svg` on the next run and taken `mug.svg` with it. The
pair went into that script's existing `RENAME` map, beside `pineapple-3`.
**Generalise this**: any rename under `_includes/icons/glasses/` is two edits,
and the filesystem one is the one that does not stick.

**All three of `glasses.yml`'s own QQ glasses were resolved the same day** —
`todo` (Coney Park Swizzle) and `long` (Long Island Iced Tea) both turned out
to be placeholder words rather than glasses, and both became `highball`. Helen
moved every swizzle onto highball at once. `any` is now the ONLY deliberately
unmapped value, and that changes the safety of the old default: "absent means
no icon" was sound while three real gaps existed, but an unmapped glass is now
far likelier to be a typo than a decision. #500 tracks the flag-only test.

### 9.11.1 The canonical glass vocabulary is a RULE now, not a preference

**2026-08-26, and it reverses what `glasses.yml` said for nine days.** That
file stated outright that "the aliases above stay live regardless: the point of
this file is that a drink is never wrong for using the other word." Helen: "I
decided to go with old fashioned rather than rocks as the canonical name, so
recipes that still have rocks are fine to break a test."

So there is a `canonical_glasses` map (alias → the spelling a drink must use)
and `test_drinks_use_the_canonical_glass_spelling` reads its whole vocabulary
from it. **Adding a pair there is what makes it enforced** — no second list.

**The aliases in `icons:` stay, and that is not a contradiction.** They do two
jobs a rule cannot: keep a drink rendering if one slips through, and absorb the
spreadsheet's own spellings on ingest, where the variance arrives whether or
not this repo approves. The rule governs what is WRITTEN into a drink; the
alias map governs what can be READ. Deleting the aliases to "finish the job"
would break every drink the rule had not reached.

17 drinks were retyped in the same commit rather than left failing — `rocks`→
`old fashioned` (9), `double rocks`→`double old fashioned` (3), plus
`old-fashioned glass`, `old-fashioned`, `champagne saucer` and `snifter`. The
invitation was to break a test, but **the suite gates the deploy (#369), so a
red `main` stops the build rather than merely reporting**.

**Why all 17 at once was safe, and would NOT have been before #347**: `rocks`
has been a plain alias to `old-fashioned` since that issue resolved — one
drawing, not two — so the change carries no meaning, only spelling, and every
drink rendered the identical icon before and after. Earlier, the two names
pointed at genuinely different artwork and this same edit would have silently
restyled nine drinks.

`martini` vs `martini glass` is deliberately NOT in the map: it splits 1–2
across three drinks and Helen's four canonical pairs do not include it. **An
alias absent from the map is permitted**, so silence means "not asked yet"
rather than "either is blessed".

### 9.12 The method-step dictionary — `_data/cocktails/methods.yml`, #290

**Added 2026-08-26. A closed vocabulary for the mechanical spine, free text for
everything else.** The argument for it is not tidiness, it is #290's own, and
it is the same one §13.1 makes about the punched-tape mark beating the
watercolour washes: a shape that changes every time has to be RE-READ, an
identical repeated one becomes something you RECOGNISE. That is exactly the
difference between a canonical "Shake all ingredients with ice." and thirteen
near-variants of it, and it matters most in the situation Helen named — people
in the house, and thirsty.

**The test for whether a step belongs in the dictionary: does its phrasing
carry information?** "with ice" versus "over ice" carries none. "other than the
champagne" carries all of it. The tail is deliberately NOT canonicalised and
never will be — "Muddle the lime chunks hard with the sugar in the bottom of a
shaker until the sugar has dissolved" cannot be collapsed without losing the
drink.

The founding census, 2026-08-26: **277 steps across 105 drinks, 144 distinct.**
One instruction accounted for 43 uses written three ways; Stir the same for 17;
Strain alone had eleven forms.

**NOTHING WAS APPLIED TO A DRINK UNTIL HELEN HAD RULED, and that was her
explicit design** — past tense since 2026-09-02, when the pass below finally
ran. "Prefer both, leaving my original too, then I delete whatever I don't
want." So `proposals:` held her exact existing string on the left and the
suggested canonical form on the right, **deleting a row was how a suggestion got
rejected**, and the pass applied only what survived.

**The design still governs the NEXT census**, which is why it is written here
rather than in a commit: propose, never apply; let her delete in either
direction; apply what is left. And do not turn this into an enforcing test
without asking — a check that failed on a non-canonical step would be enforcing
a decision she has not made.

> **THE PASS IS DONE — 2026-09-02, #630 closed.** This box said it had not
> happened from 2026-08-26 until then, and called the file "the oldest unpruned
> thing here". It is pruned:
>
> | | before | after |
> |---|---|---|
> | distinct method steps | 161 | **146** |
> | uses on the canonical spine | 110 | **177** |
> | outstanding proposals | 24 | **0** |
>
> **65 steps across 64 drinks**, of which 62 came from the 20 mechanical rows
> (applied as text edits by `tmp/apply_method_proposals.py`) and 3 from Helen's
> rulings on the QQ rows, which are recorded below.
>
> **`proposals: {}` IS THE SETTLED STATE, NOT AN EMPTY FILE.** Both this and
> `garnish.yml` empty out BY DESIGN — that is what "resolved by deletion" means
> — so a full map is the temporary state. The key stays and its guard asserts
> the KEY exists rather than that it has rows, which is the one thing whose
> silent loss would switch the check off for whatever is proposed next. §12
> carries the general form: **a ratchet list and a worklist look identical and
> want opposite assertions.**
>
> **§9.12.1 was the worked precedent and it held exactly**: measure, collapse
> only what carries no information, propose the rest, let Helen rule, delete
> each row in whichever direction it went. Use that shape again rather than
> reinventing it.
>
> **THIS BOX WAS WRITTEN TWICE, by two sessions, from opposite sides of the
> merge** — which is what a shared handover does under parallel work, and the
> merge conflict is the mechanism catching it rather than a problem. The two
> accounts agreed on everything except the count, because one was counting the
> mechanical rows and the other the total. Both numbers are above, said apart.

**THE FOUR QQ ROWS, AND THE REASON THEY WERE PARKED WAS WRONG FOR TWO OF THEM.**
This section used to say the short forms "each follow an earlier build step, so
they mean *shake what is in the shaker*". That was reasoned from the STRING —
the exact mistake a fuzzy matcher makes, made by hand. Read per instance, with
the step above each one:

| drink | the step before | answer |
|---|---|---|
| `north-sea-oil` "Stir with ice." | **nothing — it is step 1** | → "Stir all ingredients with ice." |
| `sapins-swizzle` "Shake with ice." | "Add the remaining ingredients." | Helen: *"should retain 'shake with ice'"*. Now canonical. |
| `caribbean-sazerac` "Shake the rest with ice." | a rinse | Helen: *"match please."* → "Shake the remaining ingredients with ice." |
| `smokestack-lightning` "Fine strain with ice." | a shake, into a `coupe` | **the GLASS was the wrong field** — see below |

**TWO IDENTICAL-LOOKING STRINGS WENT OPPOSITE WAYS** on nothing but the line
above them. That is #290's argument against a fuzzy matcher in its concrete
form, and it is why an explicit map is the right tool. **The preceding step is
the whole question** for any short verb form; never decide one from its shape.

**AND WHEN A STEP IS INCOHERENT, ASK WHICH FIELD IS WRONG.** Smokestack
Lightning read as a transcription fault for as long as the glass was assumed
right — you fine strain to keep ice *out*, and it said `coupe`. Helen: *"'fine
strain with ice' doesn't mean anything — I bet I meant 'fine strain over
ice'."* The step was fine and the GLASS was wrong; it is `old fashioned` now.
`glass:`, `garnish:` and `method:` all describe one serve, so an impossible
instruction may be a correct instruction beside a wrong glass.

**`"Stir with ice."` is deliberately NOT declared though its shake twin is**: no
drink stirs after a build today. A future one should say it and be declared
then. A form with no user is not drift, and adding it now is machinery for a
case that does not exist.

**Naming the glass in a strain step is the one variance that looks informative
and is not** — `glass:` already carries it and draws the icon, so "Fine strain
into a chilled coupe" says coupe twice.

Three tests guard the map without touching a single method: a proposal must
point at a real canonical step, nothing may be both canonical and
something-to-replace, and every left-hand string must still exist in the
collection — because **a proposal whose work is already done reads as
outstanding**, which is the one thing this file must not get wrong. Same
bargain `all_icons` strikes: duplicate live data only alongside the test that
keeps the duplicate honest.

**What the census found besides variance**, all fixed or flagged the same day:
three TRUNCATED steps (Between the Sheets, Espresso Martini, and Chartreuse
Swizzle — whose truncation is its FIRST step, so the whole build is missing),
two typos, three notes filed as method steps, and four steps that were one
instruction split across two lines ("Strain." + "Into a chilled glass."). Only
three fragments were genuinely presentation, and those went to `to_serve`
(§9.4). Truncations are flagged, never reconstructed: a plausible guess is
still an agent writing Helen's recipe.

### 9.12.1 The garnish vocabulary — `_data/cocktails/garnish.yml`

**Added 2026-08-31 at Helen's request, and it is methods.yml's sibling in every
respect** — same argument, same shape, same bargain. The difference is that this
one was pruned to empty within two days, which is why §9.12 now points here.

**IT IS NOT FOR FILTERING, and that matters more than it sounds.** There is no
garnish filter and this is not a step towards one — the same ruling
`taxonomy.yml` makes about glasses and about spirits. The case for it is #290's:
a shape that changes every time has to be RE-READ. The weaker case ("a
vocabulary would let you exclude by garnish") was available and is wrong; it
would have been building a feature nobody asked for, which is #459's busywork.

**The census, 2026-08-31: 130 garnish entries across 123 drinks in 65 distinct
strings**, for perhaps 35 actual garnishes. `mint sprig` / `mint sprigs` /
`mint bouquet` / `mint sprigs bouquet` was one garnish wearing four faces.
Collapsing only unambiguous drift took it to 55; Helen's rulings the next day
took it to **49**.

**`["no garnish"]` MEANS DECIDED, `[]` MEANS UNFILLED**, and the marker may only
appear ALONE, which is what stops it becoming a fake member of the vocabulary.
It was `none` until 2026-08-31 and **the rename is about the page, not the
data**: `_layouts/cocktail.html` joins this list straight into the drink page,
so the stored word is the word a reader sees. Helen: *"'no garnish' actually,
because none might read like 'not filled in' even though you and I know that's
not the case."*

**ONE DRINK ALREADY SAID IT, AND THAT IS HOW THE RENAME WAS FOUND.** ti-punch
carried `no garnish` against fifteen `none`s, and the old guard could not see
it — it only inspected lists that CONTAINED `none`, so a second spelling of the
same decision passed silently. That is precisely the failure its own docstring
claimed to prevent. **A guard anchored on one spelling cannot see the second
one**; it is anchored on the canonical string now, and names the retired
spelling rather than reporting it as merely undeclared.

**What was deliberately NOT collapsed is the useful half.** `lime wedge on rim`
says where to put it, `orange zest twist (discarded)` says it does not stay in
the drink, `luxardo maraschino cherry` names a genuinely different object.
methods.yml's own test — *does the phrasing carry information?* — decides every
one of these, and it is the same test in both files.

**A TWIST IS A STRIP OF ZEST.** Helen collapsed all four `<citrus> zest twist` /
`<citrus> twist` pairs to the short form. **The tails survived the collapse**:
only the head form was normalised, so `orange twist (discarded)` and `lemon
twist after expressing over cocktail` keep the words that say whether the peel
stays in the drink. `flamed orange zest coin` kept its `zest` — a coin is a
different cut, not a longer name for a twist.

**A COUNT STAYS ONLY WHERE THE COUNT IS THE SPEC.** `three coffee beans` is the
Espresso Martini; `12 raspberries` was how many that punch happened to want, and
became `raspberries`. One rule, two rows, rather than two decisions.

**"EITHER OF THESE, MAKER'S CHOICE" IS A SINGLE STRING, NOT A LIST** — settled
on fake-id's `orange or lemon twist`. Helen: *"either of these are lovely and
the maker can choose. I like this approach on principle."* **It has to be one
string because a list already means something else**: `garnish:` is
CONJUNCTIVE (Cobra's Fang wants a mint sprig AND a lime wheel), so
`["orange twist", "lemon twist"]` asks for both. `generic` solved the identical
problem from the opposite default, where a list means "any of these would do"
(#441). **The two fields cannot share one convention**, and anyone tempted to
unify them should read that first. One drink uses it, which is deliberately not
enough to build machinery for.

**`test_every_garnish_is_declared` is a RATCHET**: seeded from the collection's
real strings, odd ones included, so it cannot fail on what is there and bites on
the next new spelling. `proposals` is `{}` and **the key stays** — an empty
mapping says "nothing outstanding" where a missing one says nothing at all, the
same reason `GLASSLESS_ON_2026_08_27` was kept and asserted empty.

**That guard asserted `proposals` non-empty for exactly one day and was wrong.**
These empty out BY DESIGN — that is what "resolved by deletion" means — so a
full map is the temporary state and an empty one is the settled one. It asserts
the KEY exists now, which is the thing whose silent loss would switch the check
off for whatever is proposed next.

---

### 9.13 The cocktails visual language, and the index and drink page built from it

**2026-08-26, one sitting with Helen against a mockup.** Everything in this
section was decided by her LOOKING at candidates on a dev page, not by
argument. That page (`_dev/cocktails-design.html`) is deleted; it held eleven
card framings, four hovers, six greens, five second accents and three thirds,
and exactly one of each won. Deleting it was deliberate — a page of rejected
candidates that nothing renders is issue #276's trap exactly: it looks like
evidence, goes stale silently, and the next reader cannot tell which of the
eleven shipped. Recover it from git if you need the losers.

**"Ink, paper and glass."** Helen's phrase and the whole idea: a
near-monochrome ground where the glass drawings carry the personality food gets
from colour. Food leads with ten saturated brights; this site leads with line
work and spends colour sparingly on top of it.

> ### ⚠ THE PAPER IS BLACK NOW — 2026-09-02, issue #469
>
> **Helen: "One thing for sure: we're going black on black. I wear black on
> black animal print whenever possible. I have some black on black bed linen.
> This is what we're doing."** The sentence above said "a LIGHT, near-monochrome
> ground" until then, and everything in this section written before that date
> should be read as reasoning that still binds over values that have moved.
>
> **`$color-paper` is `#0e0e10` and `$color-ink` is `#e8e6e2`.** The names keep
> their jobs rather than their literal meanings — paper is still what you read
> ON — and renaming them would have touched every consumer for no gain.
>
> **A CARD IS DARKER THAN THE PAGE**, `#17171a` on `#0e0e10`. That is the one
> structural choice rather than a value: a card recedes instead of floating, and
> the drama comes from the page being the lighter thing. L\* 7.85 against 4.02,
> with the border at 18.18 holding the card's shape however close the fills get.
>
> **THE DRINK PAGE IS DONE, 2026-09-02.** It was rebuilt whole against Helen's
> own written brief and the round-two mockup she approved from it
> (`tmp/mock/drink_page.py`, gitignored scratch — read the commit that shipped
> this paragraph if the file itself is gone by the time you read this). See
> "The drink page — two states, one page" below for the anatomy and the colour
> jobs that came out of that brief.
>
> **What the inversion cost, all measured — the workings are in the commit and
> the reasoning beside each value in `_palette.scss`:**
>
> - **Every `-deep` was re-solved.** They were each ~4.75:1 against paper; on
>   black a hue must be LIGHTENED rather than darkened to carry text, and four
>   of the five are bright enough that the bare rule colour IS the text colour.
>   Only `ultra-yvette` needed deriving — and its own note had predicted that
>   from the other direction, having been stuck near 4.75 on paper because there
>   was nothing darker to make text from.
> - **Every `-wash` was re-derived**, 10% tints of white being near-white blocks
>   on black. They are 14% of each hue over a CARD. 14 rather than 10 because a
>   tint toward a dark ground moves the eye less per percentage point; at 10 they
>   read as a slightly different black.
> - **The heading bars needed nothing.** They are bands rather than text, so no
>   contrast bar applies, and all six clear 6:1 against the ground anyway.
> - **The emboss inverted.** `shared/_rule.scss`'s defaults are solved for dark
>   type on a light ground; `--emboss-shadow` computed to a LIGHT shadow once
>   `$color-text` went near-white, which reads as a second letterform rather
>   than depth. Cocktails re-points three values in its own `_rule.scss`. A
>   shadow copy is only visible where it spills past the glyph onto the ground,
>   and dark on dark shows nothing.
>
> **IT IS A PALETTE CHANGE AND NOT AN ARCHITECTURE ONE, and that was checked
> before starting rather than hoped.** `test_the_header_and_footer_are_identical_on_every_page`
> compares rendered HTML and colour is CSS;
> `test_every_chrome_class_has_a_rule_in_every_site_stylesheet` checks
> DIVERGENCE rather than values. The chrome already differed in colour between
> the sites through `$color-accent`. **Food is untouched** — verified in the
> compiled CSS, not assumed.

#### The card title sits on punched tape — #469, 2026-09-02

The header wordmark's own black label tape, at card size, carrying the drink's
name. This is what took the site black: the tape needed a dark card to sit on,
and the card needed a dark page.

**Two near-whites, one tight pair, no softening**, plus the shared heading
stroke. Not the wordmark's four copies — 1px is 5.9% of a 1rem title where the
wordmark's 1.8px is 4.5% of its 2.5rem, so the four-copy version reads as two
overlapping letterforms down here. Helen: *"the boldness of the two near-whites
with no softening shadow is exactly what we need."*

**The band is centred by moving the ARTWORK, not the words.** Every tape SVG
insets its polygon 16.47% from the top of its viewBox and 12.94% from the bottom
— identical across all seven, measured — so the visible band is 70.59% of the
box and its centre sits 1.765% low. `top: -1.765%` on the background fixes it,
after which flex centring places the lettering with no font metric involved.
**Three rounds of bugs came from compensating on the TEXT instead**, which needs
Courier Prime's real ascent and cap height, and the face ships here as woff2
only with no font parser available. Correcting a fact about the artwork ON the
artwork needs no estimate at all.

**The tape's geometry is solved for the NAME'S WIDTH**, which is the thing Helen
actually wanted: *"reasonably lengthed names of cocktails can appear on the one
line."* The word gets

    body width + bleed-left + bleed-right − 2 × pad-x

so **padding costs the name twice while a bleed pays it back once** — a generous
padding was the thing making titles ellipsise. The bleed EQUALS the padding, so
the lettering lands exactly on the ingredient line's left edge; the tape bleeds
right into the card's own padding to buy the width back. **The gutter is the
ceiling on the left bleed** — 1.05em is 16.8px against `$card-gutter`'s 15.2px,
so the tape deliberately crosses onto the glass panel by 1.6px.

**`$card-tape-pad-x` and `$card-tape-bleed` are `em` and the gutter is not**, so
dropping the title from 1.08rem to 1rem shrank the bleed to exactly the gutter
and silently removed that overlap. Any tape number in `em` is a ratio to the
title; the gutter is a fact about the card. Re-check the pair whenever the title
size moves.

**The two injected SVG attributes are a named constant**, `TAPE_ATTRS` in
`decorations.js`, shared by `tape()` and `cardTapes()`. The files carry
`width="100%"` and no height, so without `height="100%"` the element keeps its
intrinsic ratio and LETTERBOXES — a narrow tape draws far shorter than its box
while a wide one fills it, which is two tapes on one page disagreeing. A
hand-copied version of that line dropping the height cost a round.

#### The five accents — "neon bar sign", 2026-08-29

**Read this before the history below it.** The palette went one accent →
three (2026-08-26) → **five** (2026-08-29), and the earlier rounds are kept
because their REASONING still binds. The values do not.

| variable | | job | where it already is |
|---|---|---|---|
| `$color-electric-absinthe` | `#30E88C` / `#0E8248` | MOOD, **and the home colour** | glass wash and hover on a card, nav/footer chrome |
| `$color-radiant-reposado` | `#F47E25` / `#B6540A` | YOLO / GOODNESS | the ship mark on a card |
| `$color-ultra-yvette` | `#9233E6` / `#9A41E7` | HASSLE | — |
| `$color-cosmic-cosmopolitan` | `#F127A7` / `#D40E8C` | HAS TO HAVE | the matched-ingredient band |
| `$color-luminous-lagoon` | `#2ED1EA` / `#0E7C8C` | I KNOW WHAT I WANT | — |

Bare = the RULE, a vivid band under a heading, **never text**. `-deep` =
4.75:1 on paper, safe as type. `-wash` = a 10% tint for something that has
matched. **LEAVE OUT has no hue at all** and the absence is the decision —
Helen: *"for food, avoiding can be important whereas for drinks surely less
so."* Food gave its LEAVE OUT a sixth colour; this deliberately does not.

**A heading's colour is a promise the card already keeps.** That is the rule
that makes five hues feel inevitable rather than decorative: MOOD is green
because the glass panels are green, YOLO is reposado because the ship mark is,
HAS TO HAVE is cosmopolitan because matched ingredients are. Nothing was
assigned by taste alone. Helen's own reasoning, and she assigned them.

**The home colour doubles as a section colour, and that is not incoherent.**
Helen worried it was — if green is the site's colour, can it also be MOOD's?
Food answers it: `$color-accent` **is** `$color-star-root`, and §13.2 calls
those "one rhyme rather than four coincidences."

##### The three measurements that shaped it

**1. Five saturated hues that avoid food's six DO NOT EXIST.** Helen ranked
neon top but flagged that "all five colours are close (to my eye) to our food
palette" — true, and worse than she thought: one was **1° from food's hot
orange**. Sweeping the whole circle, the best possible five-set still comes
within **21°**, because food's own six already tile it (25, 58, 84, 197, 223,
313). So **saturation, not hue, is what separates the two sites**: the muted
candidate palette landed ΔE 31 from food's nearest colour where neon landed 15,
using a hue *3° away*. The sites are siblings by construction; what makes them
different is the home colour (green here, magenta there) and how freely colour
is spent.

**2. The dichromacy bar applies to exactly two of the five, and I applied it to
all five first.** It cost two candidate palettes before the error surfaced. A
heading rule sits under its section's name **in words**, so hue is
reinforcement and may safely collapse for a dichromat — food runs six hues,
several of which would fail the bar, and is not broken. The bar is real only
where colour carries meaning ALONE: **the goodness mark and the matched
ingredient**, plus the mood chip beside them on the same card. Those three were
checked — worst pair reposado vs cosmopolitan under tritanopia, **ΔE 22.6**
against a bar of 10.

> **THE TOOL IS TRACKED NOW: `scripts/palette_measure.py`.** This line said
> "re-run `tmp/neon_values.py`" and two comments in `_palette.scss` named that
> file and `tmp/greens2.py`. **All three were gone** — `tmp/` is gitignored — so
> three instructions pointed at nothing, and the black-on-black work rebuilt the
> same contrast, dichromacy and CIEDE2000 arithmetic from scratch to answer the
> same questions. It is in `scripts/` so the next inversion does not rebuild it
> a third time. `--contrast`, `--separation`, `--lstar`, `--over`.
>
> **An instruction to re-run something is only as good as the something.** This
> is §12's stale-instruction trap wearing tooling rather than prose.

**3. Ultra-yvette cannot take dark text at all.** Ink on it is 3.14:1 and
*nothing* darkened clears 4.5, because the fill is already dark — a vivid
blue-violet has no brighter version to be a fill from. This mattered until the
card stopped putting text on colour at all, and it is why nothing should start
again.

##### Bands and washes, not fills — and this is the transferable part

Helen, 2026-08-28, on a card carrying three filled things: *"There's just a lot
going on… underline the ingredient rather than highlight."*

**Fill is the loudest tool available**, and a card can carry several matches at
once. The fix was a language already invented for the headings and used nowhere
else: **a coloured band under text**. So "this colour under text" now means one
thing everywhere, and a matched ingredient is visibly the answer to the
cosmopolitan heading that found it.

- matched ingredient → a band (`text-decoration`, **not** the headings'
  `box-shadow`, because this one WRAPS and a box-shadow gives a wrapped
  fragment an odd stub)
- matched chip → a wash plus a coloured border, **text stays ink**
- **the goodness mark is the only fill left on a card**, which is right: it is
  the one thing there that is not text

**Text on a wash is ink, never the `-deep`.** Each deep is solved to ~4.75:1
against PAPER, so any tint beneath drops the pair under 4.5 — ultra-yvette
lands at 4.49 even on a 6% wash. Darkening the deeps to compensate would damage
the job they exist for.

##### What the earlier rounds still bind

**Colour weight tracks how much of the page something occupies, not how
semantically distinct it is.** Violet spent one revision on LEAVE OUT and came
straight off — "suddenly busy, and jarring". The least-used control below the
fold was the largest, so it became the loudest thing on the page. Still the
most transferable line in this section, and it is why LEAVE OUT now has no hue
at all.

**Every pair is solved, not darkened by a shared step.** The lightness that
hits a contrast target is a property of the HUE. The same trap bit again on
2026-08-28: after the swap, one shared `darken(…, 22%)` put MOOD at 10.99:1
(nearly black on bright green) and HAS TO HAVE at **3.61:1**, which fails AA.
Five fills at five lightnesses cannot share one darken value.

**Helen rejected campari red and bitter orange** as "too red-green and
inaccessible" and simulation agreed exactly: against the green, campari falls to
24.5 ΔE under protanopia while reading 101 apart to normal vision — the failure
mode where a palette looks fine to whoever picked it.

**The names are the bottles** (#555). A hue name describes the pixel; a bottle
name describes the site. `radiant-reposado` is arguably the wrong bottle —
reposado is amber-brown and hue 26 is Aperol almost exactly — and it is Helen's
name and her call, recorded so the next reader knows it was noticed.

#### The index — `cocktails/index.html`, `_filters.scss`, `assets/js/cocktail-index.js`

**`cocktail-index.js` IS DOM WIRING ONLY SINCE #579** — the pool, the ranking
and the matching rules are `assets/js/cocktail-search.js`, and the filter state
is `COCKTAIL_FIELDS` in `filter-state.js`. See §9.3.3 before changing any
behaviour described below; several of the sentences here predate that split and
describe where a rule USED to live.

**THE UNIVERSE SAYS… SITS ABOVE THE FIVE QUESTIONS, since 2026-09-02** — one
random card's tape name, ingredient line and mood chips dealt before the page
asks anything, with `deal again`. Same section, same script and same reasoning
as food's; see §13.4, which is where it is written up once for both sites.

**FIVE NAMED QUESTIONS, in the order Helen asks them** — restructured
2026-08-29 and this is the current shape:

| | | |
|---|---|---|
| 1 | **YOLO?** | `no chaos please` / `I'm open to chaos` |
| 2 | **Mood** | what the drink IS — fourteen buttons since 2026-08-30 |
| 3 | **Hassle** | four buttons: what it COSTS |
| 4 | **Has to have** / **Leave out** | typed, with candidate pools |
| 5 | **I know what I want** | drink name — the way past all of it |

**The order is the diagnosis, not a layout.** Helen: *"I feel like I am doing
work to understand what to click in order to maximise my chance of getting the
drink I want."* The page had asked ONE question — "what do you fancy?" — and
offered ten answers belonging to three different ones. **"No juicing" is not a
flavour and "I want to faff" is not a mood.** Sorting them into questions was
work the reader did silently, every visit.

**Taste and style are NOT split, and that was tried.** The first proposal had
three groups. Helen: *"honestly I think taste and style in those columns are
the same, and should be called Mood. Splitting out Hassle though feels good."*
The only cut that earns its place is between what a drink IS and what it COSTS.

**The split lives in `taxonomy.yml`'s `mood_groups`, not the template**, with
`test_every_mood_belongs_to_exactly_one_group` asserting the partition is
total, non-overlapping and free of phantoms. Without it a mood added to
`moods:` renders NOWHERE — no button, no error, and its drinks become
unfilterable. Same silent-gap class as an unmapped glass (#500).

##### HALF THE MOODS ARE HELEN'S AND NO RULE PRODUCES THEM — #452, 2026-08-30

**Nineteen moods. Nine are derived from ingredients and method; ten are
hers alone**, listed in `moods_by_hand`. `scripts/derive_cocktail_moods.py`
never emits one of hers, and `expected_moods()` preserves whatever a drink
already carries for them, so a re-run can reorder her judgement but never
overwrite it. **Verified rather than assumed**: two were put on the Negroni by
hand and the whole collection re-derived with `--write`; both survived.

**THE TEST THAT DECIDES WHICH SIDE A MOOD BELONGS ON IS HERS.** Four flavour
tags were proposed — `bitter`, `smoky`, `herbal`, `vegetal` — and she killed
all four:

> *"They're flat descriptors, which is fine in moderation, whereas I'd hoped
> for more evocative moods, you know, something I can offer beyond what one
> might guess from the ingredients list."*

A tag meaning "contains one of these bottles" is a worse copy of the HAS TO HAVE
field, which already does that and does it better. **Apply this to any future
mood.** `amaro` and `herbal` turned out to already exist as FAMILIES, so the
roll-up those tags would have duplicated was built all along; the only thing
genuinely missing was the word `bitter`, now an alias to `amaro`.

**EVERY RULE WAS SCORED against a full pass she made over all 114 drinks**,
which is the measurement to repeat rather than re-derive. Intersection over
union:

    no juicing 1.00 | fruity .94 | ice ice baby .88 | warming .79 | sharp .78
    strong brown drink .76 | I want to faff .73 || clear .67 | tiki .53
    aperitivo .36 | sugar craving .23

The four after the break moved to `moods_by_hand` on those numbers.

**`up` WAS PROPOSED AND KILLED THE SAME DAY, and the way it died is the useful
part.** Read straight off the glass it covered 58 of 114 — 51% — and
`test_no_mood_covers_more_than_half_the_collection` refused it: the guard that
retired food's `one-pot` at 57%. Helen had said *"I'm not sold on up, let's
retain it but with suspicion"* an hour earlier, and **the suite reached her
conclusion independently**. Narrowing was not available — the coupe alone is 40
drinks, so any version without it is not `up`. `mood_up_glasses` went with it.

**WHAT THIS COSTS A FUTURE INGEST, and it is the thing most likely to be
forgotten.** A newly written drink gets its nine derived moods for free and
**none of the ten that are Helen's**. Nobody will be told: the page renders, the
suite is green, and the drink is simply missing from half the browse axes.
`scripts/derive_cocktail_moods.py` is not the whole answer any more — after
adding drinks, ask her for the hand-assigned ones. The review page built for the
2026-08-30 pass is the cheap way to do it (a clickable table of every drink
against every mood); rebuild it rather than asking drink by drink.

**THE RULES UNDER-FIRE, AND THAT IS THE REASSURING HALF.** Across the entire
pass there were only **four** cases where a rule tagged something she did not.
Everything else was her adding. A conservative rule is the right kind of wrong.

**THIRTY-ONE OF HER CALLS ARE `mood_include` ENTRIES rather than looser rules**,
because every relaxation was measured and cost more than it bought: dropping
`sharp`'s ingredient cap fixes 9 and wrongly tags 20; `warming` plus falernum
fixes 2 and wrongly tags 8; one muddle instead of two fixes 3 and wrongly tags
11. `sharp` stays 40 right and 0 wrong. **A narrow, precise rule plus recorded
exceptions beats a loose rule**, and each exception still receives every other
mood and every later improvement.

**THE ONE RULE THAT DID CHANGE was `fruity`**, where the measurement went the
other way: `orange juice` in, `crème de banane` out, from 8 misses and 1 false
positive to 2 and 0. The rule excluded all citrus as "the sour component" —
true of lime and lemon, **false of orange**, since nobody builds a sour on
orange juice. Grapefruit stays out; a Brown Derby really is a sour. The orange
LIQUEURS were tested and rejected: they reach every drink she tagged and wrongly
tag nine more. **Orange juice is fruit; orange liqueur is construction.**

**`I KNOW WHAT I WANT` is last on purpose.** Food has had that escape hatch
since the beginning and this page had none, so there was no way past the
apparatus even when you already knew. Last rather than first because Helen
browses here deliberately — *"I find browsing quick and inspirational… steer
myself then read for a while then settle"* — and a name box at the top would
invite treating the page as a search box, which is not what it is for.

**YOLO USED TO BE BACKWARDS, and this is the bug most worth not
reintroducing.** `yolo` meant "ship is NOT yes-or-better", so the button for
"I'll try anything" was **the one button guaranteed to hide all 55 of the best
drinks**. `open` is now a visible STATE that applies no filter at all — Helen:
*"'I'm open to chaos'… includes all drinks, not just
not-known-to-be-definitely-good drinks."*

**The headings were outranked, not illegible**, which is why "I can't read the
headings" measured at a passing 5.12:1. They were 0.78rem grey labelling
0.92rem ink buttons — smaller AND three times paler than the things they label.
Worse, `.btn-chaos` was set in the heading's *exact* typeface, size, case and
letterspacing, so two things competed to look like headings and the real one
lost. **A control must not dress as a label.**

**There is NO GLASS FILTER and there must not be one.** The drawings are the
site's identity, not an axis. This sits alongside taxonomy.yml's older and
stronger ruling that there is no SPIRIT filter either.

**It reads DRAFTS**, on Helen's explicit call: *"for food, we build drafts
locally only, so let's do the same."* The `site.show_drafts` gate and its reason
are unchanged from the page it replaced — see §9.9 and issue #235.

**A mood with no drinks renders no button**, counted rather than listed as an
exception, so the rule holds for whichever mood is empty next. Today that is
`pudding in a glass` (2 drinks now, but see #337 — the family exists in Helen's
head and not in the collection); eighteen of the nineteen render.

**Filtering reads data- attributes, never rendered text.** Moods, chaos bucket
and a pre-lowercased ingredient string are all written at build time. A filter
that reads `textContent` breaks the first time somebody restyles a card.

**How the axes combine** (#478/#479, settled): **OR within a section, AND
between sections**, and drinks matching MORE of the selected moods **rank
first**. Two moods means "either", because AND across moods is nearly always
empty — `tiki` AND `no juicing` is a handful. The ranking is what makes OR
usable: plain OR stops narrowing anything once you pick a second mood, and
ranking gives the precision back without the one-match drinks vanishing.
Include chips are AND, because adding an ingredient means "and this one too",
which is how a cupboard works.

**Everything shown is in RANDOMISED order, shuffled ONCE PER PAGE LOAD.** Each
card gets a random sort key at startup and keeps it; filtering re-ranks against
those fixed keys. Re-shuffling on every filter change would make cards leap
around while you type into the has-to-have box, which reads as a bug however
correct it is. Random rather than alphabetical because alphabetical buries
everything after M and greets you with the same drink every time — the
`taxonomy.yml` principle applied.

#### The index's hover language — one colour, one meaning, 2026-09-02

**Magenta means "this one", and it is the only thing hover ever changes.** A
card title, a card's glass-column brackets, a filter tag, a pool chip's box and a
mood chip's box all go magenta under the cursor; nothing else moves, and nothing
resizes. It reads as one gesture because it is one colour making one claim — the
same claim `is-match` makes in the settled tense.

**Four hover states were no-ops before this, all in the same way.** Filter tags
rested at white and hovered to a dimmer white; the card title rested at `#ECE9EA`
and hovered to `#ffffff`, four values away. §12's rule is the diagnosis: **at
these sizes the eye reads hue, not lightness**, so a lightness-only hover is a
state that never arrives. The `clear` buttons are the one deliberate exception —
grey to full ink is a lightness step, and it works only because the gap is
6.50:1 to 15.47:1, which is most of the available range rather than a nudge.

**`:hover` AND `.is-on` ARE THE SAME SPECIFICITY, so the later block wins
outright.** A chosen tag turned magenta under the cursor until `:not(.is-on)`
was added. They are saying different things and only one can be true at a time:
hover means *you could pick this*, which a picked one is past — so hover stops
applying rather than being out-specified.

**A CHIP HAS A BOX AND A FILTER WORD DOES NOT**, which decides what each moves.
HAS TO HAVE's chips changed their TEXT colour on hover on top of their border,
so a chip whose words already carried magenta word-match underlines went almost
entirely magenta — three uses of one colour on one small object. LEAVE OUT had
it right by accident of being colourless. Chips move their box; bare words move
their text.

#### The card — `_cards.scss`

**THE MOOD CHIPS FILTER THE INDEX — Helen's ask, 2026-09-02.** Clicking one adds
or removes that mood exactly as its filter button does.

- **They are real `<button>`s**, not spans with a handler. That is what earns
  keyboard focus, Enter and Space, and a role — none of which a span gets for
  free — and it is why `_cards.scss` has to undo the UA's own button styling.
- **One DELEGATED listener on the list**, calling the mood buttons' own toggle,
  sync and re-render. Two reasons, and the second is the load-bearing one:
  a chip and its filter button must not be two implementations that agree today;
  and `apply()` re-orders nodes to rank them, so a per-chip listener would need
  rebinding on every pass — the class of bug §12 records for `tagShapes()`.
- **`is-match` and `aria-pressed` are painted FROM STATE in `apply()`**, never
  toggled at click time, because clear-all reassigns the whole state object
  without touching any markup.
- **The handler calls `preventDefault`**, because the chip sits inside a card
  whose title is a link.



Horizontal: the glass drawn large down a fixed left column, words beside it.
Chosen over a vertical card and over a typographic tile because it is the only
one with room for a full ingredient line, which the index needs — you can search
by ingredient, so a card must be able to show why it matched.

**THERE IS NO PANEL BEHIND THE GLASS, since 2026-09-02.** The column is still
exactly `$card-text-x` wide and still holds the drawing; what has gone is the
tinted field it used to sit on. The drawing is `$color-electric-absinthe` and
the card shows through. Helen chose it against three darker and greyer fields on
the real index, and two things made the case:

- **the green wash was the lightest thing on a card.** L\* 19.40, against the
  card's own border at 18.18 and the card itself at 7.85 — a bright field on a
  site whose premise is black on black. It arrived as a 10% tint that made sense
  on paper and survived the inversion as a value rather than as a decision.
- **the arrangement was backwards.** This section's own opening claim is that
  the glass drawings carry the personality food gets from colour; a near-white
  glass on a green field is the opposite of that, with the field carrying the
  colour and the drawing carrying none.

One `color` declaration on `.drink-card-glass` reaches every glass, because the
artwork strokes with `currentColor` (§3) — including the three fill-based
drawings, which a rule on `.glass-icon-line` would have missed.

**Every anchor is fixed, and that is the design rather than a side effect.**
Helen: the title starts in the same place on every card, and the goodness mark
sits in the bottom-right corner in exactly the same spot every time. That rules
out the obvious layout twice: a card whose height comes from its content puts
the foot somewhere different on every card, and a vertically-centred text block
moves the title. So: fixed height, body anchored top-left, foot pinned to the
bottom and out of flow.

**The cost is clamping and it is not avoidable.** Two lines of ingredients and
two rows of mood chip — the tagline went with #512, so this said "two lines each
for tagline and ingredients" describing an element the card no longer has. A
rigid grid buys its rigidity with
clamping; the alternatives are a card whose height varies with mood count
(unpinning every anchor) or no moods on cards. Helen named the trade first:
"it's a shame to lose the card proportion but I can't think of another way."

`$card-text-x` is the single source of the title's left edge — the glass column
is exactly that wide, and the body, the foot and the under-mark all derive from
it. One value moves four things together and they cannot drift apart.

**The framing and the hover took eleven and four candidates respectively.** What
won: a glass column marked by a rule in the home green along its bottom edge, no
vertical rule (eight of those down a page is a lot of signal for decoration);
and on hover, that rule plus the column's top edge going to full strength, so
the column is bracketed. **Both hover marks are painted strips, not borders** —
a border would eat into the column's fixed height and nudge the glass, and the
one rule the hover has is that nothing moves.

**The bottom rule is full-strength absinthe now, not a mix.** It was
`mix($color-electric-absinthe, $color-surface, 55%)`, which read as a pale green
while there was a green panel beside it to belong to; with the panel gone it is
the only green on a resting card, and a diluted one reads as a leftover rather
than a mark.

**Helen asked for "a very subtle lightening of the white part of the background"
and it was not available**: a card was `$color-surface` on `$color-paper`, so
its white was already the brightest thing on screen with nowhere lighter to go.

**THAT CONSTRAINT IS GONE AND ITS OPPOSITE IS NOW TRUE.** Since the inversion a
card is `#17171a` on `#0e0e10` — DARKER than the page — so a hover could lighten
it, and there is room in both directions. The hover deliberately still does not:
the brackets are what move, because nothing on this card is allowed to. Kept
here because **the lesson survives the reversal** — before promising a subtle
lightening on any design, check which end of the range the surface is already
sitting at, since on a light ground it is the answer and on a dark one it is not
even the question.

#### The goodness mark

**IT IS A SHIP AND A WORD, NOT A SQUARE — and this paragraph said otherwise
until 2026-09-02.** `cocktails/index.html` renders `.drink-card-ship-icon` (the
ship partial) beside `.drink-card-ship-word`; the tinted square is gone, and the
template's own comment records that nothing reads `ship_tints` any more. The
paragraph below describes the retired square. It is kept because **its
reasoning is the part that binds** — the scale's shape, not the mark's — and
because #511 and #612 both want a goodness scale on the DRINK page, where these
are exactly the traps to avoid. Read it as an argument, not as a description.

A small square, tinted along `ship_tints` in `_data/cocktails/taxonomy.yml`.
**Not a linear ramp and it must not be made into one**: `yes` and `oh gods yes`
are both 100 because both mean "make this" — the difference is enthusiasm, not
decision — and the whole range is spent on the gap that matters. `sure` and
`meh` were 62 and 30 for one afternoon; at 62 a `sure` was mistakable for a
`yes` at a glance, which is the one thing a scale exists to prevent.

**The border never changes at any rung.** An empty square reads as "rated, and
rated low"; a square that faded out entirely would read as "not rated", which is
a different fact the scale already holds separately as `who knows`.

**It sits AFTER the label, not before.** Before it, the square's x position
depended on the length of the rating word, so the one mark meant to be findable
without reading moved from card to card.

#### How tall a glass is drawn on a card — the curve, and the empty cheat

**Two numbers, and neither is per-glass.** Settled 2026-08-31 by Helen at
`/dev/card-glasses/`, closing #601.

| | | |
|---|---|---|
| the curve | `ratio × 0.5 + 0.5` | `cocktails/index.html` — lifts the SHORT end |
| the headroom | `$card-glass-scale: 10.4rem` | `_cards.scss` — caps the TALL end |
| `display_scale` | **`{}`** | the per-glass cheat, kept and empty |

**Each fixes a different complaint and they compose.** A curve cannot move the
tallest glass — it is the reference, so its ratio is 1.0 *by construction* —
which is why the flute filled the panel edge to edge and why headroom had to be
a separate dial. Conversely headroom moves everything together and does nothing
about a 180mm Collins reading as a stripe beside an 85mm old-fashioned. Offering
them as rival models on the dev page was a drafting error Helen caught in one
line: *"Is headroom plus compression an option?"*

**Measured, on the collision the cheat existed for:** a Collins stood 1.74× the
old-fashioned beside it and stands 1.34× now. That is why `display_scale`'s two
entries (collins 0.82, hurricane 0.74) came off — the curve does their job for
every pair rather than the two somebody noticed. Collins and hurricane are
consequently *taller* than they were, +7 and +11 points of panel height, which
was put to Helen with both numbers before the change.

**The map is kept and deliberately empty.** It is still the right home for a
judgement about ONE drawing, and it still composes with the curve. Add a line
only when a specific drawing is wrong in a way a range answer cannot see.

**`$card-glass-scale` was 13rem against a 12.9rem panel** — the reference glass
defined to be taller than the box it lives in. That is the whole of #601.

**Eight wide glasses are capped by `max-width` before they reach their height
target**, so the curve does not reach them: punch-bowl sits at 32% of the panel
and did not move. Known and accepted; the lever there is the width cap, not the
curve.

> **A CROSS-REFERENCE TO ANOTHER FILE'S BEHAVIOUR IS A CLAIM NOTHING RE-CHECKS.**
> Three places — `glasses.yml`, `_layouts/cocktail.html` and this section — said
> the card template "raises every ratio to a power". It never had. Worse,
> `glasses.yml`'s was an INSTRUCTION ("try the global curve first if a third
> glass ever wants a line here"), so it sent the next reader after a knob that
> did not exist at exactly the moment a third glass wanted one. Grepping for it
> finds the three comments asserting it, which is §12's prose-fools-a-scan trap:
> the vocabulary is densest where the claim is wrong. `git log -S` over the files
> that would have to contain it is the check that works.

**`/dev/card-glasses/` is kept rather than deleted with its losers** — Helen's
call, and an exception to the comparison-switch convention (§13.9) rather than a
hole in it. That convention is about a switch left in a SHIPPED page; this is a
dev page whose whole job is the comparison, and rebuilding the instrument costs
more than keeping it. **Its defaults are the shipped values and must stay that
way**, or it quietly starts describing a site that no longer exists.

#### The drink page — two states, one page

**Rebuilt whole, 2026-09-02, against Helen's own written brief** (reproduced in
the commit that shipped this rewrite) and the round-two mockup she approved
from it. Read `_sass/cocktails/_cocktail.scss` end to end before touching this
page again — its header carries the anatomy and the colour jobs in full, and
this section is the shorter pointer to that, not a duplicate of it.

**The anatomy.** The glass sits in the page's left margin above 1180px (large,
top-aligned with the title) and tucks inline below that width, as it always
has — only the WIDTH changed, to a clamp derived from the margin itself (see
`$glass-col`). The name sits on the same Dymo tape a card's title does —
`.drink-card-name` / `.drink-card-tape` / `.drink-card-tape-bg` /
`.drink-card-tape-word`, reused exactly rather than redrawn, with a real `<h1>`
nested inside the tape word at `display: contents` so the tape's own lettering
treatment reaches it without a second emboss stacked on top. Meta is a `<dl>`
of GLASS / GARNISH / SHIP IT?, the last of those reading `page.meta.ship`
through `_includes/cocktails/ship.html` — the SAME include the index card now
calls, factored out so a card and this page can never render one rung two
different ways. Mood chips are the card's own `.drink-card-mood` spans (not
its `<button>`s — this page has no filter list for a click to narrow).
INGREDIENTS / METHOD / NOTES follow, each with its own two-bar heading mark
(`@include heading-rule`, moved to `_sass/cocktails/_rule.scss` so the index's
filter headings and this page's section headings share one mixin rather than
two lookalikes).

**Nothing leaves the DOM.** One class (`is-making`), and the stylesheet hides
what the state does not want, so the page prints whole and reads whole with
the script blocked — **in the editorial state, deliberately the one carrying
more.** `assets/js/cocktail-make.js` sets it now from a THREE-part toggle
("read it" / a track with a knob / "make it") rather than a single button —
Helen's brief asked for "a binary slider/toggle... with 'read it' or 'make it'
active", and both labels are always on screen, so the #494 ambiguous-label
problem the old button solved with a constant label cannot arise here in the
first place: there is no single label whose meaning could be read two ways.

**Four colours, four jobs — not the three this section used to describe.**
Electric absinthe stays the page's home colour (the title's border, the
toggle's ON state) and claims no section on its own. Ultra yvette marks
INGREDIENTS and METHOD — Helen: yvette "shows what is in something", and a
method step is a component of the drink as much as an ingredient is, so one
colour marks both, under the section heading and under each ingredient's own
name (`.cocktail-item-name`'s own double-rule underline, the same device at a
smaller size). Cosmic cosmopolitan stays the bottle suggestion's colour (ASKED
FOR) and is spent nowhere else on this page. Luminous lagoon is new to the
page and marks NOTES — Helen's commentary is "a different kind of thing" from
what is in the drink or how it is made, so a different colour marks it; lagoon
already carries name-search on the index, which is the site's existing pattern
of one colour, two jobs (absinthe is home and mood). **Radiant reposado came
off notes entirely** — it is the verdict's colour (the ship mark) and a note
card must not borrow it; section rules and note cards never use pink,
curaçao, or (on notes specifically) yvette.

**Section headings are 1.35rem again, and the size is still load-bearing, not
loud.** `$emboss-stroke` is 1.6% of font-size, so at the 0.76rem they opened
at, the punched effect resolved to about a fifth of a pixel. **The effect needs
the size before it means anything** — worth knowing anywhere the punched
treatment is applied to small type. (This page's headings spent a round at
1.8rem, matching food's `.recipe-section-heading`, for a different reason —
keeping the h1/h2 ratio identical between the two sites. Helen's brief asked
for 1.35rem directly, which is a return to the number the size-registration
argument always named, not a regression from it.)

**Issue #485 is CLOSED, not a known compromise** — checked against the tracker
rather than assumed, since this section had gone on describing it as open well
after the fix shipped. What #485 wanted was the glass matching the text
column's height with no second number to keep in step by hand; the fix was to
take the glass out of flow entirely (`_sass/cocktails/_cocktail.scss`'s own
"THE GLASS IS AS TALL AS THE TITLE BLOCK" note), which had already happened
before this rewrite. The margin-width clamp this rewrite added is a separate,
later change — it makes the glass LARGER, per Helen's brief — and does not
itself touch #485's height question, which needed no further touching.

#### The six open questions, answered 2026-08-27

The index shipped with six behaviours provisional and issues raised against
each, so they were decisions rather than defaults. Helen answered all six.

**Ordering — #478 and #479, which turned out to be one question.** Answered
above under "How the axes combine" and the randomised-order paragraph beside it;
seventeen lines restating both stood here until 2026-08-31 and are deleted
rather than kept in step.

**Chaos filters, it does not sort (#480)** — unchanged, `definitely good` hides
everything else.

**The empty state (#481)** takes food's `.recipe-list-empty` treatment value
for value. One of the few places the two sites SHOULD converge: an empty list
is not part of either site's personality, and two of them would be two things
to keep in step for no gain. `text-transform: lowercase` is what makes the copy
lower case, so the markup keeps ordinary capitalisation.

**Print is the FULL page (#482), not the `make it` state** — and the
expectation was confidently wrong the other way. `make it` is what you want
beside you while pouring, but the thing beside you is the phone; a PDF is the
archive copy, and one that has dropped the tagline, the class lines and the
notes is a worse record than the page it came from. `_sass/cocktails/_print.scss`
forces it, so the same page printed twice cannot give two different documents
depending on an invisible toggle position.

Two traps there, both caught by reading the built CSS rather than by the build
succeeding: the rules first compiled to TOP LEVEL, outside `@media print`,
which would have applied on screen and permanently broken the toggle they exist
to override; and the toggle's class is `btn-make`, not the `.cocktail-make-toggle`
that got guessed. #86's guard then failed honestly on `.is-making`, because it
searched templates only and that class comes from JS — **it now searches
`assets/js/*.js` too**, which is a strengthening rather than an exemption.

**Narrow screens (#483)** — Helen asked "are screens realistically going to be
narrower than about 380px????" Yes, by the two commonest widths there are: 360px
is the dominant Android portrait width, 375px covers the iPhone SE, 8 and 13
mini. What that costs at the default card layout:

| viewport | card | text column | glass takes |
|---|---|---|---|
| 360px | 312px | 157px | 39% |
| 375px | 327px | 172px | 37% |
| 412px | 364px | 209px | 33% |

157px is about eighteen characters of Courier Prime. Losing the tagline (#512)
freed a LINE; this is a WIDTH problem.

**`$card-text-x` and `$card-glass-scale` are now custom properties as well as
Sass variables**, and that is the point rather than a detail: Sass resolves at
compile time, so five rules had each baked their own copy of `7.6rem`, and any
narrow-screen variant would have had to restate all five and keep them in step
— reintroducing the exact coupling `_cards.scss`'s header comment exists to
prevent.

**Three layouts currently sit behind `?narrow=` and TWO OF THEM ARE DUE TO BE
DELETED** — `stack` (glass as a full-width band on top, the default),
`title` (glass small top-left, title beside it) and `shrink` (the original
column, narrower). Same comparison-switch pattern as `?glass=margin` and
`?align=top` before it, and it must have the same ending: once Helen picks, the
losers and the switch script in `cocktails/index.html` go. A comparison switch
left in becomes a permanent branch nobody dares remove.

#### Every drink names a glass, and `any` is retired (#491)

`any` meant "no requirement" and was the last exempt value in
`test_every_glass_value_is_in_the_vocabulary`. Exactly one drink ever used it —
Daisy de Santiago, `[collins, any]`. Helen:

> *"when someone tells me to use an old fashioned glass I always automatically
> assume I can use any glass I like, so there's no need to have 'any' as a
> glass type."*

The freedom it encoded is one she applies to every glass spec, so recording it
on one drink said nothing true about that drink and something false about the
other 113. Daisy now reads `[collins]`, which is what "anything, but preferably
a Collins" always meant. **There is now no exempt value.**

**The real gap that issue was hiding was sixteen of 114 drinks naming no glass
at all, and it is CLOSED — 2026-08-30.** On a drink page the glass is the hero,
drawn as tall as the whole title block, so an empty `glass` was a page with a
hole where its main image goes. `test_every_drink_names_a_glass` ratcheted the
sixteen rather than guessing, because which glass a drink wants is Helen's
knowledge and a wrong glass looks exactly as confident as a right one.

She named all sixteen in three sittings. `GLASSLESS_ON_2026_08_27` is empty and
the test is now simply what its name says. **The empty set is asserted rather
than assumed** — an exemption list that has emptied is the moment a ratchet
stops doing anything, so its sibling fails if a name is ever added back.

**WHAT MADE IT QUICK WAS SHOWING THE TOTAL VOLUME**, which is the transferable
part. That is what actually decides a glass and it had never been put in front
of her; several drinks then answered themselves — the Bellini's own method
already said "add 25 ml syrup to a champagne flute", Banana Boulevardier's said
"over a large ice block". Two glasses she wants and does not own (a sling, a
zombie) are recorded as NOTES rather than data, because a `glass` value is what
she would actually pour into.

#### A technique worth keeping: tracing a filled icon into strokes

The tiki mug had no lines in it. Its source is fill-only stock artwork — one
rule, `.a{fill:#231f20;}` — so publishing it with `glass-icon-line` stroked the
OUTLINE of the ink and drew a hollow double line. Filling it instead rendered
correctly but left no stroke width to control: it read ~2.8× heavier than every
glass beside it and got heavier as it grew, while theirs stayed put.

Helen searched and found no stroked tiki mug SVG anywhere. **Three hand-redraws
missed**, and the problem was method, not care — eyeballing a thirty-stroke
drawing reproduces what you notice and normalises what you do not. What worked:
rasterise the original FILLED, thin it to a one-pixel skeleton (Zhang-Suen),
walk that into strokes, simplify, emit. 103,817 ink pixels → 7,073 skeleton
pixels → 46 strokes. An overlay check (original in grey, traced lines in black)
showed essentially no grey.

**This is valid whenever the artwork is UNIFORM WIDTH** — every cap in that file
is a 0.85 radius arc, so the ink is 1.7 units throughout, and the medial axis of
a constant-width stroke is its centreline. It would not be valid on artwork with
varying weight.

**Both tools are now permanent, 2026-08-27 (#498):**
`scripts/trace_centrelines.py` (the tracer, generalised from "the tiki mug" to
any filled uniform-width artwork, with a CLI and a dry-run default) and
`scripts/svgrender.py` (the rasteriser, which also does the canvas measuring in
§9.14 and is imported by two tests). Verified against the mug on the move:
identical 103,817 → 7,073 → 46 strokes, 323 points.

Two traps if it is ever rebuilt. There is no rasteriser in this environment, so
one was written (path flattening, scanline fill, PNG out) — validated against
three known-good icons before being trusted on anything new. And the obvious
skeleton-walking algorithm does not work: splitting the graph wherever a pixel's
degree is not 2 assumes 4-connectivity, but a Zhang-Suen skeleton is
8-connected, so a pixel on a plain diagonal has three neighbours and nearly
everything classifies as a junction — that version returned 2,966 polylines for
a thirty-stroke drawing. Walk greedily, preferring the neighbour that best
continues the current direction, so strokes run straight THROUGH crossings.

---

### 9.14 `heights_mm` sizes the CANVAS, so margin inside a drawing costs you

**2026-08-26, found by measurement after two glasses looked wrong side by
side.** An icon renders at the height `heights_mm` gives its **viewBox**. The
glass inside that viewBox is whatever fraction of it the artwork occupies — so
a drawing with empty margin renders SMALLER than one without, at the same
`heights_mm`, and no data change fixes it.

The case that surfaced it: Helen's redrawn double old-fashioned.

| | ink fills viewBox height | renders, vs the single |
|---|---|---|
| `old-fashioned` (85 mm) | 99.0% | — |
| `old-fashioned-double` previous (100 mm) | 99% | 1.18× ✓ |
| `old-fashioned-double-2` (100 mm) | **75.7%** | **0.90×** ✗ |

`heights_mm` says the double should stand 1.176× the single. The redraw stands
0.90× — a double old-fashioned that draws smaller than a single — because a
quarter of its canvas is air. **The viewBox being BIGGER is not the same as the
glass being bigger, and it is easy to check the wrong one:** the redraw's
viewBox is 1.29× the single's, which looks like confirmation and is not.

**How to check.** Measure the ink's extent as a fraction of the canvas.
Reasoning from viewBox numbers and internal matrix scales gave the wrong answer
here; measuring did not.

#### FIXED AT THE SOURCE, 2026-08-27 — and the cause was never carelessness

`scripts/normalise_glass_icons.py` now **fits every icon's viewBox to its own
artwork** as its last step, so a slack canvas cannot reach the site. The guard
that was "worth a guard eventually" exists too —
`test_no_glass_artwork_has_a_slack_viewbox` — but as a backstop for artwork
that skipped the normaliser, and its grandfather list is EMPTY.

**Why it belongs in the pipeline rather than in a checklist.** Helen:

> *"I created the coupe and goblet drawings by editing others, which will be
> how the height issue happened. I am not able to do anything other than this
> as I can't draw."*

A shortened drawing keeps the taller drawing's canvas. That is the inevitable
output of the only way she can make a glass, so "remember to fit the canvas" is
an instruction that will fail every time.

**It found two worse than the one that prompted it.** The double old-fashioned
had improved to 85.5% by the time anyone looked (settling on `old-fashioned-2`
did that, unmeasured). Goblet was at **69.5%** and coupe at **82.5%** — and the
coupe is the one that mattered: **40 drinks**, declared the same 150 mm as the
highball and rendering **15% shorter than it**. Two glasses that should be
identical on screen were not, and nobody had noticed, because nothing is out of
proportion WITHIN a drawing — only between it and its own frame.

**Three things about the measurement, each learned by getting it wrong:**

1. **Not a raster.** Ink-pixel counting works, but the answer depends on where
   the pixel grid falls, which depends on the viewBox, which is what is being
   computed. Over eight successive fits the canvas oscillated across a
   ~0.1-unit band instead of settling.
2. ~~**Not raw geometry either.**~~ **WRONG ON BOTH HALVES, AND IT COST THE
   COUPE — #599, 2026-08-31.** This said some drawings carry paths outside their
   own viewBox, "clipped by it and never visible", so `ink_bbox_units` should
   clip the points to the viewBox and `fit_viewbox` should only ever shrink.

   **They were visible.** `.drink-card-glass svg` sets `overflow: visible` — a
   root `<svg>` clips only because the UA stylesheet says so (§9.11, added to
   stop a stroke on the frame edge being sheared), so every card painted the
   excess. Helen reported the coupe sitting high in its panel; that was 11.8
   units of bowl hanging above its own canvas.

   **And the numbers were mis-measured.** `svgrender.parse_icon` read ONE
   `<g transform="translate(...)">` with a regex. Four icons nest a
   `<g transform="matrix(...)">` holding the bowl — coupe, goblet,
   old-fashioned-double, nick-and-nora — and that matrix was dropped, so the
   figures quoted here described geometry in the wrong place. The parser
   composes the whole ancestor stack now and bakes it into the geometry, so a
   caller cannot apply only the outermost.

   `ink_bbox_units` measures ALL the ink, and `fit_viewbox` grows as well as
   shrinks. **The creep the shrink-only clamp prevented was a property of
   measuring clipped ink** — the input moved when the frame moved. An unclipped
   bbox does not depend on the viewBox at all, so it cannot creep, and the
   idempotence guard still passes.

   **`heights_mm` scales the VIEWBOX**, so ink outside it is height nothing
   accounted for: the coupe was declared 150 mm and drew as if 179, the goblet
   175 and drew as if 259 — taller than the flute. Eight canvases were refitted;
   the other 19 did not move, which is the evidence the corrected fit agrees
   with the pipeline everywhere it was already working.

   **Why it will happen again, in Helen's own words:** Inkscape keeps the
   previous canvas silently even when it reports the document as resized, so a
   glass built by editing another arrives framed for a different glass. That is
   the same argument as §9.14's own — it belongs in the pipeline, not in a
   checklist.
3. ~~**Shrink-only.**~~ **GONE with the clip, 2026-08-31.** It read: padding an
   ink box that touches the clip edge pushes the canvas out, admitting a sliver
   of hidden artwork, enlarging the box, pushing it out again — unbounded creep,
   one margin per regeneration. All true, and **all a property of measuring
   CLIPPED ink**: the input moved when the frame moved. An unclipped bounding
   box does not depend on the viewBox at all, so there is no feedback to creep,
   and `fit_viewbox` grows as well as shrinks.
   `test_fitting_a_canvas_never_moves_the_artwork` still asserts idempotence and
   still passes. **The general form is worth more than the fix: a guard against
   a feedback loop is only needed while the loop exists, so check whether it
   still does before keeping the guard's cost.**

**Margin is 1.4 user units, not a percentage.** These icons use
`vector-effect: non-scaling-stroke`, so the stroke is a fixed number of SCREEN
pixels and occupies MORE viewBox units the smaller the icon renders. A
percentage margin shrinks exactly when the stroke needs it most — on a card —
and clips the rim.

**Unconditional, and that was measured before choosing:** with canvases fitted,
23 of 26 icons move by 0.4% or less.

**A guard exists for each direction now, and neither substitutes for the other.**
`test_no_glass_artwork_has_a_slack_viewbox` rasterises INSIDE the viewBox and
asks what fraction of the canvas the ink spans — so it catches a canvas bigger
than its drawing and is *structurally incapable* of seeing the reverse, because
ink outside the frame is not in the raster it measures. Every icon scored
96–100% on it while four had artwork hanging out.
`test_no_glass_artwork_is_drawn_outside_its_viewbox` is the other direction, and
`test_the_icon_parser_applies_nested_transforms` is the one that keeps the
measurement honest — a synthetic two-group SVG with the answer worked by hand,
so it still bites if the drawings are ever flattened.

**AND THE NORMALISER DELETED ALL 26 ICONS. TWICE.** Its first act is to empty
`_includes/icons/glasses/`. `SRC` is `tmp/cocktail-glasses`, a **gitignored
inbox** that is empty in a fresh worktree — so on 2026-08-27 it emptied the
destination with no input and wrote nothing back, printing `0 icons ->` as if
that were a result. (The first time, 2026-08-26, was an import running a bare
`main()`; that is why the file has a `__main__` guard.) It now refuses unless
it has usable input, BEFORE deleting anything. **A destructive step that runs
before its inputs are checked will eventually run with no inputs.**

Recovery both times was additive — `git show HEAD:<path>` writing only absent
files — rather than `git checkout --`, which the destructive-git hook refuses
on a dirty tree and which would have taken uncommitted work with it.

### 9.15 Never save a redraw over its predecessor

**The rule, and it now has a mechanism behind it.** `_design_sources/` is the
record of what was tried. A record you can overwrite is not one.

Helen dropped a corrected double old-fashioned, it was copied over the file it
replaced, and for one commit the only surviving copy of the previous drawing
was in git history. `/dev/glasses/` recovered it with `git show`, which worked
and was the wrong shape: the whole job of comparing a redraw against what it
replaces cannot rest on archaeology that a squash, rebase or shallow clone
removes.

**The convention** — base name is the original, a numeric suffix is the redraw,
and both stay on disk. Eleven sources carry one after the 2026-08-31 pass
(`coupe-4`, `absinthe-2`, `collins-4`, `goblet-2`, `hot-toddy-2`,
`julep-cup-3`, `sherry-2`, `sour-2`, `tiki-mug-3`, `pineapple-4`, plus
`hurricane-2`), so **read `RENAME` in the normaliser rather than guessing which
number is live** — the count moves and the suffix is a fact about this repo's
history, not a pattern.

**Which one publishes is then a NAMED SWITCH, not an accident.** In
`scripts/normalise_glass_icons.py`, a `RENAME` entry points the suffixed name
at the published name and a `SKIP` entry holds back the one it supersedes, with
a comment saying which two lines to delete to reverse it. That is how an
undecided choice should sit in a repo: both options present, one live, and the
change a deletion rather than a reconstruction.

**VERIFY BY RESOLUTION, NOT BY INSPECTION.** After changing that switch, re-run
the normaliser's own skip/strip/rename logic and assert exactly one source
resolves to the published name, then regenerate and confirm the output matches
what is on disk. Issue #484 is what happens without this: the published
old-fashioned was correct only because someone had written it by hand, and the
`sorted()` ordering meant a regeneration would have silently replaced it with a
superseded 2-path draft. `-` is 0x2D and `.` is 0x2E, so every suffixed name
sorts BEFORE the bare one, and the bare one wins by being written last.

### 9.16 The candidate drawer — `/dev/glasses/` sections 5 and 6

Every drawing in `_design_sources/cocktails/glasses/`, normalised into
`_includes/icons/glass-candidates/` and listed in
`_data/dev_glass_candidates.yml`, both written by
`scripts/build_glass_candidates.py`. Rejects and superseded options included:
this is the drawer, not the shelf.

Three constraints shaped it, and all three are in the script:

- **Jekyll cannot reach `_design_sources/`.** `include` reads only from
  `_includes/`, and no plugin here loads an arbitrary path.
- **The copies cannot live in `_includes/icons/glasses/`.** That is the
  published set and `test_all_icons_matches_the_icon_directory` asserts it
  matches `all_icons` in both directions. A sibling directory is invisible to
  it, because that test globs non-recursively.
- **Jekyll cannot enumerate a directory**, so the names are handed to the page
  as data — written in the same run as the copies, so they cannot drift.

The list is deliberately NOT in `_data/cocktails/`, which is the site's
vocabulary. Scaffolding for one dev page does not belong beside three files the
whole site reads.

## 10. Validation — run `pytest`, don't read this

**The suite gates the deploy now (2026-08-18, issue #369).** Until then the
workflow checked out, built, rendered PDFs and deployed with no test step
anywhere, so every guard in this repository protected a local run and nothing
else. `.github/workflows/build-and-deploy.yml` has a `test` job and `build`
declares `needs: test`. Three things about it are load-bearing:

> **THE COCKTAIL GATE NOW FIRES AT PROMOTION — #540, Helen's ruling 2026-08-29,
> choosing option 4 of the four that issue lists: gate at promotion, and leave
> the private drinks out of a runner.**
>
> What it was: `tests/test_cocktails.py`'s `_load()` globbed `_cocktail_drafts/`
> alone, and CI checks out this repo without that private one, so **24 of the
> module's 41 tests skipped in every deploy run**, reported as passes.
>
> **#540's own account of the fix was too optimistic, and this is the part to
> carry.** It says the mask "comes off the day a cocktail is promoted". It did
> not. `_cocktail_recipes/` lives in THIS repo and IS present in CI — but the
> loader never read it, so a promoted drink would have been checked by nothing,
> anywhere, ever. Promotion did not lift the gate; it moved a drink permanently
> out from under it. The corpus is both roots now.
>
> **The half that the fix alone would have shipped broken.** Building the CI
> shape — drafts moved aside, real drinks copied into a scratch
> `_cocktail_recipes/` — showed **five guards failing on entirely correct
> data**. All five hang on a shrink-only registry (`GLASSLESS_ON_2026_08_27`,
> `KNOWN_PROSE_SUGGESTIONS`, `card_name_joins`, `methods.yml`'s proposals) or on
> a mood's share of the book, and **that class of claim is unanswerable on a
> partial corpus in the one direction that matters: a drink merely ABSENT looks
> exactly like a drink FIXED.** Five false reds on `main`, and not once —
> every later promotion re-runs them over a partial corpus too.
>
> So the two halves are separated. The RATCHET ("no NEW offender") is a
> per-drink claim and runs everywhere, which is the coverage promotion buys; the
> STALENESS half calls `_require_whole_collection` and skips with a reason.
> `WHOLE_COLLECTION_ONLY` is the registry and
> `test_whole_collection_only_says_what_it_does` keeps it true both ways.
>
> **`_load()` is the only door, and a test now enforces that**
> (`test_every_drink_reading_test_goes_through_the_loader`). One future test
> globbing the drafts itself reopens #540 for itself, silently, in CI only.
>
> ### THE SAME GAP FROM A NEW ANGLE: A PUBLIC TEST CAN NEED PRIVATE DATA, AND
> ### NOTHING MAKES THE TWO MERGES ARRIVE TOGETHER — #624, 2026-08-31
>
> The garnish vocabulary landed in halves: `_data/cocktails/garnish.yml` and its
> three tests merged HERE while the drink-side rename sat on an unmerged branch
> in the drafts repo. `main` was red for anyone with a current clone and **green
> in CI**, because the runner has no drafts and `_cocktail_recipes/` is empty —
> so those tests passed over an empty corpus. The deploy gate could not see it.
>
> **The tell is both directions failing at once.** "39 garnishes not declared"
> AND "garnish.yml proposes changes to strings no drink says any more" cannot
> both be a mistake in one file; they mean two files are at different commits.
> Read that as a synchronisation fault, not a data fault, and check the other
> repo before touching either.
>
> #540 made a PROMOTED drink checkable everywhere. This is the case where a
> public test depends on data the runner cannot reach at all, and the honest
> answer is not yet decided — see #624.
>
> **Still true, and not silenced:** at ONE promoted drink, four anti-vacuity
> asserts fire ("no rum ingredient carries a suggestion, so this check is
> vacuous"). They are correct, they say so accurately, and they self-resolve by
> five drinks. Adding them to `WHOLE_COLLECTION_ONLY` would lose that coverage
> in CI permanently to buy quiet in a one-drink window.

- **`fetch-depth: 0`.** `actions/checkout` is shallow by default, and in a
  depth-1 clone `git log -- <file>` reports the same single commit for every
  file — so §4.0's provenance test would examine nothing and pass.
- **The JS suite needs a glob**: `node --test tests/js/*.test.js`. Passing the
  DIRECTORY (`node --test tests/js/`) treats it as one test file and reports
  "tests 1, fail 1" without running the ones inside it.
- **CI has no private drafts, and every test that reads them now says what it
  does about that.** `_food_drafts/` and `_cocktail_drafts/` are separate
  private repos, gitignored here, so a CI checkout has the published recipes and
  none of the several hundred drafts. Resolved 2026-08-20, issue #378, and split by
  what each check actually reads:

  - **Drafts only** — skips, with a reason, so the run reports "did not run"
    rather than "checked and clean". `test_accents_in_drafts`,
    `test_pan_and_ingredient_sizes_use_digits_in_drafts`,
    `test_pantry_entries_are_actually_used`.
  - **Recipes and drafts** — keeps running, because the published half is real
    coverage and is the half that ships, and says in its own docstring what the
    CI green does and does not mean.
    `test_no_main_ingredient_spelling_collisions`,
    `test_no_recipe_uses_the_retired_instructions_field`.

  **The registries in `test_suite_hygiene.py` are the point**, not the five
  fixes. `test_every_draft_reading_test_says_what_it_does_without_drafts`
  derives the list from the source and fails on any draft-reading test that is
  in neither set, and on a set member that does not match what the set claims.
  Nothing about typing `for draft in ALL_DRAFTS` tells you the list is empty on
  the machine that gates the deploy, so a sixth quiet test cannot be added by
  accident. Per-draft parametrised tests are exempt and need no entry — pytest
  already reports an empty parametrisation as a skip, which is the ~51 skips a
  CI-shaped run shows.

**Before pushing anything that CI will run, simulate it**: move both private
draft directories aside, run the full suite, move them back. A green local run
proves less than you think, because your machine always has the drafts.


Counts move as recipes/guards are added — run the suites, don't quote numbers
from here.

| File | Covers |
|---|---|
| `test_front_matter.py` | Required fields, retired fields, xor rules, group names |
| `test_style.py` | Typography, spellings, accents, time formats, `Estimated` |
| `test_taxonomy.py` | Declared tags/stars, co-tags, links, spelling collisions |
| `test_site_config.py` | Architecture guards, not recipes — every check exists because something went wrong at least once |
| `test_drafts.py` | `_food_drafts/`-scoped subset of the structural/style rules above, via its own `draft` fixture — see its own module docstring for exactly which rules ported and which deliberately didn't |
| `test_reference_data.py` | `_data/food/internal_temperatures.yml`'s own invariants — see §14 |
| `test_suite_hygiene.py` | Tests about the tests: the one failure mode whose symptom is green (§12) |
| `test_cocktails.py` | The drinks' own spec, **and the glass ARTWORK's** — the two viewBox guards face opposite directions (§9.14) and `test_the_icon_parser_applies_nested_transforms` keeps their measurement honest. **This table omitted the file entirely until 2026-08-19**, and §9.5 still said "no tests exist for cocktails at all" — both written before it did |
| `test_page_links.py` | Every `<a href>` in every template, traced to a literal path. Also omitted from this table until 2026-08-19 |
| `test_rendered_pages.py` | Assertions about BUILT html, including the two chrome guards (§2.5), `test_every_published_page_links_a_stylesheet` (§2.4), and `test_every_icon_partial_class_has_a_styled_base` (#396) |
| `test_source_attribution.py` | The six citation rules, over recipes and drafts — see `SOURCE_ATTRIBUTION_SPEC.md` (§4). Omitted from this table until 2026-08-21 |
| `test_prose_pages.py` | House typography on the pages that are NOT recipes, and on the reference data that supplies their words (§5, #413) |
| `test_magic_bag.py` | `_food_magic_bag/`'s own schema, via its own `magic_bag` fixture — a much shorter spec than a recipe's, and deliberately so (§4.3) |

`pytest.ini` declares three suite MARKERS, which this section never mentioned:
`pytest -m food`, `-m cocktails`, `-m shared`. They exist for signal, not speed
— while Helen is doing food QA by hand her in-progress edits make the food half
red, and a red suite hides a real cocktails regression. `test_suite_hygiene.py`
asserts every module declares one, because an unmarked file is silently missed
by every filtered run.

### 10.1 Standing rules that came out of the 2026-08-12 issue audit

**CUT HARD 2026-08-29.** This section was 157 lines, most of it an enumeration
of twenty-odd issues closed in August 2026 and the tests each became. Every one
of those tests exists and states its own rule in its own docstring and assert
message — §11 requires that — so the table was a second copy of information that
maintains itself. Deleted rather than trimmed; `git log` and the tests are the
record. What survives is the handful of rules that still govern behaviour today.

**The audit itself is worth being able to repeat, and it is three steps**: grep
every test file for `issue #NNN` citations, diff that set against the closed-issue
list from the GitHub API, then check each gap against the actual front matter
before calling it a gap. Helen's framing, and the reason it happened: *"I'm
concerned that issues we closed in the last few days weren't represented as
tests... I still don't want to end up in a mess."* Most closures did have a test;
a real cluster did not.

**TWO TESTS ARE EX-CHECKLISTS, AND A RED IN EITHER IS NOW A REAL REGRESSION.**
`test_oven_temperature_says_fan` (#146, ~19 recipes) and
`test_milk_specifies_type` (#167, 9 recipes) both started deliberately red as
standing backlogs and were worked through by hand. Both pass now. **The reason
neither was ever a candidate for a bulk fix is still live**: which figure of a
fan/conventional pair is the fan one, and which milk a recipe actually used,
are answerable only from the original source — never guessable from the file.
If either goes red, get Helen's source material recipe by recipe; do not fix
blind. (At INGEST this is cheap and the page is in front of you — see §4's
ingest contract, which is why 39 drafts should never have reached this state.)

**`test_ingredient_notes_are_lowercase_fragments` FLAGS AND NEVER FIXES.** One
sentence, no trailing full stop, lower case unless the first word is `I` or a
declared proper noun. Helen: *"I'll look at violations myself because I care
about tone of voice."* Whether a capitalised first word wants lowercasing or
belongs in `taxonomy.yml`'s `proper_nouns` is her call. Same standing rule as
`QQ`: don't fix a violation unprompted.

**`PLACEHOLDER` was a second draft marker for one day** (2026-08-09 to
2026-08-10) and is retired; there is one marker, `QQ`. Never add a third.
**The ~190 drafts that still said `PLACEHOLDER - rewrite: ...` are gone as of
2026-08-31** — Helen asked for the whole corpus to be paired, and
`tmp/rename_markers.py` renamed 1,074 markers in place (270 `QQ PLACEHOLDER` +
804 `PLACEHOLDER - rewrite:`) to `QQ original`. This paragraph told you to leave
them alone; her instruction supersedes that, and the corpus is now uniform. See
§4 for the interleaved format.

**Which checks read `_food_drafts/` — ask the registry, not this file.** This
section claimed "exactly three" until 2026-08-21 while contradicting itself a few
hundred words above. There is a mechanical answer: `SKIPS_WITHOUT_DRAFTS` and
`PARTIAL_IN_CI` in `test_suite_hygiene.py`, enforced by
`test_every_draft_reading_test_says_what_it_does_without_drafts`.

The one that fires in practice is `test_no_main_ingredient_spelling_collisions`,
when a new draft's spelling collides with an existing ingredient — it caught
`"demerara sugar"` against four recipes' `"Demerara sugar"` on 2026-08-21.
**Before reporting a new failure, check whether the file is a draft Helen just
added**: `find _food_drafts -name '*.md' -mmin -120`. Don't chase it, and don't
tidy a draft you weren't asked to tidy.


### 10.2 Diagnosing decoration JS — the stub-DOM harness

`decorations.js` is an IIFE that touches the DOM directly and has no tests.
When something in it misbehaves, write a throwaway script (scratchpad, not
the repo) that builds a fake `window`/`document`, then `vm.runInContext` each
script **in the order the built page loads them** — read that from `_site/`,
not the layouts, because a layout's scripts land inside `{{ content }}` and
aren't where the file suggests. Print which scripts threw and which URLs were
fetched. This caught two real bugs by hand-reasoning alone; it's worth
knowing the trick rather than re-deriving it.

---

## 11. Working practices

**Never run `git reset --hard` without asking Helen first — every single time.**
Same for `git checkout --`/`git restore` over a dirty tree and `git clean -fd`.
They discard uncommitted work with no undo and nothing in the reflog to recover
it from. Check `git status` first and say what it shows; if something must be
discarded and she is not around, `git stash -u` instead, because that is
reversible. This is written here because it happened on 2026-08-18: a
`git reset --hard origin/main` run to move a stray commit off `main` also wiped
a half-finished handover edit sitting uncommitted in the same tree. The commit
survived. The uncommitted work did not.

**A hook enforces that rule now — added 2026-08-19, after the rule was read and
broken the same day.** See §11.0 below. It is the first executable rule in this
repo that is about the AGENT's behaviour rather than the site's content, so it
is worth knowing exists before you meet it.

**Check `git branch --show-current` immediately before every commit**, not at
the start of the task. Helen merges PRs and checks out `main` while you are
working, so the branch you started on is not necessarily the branch you are on.
Two commits landed directly on `main` this way on 2026-08-18 — **and the rule
paid for itself again on 2026-08-19**: Helen merged a PR and pulled mid-task,
which deleted the working branch out from under a session that had staged, but
not yet committed, an unrelated change. The check caught it standing on `main`
with three staged files. `git checkout -b <branch>` carries staged changes
across, so the fix is to branch and commit, not to unstage anything.

### 11.-1 The branch workflow, and the second hook

**Settled with Helen 2026-08-20. Four steps, and only one is hers.**

1. Claude works on a branch and pushes it (with her confirmation — see
   `CLAUDE.md`, the push rule is unchanged).
2. **Helen opens the PR, reviews, merges. That is all she does.** No local
   checkout, no pull.
3. Claude runs **`git fetch origin main:main`** — which fast-forwards the local
   `main` ref *without checking it out* — then deletes the merged branch local
   and remote and branches afresh.
4. Repeat.

**The whole point of step 3 is that Claude is never standing on `main`**, so it
cannot write there by accident. It also fails loudly rather than mangling
anything if the update is not a clean fast-forward, which is the signal that
someone has committed locally to `main`.

The old pattern — `git checkout main && git pull origin main` — is what this
replaced, and the gap it opens is exactly how a commit landed on `main` on
2026-08-20. **`git fetch origin main:main` is the form to use.** It is not a
stylistic preference.

**`.claude/hooks/guard-main-branch.py`** is the backstop: a PreToolUse hook on
`Bash` that refuses `git commit` and `git merge` when the target repo is on
`main`. Two details worth knowing:

- **It asks about the right repository.** It reads a leading `cd <path>` out of
  the command, because the nested drafts repos are edited through
  `cd _food_drafts && git ...` and four commits landed on `_cocktail_drafts`'
  `main` on 2026-08-17 for want of exactly this.
- **It strips quoted spans and heredoc bodies first**, like its sibling below,
  so a commit message may discuss the commands it refuses.

Everything else on `main` is allowed: reading, fetching, branching, checking
out, pushing an existing commit. The hook is not a lock on `main`, only on
writing history to it.

**Why a hook and not a firmer sentence — the failure is worth reading.**
`CLAUDE.md` already said to check `git branch --show-current` immediately before
every commit. The agent that broke the rule on 2026-08-20 *ran the check*:

```
git branch --show-current      <- the check
git add ...
git commit -F ...              <- already done by the time it printed
```

All three in one shell call, so the check printed `main` in the output of the
call that had already committed. **A check that cannot stop the thing it is
checking is a narration, not a check.** Run it in its own tool call, read the
answer, then decide — and note that this is the third time this repository has
concluded that a rule which gets read and broken needs a mechanism rather than
better wording.

### 11.0 The destructive-git hook

`.claude/hooks/guard-destructive-git.py`, wired as a **PreToolUse hook on
`Bash`** in `.claude/settings.json` with `if: "Bash(git *)"` so it only wakes
for git commands.

**Why it exists, and why it is code.** The rule above had been in `CLAUDE.md`
since 2026-08-18. On 2026-08-19 a session that had read it ran
`git checkout -- <two files> 2>/dev/null || true` to undo an edit it had just
made itself, and discarded work in the process. **A rule an agent reads and then
breaks needs enforcement, not rewording.** That is the same conclusion this
repository already reached twice, about `meta.awaiting_fix` and
`meta.proofread`: both were documented at length long before anything checked
them, and both were violated until something did.

**What it refuses**, when — and only when — `git status --porcelain` is
non-empty:

| Shape | Caught |
|---|---|
| `git checkout -- <paths>`, `git checkout <ref> -- <paths>` | yes |
| `git checkout <path>` — **no `--` at all** | yes, since 2026-08-19 |
| `git checkout .` | yes |
| `git reset --hard` | yes |
| `git clean -f` / `-fd` / `-xfd` / `--force` | yes |
| `git restore`, `git restore --worktree` | yes |

**What it deliberately allows, and the reasoning matters more than the list:**

- **Everything, on a CLEAN tree.** These commands are no-ops with nothing
  uncommitted. A guard that fires on harmless invocations is one you learn to
  route around, and an agent trained to route around a safety rail is worse off
  than one with no rail. The *combination* is the danger, so the combination is
  what is checked.
- **`git stash` / `git stash -u`**, which is the reversible answer the refusal
  points you at.
- **`git restore --staged`** on its own: that unstages and leaves the working
  tree untouched. Add `--worktree` and it refuses.
- **Quoted mentions**, e.g. `git commit -m "do not git checkout -- things"`.
- **Heredoc bodies.** Commit messages here are written through
  `git commit -F` from a heredoc, and they quote these commands constantly —
  the `CLAUDE.md` entry being enforced names three of them.

**THE BARE-PATH FORM WAS MISSING FOR A DAY, AND IT COST WORK.** The first
version patterned only the ` -- ` spelling. On 2026-08-19 a session ran
`git checkout tests/test_style.py` — reflexively, to undo a test-break it had
made itself, which is the exact scenario the hook exists for — and the hook
allowed it, discarding that file's uncommitted changes. **The guard's own author
fell into the hole the guard did not cover, hours after building it.**

The fix could not be a pattern: `git checkout main` is harmless,
`git checkout feat/some-branch` is harmless and looks exactly like a path, and
`git checkout tests/foo.py` destroys work. It asks the filesystem instead — an
argument naming a file that exists is a path, and nothing else is.

**The general lesson is about how a guard gets tested.** Both times this hook was
verified, the verification used the spellings its author had in mind. Enumerate
how the dangerous thing can be SPELLED, not how you happen to write it.

**Both quoted mentions and heredoc bodies were found by testing, not by
thinking, and the second found the loudest way available: the hook blocked the
very commit that introduced it.** A heredoc body is not quoted — it is data on stdin that merely
*looks* like shell text — so the quote-stripping added for the first case did
not reach it. If you extend this hook, extend the test sweep with it, and check
the two failure directions that matter: a heredoc *followed* by a real
destructive command must still block, and an *unterminated* heredoc must fail
safe rather than swallowing the rest of the line. Both are covered today.

**Why a hook rather than a `deny` entry in `permissions`.** A deny rule is a
prefix match on the command string, and the command that got past the written
rule was a compound line with a redirect and a fallback
(`… 2>/dev/null || true`). The hook reads the whole command and then asks git
whether anything would actually be lost. `CLAUDE.md` already notes that Bash
cannot be reliably restricted by permission patterns; this is the general answer
to that, not a special case.

**`python3`, not `bash`** — there is no `jq` on this machine. It is invoked as
`python3 <path>` so it needs **no execute bit**: `CLAUDE.md` forbids changing
file permissions without asking every single time, and a guard that required a
`chmod` to install would be self-defeating. Keep that property if you touch it.

**Known limits, stated so they are not mistaken for coverage:**

- It cannot see a `cd` earlier in the command line — it asks git about the
  directory the hook itself runs in, so a command that changes directory first
  may be judged against the wrong repository. Accepted: a wrong-but-loud block
  is recoverable in a way a silent discard is not.
- `bash -c "git reset --hard"` slips through, because the quote-stripping
  removes it. That is deliberate evasion rather than the accident this exists to
  catch, and no regex fixes it.
- It counts UNTRACKED files as dirty. Right for `git clean`, conservative for
  the others, and conservative is the correct direction here.

**If it blocks you and you think it is wrong, read the refusal before working
around it** — it names what is uncommitted. The commonest legitimate case is
undoing an edit you just made yourself, and the answer there is to **re-edit the
file**, not to reach for git. That is precisely the mistake that caused the hook
to be written.


Helen writes no code by choice, has strong systems judgement, wants
explanations that assume both. Offer aesthetic opinions — she asks for them.
Disagree with her when you think she's wrong; say plainly when you were
wrong yourself.

**Her hours are hers. Never remark on the time, suggest stopping, or wonder
aloud whether something should wait until tomorrow.** Helen, 2026-08-20, after
a session ended a summary with "it's half past midnight — that's a good place
to stop": *"I am aware of the time. I keep my own hours. Please never tell me
to stop or go to bed — those things are up to me."*

She added *"I'm sure this used to be in the handover"* — it never was, under
any phrasing, checked with `git log -S` across the whole tracked history of
this file and `CLAUDE.md` including deleted versions. So it had been said in
conversation and never written down, which is exactly what this section exists
to stop: a preference that leaves no trace in a file gets rediscovered by
annoying her with it again.

**The four below are about the INTERACTION, not the artefact, which is why
they have to live here.** The codebase teaches the house style better than any
prose could — read `_palette.scss` arguing itself down to four colours, or
`food/_rule.scss` on which dial to reach for first, and you will absorb more
than a section like this could tell you. But none of that can teach how the
work actually gets decided, because that leaves no trace in a file. Each line
here earned its place by being learned late, after the same thing had happened
two or three times. Added 2026-08-14.

- **Show, don't describe.** For anything debatable, build it at a throwaway URL
  and hand her the link. She will settle in one line what an hour of argument
  won't. Two demo pages decided the longform styling and the entire reference
  layer; the alternative was a list of options nobody could evaluate.
- **She reports symptoms, not diagnoses — and reports them accurately.** "The
  bar slightly obscures the word" was an axis clipping its own data. "It is
  lost at the moment" was a grouping error. "The FSA line is clipped" was a
  safety zone drawing 9°C away from the figure it was labelled with. Treat the
  observation as exact and go and find the cause; do not treat her wording as
  the brief, and do not stop at the thing she described.
- **An aesthetic objection usually has a structural reason under it.** "It makes
  no sense where it is", "even worse in my opinion", "I find the bullet points
  choppy" — look for the reason before complying, because the reason is
  generally the better fix. Complying with "it feels lost" would have added
  whitespace; the actual answer was that a horizontal rule was on the wrong
  side of it, grouping the figure with the wrong neighbours.
- **UAT is a first-class method here, and she is the only user.** She will find
  rendering faults no test in this suite can see — every filled bar on the site
  vanished once while 16,806 tests passed. When you cannot see something
  yourself, say so plainly and hand it over. Then write the test her eye just
  stood in for.

**The test suite is self-sufficient by design — GitHub Issues are
provenance, never a dependency.** Confirmed explicitly 2026-08-12, Helen's
own request: you should be able to bring `_food_recipes/`/`_food_drafts/`
into shape from `pytest` output and this file alone, with no GitHub access
at all. A `GitHub issue #NNN` citation in a test docstring or comment
records *why* a rule exists, historically — it is never the only place the
rule itself is stated. Every assert message names the actual fix (the
allowed list, the required shape, the reasoning), not just an issue number
to go look up. **Keep this true when you add a test**: if you find yourself
writing a docstring that only makes sense after reading the issue it cites,
that is a gap to close in the docstring, not something to leave for the
next session to chase down. This does not mean stop citing issue numbers —
they are useful history and cost nothing to keep — it means the citation
must never be load-bearing.

**Test names and error messages are both expressive, on purpose — Helen's
own words, 2026-08-12.** The self-sufficiency above depends on this, not
just on docstrings: a failing-test summary (`pytest -q`'s one-line-per-
failure output, or a CI notification) shows the test NAME and the assert
MESSAGE, not the docstring underneath it. If either one is generic, the
self-sufficiency is fake — you'd have to already know where to look.

- **Name the rule, not the mechanism**: `test_egg_size_is_stated`,
  `test_unsalted_butter_has_salt_or_a_note`, `test_title_and_slug_dont_
  diverge` — a reader knows what broke before opening the file. Not
  `test_egg_1`, `test_check_butter`, `test_slug_rule_2`.
- **The assert message names the actual fix**, inline, every time — the
  offending value, the allowed list or required shape, and (for a standing
  checklist) why it's not safe to fix blind. `f"{where(recipe)} has
  unqualified mustard: {bad!r}. Allowed: {...}."` tells you the file, the
  problem, and the fix in one line; `assert not bad` alone tells you
  nothing pytest didn't already know.
- Applies to every new test, not just the ones from a GitHub issue —
  this is a general standard for the suite, not scoped to 2026-08-12's audit.

**Git.** Branch/commit/push mechanics are in `CLAUDE.md` at the repo root —
that's the source of truth now, not this file. In short: branch from an
up-to-date `main` (§11.-1 step 3 — `git fetch origin main:main`, never a
checkout), commit freely without asking, never push without explicit
confirmation. **"Ask before creating a branch" used to be in this sentence and
is wrong**: the four-step workflow in §11.-1 has Claude branching afresh after
every merge, unprompted, and that is the point of it.

**Branch names:** `<type>/<what-its-about>`, lowercase, hyphens. Short-lived,
one concern each, deleted after merge, local and remote.

**Commit subjects:** `(type) lowercase description`, no full stop. The type
words actually in use on `main`, counted 2026-08-21 rather than asserted:
`styling`, `content`, `fix`, `docs`, `feat`, `test`, `chore`, `reference`,
`refactor`, `copy`, `data`. **This said "five type words in current use" and
named a set that excluded four of the top seven** — `content` and `docs` alone
account for 133 commits. Derive the list with
`git log main --format='%s' | grep -oE '^\([a-z]+\)' | sort | uniq -c` rather
than trusting any list written here. Write what the change *does*, not what you
did:

```
(fix) stop the logo tape forcing horizontal scroll on narrow screens
(refactor) extract ingredient search matching into a pure, testable module
```

ASCII `--` in commit messages, not an em dash — the em-dash rule in §5 is for
site prose, and commit messages go through tools happier without it.

**Commit bodies**, when the change isn't self-evident: why not what; how you
know it works ("0/100 before, 100/100 after" beats "fixed"); whether a fix
predates the branch or is a regression from it, and what you checked to know
that; what you ruled out; guards added, and that you broke them to prove they
bite.

---

> ## TAG THE ISSUE. EVERY COMMIT, NO EXCEPTIONS.
>
> **Resolves an issue → a trailer**, on its own line, one per issue:
> `Fixes #N` or `Closes #N`. GitHub closes it when the commit reaches `main`.
>
> **Merely advances or touches one → cite it in the body**: `Towards #N`,
> `See #N`. No closing behaviour, and that is the point — it is how the next
> reader finds the conversation behind the change.
>
> **Cross-repo needs the full form.** A bare `#N` resolves only within its OWN
> repository, and the nested drafts repos have their own empty trackers, so from
> `_food_drafts/` or `_cocktail_drafts/` it is
> `Towards DeckOfPandas/helen-triages#367`. Note also that such a trailer from a
> PRIVATE repo closes and cross-references **nothing** — see §12 — so closing a
> public issue from work done there is a separate, deliberate step.
>
> **Do it AT COMMIT TIME.** While nothing is pushed a message can still be
> rewritten; after a push it is fixed, and a trailer cannot be attached to a
> merged commit retroactively.
>
> **Helen's standing preference, 2026-08-29:** *"via commit message if possible
> — this is always my preference."* The `GH_TOKEN` API is for the cases a
> trailer genuinely cannot reach, not for convenience. A trailer ties the
> closure to the commit that earned it; closing out of band leaves the issue and
> the code with no link between them.
>
> **This keeps being got wrong, and the cost is always the same shape.** Four
> issues in one 2026-08-16 session (#52, #273, nearly #274/#281) shipped, merged,
> and sat in the open list looking like outstanding work. It happened again and
> was only caught on 2026-08-29: **#558 and #561 were both fully delivered days
> earlier** — verified by grepping the data, not by reading anything — and both
> were still open, because their commits carried no trailer. By then a trailer
> was impossible and they had to be closed through the API.
>
> **Before reporting an issue as done, check**:
> `git log main --grep="#N"`.

End every commit:
```
Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

**Ask her the decisions as you hit them, not in a batch at the end.** Her own
instruction, 2026-08-16: "Give me decisions to make as you go." It works
because her answers are fast and they change what the next hour looks like —
three rulings mid-way through the exclude vocabulary (collapse citrus to the
fruit; strip container words; split only compounds whose halves are both known
ingredients) each removed a class of guesswork rather than a single case.
Bring her the fact that forces the decision, not the options in the abstract:
"only 2 of 73 methods have this shape" settled the doneness UI in one reply.

**One agent at a time in this working tree, and never one that switches
branches.** 2026-08-16: a background agent was given issue #274, created its
own branch, and was still working when Helen ran `git checkout main` and
pulled. The checkout moved the tree out from under it, so it carried on
editing on `main` — its branch left empty, its work stranded uncommitted on
the branch it must never touch. Nothing was lost (the edits were sound and
were moved onto a fresh branch), but the failure mode is silent and the tree
is shared with a human who is also using git. Delegate the reading and the
scanning; keep the branching in the foreground.

**Issue tagging is the boxed rule above**, not a footnote here.

**This paragraph used to add "Helen has read-only `gh` access by choice, so
nobody can close them programmatically after the fact".** That stopped being
true on 2026-08-17 and stayed in the file until 2026-08-21, contradicting §10.1
four hundred lines earlier, which records the change. Claude may now read,
raise, close, reopen, comment on, label and assign issues on the three
`DeckOfPandas` repos via the `GH_TOKEN` fine-grained token — and nothing else,
no pushes, no PRs, no settings. `CLAUDE.md` is the authority. **A trailer is
still the right way to close an issue**, because it ties the closure to the
commit that earned it; the point is that a missed one is now recoverable
without waiting for Helen.

### 11.0.0 Prefer LARGER pull requests -- every merge is a deploy

Helen, 2026-08-24: "I have a soft limit on deploys per hour, so I prefer larger
pull requests where that's practical."

Every merge to `main` triggers `.github/workflows/build-and-deploy.yml`, so the
cost is per PR, not per commit. A run of tidy single-concern branches -- the
habit the branch workflow below otherwise encourages -- burns that allowance
fast for no benefit to her.

**So: accumulate related work on one branch and push once.** Fold small things
into whatever branch is already open rather than raising one of their own: a
handover note, a stray fix spotted in passing, a follow-up to something already
on the branch. **Keep separate COMMITS per concern**, so review stays readable
and any one thing can still be reverted alone. It is the PR count that costs.

Do not batch when batching is wrong. An urgent fix should not wait behind
unfinished work; genuinely unrelated changes that need independent review, or
that touch another agent's area, are still worth their own PR. **Say what is
being held back**, so she can ask for it sooner if she wants it.

### 11.0.2 `/tidy-drafts` — the mechanical half of a drafts pass, on request

**Added 2026-08-29 at Helen's request**: *"I also want a way of saying hey,
Claude, please tidy up my drafts files."* `.claude/commands/tidy-drafts.md` is
the procedure and `scripts/tidy_drafts.py` is the engine — the first project
slash command in this repo, and the first thing in `.claude/` that is not a
guard hook. `/ingest` (§11.0.3) is the second and copies its shape exactly:
a script that reports, a command doc that decides.

**RUN FOR REAL 2026-08-29**, in three commits, one per class. What it did, and
what the rules read afterwards:

| | before | after |
|---|---|---|
| scalar quoting | 295 drafts | **0** |
| `main_ingredients` quoting | 279 | **0** |
| `tags` quoting | 248 | **0** |
| en dashes | 58 | **0** |
| `meta:` three flags in order | 341 | **5** |

**All four zeroes were then ADOPTED as draft rules** (`test_drafts.py`, two-line
delegations) and removed from `NOT_FOR_DRAFTS`. That is the point of having
cleared them: without adoption the next ingest re-grows the backlog quietly and
the pass has to be run again for ever. The five remaining `meta:` files are
three carrying `claude_rewritten` (legitimate on a draft, forbidden on a recipe)
and two with no `awaiting_fix` at all, which is Helen's to set because that flag
fails closed.

**The boundary is formatting versus judgement, and it is the whole design.** It
fixes quoting, en dashes, `--`/`->`, accents and the #429 `meta:` migration. It
never resolves which milk, which flour, or whether an oven figure is the fan
one: ~25 rules and 600-odd hits, every one needing Helen or her source material,
all of them reported and left alone.

**A THIRD CATEGORY EXISTS AND TITLE/SLUG DIVERGENCE IS IN IT: not a fix, not a
judgement, NOT A FINDING.** The script reported a title whose head-clause words
are absent from the filename — 19 drafts, and 19 of the 21 lines it printed.
Helen ruled the whole class out on 2026-09-01: *"let's not run the 'title
matches slug'-ish test over drafts."* The reasoning is worth keeping because it
is the general shape of a false finding here. **A draft's title is still the
SOURCE's title, and the slug is already the dish.** `chocolate-fudge-cake`
titled "Cassie's Favourite Chocolate Fudge Cake", `swedish-meatballs` titled
"Bronte's Swedish Meatballs", `choc-chunk-cookies` titled "Malty NYC-style Choc
Chunk Cookies" — every one is the ingest doing exactly the right thing, keeping
the source's own words in `title:` while the filename names what the dish is.
The divergence closes itself at promotion, when Helen writes the title she
wants; and she mostly will, since her rule on possessives is *"I mostly dislike
'Cassie's Sunday Chicken' unless Cassie is either famous or a member of my
family."* The reporter is deleted, and `test_title_and_slug_dont_diverge` moved
in `NOT_FOR_DRAFTS` from the "real gaps" section to the deliberate-decline one.
**The recipe-side test is untouched** and still fires where it means something:
on a published page, where the title is hers. That is the second entry in that
registry found pointing the wrong way (the first was
`test_note_dicts_have_label_and_text`, 2026-08-29) — read a "GAP" label as a
claim to check, not a fact.

**It never touches a `QQ` line**, which is not a technicality: two thirds of the
corpus-wide en-dash hits are inside un-rewritten source text (86 of 130), and 22
files consist of nothing else. Verified on the real run rather than trusted: of
the 44 lines it changed, **zero begin with `QQ`**, counted from the diff.

**Every rule is imported from the test suite, never re-typed** — `META_ORDER`,
`RETIRED`, `SCALAR_STRING_FIELDS`. A fixer carrying its own
copy of the contract eventually tidies files INTO a shape the tests reject,
while looking green the whole time. That import is also what resolved the
`test_invisible_keys_are_really_invisible` failure the first draft caused
honestly, rather than by narrowing a guard that says in its own message not to.

Scope was settled with Helen and the exclusions are hers: size words (108
drafts) are out, cocktail drafts are out while that schema moves, and a missing
`meta.awaiting_fix` is reported rather than invented because that flag fails
closed and writing `false` asserts a recipe is fit to publish.

### 11.0.3 `/ingest` — the procedure, and the pre-flight that feeds it

**Added 2026-08-31.** `.claude/commands/ingest.md` is the procedure;
`scripts/ingest_preflight.py` is the engine. Same division as `/tidy-drafts`:
the script reports and never writes, the doc decides.

**WHAT THE PRE-FLIGHT IS FOR: one list, grouped by DECISION, not by file.**
Ingesting fifteen photographs means the same ruling arrives eleven times in
eleven files, and asking eleven times is how a session burns Helen's attention
on one question. The report gathers every decision a batch needs — undeclared
bottles, undeclared generics, garnish strings that are near-misses on the
vocabulary, method steps that already have a proposal, US units, unitless
amounts — and prints each one once with its instances under it.

**It imports every rule from `tests/`**, never re-typing one, for the reason
`tidy_drafts.py`'s own header gives at length: a checker carrying its own copy
of the contract eventually reports against a shape the suite has moved on from.

**THE ROUND TRIP, AND IT IS THE HALF THAT WAS MISSING UNTIL 2026-09-02.** The
standalone documents (see the header) describe what a repo-less session should
HAND BACK; nothing described what to do when the file arrives. Helen asked
directly — *"is this in the case where I get files back from a Claude web and
we need to ingest them properly once I'm back at a desk? Is the pipeline very
clear in the handover?"* It was not, and it is now the second section of
`.claude/commands/ingest.md`:

    she pastes INGEST_ONE_*.md + the recipe into claude.ai, away from her desk
      -> a draft file, plus a short "what I could not know" list
      -> saved into _food_drafts/ or _cocktail_drafts/ root, on a branch
      -> COCKTAILS: python3 scripts/derive_cocktail_moods.py --write
      -> pytest, then /tidy-drafts for food
      -> work the hand-back list as TIER 3 questions -- ask, never fill in
      -> ingest_preflight.py for a drink

**A FILE FROM A REPO-LESS SESSION IS 90% OF AN INGEST**, and what is missing is
exactly the parts that need this repository: `mood` (derived from
`taxonomy.yml`), `generic` and `suggestion` (a dictionary lookup, and Helen's
standing `QQ` anyway), a glass the source did not name, and whatever else its
list flags. **Do not redo the parts that are done** — its prose has already
been rewritten and re-rewriting it burns her review twice.

**THE COCKTAIL CASE FAILS A TEST ON ARRIVAL AND THAT IS EXPECTED.** `mood: []`
disagrees with `test_every_drinks_moods_match_the_derivation` until the deriver
runs. Proved end to end on 2026-09-02 rather than assumed: the worked example
was copied into `_cocktail_drafts/`, failed exactly that one test, and
`derive_cocktail_moods.py --write` turned it green — 125 drinks, 124 already
agreeing, 1 written.

**THE PLAYTEST CHANGED THREE THINGS, and the third is the useful one.**
Absences became NEAR-MISSES, because "this garnish is undeclared" is noise and
"this is one word off `lime wheel`" is a decision. Steps already in
`methods.yml`'s proposals stopped being reported, since that map is the queue
for exactly them. And **the `star_ingredient` check was deleted outright**: it
fired on 118 drafts, about a third of the corpus, which §7 documents as
correct — a blank star is the right answer for a plain sponge — and §12 uses
that exact field as its worked example of a false finding. A check that fires
on a third of the data is describing the data, not auditing it.

### 11.0.1 More than one agent now shares this checkout — use a worktree

2026-08-23. A session went to branch and found the working tree already on
someone else's branch with an uncommitted file in it. **Do not stash, move or
commit another agent's uncommitted work**, and do not switch branches out from
under it. Take a worktree instead:

    git worktree add .claude/worktrees/<name> -b <branch> main

That gives a clean checkout of `main` in its own directory, leaves the shared
tree completely untouched, and is removed with `git worktree remove` once the
branch is merged. `.claude/worktrees/` already holds others.

**One catch, and it will look like the drafts have vanished.** The nested
private drafts repos (`_food_drafts/`, `_cocktail_drafts/`) are gitignored here,
so a fresh worktree does not contain them and a build from it renders an empty
index. Symlink the one you need:

    ln -s /home/helen/projects/helen-triages/_cocktail_drafts _cocktail_drafts

The symlink is itself covered by `.gitignore`, so it cannot be committed by
accident.

### 11.1 A file with a colon in its name will crash the whole build

WSL writes `<name>:Zone.Identifier` beside anything dragged in from Windows.
Jekyll reads the colon as a URI scheme separator and `jekyll-sitemap` dies
with a raw Ruby backtrace that never names the file — only crashes on names
that aren't legal schemes, so it can lurk harmlessly for weeks.
`_config.yml` excludes `"*Zone.Identifier"`. If a build dies in `addressable`
with `Invalid scheme format`, `find . -name "*:*"`.

### 11.2 Do not trust this document over the code

Past versions have been wrong in specific, costly ways: a module described as
existing that was actually unmerged on a different branch; a deploy workflow
recorded as "written and waiting" that didn't exist at all; a companion-docs
table that listed a file nobody had ever written, for three versions running,
because nobody checked. **If the code and this file disagree, the code wins,**
and the fix is to correct this file, not to trust it harder next time.

> ### AN OPEN ISSUE IS A DOCUMENT TOO, AND IT ROTS FASTER
>
> **MEASURE ANY ISSUE OLDER THAN A DAY BEFORE ACTING ON IT OR REPEATING IT.**
> Not "read it carefully" — run the numbers in it against the data.
>
> Helen, 2026-08-31, on being asked about something settled for the third
> time: *"I saw Kamaniwanalaya and Swizzle and felt annoyed again — have we
> not settled this? Now three times or more?"* She was right, and the cost of
> being wrong here lands on her rather than on the suite.
>
> **The instance that earned this box.** #600 was raised on 2026-08-30 by
> copying #542's "Also outstanding" section, written 2026-08-27, without
> re-measuring a word. Four days. Every claim in it was false by the time it
> was written: six drinks said to carry a half-empty disjunction — **zero**
> did, four of them had no list `generic` at all any more; a drink said to
> need a decision — Kamaniwanalaya — **already had the exact fix requested**;
> a second drink, `swizzle`, **no longer existed**, having become the
> Martinique Swizzle; and two suggestion strings quoted as outstanding were
> **not in `unresolved_suggestions` any more**.
>
> **The same day it also named `caramel-forward Jamaican rum`** — a style
> settled twice, and one for which `hers_to_apply` plus
> `test_no_drink_uses_a_generic_that_is_helens_to_apply` had been built THAT
> MORNING precisely so it could not come back. The guard held; the prose went
> round it. **A mechanism stops the data regressing and does nothing about an
> agent re-raising the question in words.**
>
> Why an issue rots faster than this file: nothing re-reads it. This document
> gets corrected when a session trips over it, and every guard in `tests/` is
> re-run on every commit — an issue body is written once and is never
> executed, so it records the collection on the day it was typed and says so
> nowhere. **Its age is the only warning you get.**
>
> Three minutes of measuring closes a stale issue outright. Repeating it costs
> Helen the same conversation for the third time.

### 11.2.1 Do not ship a layout at a size you cannot look at

**Issue #539, at Helen's request, from a near-miss rather than a bug.**

> **If a change only manifests at a size, state or device you cannot produce,
> building a way to SEE it is part of the work, not overhead.**

#483 asked how the cocktail cards should behave on a narrow screen. Three
candidate layouts shipped behind a `?narrow=` switch under
`@media (max-width: 400px)` — and **neither Helen nor the agent could look at
any of them.** A desktop window will not drag narrower than about 500px; device
mode reflows correctly but shows one option at a time, and "is stacking better
than just making it smaller" is a *comparison*; and her actual device is an iPad
at 768–834px, where a 400px breakpoint never fires at all.

**That is worse than picking the wrong layout, because it looks like progress
and produces no decision.** One of the three was also broken outright — the
`title` variant ran its ingredient line underneath the glass panel, hiding the
first words of every card. Obvious in a screenshot, invisible in the source, and
it had been committed and pushed.

**What fixed it: a dev page of iframes at fixed CSS widths** (360 / 390 / 320).
An iframe carries its own viewport, so `width: 360px` is a genuine 360px layout
whatever the screen around it is — it works on the iPad, on a desktop, at any
window size, and puts the candidates side by side. Helen found the bug in one
look, chose `stack`, and the page went with the losing variants.

The trick generalises to anything viewport-conditional: breakpoints, and by the
same argument (though an iframe cannot print) print. It sits alongside the
existing comparison-switch convention — build the options, let Helen look, then
**delete the losers and the switch** — because this near-miss is exactly what
happens when the first half is done and "let Helen look" is assumed rather than
provided for.

**There is no browser in this environment**, which is what makes this a rule
rather than a nicety: an agent cannot check its own narrow-screen work at all,
so the only way anyone sees it is if a way to see it is built.

### 11.3 CSS naming — flat noun for the thing, `--modifier` for its state

Not a split that needs unifying (issue #131 is still open on GitHub — a
2026-08-10 commit's `Closes #128, #131` trailer never actually closed it,
and cited a HANDOVER "CSS naming section" that didn't exist until now). Two
registers, both deliberate:

- **Flat hyphenation names the thing**: `recipe-meta`, `ingredient-pill`,
  `btn-ingredient`, `category-label`. This is the default and covers most of
  the codebase.
- **A trailing `--modifier` flags state or variant on that thing**, real BEM
  (base class always present alongside the modifier, never standalone):
  `ingredient.ingredient--annotated`, `category.category--star`,
  `badge.badge--matched`, `ingredient-pill.ingredient-pill--pantry`. Confirmed
  2026-08-12 by checking every `--`-suffixed class site-wide for its base
  class — 8/9 had one. Helen's own read on this, then verified: the person
  who introduced `--modifier` classes meant it as a real pattern, not drift.
  `8f9eb52` (2026-08-02, also Helen's) already established this narrowly for
  the recipe page — turned out to hold site-wide.
- **This is why the icon-coverage test only checks the BASE class** (#396,
  2026-08-21). `test_every_icon_partial_class_has_a_styled_base`
  (`test_rendered_pages.py`) reads the class attributes out of
  `_includes/**/*.svg` and requires the part before `--` to have a rule in
  `food.css` or `cocktails.css`. **31 of the 41 classes there are modifiers
  whose base carries the styling**, so demanding a rule for every modifier
  would fail on correct code. The cost is stated rather than hidden: a typo in
  the MODIFIER half is invisible to it. It catches the failure that actually
  happened — an icon naming a class the stylesheets had never heard of, which
  renders unstyled at whatever size the surrounding flow gives it.
- The one exception was a real bug, now fixed: `.ingredient--matched` in
  `_recipe-list.scss` had no `.ingredient` base (the pill's actual base is
  `.ingredient-pill`) — same defect class `8f9eb52` fixed elsewhere. Renamed
  to `.ingredient-pill--matched`.
- BEM **element** syntax (`__content`) is different and *was* a real
  inconsistency — fixed in the same 2026-08-10 commit
  (`.badge-group__content/__meta` → `.badge-group-content/-meta`).
- **Do not attempt a big-bang rename.** The issue text says so directly:
  "apply opportunistically, not as a big-bang rename across ~1,400 lines for
  no functional gain." A prior architecture review (2026-08-12) drafted a
  full file-by-file migration plan before this check ran — don't resurrect
  it; the premise (BEM-as-drift) didn't survive checking the base classes.

---

## 12. Traps you will fall into

**You will flag `QQ` as an error.** It's Helen's deliberate placeholder.
Never flag it, never fix it, never convert it.

> ### FOUR THINGS THE BROWSER DOES THAT NO TEST HERE CAN SEE, 2026-09-02
>
> All four shipped green, all four were found by Helen looking, and all four are
> facts about CSS or the UA rather than about this repo.
>
> **1. AN `<input>` DOES NOT INHERIT `color`.** It takes the UA stylesheet's
> `fieldtext`, which is near-black whatever its ancestors say. So when the
> cocktails palette inverted, every element on the page took the new colours for
> free through inheritance and the search inputs silently did not — typing
> produced **black text on a black ground**, invisible rather than absent.
> Nothing could see it: the class has a rule, and the contrast guards do not read
> form controls. **The same is true of `background`, `font-family` and
> `font-size` on form controls.** Set them explicitly or they are not set.
>
> **2. `text-shadow` PAINTS UNDER TEXT DECORATIONS, NOT JUST GLYPHS.** The card
> title's punched lettering casts a near-white copy up-and-left, and that copy
> landed on the search-hit UNDERLINE too — a purple line with a white line beside
> it. The fix is not to remove the shadow (that would unpunch the matched letters
> mid-title) but to stop the mark being a decoration: it is a `linear-gradient`
> background now, which is §13.1's own device and is not painted by a shadow.
>
> **3. `<mark>` ARRIVES WITH A UA BACKGROUND AND COLOUR** — `Mark`, a hard
> yellow, and `MarkText`. `background: none` resets it; `background-image:` does
> **not**, because it only sets the image and leaves the colour underneath.
> Swapping the shorthand for the longhand brought the yellow back an hour after
> the rule's own comment warned about it. **Use the `background` shorthand for
> anything that paints a `<mark>`** — it resets the colour as part of setting the
> image, so the guard is in the syntax.
>
> **4. A PROPERTY DECLARED TWICE IN ONE BLOCK IS INVISIBLE TO
> `test_no_selector_declares_the_same_property_twice`.** That guard compares
> SEPARATE blocks, and it is genuinely good at that — it caught a second
> `.btn-clear-filter { color: … }` within a minute. But `@include` a mixin and
> then override one of its values, and both land in one block with the mixin's
> sitting dead. That is why `index-section-label` takes `$size` and `$tracking`
> now: **arguments rather than an override after the include.**
>
> ### FIVE TRAPS FROM ONE DESIGN SESSION, 2026-09-02, AND THEY SHARE A SHAPE
>
> The black-on-black work (#469) took nine rounds of Helen looking, and **five
> of those rounds were spent on bugs I introduced rather than on the design.**
> Every one was in a hand-built replica of the card's CSS in a dev page's
> `<style>` block. The real card had none of them. Her own diagnosis was the
> right one — *"the tape was perfect in layout earlier, and since we've been
> changing colours, yet the layout has been all over the place"* — and the
> answer was to stop replicating and build it for real.
>
> **1. A STRAY `*/` IN AN INLINE `<style>` FAILS SILENTLY.** Prose written after
> a comment had already closed left NINETEEN unbalanced delimiters; the parser
> inverted at the first one and read comments as CSS and CSS as comments for the
> rest of the block. `--tape-pad-top` was never declared, so `padding:
> var(--tape-pad-top) …` was invalid at computed-value time and computed to its
> INITIAL value — zero, on all four sides. The same slip in a `.scss` file is a
> loud build error. **This is §12's Liquid-comment trap from the parser side**,
> and it is the one that costs somebody else's time rather than your own.
> Corollary, learned the same hour: **you will break a rule again while
> documenting the fix for it.** I repeated the identical slip writing the
> explanation of it.
>
> **2. GIVE EVERY `var()` IN A SHORTHAND A FALLBACK.** One unresolvable custom
> property does not lose one value — it invalidates the whole declaration. A
> fallback turns a silent catastrophe into something merely a little off.
>
> **3. A CUSTOM PROPERTY CONTAINING `var()` IS SUBSTITUTED WHERE IT IS DECLARED,
> NOT WHERE IT IS USED.** `--tape-pad-top` was declared on an ancestor, so its
> `var(--tape-pad-y)` resolved against THAT element's value and inherited down
> frozen, while the sibling declaration read the live one on the tape itself.
> Two paddings that were supposed to move together stopped doing so. Invisible
> at the default, because there the stale value is the correct one.
>
> **4. RETYPING A WORKING LINE IS NOT COPYING IT.** `decorations.js` had drawn
> this exact artwork for weeks with
> `'<svg preserveAspectRatio="none" height="100%"'`; I retyped it from memory
> and dropped the height. The tape files carry `width="100%"` and no height, so
> the element LETTERBOXED — a narrow tape drew far shorter than its box while a
> wide one filled it. **Two elements on one page disagreeing is the tell**, and
> it was in the screenshot before I saw it.
>
> **5. COMPENSATE FOR A FACT ABOUT OBJECT A ON OBJECT A.** Three rounds went on
> centring the tape's lettering by nudging the TEXT, which needs the typeface's
> real ascent and cap height — unavailable, since Courier Prime ships here as
> woff2 only. The band's offset is a fact about the ARTWORK and correcting it
> there (`top: -1.765%`) needs no estimate at all.
>
> **AND THE MEASUREMENT THAT DISAGREES IS MEASURING THE WRONG THING.** Told
> twice that the tape was "still small", I measured the box, found it correct,
> and reported that its proportions were already more generous than the header
> wordmark's. Every number was right. All of them were arithmetic about a BOX
> and none was about what was being PAINTED in it. **When the person who can
> see it says the same thing twice, stop defending the measurement.**

**You will WRITE DOWN a rule instead of following it, in the same file, in the
same minute.** 2026-08-19, and it is the most humbling entry here. Moving
`about.html` to the repo root took it out of the `_config.yml` default that
supplied its `site_key`, so the key had to be set by hand. A comment was written
into that file's front matter saying exactly this — four sentences, citing §2.4,
naming the consequence — and the `site_key: food` line was never added. The page
shipped with no stylesheet at all and the whole suite passed over it.

The general form, which is worth more than the instance: **writing an
explanation of a constraint feels like satisfying it.** The comment and the code
are two separate acts and the first one is the one that feels like completion.
If you find yourself documenting why something must be done, do it first, then
write the comment — and if the constraint is worth four sentences, ask what
would fail if it were violated, because that question is a test.

**You will make markup shared and leave its CSS forked.** 2026-08-19, issue
#374. The header and footer came from one shared template, and on cocktails the
two nav icons rendered as raw unstyled SVG, because their rules lived in
`_sass/food/`. Every check passed: the markup is shared, the classes have rules
(in `food.css`, which is the only stylesheet
`test_every_class_we_emit_has_a_rule_in_the_stylesheet` reads), every link
resolves. **"Shared" is a claim about three layers, not one** — markup, cascade
and assets — and it is only true when all three hold. See §2.5.

**YOU WILL MEASURE THE WRONG LAYER AND REPORT THE ANSWER AS A FACT.**
2026-08-31, and it is the sharpest one on this page because the measurement was
real, the numbers were right, and the conclusion was false. Helen said she was
"9/10 sure" the food picker suppresses a bare `chicken` chip when `chicken
(all)` is offered. I called `ingredient-search.js`, asked what it returned, got
the bare chip in 54 places, and told her food had no such rule. **It does —
issue #51 — and the suppression is in `filters.js`, at render time.** The module
offers the entry and the wiring drops it. So the check exercised the layer that
does not implement the rule and reported its absence.

**A measurement is only evidence about the layer it ran through**, and she was
looking at the page, which is the only layer that settles anything. Before
reporting that a behaviour does not exist, ask which file would implement it if
it did — and if the answer is the DOM wiring, §10.2's harness or a screenshot is
the check, not a module call.

**A SOURCE-SCANNING GUARD WILL BE FOOLED BY THE PROSE EXPLAINING IT.** SIX
times on 2026-08-19–31, in six unrelated places, which is what promotes this
from an anecdote to a rule:

1. The destructive-git hook (§11.0) refused the commit that introduced it: the
   message described the commands it blocks.
2. `test_both_ingredient_pickers_mark_their_word_matches` counted
   `r.hasWordMatch` in `filters.js` and passed while broken, because the comment
   written directly above the function it guards names that flag twice.
3. `test_every_draft_reading_test_says_what_it_does_without_drafts` flagged
   ITSELF — a test about draft-reading tests necessarily writes the corpus name
   in its own docstring and in the line that looks for it.
4. That same test then misclassified two others, because "does it skip?" asked
   whether the word "skip" appeared, and their docstrings explain that they
   deliberately do not.
5. `test_invisible_keys_are_really_invisible` (§4.0) word-grepped the render
   surface, and one comment in `ingredient-search.js` using the English word
   "rewritten" kept `meta.rewritten` off `INVISIBLE_KEYS` for two days. Fixed
   2026-08-21, issue #428.
6. `test_a_filter_state_binding_is_only_asked_for_what_it_has` (§3) failed on
   the paragraph explaining the bug it was written for — that comment names
   `FilterState.arrivedByGoingBack`, which is precisely the string it hunts.
   2026-08-31, within a minute of the guard existing. It imports
   `test_front_matter._strip_comments` rather than growing a second stripper.

**A test that greps source cannot tell code from commentary**, and the
commentary explaining a rule is exactly where that rule's vocabulary is densest
— so this is not a rare collision, it is the likely one. In ascending order of
robustness: strip comments and quoted spans before counting; match a call SHAPE
rather than a name; or parse the AST and ask the syntax tree, which is what (4)
ended up doing and which cannot be fooled by prose at all.

**STRIPPING STRING LITERALS TOO IS THE OBVIOUS NEXT MOVE AND IT IS A BUG.** (5)
strips comments and deliberately KEEPS strings, because a string literal is
exactly how a key gets read — `page["source_type"]`, `data['meta']['rewritten']`.
Losing one turns a real read into a silent miss, which for that guard is the one
direction it must never fail in. Strings are still *tracked*, so the `//` inside
`"https://..."` is not mistaken for a comment start, but their contents survive.
**Ask which direction a given guard must fail in before deciding how aggressively
to strip.**

Every one was caught by breaking the thing on purpose and watching. **Read the
output, not the exit status** — (2) printed nothing at all, which is the only
reason it was noticed.

**AND THE SAME COLLISION RUNS THE OTHER WAY: A PARSER WILL READ YOUR
DOCUMENTATION AS CODE.** 2026-08-26, building the magic bag (§4.3). Liquid
**tokenises tags inside a `{% comment %}` block** rather than treating the body
as text, so a comment that quotes a bare `if` tag in full — written to explain
what the code below it does — is a real syntax error that takes the entire
build down. Everything above is about prose being mistaken for code by a guard
that greps; this is prose being mistaken for code by the actual parser, and it
fails immediately and loudly rather than silently, which is the one mercy.
**In a Liquid comment, name a tag rather than writing it out** (`an include
tag`, not the tag itself); `{% raw %}` works but is easy to forget when you are
mid-sentence. The general form: before quoting syntax inside a comment, ask
whether the thing that reads this file parses comments or skips them.

**YOU WILL ADD A NEW LINK SHAPE AND NOTHING WILL BE WATCHING IT.** Recipes had
two: `](../slug/)` and `](../reference/slug/)`, each with its own guard. Issue
#353 added a third, `](#fragment)` — a tagline linking down into that page's own
longform — and with the ganache tagline pointed at `#nonexistent-anchor` the
whole suite passed. 18,886 green over a link that goes nowhere.

**A wrong fragment does not 404**, which is why it needs a test at all: the page
loads and the browser sits at the top, so it reads as "the scroll didn't work"
or, worse, as a recipe with nothing further down — on a tagline that has just
promised there is. This repo had already been bitten by that one shape over, and
says so in `test_page_links.py`'s own docstring
(`../temperatures/#steak` when the real id was `#beef-steak`) — but that scanner
reads TEMPLATES, and a tagline is front matter, so it never looked.

`test_same_page_fragment_links_land_somewhere` closes it. **Its obvious version
was wrong and failed thirty recipes**: reading ids out of the recipe file is
right for body headings, which are raw HTML (§4.1), and misses `#doneness`
entirely — that id belongs to `_layouts/recipe.html`. Ids flood outward along
the layout and include edges, which is the fact `_ids_visible_from()` in
`test_page_links.py` already encodes; meeting it from the other direction cost
two rounds.

**You will trust a corpus glob that names files instead of finding them.**
`test_page_links.py`'s page list was `food/**`, `cocktails/**` and the literal
`[ROOT / "index.html"]` — correct on the day it was written, when the redirect
was the only root-level page there had ever been. `about.html` arrived beside it
and was invisible: every link to `/about/` read as pointing at nothing
published. That failure at least announced itself. **The mirror image is the one
to fear** — a page the corpus cannot see is also a page whose own outbound links
are never scanned, and that direction is silent. This is the same family as the
stale `JS_DIR` and the non-recursive SCSS glob below, wearing a different mask:
not a pattern that went stale, but a list that was never a pattern.

**You will re-add a hardcoded search threshold.** It lives in
`FAMILY_BUTTON_MIN_CHARS`, read from `ingredient_words.yml`'s
`search.family_button_min_chars`. A test fails if a literal reappears in
either JS file.

**YOU WILL SCOPE A GUARD BY THE VALUE IT IS POLICING, AND IT WILL NOT SEE THE
RIVAL VALUE.** 2026-08-31, and it is a sharper cousin of the entry below.
`test_no_garnish_is_stated_as_none_and_nothing_else` existed to stop a second
spelling of "this drink takes no garnish" — its docstring says so outright. It
opened by skipping any drink whose garnish list did not CONTAIN `none`. So
`ti-punch`, which said `no garnish`, was invisible to it: the one drink in the
collection actually committing the fault the test was written to prevent, waved
through by the test's own first line, for however long it had been there.

**The general form: a guard that filters on the canonical value can only ever
see drinks that are already right.** Everything wrong is, by definition, spelled
differently — which is what put it outside the filter. Anchor on the FIELD and
ask what it holds, not on the value and ask whether it is well-formed. Same
family as the stale `JS_DIR` below, but it fails on a corpus that is fully
present and a pattern that is not stale, so nothing about it looks wrong.

**AND YOU WILL ASSERT A REGISTRY IS NON-EMPTY WHEN EMPTYING IT IS THE GOAL.**
Same day, my own guard, wrong within a day of being written. `garnish.yml`'s
`proposals` block is a WORKLIST — rows are resolved by deletion, in either
direction — so a full map is the temporary state and an empty one is the settled
one. Asserting it non-empty made finishing the work a test failure.

**A ratchet list and a worklist look identical and want opposite assertions.**
`GLASSLESS_ON_2026_08_27` empties and must STAY empty, so its sibling asserts
emptiness. `proposals` empties and will refill, so it must assert only that the
KEY exists — the thing whose silent loss would switch the check off for whatever
is proposed next. Ask which kind you have before writing `assert thing`.

**A DECLARED EXCEPTION SILENCES EVERY CHECK DOWNSTREAM OF IT, NOT ONLY THE ONE
IT WAS DECLARED AGAINST.** 2026-09-02, #585, and it is the sharpest thing that
pass found. `unresolved_suggestions` exists to say "this string names no bottle
yet" so `test_every_suggested_bottle_resolves` bites on the next one. But a
string that resolves to no bottle also resolves to no CATEGORY — so #534's
cross-category check silently skipped every drink carrying one. Royal Bermuda
Yacht Club had been suggesting a `clear blended multi-region rum` against a
generic asking for `lightly aged and filtered` for as long as the string was
prose, and nothing could see it. Declaring the bottle made the second check
fire within seconds.

**An exemption is a hole in every rule that reads the same field**, not just in
the rule that granted it. Before adding one, ask what else consumes that value
and what those checks will now not see — and when you retire one, expect
something unrelated to go red, because that is the coverage coming back.

**AND A REGISTRY OF DECLARED FAILURES NEEDS A STALENESS GUARD OR IT ROTS
SILENTLY.** The same block held seven rows naming strings no drink said any
more — finished work still reading as outstanding, and still exempting those
strings for whoever wrote them next. `test_every_suggested_bottle_resolves`'
own docstring said "deleting a line there is how one gets retired — the same
shape `methods.yml` uses for its proposals", and methods.yml had a test
enforcing exactly that while this file had only the sentence. **A convention
stated in a docstring is not a convention anybody follows.** Both have the
guard now; `KNOWN_PROSE_SUGGESTIONS` is empty and `unresolved_suggestions` is
down to 16.

**YOU WILL EXEMPT YOUR OWN WORK FROM A RULE WRITTEN FOR SOMEBODY ELSE'S.**
2026-08-31, eleven days late. House style deliberately stops at a `QQ` line
(§5): that is the source's wording, and correcting its dash edits words about
to be deleted. The interleaved format then introduced `QQ Claude`, which is
**our** prose — and both guards matched any line starting `QQ`, so Claude's
own writing sat behind an exemption written for a copyright holder's. §4 said
in plain English that `QQ Claude` "IS held to normal house style". The
sentence was right; the regex never implemented it.

**The exemption was never wrong. The pattern was**, which is why the fix is a
lookahead and not a carve-out. When a marker gains a second meaning, go back
to every pattern that matches the first one: a prefix rule silently widens to
cover whatever is added after it.

**AND A GUARD THAT HAS NEVER FIRED MAY ONLY BE STARVED.** The hole existed for
eleven days across 32 drafts and showed nothing. ~1,000 new `QQ Claude` lines
in one day surfaced 15 hidden violations immediately. **Coverage is
proportional to traffic**, so a quiet rule is not thereby a proven one. Before
scaling an operation tenfold, ask which guard is about to see real volume for
the first time.

**A `git fetch` IS ONLY GOOD FOR THE MOMENT YOU RAN IT.** 2026-08-31, and it
is embarrassing because the discipline was being quoted elsewhere in the same
session. A fetch ran, four tool calls of other work happened, and the branch
state from before was then reported as current — wrong in one direction, and
after Helen said "I thought I'd merged that", wrong in the other. **Re-fetch
immediately before reporting**, and say what the fetch showed rather than what
you remember it showing. `git log --branches --not --remotes --oneline` is the
sweep; its answer expires the moment anyone else pushes.

**You will write a test that cannot fail and not notice.** The most dangerous
trap here because the symptom is green. Has happened four times now: a stale
`JS_DIR`, a non-recursive SCSS glob (both a path/pattern going stale after a
file move, silently matching nothing); `garam-masala-powder.md`'s
`method_groups` using `step:` (singular) with no `name:` — `test_method_
xor_method_groups` only checks which top-level key is present, not its
internal shape, so `recipe.method_steps` silently returned `[]` and every
prose-scanning test saw nothing to check (fixed by
`test_method_groups_have_name_and_steps` / `test_method_produces_actual_
steps`, `test_front_matter.py`, 2026-08-10); and `indian-mutton-raan-roast.
md`'s tagline linking to `../garam-masala-powder.md)` — a shape neither
`test_internal_recipe_links_resolve` nor `test_internal_links_have_trailing_
slash`'s regex considered at all, since both require a slug of exactly
`[a-z0-9-]+` (fixed by `test_internal_links_are_well_formed`,
`test_taxonomy.py`, 2026-08-10). **When you add a guard, break the thing it
guards and watch it fail.**

**The fifth, 2026-08-14, written by a session that had just read this
paragraph.** Worth recording in full because it is the first one where the
vacuous test was the GUARD ITSELF, not an older test going stale — and
because the mistake looked like ordinary care at the time. Asked to stop the
print stylesheet flooding every sheet with `$color-bg`, that session deleted
the print block's own `background: $color-bg` line — which changed nothing,
because `shared/_base.scss` sets `body { background: $color-bg }` for the
screen and that rule is still in the cascade inside `@media print`.
**Removing an override is not overriding.** Helen found the tint still
printing.

The fix came with a new guard, `test_print_neutralises_the_screen_page_
background`, which asserts that whatever paints the ground for the screen is
answered in print. It was broken on purpose to check it bit — **and it
passed while broken**. `_top_level_blocks` matched only selectors starting
with `.#%&`, so a bare `body` was invisible to it: the scan found nothing to
neutralise, hit an `if not paints_ground: return`, and reported green. Two
separate vacuity bugs stacked — a matcher that could not see the thing, and
an early return that turned "found nothing" into "nothing wrong".

Two things came out of it, and the second is the more useful:

- `_top_level_blocks` now matches element selectors too. `body`, `a`,
  `main` and `h1, h2, h3` — every bare element rule in `shared/` — had never
  been seen by anything built on that helper, including
  `test_no_selector_declares_the_same_property_twice`. Widening it surfaced
  no pre-existing duplicates.
- **Never `return` early because a scan came back empty. Assert it is
  non-empty instead**, with a message saying what to do if the emptiness is
  legitimate. This is the sharper form of the `assert js_files` /
  `assert found_any` / `test_sass_files_are_actually_found` pattern already
  used in several places. An early return *looks* like care — "nothing to
  check, so nothing to fail" — and is precisely how a test stops testing
  with no symptom. `tests/test_suite_hygiene.py` enforces it for any test
  that is not parametrised per recipe/draft (a per-item test may return
  early: the other 80 parametrisations still exercise the predicate). It
  cannot see the subtler variant — a per-item test returning early because a
  shared *reference* set is empty — which `test_accents_in_prose` was doing
  until the same day, silently able to disable the accent rule across the
  whole collection if `accented_words.yml` ever lost its `words:` key. Both
  now assert.

**You will assume "end of `<body>`" means "loads first".** It doesn't in a
layout that renders `{{ content }}` above its own scripts — a page layout's
scripts land *inside* content, above `default.html`'s closing scripts.
`assets.js` now loads at the end of `<head>` specifically so `window.HTF`
exists before anything else runs;
`test_assets_js_loads_before_any_other_script` and the analogous
`ingredient-search.js`/`recipe-list.js`-before-`filters.js` guards exist
because this bit for real once, silently, for weeks.

**You will assume you know how many stylesheets import `shared/`.** Two, as
of 2026-08-15 — `food.scss` and `cocktails.scss`. It was three until then,
and the third is why this entry exists at all: `root.scss` styled the
landing page, belonged to neither site, and was the one nobody thought
about. Moving the punched-tape mixin into `shared/_rule.scss` (§13.8)
needed a new `@import` before `shared/_layout.scss` in all three; the first
attempt updated food and cocktails and missed root, which doesn't fail
loudly at compile time for the two you remembered — it fails the *next*
time someone builds or visits the one you didn't, with a Sass error that
names the mixin, not the missing import.

`root.scss` was deleted with the landing page (§2.2, issue #204), so that
specific trap cannot fire again. **Keep the habit anyway**: grep for every
`@import "shared/` site before assuming you've covered them. The number is
a fact about the repo on the day you read this, and it has already changed
twice.

**You will move a colour and strand the numbers tuned against it.** A number
tuned for a colour belongs to the colour, not the place it happens to be —
bit twice in one session moving aureolin between filter slots, and again this
session building the category-code bar: `-active` tokens are tuned for
*text on a fill*, not a bare colour swatch, and using them for a solid bar
just reads as dark; darkening several warm hues together pulls them toward
the same muddy brown, which is exactly wrong for something that has to stay
distinguishable as a code. When you move or reuse a colour, grep for every
value derived from it and recheck each by eye.

**You will give an element asymmetric padding to compensate for something,
and find it's invisible until a much later change makes it not.** Bit for
real 2026-08-02: `.site-logo-top` had `padding-right: 0.18em` alongside
`letter-spacing: 0.18em`, presumably meant to balance the trailing gap
letter-spacing already adds after the last character — it didn't balance it,
it doubled it, and nobody could tell, because the element always defined the
width of its own container, so there was no larger frame for the lopsidedness
to show up against. It became a visible shift the moment a later change (the
wordmark redesign, §13.8) let something else define that width instead.
**Any padding, margin or inset that's asymmetric "to compensate for X" is
only ever verified relative to whatever's true TODAY** — if the element's
box and its container's box might ever stop being locked together, check the
asymmetry still makes sense once they aren't, not just that it looks right
right now.

**You will assume every SVG is formatted the way the last one was.** Two
different exporters are in use — most decorative folders open with `<svg `
(space), `backgrounds-headers/`'s 100 Inkscape exports open with
`<svg\n   width="…mm"`. A literal `'<svg '` match silently no-ops on the
second kind — no error, just subtly wrong output, because a failed
`String.replace` returns the input unchanged. Match `<svg` plus whitespace,
not a specific character.

**AND YOU WILL READ ONE TRANSFORM WHERE THERE ARE TWO.** 2026-08-31, #599, the
same family one level deeper. `svgrender.parse_icon` pulled the first
`<g transform="translate(…)">` out with a regex; four icons nest a
`<g transform="matrix(…)">` holding the bowl, and that matrix was silently
dropped — so every measurement of those four read their geometry in the wrong
place, and the normaliser then fitted their canvases to what it had mis-read.
`normalise_glass_icons.py`'s `_emit` had the mirror bug: it re-emitted a
transform on a `<g>` and dropped one on a `<path>`, which on Helen's pineapple
(a negative y scale) would have flipped the drawing rather than nudging it.

**Both failed in the direction that looks fine.** The bowl still landed
somewhere inside the canvas, so the slack-viewBox guard measured a healthy
97.5% fill while 11.8 units of rim sat outside the frame entirely. **A
transform is a stack, not an attribute** — compose the ancestors, and prefer
baking the result into the geometry so a caller cannot apply half of it.

**A CROSS-REFERENCE TO ANOTHER FILE'S BEHAVIOUR IS A CLAIM NOTHING RE-CHECKS**,
and the same day proved it: three separate comments said the card template
"raises every ratio to a power" and it never had. One of the three was an
INSTRUCTION to reach for that curve. Grepping finds the comments asserting the
claim, not the code — `git log -S` over the file that would have to implement
it is the check that works. See §9.13.

**You will rename something and silently un-ignore it.** `.gitignore`
matches by directory *name*. `test_every_drafts_collection_is_gitignored`
derives the expected patterns from `_config.yml` so this can't recur quietly
— it already has once, for real, for 229 files.

**A "GENERATOR" MAY HAVE STOPPED GENERATING, AND ITS OWN DOCSTRING MAY NOT
KNOW.** 2026-08-21, a near-miss caught only by taking a backup first.
`_data/food/cooking_methods.yml` was produced by two scripts in `scripts/`, and
both said, at the top: "The data file is the source of truth from here on; edit
it directly, or edit this script and re-run." The second half was false and had
been for eight days. The file had been hand-edited since — a whole `venison`
section and its own header comment, neither of which exists in the pinned page
the scripts parse — so a re-run does not REGENERATE it, it OVERWRITES it,
dropping 166 lines. The data file's own header already said "leave those scripts
alone"; the scripts contradicted it, and the scripts are what you read when you
are standing in `scripts/` wondering how to change three characters.

**Two habits come out of it.** Before running anything that writes a tracked
file, run it once and diff — or copy the file to `tmp/` first, which is what
turned this from a loss into a paragraph. And when a generator's output becomes
hand-editable, fix the comment in the GENERATOR, not only in the output: the
person about to re-run it is by definition reading the wrong one.

**YOU WILL ASK "IS ANYTHING UNPUSHED?" OF THE BRANCH YOU HAPPEN TO BE ON.**
2026-08-29, and it cost one of Helen's own edits. She answered a flag by editing
a draft; that was committed, and the session then created a different branch
without pushing it. The PR merged everything up to the commit before, so `main`
took the value she had just corrected away.

**The status sweep run at the end reported `unpushed=0` and was believed.** It
used `git log @{u}..HEAD`, which asks only about the CURRENT branch — a branch
walked away from is invisible to it. Same shape as the `git branch
--show-current` failure `CLAUDE.md` records: **a check narrow enough to miss the
thing it exists to catch is a narration, not a check.**

    git log --branches --not --remotes --oneline     # every unpushed commit, any branch

It was recovered because `git branch -d` refused with "not fully merged" and the
refusal was READ rather than overridden with `-D`. On a squash-merged branch that
refusal is routine and the reflex is to force it — do not, until you have
diffed the branch's file against `main` and know what is in it. Squash merges
make `-d` unreliable in exactly the situation where `-D` is unrecoverable.

**YOU WILL READ THE PATCH AND THINK YOU HAVE CHECKED THE OUTPUT.** 2026-08-29,
building `/tidy-drafts` (§11.0.2). Its `meta:` rewrite scanned the block as
"indented or blank", which swallowed the trailing empty line that splitting on
newlines always leaves — so every file came out ending `proofread: false---`
and **341 of 342 drafts stopped parsing at all**. The diff looked entirely
plausible: the right two lines gone, the right three in the right order, and
nothing in a unified diff draws your eye to a newline that is no longer there.

It was caught by parsing both sides and diffing the PARSED front matter, not by
reading the change. **For anything that rewrites structured text, the check is
to load the result, not to look at the patch** — and the same pass is what
proved the quoting was a genuine no-op on the data, which is the other thing a
diff cannot tell you (`serves: 6` and `serves: "6"` differ in type and look
identical in intent).

The corollary, and it is why this sits beside the entry below: verify against a
COPY. `_food_drafts/` was never written to at any point while this was being
built, so the 341-file breakage cost nothing.

**You will rewrite YAML you were only asked to edit.** Not one of the
several hundred front-matter edits made across this project's history has
gone through a YAML dumper. **Parse to check, edit as text.** A
round-trip through `yaml.dump()` silently loses comment placement, key
order, quoting style, and the exact `[""]` formatting `method_short`
depends on — correct in a spot check, wrong across three hundred files. If a
bulk pass is requested and re-serialising looks tempting, say so and offer
text-editing instead.

**You will see a force-push rejection and assume something's badly wrong.**
It happened once, 2026-08-02: a non-fast-forward rejection on a styling
branch that turned out to be nothing worse than a stale remote — `main` had
advanced (a separate branch's PR had merged into it) and the local branch had
been rebased onto the new `main` outside the session, giving its commits new
hashes for identical content, while the remote copy was never rebased and
just sat behind. **Before doing anything destructive: `git fetch`, then
diff each of the "diverged" commits against its counterpart by message** —
if the diffs are empty, it's a rebase artifact, not lost work, and the fix is
an ordinary `git push --force-with-lease` of the correct (usually local)
side. Only force-push once you've actually confirmed nothing unique would be
lost, not because a rejection is scary and force feels like the fast way out.

**The data is cleaner than you think.** Zero undeclared tags, zero
star-ingredient typos, zero accent collisions, last checked. If you scan and
find "lots of problems", be suspicious of your own findings before reporting
them — check whether what you found is a documented convention (a blank
`star_ingredient` is correct for a plain sponge) before offering to fix it.

**Helen adds drafts while you work — this is normal**, often several times a
day, in batches. A test failure that appears between two runs of the same
suite is more likely a new draft than something you broke — check mtimes
before blaming yourself or her, and leave a draft you weren't asked to touch
alone.

**You will suggest tooling that's already been rejected**: `jekyll-seo-tag`,
Stylelint, a bundler, a CSS framework, schema.org/Recipe structured data
(declined because it would push adapted magazine recipes into Google's rich
results). Each was considered and declined deliberately — `DEV_JOBS_v26.md`,
which used to record the stated reasons, is retired; check git log or
GitHub Issues before re-proposing one, and argue against the recorded
reason rather than assuming it was never written down.

**You will use `display: flex` for a simple two-part row, then break it the
day one part needs more than one line of content.** `.method-full li` was
flex (number, then step text) for exactly as long as every step was a single
line — the day one needed a nested list (§4.2), flex turned the list into a
third item laid out beside the number instead of underneath the text it
belonged to. `position: relative` on the container + `position: absolute` on
the generated number, the technique `.recipe-body-content`'s numbered list
and `.method-short`'s bullets already used, doesn't have this failure mode:
the number sits outside the element's own flow, so anything else inside —
one line or several block-level children — stacks normally. Prefer this over
flex for "a label plus arbitrary content" from the start, not just once
something breaks it.

**You will write a bare element selector inside a component, and it will
capture something that doesn't exist yet.** Twice now, both times an `a`,
both times because the container held exactly one link on the day the rule
was written, so `a` was an accurate way to say "the title" or "the body
link". Issue #40 then made every tag badge an `<a>`:

- `article.recipe a` (recipe page) — caught during that work and fixed to
  `article.recipe a:not(.badge)`.
- `.recipe-row-content a` (index page) — the identical rule, one file over,
  missed. Every badge on the index silently took the recipe title's 1rem
  heading treatment instead of its own 0.72rem pill, and stayed that way
  until Helen sent a screenshot (issue #258). It is `.recipe-title-link`
  now, which is also what `filters.js`'s `querySelector('a')` had to become
  in the same issue, for the same reason.

**No test can catch this, and issue #259 was opened to build one and then
closed rather than half-built.** `test_every_class_we_emit_has_a_rule_in_
the_stylesheet` asks whether a class HAS a rule, not whether that rule
WINS — a class whose every declaration is outranked passes it happily. A
lint for "bare element selector inside a component" fires on
`.recipe-body-content p`, `.method-full li` and `.tc-contents li a`, all
legitimate; narrowing it to `a` still hits `.ct-doneat a`. Anything
reliable needs real cascade resolution, i.e. a headless browser reading
computed styles, which is a large slow dependency for a two-instance bug.

So it is a habit rather than a guard: **when a component rule targets a
bare element, ask whether the container will only ever hold one of them.**
If the answer is "one today", name the class instead. The symptom when you
get it wrong is not an error — it is a correct-looking rule that has
stopped applying, which reads as a design decision nobody remembers making.

**You will forget an element inherits from its parent when nesting inside a
styled heading.** `.btn-method-toggle` sits inside `.recipe-section-heading`,
which sets both `-webkit-text-stroke` and `text-shadow` (`punched()`) — both
inherit by default, and neither was ever reset on the button, so it was
picking up the parent's emboss effect on top of its own styling. Invisible
in a casual look (dev tools shows inherited values in the same grey as
irrelevant defaults) until Helen compared it side by side with a plain link
and could tell something was different without being able to say what.
Any interactive element nested inside a punched-tape heading needs explicit
`-webkit-text-stroke: 0` and `text-shadow: none` unless it's actually meant
to carry the effect too.

---

**A rule nested under a parent is a bet on where the element lives, and
moving the markup silently voids it.** 2026-08-16, issue #275. `.btn-reveal`
and `.exclude-reveal-row` were nested under `.controls .search--exclude`. The
reveal button was then moved into `.search-input` so it could share a grid
column with the heading it sits under — and both rules stopped matching
anything at all. The button shipped with no styling whatsoever: no font, no
underline, no colour. **Sass compiled without a warning and all 17,170 tests
stayed green**, because nothing in the suite can see that a selector now
matches zero elements. Caught only by diffing the compiled selectors in
`_site/assets/css/food.css` against the new markup. Nesting is fine; nesting
plus a markup move is a silent break, so when you move an element, grep the
compiled CSS for every rule that named its old ancestor. This is the same
family as the "test that cannot fail" run above — a green suite proving
nothing — but the vacuous thing is a CSS selector rather than a test.

**YOU WILL WRITE A `:not(...)` RULE TO TAKE SPACE AWAY, AND IT CAN ONLY EVER
ADD.** 2026-08-30, issue #589, and it is a one-line fact with a two-week tail.
Issue #290 moved the results pool's gap onto the pool itself, gated on
`:not(:empty)`, so an empty picker would stop buying dead air — and its own
comment says exactly that. It never did, because `_search.scss` went on
declaring `margin-top: $space-lg` on the same element unconditionally, and a
conditional override sits ON TOP of its base rather than replacing the
condition. So the pool got 0.75rem with content in it and kept the larger 1rem
with none: **4px TALLER empty than full.**

The visible symptom was somewhere else entirely, which is why it took a bug
report to find. Picking a LEAVE OUT candidate empties the pool at the same
moment the chosen pill is drawn below it, so the pill landed 4px lower than the
chip that had just been clicked — Helen: *"if I click a chip, it then jumps
downwards by a few pixels, but should stay in the same place."* Nothing about
the chip had changed at all.

**The general form: to make a state cost NOTHING, the base must declare
nothing.** Ask which value applies when the condition FAILS, because that is the
one a `:not()` rule never gets to set. `test_an_empty_search_results_pool_
reserves_no_space` is the guard.

The `:empty { display: none }` idiom next door does not have this problem, and
the difference is worth knowing: `display: none` removes the box and its margins
together, so an unconditional margin beside it is harmless. That makes the rule
depend on its neighbour, which is why `.exclude-active` uses `:not(:empty)`
anyway.

**A lightness-only colour change is not a state change at small type.** Twice
in one day, 2026-08-16, both found by Helen on the page and neither visible to
me in the source. The footer reference links moved `$color-clear-text` →
`$color-text` on hover (#4f4e4a → #211f20) and the LEAVE OUT reveal link moved
`lighten($color-text, 12%)` → `$color-text` (#3a3739 → #211f20). Both are real
changes; both are invisible at 0.75–0.78rem. Her report was the same sentence
each time: it "doesn't change on mouseover or click". **At small sizes the eye
reads hue, not lightness** — every interaction state on this site that
actually works moves hue (the clear buttons sit at their section's darkened
root and shift; body links go to the core magenta). If you find yourself
darkening a grey by 12% to signal a state, you have written a no-op.

**A generated sweep over a table proves the predicate, not the table.**
`tests/js/filter-state.test.js` generates one case per field from
`FS.FIELDS`, and it is genuinely load-bearing — but it can only prove that
`hasAnythingToClear()` handles every field `FIELD_SPEC` **declares**. It
cannot prove `FIELD_SPEC` declares every piece of state the page holds, and
that second claim is the one that keeps failing: `nameQuery`, then
`isSearching`, then two rival predicates, then the LEAVE OUT box (#274,
2026-08-16). A control with no field is invisible to a sweep over fields. The
fix that closes the class rather than the instance comes at it from the page:
`test_every_text_input_on_the_index_has_state_behind_it`
(`tests/test_rendered_pages.py`) reads every `<input type="text">` id out of
the BUILT index page and fails on any control it has not been told about.
**When a generated test keeps missing the same bug, ask what its input list is
generated FROM, and generate the next one from the other end.**

**A photo "batch" is not one source, and an ordinal count of photos is not a
filename.** 2026-08-21, a 43-photo inbox ingest. An early low-detail survey
numbered the photos and named a recipe at each number; several later ingestion
passes were then handed that ordinal ("photo 30 is Chelsea Buns") and had to
guess or recompute which actual file that was, and got it wrong more than
once — pointing at pages that turned out to already be drafted, causing
redundant re-ingestion of recipes that already existed (harmless here only
because the underlying source text was identical either time). The same inbox
also turned out to hold pages from three unrelated cookbooks plus one AI-chat
screenshot, not the one book the batch was assumed to be. **Resolve every
recipe-to-photo mapping by actually opening the photo, not by trusting a
prior pass's count or an assumed shared source for a whole folder** — cheap
per photo, and the alternative is silent overwrites or gaps that only surface
when someone later reads the file.

**AND A CAPTURE THAT ENDS MID-RECIPE LOOKS EXACTLY LIKE A COMPLETE ONE.**
2026-08-31, both halves of the same inbox. A screenshot of a web recipe stopped
just below the dipping-sauce list, and a book photograph stopped mid-sentence at
"Stir until cold,". **Neither announces itself** — the first read as a finished
ingredient list, and only counting every ingredient the method steps name gave
any evidence at all (weak evidence: it proved nothing was missing that was USED,
not that nothing followed). Helen checked the page and confirmed it. The second
was obvious only because the sentence broke.

So: **an ingest transcribes what is in frame and says where the frame ended.**
Never complete the recipe from the sibling recipes on the same page, however
uniform they look — the other punches in that chapter all end the same way and
that is still their wording. Flag, and raise an issue if it needs the book back
(#627, #628). Two photographs in that batch also caught only a title and half an
intro, from pages Helen had not meant to include; she said so and they were
dropped rather than guessed at.

**"Lost work" after a disconnect may just be sitting in a `git worktree` you
haven't looked in.** 2026-08-22, `_cocktail_drafts`. Helen described a whole
prior session's rum-typing work (Milliners Punch, Anita's, Zombie Intoxica,
20+ generics, the Lemon Daiquiri drop — 8 commits) after a Windows Terminal
crash. The plain `_cocktail_drafts` checkout showed none of it — `git log`
there stopped well before it, and it looked exactly like genuinely lost
work. It wasn't: `git branch -a -v` showed a local-only branch
(`data/type-rum-generics`, never pushed) already checked out in a SEPARATE
worktree at `.claude/worktrees/cocktails-rum/_cocktail_drafts` — `git
worktree list` names the path directly, and `git switch <branch>` fails
loudly ("already used by worktree at …") rather than silently, which is the
tell. All 8 commits were there, clean, untouched. **Before reporting
anything as lost from a disconnected session, run `git branch -a -v` and
`git worktree list` in the relevant repo** — a branch that exists locally
but not on any remote, or a worktree at a path you didn't expect, means the
work survived, just not in the directory you happened to be standing in.
Git stashes are shared across a repo's worktrees (branches are not), so once
found, `git stash` moves uncommitted edits from one checkout into the other
without needing to redo them by hand — expect `git stash pop` to conflict if
both sides touched the same lines, and resolve to the known-correct state
rather than fighting the merge markers.

**A `Fixes owner/repo#N` trailer in a PRIVATE repo's commit does not close,
comment on, or even cross-reference the issue — checked by measurement, not
assumed.** 2026-08-22, `_cocktail_drafts` (private) vs. `helen-triages`
(public). Dozens of commits over the day carried correctly-formed trailers
(`Towards DeckOfPandas/helen-triages#335`, `Fixes
DeckOfPandas/helen-triages#442` etc.) — the right syntax per CLAUDE.md's own
"a bare #N only resolves within its own repository" rule. Pulling #335's
full timeline via the GitHub API afterwards showed **zero** cross-reference
events from any of them; the only "referenced" event with a real commit
attached was a commit that happened to live in the public repo itself.
GitHub appears to deliberately suppress cross-repo reference/close events
originating from a private repository, presumably so a private repo's
existence and commit messages can't leak onto a public issue page for
someone without access to it. **The trailer is still worth writing** — it's
correct, self-documenting `git log` history in the repo that has it — but
treat closing or commenting on the public issue as a separate, deliberate
step you do by hand (comment with the commit SHA, then close), never
something the commit message will do for you across that boundary.

**YOU WILL LOOP A COLLECTION THAT `output: false` DID NOT EMPTY.** `output:
false` stops Jekyll *writing* a document. It does **not** remove it from
`site.<collection>`. So a template that loops `site.cocktail_drafts`
unconditionally prints every private drink name into public HTML and links them
at URLs that were never written — and every test passes, because the links are
"valid" and nothing is checking the index for things that should not be on it.
This is issue #235, and it has now been available to happen twice.

The guard is a config key that exists **only** in `_config_local.yml`
(`show_drafts`), so production declares nothing and the condition is false
there. **Do not replace it with a check on whether the collection is
non-empty** — that is true in production too, which is the entire trap.
And verify it by BUILDING BOTH WAYS rather than by reading the template:
`--config _config.yml` alone must yield zero cards and zero drink names.

**YOU WILL CHECK ONE ELEMENT'S WIDTH AND CALL THE ROW SAFE.**
`test_no_element_can_force_horizontal_scroll` looks for a single `width: Npx`
above 320 with nothing clamping it. The footer overflowed a phone anyway, and
every element in it was under the threshold: a `1fr` track will not shrink
below min-content, so the row's floor was "temperatures" (~120px) plus the
hearts' flat 240px plus 2rem of gaps ≈ 392px against a ~360px viewport.
**Overflow is a property of the ROW, not of any element in it.** Three
sub-320px tracks side by side overflow a phone perfectly well.

That test's docstring also still says "the site has no media queries and does
not need any". It has had one in `food/_recipe-list.scss` for a long time, and
`shared/_layout.scss` added a second on 2026-08-23. Three counting print.

**YOU WILL ASSUME DOM ORDER DECIDES WHAT PAINTS ON TOP.** It decides only among
peers at the same level. `.site-nav-icons` is absolutely positioned into the
header's bottom-right corner and was invisible and unclickable on a phone —
not because of a z-index anyone set, but because `.site-logo-tape` carries BOTH
`position: relative` AND `transform: rotate(-1.75deg)`. Either one promotes it
into the positioned layer; being later in the DOM with the same `auto` z-index
then wins outright. On a wide header the two never meet, so this is invisible
until someone opens the site on a phone.

**The fix was structural, not a z-index.** Raising the nav above the tape puts
icons on top of artwork, which is not what anyone wants to look at. Below 600px
the row now gets its own line beneath the wordmark, so there is no overlap left
to resolve. Reach for `order` rather than moving markup when the DOM order is
carrying something else — here, the nav is first for tab order and stays first.

**AN INLINE `<svg>` CLIPS ITS OWN CONTENT BY DEFAULT.** Every browser's UA
stylesheet sets `overflow: hidden` on the root `svg` element specifically —
not a CSS property default, a default for that element — so a stroke whose
rounded join or cap sits right on the viewBox edge gets silently sheared off,
with nothing in the SVG source or the surrounding layout CSS suggesting why.
Found on the cocktails glass icons, 2026-08-26 (§9.11), on the real site as
well as a dev-only comparison page — fixed everywhere with an explicit
`overflow: visible`. Worth checking on ANY inline SVG icon that touches its
own edges, not just glasses.

## 13. The site's visual design

Recipe page redesigned 2026-07-31. Index page brought onto the same mark
2026-08-01, then substantially reworked again 2026-08-02 (row layout,
category-code bar, pagination, shuffle). **Read this before changing anything
about how either page looks.**

**The one-line summary:** both pages use one decorative device — a blocky
two-colour bar overlapping the base of a heading, lettering in front of it —
and differ deliberately on how much COLOUR they spend, because colour does
different jobs on each. Detailed iteration history for anything below (what
was tried and rejected, and why) lives in git commit messages, written for
exactly that purpose — this section states the current shape, not the road
to it.

### 13.1 The mark

`box-decoration-break: clone` on an inline element with a per-line
`linear-gradient` background, not `border-bottom` (draws on the box, so a
wrapped two-line title gets one bar at line-one's width, overhanging line
two) and not `text-decoration` (paints over glyphs, not behind them). Dials
live at the top of `_sass/food/_rule.scss` (moved there from `_recipe.scss`
so the index could reach it too) — `$rule-thickness`, `$rule-drop` (bigger =
lower = less overlap; the single most character-defining value),
`$rule-indent`, `$rule-overhang`, plus a second, thinner rule
(`$rule-under-*`) directly beneath sharing the right edge and starting
further left, reading as one bar with a stepped edge rather than two.

**The violet (under) rule is flush with the lettering; the green (top) rule
is inset**, not the reverse — everything on the page starts at x=0, and a
mark hanging into the left margin reads as broken alignment, not design.

It replaced watercolour brush washes. The reason it won wasn't raw area: a
wash picked a random shape per page load, so the eye had to re-identify it
each time. An identical, repeated mark becomes something you *recognise*
rather than *read* — for "can a cook glancing at a propped-up iPad land on
the right section immediately", that beats mass. Don't re-open this with "a
filled field is more visible" — that argument was made, in favour of the
wash, and lost.

### 13.2 The recipe page's colour budget

Four hues, and the count is the design: `$color-bright-magenta` (title rule,
footer hearts, method toggle, and — as `$color-recipe-link`, darkened 12% —
every cross-recipe link, wherever one appears: tagline, notes, method
steps), `$color-section-underline` / `$color-section-underline-2` (the two
rule colours, spring green and violet, which only ever appear *together*
inside one composite mark — and, since 2026-08-03, violet's second job: the
hand-drawn arrow beside an ingredient/step note, `.annotation-mark`
in `_recipe.scss`), and `$color-aureolin` (ingredient-amount highlighter).
Everything else — the whole of the method, notes, boxes — is
`$color-clear-text` or `$color-border`. Colour is on what you *navigate* by,
off what you *read* — a link counts as something you navigate BY, even
mid-sentence, not decoration on something you're reading. The annotation
arrow is the one exception to that split: it's decoration, not navigation,
but it took violet rather than magenta specifically *because* magenta
already means "interactive" on this page — see `_palette.scss`'s "Cross-
recipe links" comment for the full reasoning.

Magenta carries three jobs at once (title rule, toggle, links) on top of
doubling as `$color-star-root`, so the star badge matches the title — all
accepted as the same rhyme, not four separate coincidences: magenta is the
site's one "this is interactive/branded" colour. A new hue was tried for
links first (`$color-vivid-rose`, 2026-08-02) and reverted the same day once
Helen's actual preference turned out to be reusing magenta instead —
`_palette.scss` documents both the exact contrast measurement (5.26:1
against `$color-bg`, link text at 0.82–0.95rem is too small for the relaxed
3:1 exception, so 4.5:1 was the real bar) and why a darker/further variant
was tried and reverted (cohesiveness with the title rule won out over more
distance from the footer hearts). **If a fifth colour is ever proposed,
that's the point to stop and ask whether an existing hue could do the job
instead, the way magenta and violet both just did.**

### 13.3 Spacing

Named scale, not a scatter — sixteen distinct gaps were previously in use,
every one above 2rem a bare literal. `$spacing-block-gap` (1.75rem, within a
section), `$spacing-section-gap` (3rem, below a section), `$spacing-section-
top` (4.5rem, above a heading). Deliberately far apart: a gap only reads as
hierarchy if it's obviously bigger than the one below it. `padding` doesn't
collapse, `margin` does — check which you're using before adding to an
existing gap.

### 13.4 The index page

Same mark, deliberately different colour discipline — see §13.5. Filter
labels carry the punched-tape effect, §13.4.1.

**THE SECTIONS, IN PAGE ORDER, AND IT CHANGED ON 2026-08-30** (issues #583,
#586, #562 — the food index converging on the shape §9.13 gave cocktails):

| | | |
|---|---|---|
| 0 | **THE UNIVERSE SAYS…** | one random row, dealt above the panel; since 2026-09-02 |
| 1 | STAR INGREDIENT | |
| 2 | MOOD | |
| 3 | PRACTICALITIES | |
| 4 | **HAS TO HAVE** / **LEAVE OUT** | side by side, `.search-pair` |
| 5 | I KNOW WHAT I WANT | the escape hatch, last on purpose |
| — | META FILTERS | local only, and **one button now**: `draft` |

**THE UNIVERSE SAYS… — PR #660, 2026-09-02, and the same section exists on
cocktails.** The page offers before it asks: one random survivor above the
filter panel, with a `deal again` control. `assets/js/universe.js` (shared,
site-agnostic) picks a random row from the selector in
`data-universe-rows` and CLONES the parts named in `data-universe-parts`
into `.universe-pick`, so the pick is a real row's title link and ingredient
line (food) or a real card's tape name, ingredient line and mood chips
(cocktails) and cannot drift from how rows look. Cloned buttons become spans
(a card chip outside the card list would be a button that does nothing);
cloned tape slots are filled by `decorations.js`'s `cardTapes()` because
universe.js runs before it, and re-filled from the source card on a later
deal. Absent JavaScript the section is `hidden`. Helen's copy, exactly: "the
universe says…" and "deal again"; she is supplying an SVG for the ↻
placeholder in `.universe-again-icon`. The food pick carries no badges, on
her wording ("style the recipe line like the recipes in the list below, and
give a single line of main ingredients below it") — an open question in
`DESIGN_PLAN.md`. Frame styles: `food/_universe.scss`,
`cocktails/_universe.scss`.

**HAS TO HAVE was `SEARCH MAIN INGREDIENTS`** — that named the mechanism where
every other label names the question, and cocktails already asked it in the
better words.

**LEAVE OUT was behind a reveal link**, "(I know what I don't want)", opened
closed on a progressive-disclosure argument: revealing it deliberately framed it
as a dislike navigator rather than a sixth filter everyone must consider on the
way past. **The framing was the only thing the disclosure bought**, and sitting
beside its own opposite does it better — so the button, its two label strings,
its `aria-expanded`, the `hidden` panel, clear-all's special case and
`#exclude-active` living outside the panel all went at once. It is a
`.category.search` sibling now; §13.5 still gives it no code hue.

**META FILTERS was five buttons and is one.** `needs rewrite`, `needs
proofread`, `no short method` and `has short method` all asked "is this recipe
finished yet", which Helen does not need this page to ask — the same call she
made about cocktails' `meta.status`. `draft` survives because it is a different
kind of fact: which collection a row came from. The rows lost their `needs
rewrite` / `needs proofread` badges in the same pass, keeping only `magic bag`
and `draft`, which say what you are about to CLICK.

**That dissolved the three-valued `data-meta-short`** (§4.3's fourth bullet, and
the specific branch #506 was raised to get under test). The attribute and its
filters.js branches are gone; #506 closed on the argument rather than the
example — see §3.

**Density is the index's own** (`$index-section-gap`, `$index-label-gap` in
`shared/_tokens.scss`), not the recipe page's tokens — matching them was tried
and rejected on sight, pushing the five filter sections ~340px apart. The index
is a control panel (every section visible in one glance); the recipe page is
a document (space isolates the one section you're mid-task on).

**TIGHTENED ON 2026-09-02 FOR THE FOLD** (PR #660, from the design review's
first finding: the first recipe sat ~1,200px down at desktop and the page
opened as an instrument panel with no output). Section gap 1.5rem → 0.75rem,
label-to-buttons gap 0.75rem → 0.5rem, panel top padding 1rem → 0.3rem, the
filter headings 1.35rem → 1.05rem (cocktails 1.6rem → 1.2rem), and the
survivor count's margins pulled up on both sites. Helen chose this
("tighten") over three louder candidates — one row per group behind a "more"
link ("loses what the page is here for"), a side rail ("makes the page look
like even more work"), and a strip of four random rows. The ratio between the
two gaps is 1.5:1 now, not 2:1.

#### 13.4.1 The punched-tape effect — mechanism, not just description

Helen's device. **Since 2026-08-12 it is on EVERY heading on every site, and
it is applied from one place: the `h1, h2, h3` rule in
`_sass/shared/_base.scss`.** Individual components override the colour, the
size and (on the two biggest) the offset, but none of them opts *in* any more —
opting in was exactly how the effect came to be missing from some headings and
mis-tuned on others. `.category-label` (the index's filter section labels —
STAR INGREDIENT, MOOD, etc.) lives in `_sass/food/_category-labels.scss`; the
header wordmark lives in `_sass/shared/_layout.scss`, see §13.8.

**2026-09-02 UPDATE, READ THIS BEFORE FOLLOWING THE REST OF THIS SECTION AS A
HOW-TO.** Dark-on-light punched lettering (food's own case) never actually
worked — its highlight copy was painted in a colour with no headroom above the
page to be seen against, and its shadow copy did all the work alone, reading
as a second letter rather than depth ("dissolving in acid" on the FAQ). The
mechanism below — two dials, stroke sets weight, shadow sets direction — is
still exactly right and unchanged; what changed is that the raw values it
used to read (`$color-emboss-light`, `rgba($color-text, 0.38)`, and every
per-component restatement of `$emboss-stroke $color-label-stroke`) are gone,
replaced by four named TIERS (display, heading, label, plain) that resolve
those two dials together through `@mixin lettering($tier, $offset)`. A new
consumer says its tier — `@include lettering(heading)` — rather than writing
`-webkit-text-stroke` and `text-shadow` by hand the way this section still
describes below. **`model_instructions/LETTERING.md` is the reference now**:
the physics, the tier table with every site's values, the full consumer
inventory with file:line, and the traps. This section stays as the historical
record of how the mechanism was discovered and reasoned about — it is not
rewritten — but do not copy code from it for a new element; read LETTERING.md
instead.

**Two things on the index deliberately do NOT wear it, and both were checked
with Helen rather than assumed.** The results heading's "N survivors" count is
plain body text — it carries `class="category-label"` but sits outside
`.category`, so the rule is scoped to keep it out, and `.results-heading
.category-label` now states the bare treatment outright so it can't be
"fixed" again by accident (it was, once, on 2026-08-12; Helen: "I liked it
bare"). **§13.7 contradicted this paragraph for three weeks** and an issue got
written from the wrong one — see the box there; the two agree now. And the **active states of filter buttons and recipe-row tags** carry
a heavy `-webkit-text-stroke` in the *same* colour as the letter with
`text-shadow: none` — see §13.4.2, that is a different effect wearing the same
property. Written out in full because "reads as
embossed label-maker text" is not enough to reproduce it — the actual
mechanism, and the trap in it, aren't visible from the compiled CSS.

**Where it lives.** The mixin is `@include punched($style: raised)`, defined
in `_sass/shared/_rule.scss`. It moved there from `_sass/food/_rule.scss` on
2026-08-02 when the wordmark started using it — the wordmark lives in
`shared/_layout.scss`, which every site stylesheet compiles, and a mixin
must be defined before the partial that calls it, so a food-only file could
no longer hold it. (At the time that meant three stylesheets, and the third,
`root.scss` for the landing page, was missed on the first pass of this exact
move — the origin of §2.2's and §12's warnings. It is two now, and both
those entries have been rewritten; the history is kept because the failure
mode was about *counting* the consumers, not about that one file.) It
depends only on `$color-bg` and
`$color-text`, which the palette contract guarantees every site defines, so
nothing about the mixin itself ever assumed food. Two arguments exist and are
both live: `raised` (default) reads as embossed, light falling from the
upper-left; `pressed` inverts the light for a stamped-in look. Neither is a
hypothetical — both are real, tested options.

**Two independent halves, not one mixin doing one thing:**

- `@include punched(raised)` supplies a hard-edged (zero blur), two-copy
  `text-shadow` — one copy offset up-left in `$color-emboss-light`, one
  offset down-right in `$color-emboss-shadow` (`rgba($color-text, 0.38)`).
  This is what gives the sense of a light source and depth. No blur
  specifically: a blurred shadow reads as floating *above* the page, the
  opposite of a letter punched *into* it.
- `-webkit-text-stroke: $emboss-stroke $color-label-stroke` is a **separate
  declaration alongside the mixin call, not inside it**. It's what gives the
  letterform its edge weight.

**Stroke sets weight, shadow sets direction. Either can be adjusted without
touching the other.** A uniform stroke has no direction in it — it can only
give a soft, detached-from-the-background edge, not a claim about which way
the light falls. That claim is what the shadow half is for.

**BOTH HALVES ARE PROPORTIONS OF THE TYPE THEY SIT ON. This is the whole
trap, and it bit twice before it was understood.** Both `-webkit-text-stroke`
and a `text-shadow` offset are absolute lengths, so one value across a range
of type sizes is a range of different letters — and the two failures look
nothing alike, which is why they were diagnosed years apart:

- **Too much stroke** and the outline fills the counters, leaving the emboss
  copies no crisp edge to sit against. The letter reads *outlined*, not
  raised. This is what a flat `0.5px` was doing to 0.85rem meta labels (3.7%
  of the type).
- **Too little offset** and the shadow copies barely clear the glyph at all.
  The letter reads *flat*. This is what a flat `1px` was doing to 1.8rem
  section headings (3.5%), while the same 1px on a 0.9rem label (6.8%) looked
  exactly right — the effect was strongest on the smallest type on the site
  and weakest on the biggest, the opposite of what the source implied.

**So do not write either value as a raw number.** The three fixed stroke
tokens (`$stroke-heavy` / `$stroke-medium` / `$stroke-light`) were retired on
2026-08-12; if you find them referenced anywhere, that reference is stale.
Use instead, both in `_sass/shared/_rule.scss`:

- `$emboss-stroke` — **`0.016em`**, i.e. 1.6% of font-size (1.4% against
  Courier New; Helen re-tuned it against Courier Prime, and the heavier face
  wanted MORE edge, not less). An `em` resolves against the element's own
  computed size, so this is self-scaling and needs no argument, no arithmetic
  and no maintenance. It is what lets the global `h1, h2, h3` rule work at
  all, since that rule cannot know what size a heading will turn out to be.
- `$emboss-offset` and `$emboss-offset-large` — **both `1px` now.** They stay
  hard whole pixels rather than a computed proportion, deliberately: a
  fractional stroke antialiases harmlessly along an edge, but a fractional
  shadow offset antialiases the whole duplicate glyph, which is the soft
  floating read the "no blur" rule exists to prevent. The 2px large offset
  went when Helen tuned the h1 against Courier Prime (two letters, not one
  raised one) and the wordmark's own 2px went with the tiers on 2026-09-02;
  the two variables stay separate in case the levels want to diverge again.

**SINCE 2026-09-02 NOBODY WRITES STROKE AND SHADOW BY HAND: A CONSUMER NAMES
ITS TIER.** `@include lettering(display | heading | label | plain)` in
`shared/_rule.scss`, and the tier resolves to per-site custom properties.
Display is HELEN TRIAGES and the recipe title (hard), heading is every other
heading at 1rem and up (soft), label is everything smaller (stroke only, no
copies — below 1rem a shadow cannot clear the stroke to be seen), plain is
nothing. The finding that produced them — food's dark-on-light punched
lettering had a WHITE highlight on a near-white page (invisible) and a 68%
ink shadow (a second letter), "dissolving in acid" on the FAQ — and every
value per tier per site is in **`LETTERING.md`**, which supersedes the rest
of this subsection wherever they disagree.

The original ratios weren't invented — they were where the two elements that
demonstrably worked already sat: HELEN TRIAGES at 6.3% offset after Helen
tuned it by hand, and the longform Tips label at 6.8% offset / 1.4% stroke,
which is the element she pointed at ("it looks better than the lettering for
my existing page headings — am I imagining this?"). She wasn't; the Tips
label is on the label tier now and the ratio argument is history.

> **THE EXCLUSION IS FOOD'S ONLY, SINCE 2026-09-02 — #469.** Everything below
> is still exactly right for food and no longer describes cocktails. Helen, on
> the inverted header: *"the wordmark text is weirrrrrd… I would like the same
> lettering you created for our new white on black headings."* HELEN TRIAGES
> there is on the display tier with cocktails' own values. The tape word
> [ COCKTAILS ] briefly matched the card tapes' two near-whites and, on
> 2026-09-02, went back to the shared four-copy tape lettering [ FOOD ] wears —
> Helen: "treat [ COCKTAILS ] the same way we now treat [ FOOD ]" — while the
> card tapes keep their two copies, because four collapse into two letterforms
> at 1rem. See LETTERING.md §8.
>
> **THE ARGUMENT BELOW IS WHY IT WAS EXCLUDED, AND THE ARGUMENT IS WHAT
> EXPIRED.** It rests on the two halves sitting on opposite grounds: dark type
> on light paper above, light type on black tape below, so a mid-grey highlight
> came out darker than a near-white letter. On cocktails the page is `#0e0e10`
> and the tape is `#0d0d0d` — **one unit of lightness apart** — so they are the
> same ground and the same problem, and one answer is honest rather than a
> compromise. Food's paper has not moved, so food keeps both treatments.
>
> **AND `.site-logo-top` WAS A REAL BUG ON A DARK GROUND, not a preference.** It
> hardcoded `text-shadow: -2px -2px 0 #dad7d8, 2px 2px 0 rgba($color-text, 0.5)`
> — a literal light grey chosen as "a touch darker than the page", which is only
> a highlight when the page is light, plus half-opacity ink, which is only a
> shadow when the ink is dark. Inverted, BOTH copies came out light: two pale
> blobs 2px apart on either side of a near-white letter. Its stroke had the same
> fault.
>
> **§13.10.2's own note had named the cause and nobody saw it was a bug
> waiting** — it says this element "sits outside the custom-property system…
> nothing touching those properties could reach it", written about a typography
> pass and equally true of a palette. Five values are custom properties now,
> defaulting to the literals they replaced, so **food is byte-identical**
> (verified in the compiled CSS) and cocktails re-points them. That is the
> palette contract doing its job (§2.3) rather than a chrome fork: one rule, one
> markup, a value each site supplies.

**`[ FOOD ]` IS THE ONE DELIBERATE EXCLUSION, AND IT MUST STAY EXCLUDED.**
`.site-logo-word` — the bracketed site word sitting on the tape, `[ FOOD ]` /
`[ COCKTAILS ]` — sets `-webkit-text-stroke: 0` and does **not** call
`punched()`. It carries a bespoke four-copy `text-shadow` instead (two pairs:
one tight and crisp right at the glyph edge, one wider and softer further
out), built in the issue #122 pass on 2026-08-10. That is not an unconverted
straggler and it is not drift: it is a different problem being solved.

The reason is the background. Every other heading on the site is dark type on
`$color-bg`, so a light copy up-and-left genuinely reads as a highlight. This
word is **light type sitting on the tape SVG**, and the version before #122
did call `punched(raised)` — with the result that the "light" copy (a mid
grey) came out *darker* than the near-white letter it was supposed to lift.
No headroom, no raised read, "just looks like two sets of lettering" (Helen).
The fix pulled the fill off pure white to `#e7e2e3` so a brighter copy has
somewhere to exist, and split one shadow pair into two so the letter gets both
a cut line and a glow.

**Re-tuned 2026-08-26 for Courier Prime (issue #470).** The mechanism is
unchanged — still four copies, still a fill below white — but every number moved:
fill `#ECE9EA`, offsets `1.0px` / `1.8px`, outer highlight `0.75`. The two copies
came *towards* each other, the gap narrowing from 1.6px to 0.8px, so the bevel is
tighter and better defined rather than spread. A heavier letterform has more ink
of its own for the copies to sit against.

Applying `$emboss-stroke` or `punched()` here would undo that. Its sibling
`.site-logo-top` (HELEN TRIAGES) is a normal consumer and *was* brought onto
the ratios on 2026-08-12; the two halves of the lockup have always been
styled independently and always will be. If the lockup ever looks mismatched,
the answer is to tune `.site-logo-word`'s own four copies, not to hand it the
shared treatment.

**One explicit exclusion: no square brackets around punched-tape text.**
Tried, cut. Brackets are the wordmark's own device — `[ FOOD ]` /
`[ COCKTAILS ]`, a literal value from `_data/sites.yml` rendered by
`default.html`, not a decorative flourish available to reuse. Stroked caps
pattern-match toward "wants brackets"; resist it.

**The footer's reference block is the one other place the brackets appear,
and it is the device rather than an exception to it** (added 2026-08-16,
issue #272). It renders `[ {{ this_site.word }} ]` — the same value, from
the same file — as a label saying which site those reference pages belong
to, so cocktails' own block would read `[ COCKTAILS ]` the day it has one.
It carries no `punched()` and no stroke, which is the part this rule
actually forbids. The test to apply if a third use is ever proposed: is it
naming a SITE, from `sites.yml`, or is it reaching for brackets because
capitals look like they want some?

**The wordmark WAS stroke-only, deliberately, until 2026-08-02 — this is now
out of date if you find it repeated elsewhere.** An earlier version of this
document said the wordmark demonstrated "the soft-edge, stroke-only look...
but never as raised, because there is no direction in it," citing a comment
in `_rule.scss` that predates the mixin's move. That's no longer true: both
HELEN TRIAGES and the bracketed word now call `@include punched(raised)`
too. If you see the old claim anywhere (an older branch, a stale comment),
the code is what to trust — check `_sass/shared/_layout.scss` directly
rather than this document or an old comment.

**The recipe page's own headings were stroke-only too, until the same day.**
`.recipe-title-text`, `.recipe-section-heading`, `.recipe-group-heading` and
`.recipe-meta li strong` all had a plain `-webkit-text-stroke` with no
explicit colour (defaulting to `currentColor`, i.e. the same as the fill —
no lighter derived tone, no emboss shadow) until Helen spotted the
inconsistency: `.category-label` on the index had already been upgraded to
the full punched treatment, matched to these same headings' proportions
(the §13.4.1 worked example above), while the headings it was matched *to*
still used the plain version. All four now call `@include punched(raised)`
and use `$color-label-stroke` for the stroke colour, same as the index and
the wordmark. Stroke *widths* stayed per-element on that pass and drifted for
another ten days; they are all `$emboss-stroke` now — see the proportion
section above. `.btn-method-toggle` deliberately did **not** get this — it's
documented as matching the index's `.btn-clear-inline`, which has no stroke
or punch treatment at all, so changing just the recipe-page half of that pair
would have created a new inconsistency rather than closed one.

**`.recipe-body-content h3` is no longer an exception.** An earlier version of
this section said it "deliberately stayed plain, on purpose... that split is
the hierarchy, not an oversight." That is out of date as of 2026-08-12: it now
takes the treatment from the global rule like every other heading, and states
only its stroke *colour* locally (`shared/` may name just the nine
palette-contract variables, so it outlines in `$color-text` by default, which
is too dark against this element's own lightened grey). The hierarchy between
`h2` and `h3` in body content is carried by size, colour and spacing, which
was always doing the real work — "no emboss at all" was one level of
difference too many, and it made `h3` the odd heading out on a site where
every other one is embossed. The about page's FAQ questions are the visible
case.

**To extend the device somewhere new:** `@include punched(raised)` plus
`-webkit-text-stroke: $emboss-stroke <a colour LIGHTER than the letter>`, and
leave `$emboss-offset` / `$color-emboss-light` / `$color-emboss-shadow` alone —
those are the constants that make every use of this read as one consistent
device rather than a new effect invented each time.

#### 13.4.2 The other `-webkit-text-stroke` — faux-bold, not an edge

**One CSS property, two unrelated jobs, and telling them apart is the whole
of this section.** Check the stroke's COLOUR before assuming a heavy stroke is
a mis-tuned punched-tape edge:

- **Lighter than the letter** (`$color-label-stroke`) → it's an **edge**, half
  of the punched-tape effect. Wants `$emboss-stroke`, 1.4%. §13.4.1.
- **The same colour as the letter** (`$color-text`) → it's a **faux-bold**,
  and has nothing to do with the punched effect. Wants to stay heavy.

The faux-bold exists because **the headings font ships only Regular and Bold as
static faces** — Courier Prime now, Courier New before it, which is one of the
reasons that swap was safe — so `font-weight: 900` already resolves to Bold and
there is nothing above it. Thickening the glyph with a stroke in its own colour is the
only way to get "heavier than bold" — which is what an *active* filter button
needs, since the whole signal is that it looks heavier than the ones next to
it. It's used at ~0.6px by the active states of the filter buttons
(`_category-labels.scss`, `_search.scss`, `_active-filter-states.scss`), by
`.badge--matched` on a recipe row — added 2026-08-26 so a matched badge and the
filter button that matched it read as one idea rather than two — and by
the matched tags, title hits and ingredient hits on a recipe row
(`_recipe-list.scss`).

**These are NOT raised, despite looking as if they might be.** Every one of
them sets `text-shadow: none` explicitly. Helen removed the emboss from them on
2026-08-03 for a reason that still holds: the category colour already lives in
`.tag-shape`, and the punched treatment means "landmark / heading" everywhere
else on the site, where these are controls in a selected state. She raised the
question again on 2026-08-12 ("should these get the same treatment... I could
argue it either way") and the answer was no on both counts — bringing them onto
`$emboss-stroke` would thin them by roughly 3.5× and delete the selected-state
weight jump, which is the only thing distinguishing an on filter from an off
one.

**What they DO share with §13.4.1 is the drift, in their own job.** 0.6px is
absolute across type from 0.72rem to 1rem, so it runs 5.2% on a badge and 3.75%
on a `.title-hit` — two elements that sit on the same recipe row. If that gets
fixed, it gets its own em constant with its own name, next to `$emboss-stroke`
and explicitly not it. Open, not done.

**THE STROKE IS THE RIGHT LEVER FOR A SELECTED STATE PRECISELY BECAUSE IT
OCCUPIES NO SPACE**, and that is the useful half of issue #389 (2026-08-19).
Helen: "filter tags to the right of a selected one move to the right — they
should stay in the same position." It was not the stroke, which paints outside
the glyph and cannot move anything. `%btn-active-base` was declaring
`font-size: 0.74rem` and `letter-spacing: 0.04em`, neither matching the resting
state it replaced, so selecting a tag re-measured it. Letter-spacing did most of
it — 0.04em lands after every character including the last (the same trailing-gap
fact §13.8's wordmark trap turns on), about 0.38px each, roughly 5.7px on
`one-handed food`.

**It was two bugs in one rule.** Two different resting bases extend that
placeholder — `.btn-tag`/`.btn-star` at 0.75rem with no letter-spacing, and
`.btn-meta` at 0.72rem with 0.02em — so no single pair of values could ever have
agreed with both, and META filters were shifting by a different amount again.
Declaring NEITHER lets each active button inherit its own resting metrics. The
fix is a deletion.

**So: an active filter rule may change colour, `.tag-shape` fill and
`-webkit-text-stroke`, and nothing that changes a box's size.**
`test_no_active_filter_button_changes_its_own_width` reads the COMPILED CSS and
enforces it — on the compiled output because the trap is not that placeholder,
it is the IDEA that a selected state may restyle type, which can arrive in any
of the five rules that extend it or in a sixth written next year.

### 13.5 The colour contract, and why the two pages differ

**Recipe page: five hues** (§13.2), colour as decoration, rationed.
**Index page: five hues**, one per filter section, in page order: `$color-
star-root` (STAR INGREDIENT), `$color-vivid-cerulean` (MOOD), `$color-
aureolin` (PRACTICALITIES), `$color-pure-lime-green` (**HAS TO HAVE** — this
section was `SEARCH MAIN INGREDIENTS` until issue #583, 2026-08-30, and the
variable name still says ingredient),
`$color-hot-orange` (I KNOW WHAT I WANT). **LEAVE OUT still takes no code
colour**, on the reasoning §13.4 gives, even though #586 has since promoted it
from a hidden panel to a section of its own beside HAS TO HAVE — its heading
carries a cobalt double-rule and its buttons stay neutral. On the index colour is a CODE — each
hue ties a section's rule to its filter buttons, active states, and badges,
so it has to be learned and distinct. On the recipe page colour is
decoration and has to be rationed. **This is a principled divergence — don't
equalise the counts.** They happen to both be five as of 2026-08-02 — that's
coincidence, not the counts converging on some shared target. The recipe
page's five could go to six tomorrow if a decoration earned it and the
index's five stayed five; nothing ties them together.

**One source.** `$color-star-root` and its four siblings in `_sass/food/
_palette.scss` are the only place a section's colour is written. If you find
yourself adding a second place to set one, the roots are wrong, not the
override.

### 13.6 The recipe list

Each row: title, ingredient line, then pills — in that order, deliberately
(§13.6.1).

**Title** is `$font-headings` (Courier Prime), lowercase, weight 600, 1rem.
Weight 400 and 500 render *identically* — Courier Prime, like Courier New before
it, ships only Regular and Bold as static faces, so any request ≤500 resolves to
Regular and only >500 jumps to Bold. If a future weight change appears to do
nothing, this is why.

It spent 2026-08-24 to 08-26 in IBM Plex Mono and came back; see §13.10.1, which
is the more useful read, because *why* it came back is the rule.

**Ingredient line** is clamped, not left to wrap freely — one line on wide
screens, two below 600px (a narrower column holds too little on one line to
serve the recall-lookup case the search exists for), with a soft fade on
truncation via a JS-set `.is-clamped` class (`updateIngredientClamp()` in
`filters.js`, comparing `scrollHeight` to `clientHeight`). **Not a fixed
CSS mask** — a percentage-based or always-on fade was tried first and
visibly faded short, complete lines that were never actually truncated; CSS
alone has no selector for "this box's content overflowed it."

A row used to open with a "category-code bar" — five squares showing which
of the five filter categories that recipe hit, lit or unlit. Removed
2026-08-03: four rounds of tuning (colours, then alpha, then per-hue darken
values) and Helen still didn't love it — see git history
(`.recipe-row-code` in `_layout.scss`/`food/index.html`, the "Category-code
bars" block in `filters.js`) if reviving the idea. The `data-tags`/
`data-star`/`data-ingredients`/`data-meta-*` attributes on each `<li>` stay
— those drive actual filtering, not the bar.

#### 13.6.1 Row order and why

Title, then ingredients, then pills — ingredients outrank pills because they
carry the recall-lookup case ("the one with the sorrel") the search exists
to serve; pills matter more at filter-time than at browse-time.

### 13.7 Results heading, pagination, shuffle

**"N survivors"**, left-aligned, between the filter matrix and the list, and
**PLAIN BODY TEXT** — no punched treatment, no stroke, no colour rule
underneath. It carries `class="category-label"` and `.results-heading
.category-label` sets every one of those values back to the body default on
purpose, with Helen's ruling in its own comment: *"I liked it bare."*

> **THIS SECTION SAID THE OPPOSITE FOR THREE WEEKS AND IT COST A DECISION.** It
> read "right-aligned... reuses the filter section labels' own punched/stroke
> typography", which stopped being true on 2026-08-03 (alignment: sitting alone
> at the right edge of an otherwise left-aligned page, it "read as stray rather
> than placed") and 2026-08-12 (typography: tried, and she preferred it bare).
> **Issue #615 was then written from this paragraph** — "the survivors line is a
> heading on food and a caption on cocktails" — and asked whether cocktails
> should match a food treatment that does not exist. The two sites did differ,
> in both directions at once: cocktails' was smaller AND more styled. Matching
> food meant going plainer, not louder, which is the opposite of what the issue
> proposed. Cocktails' `.drink-count` took the same values on 2026-08-31.
>
> **An issue inherits the handover's mistakes.** §11.2 says an open issue rots
> because nothing re-reads it; this is the other direction — a stale line here
> is copied into an issue and becomes a plan.

The gap above it uses `$spacing-section-gap`, not `$spacing-section-top`; see
`_recipe-list.scss`'s own note on why that was reduced and why it wants Helen's
eye rather than arithmetic.

**Pagination**, 20 per page: prev/next, a page-status label, and a
`(see all)` link that drops the page-size cap for the current filter state
entirely. `update(preservePage)` — every existing filter-changing call site
is untouched by the default (resets to page 1); only the pagination and
see-all handlers pass `true`. The pure page-slicing maths (given a count, a
requested page, a page size and a showAll flag, what's actually current and
which slice) lives in `assets/js/recipe-list.js`, not inline — see §3.

**Shuffle** — Fisher-Yates, in `recipe-list.js`, applied on the "clear all"
click and on every fresh page load (both are the same "no filters active"
state). `.recipe-list` starts `visibility: hidden` in CSS and `filters.js`
reveals it only after the initial shuffle+render, so a refresh shows the
shuffled order directly rather than briefly flashing the server-rendered
alphabetical one and flipping — CSS can't detect "JS has finished", so this
trades the visible flip for a brief blank instant instead, which is the
actual fix, not a partial one.

**ONE ARRIVAL IS EXEMPT: GOING BACK.** Issue #387, 2026-08-19. Arriving at the
index by a back/forward navigation restores the list you left — shuffle order,
filters, page number, see-all and scroll position — instead of shuffling. Every
other way in (typed, bookmarked, followed, reloaded) still shuffles, so the rule
above is unchanged rather than weakened.

Saved to `sessionStorage` on `pagehide` and restored when
`performance.getEntriesByType('navigation')[0].type` is `back_forward`. Half-
finished searches are deliberately not restored (text typed with nothing chosen
is candidates mid-thought, not a filter); a CHOSEN ingredient result is, rebuilt
to the exact end state the click handler leaves.

**THE DRINKS INDEX HAS IT TOO SINCE #595, 2026-08-31**, on Helen's "exactly as
the food site does", and the one real difference is worth knowing before
touching either. **Food restores an ARRAY; cocktails restores the SORT KEYS.**
Food keeps its order in `items` and reorders the DOM to match. The drinks index
derives its order every pass — rank by matched moods, then each card's random
key — so putting the nodes back and calling `apply()` would re-sort them by keys
randomised at startup. Each card takes its INDEX in the saved order instead, and
a drink the record has never seen sorts after all of them rather than being
dropped. `arrivedByGoingBack` lives in `filter-state.js` now, shared by both and
taking `performance` as an argument, so the one browser fact underneath this can
be asked a question without a browser.

**IT WAS BUILT ON THE BACK/FORWARD CACHE FIRST, AND THAT WAS WRONG.** The
reasoning was seductive: go back, the browser restores the page without
re-running anything, the order survives for free. It cannot work here.
`jekyll serve` sends `Cache-Control: … no-store …` (measured with `curl -I`, not
assumed), and `no-store` disqualifies a page from bfcache in Chrome and Firefox
— so on the machine this site is actually developed on, bfcache can NEVER apply.
Helen saw the index reshuffle with her own back button, which is what proved it:
a bug in the new arrow could not have done that.

**The general lesson is worth more than the fix.** bfcache is an optimisation a
browser may decline for its own reasons, so a feature resting on it works
sometimes — and here it would likely have worked on the deployed site and never
on :4001, so the page Helen looks at all day would have disagreed with the live
one. That is issue #235's trap running backwards. The navigation TYPE is a fact
rather than a favour: it reports a back/forward navigation whether or not
bfcache was involved, which is why the fix rests on it instead.

This is also why `toQuery()` in `filter-state.js` is still unwritten. Its own
comment says to add it "the day something calls it"; the thing that would have
called it turned out not to want it, because with no filters set the index
reshuffles on load and a URL carrying every filter perfectly still hands back a
differently ordered list.

### 13.8 The wordmark

Redesigned 2026-08-02. HELEN TRIAGES and the bracketed site word (`[ FOOD ]`
/ `[ COCKTAILS ]`) both carry the punched-tape effect now (§13.4.1) and the
black tape behind the bracketed word is sized to the lettering rather than a
hardcoded pixel value.

**The wordmark is the ONE thing the chrome still varies per site, and that is
its job** — it says where you are. Everything else in the header and footer is
identical everywhere (§2.5). It sits in `.site-title-link`, above the nav row,
so it is already separated in the markup from everything the chrome guards
compare.

**THE ABOUT PAGE BELONGS TO NO SITE, and says so twice.** Two front-matter keys
on `about.html`, both read by `_layouts/default.html`:

- **`wordmark_word: "??"`** — the bracketed word on the tape, so that page reads
  HELEN TRIAGES / `[ ?? ]` instead of `[ FOOD ]` (issues #398, #395).
- **`site_neutral: true`** — suppresses the `" | " + site_title` that every
  other page appends, so the browser tab reads `??` and not one site's name.

The page is called `??`: the `<h1>`, the front-matter title and the tab all say
it, matching the `??` nav link that reaches it. Helen, settling #395: *"The name
of that page is '??', so wherever a title would appear it should read '??'."*

It needed both because `/about/` hangs off the shared header of BOTH sites at a
site-neutral URL while carrying `site_key: food` — which it must, since that is
what gives it a stylesheet at all (§2.4). **Belonging to no site for DISPLAY and
borrowing one site's CSS are different claims**, and only the first is
declarable; that is the honest wart in this arrangement and the reason
`site_neutral` cannot simply be inferred from `site_key`.

§13.4.1's test for a new use of the brackets is *"is it naming a SITE, from
`sites.yml`, or is it reaching for brackets because capitals look like they want
some?"* **This is the first case genuinely in between**, and it passes on the
reading that `??` in the site slot is how a page says it belongs to neither.

**The core sizing mechanism: whichever row is naturally wider defines the
width, via CSS Grid, not JS.** `.site-logo` is `display: inline-grid;
grid-template-columns: max-content;` with `justify-items: center`. Both
`.site-logo-top` (HELEN TRIAGES) and `.site-logo-tape` (which wraps the
bracketed word) sit in that one column with no width forced on either —
`grid-template-columns: max-content` takes the largest max-content
contribution across everything placed in the column, so the column, and with
it the tape's core width, becomes exactly as wide as whichever line actually
needs more room. On food that's still HELEN TRIAGES (13 characters at 2rem
beats "FOOD" at 2.5rem); on cocktails it's `[ COCKTAILS ]` (13 characters at
food's own 2.5rem is wider than HELEN TRIAGES's 13 at 2rem). No JS
measurement anywhere, and nothing to keep in sync if the title copy or either
site's word ever changes — the browser works it out from what actually
renders.

**This wasn't the first version, and the first version is worth knowing
about because the reasoning that ruled it out generalises.** Version one
pinned the core to HELEN TRIAGES's width unconditionally and let the tape
protrude a fixed amount past it. That made `[ COCKTAILS ]` impossible at
food's own height — 13 characters at 2.5rem is wider than HELEN TRIAGES's 13
characters at 2rem, so it could only fit by shrinking, which is what shipped
first (a cocktails-only `font-size` override). Helen's actual preference,
once she saw it: keep `[ COCKTAILS ]` at food's height and let the *tape*
adapt instead. The trade being made, stated plainly rather than left
implicit: cocktails' tape is now wider than HELEN TRIAGES rather than
matching it exactly. Food is unaffected either way.

**`$tape-protrusion`** (`_sass/shared/_layout.scss`) is how far past that
core the tape graphic itself extends, currently `0.2rem`, trimmed down twice
on Helen's request from an initial `1.5rem`. One value, shared by both
sites' `.tape-bg` — there's no per-site protrusion, so "make cocktails'
shorter, then match food to it" is already true by construction whenever
this number changes. Kept small even after the §13.9 redesign gave food's
tape real corner geometry — the corner shape reads at the tape's own ends,
not in how far it protrudes past the lettering, so there's been no reason
to revisit this number for that reason. (Originally written when the old
pre-redesign SVGs really were a single near-rectangular polygon with no
corner geometry at all, which is no longer true for food — see §13.9. Still
true for cocktails, which hasn't had its own redesign pass.)

**`.site-logo-word`'s padding is `1.4em`, not a percentage — this isn't a
style preference, percentage padding here would be circular.** Percentage
padding resolves against the containing block's width, but
`.site-logo-tape`'s width is now itself *derived from* this element's
content (the mechanism above). A percentage padding would be sizing itself
off a number that's trying to size itself off the padding. `em` has no such
problem and still scales with the word's own font-size the way the old
percentage scaled with the tape's.

**The trap that bit here, worth its own entry because it's a real, general
pattern:** `.site-logo-top` carried `padding-right: 0.18em` with no matching
`padding-left`. `letter-spacing` adds a trailing gap after the *last*
character as well as between every other pair (the same fact the recipe
title's rule insets already account for, §13.1) — so this box's own
`max-content` width already ran slightly past its visible glyphs before the
padding was even added. Matching padding on the right didn't compensate for
that trailing gap, it **doubled** it. This was completely invisible for as
long as `.site-logo-top` always defined its own grid column (food) — there
was no larger frame for it to be off-centre *within*. It became a visible
rightward shift the moment something else (cocktails' wider word) started
defining the column instead, because centering a box that's already
internally lopsided inside extra space makes the lopsidedness visible for
the first time. Removed. See §12 for the general form of this trap — it will
recur anywhere an element's width and its container's width are assumed to
always be equal until one day they aren't.

**The same mechanism was used for the index page's reveal link — and the way it
failed is the part to keep.** 2026-08-16, issue #275: "(I know what I don't
want)" had to centre under I KNOW WHAT I WANT, whose width changes with its own
text. Same answer as above — `display: inline-grid; grid-template-columns:
max-content; justify-items: center`, both rows in the one column
(`.name-heading-stack`).

**THAT LINK AND ITS STACK ARE GONE, 2026-08-30, issue #586.** LEAVE OUT is a
section of its own beside HAS TO HAVE now, so there is nothing to reveal and
nothing to centre; `.name-heading-stack`, `.exclude-reveal-row`, `.btn-reveal`
and `.exclude-panel` were all deleted rather than left compiling. **The
paragraphs below are kept anyway**, because the mechanism is the WORDMARK's and
is still live there — this was its second consumer, and the failure it hit is a
property of the trick rather than of the page.

The first attempt put the heading, the search input, the exclude panel and the
active list into a single grid on `.search--name`, with the panel spanning
every column. It came out ~116px too wide, and the reason is worth carrying:
**a spanning grid item still contributes to an intrinsic track's size.** With
`grid-template-columns: max-content minmax(0, 1fr) max-content`, an item
spanning `1 / -1` pushes its contribution into the only intrinsic track it
can — so the LEAVE OUT panel, not the heading, decided the width of the column
the link was being centred in, and the search input beside it moved right by
the same amount. Visible on the page as `recipe name...` no longer lining up
with `ingredient name...` above it.

So the shared column must contain **only** the two things being centred on
each other. That is a real constraint on this trick, not a tidiness
preference: anything else placed in that column, or spanning through it,
becomes the thing that sizes it.

### 13.9 The tape background

Redesigned 2026-08-10, issue #122 — replaced food's original 4 tape files
(one plain skewed polygon each, sparse and left-heavy machine marks, no
bevel — see git history before this date if you need to see them) with 7
new ones. **`scripts/generate_tape.py` is the tool, and its own docstring is
the actual spec** — this section is the summary, not a substitute for
reading it before regenerating anything.

```
python3 scripts/generate_tape.py --corner-mode both_acute --seed 30 \
    --out assets/img/chrome/tape/tape-1.svg
```

**The output directory moved out of `assets/img/food/` on 2026-08-19** (§2.5):
the wordmark is shared chrome, so there is one tape set for the whole repo.
Regenerating no longer has a "and copy it across to cocktails" step.
`_data/chrome.yml`'s `tape_count` must match what the directory holds, and
`test_tape_count_matches_the_tape_directory` checks both the count and that the
run is gapless — `decorations.js` rolls a random n in 1..N and builds the
filename from it, so a gap is an intermittent 404 rather than an error.

`--seed` drives the corner shape; `--marks-seed` (defaults to `--seed`)
drives the machine marks independently, so a shape you like can be paired
with a different mark layout without redrawing the corners. There is no
"generate a good one automatically" mode — generate a batch across all
three `--corner-mode` values, look at them against the real header (a
throwaway HTML file reusing the actual `.site-logo-*` CSS from
`_sass/shared/_layout.scss` is the fastest way — inline the candidate SVGs,
don't screenshot the live site), and hand-pick. That's genuinely how the
current 7 were chosen, over several rounds of feedback, not a one-shot
generation.

**Three independent parts, same file:**

- **Corner shape.** The polygon's top edge stays flat; each BOTTOM corner
  can independently be acute (<90°, that side's bottom edge flares past the
  top edge) or obtuse (>90°, it insets under it) — `corner_mode` is
  `both_acute`, `both_obtuse`, or `mixed` (one of each). Magnitude is
  randomised within the seed, currently 4–16px of skew. Helen's read after
  comparing all three across a real batch: no consistent winner — the
  current 7 mix all three corner modes deliberately, not by accident.
- **Machine marks.** 5–7 narrow clusters (weighted to land on 6), each a
  handful of jittered near-vertical lines — not an even scatter, gaps
  between clusters are wide and irregular on purpose, closer to how a
  physical label-maker actually marks tape than uniform spacing. The tape
  is split into three zones (left flank / the "letter zone" behind the
  lettering / right flank); every generation guarantees at least one
  cluster per zone, and the single clearest and second-clearest cluster on
  the whole tape always land one per flank — enforced by construction
  (assigned before the rest are drawn), not checked afterwards. Which flank
  gets the single clearest mark is randomised. `LEFT_FLANK_FRAC` /
  `RIGHT_FLANK_FRAC` (0.16 each) are a guess at how much of the tape's
  rendered width sits outside the word block — not measured against real
  font metrics, since the source viewBox is stretched non-uniformly
  (`preserveAspectRatio="none"`) to whatever the real wordmark width turns
  out to be. Worth rechecking by eye if the flank ever reads too wide or
  narrow against real lettering.
- **Edge bevel.** A highlight line pair on the top and left edges, a much
  subtler pair on bottom and right, both hard-offset with no blur — the
  same light-from-top-left, two-hard-copies logic as the wordmark's own
  `punched(raised)` mixin (§13.4.1), not a separate effect invented for the
  tape. Because `.site-logo-tape` rotates the tape and the lettering
  together as one unit, defining "top-left" in the SVG's own local,
  pre-rotation coordinate space keeps it automatically consistent with the
  lettering's light source with no compensation needed for the
  `rotate(-1.75deg)` — both tilt together afterward.

**The wordmark lettering got a matching fix in the same pass** (`.site-logo-
word` in `_sass/shared/_layout.scss`) — not part of the SVG generator, but
decided alongside it and worth knowing about together. The old version's
fill was pure `$color-white`, already the top of the brightness range, so
its "light" shadow copy (a mid grey) was actually *darker* than the letter
it was meant to highlight — no headroom, so it read as two overlapping
letterforms rather than one raised one. Fixed by pulling the fill to an
off-white (`#e7e2e3`) so a genuinely brighter copy has room to exist above
it, and splitting the single shadow pair into a tight crisp one at the
glyph edge plus a wider soft one further out — same bevel logic as the
tape's own edge highlight, applied to text. Helen's own call after
comparing a higher-contrast pull side by side: the lighter version read
better — less "realistic" contrast, more effective as a label.

**Lettering alternatives tried and rejected, so they aren't re-proposed —
this session's own commit message didn't capture these, only the final
pick, so it's recorded here instead:**

- A flat, bigger emboss offset (no stepped bevel — just the original
  single shadow pair, offset further, on the lighter fill). Helen: "looks
  raised up and left... and not well" — reads as the whole letter shifted
  diagonally, not as a raised edge.
- A gradient fill on the glyph itself (`background-clip: text`, a diagonal
  light-to-dark sweep inside each letterform), on the theory that internal
  shading would look more physical than an offset copy. Helen: "looks like
  the lettering is made from twisted wire" — a diagonal gradient samples
  differently across a thin bold stroke's horizontal vs. vertical segments,
  which reads as a twist rather than a shaded surface. Tightening the
  gradient's transition band (from a 30–100% smooth sweep to a near-step at
  46–54%) was tried as a fix and not pursued further once B was already
  winning.
- The gradient fill combined with the stepped bevel (all of the above at
  once). Helen: "good, but I prefer the crispness of B... even if less,
  you know, accurate" — B's flat fill plus stepped shadow read more
  dynamic than the more literally physical combined version.
- Higher-contrast pulls of B's fill (`#a8a2a3`, `#8a8384`, pulling further
  from white than the then-shipped `#e7e2e3`; the fill is `#ECE9EA` since
  #470, one step lighter again) — more headroom for the highlight,
  in principle more "accurate", but rejected in a direct side-by-side: the
  lighter, less contrasty version was the one that actually read as raised.

**Provenance of the 7 shipped files** — which `--seed`/`--corner-mode`
produced each, for anyone regenerating or swapping just one:

| File | Seed | Corner mode |
|---|---|---|
| `tape-1.svg` | 30 | both_acute |
| `tape-2.svg` | 32 | both_acute |
| `tape-3.svg` | 33 | both_acute |
| `tape-4.svg` | 35 | both_obtuse |
| `tape-5.svg` | 36 | both_obtuse |
| `tape-6.svg` | 40 | mixed |
| `tape-7.svg` | 45 | mixed |

All generated with `marks_seed` unset (defaults to `seed`) — see
`scripts/generate_tape.py`'s own `generate()` signature.

**One thing raised here is still open, and one has been overtaken:**

1. **OVERTAKEN, 2026-08-19, issue #374.** This used to record a 2026-08-15
   ruling (#223) that cocktails stays at PARITY with food's tape, with copying
   across as part of regenerating food's set. There is one directory now, so
   there is nothing to keep in parity and nothing to copy. See §2.5 and §9.8.
2. **STILL OPEN. `decorations.js`'s `tape()` picks one of the N SVGs at random on
   every page load** (`data-tape-count`). This is the exact pattern §13.1
   documents as tried and rejected for the recipe/index section marks — "an
   identical, repeated mark becomes something you recognise rather than
   something you read" — but whether that reasoning actually applies to a
   background texture behind a fixed wordmark (rather than a wayfinding
   device you need to re-find on every page) was never revisited in this
   pass. Worth deciding out loud, not by default either way.

---

### 13.10 Typography — three fonts, and the rule for which goes where

**The site self-hosts everything and names no system font as a first choice.**
`_sass/shared/_fonts.scss` declares eight faces, 124 KB, latin subset, served from
`assets/fonts/` with relative urls (which resolve against the compiled
stylesheet's own location, so they survive any baseurl — a `{{ site.baseurl }}`
would not work at all, Sass not being run through Liquid).

    Selawik        300 350 400 600 700    $font-body
    Courier Prime  400 700                $font-headings
    IBM Plex Mono  600                    $font-label

Every stack keeps the old system font as its fallback, so a failed woff2 degrades
to what the site looked like before rather than to a generic.

**WHY, and it was never really about PDFs.** Issue #373 reported "PDFs on prod
have surprising fonts". The cause was that there was no `@font-face` anywhere and
both stacks named only desktop-installed fonts: `scripts/generate_pdfs.py`
renders with headless Chrome on `ubuntu-latest`, where Courier New, Segoe UI and
Roboto are all absent — measured, not assumed — so everything fell to DejaVu and
lost the 300/350 weights too, DejaVu having no Light face. But the same was true
of every reader: the site rendered in a different typeface on Windows, on a Mac
and on Linux. **The PDF was only where it became visible.**

**Why these three.** Selawik is Microsoft's own OFL-licensed, metric-compatible
substitute for Segoe UI, so no measurement moved — and its five faces are exactly
the five weights the CSS already asked for, because the scale grew up against
Segoe UI in the first place. Courier Prime ships **two** weights exactly as
Courier New did, which is what made it a safe swap: everything ≤500 still
resolves to Regular and >500 still jumps to Bold, so the four places that
compensate for that with a stroke rather than a weight (`_recipe-list.scss:98`,
`_recipe-header.scss:237`, `_palette.scss:113`, `_buttons.scss:101`) kept working
untouched. Rejected: Open Sans (Helen: "aggressively blah"), Cousine (Courier
New's metrics on Liberation Mono — the measurements without the character),
Myriad Pro (commercial Adobe, cannot be self-hosted in a public repo).

#### 13.10.1 `$font-label` — the rule, and the five elements that failed it

**IBM Plex Mono is for numbers you act on.** Ingredient amounts on food, drink
amounts on cocktails, the temperature readouts and axis ticks on the doneness
charts, the inputs and results of the timings calculator. Nothing else — not
labels, not badges, not buttons, not note labels.

**Settled 2026-09-02, Helen:** "Please apply Plex amounts on the drinks page,
and the doneness charts and timing calculator. Send note labels back to
Courier." Every consumer as of that decision:

    food/_recipe-annotations.scss   .ingredient-amount
    cocktails/_cocktail.scss        .cocktail-amount
    food/_temperature-chart.scss    .tc-value, .tc-tick
    food/_timings.scss              .ct-field input/select, .ct-total,
                                     #ct-table td:last-child

It took two rules and a run of five returns to find. This variable was
`$font-recipe-title`, then over three days owned badges, tag buttons, category
labels, filter states, two status messages and the index titles. **Every one
came back**, and the returns are worth more than either rule tried on them:

- `.category-label` failed on **size**. At 1.35rem it was the largest thing
  wearing the face, and Plex at display size reads as a *heading* font — the one
  thing it must not do.
- `.btn-tag` / `.btn-star` / `.btn-meta` failed on **pairing**. A filter tag and
  the same word on a recipe row are one idea twice and must match; the ingredient
  search input is Courier as well. Helen's diagnosis is the sharp one: "this
  actually seemed fine when the fonts were more different." Courier New and Plex
  Mono were far enough apart to read as deliberate. Courier Prime and Plex Mono
  are close enough that the same difference reads as an accident.
- `.badge` failed the same way, pairing with the filter button that matched it.
- `.recipe-title-link` failed on **nothing measurable**. Helen, after two days:
  "I could justify it intellectually by counting font groups, but it could well
  be that I got used to seeing the typewriter effect and now I miss it." The
  justification turned out to be the good one.
- **`.note-label` failed last, and took the longest to notice.** It held the
  face from 2026-08-24 until this decision — a real functional win at the time
  (Plex's larger x-height reads better than Courier Prime at 0.62rem uppercase)
  — under the rule this section used to state: "is this on a recipe page, and
  something you look at with your hands full?" A note label passed that test
  for a year of not being looked at closely, because on food's own pages the
  test and the real rule happened to agree for every OTHER element too. It
  stopped agreeing the moment Plex was asked onto a temperature reading and a
  calculator result — neither is "a recipe page" and both are obviously
  correct — which is what exposed the old rule as a proxy for the true one
  rather than the true one itself. `.note-label` is a word ("TIP", "MAKE
  AHEAD"), not a figure, so it went back to Courier the same day.

**So the test for a new consumer is not "is this a label", and it is not "is
this on a recipe page" either — both lost to the plainer question underneath
them: is it a number you act on?** Every element in the list above that failed
was a label of some kind, on a recipe page or off it. Every element that has
actually held the face — food's amount, cocktails' amount, a temperature
reading, an axis tick, a calculator input or result — is a figure someone
reads in order to do something with it.

The clash only works while Plex Mono stays the minority face. It now has more
consumers than it did under the old rule, across both sites and off the
recipe page entirely, but the shape hasn't changed: everything you *read* to
decide something is still Courier or body prose, and only the number you act
on next wears the third face.

#### 13.10.2 The emboss, and the ceiling on the highlight

Values live in `_sass/shared/_rule.scss` and were tuned by eye at `/dev/emboss/`,
not argued for:

    $emboss-stroke        0.016em      (was 0.014em against Courier New)
    $emboss-offset        1px
    $emboss-offset-large  1px          (was 2px; 2px read as two letters)
    $color-emboss-shadow  rgba($color-text, 0.68)   (was 0.38)
    $color-label-stroke   lighten($color-text, 30%) (was 20%)

**`$color-emboss-light` is `$color-white`, and the reason is a ceiling.** It used
to be `$color-bg` — "the paper catching the light", right as a model and
*invisible in practice*, because a copy painted in the background colour and
offset over the background cannot be seen. It only ever did visible work where a
heading sits on something else. Helen, comparing against the header wordmark:
"we're still missing the white up and left from the simulated light source." She
was right and it was never going to appear: `.site-logo-word` is light type on
black tape and has the whole brightness range; **dark type on #faf7f8 has about
3% of headroom and no more.** `$color-white` spends all of it. A stronger
highlight needs a darker ground, not a bigger number — so on a light ground the
raised read has to come from the *shadow*, which is what 0.38 → 0.68 did.

**`.on-dark` inverts the whole thing, and it is custom properties for a reason.**
The two grounds disagreed on every value, because they are inverse problems: on
dark, a dark shadow is invisible and the *light* copy does everything. Sass
variables resolve at compile time and cannot be overridden by context, so the six
values are custom properties on `:root` and `.on-dark` re-points them — reaching
any nesting depth, in any partial, including ones written later. A
`.on-dark h1 { … }` block would have had to out-specify thirteen component rules
and would have missed the fourteenth. **Both `shared/_rule.scss` and
`food/_rule.scss` emit their blocks behind an emit-once guard**, because
`food/_timings.scss` imports them again — free while they were pure definition
files, not free once they emitted CSS.

> ### `.on-dark` IS DELETED — 2026-09-02, #469 closed, and it WORKED
>
> The class never had a consumer: one swatch on `/dev/emboss/`, gone
> 2026-08-26, then nothing. Its four values were finally exercised for real on
> the dev stages where Helen judged the black cocktails headings, she approved
> them, **and they are `_sass/cocktails/_rule.scss`'s defaults now.**
>
> **THE FINDING IS WHY IT GOES RATHER THAN GAINING A USER: a dark SECTION on a
> light site wants a context class; a dark SITE wants its palette inverted**,
> after which every shared partial follows for free and the class has nothing
> left to do. Four numbers are safer in a palette that renders on every page
> than in a class nothing renders. Recover it with
> `git show 0b350c3:_sass/shared/_rule.scss` if food ever wants a dark section —
> the mechanism is still right, and it is described in place.
>
> **Of the three things #469 said would bite, one is fixed and one is not.**
> `.site-logo-word` reads custom properties now, so the wordmark is reachable.
> `shared/_base.scss` still hardcodes `$color-text` on plain `h1/h2/h3` — which
> costs nothing on an inverted SITE, because `$color-text` inverts with it, and
> would still bite a dark SECTION. The third — that the numbers were unverified
> — is spent: they have been looked at on real content and kept.
>
> **THE INSTRUCTION THAT USED TO BE HERE IS THE LESSON.** From 2026-08-26 this
> paragraph and the code both said to delete the block "if a dark section still
> has not appeared", and on 2026-09-01 that was withdrawn because one nearly
> had. A stale *description* misinforms the next reader; a stale *instruction*
> sends them to do a thing. **When you write "do X if Y", Y is a fact about the
> day you wrote it, and nothing re-evaluates it.** Record the condition and who
> can rule on it; do not pre-authorise the action.

The paragraph above describes the class in the past tense. What remains true is
the MECHANISM: the two grounds are inverse problems — on dark, a dark shadow is
invisible and the *light* copy does everything — and Sass variables resolve at
compile time and cannot be overridden by context, which is why these six values
are custom properties at all. That is what let cocktails invert without a single
`.cocktails h1 { … }` override anywhere.

#### 13.10.3 `/dev/emboss/` — tune here, not in a mock

Local only (`_dev/`, `output: false` in production). **It tunes the tape
wordmark now, not the headings** — `.site-logo-word` lives in the shared header,
which this page renders like any other, so the dials override the live element at
the top of the page rather than a copy of it. The panel writes the settled values
out as real SCSS.

The heading dials were here too until 2026-08-26 and were deleted at Helen's ask:
with both panels stacked she could not get the wordmark and its own controls on
screen together, which for a look-at-it page is the only thing that matters.
Recover them from git history if the smaller type levels ever want tuning — the
heading emboss values themselves are settled, in `_sass/shared/_rule.scss`.

Deleting them also took `.on-dark`'s only consumer with it; see §13.10.2.

That distinction is load-bearing. Its predecessor, a standalone file in `tmp/`,
reproduced the treatment by hand and applied the **stroke only, with no shadow** —
so Courier Prime looked flat and the fault looked like the font's. It cost an
exchange. **The emboss is stroke *and* a two-copy directional shadow**; the
stroke sets the weight of the edge, the shadow sets its direction, and a
reproduction is a second thing to keep in step with the first.


## 14. Reference pages and the internal-temperatures data layer

Built 2026-08-11–12, at Helen's request — the "standalone page for
cross-recipe reference material" §4.1 mentions was hypothetical until now.

> ### ⚠ RESTRUCTURED 2026-08-19 — the six issues below are DONE
>
> This section was rewritten in place rather than annotated, so what follows
> describes the layer as it now is. Recorded here only so a reader who
> remembers the old shape knows what moved and does not go looking:
>
> - **#382** `food/reference/cooking-methods.html` is **deleted**. Nine of its
>   twelve sections were a genuine duplicate of the calculator — verified, not
>   assumed: the calculator's protein list is exactly the nine that had method
>   tables. The steak table was **dropped** (Helen: "I know how to cook
>   steak"). Fish and shellfish **moved onto the methods page**, since nothing
>   else on the site holds them. `_includes/food/method_table.html` went with
>   the page, being its only consumer.
> **The old filenames are still in this section where it describes HISTORY, and
> that is deliberate — but nothing below should name a LIVE page by one.** Five
> places did until 2026-08-21, two days after the rename. Beware especially that
> there have been two different pages called `internal-temperatures`: the
> original combined tables page, retired 2026-08-14, and the current charts
> page, renamed back to that name by #384 on 2026-08-19.
>
> - **#383 / #384** both surviving pages were renamed, files and permalinks:
>   `/food/reference/cooking-methods-and-timings/` and
>   `/food/reference/internal-temperatures/`. **There is no redirect from
>   either old URL** — no redirect plugin here, and one was not added for two
>   renames. An external bookmark 404s.
> - **#385 / #386 / #368** the footer link is "methods and times"; every
>   section crosslink now reads "cooking methods and timings →"; the duplicate
>   crosslink under the contents list is gone.
>
> **This overturned "they do not merge"** (#207, 2026-08-15), which used to sit
> at the end of this section and has been rewritten with it. That ruling was
> about the calculator versus the tables and it still holds for the calculator;
> #382 was the newer call about the PAGE, and it won.
>
> **`groups` and `groups[].columns` are GONE from `cooking_methods.yml` as of
> 2026-08-21, issue #400** — and the shape of that job is the part to carry.
> The deleted include was their only consumer, so the issue called them dead
> data and asked for their removal. That was right about the RENDERING and
> wrong about the CONTENT: `groups` held 35 paragraphs, 1,942 words and 14
> outbound links, of which 14 paragraphs were sourcing notes naming where each
> timing figure came from — Delia Smith, Waitrose, Gressingham, the American
> Lamb Board. Original research, existing nowhere else, invisible on the page
> for eight days and making up 30% of the JSON blob shipped to every visitor.
>
> So it moved before it was deleted, to
> **`food/reference/cooking-methods-prose-archive.html`, committed but not
> built** (`published: false`). All 35 paragraphs are byte-identical and all 14
> links survived — checked, because the links live INSIDE the sourcing notes
> and are exactly what a careless copy loses without changing a visible word.
> The JSON blob in the built page dropped from ~56 KB to 39 KB.
>
> **Three guards followed the content rather than retiring with it**, and one of
> them is the lesson: `test_every_method_belongs_to_a_declared_group` did not
> fail when `groups` left, it PASSED — it skipped any protein with no declared
> groups, and suddenly none had any. A test reporting green having compared
> nothing. It now checks `method.group` (which is live, read by
> `cook-schedule.js`) against the archive's headings, so the archive cannot rot
> away from the data either. `test_group_columns_are_all_renderable` was retired
> earlier rather than left passing over a template that no longer exists.
>
> **`published: false` pages are excluded from `test_page_links.py`**, which the
> archive exposed: an unbuilt page has no URL, so its relative hrefs have no base
> to resolve against, and all fourteen reported as broken. The exclusion drops
> such a file from BOTH sides — its links go unscanned AND it stops counting as a
> valid link target, because otherwise every link INTO an unpublished page would
> pass here and 404 in production.

### What exists

`food/reference/` holds **two** pages as of 2026-08-19:
`internal-temperatures.html` (permalink `/food/reference/internal-temperatures/`,
the charts) and `cooking-methods-and-timings.html` (permalink
`/food/reference/cooking-methods-and-timings/`, a weight → schedule calculator,
plus the fish and shellfish tables that outlived the third page). There is no
`index.html` — deleted 2026-08-15, issue #218 — so there is no
`/food/reference/` landing page, and there is no top-level nav link into this
layer at all: Helen's own call, made the same day, closed issue #213 as
won't-do-for-now. **That is a decision to record, not a plan to build towards**
— she may revisit it — but as things stand nothing points a visitor at these
pages except a direct URL, the two footer links, or a link from inside one of
them.

**Fish and shellfish are on the calculator page but are not OF it**, and the
page says so in a line of its own. The protein dropdown lists nine roasting
proteins and will never list these two: fish is governed by thickness and
shellfish by the shell opening, so there is no weight to schedule from. Helen's
framing, 2026-08-19, when asked where they should go: "it's good to have the
reminder about options of how to cook... they still have methods so they go on
the methods page." Without the line saying why, two tables under an instrument
read as a section of it whose controls have gone missing.

`sustainability.html` does not exist, and never became a finished page.
It was removed entirely 2026-08-15, issue #224 — the page, its two "See
also: sustainability" links from `cooking-methods.html`, and every other
reference to it. It went from ingest to deletion without ever being
fact-checked (below); if a future session finds the old draft table and
is tempted to rebuild the page from it, treat that as starting from
scratch, not restoring something that was once verified.

`internal-temperatures.html`, the original single page charting these
figures, is also gone — split in two on 2026-08-14 (issues #183/#189/
#202) into `temperatures.html` and `timings.html` above, because it had
outgrown one page: one half is "what's the safe/target number", the
other is "given a weight, when do I put this in and take it out", and
conflating them made neither easy to scan.

Same `site_key: food` inheritance as every other page under `food/`
(§2.4). Content was originally ingested from 15 draft tables in
`_food_drafts/reference-info/` (chicken/turkey/goose/duck roasting,
beef/pork/lamb/ham roasting and slow-cooking, steak, fish and shellfish
cooking, fish and shellfish sustainability, meat carbon, nut milks) — the
sustainability table is part of that same original ingest, and is the one
table that never became a surviving page; the rest of this section is
about what the others became.

**Page pattern**: reuses `.recipe`/`.recipe-body-content`, the same
wrapper `about.html` already used for a prose page — no new page
type invented. Tables are `<table>` markup, not markdown pipe tables:
`food/*.html` files aren't run through kramdown (only `.md` is), so a
markdown table in one of them renders as literal pipe characters, not a
table. **`internal-temperatures.html` holds no `<table>` at all** — checked, not
assumed: every figure on it is a div-based chart drawn by
`_includes/food/temp_row.html` from the data, which is why
`tests/test_rendered_pages.py` asserts on `.tc-row`/`.tc-out-at` rather
than on cells. `cooking-methods-and-timings.html` is the mixed one: its eight timing
sections render from data, and its three remaining `<table>`s — steak,
fish and shellfish — stay hand-written on purpose, because they carry no
timings to reconcile and the fish table's eleven rowspans would not
survive a generic loop. No table CSS existed anywhere on the site before this
— `article.recipe .recipe-body-content table`/`th`/`td` plus a
`.table-scroll` horizontal-scroll wrapper, both in
`_sass/food/_recipe-notes-body.scss`.

**How a reader reaches these pages.** Until 2026-08-16 they were reachable
only from a recipe that happened to be wired to one, or from each other —
nothing on the index or in the nav pointed at the reference layer at all.
Issue #272 added two links in the footer ("internal temperatures", "times and
methods") under the site's own bracketed word, driven by `reference_links` in
`_data/sites.yml`; a site without that key renders nothing, the same
absent-means-nothing convention `footer_svg` and `about_url` already use.

Deliberately the footer and not the nav, and Helen's framing settled what had
looked like a tension with "what to cook, not how to cook": these pages would
not teach anyone to cook, they are look-up material for someone who already
does — used "when I'm planning out what I've decided to cook, and when I'm in
the kitchen about to be covered in raw chicken". A nav slot would have made
the reference layer a peer of the two sites. The block is asymmetric (food has
links, cocktails has none) and that is an open question, not an oversight.

### The data layer — two datasets now, not one

`_data/food/internal_temperatures.yml` is the single source for out-at
temps, endpoints and carryover — VOCABULARY layer, same status as
`taxonomy.yml` (§7). Read by two things: `internal-temperatures.html` (every
number on the page is a Liquid lookup into this file, not a literal) and
`recipe.html` (a recipe's own `internal_temp_ref` + `doneness` front
matter, below). **"Out at", never "pull at"** — Helen's call, 2026-08-13:
pull is American. The data fields are `out_at` / `out_at_min` /
`out_at_max` / `out_at_open`, and `tests/test_style.py`'s
`_INTERNAL_TEMP_RE` knows the phrase so a recipe writing it into a method
step isn't flagged as an oven temperature missing its "fan". Every figure
is numeric as well as a display string — `out_at: "48–50°C"` sits beside
`out_at_min: 48` — deliberate duplication, because the display strings
carry words a number can't ("74–75°C in the thigh"), guarded by
`tests/test_reference_data.py`, which also holds the axis bounds, the
safety-threshold spec and the note-integrity checks.

Four shapes, because the source data wasn't uniform: `endpoint` +
`carryover` (whole poultry — one figure, no doneness choice);
`doneness: { level: {out_at, rested} }` + `carryover` (beef/pork/lamb
tender roasts, ham fresh, steak, salmon, tuna — a real doneness
spectrum); `tender_at` alone (tough/slow-cooked cuts — collagen
breakdown, not an out-at temperature); `target` + `carryover` (cured ham
— one figure, not a spectrum). A consumer checks which keys exist on the
resolved node rather than assuming a shape from the protein name — see
the file's own header comment.

**The calculator page has a data layer of its own — it is no
longer true that only internal temperatures are data-backed.**
`_data/food/cooking_methods.yml` **IS THE SOURCE OF TRUTH AND IS EDITED BY
HAND.** `scripts/build_cooking_methods.py` and
`scripts/build_cooking_methods_prose.py` are MIGRATION TOOLS, not generators to
re-run: they are pinned to commit `8bdbd27` — the last version of the old
`cooking-methods.html` that still held its tables by hand — and running either
against the working copy finds no tables and writes an empty file. The pin has
an assertion on the table count, and that's why; don't remove the pin to "fix"
the assertion.

**Do not re-run them at all.** The data file has been hand-edited since the
migration — the whole `venison` section and the file's own header comment exist
in neither script's input — so a re-run overwrites rather than regenerates it,
dropping 166 lines. Both scripts said "edit this script and re-run" until
2026-08-21 and now say the opposite; see §12's trap on generators that have
stopped generating. Steak, fish and shellfish stay hand-written tables
deliberately: they carry no timings, so there's nothing in them to
reconcile against the data, and fish's table uses eleven rowspans and
several empty cells that a generic rows-loop would silently flatten into
a different table. Only these two pages have moved to a generated/
data-backed pattern; don't assume a future third reference page works the
same way underneath just because these two do.

### Recipe wiring

`internal_temp_ref` is a dot-path into the data file (`beef.tender_roast`);
`doneness` (optional) picks a level within that entry's own `doneness` map
(`medium_rare`). Resolved in `recipe.html` — but **not into a metadata
line any more**. It used to render an "Internal temp" line in
`recipe-meta`, alongside Serves/Prep/Cook; Helen, 2026-08-14: "I don't
like the internal temperature featuring in the metadata — it's ugly, it
spoils the rule of 3, and it's nowhere in sight when you're actually
cooking." All three were true, and the last is the one that decided it —
that grid is read once, while deciding whether to cook the thing, while a
temperature is read with a probe in your hand, twenty minutes in. The
resolved figure (a doneness spectrum where the data has one, a single
point otherwise) now renders below Notes, at `#doneness`, and the
metadata grid carries nothing but a link: the Cook line reads something
like "30 mins, but check cooking temperatures" rather than stating a
figure inline.

**Why a live number can only ever render somewhere the layout itself
controls, never inline in a method step or note**: front matter is never
Liquid-templated (§4) — a value from the data file can only appear
somewhere `recipe.html` itself decides to put it, not inside text the
recipe author typed. Real constraint, not a design choice; don't try to
thread a live figure into a method sentence, it can't work without
changing that rule. Only the *location* the layout chooses has moved
(metadata line → below Notes) — the constraint that forces it to be
layout-controlled at all hasn't.

Opt-in, per recipe, not rolled out — a minority of published recipes are
wired, added by more than one session working on this in parallel since
2026-08-12. Check a given recipe's own front matter rather
than assuming a protein has or hasn't been wired. **A recipe that should
be wired and isn't is a test failure, not a gap to notice by eye**:
`test_every_recipe_with_a_known_protein_has_a_temperature_or_a_reason`
(`test_reference_data.py`) demands either an `internal_temp_ref` or an
entry in that file's `NO_TEMPERATURE_BECAUSE` dict giving a reason.
Drafts are deliberately exempt — Helen, 2026-08-14: wiring one is wasted
work until she's cooked it. The test catches each draft on the day it's
promoted, which is the right moment.

**`NO_TEMPERATURE_BECAUSE` has THREE kinds of entry, and the third is new and
easy to miss.** The first two are "not the dish" (the protein is a stock or a
garnish) and "a cut the data doesn't cover" — both say, in effect, that no
figure exists. The third says a figure exists and still does not apply, and
`youvetsi` is its only member: it is bone-in short rib, so `beef.tough_cuts`
(the collagen-breakdown figure, 90–96°C, for exactly short rib and pot roast) is
correct about the cut. It was wired to it on 2026-08-21 and unwired the same day
by Helen, cooking the dish, having stopped taking the meat off the bones —
*"it'll just fall off at the end, being whatever temperature the pan sits at for
3 hours"*. **A figure can be right about the cut and useless in the method**, and
nothing in the data can see that: three hours in a covered casserole has no
moment where anyone probes anything. The wiring was not wrong, which is why no
test caught it and why it took the person actually cooking. If you meet an entry
here, read its reason before assuming it marks a gap in
`internal_temperatures.yml` to be filled.

**Guard tests**: `test_internal_temp_ref_resolves` (`test_front_matter.py`)
+ the `internal_temperatures` fixture (`conftest.py`) — same pattern as
`test_tags_are_declared` (§7). Liquid's `hash[variable]` lookup has no
equivalent of a KeyError, so a typo'd path doesn't error, it silently
renders no doneness section at all; this is the only thing that catches
that. `tests/test_rendered_pages.py` asserts on BUILT HTML rather than on
the data or the template source, and exists because the two worst bugs in
this layer both lived in the gap between correct data and what Liquid
actually emitted — a `{% assign %}` leaking out of an include onto all 42
chart rows, and a safety zone drawing 9°C off its own label. Both had
passed every data-level test. It skips without a bundler.

**`safety_min` / `safety_label` / `safety_summary` shade everything below
the cited guidance** on `fish.salmon` (63°C), `pork.roasting` and
`ham.fresh` (70°C) only — beef, lamb and steak have none on purpose, since
UK guidance treats pink as fine for those. This used to be a hard-coded
`--t:63` in one page's markup, which meant it couldn't warn anywhere
else; it's data-driven now, with two guards stopping it going missing
again.

### Fact-checking status — read before trusting a number on either page

Every figure on `internal-temperatures.html` and
`cooking-methods-and-timings.html` has been
checked at least once against real sources (UK FSA, USDA FSIS, Waitrose,
BBC Good Food, Delia Smith, Jamie Oliver, Gordon Ramsay and others — cited
under each table via `<p class="recipe-source">`). A systematic error was
found and corrected 2026-08-12: turkey, goose, beef's standard roast,
pork's leg/tenderloin, lamb's rack, and cured ham's boil/roast timing were
all roughly half the real rate. Helen's own recollection is that an
earlier session muddled 500g/lb timings with 1kg timings when the drafts
were first written, and the shape of the error (consistently ~2× too
fast) matches that. If you find another row that looks suspiciously fast
against a real recipe, this is the first thing to suspect.

**The "checked once... remove once confirmed" notes under each table are
Helen's own working scaffolding, not errors to fix.** She's verifying each
cited source herself over time and will strip a note once she has. Same
standing rule as `QQ` (§4) and `test_ingredient_notes_are_lowercase_fragments` (§10) —
don't "helpfully" remove one unprompted.

**Two flagged, not fixed, food-safety gaps**: pork's "medium" doneness
(60–62°C) and fresh ham's "hint of pink" doneness don't clear the UK FSA's
pork-specific core-temperature guidance, unlike beef/lamb, which FSA
treats differently — `internal_temperatures.yml`'s `safety_note` fields on
`pork.roasting` and `ham.fresh` have the detail, and the same two entries
carry the `safety_min`/`safety_label`/`safety_summary` fields that shade
the chart past that line on `internal-temperatures.html` (above). Deliberately not
"corrected" to the well-done figure — whether to keep serving pork pink is
Helen's call, not something to silently override.

### The timings calculator and doneness

`cook-schedule.js` has always taken a `doneness` argument; `cook-timer.js`
opened `render()` with a literal `var doneness = "rare";` and shipped no
control, so every `medium` rate in `cooking_methods.yml` was sourced, checked
data that nothing could display (issue #246, fixed 2026-08-16).

**Only 2 of 73 methods have the `by_doneness` shape** — beef's standard
constant roast and venison's haunch — and that number decided the design. A
rare/medium control would be a page-level widget that changes nothing for
seven of the nine proteins, and a control that usually does nothing reads as
broken. Helen's call: show both figures on those two cards, add no control.

`resolve()` now returns a `levels` array alongside the existing `lo`/`hi` and
aside, which still describe the single requested level — **additive on
purpose**, so `orderMethods` keeps sorting on one consistent figure and every
existing caller and test sees what it saw before. Levels come out in data
order, not alphabetical: the yaml lists rare before medium, which is the order
the rates rise in; alphabetical would put medium first and make it look like
the default. If a third level is ever added to a row, it renders with no code
change.

### What's not done

**Venison and braised/confit duck legs have no temperature data.** Four
recipes want them and are deliberately unwired rather than pointed at an
approximation: two venison, a duck-leg casserole and a confit. Roasted
duck legs DO now use `poultry.duck` — Helen, 2026-08-14: the figure says
"in the thigh", which is exactly what a leg is. Venison has its own
issue.

**Almost nothing links recipes to the methods page.** Temperatures are wired
both ways. Exactly one recipe links the calculator
(`christmas-roast-turkey-lemon-parsley-garlic.md`, a relative link from a method
step); nothing else does.

**THE OVERLAP THAT WAS "SETTLED" IS GONE, BECAUSE ONE SIDE OF IT IS.** Until
2026-08-19 this section ended by recording issue #207 (2026-08-15): the tables
page and the calculator both rendered the same 65 methods from the same data,
one as tables and one as an instrument, and Helen's call was that **they do not
merge** — the tables answer *what are my options*, the calculator answers *what
time do I put it in*, the same control-panel/document split the index and a
recipe page already make.

Issue #382 (2026-08-19) deleted the tables page. That is not a reversal of the
reasoning so much as a decision that the *what are my options* side was not
earning a page: nine of its twelve sections were the same data the calculator
already renders, and Helen's read on the rest was that she does not need to be
told how to cook a steak. What genuinely answered a question nothing else did —
fish and shellfish, neither of which has a weight-driven schedule — moved onto
the calculator page and is still there.

**The lesson worth keeping from #207 is the one about crosslinks, not the one
about pages.** Two views of one dataset need to point at each other well; that
is why every protein section on the temperature charts carries its own
`?protein=` link into the calculator. Keep that up. If a future session wants to
rebuild a tables view, the question to answer first is which question it
answers that the calculator does not.
