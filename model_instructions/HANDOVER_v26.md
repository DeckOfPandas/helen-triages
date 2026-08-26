# HANDOVER v26

**Helen Triages** — a Jekyll mono-repo serving two personal decision-support
sites. **Food** answers *what shall we cook*, not *how do I cook*. **Cocktails**
is its sibling: it has real drinks and a schema now, and almost no styling.
Written 2026-08-02, revised 2026-08-21. Supersedes v25 — deleted, not kept, per
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
> **§12 is the traps section.** Read it before you touch anything — it is the
> most re-used part of this document. (This box said "§10" from v26's first
> draft until 2026-08-21, pointing every reader at the validation section
> instead. §10 is worth reading too, but it is not the one being recommended
> here.)

**One companion document: `SOURCE_ATTRIBUTION_SPEC.md`.** It is the full
contract for `source` and `source_type` — the eight types, the exact string
shape each one dictates, and the date rule that separates a `publication` from a
`website`. §4 summarises it and deliberately does not repeat it. It exists
because ingestion sessions need the citation rules without reading 3,500 lines
of this.

**This paragraph said "No companion documents" until 2026-08-21**, having been
written before that spec existed and never revisited — while §4, four hundred
lines later, cited the file by name. Its own last sentence said to run
`ls model_instructions/` before trusting it, and nobody did, which is the
smaller lesson inside the larger one: **an instruction to verify is not
verification.**

Two older companions are genuinely retired. `RECIPES_SEEN_v23.md`, a
slug/publish-status inventory, went on 2026-08-11: it saved compute during large
batch ingests from photos, back before the Max plan made that a non-issue.
`DEV_JOBS_v26.md` went on 2026-08-10; the backlog is on GitHub Issues now. Run
`ls model_instructions/` anyway — and this time actually run it.

---

## 1. How to run it

```
jekyll-local        # port 4001, drafts visible — the working view
jekyll-prod         # port 4002, exactly what deploys — no drafts, no meta filters
pytest              # content and structure checks
.node-runtime/node/bin/node --test     # tests/js/*.test.js — no arguments, not system node
```

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
_data/        sites.yml   accented_words.yml   food/*.yml   cocktails/taxonomy.yml
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
(gitignored from this one — see `.gitignore`), pushed to a separate private
GitHub repo. `output: false` only stops Jekyll rendering them; the repo
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
"one method line"**, as this said until 2026-08-16: see §9.6); `_data/food/*.yml` vs `_data/cocktails/*.yml`;
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
| `assets/js/filters.js` | DOM wiring for all of the above | Not directly tested; exercised by hand |

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
serves: 4                        # xor makes: — never both
prep_time: "20 mins"
cook_time: "1 hr 30 mins"
main_ingredients: ["cavolo nero", "butter beans", lemon]
star_ingredient: greens          # optional; ~a quarter are legitimately blank
internal_temp_ref: beef.tender_roast   # optional; see §14 — most recipes have neither this nor doneness
doneness: medium_rare                  # optional, only alongside internal_temp_ref; see §14
tags: [soup, "one-pot"]
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
  awaiting_fix: false            # true  = do not publish this page at all
  proofread: false               # false = Helen has not blessed THIS text
```

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
once she says so, same reasoning as the `proofread` rule in §4.0. Considered
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
before matching (§12, and the constant's own comment), `meta.rewritten` is on
the list, and **the measurement taken before adding it was that it releases
ZERO recipes from `proofread: false` today** — it is purely forward-looking,
which is exactly the condition under which widening that list is safe.

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

**A recipe publishes only if it says `awaiting_fix: false`. Nothing else
publishes.**

Not "true hides it" — **false is the only thing that lets it through.** The flag
missing, the flag left under its old hyphenated name, the value quoted as a
string: all held back. `_plugins/hide_awaiting_fix.rb` removes the document from
its collection at `:post_read`, so it gets no URL, no sitemap entry and no place
in `site.food_recipes`.

**It fails CLOSED, and it used to fail open.** Helen's call, 2026-08-18. The
first version hid a document only on an explicit `true`, which meant every way
of getting the flag wrong ended with the page live — a missing key was
indistinguishable from a deliberate clearance, and `awaiting_fix: "true"` is a
string that never equals Ruby's `true`, so it published the page you had just
flagged. This is the gate that decides what the world sees; the cost of failing
closed is that a new recipe does not publish until someone writes
`awaiting_fix: false`, and that is the right cost.

**`GATED_COLLECTIONS` is `food_recipes` and `cocktail_recipes` only, and the
scoping is not optional.** Fail-closed applied to every collection would delete
the entire site: `dev` pages carry no `meta.awaiting_fix` at all, and plenty of
drafts don't either. Drafts and dev pages have their own `output: false`
protection and need no gate regardless of whether they happen to carry the key.
(A growing number of drafts DO carry one anyway, used informally as a personal
"needs more source material, don't promote yet" note — no plugin reads it
there, so it's Helen's own bookkeeping, not enforcement.)

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

**The test's scope is `_food_recipes/` only — the rename never propagated
through `_food_drafts/`.** As of 2026-08-21, roughly 90 pre-existing drafts
still carry the old hyphenated `awaiting-fix`, uncaught, because nothing scans
drafts for it. Concretely dangerous while ingesting: copying an existing draft
as a template for a new one silently copies whichever spelling that draft
happened to have. A same-day ingestion session did exactly this across 34 new
files before catching it. Always write `awaiting_fix` (underscore) on any new
draft regardless of what the file you copied from uses — it costs nothing now
and it's the only spelling that still works once the file is promoted.

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
  method step starts with `QQ PLACEHOLDER `.** Restated 2026-08-18 because
  the practice had drifted: the prefix is `QQ PLACEHOLDER ` and it goes on
  the METHOD STEPS, not just on the odd field somebody noticed was rough.

      method:
        - "QQ PLACEHOLDER Heat the oven to 180°C fan and grease a 20-cm tin."
        - "QQ PLACEHOLDER Cream the butter and sugar until pale."

  The point is that a transcribed step is not a finished step even when it
  reads perfectly well. Helen rewrites every one into her own voice, and
  ingested text that happens to scan cleanly is exactly the kind that slips
  through un-rewritten — so the marker goes on at ingest time, on all of
  them, and comes off one at a time as she rewrites.

  `test_no_qq_placeholder` (§10) catches any that reach `_food_recipes/`.
  Drafts may carry it indefinitely; that is what drafts are for.

  One marker, not two. Older drafts (roughly 190 files, predating this
  convention) say `PLACEHOLDER - rewrite: ...` instead — leave them alone,
  see §12 on not tidying a draft unprompted, but write every new ingest as
  `QQ PLACEHOLDER `. (This is the exact
  convention already in wide use across `_food_drafts/` — as of 2026-08-10
  it's still written there as `PLACEHOLDER - rewrite: ...` in roughly 190
  files, predating this paragraph existing at all. Those weren't
  bulk-converted — see §12 on not tidying a draft unprompted — but
  every new ingest from here on uses `QQ`.)

  **Interleaved original/rewrite variant, established 2026-08-21.** When
  Helen wants the source wording and the paraphrase visible side by side
  (e.g. to judge rewrite quality directly, rather than trusting it blind),
  write each step as a PAIR of consecutive entries instead of one bare
  `QQ PLACEHOLDER ` line:

      method:
        - "QQ original Heat the oven to 180C fan and grease a 20cm tin."
        - "QQ Claude Heat the oven to 180°C fan and grease a 20cm tin."

  `QQ original` is copied verbatim — same source punctuation, degree-sign
  habits, "minutes" instead of "mins", everything — because the whole point
  is an unedited comparison. Never tidy or house-style a `QQ original` line;
  it will read as broken house style and that's expected, not a bug to fix.
  `QQ Claude` is Claude's own paraphrase and IS held to normal house style,
  same as any other prose it writes. This is a preference to confirm per
  ingest, not a permanent replacement for bare `QQ PLACEHOLDER ` — ask which
  format she wants for a given batch.

  **Generating a `QQ original` line risks "API Error: 400 Output blocked by
  content filtering policy."** Seen twice on 2026-08-21, both times from a
  single large `Write` containing a full method's worth of verbatim
  copyrighted book prose at once. Building the file incrementally instead —
  one step, or one step-pair, per `Edit` call, never the whole `method:`
  block in one shot — avoided it completely across the rest of that session's
  ~30 recipes. Keep the same discipline in any commentary/reasoning that
  quotes the source at length; the trigger isn't obviously scoped to file
  writes alone.
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
  awaiting_fix: false                                     # the publish gate, and nothing else
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

**`meta:` is ONE flag here, not three.** `rewritten` and `proofread` are recipe
flags with no meaning for a dish that has no source and never left Helen's own
head — and a flag that can only ever hold one value is precisely what
`test_front_matter.py`'s `cooked_before` tombstone warns against. `awaiting_fix`
stays, and `food_magic_bag` is in the plugin's `GATED_COLLECTIONS`, because the
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
- **The three meta filters.** "needs rewrite", "needs proofread" and "no short
  method" all mean *this recipe isn't finished yet*. On the defaults an entry
  answers true to all three and pads every one of those working lists with
  dishes that can never leave them. `data-meta-short` is **three-valued now** —
  `'true'`, `'false'`, `'n/a'` — because that filter is a PAIR whose halves want
  opposite answers, and only a third value fails both. `filters.js`'s no-short
  branch requires an explicit `'false'`; reading it as `!== 'true'` is the
  natural spelling and is the bug.
- **A `magic bag` badge on the row, shown in production** unlike the two
  work-state badges. Without it a magic-bag row is indistinguishable from a
  recipe row until the page loads and there is no method on it.

**Not covered by any test: `filters.js`.** That file has no unit tests at all
(§3's table says "exercised by hand"), so the three-valued change is reasoned
and hand-checked, not exercised — a production build emits the values in the
right proportions (67 `false`, 19 `true`, 1 `n/a`) but the branch itself has
never been executed by a test. **Issue #506**, which proposes the §3 split:
pull the predicate out as a pure function and test that, leaving the DOM wiring
behind. Exactly the `back-link.js` argument.

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
you'd have to go buy, the vegetable that's the point. Cap at eight. **Not
mechanically enforced** — no test checks the count, so a recipe with a
spice-heavy ingredient list can go over deliberately, case by case, rather
than being forced to cut something that genuinely fails the substitution
test. `indonesian-chicken-curry-gulai-ayam.md` (11) and `citrus-soy-salmon-
sticky-rice.md` (12) both sit well past the cap — Helen's explicit call
(2026-08-02 and 2026-08-09 respectively): everything in each is a "would
have to specifically go buy" ingredient, so nothing was a good candidate to
cut. Don't flag either as a violation to fix, and don't expect this to stop
happening — more lists will grow past eight over time as ingredients get
added to existing recipes. The cap is a soft first-pass guide, not something
to defend by cutting a genuine substitution-test ingredient.

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
lifted copy.

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

Known defects in the source, to expect rather than be surprised by: the
Sazerac's last method step is **truncated in the CSV itself** ("Strain the
shaken drink into the absinthe-coated" — and stops), carried as a `QQ`;
`Corvoisier` should be Courvoisier; `La Fee Parisienne` and
`Creme de Pêche` are missing accents that `_data/accented_words.yml` covers
(it lives at `_data/` root precisely because it is house style for both
sites, and `crème` is its own worked example).

### 9.3 Cocktail front matter

```yaml
title: "Sazerac"
tagline: "QQ"                    # the one line of prose; QQ until written
glass:                           # LIST, not scalar — corrected 2026-08-17
  - "rocks"
garnish: []                      # LIST — Cobra's Fang has two
ingredients:                     # FULL list, untriaged, in build order
  - amount: "0.5 oz"             # the quantity AS WRITTEN — display string
    ml: 15                       # the same quantity numerically; see below
    item: "Appleton Estate Reserve"   # what you actually pour, brand-led
    generic: "Jamaican, moderately aged"  # the #314 vocabulary; see §9.3.1
    suggestion: "Pierre Ferrand ambre"  # alternative bottle or category
  - amount: "15 ml"
    ml: 15
    item: "Light aged rum"       # the source genuinely doesn't name a bottle
    generic:                     # a LIST means "or", never "and" — §9.3.1
      - "lightly aged and filtered"
      - "blended multi-region rum, clear"
    suggestion: "Havana 3"       # bottle NAME(S) ONLY — never reasoning, §9.3.1
    note: "Whichever you prefer or are trying to use up"   # the REASON, resolving #457
  - amount: "15 ml"
    ml: 15
    item: "Black rum"
    generic: "moderately aged"
    character:                   # a property of THIS RECIPE'S use of the
      - "blackstrap"             # bottle, not of the bottle in the abstract — #441, §9.3.1
    suggestion: "Gosling's"
method:                          # ORDERED LIST — the steps are sequential
  - "Pour absinthe into ice-filled glass."
to_serve: ""                     # PRESENTATION, not a further instruction
notes:                           # bare strings, as food — DRINK-level, not per-ingredient
  - "This is much less sugar than many recipes"
source: ""
source_url: ""                   # external; nothing verifies it, see §9.6
meta:
  ship: "oh gods yes"            # a real ordered vocabulary now — see §9.5
  date_last_edited: "2026-08-16"
```

**`amount` and `ml` are the same fact twice, on purpose, and want a guard.**
Same idiom as `internal_temperatures.yml`'s display-string-beside-numeric-pair
(§14): the string carries units a number cannot, the number makes ratios and
scaling possible at all. **`ml` is ABSENT wherever the unit is not
volumetric** — a dash is not 0.8 ml in any way worth writing down — so a
consumer must check for the key rather than assume it. Conversions used:
1 oz → 30 ml, 1 tsp → 5 ml. That is bar-standard rounding, not 29.5735;
it keeps ratios clean and it is a decision, not an accident.

**`item` versus `generic`.** `item` is the bottle: "Skippers dark rum",
"Briottet Abricot". `generic` is the category: "Demerara, aged", "apricot
liqueur". No rule can derive the second from the first, which is why it is
stored rather than computed.

~~**Nothing reads `generic` yet.**~~ **OUT OF DATE — corrected 2026-08-22.**
This was true when written and has not been true since #322/#314 landed.
`generic` now has a real, tested, growing vocabulary
(`_data/cocktails/ingredients.yml`, §9.3.1) and 526+ of 594 ingredient
entries are typed against it (#335 tracks the rest). It is still the
cocktails analogue of food's `main_ingredients`, not a copy of it, and
nothing browses by it yet (§9.1's "no star axis" rule still holds) — but
it is a live, populated field, not an aspiration.

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

**Disjunctive `generic` has an agreed threshold, not a free-for-all.**
Helen, 2026-08-21: multi-value only when both bottles can actually be named
and a reason given for each — "I don't know which" stays a plain `QQ`, it
does not become a two-item guess.

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
  its contents move into `method` on ingest, and **none of the first three
  drinks has a real `to_serve`**.
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

### 9.5 Open, and worth deciding out loud

- **`garnish: []` versus stating "none".** The Sazerac's CSV row says `None`
  deliberately, and that is information — "no garnish" is a decision, blank
  is an unfilled field, exactly the distinction food's `cook_time: "None"`
  preserves. Currently flattened to `[]`, which loses it. Putting `"none"`
  in the list instead would pollute any future garnish vocabulary with a
  fake member.
- ~~**`meta.status` and `meta.ship` have no vocabulary.**~~ **OUT OF DATE,
  2026-08-23.** `meta.status` is retired entirely — Helen: "I am perfectly
  well aware of how much work I have done on each drink... it's easy to keep
  track of" — its only consumer anywhere in the codebase was `chaos`'s
  `haven't tried` bucket, which is dropped rather than redefined, since an
  untried drink never publishes. `meta.ship` has a real, ordered, tested
  vocabulary, `ship_scale` in `_data/cocktails/taxonomy.yml`: `not really` <
  `meh` < `sure` < `yes` < `oh gods yes` (`meh` replaced `maybe`/`okay`, which
  "only ever meant the same shrug"). `who knows` and `QQ` are deliberately
  OFF that scale — see the file's own comment. §9.9 is where this vocabulary
  turned into an actual feature.
- ~~**No tests exist for cocktails at all.**~~ **OUT OF DATE, corrected
  2026-08-19.** `tests/test_cocktails.py` exists and is substantial — glasses,
  generics, moods, methods, the `amount`/`ml` agreement guard this paragraph
  asked for. `tests/conftest.py` is still explicitly the FOOD suite; the
  cocktails module carries its own fixtures and its own `cocktails` marker.
  The standing requirement is unchanged and still worth knowing: per
  `test_suite_hygiene.py` a cocktails test must ASSERT its corpus is non-empty
  rather than skipping, or it passes vacuously on a clean checkout where
  `_cocktail_drafts/` is not present.

  **Left visible rather than silently rewritten, as a worked example of §11.2.**
  This claim was wrong for some time, sat in the section a reader would go to
  for exactly this question, and was found only by running `ls tests/`. Do not
  trust this document over the code.
- `_data/cocktails/taxonomy.yml` — check it before repeating this: it was
  described here as "still empty", and moods and generics have since been
  argued out and are enforced by tests.

### 9.6 Two earlier claims in this document were wrong

- **"a cocktail is… one method line"** (old §9, and §2.2's forked-layouts
  paragraph). It is an ordered list. The Sazerac's five steps get a different
  drink if reordered: coat the glass with absinthe, shake the rest, discard
  the wash, strain in.
- **`garnish` is not a scalar.** Cobra's Fang carries a mint sprig AND a lime
  wheel. `_layouts/cocktail.html` assumed one value until real data arrived.

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

### 9.9 The index browses by goodness, and `meta.ship` IS the rating

2026-08-23. Helen asked for "filter buttons on the front page to show me a list
of recipes by goodness, e.g. 'oh gods yes'." The field already existed. `meta.ship`
is not a yes/no publish flag despite the name — it holds her own verdict, in her
own words, and "oh gods yes" was already on 18 drinks. The distribution when this
was built (`okay`/`maybe` collapsed into `meh` in the same session, just after):

    yes 37 · QQ 19 · oh gods yes 18 · meh 17 (was okay 14 + maybe 3) ·
    who knows 12 · sure 6 · not really 5

**The template's own ordering list went stale within the same day.** It
hardcoded `"oh gods yes,yes,sure,okay,maybe,not really,who knows,QQ"` — and
the `meh` collapse landed in a *different, still-unmerged* PR at the same
time. Nothing crashed (an unlisted value "just sorts last", by the page's
own design), but it meant 17 drinks — the single biggest bucket after
yes/QQ/oh-gods-yes — would have silently sorted dead last instead of between
`sure` and `not really` the moment both PRs merged. Caught by rebuilding the
combined state of both pending branches locally before trusting either one
was done; neither branch's own tests could have caught it, because each was
green in isolation. Fixed to `"oh gods yes,yes,sure,meh,not really,who
knows,QQ"`. **Whenever a hardcoded value list and a vocabulary it enumerates
live in different files (worse, different repos), a change to one is a
silent break in the other until someone rebuilds both together.**

**Look for the vocabulary before inventing one.** The whole feature was a
template and a stylesheet; no new field, no migration, and nothing for Helen to
fill in. A rating scale designed from scratch would have been worse AND would
have needed 115 decisions from her.

**The index reads DRAFTS, not recipes**, and this is not a shortcut: there are
115 cocktail drafts and **zero** promoted cocktail recipes, so the previous
index — a bare `<ul>` over `site.cocktail_recipes` — was looping an empty
collection and had been since it was written.

Ordering is declared in the template, not derived. Nothing about the strings
says "oh gods yes" beats "sure". Any value not in the declared list still
renders and still filters, so a word Helen invents mid-session sorts last
rather than vanishing.

---

### 9.10 The ingredient line, for real — #465/#457/#460, 2026-08-25

`_layouts/cocktail.html` renders each ingredient as three parts: **amount +
headline** / **class line, with character folded on** / **note**. Settled by
walking real drink data against "does this get Helen the drink she wants"
(#459) rather than designed up front.

- **Headline** is `suggestion` when present (oxford-joined if a list —
  "Planteray 3, El Dorado 3, or Havana 3"), else `item`. You shop by bottle
  name; an item with no suggestion falls back to itself.
- **Class line** is `generic`, oxford-joined if a list. A rum-family style
  name (looked up live via `ingredients.family_of`, not hardcoded) gets the
  site's heading face — blockier, so the internal comma in "Demerara, aged"
  doesn't collide with a plain list-join comma — with a quiet italic "or"
  between disjunctive options. Scoped to rum on purpose: "cognac" has no such
  collision and stays plain.
- **Character** folds onto the class line as `(character: blackstrap)`, a
  LABELLED parenthetical, never a bare one — "moderately aged rum
  (blackstrap)" reads as if blackstrap were a TYPE of moderately-aged rum,
  real confusion with actual black rum. Never its own line: #441 settled that
  character is a property of THIS recipe's use of a bottle, not the bottle in
  the abstract.
- **Note** is its own line, always visible, no interaction — #457's fix for
  reasoning that used to get smuggled into `suggestion`. Right-alignment was
  tried and dropped: read as competing with the class line above it.

**`generic`/`suggestion` can be a string or a list, and Liquid's `for` quietly
treats a bare string as a one-item sequence** — checked against the real
`liquid` gem before relying on it, not assumed. One oxford-join loop handles
both shapes with no type-detection anywhere in the template.

**Deliberately not solved**: no spirit-word ("rum", "gin") is appended after
a bare style name. Several families already bake their spirit into the
string ("blanco tequila") and others don't ("bourbon" needs no suffix,
"London dry" does) — auditing all of that is real, separate work, not a
template one-liner. No colour decision either — the placeholder monochrome
palette is untouched, unargued on purpose (§9.3.1).

### 9.11 Glass icons — real relative height, and a UA-stylesheet trap

**Sized by real height, not a common rendered height, since 2026-08-25
(#298).** `_layouts/cocktail.html` computes `--glass-icon-height` per drink
from `_data/cocktails/glasses.yml`'s `heights_mm` against the tallest real
glass (counted live every render, not hardcoded), and
`_sass/cocktails/_cocktail.scss` consumes it with 2.6rem as the fallback for
a glass with no entry. `_dev/glasses.html`'s section 2 proved the calculation
out before it reached the real page; section 1 is now the honest "as the
site actually shows it" view, height AND the real 3.2rem width cap together
— it was quietly stale for a day, still claiming "every icon is the same
height here" after #298 shipped, a live instance of §11.2.

**The width cap matters as much as the height, and can make a correctly-sized
glass look wrong without it.** Helen, 2026-08-26, on `_dev/glasses.html`
section 2 (which has no width cap): goblet and mule-mug both looked
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

## 10. Validation — run `pytest`, don't read this

**The suite gates the deploy now (2026-08-18, issue #369).** Until then the
workflow checked out, built, rendered PDFs and deployed with no test step
anywhere, so every guard in this repository protected a local run and nothing
else. `.github/workflows/build-and-deploy.yml` has a `test` job and `build`
declares `needs: test`. Three things about it are load-bearing:

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
| `test_cocktails.py` | The drinks' own spec. **This table omitted it entirely until 2026-08-19**, and §9.5 still said "no tests exist for cocktails at all" — both written before it did |
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

### 10.1 The 2026-08-12 issue audit

Helen's own framing: "I keep getting confused… I'm concerned that issues we
closed in the last few days weren't represented as tests — I wasn't paying
attention, and I'm not sorry, because that's part of the experiment, but I
still don't want to end up in a mess." The finding: of ~35 real (non-PR)
issues closed 2026-08-10 through 2026-08-12, most had a matching test, but
a real cluster didn't — closed by hand, correctly, with nothing guarding
the fix afterward. Method: grepped every test file for `issue #NNN`
citations, diffed that set against the closed-issue list pulled via
`curl` to the GitHub API (read-only at the time; **access changed
2026-08-17** — Claude may now raise, close, comment on, label and assign
issues via a fine-grained token, and nothing else. See CLAUDE.md), then
checked each gap against the actual front matter before deciding whether it
was a real gap, already-satisfied-but-untested, or a false alarm from a
too-strict reading of the issue title.

**Fixed and now guarded** (GitHub issue → test): #147 main_ingredients
egg/eggs count agreement (`test_main_ingredients_egg_count_agrees`,
already-compliant data, pure regression guard) · #144/#145 egg size in
`amount:` (`test_egg_size_is_stated`, one real placement bug fixed) · #149
size word in `amount:` not `item:` (`test_size_word_is_with_the_count_not_
the_item`, five real fixes — apples, lemons ×2, garlic, butter pats, not
just #149's own carrot example) · #135 homemade pastry needs salt
(`test_homemade_pastry_has_salt`, already compliant) · #138 unsalted
butter needs salt or a note (`test_unsalted_butter_has_salt_or_a_note`,
already compliant except one method-step wording nuance) · #171 garlic
form (`test_garlic_specifies_form`, real main_ingredients fixes across 8
recipes) · #173 loomi colour (`test_loomi_specifies_colour`, already
compliant, one user) · #174 method-step notes read as sentences
(`test_method_step_notes_are_sentences`, 18 real fixes across 13 recipes,
the mirror-image convention to `test_ingredient_notes_are_lowercase_fragments`) · #172
title/slug divergence (`test_title_and_slug_dont_diverge` in
`test_taxonomy.py`, one real standing case — see below) · #170/#168
quoting (`test_main_ingredients_entries_are_quoted`, `test_tags_entries_
are_quoted`, `test_scalar_fields_are_quoted` — 125 + 94 + 284 unquoted
values fixed across the whole collection; **deliberately excludes
`meta:` booleans** — quoting `rewritten: true` would silently make it the
string `"true"` and break every `is True` check in the suite, checked
against the actual test code before touching a single value) · #169
`short_name` removed entirely (zero template/JS/SCSS references found
before removal; see §4).

**`test_milk_specifies_type` was a standing checklist, not a guard expected
to be green** (same shape as `test_oven_temperature_says_fan`, §10 above,
and now in the same state) — issue #167's 9-recipe backlog has since been
worked through, the test passes, and a failure in it going forward is a
real regression, not a known gap. The reason it was never a candidate for
a bulk fix is still live: which milk a recipe actually used needed Helen's
own source material or judgement, not a guess — "whole milk" could not be
assumed blind for every unspecified case. If it goes red again, the same
rule applies: it needs her judgement, not a mechanical fill-in.

**Retired 2026-08-12, Helen's explicit call, not fixed by filling in
values**: `test_bake_eggs_state_a_weight` (#145's second half — a bake
stating a gram weight/range for its eggs on top of the UK size band) and
`test_fresh_aromatics_state_a_paste_equivalent` (#153/#155 — fresh
ginger/garlic/lemongrass stating a paste/purée equivalent) are both gone,
issues #181/#182 closed. Neither had a single compliant recipe as of
2026-08-12; Helen decided the requirement itself wasn't worth keeping
rather than working through the backlog by hand. `test_egg_size_is_stated`
(UK size band, no gram weight) is unaffected and still enforced.

**Resolved 2026-08-12**: `ridiculously-good-oxtail-stew.md`'s title,
"Sticky Oxtail Stew" (agreeing with its own tagline), had disagreed with
its filename since before this HANDOVER's own §4 filename-stability rule
started blocking an unprompted rename. Helen's explicit call: renamed the
file to `sticky-oxtail-stew.md` rather than reverting the title.

**Deliberately NOT ported to every value in the file, and why** (checked
against real data before deciding, not assumed): the qualified-ingredient
closed lists, `test_ingredient_notes_are_lowercase_fragments`, `test_ingredient_group_
order_matches_title`, and `test_spice_order_within_group` were all
considered for a draft-scoped version and rejected — see `test_drafts.py`'s
own module docstring for the full reasoning per rule.

`.node-runtime/node/bin/node --test` runs `tests/js/*.test.js` — five files
today, listed in §3's module table. Node tests, not pytest, because they test JS
modules directly. **This said "20 checks across two files" until 2026-08-21, when
there were 161 across five**, which is the ordinary fate of a count written into
prose: run the suite, don't quote from here.

**`PLACEHOLDER` briefly existed as a second draft marker alongside `QQ`**
(added 2026-08-09, its own `test_no_placeholder_marker`, after
`roast-beef-fillet.md` published with literal "PLACEHOLDER - rewrite: ..."
still in every method step) and was retired 2026-08-10 — one marker for
everything now, not two. `test_no_qq_placeholder` covers both cases: a
blank field (`cook_time: QQ`) and an un-rewritten ingest line
(`QQ - rewrite: ...`). If you see `PLACEHOLDER` anywhere, it predates this
retirement — treat it exactly as `QQ`, don't add a third marker, and see
§4's ingest paragraph for the actual instruction.

**`test_ingredient_notes_are_lowercase_fragments`** (`test_taxonomy.py`,
renamed 2026-08-12 from `test_ingredient_annotation_style` so the failure
summary states the rule without opening the file) checks: one sentence, no
trailing full stop, lower case unless the first word is `I` or a declared
proper noun. It only flags, never rewrites, because Helen said so directly:
"I'll look at violations myself because I care about tone of voice."
**Don't fix a future violation of this test unprompted** — whether a
capitalised first word needs lowercasing or is actually a proper noun that
belongs in `taxonomy.yml`'s `proper_nouns` list is her call, same standing
rule as `QQ`.

**The ~12-recipe backlog against that test was cleared 2026-08-09, at
Helen's explicit in-session request** — this one batch was prompted, not a
change to the standing rule above. Nearly all were mechanical (strip the
full stop, lowercase the first word, leave mid-sentence proper nouns like
Merlot or Ceylon alone). Three needed real judgement and are worth Helen
double-checking the actual wording chosen, not just that the test now
passes: `best-ever-chocolate-sponge-cake.md` and `chai-spice-powder.md`
each had a genuine two-sentence note merged into one; `indonesian-chicken-
curry-gulai-ayam.md`'s ginger note started "I'm", which the test doesn't
exempt the way it exempts bare `I` (lowercasing to "i'm" would just be bad
grammar), so the sentence was reworded to drop the leading "I'm" instead of
touching the test.

The `Estimated`-timing (§5), `QQ`-placeholder, `cherry-glaze.md`
reversed-bracket-link, and the `test_typography`/
`test_brown_sugar_is_soft_brown_sugar` failures on
`indonesian-chicken-curry-gulai-ayam.md`, `mixed-spice-powder.md`,
`citrus-soy-salmon-sticky-rice.md` and `miso-salmon-veg-traybake.md` that
used to live in this list are all resolved (the last batch fixed
2026-08-10, commit `117edc9`) — don't go looking for them.
`peanut-butter-ice-cream` still links to `ben-jerrys-sweet-cream-base-1`,
but that recipe was promoted out of drafts 2026-08-09, so the link is no
longer to a draft.

**`test_oven_temperature_says_fan` was a standing checklist, not a guard
expected to be green, from issue #146 until the ~19-recipe backlog was
worked through by hand — it passes now, and a failure in it is a real
regression to investigate, not a known backlog to wave past.** The
reasoning that made it a checklist rather than a bulk-fix in the first
place is still live and still worth knowing: house style is fan-only, and
fixing one of these recipes meant confirming from the *original source*
which figure was the fan one — they aren't always in the same order in a
fan/conventional pair (§5), so it could never have been guessed or
bulk-fixed from the file alone. If this test goes red again, treat it the
same way: don't attempt a fix blind, get Helen's source material or her
direct confirmation, recipe by recipe.

**Which checks read `_food_drafts/` — ask the registry, not this file.** This
section claimed "exactly three" until 2026-08-21, naming three, while the same
section listed five a few hundred words above and `test_drafts.py`'s 31
per-draft tests and the whole of `test_source_attribution.py` read them too. The
number was wrong, it contradicted its own section, and there is a mechanical
answer: `SKIPS_WITHOUT_DRAFTS` and `PARTIAL_IN_CI` in `test_suite_hygiene.py`
are the registries, and `test_every_draft_reading_test_says_what_it_does_without_drafts`
fails on any draft-reading test in neither.

The one that fires in practice is
`test_no_main_ingredient_spelling_collisions`, when a new draft's spelling
collides with an existing ingredient — it caught `"demerara sugar"` against four
recipes' `"Demerara sugar"` on 2026-08-21. **Before reporting a new failure,
check whether the file is a draft Helen just added:**
`find _food_drafts -name '*.md' -mmin -120`. Don't chase it, don't tidy a
draft you weren't asked to tidy.

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

**Put `Fixes #N` on the commit, or the issue stays open forever.** Four issues
in one 2026-08-16 session (#52, #273, and nearly #274/#281) shipped and merged
with no trailer, so GitHub never closed them and they sat in the open list
looking like outstanding work. Check `git log main --grep="Fixes #N"` before
reporting an issue as done.

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

**A bare `#N` only resolves within its OWN repository.** The nested drafts repos
have their own empty trackers, so a cross-repo reference needs the full
`DeckOfPandas/helen-triages#N` form.

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

**A SOURCE-SCANNING GUARD WILL BE FOOLED BY THE PROSE EXPLAINING IT.** FIVE
times on 2026-08-19–21, in five unrelated places, which is what promotes this
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
unconditionally prints 115 private drink names into public HTML and links them
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

**Density is the index's own** (`$index-section-gap`, `$index-label-gap` in
`_layout.scss`), not the recipe page's tokens — matching them was tried and
rejected on sight, pushing the five filter sections ~340px apart. The index
is a control panel (every section visible in one glance); the recipe page is
a document (space isolates the one section you're mid-task on). Keep the
ratio near 2:1.

#### 13.4.1 The punched-tape effect — mechanism, not just description

Helen's device. **Since 2026-08-12 it is on EVERY heading on every site, and
it is applied from one place: the `h1, h2, h3` rule in
`_sass/shared/_base.scss`.** Individual components override the colour, the
size and (on the two biggest) the offset, but none of them opts *in* any more —
opting in was exactly how the effect came to be missing from some headings and
mis-tuned on others. `.category-label` (the index's filter section labels —
STAR INGREDIENT, MOOD, etc.) lives in `_sass/food/_category-labels.scss`; the
header wordmark lives in `_sass/shared/_layout.scss`, see §13.8.

**Two things on the index deliberately do NOT wear it, and both were checked
with Helen rather than assumed.** The results heading's "N survivors" count is
plain body text — it carries `class="category-label"` but sits outside
`.category`, so the rule is scoped to keep it out, and `.results-heading
.category-label` now states the bare treatment outright so it can't be
"fixed" again by accident (it was, once, on 2026-08-12; Helen: "I liked it
bare"). And the **active states of filter buttons and recipe-row tags** carry
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

- `$emboss-stroke` — **`0.014em`**, i.e. 1.4% of font-size. An `em` resolves
  against the element's own computed size, so this is self-scaling and needs
  no argument, no arithmetic and no maintenance. It is what lets the global
  `h1, h2, h3` rule work at all, since that rule cannot know what size a
  heading will turn out to be.
- `$emboss-offset` (`1px`) and `$emboss-offset-large` (`2px`) — target 6.5%
  of font-size. These stay hard whole pixels rather than a computed
  proportion, deliberately: a fractional stroke antialiases harmlessly along
  an edge, but a fractional shadow offset antialiases the whole duplicate
  glyph, which is the soft floating read the "no blur" rule exists to
  prevent. 1px up to about 1.2rem, 2px from about 1.6rem. Only the recipe
  title and the recipe section headings need the large one.

The two ratios aren't invented — they're where the two elements that
demonstrably worked already sat: HELEN TRIAGES at 6.3% offset after Helen
tuned it by hand, and the longform Tips label at 6.8% offset / 1.4% stroke,
which is the element she pointed at ("it looks better than the lettering for
my existing page headings — am I imagining this?"). She wasn't.

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
aureolin` (PRACTICALITIES), `$color-pure-lime-green` (SEARCH MAIN INGREDIENTS),
`$color-hot-orange` (I KNOW WHAT I WANT). On the index colour is a CODE — each
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

**"N recipes"**, right-aligned, between the filter matrix and the list —
reuses the filter section labels' own punched/stroke typography with no
colour rule underneath, the same reason META FILTERS carries none: it isn't
one of the five filter categories, so it doesn't borrow one of their hues.
Margin above uses `$spacing-section-top`, the recipe page's own "gap above a
heading" token, rather than inventing a second one.

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

**The same mechanism, used for the index page's reveal link — and the way it
fails.** 2026-08-16, issue #275: "(I know what I don't want)" had to centre
under I KNOW WHAT I WANT, whose width changes with its own text. Same answer
as above — `display: inline-grid; grid-template-columns: max-content;
justify-items: center`, both rows in the one column (`.name-heading-stack`).

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
`_sass/shared/_fonts.scss` declares nine faces, 152 KB, latin subset, served from
`assets/fonts/` with relative urls (which resolve against the compiled
stylesheet's own location, so they survive any baseurl — a `{{ site.baseurl }}`
would not work at all, Sass not being run through Liquid).

    Selawik        300 350 400 600 700    $font-body
    Courier Prime  400 700                $font-headings
    IBM Plex Mono  600 700                $font-label

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

#### 13.10.1 `$font-label` — the rule, and the four elements that failed it

**The index is entirely Courier Prime. IBM Plex Mono appears only on recipe
pages, on two things: `.ingredient-amount` and `.note-label`.** That is the whole
rule. The split falls on **browsing versus cooking**, not on any property of the
elements.

It is short because it is what survived. This variable was `$font-recipe-title`,
then over three days owned badges, tag buttons, category labels, filter states,
two status messages and the index titles. **Every one came back**, and the
returns are worth more than the rule:

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

**So the test for a new consumer is not "is this a label".** Every returned
element was a label. It is: *is this on a recipe page, and something you look at
with your hands full?* The rule that lost four times — "things you scan" — asked
what an element **is**. The rule that works asks what it must **agree with**.

The clash only works while Plex Mono is the minority. Two consumers is a
comfortable minority; five was not.

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

**Nothing on the site uses `.on-dark` at all.** It had one consumer, a swatch on
`/dev/emboss/`, and that went when the heading dials did on 2026-08-26 — so the
class is now live CSS with no user anywhere, and its numbers cannot be seen
without re-adding a swatch. They were a considered starting point rather than a
verified result even then. Kept rather than deleted because the reasoning behind
it took a real conversation to reach and issue #469 tracks it; delete it instead
if a dark section still has not appeared by the time anyone reads this. This is
*not* dark mode, which Helen has explicitly deferred.

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
