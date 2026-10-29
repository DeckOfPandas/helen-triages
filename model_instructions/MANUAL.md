# MANUAL

**Helen Triages** — a Jekyll mono-repo serving two personal decision-support
sites. **Food** answers *what shall we cook*, not *how do I cook*.
**Cocktails** is its sibling: a schema, a designed index and recipe page, and
a published collection in `_cocktail_recipes/`.

**This file is the present tense**: how the repository works today. It carries
no history. When something changes, rewrite the paragraph that describes it.
Section numbers are stable, because code comments and other documents point at
them as `MANUAL §n`; a section that is now only a pointer keeps its number.

- **`CLAUDE.md`** (repo root, loaded into every session) is the rules for an
  agent: git, pushing, the token, the Bash rules, who may set which gate flag.
  This file does not repeat them; it says how the mechanisms work.
- **`DECISIONS.md`** is the journal: one short entry per ruling of Helen's that
  is still in force, with her reason, under these same section numbers.
  **Before re-opening anything, find its entry there** — grep
  `DECISIONS_INDEX.md` first.

**Do not trust this document over the code.** Verify anything you are about to
act on. If the code and this file disagree, the code wins, and the fix is to
correct this file. Name files, never line numbers.

### Read this first, by what you are here to do

**To change the site:** §2.5 (one header, one footer), §3 (the three layers),
§4.0 (the gate flags — every recipe edit touches them), §12 (the traps),
§13.11 (how a design decision gets made: by Helen looking, never by argument).

**To ingest or fix drafts:**

1. `PIPELINE.md` — the one map of a recipe's journey — then the procedure for
   your step: `.claude/commands/ingest.md`, `ingest-inbox.md` or
   `tidy-drafts.md`. The `QQ` conventions live in `ingest.md`.
2. §4 for a food recipe's schema, §9.3 for a cocktail's, §4.0 and §9.1.1 for
   the flags, §5 house style, §7 food's taxonomy.
3. `PUBLISHING_A_COCKTAIL.md` before touching anything in `4-promote/`.

### The companion documents

All in `model_instructions/` unless a path is given.

| file | is |
|---|---|
| `DECISIONS.md` | the journal — see above |
| `DECISIONS_INDEX.md` | generated: one line per journal entry, for grepping. `python3 scripts/build_decisions_index.py --write` after any journal edit; `tests/test_decisions_index.py` fails until you do |
| `START_A_SESSION.md` | the prompt Helen pastes to start a session |
| `PIPELINE.md` | the one map: the ways in, the intake pass, Helen's folders and the words that move a file, the way out, and the way back when an agent touches a published file |
| `PUBLISHING_A_COCKTAIL.md` | the promotion steps in full, and the word "final" |
| `.claude/commands/ingest.md`, `ingest-inbox.md`, `tidy-drafts.md` | the three slash commands: each a procedure over a script in `scripts/` that reports and never writes unasked (§11.0.2–§11.0.4) |
| `SOURCE_ATTRIBUTION_SPEC.md` | the `source` / `source_type` contract; §4 summarises it |
| `INGEST_ONE_RECIPE.md`, `INGEST_ONE_COCKTAIL.md` | for a Claude with no repository, so they stand alone. Every vocabulary block in them sits between `<!-- vocab:… -->` markers and is rendered from `_data/` by `scripts/build_ingest_vocab.py` (`--check` / `--write`), which `tests/test_standalone_docs.py` enforces. Hand-edit nothing inside a marker pair; keep the prose outside them in step when §4, §5, §7, §9.3 or the attribution spec changes |
| `CLAUDE_WEB_INGEST.md` | how a claude.ai chat is pointed at those two files by URL, and what it is told |
| `INGEST_INBOX_DESIGN.md` | the envelope an ingest issue carries (§6) and its security argument (§8) |
| `LETTERING.md` | the tiers of punched-tape type |
| `LEOPARD.md` | the black-on-black print on the cocktails page ground: what ships, the generator, where it must never go |

---

## 1. How to run it

```
python3 scripts/verify.py    # every check below, in one command -- prefer this
pytest                       # content and structure; one session at a time
node --test                  # the JS suite, discovered from the root (§10)
jekyll-local                 # port 4001, drafts visible
jekyll-prod                  # port 4002, exactly what deploys
```

Inside the container these serve on 4001 and 4002; `.devcontainer/run.sh`
publishes them to the host as 5998 and 5999, so Helen's browser opens
`http://localhost:5998/helen-triages/`, then `/food/` or `/cocktails/`.

**A session starts one when Helen asks**, from its own worktree, in the
background, and gives her the host URL. `scripts/browser/serve.sh` is a
different thing: a short-lived server the screenshot tooling owns (below), on
a port the host cannot reach.

#### `scripts/verify.py`

Runs five checks and exits non-zero if any fails: `pytest`, the JS suite,
`scripts/derive_cocktail_moods.py` (did a vocabulary edit move a cocktail's
moods?), `scripts/build_ingest_vocab.py --check` (do the standalone ingest
documents still match the data they are rendered from?) and
`scripts/check_slug_keys.py` (does every slug-keyed entry in the public
cocktail taxonomy name a cocktail?). The last three are the ones a session
forgets when it runs the two suites by hand.

**A check may say `SKIP`, which is neither a pass nor a failure.**
`check_slug_keys.py` is the one that does. `mood_include` / `mood_exclude`
live in the public taxonomy and are keyed by slug, but most of the cocktails
they name are drafts, so only a checkout holding the drafts clone can tell an
entry naming a real draft from one naming nothing. Without the clone it exits
2 and says it verified nothing; the run still goes green, and the closing
line says so. **A green `verify.py` in a bare worktree has not checked this.**
Clone the drafts repo (`CLAUDE.md` has the command) and run it again before
merging anything that touches a slug-keyed entry.

`python3 scripts/check_food_tags.py` is a report and is deliberately not in
`verify.py`. It lists food recipes whose tags or star disagree with their
title, from `tag_hints` in `_data/food/taxonomy.yml`. It writes nothing and
fails nothing; `--drafts` is the list to have open while proofreading.

**One `pytest` at a time.** Two runs share one `.jekyll-cache` and one `tmp/`.
(The gate fixtures named `zzz-gate-…` are written into a copy of the tree by
`built_with_fixtures` in `tests/test_rendered_pages.py`, never into the real
collections.)

#### Runtimes

`.node-runtime/` and `.gh-runtime/` are gitignored and do not come with a
worktree; run the system `node`. `gh` is installed by the devcontainer image.
Call it through the wrappers and never name the token; `CLAUDE.md` owns those
rules and lists every call that runs without asking. The one mechanism worth
knowing here: `sh scripts/gh-read.sh <endpoint>` takes `--fields a,b` (one
object), `--each a,b` (a list) or `--jq <expr>`, plus `--paginate`. Prefer
the first two, which build the jq inside the script; a `--jq` expression
containing a quoted `[`, `]` or `|` is refused by the unanalysable-bash hook,
while `--jq .body` is fine.

#### The headless browser

Looking is cheaper than reasoning. The devcontainer image carries Playwright
with Chromium and WebKit (Safari's engine, for a script that launches
`webkit` itself; the harness and the suite use Chromium) under
`/opt/playwright`; `sh scripts/browser/install.sh`
checks the image's copy is the pinned version and stops. Outside the image,
or in an image built before the pin moved, it installs both under
`tmp/browser/`, and `scripts/browser/env.sh` prefers that local copy when it
exists. The Python binding used by `tests/test_browser_smoke.py` is the same
version and resolves to the same Chromium.

The Playwright version is pinned on one number in the Dockerfile (npm and
pip), `install.sh` and `requirements-test.txt`.
`tests/test_browser_harness.py` and `tests/test_devcontainer_pins.py` fail if
they differ, and `playwright` is in `dependabot.yml`'s ignore list because a
bot can move only one of them. Editing the pin in the Dockerfile is the whole
of a bump: `.devcontainer/run.sh` stamps each image with a hash of
`.devcontainer/` and rebuilds when the hash no longer matches
(`.devcontainer/README.md`).

**`.devcontainer/build_inputs_hash.py` reads `.dockerignore` as exact
filenames only, and fails wide**: a line holding `*`, `/`, `!` or `?` makes it
hash everything, a spurious rebuild and never a missed one. Never list a file
the Dockerfile copies (`tests/test_devcontainer_hash.py`). The stamp cannot
see the base image or an apt package moving upstream; that wants
`docker build --pull --no-cache` by hand.

| Command | Does |
|---|---|
| `sh scripts/browser/build.sh` | builds exactly what deploys into `tmp/site` |
| `sh scripts/browser/serve.sh` (in the background) | serves it on the first free port from 4010 and writes the port to `tmp/browser/port`; one server per worktree |
| `sh scripts/browser/shoot.sh <label> <path>...` | screenshots at 360, 390 and 1280 wide and names every element past the viewport |
| `sh scripts/browser/crop.sh <path> <selector> <name> [width] [type-into] [text]` | crops one element at 2x and prints its box in CSS px (`x`, `y`, `w`, `h`, `right`); the last two arguments type text into a box first |
| `sh scripts/browser/click-crop.sh <path> <click-selector> <crop-selector> <name> [width]` | clicks one element once, then crops another |
| `sh scripts/browser/styles.sh <path> <selector> [width] [prop,prop,...]` | prints each matching element's box and computed styles |
| `sh scripts/browser/gaps.sh <path> [width] [root-selector]` | walks the visible block-level descendants of `main` (or another root), printing each one's height, margins, padding and the gap to the sibling before it |
| `python3 scripts/browser/inkbox.py <png> [gap]` | prints each band of ink in a crop with its vertical extent and centre |

Read the PNGs with the Read tool. Traps:

- **Every `<path>` is site-relative; the tool adds `/helen-triages` itself.**
  `/food/`, never `/helen-triages/food/`. Passing the baseurl asks for a page
  the server answers 404, and the tool then reports `no elements for
  <selector>`, exactly as it does for a selector that matches nothing. If a
  selector you are sure about reports nothing, check the path first.
- **A box is not ink.** An alignment question about marks is answered by
  `inkbox.py`, not by comparing boxes.
- **Two crops are not one image.** An element screenshot pads its box by about
  a pixel and two rasters land on different sub-pixel phases, so crop the
  element that contains every mark you are comparing and read them from that
  one image. Where that element also holds the tape, hide the tape with
  `visibility: hidden` on `.site-logo`, which keeps its box so nothing moves.
- **The last device pixel may be unreachable.** Two ink bands of different
  heights have centres half a pixel out of step; walk the value, read what
  each one paints, and take the one that looks level (§13.11).
- **Mobile emulation grows the layout viewport to fit the widest element**, so
  `innerWidth` is the symptom, not the measure; `shoot.sh` compares against
  the width it asked for.
- **A control that exists only on a local build** (the header search box,
  §2.5) is not in `build.sh`'s output. Build with
  `--config _config.yml,_config_local.yml -d tmp/site` before cropping it.
- **Headless Chromium snaps a monospace advance and a baseline to whole
  pixels**, so a screenshot's line breaks are not Helen's. Compute how many
  characters fit from the face's 0.6em advance, and measure a baseline on type
  laid out many times too big, as `scripts/card_tagline_baseline.py` does.
- **The index shuffles, so `.drink-card:first-child` is a different drink in
  every screenshot.** For a before and after of a card, crop the related
  cards on a drink page: the same cards every build.
- **When a pixel reading disagrees with the CSS you just compiled, suspect the
  reading.** Say which mark the sample landed on before reporting that a
  change did not apply.

#### Config, and what `jekyll serve` does not reload

`jekyll serve` does not reload `_config.yml`; restart after any change to it.

**It does not reload `_plugins/` either, and that fails silently.** Ruby
plugins are loaded once at boot, so a server started before a plugin existed
or changed serves a site where that plugin never ran, with nothing in the log
and no error on the page. Restart after adding or editing any file in
`_plugins/`. To confirm which you are looking at, the plugins log a line each
at build (`Costs:`, `Units:`, `Cards:`, `Shopping:`); no line means it did not
run. `--plugins <empty dir>` reproduces the state deliberately.

**`_config_local.yml` is where every local-only switch lives.** Two
mechanisms, and they are not the same:

| Key | `_config.yml` | `_config_local.yml` |
|---|---|---|
| `show_source_wording` | `false` | `true` |
| `show_awaiting_fix` | `false` | `true` |
| `pdf_downloads` | `true` | `false` |
| `show_drafts`, `show_costs`, `show_header_search`, `show_local_reference_links`, `unpublished` | not declared | `true` |
| `output` on the `dev`, `food_drafts` and `cocktail_drafts` collections | `false` | `true`, with a permalink |

A key in the fourth row is safe because production does not declare it: the
template gates on the key, so it cannot be true on the live site. **Never
move one of those into `_config.yml`, and never put a baseurl in
`_config_local.yml`.** `show_awaiting_fix` switches the whole publish gate
off locally (§4.0). `show_drafts` also puts a `hide drafts` / `show drafts`
pill (`#drafts-toggle`) under SHORTLISTED on both indexes: it narrows the list
to what the live site holds, is not part of the filter state, and resets on
every load.

Scratch files go in this repo's gitignored `tmp/`, never machine `/tmp`
(`CLAUDE.md`).

---

## 2. The mono-repo shape

One Jekyll build, one `_config.yml`, two sites:

```
https://deckofpandas.github.io/helen-triages/food/recipes/<slug>/
https://deckofpandas.github.io/helen-triages/cocktails/recipes/<slug>/
```

### 2.1 Why the collections aren't inside `food/`

Jekyll only discovers a collection at `_<name>` directly under the source
root (or one shared `collections_dir`); `food/_recipes/` is silently ignored.
So the site lives in the collection's name and `permalink` does the routing.
`collections:` in `_config.yml` is the authority.

| Directory | In production | Permalink |
|---|---|---|
| `_food_recipes/` | `output: true` | `/food/recipes/:path/` |
| `_food_magic_bag/` (§4.3) | `output: true` | `/food/magic-bag/:path/` |
| `_cocktail_recipes/` | `output: true` | `/cocktails/recipes/:path/` |
| `_food_drafts/`, `_cocktail_drafts/` | `output: false` | local only: `/food/drafts/:path/`, `/cocktails/drafts/:path/` |
| `_dev/` (internal reference pages) | `output: false` | local only: `/dev/:path/` |

`food/` and `cocktails/` hold each site's pages (`food/index.html`,
`food/reference/`, `cocktails/index.html`), not their collections. The root
`index.html` is a bare redirect to `/food/`. `_design_sources/` holds Helen's
raw Inkscape glass drawings, committed as they are (§9.11, §9.15). For the
rest, run `ls`.

**Plugins.** `_plugins/` decides what a built page shows, once, at build time:
`publish_gate.rb` removes any gated document that does not carry an explicit
pass (§4.0, §9.1.1); the `cocktail_*.rb` plugins do the price, unit and
card-ingredient work (§9.3.4, §9.3.5, §9.10.1); the `food_*.rb` plugins
assign each food ingredient its grocery aisle and work out what a recipe
feeds or makes and whether it halves (§8.2); `amount.rb` is the one reading
of an `amount:` string they share. `ls _plugins/` lists them and each file's
header says what it does.

**GitHub Pages' safe mode ignores `_plugins/` entirely, without warning** —
the gate would be gone and the build green. The workflow therefore runs its
own plugin-capable build, and
`test_deploy_workflow_still_runs_a_plugin_capable_build` in
`tests/test_site_config.py` asserts that it still does.

**The two drafts collections are each their own nested git repo**, gitignored
here and pushed to a private GitHub repo of their own:
`helen-triages-food-private` and `helen-triages-cocktails-private`.
`output: false` only stops Jekyll rendering them; the repo split is what keeps
their source out of a public repo whatever the build config says. A draft is
promoted to `_food_recipes/` or `_cocktail_recipes/`, and so becomes public on
the next deploy, only once it contains no copyright material: Helen's own
words, or sufficiently adapted. The split is what makes it safe to leave
drafts unpromoted for as long as needed, not a reason to promote them faster.

**Editing a file inside `_food_drafts/` or `_cocktail_drafts/` from this
working tree is normal**, but `git status` here never shows it and `git add`
here cannot capture it. It is a separate, private history, reached with
`sh scripts/git-drafts.sh` (`CLAUDE.md`). Do not "fix" the missing tracking
and do not report draft edits as at-risk work in this repo.

**A draft says so, on the local site only.** A cocktail draft carries a
`draft` badge on its index card and beside the name tape on its own page
(`_includes/cocktails/draft-badge.html`), emitted by `collection` the way
food's draft pill is. Nothing gates it: a production build has no draft in the
loop to mark.

### 2.2 Shared versus forked

**Shared**, at the root, names neither site:

- `_layouts/default.html`.
- `_sass/shared/`. `_tokens` is structural and never references a palette;
  `_layout` is the structure of `default.html`; `_rule` holds the lettering
  mixins; `_chrome` is the header and footer's colour. `ls _sass/shared/` for
  the rest.
- `_data/accented_words.yml` (house style for both sites) and
  `_data/chrome.yml`.
- `assets/js/`: no script's logic knows which site it is on; it reads the site
  key from the page (§3). That is a claim about logic, not file names:
  `cocktail-index.js`, `cocktail-search.js` and `cocktail-make.js` load on
  cocktails pages only. `assets/js/assets.js` loads first on every page.
- `assets/img/favicon/` (one set per site, named by `site_key`),
  `assets/img/chrome/`, `about.html`.

**The stylesheets are Sass modules: every file names what it reads with
`@use`, at its very top, and there is no `@import`.** `food.scss` and
`cocktails.scss` are the two sites, and their `@use` order is the CSS order,
since a module's rules land where it is first loaded. A shared partial reads a
palette only through `shared/theme`, which each entry stylesheet fills from
its own palette with `@use "shared/theme" with (...)`; a site partial `@use`s
its own palette. Grep for `"shared/<name>"` across `assets/css/` and `_sass/`
before renaming or splitting a shared partial: every user names it. An
`@extend` reaches only modules the extending file loads, so a shared rule a
site class should join names that class itself (`shared/_print.scss`'s
`.btn-drafts-toggle`).

**A site's own partial loads after the shared one it follows, so a per-site
rule at equal specificity silently undoes a shared change on that site only.**
Before changing a shared value, grep `_sass/food/` and `_sass/cocktails/` for
the same selector.

**Forked**, because cocktails is philosophically distinct and not a reskin (a
recipe is a procedure; a cocktail is a formula plus a build):
`_layouts/recipe.html` vs `cocktail.html`; `_data/food/` vs
`_data/cocktails/`; `_sass/food/` vs `_sass/cocktails/`; `assets/img/food/`
vs `assets/img/cocktails/`; `assets/css/food.scss` vs `cocktails.scss`.

### 2.3 The palette contract

Shared partials read a palette only through `_sass/shared/_theme.scss`, which
declares the variables they may use and nothing else: the colours
`$color-accent`, `$color-bg`, `$color-border`, `$color-clear-text`,
`$color-mood-root`, `$color-surface`, `$color-text`, and the fonts
`$font-body`, `$font-headings`, `$font-label`. Each entry stylesheet passes
every one from its own palette (`@use "shared/theme" with (...)`); one left
out stops the build with an error naming it. A shared partial that reaches
for any other palette variable fails as "Undefined variable", on both sites.
`test_every_palette_satisfies_the_shared_contract` reads the theme's list and
holds both palettes and both entry stylesheets to it;
`test_the_two_palettes_declare_the_SAME_font_stack` keeps the two font stacks
equal without lifting them into `shared/`.

**`$color-accent` means this site's one "interactive / branded" colour**, and
is what lets the chrome be shared (§2.5). Each site assigns it in its own
`_sass/<site>/_palette.scss`; on cocktails it is the same colour as
`$color-mood-root`. A grey `$color-accent` is a symptom (the lightness-only
no-op of §12), never a state to leave.

### 2.4 `site_key`

`_config.yml`'s `defaults:` sets `site_key` per collection and per directory.
It keys into `_data/sites.yml` (`title`, `word`, `description`, `css`, `home`,
`icon`, `social_image`, `reference_links`) and into `_data/<key>/` for the
site's vocabulary. `social_image` is the site's link-preview card, a PNG of
its own wordmark rendered by `scripts/render_social_images.py` from the built
site. A site-neutral page (about, 404) carries `site_key: food`, so it takes
food's card and food's description.

The tab and home-screen icons are `assets/img/favicon/<site_key>-<size>.png`,
linked by `site_key` in `default.html`: `[ ]` alone at 16px, HT over `[ ]` at
32 and 48, and the wordmark at 180 for a phone's home screen. Food's HT over
`[ ]` splits black-on-white over white-on-black; cocktails is white on black
throughout, so the two sites differ by colour at every size. A favicon cannot
load a web font, so `scripts/render_favicons.py` draws the small ones in a
browser that has Courier Prime, and `scripts/render_social_images.py` shoots
the 180 with the cards. Both are run by hand and their PNGs committed; give
them the headless shell from `/opt/playwright` as `--chrome`, because the full
Chrome build does not exit in the devcontainer.

**A root-level page must declare `site_key` in its own front matter**, because
the defaults assign it by directory and there are only two. A page with no
`site_key` gets the repo-level title and no stylesheet, silently;
`test_every_published_page_links_a_stylesheet` catches it.

**Decoration is opt-in and absence is silent.** `_data/cocktails/glasses.yml`
is the example: a glass with no entry renders no icon rather than a broken
one. A missing key is not a 404; a key pointing at missing artwork would be.

### 2.5 The shared chrome — one header, one footer

There is one header and one footer for the whole site: literally the same
code and assets, not two kept in parity (DECISIONS §2). "Shared" is a claim
about three layers — markup, cascade, assets — and is only true when all
three hold (§12).

| Thing | Where |
|---|---|
| The one header and the one footer | `_layouts/default.html`, with no `site_key` branch in either |
| Their structure | `_sass/shared/_layout.scss` |
| Their colour | `_sass/shared/_chrome.scss` |
| Their artwork | `assets/img/chrome/`: `tape/`, `hearts/`, and `tag-shapes/` (not chrome, but the one other artwork both sites wear) |
| What is left of chrome config | `_data/chrome.yml`: `tape_count` and nothing else |
| How a script fetches the artwork | `HTF.chromeAsset(path)` (§3) |

`_data/sites.yml` keeps only what says where you are. **The test before
adding a key there: does this say where you are, or what the chrome is?** The
second belongs in `chrome.yml`, or nowhere. `RETIRED_SITE_KEYS` in
`tests/test_page_links.py` fails if a removed key reappears.

#### The nav row

- **The nav is the door to the other site.** One loop over `sites.yml` in
  that file's order, skipping `page.site_key`; each entry is its bracketed
  word and an arrow, `[ COCKTAILS ] →` on food. The site's `icon` key and
  artwork exist but are not in the row. A `site_neutral` page shows every
  site. One template, no per-site key.
- **The arrow is drawn, not typed** (`_includes/icons/arrow-right.svg`, which
  takes a `class` parameter). Courier Prime ships as a subset with no arrow
  in it, so `&rarr;` would be whatever face the reader's machine substitutes,
  and a substituted glyph moves the metrics that decide where the ink sits.
- **Type never has its ink centred in its box.** The row centres boxes with
  `align-items: center`, and all-caps lettering runs baseline to cap line
  while the line box keeps the descender depth, so `.site-nav-word` carries
  `top: 0.1em` to drop the lettering onto the marks' line. That number is
  measured; to re-measure, crop the whole link and read the ink bands in that
  one image (§1).
- **Position.** The row sits at the right-hand end of the header's second
  row and the `??` about link (a literal `/about/`) at the left end, both on
  the cards' edges, at every width, hanging close under the tape:
  `$header-door-gap` (0.1rem) of top margin on the row, on `??` and on the
  local search box under the door, and 0.2rem of bottom padding on
  `.site-header` (DECISIONS §13).
- **`.site-header-inner` is the cards' width**: `$width-content` minus
  `main`'s padding, because `main`'s width includes its padding. Below
  `$header-stack-width` the header stacks into one column.
- **`/about/` is the one page with two doors and is laid out for them.**
  Two doors do not fit column 3, so `.site-neutral .site-nav-icons` spans all
  three tracks and sets `nowrap`; the row still ends on the cards' right
  edge. The `??` is not emitted there at all — not hidden, because a hidden
  link is still in the tab order and would point at the page you are on.
  Below `$header-stack-width` the two doors take an edge each, and the first
  is mirrored (arrow first, turned round) so both arrows point away from the
  wordmark.
- **On a local build the header has a third row: the search box**
  (`_includes/page-search.html`, row 3 column 3 of the same grid), gated on
  `show_header_search`. The deployed header has none. §13.13 has the box.

#### The footer

The reference block is a column per site, gated on that site having
`reference_links`: the loop asks every site, so food's links appear on a
cocktail page and the reverse. The hearts are pinned to grid column 2 so a
second column cannot push them off centre. Once the footer stacks, a short
hairline sits over `about` so it does not read as the last column's next
link.

**Trap: a definite `grid-column` with an auto row is still auto-placed.**
Items are placed in DOM order, so an earlier auto item takes row 1 column 2
and the pinned one drops to row 2; a `_data/sites.yml` edit alone can do it.
Every footer item names its row and its column. **And a hover on the link
does not reach a child that sets its own `color`**: the icon follows
`currentColor`, `.site-footer-ref-word` does not, so the hover rule names the
word too.

**A link may be `local_only: true`, and that gates the link, not the page.**
The template drops such a link unless `show_local_reference_links` is set, and
a site left with no surviving links draws no column. It is half a switch and
must be set and cleared with the other half, `published: false` on the page
itself (§14; `unpublished: true` in `_config_local.yml` is what builds such a
page locally). A link with no page is a 404; a page with no link is reachable
only by typing its URL. `test_site_nav_links_resolve_to_real_pages` inverts
for such a link rather than skipping it — it must point at a page that is
unpublished — so clearing either flag alone goes red.
`grep local_only _data/sites.yml` shows whether any link carries it now.

#### Guards

Two, and neither substitutes for the other.
`test_the_header_and_footer_are_identical_on_every_page` compares the
rendered HTML of the nav row and the whole footer across a food page, a
cocktails page and a recipe, byte for byte, and requires each site's row to
name the other site and not itself. If it ever needs an exception carved into
it, that exception is a second header arriving.
`test_every_chrome_class_has_a_rule_in_every_site_stylesheet` compares the
compiled CSS for every class the template and the icon partials emit. Its
pattern refuses braces, so a Liquid conditional inside a `class` attribute
drops every class in that attribute from the checked set while the test
passes. That is why the `site-neutral` header is two whole `<header>` tags.

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

Each layer knows nothing about the layer above it.
`_sass/<site>/_palette.scss` is the only place a colour is written down (JS
reads custom properties; SVGs use `currentColor`). `_data/food/taxonomy.yml`
is the only place food's tags and stars are declared. `assets/js/assets.js`
is the only place a base URL or site key is derived, or a file fetched.
Helen's principle: *the data model must not assume anything about or impose
anything on the data.*

**Split inside behaviour once a module gets non-trivial**: pure algorithm
apart from DOM wiring, so Node can test it. A pure module `<name>.js` is
tested by `tests/js/<name>.test.js`. The pairings that do not follow the
name:

| Module | Tested by |
|---|---|
| `assets.js` (`HTF.escapeHtml`, `HTF.indexMemory`, `HTF.shortlist`, the asset helpers) | `escape-html.test.js`, `index-memory.test.js`, `shortlist.test.js` |
| `filters.js` (DOM wiring, food index) | `food-index-startup.test.js` (§10.2) |
| `cocktail-index.js` (DOM wiring, cocktails index) | `cocktail-index-startup.test.js`, over `tests/js/index-harness.js` (§10.2) |
| `ground-print.js` (the page-ground print, `LEOPARD.md` §7) | `ground-print.test.js` for the pure pieces; the drawing is looked at in a browser |

`list-view.js` (shuffle and pagination), `filter-state.js` (what an index's
filter state is) and `results-bar.js` are used by both indexes.

**`HTF.filterState` is the module and `HTF.filterState.create(SPEC)` is a
binding of spec-bound functions.** Reading a name off the wrong one throws
silently in the browser while every pure test stays green.
`test_a_filter_state_binding_is_only_asked_for_what_it_has` reads both export
blocks; §10.2's harness runs the real page.

**`entriesMatchKey` is a word-prefix match**: asking for `salt` must not
reach `unsalted butter`. Families that containment would fake (`nuts`) are
carried by the vocabulary in `_data/food/ingredient_words.yml`, never by
loosening the rule; an `aliases:` entry cannot do it, because a row is
matched against raw `main_ingredients` and sees no alias.

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
source_type: publication         # required; SOURCE_ATTRIBUTION_SPEC.md
serves: "4"                      # xor makes: -- never both. Quoted
serves_estimate: 6               # required unless serves: opens with a
                                 # number. An integer, people, unquoted
prep_time: "20 mins"
cook_time: "1 hr 30 mins"
main_ingredients: ["cavolo nero", "butter beans", "lemon"]
star_ingredient: "greens"        # optional
internal_temp_ref: beef.tender_roast   # optional; §14
doneness: medium_rare                  # optional, only with internal_temp_ref
tags: ["soup"]
ingredient_groups:
  - name: soup                   # bare noun -- the template adds "For the "
    items:
    - amount: "400 g"
      item: "butter beans, drained"
      note: "Jarred are worth it here."
    - item: "vegetable oil, to fry"
      incidental: true           # optional; see below
method:                          # xor method_groups: -- never both
  - "Step text."
  - step: "Step text."
    note: "An aside."
method_short:
  - ""                           # [""] = not written. A block scalar = written.
notes:                           # optional; always a list, never a blob
  - label: "Sinking"             # both keys always
    text: "If it sinks, you added too much syrup."
meta:                            # exactly these three, in this order -- §4.0
  rewritten: false
  awaiting_fix: false
  proofread: false
```

`tests/test_front_matter.py` is the schema's authority; keep this block in
step with it, because a schema example is copied more often than it is
checked.

| Rule | Where it is enforced |
|---|---|
| Required keys | `REQUIRED`: `title`, `tagline`, `source`, `source_type`, `main_ingredients`, `tags`, `ingredient_groups`, `method_short`, `meta` |
| `serves` xor `makes`; `method` xor `method_groups` | `test_serves_xor_makes`, `test_method_xor_method_groups` |
| Top-level scalar strings are double-quoted | `SCALAR_STRING_FIELDS`; `/tidy-drafts` fixes it mechanically |
| Members of `main_ingredients` and `tags` are quoted | `test_main_ingredients_entries_are_quoted`, `test_tags_entries_are_quoted` (`tests/test_taxonomy.py`, and again over drafts) |
| `meta:` is `rewritten`, `awaiting_fix`, `proofread`, in that order, real booleans, nothing else | `test_meta_block_is_exactly_the_three_flags_in_order` |
| Retired keys stay retired | `RETIRED`, which says what replaced each |
| `serves_estimate` present where needed, a positive integer | `tests/test_food_shopping.py` |

`meta.claude_rewritten` (optional) may sit alongside the three on a draft
only: it records that Claude took a tidy-up pass, not that the recipe is
rewritten. `RETIRED` and the tombstone beside
`test_claude_rewritten_is_a_real_boolean` record the retired `cooked_before`
promotion gate and how to restore it. Do not resurrect a retired key for a
gap it used to paper over.

**`source_type` is required alongside `source`.**
`model_instructions/SOURCE_ATTRIBUTION_SPEC.md` is the contract and
`tests/test_source_attribution.py` enforces it over recipes and drafts. The
rule most likely to catch you: the date is what separates a `publication`
from a `website` — no date, it is the website. `source_type` renders nowhere,
so it is in `INVISIBLE_KEYS` (§4.0).

**The staging folders inside the drafts repos are Helen's.** They record where
she is with a recipe, which no flag can say; `PIPELINE.md` §3 names them and
`tests/test_staging_folders.py` holds the list. Never move a file between
them unless asked, and never delete a `QQ original` line. The folders and the
flags answer different questions and are not expected to agree.

**The ingest contract, the `QQ` conventions and the tiers live in
`.claude/commands/ingest.md`.** The one line: is the answer in the source, or
in Helen's head? `QQ` anywhere is Helen's placeholder — never flag it, fix it
or convert it; `test_no_qq_placeholder` stops one reaching `_food_recipes/`.
**Split `ingredient_groups` and `method_groups` at ingest, once, and never
regroup afterwards**: on a published recipe regrouping is a content edit and
takes `proofread` down with it.

#### Field by field

- **`incidental: true`** marks a cooking fluid or tin-and-pan fat (frying oil,
  greasing butter, flour for dusting) that the Ingredients section skips and
  `main_ingredients` must not list (`test_incidental_not_in_main_ingredients`).
  Whether an oil is core is a judgement (unusual oil, stated smoke point,
  finishing drizzle → core), so it is an explicit flag. A fat or flour listed
  only for the tin or the pan must carry it, a real line loses a ", plus
  extra for the tin" tail, and deep-frying oil is listed unflagged with no
  amount as "<oil>, for deep frying": the words are `_data/food/incidentals.yml`, read by
  `incidental_verdict` in `tests/test_taxonomy.py`, which `/tidy-drafts`'s
  `incidentals` rule applies. Nothing wider takes the flag unasked
  (`.claude/commands/ingest.md`). A flagged line may share its name with a real one: a
  cheesecake that greases with butter and bakes with it is right to list
  butter. The test objects only where nothing but an incidental line accounts
  for a main ingredient.
- **An ingredient's quantity is its own `amount:` key, never inside `item:`
  text.** The highlighter is driven by `{% if item.amount %}` and never scans
  text, so `item: "~1 tbsp tamarind paste"` renders unstyled with no error.
  No test catches this.
- **`serves` / `makes` values may be prose in Helen's voice** ("Depends on
  appetite"); never tidy one into a number. That is why `serves_estimate:`
  exists: the scaler needs an integer and her words must not be touched. It
  is required wherever `serves:` does not open with a number, which includes
  every `makes:` recipe. `makes:` is never read as people however numeric it
  looks: 950 ml is not 950 portions. It is an unquoted integer — a quoted
  `"6"` is a string and the plugin will not read it. It is produced at
  ingest; ask Helen rather than guess when the source does not support one.
- **A range takes its lower end.** The scale is portions wanted over portions
  made, so a smaller base gives a bigger multiplier and more food, and
  over-catering is the safe direction. This governs `serves: "4–6"` (the
  plugin takes 4), any `serves_estimate:` written from a range, and a
  `makes:` range on the recipe page's box (§8.2).
- **A component recipe cannot always be one number, and the truth goes in a
  note.** A ganache glazes one cake, fills another or makes truffles.
  `serves_estimate:` takes the commonest use and a note carries the rest. Do
  not invent a schema for this without Helen (DECISIONS §8.2).
- **`method` xor `method_groups`**; with both present the second is silently
  dropped. A `method_groups` entry needs `name` and `steps`.
- **Group names.** Ingredient group names are bare nouns; the template adds
  the rest, and only when a recipe has more than one group
  (`_layouts/recipe.html`):

  | `name:` | heading |
  |---|---|
  | `dressing` | For the dressing: |
  | opens with `to ` (`to serve`, `to finish`) | To serve: — itself, capitalised, no "For the" |
  | `variation: chocolate chip` | Variation: chocolate chip — no colon after |
  | absent | For the base: |

  So a name must read after "For the" or open with `to `; a bare verb
  (`assemble`) does neither, and a leading article (`for the dressing`) is
  refused by `test_group_names_omit_leading_article`. A method group's name
  is printed bare — no prefix, no colon, no capital added — so
  `Make the sauce` is fine there. The CSS uppercases both.
  `test_a_group_named_to_something_is_its_own_heading` pins the table.
- **Cross-recipe links are markdown and relative**: `[text](../slug/)`. Front
  matter is never run through Liquid, so a root-relative link cannot pick up
  the baseurl.
- **`notes:` items are `{label, text}`, both keys always present**, on both
  sites and in both drafts repos; a bare string is refused everywhere
  (`test_note_dicts_have_label_and_text_when_dict` on drafts). An empty
  string in either half is a placeholder for Helen to type into, and both
  layouts count an empty note out before deciding whether to print the NOTES
  heading. A published note must have both halves filled
  (`test_note_dicts_have_label_and_text`). Four or more notes is the signal
  to write body content instead (§4.1).
- **A draft never says `notes: []`, and a draft note with text never has an
  empty label.** A draft with nothing to say carries one empty pair, so
  there is always somewhere to type; text nobody has headed is labelled
  `"QQ"`, which stops it publishing unread.
  `python3 scripts/tidy_drafts.py --only notes --apply` writes both, and
  `test_a_draft_has_a_notes_slot_and_no_unlabelled_note` (food) and
  `test_a_draft_drink_has_a_notes_slot_and_no_unlabelled_note` refuse
  either. A published page with no notes may write `notes: []` or omit the
  key; a published drink may also keep the draft's empty pair, which prints
  nothing. A note with only one half written is refused
  (`test_a_published_drink_note_is_a_filled_pair`).
- **`internal_temp_ref`** (with `doneness`) pulls a live figure from
  `_data/food/internal_temperatures.yml` (§14); opt-in.
- **Filenames are stable by default.** If a rename is clearly indicated, say
  so and ask.

This is not the only shape a food document can take: `_food_magic_bag/`
(§4.3) has its own schema and its own test file, so the rules above can stay
unconditional.

### 4.0 The gate flags — read this before editing any recipe

The flags live under `meta:`. **`CLAUDE.md` owns the rules for an agent**:
set `proofread: false` in the same commit as any edit to a recipe file, never
set `proofread: true` or `rewritten: true`, and never move a baseline without
Helen's grant. This section is what each flag means and how the machinery
reads them.

#### What each flag means

| Flag | `true` means |
|---|---|
| `rewritten` | the prose on the page is Helen's, not the source's |
| `awaiting_fix` | a known problem is ticketed against a page she has read |
| `proofread` | Helen has read what is now in the file |

`proofread` does not record how big a change was; it records whether her
judgement still covers the bytes in the file. She is the last human judgement
before a recipe publishes, so any agent edit invalidates it.

`awaiting_fix: true` is a bookmark, not "unfinished". Helen: *"'awaiting_fix'
means I've proofread, but one small thing has been raised as a ticket,
meaning that once that's fixed I can look for just that one thing rather than
having to read the entire file again carefully."* So a flagged page has been
read; do not treat the flag as permission for further edits.

The flags are different facts, and requiring more than one is not the "two
fields that must agree" mistake the plugin header refuses for `published:`.
A page is routinely `proofread: true, awaiting_fix: true` (read, one thing
ticketed) or `awaiting_fix: false, proofread: false` (an agent touched it
since she read it).

#### How the gate reads them

`_plugins/publish_gate.rb` runs at `:post_read` over `GATED_COLLECTIONS` —
`food_recipes`, `food_magic_bag` and `cocktail_recipes` — and removes every
document that does not pass:

| Collection | Publishes only if |
|---|---|
| `food_recipes`, `food_magic_bag` | `meta.awaiting_fix` is exactly `false` **and** `meta.proofread` is exactly `true` |
| `cocktail_recipes` | both of the above **and** `meta.rewritten` is exactly `true` |

- **It fails closed.** A missing `meta:` block, a missing flag, the old
  hyphenated key, or a quoted string (`"true"`, `"false"`) all hold the page
  back. A new recipe does not publish until every flag it needs is written.
- **`true` and absent are different states** even though both hold a page
  back: an absent `awaiting_fix` has not been decided, and
  `scripts/tidy_drafts.py` reports a draft with no flag rather than writing
  `false` into it.
- **It removes the document, not a link to it.** A held-back page gets no
  URL, no sitemap entry and no place in `site.food_recipes`, so nothing
  downstream has to remember to filter.
- **Its log line names which flag held each page back**:
  `publish gate: held back N page(s) -- <path> (<flags>)`.
- **Food's `rewritten` is not a gate leg.** It decides whether a row shows on
  the food index (`food/index.html` shows a recipe only if
  `meta.rewritten` or `site.show_source_wording`); the page itself still
  publishes on the two flags. On cocktails `made_before` deliberately does
  not gate, so an unmade cocktail publishes (§9.1.1).
- **`show_awaiting_fix`** switches the whole gate, every leg: `false` in
  `_config.yml`, `true` in `_config_local.yml` so held-back pages stay
  visible while you work.
- Drafts and `dev` pages are protected by `output: false` and are not gated;
  gating a collection whose documents carry no `meta` would delete it.
- **A new or tighter leg can only take pages off the site**, and whatever
  passed only the looser rule leaves silently. Before building one, write
  each combination of flags as a sentence about what does and does not reach
  the live site and show Helen; then count what it will hold back
  (`python3 scripts/dark_pages.py origin/main`) before the change, not after.
- **The gate removes the page and leaves every link to it**, so an agent's
  flip on a linked-to recipe turns
  `test_no_link_in_the_production_build_points_at_a_file_that_isnt_there`
  red, and the caramel recipe is several tests' control page. Such an edit
  cannot merge by itself: `PIPELINE.md` §5 has the two ways through, and
  `scripts/needs_helen.py` names the linking pages.

**Always `awaiting_fix` with an underscore.** Liquid parses
`page.meta.awaiting-fix` as subtraction, so a template asking about the
hyphenated spelling gets arithmetic.
`test_no_recipe_uses_the_old_hyphenated_awaiting_fix_key` guards
`_food_recipes/` and `test_no_drink_uses_the_old_hyphenated_awaiting_fix_key`
guards `_cocktail_recipes/`; nothing scans drafts, so copying an old draft as
a template is the hazard.

#### The proofread test and its two exemptions

`test_agent_edited_recipes_are_not_marked_proofread` reads git history: if a
recipe's newest commit carries a `Co-Authored-By: Claude` trailer, the file
must say `proofread: false`.
`test_agent_edited_drinks_are_not_marked_proofread` in
`tests/test_cocktails.py` is the same test for cocktails.

- **It reads committed history**, so it fires on the run after your commit.
  Set the flag while you edit.
- **`BASELINE_COMMIT`** (`COCKTAIL_BASELINE_COMMIT` for cocktails)
  grandfathers everything up to and including itself. It names a point in
  history, never a file. When it may move is `CLAUDE.md`'s; the constant's
  own comment says to measure first (how many recipes is the rule holding at
  `proofread: false` right now?) and to move it before the next batch of
  agent edits, never after, or it sweeps them up.
- **`INVISIBLE_KEYS`** names keys nothing renders: `source_type` and the two
  retired meta keys. A commit changing only those, with the body
  byte-identical, needs no flip. `test_invisible_keys_are_really_invisible`
  scans `RENDER_SURFACE` (`_layouts`, `_includes`, `_plugins`, `assets/js`,
  `scripts` — not pages) to keep the claim honest, so a key that starts being
  rendered has to come out. `meta.rewritten` is not on the list: it is a gate
  leg on cocktails.
- **A commit that only reorders the `meta:` block is exempt** — the same file
  spelled differently. "Nothing changed" and "I cannot tell what changed" are
  opposite answers, and the guard fails closed only on the second.
- **There is no per-file exemption list, and one must not be built.** A list
  matched on filename never expires and exempts every future edit. If one
  recipe ever needs clearing while others are held, build an entry that
  clears one commit, with the case in front of you.

**Stage explicitly; never `git add -A`.** The repository cannot tell your
edit from Helen's; only the staging can.

**Guarded from every direction**, because every failure mode is silent:
mechanism tests in `tests/test_site_config.py`, data tests in
`tests/test_front_matter.py`, and `tests/test_rendered_pages.py` builds a
real production site and asserts held-back pages absent and passing pages
present. Jekyll's safe mode would skip the plugin altogether (§2.1). The
cocktails side of the gate is §9.1.1.

### 4.1 Body content below the front matter (rare)

The Markdown body after the closing `---` renders verbatim inside
`.recipe-body-content`, between Notes and the source footer; the ganache and
the hollandaise are the examples. **It continues the recipe; it does not
become a blog post.** Section headings in it are peers of INGREDIENTS /
METHOD / NOTES, which needs the exact raw HTML `_layouts/recipe.html`
generates:

```
<h2 class="recipe-section-heading"><span class="section-heading-text">Tips</span></h2>

- A bullet list here parses as normal markdown again.
```

Leave a blank line either side so kramdown parses the surroundings as
markdown. A subtitle under a peer heading is
`<p class="recipe-section-subtitle">`. A bare `## Heading` gets a sane
fallback and will not match the page. Reading width matches Method (no cap),
not Notes.

### 4.2 A bullet list inside one method step

A `|` block scalar with blank lines around the list embeds a real markdown
list inside one step. `.method-full li` is `position: relative` with an
absolutely positioned number (not flex, which lays a nested list beside the
number), and `.method-full ul li` resets `counter-increment` so nested bullets
do not advance the step counter. Grouped methods compose the group indent
with the number column via `calc`.

On a phone the number column is narrower. That rule is
`.method-full > li:not(.method-group-heading-item)`, specific on purpose: a
phone rule written as `.method-full li` above the base rule's identical
selector never renders (§12's equal-specificity trap).

### 4.3 The magic bag — dishes with no recipe

`_food_magic_bag/` holds dishes Helen cooks from memory and will never write
up. The directory does not exist until the first dish is written.

```yaml
title: "Fridge-end fried rice"
tagline: "The thing that happens to yesterday's rice."   # key required, value may be ""
main_ingredients: ["rice", "eggs", "spring onions"]      # what makes it findable
tags: ["fakeaway"]                                        # optional here
ingredients:                                              # flat, incomplete
  - "cold cooked rice"
  - item: "dark soy sauce"
    note: "Light soy makes it taste thin."
notes:                                                    # optional, {label, text}
  - label: "Rice"
    text: "Has to be cold and a day old."
meta:
  awaiting_fix: false                                     # two flags, not three
  proofread: false
```

**It is not a variant of the recipe schema.** Every structural guard in
`tests/test_front_matter.py` is unconditional and stays so; this shape gets
`tests/test_magic_bag.py`, whose `REQUIRED`, `RECIPE_ONLY` and `META_KEYS`
are the schema. The shortness is the feature: capturing a dish has to be
nearly free. `meta:` is `awaiting_fix` then `proofread` — `rewritten` has no
meaning without a source, and `proofread` is required because the gate reads
it (§4.0). An ingredient is a bare string or `{item, note}`, never with an
`amount`. The page carries no standing caveat about incompleteness.
`test_no_recipe_only_keys` catches a dish being written up in place:
promotion means moving it to `_food_drafts/` and taking the recipe schema.

**What `food/index.html` does for it**, most of which fails silently if
undone:

- Every recipe row is gated on `recipe.meta.rewritten or
  site.show_source_wording`. The magic bag is exempted in both places (the
  row `if` and the survivor count), not papered over with a fake `rewritten`.
- The derived ingredient index reads `ingredient_groups`, so a second loop
  reads `ingredients`. An empty vocabulary would hand back every dish on an
  exclusion: fine to include on, dangerous to exclude by.
- A `magic bag` mark on the row, shown in production, because it says what
  you are about to click.

**The mark, and no filter.** The `magic bag` mark is written into the row's
`.badge-group-meta`, the slot the `draft` mark uses, and
`_sass/food/_badges.scss` styles the two in one rule. Nothing on the index
filters on it and no row attribute records it: do not add one. The mark is on
the index row only; the dish page has none.

**A magic-bag dish can be a draft, and `magic bag` is always on the right.**
`draft` on a row means *this row is not on the live site*. For a recipe that
is its collection (`food_drafts`); a magic-bag dish never lives there, so for
it `food/index.html` derives `is_draft` from the gate flags, failing closed.
A new dish is marked `draft` locally until Helen sets `proofread: true`.
Production never shows the pair, because the gate removes a held-back dish
before the index renders. `magic bag` is written last into a slot packed to
its right-hand end. A held-back recipe in `_food_recipes/` is not marked
`draft`. `tests/test_rendered_pages.py` pins this against fixture dishes,
including one local fixture build (`built_with_fixtures(..., local=True)`),
since no production build can contain the pair.

**The spec always runs.** Every test in `tests/test_magic_bag.py` is
per-entry, so an empty collection would collect zero cases and read green.
`tests/conftest.py` parametrises `magic_bag` with a committed fixture entry
(`tests/fixtures/magic_bag/`, outside Jekyll's build and outside
`ALL_MAGIC_BAG`), and `test_magic_bag.py` breaks that fixture one way per
rule to prove each rule can fail. There is deliberately no "collection must
be non-empty" assertion; an empty collection prints *"Not evidence about the
magic bag"* at the end of the run instead.

`.recipe--magic-bag` exists for one spacing consequence (the badges would
otherwise sit against the tagline on a page with no metadata grid) and is not
a hook for making these pages look different.

---

## 5. House style

- Unicode fractions (`½`). `→` for arrows. British spellings. Titles use
  `and`, never `&`.
- Em dash for `--` in prose (not in commit messages, §11).
- **En dash for a number range**: `3–4 mins`, `170–180°C`, `36–40% fat`.
  The scope is what a reader sees, so `cook_time` counts;
  `test_number_ranges_use_en_dashes` reads the whole file, with ISO dates
  blanked first.
- `°C` always, **fan oven only**. Check which figure of a printed pair is the
  fan one before deleting the other.
- **A number and its unit take a space**: `15 ml`, not `15ml`. `kg`, `g`,
  `ml`, `cl`, `cm`, `mm`, `oz`, `tsp`, `tbsp`.
  `scripts/tidy_drafts.py --only units` is the pass, and
  `.claude/commands/ingest.md` carries it as an ingest fix. A temperature is
  not one of the units: `180C` wants a degree sign, which the tidy pass
  reports and never fixes, because spacing it to `180 C` would half-fix it
  and hide the fault. On a cocktail the rule reaches Helen's prose only; an
  `amount` is left alone, since a `QQ` note may quote it back.

**It reaches prose pages, not just recipes** (`tests/test_prose_pages.py`):
the about page, the index pages and the reference pages, including the words
those pages render out of `_data/food/*.yml`.

**The tests stop at a `QQ` line; on food, the formatter does not.** A step
beginning `QQ` is still the source's wording awaiting a rewrite, so no test
holds it to house style and no rule changes a word of it. But
`tidy_drafts.py` formats a food `QQ` line's dashes, unit spaces and accents,
so Helen rewrites from text already in house style; on a drink it leaves the
line alone. The one test that reads a `QQ` line is the drafts accent test,
which the formatter satisfies. `QQ Claude` is our prose and is held to house
style everywhere. Both `conftest._QQ_LINE` and `scripts/tidy_drafts.py` match
`QQ\b(?!\s+Claude\b)` as a prefix, so a finished step that merely mentions
the marker is checked like any other prose.

**Time.** `prep_time` / `cook_time` use `20 mins` / `1 hr 30 mins` / `2 hrs`;
prose uses `mins` / `hours` / `seconds`; only numeric quantities abbreviate.
`cook_time: "Until done"` for family bakes with no stated time. **An
unprinted time is written `Estimated N mins` at ingest, and never reaches a
published recipe**: `test_no_estimated_time_reaches_promotion` fails on one
in `4-promote/`, before the copy, and `test_no_estimated_timings` on one in
`_food_recipes/`. Helen replaces it from the source or from cooking it.

**Accents** come from `_data/accented_words.yml`: a curated
unaccented-to-accented map plus a `no_accent:` list. Prose and titles, a
title gaining an accent its source did not print — never slugs, filenames or
`source:` (reproduced as the publication spells it).

The test for a mechanical fix: does it lose information or make a judgement?
`1/2` → `½` does neither; a spelling is a word, not a character, and is
reported rather than fixed.

---

## 6. `main_ingredients`

An unordered set in the data; ordering is presentation.
`_data/food/pantry.yml` is a bare list of pantry staples that are sunk to the
end and dimmed, by exact lowercase match.

- **Sweet and baking — the completeness test**: everything whose absence
  breaks the recipe, no cap. Flour, butter, eggs and sugar included: a cake
  row without them looks odd, and a search for "eggs" is narrowed by the
  filters, not by leaving them out.
- **Savoury — the substitution test**: would I improvise around a gap here?
  The protein, the fat or liquid that defines the character, anything you
  would have to go and buy, the vegetable that is the point. Herbs, citrus,
  cream or wine that the dish tastes of go in too: they are what people skip.

**Be generous.** Eight is a first-pass guide that has been read as a budget;
Helen's own recipes run to fourteen. The number is an output of the test,
never an input, and is deliberately not enforced.

Cheeses use the bare name where it stands alone (cheddar, feta, comté); keep
"cheese" only where the qualifier means nothing without it (blue cheese,
cream cheese). Butter is `butter` in a draft, where a `QQ butter` line still
earns it, and `salted butter` or `unsalted butter` in a published recipe. Lowercase; `test_no_main_ingredient_spelling_collisions`
enforces consistent spelling across recipes and drafts.

---

## 7. Taxonomy (food)

`_data/food/taxonomy.yml` declares the star ingredients and the tags, and its
own comments carry each tag's meaning, Helen's test for it and the reasoning
behind every retirement. Adding a term there is all that is needed. Read the
file before tagging; what follows is what it does not say, or what a session
gets wrong.

**Star ingredient** (optional) is the one thing the recipe is about; a good
share of the collection correctly leaves it blank. Egg as a binder or
leavening is not `eggs`; a dish literally about the egg is. Squash is
`root veg`. `greens` is leaves and brassicas only; a tomato, courgette,
pepper or leek dish whose vegetable is the point has no star, and a bean,
lentil or chickpea one is `legumes`. `retired_star_ingredients` makes a retired value fail with its
reason rather than blend into "not declared".

**Tags are two groups, different in kind.** Mood is what you feel like
eating, a craving. Practicalities are what the occasion demands of you
regardless.

**Meanings the file leaves to this section:**

- `no-cook` answers "can I put this on the table without cooking?" A spice
  blend is uncooked and a useless answer, so it stays untagged. Melting
  chocolate is prep, so a fridge cake is `no-cook`.
  `test_no_cook_tag_implies_no_cook_time` ties the tag to `cook_time`.
- `virtuous` is narrow: lean protein, or genuinely veg-forward with a wine or
  citrus sauce doing the work. `herbivore-ish` is the wide one: a main where
  the vegetable is the point, whatever else is on the plate, and a dish can be
  both. It is for mains only and implies `main` (`co_tags`).
- `knife and fork` is about how it is eaten, not what is on the plate; a
  whole roast cauliflower takes it as readily as a saddle of lamb.
- Two tags have co-tags: `ice cream` implies `dessert` and `make-ahead`, and
  `herbivore-ish` implies `main` (`co_tags`, `test_co_tag_rules`).

**Meanings you would not guess** (the file has each in full):

- `one-handed food` — eat it curled on the sofa. Anything that rolls, spills
  or needs chasing is out, and no soup takes it, however thick.
- `make-ahead` — a substantial part is genuinely finished ahead. A bake that
  merely keeps is not; an overnight marinade is not. `freezable` and
  `make-ahead` are separate axes.
- `drinks` is anything drinkable that is not a cocktail.
- `side` is a dish served beside a main (mash, a gratin, roast veg, a slaw);
  `extras` is what is not a dish at all (sauces, stocks, pickles, doughs).
- A star is blank where a dish has two leads (chicken and prawns). `fruit`
  goes on a cake only where the fruit is the point, not a citrus sponge.
- `fiddly and fun` and `showstopper` are a pair: the first is about the
  process (you make it because you want to potter), the second about the
  result (it makes people gasp at the table). Either, both or neither. Slow
  is not fiddly.
- `bakes` is a baked good out of the oven, not anything that merely goes in
  it. `sweet snack` is individual pieces eaten by hand outside a meal, not
  slices of something else.

**`main` — this could be dinner — is the one tag with a rule behind its
proposal.** Never with `dessert`, `sweet snack`, `ice cream`, `drinks` or
`nibbles`. A recipe with none of those and none of `bakes`, `extras`, `side`,
`starter`, `breakfast`, `hot snack` is a main. With one of that second six
it is a question to Helen — except that savoury pancakes are breakfast or a
snack, never dinner. A frittata, baked eggs, a vegetable fritter or a griddle
cake may be a main, and is asked.
`INGEST_ONE_RECIPE.md` §4 asks a new recipe the same thing.
It is a proposal for her yes or no, never a deriver.

**Co-tags: the test for adding another.** Sound when the implied tag is a
rollup or a genuine affordance; unsound when it is definitional.

**Standing per-recipe calls, not to be "fixed" for consistency**: the lemony
cavolo nero soup is not tagged `soup` (its own tagline calls it a stew);
`pancetta-white-bean-stew` is not `freezable` though its two sibling stews
are; the griddle cakes are `root veg`. DECISIONS §7 has each.

**"Declared" and "filterable" are the same thing.**
`_includes/recipe_badges.html` builds a recipe page's badges from
`tag_groups` in `_data/food/filter_sections.yml`, so a tag in `taxonomy.yml`
whose group is absent there renders nowhere. There is no way to keep a tag as
page information without a filter button, and that split was proposed and
rejected: if a fact matters while you read, a `notes:` line says more than a
badge; if it matters while you browse, it needs the filter. Do not build it
to make the ontology tidy.

---

## 8. Ingredient search architecture

Most main ingredients appear in exactly one recipe. That makes them useless as
a pantry filter and exactly what a recall lookup needs ("the one with the
sorrel"), which is what the ingredient search is for. Title search exists
beside it.

**The vocabulary is `_data/food/ingredient_words.yml`.** `food/index.html`
emits the whole file as JSON in `#ingredient-vocabulary`;
`assets/js/ingredient-search.js` (pure, no DOM, `IS.create(vocabulary)`) is
the matcher, and `filters.js` is the DOM half. `page-search.js` builds its
ingredient entries through the same matcher, and `_layouts/recipe.html` hands
two of the lists (`trailing_phrases`, `singulars`) to the recipe scaler
(§8.2). Each key's header comment in the YAML holds the reasoning for its
entries; check the real data before adding to any list.

| key | what it does |
|---|---|
| `search.family_button_min_chars` | how many letters must be typed before an `(all)` button may appear |
| `trailing_phrases` | stripped from the END of an entry (`to taste`, `to serve`) |
| `quantity_units` | unit words stripped after a leading number (`1 tsp salt`) |
| `measure_phrases` | leading container and portion phrases, matched as `phrase + ' '`, longest first. The trailing space is load-bearing: `can ` cannot fire on "cannellini" |
| `modifiers` | leading preparation words stripped before matching (`chopped`, `fresh`). Not stripped when the next word is `or`/`and`: "fresh or frozen cranberries" stays whole |
| `stopwords` | connectors that never count as a match target |
| `aliases` | whole-phrase rewrites, keyed on the entry AFTER the strips: a name renames, a list splits (`beef or venison stock`), an empty list drops |
| `display_names` | a button label for a match key; matching still runs on the key |
| `singulars` | plural → singular, so `cherries` and `cherry` are one button |
| `synonyms` | curated families: typing toward the key widens to every member, matched by containment |
| `never_family` | head words that never earn an `(all)` button (`red`) |
| `family_exceptions` | entries that do not count toward their head word's family (`cherry tomatoes`) |

**One normalisation pipeline, `normaliseEntry`:** trailing phrase → leading
quantity → measure phrase → modifiers, then `aliases`. So "juice of 2 lemons"
is an `aliases` job, not a phrase. Every strip is a no-op on a clean entry,
which is what lets both pickers go through `buildMasterList`.

**A picked entry matches a row by word prefix, not containment**
(`entriesMatchKey`): every word of the key must start some word of the row's
entry, so `salt` does not match "unsalted butter". A `synonyms` family is the
one exception and matches on containment of any member.

**An `(all)` button** is offered for a word that is the FIRST word of two or
more entries ("chicken" heads breast, leg and thigh; "chop" is the second word
of "lamb chops" and heads nothing).

**Core ranking rule — three bands**, `bandOf` / `orderByBand`:

1. the entry starts with the query;
2. some word in the entry starts with it;
3. the entry is in the list for another reason (a family member).

Band 3 is never promoted. Get this backwards and "chi" ranks chocolate chips
beside chicken breast. The order within a band is the input order, which is
alphabetical only because `buildMasterList` sorts and `orderByBand` is stable.
`orderByBand` is shared with the cocktails index (`cocktail-search.js`, §9.3.3);
the predicates that decide a band are each site's own.

### 8.1 Two pickers, one code path, very different input

**They are not two implementations.** Both call `IS.buildMasterList` with the
same vocabulary and `IS.search` over the result.

| picker | reads | which is |
|---|---|---|
| HAS TO HAVE (include) | `data-ingredients` on each row ← `main_ingredients` | clean, curated words; a partial hint |
| LEAVE OUT (exclude) | `data-all-ingredients` on each row ← every ingredient `item:`, cut at its first comma or open bracket, lowercased, joined with **`\|`** | prose written for a cook |

The exclude picker uses the harder source deliberately: `main_ingredients` is
partial, and excluding by a partial list is unsafe. So the answer to a bad
exclude candidate is always to teach the vocabulary, never to fork the logic.

**Fuzzy to find, exact to filter.** Typing "pea" offers peas, peanut butter
and pearl barley; the one picked is then applied by
`FilterState.excludesRow` as set membership against the row's entries, never
as a substring. An `(all)` value goes through the family match.

**HAS TO HAVE picks several, AND across them.** `state.includedIngredients` is
a Set, like `excludedIngredients` and like cocktails' `include`. A chip click
toggles membership; chosen chips stay in the pool across searches, first and
still removable; a unique typed match is added, not substituted; the clear
button clears the search and leaves the choices. `FilterState.includesRow` is
`excludesRow`'s sibling but sends every value through the family match,
because it reads the partial `main_ingredients`, where "chicken" has to reach
"chicken breast". With no family matcher it matches nothing. Display labels
live in `filters.js`'s `ingredientLabels` map and are saved and restored with
the rest of the filter state.

**LEAVE OUT's chosen pills** are painted from state into `#exclude-active`,
above the candidate pool, with a line reading "hiding peas and coriander".
The two sections sit side by side in `.search-pair`. How the chips look is
§13.4.

**"One code path" is a claim about the algorithm, not the pickers.** Both
button builders must apply the word-match class (`btn-ingredient--word-match`,
`btn-exclude--word-match`) and both call sites must pass the flag;
`test_both_ingredient_pickers_mark_their_word_matches` checks it. The emphasis
marks a word-prefix match: the entries you meant, against what the vocabulary
brought along. The treatment is `@mixin index-chip-word-match($colour)` in
`_sass/shared/_rule.scss`. The exclude hover is deliberately darker than the
state it replaces, and
`test_the_exclude_hover_is_actually_darker_than_the_state_it_replaces`
compares relative luminance so the direction is asserted.

**Trap: measure production, not your local build.** The local build folds in
every draft, and a draft's `item:` lines are the worst input the picker ever
sees. They are rewritten before publishing, so a vocabulary entry aimed at one
is work done twice. When the exclude picker offers dozens of candidates for
three letters, it is almost always recently added drafts; leave it. Building
the picker's vocabulary from published recipes only is an option that has been
costed and not taken, and taking it is Helen's decision. To measure: build
both configs into `tmp/`, pull `#ingredient-vocabulary`'s JSON and every
`data-all-ingredients` (split on `|`, not a comma) out of `food/index.html`,
and run `IS.create(vocab).search('chi', IS.buildMasterList(entries))` in Node.

### 8.2 The food shopping list and its scaler

Two controls share one set of arithmetic: the shopping list at the foot of the
food index, and the scaler on each recipe page. Costing is cocktails' only.
The rulings behind every rule here are in DECISIONS §8.2.

#### Where each part lives

| file | is |
|---|---|
| `_data/food/aisles.yml` | the aisles in shop order (`order`), a keyword table (`keywords`), and `never` (things that are not shopping) |
| `_data/food/scaling.yml` | every word list the scalers and the judge read: stepped measures, `yields`, `half_recipe`, `count_nouns`, `whole_fruit` |
| `serves:` / `serves_estimate:` / `makes:` in each recipe | the yield (§4) |
| `_plugins/food_shopping.rb` | at build: assigns each ingredient its aisle, resolves the portion count, and hangs `shopping`, `portions`, `portions_estimated`, `made`, `whole_recipes`, `half_recipe` on every document. No arithmetic on amounts |
| `_plugins/food_yield.rb` | reads a `makes:` line into what it counts (`page.made`) |
| `_plugins/food_half_recipe.rb` | judges whether ×½ is offered (`page.half_recipe`) |
| `assets/js/shopping-list.js` | the amount parser (`parseAmount`, `splitParenthetical`), `foldKey`, `foldUnit`, `unitLabel`, `fractionText`. Shared with cocktails (§9.13) |
| `assets/js/food-shopping-list.js` | the list's totals, `build()`, and `totalText`, the one formatter for a scaled food amount. Pure |
| `assets/js/food-scale.js` | one amount at a factor, and the scaler's stepping modes. Pure |
| `assets/js/recipe-scale.js` | the recipe page's DOM half |
| `assets/js/filters.js` | the shopping list's DOM half: the rows, their words, the painting |

The two Ruby readers have no Jekyll in them, so `scripts/food_yield.rb` can
run them and `tests/test_food_yield.py` checks every shape without a build.
Script load order matters on both pages, because each file reads its
dependency at module scope; `tests/test_site_config.py` guards it.

#### How many a recipe feeds, and what it makes

`serves` and `makes` are exclusive (§4). The plugin resolves three things:

- **`page.portions`** — the leading number of `serves:` (the lower end of a
  range, so the multiplier errs toward more food), otherwise
  `serves_estimate:`, which sets `page.portions_estimated` and is printed with
  a `~`. `makes:` is never read as people, however numeric it looks.
- **`page.made`** — `food_yield.rb`'s reading of `makes:`, or nil. Never set
  where `serves:` states a number.
- **`page.whole_recipes`** — true for every recipe whose yield is `makes:`.
  Such a recipe scales in whole recipes; a `serves:` recipe scales a portion
  at a time.

A recipe with neither figure has `portions` nil. The build carries on;
`tests/test_food_shopping.py` fails
(`test_every_published_recipe_states_how_many_it_feeds`, and the draft twin).

#### What the index is handed

`food/index.html` writes `#recipe-ingredients`, one JSON object per recipe
that has a row, keyed by `recipe.url`, and `#recipe-aisles` (the `order` list
only). The page never sees the keyword table, so there is one implementation
of the aisle rule.

| key | meaning |
|---|---|
| `p`, `e` | portions, and whether they are an estimate |
| `y`, `k` | the yield in the recipe's own words, and which key it came from (`serves` or `makes`). Never print `y` behind a fixed word |
| `w`, `h`, `m` | `makes:` recipes only: `whole_recipes`, `half_recipe`, `made` |
| `i` | the ingredients: `a` amount as written, `n` name, `s` aisle |
| `pt`, `f`, `c`, `x` | on an ingredient: fruit parts, fruit, count, pointer (below) |

The word lists reach the panel as attributes on `#shopping-list`:
`data-whole-measures` (`half_step_measures` and `half_step_counts`, joined),
`data-quarter-measures`, `data-count-nouns`, `data-container-nouns`. With an
attribute absent, the rule it feeds does nothing.

#### The aisle and the name

The name is the item text up to its first comma or open bracket, the same cut
the exclusion index makes
(`test_the_shopping_list_and_the_ingredient_index_agree_on_a_name`). **The
longest keyword wins**, matched on whole words: `milk` is dairy and
`coconut milk` is a tin. An exception is an entry, never a precedence rule.
`never` matches the whole name and drops the ingredient. Nothing matching is
`other`. `tests/test_rendered_pages.py` is the only place the Ruby matcher can
be checked.

Two deliberate differences from the exclusion index: a cross-recipe link
(`[grandma's lemon curd](../…)`) is kept, under its link text, and forced to
`other`, where the exclusion index drops it; and an `incidental:` item is
skipped here and indexed there.

#### The panel and its rows

The panel is the last thing on the food index and is shown only in the
shortlist view (§8.9). It totals the shortlist, in the order recipes were
shortlisted, not the rows on screen.

**Each row says what its number counts.** A `serves:` recipe's box counts
portions; a `makes:` recipe's (`w`) counts batches, from the same three
figures the recipe's own page uses, so the two step alike.

    [7]   portions of Moules Marinière             serves:, one person at a time
    [2]   batches of 18 Peanut Butter Cookies      makes: a count; the title names the thing
    [1]   batch of 24 Guinness … Cake squares      the title does not name it: said after
    [1]   batch of 3 dozen Homemade Florentines    a dozen stays a dozen
    [0.5] batch of Ben's Chocolate Ice Cream       makes: a measure, or no count; ½ offered
    [2]   × 8-inch Beetroot Chocolate Cake         makes: one thing the title names
    [2]   jars of Peanut Sauce                     makes: one thing that holds it
    [3]   Rainbow Confetti traybakes               makes: one thing that is it

`rowWords` in `filters.js` writes them:

- **The figure after "of" is what one batch makes and never moves.** It is
  shown only for a count above one, and not for a yield that itself counts
  batches.
- **The thing made is said once.** Where the title already names it (the
  yield's last word found in the title, singular against singular) the noun is
  dropped. Where it does not, the noun follows the title, and the title's own
  last word before any " with …" goes singular if it is a plain plural
  (`singularHead`): "batch of 16 … Brownie squares".
- **A yield of one named thing is not a batch.** Named by the title, the row
  is `×` and the title, which is not made plural. Not named, a container
  (`yields.container_words`) goes first with "of" and anything else follows
  the title, plural above one.
- **It needs the noun**, so a `makes:` that opens with a number names the
  thing (`"16 bars"`, never `"16"`). A bare count has nothing to print and its
  row is "batch of" the title.
- **The batch rows come last, under a hairline** on the first of them
  (`.shopping-list-recipe--first-batch`), drawn only when there are portions
  rows above. Each group keeps shortlist order.
- **"Set all to N portions" sets the portions rows and skips the batch rows.**
  It ships empty: no single number means "as written" for every recipe.
- **A batch box steps ½ (only where `h`), 1, 2, 3 and never 1½.** The input's
  step is a half where a half is offered, so its spinner lands on 1½;
  `batchCount` sends that to the next whole batch in the direction of travel.
  A typed figure is tidied on `change`, never under the cursor.
- **A recipe with no portion count gets no box**, and its row says which key
  to add. It still contributes its ingredients at ×1.
- Every recipe name is a link (`.shopping-list-recipe-link`).

**Trap: do not print the yield beside the recipe name.** A number at each end
of a short line reads as one expression (`7 Moules Marinière serves 4` reads
as 28 portions), and the row has to open with a number. The yield lives in the
input's `title` and `aria-label`.

**Trap: ask the recipe, not the store, whether it can be scaled.** A stored
number is a preference; only the blob says whether there is a count to divide
by (`hasPortions`), and a stored half batch is honoured only while the build
still offers one.

**Trap: an empty panel under a visible shortlist** means the plugin did not
run, and the panel says so. Jekyll loads `_plugins/` once at start: restart
the server (§1).

#### The totals

`build()` in `food-shopping-list.js` takes one entry per ingredient with its
recipe's scale: portions wanted over portions made, or the batch count.

- **Grouping.** The key is the folded name, plural folded to singular
  (`foldUnit(foldKey(name))`), so `onion` and `onions` are one row. The key is
  never shown; the label is the first spelling seen. Rows are alphabetical by
  folded name within an aisle.
- **Units.** Grams and millilitres are the only units totalled in; `kg`, `l`,
  `litre` and `cl` fold into them and a total of a thousand or more is shown
  in the bigger unit. Nothing else is converted: two units of one ingredient
  print as `2 sprigs + 10 g`.
- **Precision.** Nothing is rounded coarser than a gram: two thirds of 200 g
  is 133 g. A sub-gram total keeps a decimal and is never `0 g`. Spoons and
  counts keep cook's fractions (`⅔ tsp`, `3⅓`), which is notation, not
  rounding: ⅔ prints only for exactly two thirds.
- **Ranges, tildes, brackets.** Both ends of `30–50 g` scale; `~` is kept; a
  bracket that restates the quantity scales with it (`1 tbsp (6 g)`).
- **A line with no amount is counted, not summed**: `×3`, or `some (×2)`.

**What the numbers did not reach is named under the rows**: `(Not scaled:
salted butter, salt)` in `.shopping-list-note`. A row is named when any line
behind it had no amount, so a name can appear beside a total. The row itself
then lists the recipes whose line was not scaled, as links
(`unscaledRecipes`, `.shopping-list-unscaled`).

**A row that is one bare count agrees with its number** — "2 lemons", "½
lemon" (`countedLabel`). A spelling some recipe on the row wrote is used
first. A form nobody wrote is made only for a noun on `count_nouns`: the last
word of the name, with a regular plural. Rows with a unit, mixed rows, a name
opening with a by-eye measure, and a name that is a choice or a phrase are
left alone. **Do not widen it to "any last word"**: that is wrong for about a
quarter of real names ("sprigs thyme", "goose", a name cut at its comma).

**A stepped measure is bought in whole ones, rounded up, and the row says
what the recipes call for.** This applies to every word on the three lists in
the next section, alike.

    1 handful, seven portions of a recipe for six   2 handfuls (1¼ in the recipes)
    5 twists ×⅔                                     4 twists   (3¼ in the recipes)
    1 handful ×1.5                                  2 handfuls (1½ in the recipes)
    4 sprigs ×2                                     8 sprigs

- The amount is what to buy. The bracket (`aside` on the row,
  `.shopping-list-aside`) is the total asked for, to the nearest quarter,
  always a fraction.
- **Quarters for every stepped measure here, whatever its step on the recipe
  page.** `food-shopping-list.js` rounds for itself and never calls
  `halfStep`. The list and the recipe page can therefore show different
  figures for a pinch, and that is ruled: do not make the bracket quote the
  recipe page's step.
- No bracket when the two agree, which includes a total that rounds to a whole
  number. The total is stepped once, never each recipe's share. A row with a
  second total names the unit in the bracket.
- A measure written into the item with no amount (`a handful of fresh
  parsley`) is an unquantified line here and is named on the Not-scaled line.

**One fruit, two parts.** `mark_fruit` in the plugin marks a line; `reunite`
does the sums, each inside one recipe. The vocabulary is `whole_fruit`.

| the recipe writes | the blob carries | the list does |
|---|---|---|
| `item: "juice of 1 lemon"` | `f: "lemon"`, `c: "1"`, `pt: ["juice"]` | totals it as 1 lemon, in the fruit's aisle |
| `amount: "1"`, `item: "lemon, zested and juiced"` | `pt: ["zest","juice"]` | totals it, mergeable |
| `amount: "1 tbsp"`, `item: "lemon juice"` | nothing | nothing: a spoonful is not some number of lemons |
| `item: "olive oil, the rest of the oil above"` | `x: true` | drops it beside another line of the same name |

Different parts of the same fruit are the same fruit; the same part twice
adds. Each part is summed, the part needing the most fruit decides, and
counted lines that do not use that part are dropped: juice of 1 and zest of 1
is 1; four zested with 2½ juiced is 4. A line naming no part ("lemon, cut into
wedges") is always added. Two recipes add. A bracket after the note is an
aside, not the part. The fruit must be the last word of the name ("unwaxed
lemons", not "watermelon"). **The name `n` is never changed**, because the
exclusion index and the list must agree on it; the fruit travels beside it.
**A pointer is keyed on its own words** (`whole_fruit.pointers`, or "the zest
of the one …"), never on "no amount, same name": "salted butter, extra, for
greasing" is extra and stays counted.

#### The recipe page's scaler

`recipe-scale.js` stashes every amount as written and scales from that, never
from the screen; at the recipe's own count the written text returns byte for
byte. The control ships `hidden` and the script reveals it. All arithmetic is
`food-scale.js`: `scaleAmount` parses with `parseAmount`, folds kg and litres
down, and prints with `totalText`, so the gram, fraction, range and bracket
rules above hold here too. `2 large` scales to `4 large`: a size word is a
unit to the parser.

**A measure taken by hand or eye scales in steps.** Three lists in
`scaling.yml`, and a word is on exactly one (a test refuses a word on two):

| list | step | 1 at seven portions for six |
|---|---|---|
| `quarter_step_measures` | nearest ¼, never below ¼ (`quarterStep`) | `1¼ handfuls` |
| `half_step_measures` | nearest ½, never below ½ (`halfStep`) | `1 pinch` |
| `half_step_counts` | nearest ½, never below ½ | `1 drop` |

- `food-scale.js` names no measure. `_layouts/recipe.html` joins the two
  half-step lists onto the control as `data-half-step-measures` and the third
  as `data-quarter-step-measures`; handed no list, a handful scales linearly.
  Adding a measure is a line of YAML.
- The word is matched whole, anywhere in the unit, singular or plural
  (`1 small handful`, `1 large handful each`), and the plural is written back
  to suit the new number. The plural is `unitLabel`'s: singular at exactly
  one, plural otherwise, so `½ handfuls`.
- **`half_step_counts` is separate from `half_step_measures` because of the
  half-recipe judge**, which is handed only the latter and lets those halve
  always. `1 lot` of another recipe must go on refusing a half recipe.
- **`large`, `medium` and `small` never join a list**; a test refuses them.
- **The same measure written with no number scales too**
  (`scaleLeadingMeasure`): `a`, `an`, `one` or nothing before a singular
  measure is one, a size word between is kept, and at a result of one the
  recipe's own words stand. `A large handful of fresh coriander` ×3 is
  `3 large handfuls of fresh coriander`. `recipe-scale.js` writes only the
  row's first text node, so an item that opens with a link is not scaled.
  "a few", "some", "a couple of" and a bare plural are not numbers.

**What does not scale is named under the control**: `(Not scaled: Tabasco
sauce, salt)`, parenthesised, comma-joined, no full stop, each name once,
hidden at the recipe's own count. It lists an ingredient with no amount and an
amount or opening with no count in it. The name is the ingredient, not the
recipe's sentence (`noteName`): a leading measure phrase is dropped only where
it holds a declared measure and ends in `of` (so `cream of tartar` survives);
then everything from the first comma or open bracket; then a trailing phrase
from `trailing_phrases`. The comma cut is what makes the comma-joined line
safe. Its cost, accepted: an item that is itself a list is named by its first
member.

**"1 large egg", not "1 large eggs".** When a bare count or size-word amount
written for more than one comes down to exactly one, `scaleAmount` returns
`one` and `recipe-scale.js` rewrites the item's first text node through
`singularItem`: the last word before the first comma, bracket or preposition,
made singular by `singulars` in `ingredient_words.yml` (`data-singulars`) and
then `foldUnit`. It is left as written where that is unsafe: a head naming two
things, a capitalised noun, an `-oes`/`-ies` word the map does not hold, a
word with no plural.

#### What the box counts

| recipe | box | steps |
|---|---|---|
| `serves:` with a number, or a `serves_estimate` without `makes:` | portions | one portion at a time, floor 1 |
| `makes:` that `food_yield.rb` can read (`data-made`) | the thing made; the word "portions" is not printed | whole recipes |
| `makes:` it cannot read (`data-whole-recipes`) | `~N` portions, the `serves_estimate` | whole recipes |

**Whole recipes** (`wholeRecipes`): plus and minus multiply the recipe by 1,
2, 3 and the box shows what that many make. The box is an input showing a
derived figure: a typed number goes to the nearest whole recipe.

`food_yield.rb` reads only the start of the `makes:` line, after an optional
word from `yields.approx_words`:

| `makes:` | ×1 | ×2 |
|---|---|---|
| `4–6 waffles, depending on …` — a range | `4` waffles, the lower number | `8` waffles |
| `about 8 pancakes` | about `8` pancakes | about `16` pancakes |
| `64+ tiny macarons` | `64+` tiny macarons | `128+` |
| `one 8-inch cake` — a number word | `1` × 8-inch cake | `2` × 8-inch cakes |
| `1 dozen mince pies` | `1` dozen mince pies | `2` dozen mince pies |
| `950 ml`, `approx. 75 g` — a measure | `950` ml | `1900` ml |
| `Some`, `Plenty for two people`, `about 8`, `9 or 16` | not read: the portions box | |

The noun agrees with the number (`thingText`): it is the last word before any
" of ", and its plural is `unitLabel`'s. A `group_words` yield (`dozen …`)
never changes. A thing that opens with a digit gets a `×`. A count of nothing
named (`about 8`) keeps the portions box because there is no word to put
after the number.

#### Half a recipe

Whole-recipe stepping has one step below one, ×½, where the build allows it:
the steps are ½, 1, 2, 3 and never 1½, stepped or typed. `food_half_recipe.rb`
judges (`data-half-recipe` on the input); the browser only reads the mark, and
without it minus at one recipe does nothing. The judge is conservative: one
line that will not halve refuses the recipe. Its lists are `half_recipe:` in
`scaling.yml`.

| the amount is | it halves |
|---|---|
| a weight, volume or length (`divisible_units`) | always |
| a by-eye measure (`half_step_measures` plus `by_eye_also`) | always |
| a cup (`half_units`) | if it is a multiple of ½ |
| a spoon or imperial measure (`quarter_units`) | if it is a multiple of ¼: an eighth is the smallest fraction the page prints |
| a count of things — `3` eggs, `2 large`, `1 sprig`, `2 x 400 g` tins | if it is even, or the thing is on `halvable` |
| no number, or no amount | cannot object: it does not scale |

And the yield must halve to at least one of itself: `one 8-inch cake`,
`1 jar`, `1 dozen` and `1 litre` refuse. An odd count halves to a range of one
(`yieldBox`: 5 is `2–3`, `125 ml` is `62–63 ml`, `64+` is `32+`). A portions
box halves only an even number.

- `egg` is off `halvable` on purpose, and that one word decides most refusals.
- `halvable` is about ingredients: a yield of `1 jar` still does not halve.
- A sprig, a bunch, and every `half_step_counts` word are counts to the judge.
- A recipe loses its half step through a rule, never by being named.
- `tests/test_food_yield.py` names the published recipes that keep the
  portions box and the ones offered a half step.

#### Storage

`HTF.shortlist` (`assets/js/assets.js`) keeps the counts in localStorage keys
of their own, per site: glasses, portions and batches. They are separate
because a missing entry means something different in each: one glass; however
many this recipe makes, so `1` is a real stored answer; one batch. A stored 6
cannot say whether it meant people or batches. A half batch is storable;
whether this recipe may have one is `filters.js`'s question.

#### Tests

`tests/js/food-scale.test.js` (the recipe scaler, reading the real
`scaling.yml`), `food-shopping-list.test.js` (totals, rounding, fruit,
pointers), `shopping-list.test.js` (the parser, including that nothing the
cocktails collection writes parses differently — check it before widening the
parser), `food-index-startup.test.js` (the wiring and the batch rows, §10.2),
`shortlist.test.js` (the stores), `tests/test_site_config.py` (the lists
reaching both pages), `tests/test_food_shopping.py` (the data),
`tests/test_food_yield.py`, `tests/test_rendered_pages.py`.

### 8.9 The shortlist view on both indexes

**`shortlisted (N)` is a view, not a facet.** Pressing it on clears every
other filter and shows the whole shortlist. Setting any filter, or choosing a
search result, while it is on turns it off and applies that filter to the
whole collection; typing into a box without choosing keeps it. `clear all`
turns it off. The rule is two functions in `assets/js/filter-state.js`,
`enterShortlistView` and `reconcileShortlistView`, the second run at the top
of every `update()`/`apply()`; `tests/js/shortlist-view.test.js` generates the
cases from both field tables. Why it does not compose: DECISIONS §8.3.

**`?shortlist=1` enters it on both indexes**, by calling the same
`enterShortlistView()` the button calls, so the two doors land in one state.
It runs after the other query blocks and replaces them, and drops the
remembered scroll with the remembered list. The `see shortlist (N)` link
beside a page's shortlist pill (`_includes/page-actions.html`) points there,
ends `#results`, and is shown only while N is above zero.

**`?shortlist=slug,slug` is a shortlist someone sent. The index shows it and
saves none of it.**

- `HTF.filterState.parseShortlist` reads both meanings: slugs are `[a-z0-9-]`
  only, and `1` is never a slug. `HTF.shortlist.resolveSlugs` matches slugs to
  live keys and writes nothing.
- The view is the ordinary shortlist view with `sharedKeys` answering "is this
  one on it" in place of the store. The page drops the list the moment the
  view goes.
- The note `[data-shared-shortlist]` says how many and names any slug nothing
  answers to. `shortlisted (N)` is not lit; pressing it shows your own list.
- The shopping list is open and totals the link's recipes as written. A number
  typed into a box is saved, as that recipe's count.
- **"keep these"** merges the list in (`HTF.shortlist.addAll`) and shows
  yours.

**The link is the whole panel** at the foot of each index, "Share or save the
shortlist" (`[data-shortlist-export-panel]`, shown only while something is
shortlisted). `shortlist-export.js` builds `[data-shortlist-share]` from
`shortlistQuery` and `slugOf`. There is no JSON export, no restore and no
clear button, and a link carries no portions or glasses.

Tests: `tests/js/shortlist-share.test.js` (the store),
`filter-state.test.js` (the grammar), and both index startup harnesses (the
wiring).

## 9. Cocktails

**Cocktails does not share food's data model.** A food recipe is a procedure;
a cocktail is a formula plus a build. The two share the outer layout, the type
scale, the palette contract and house style, and nothing else. Read this
section, not §4.

### 9.1 Nothing about the drinks is public. The shell is.

**The rule: nothing about an unpublished drink reaches the public repo or the
live site** — not its file, not its name in a commit message, an issue, a
branch name or a test.

Two independent mechanisms hold it, and neither is redundant:

- `_cocktail_drafts/` is its own git repository
  (`helen-triages-cocktails-private`), gitignored here. `_food_drafts/` is the
  same shape (`helen-triages-food-private`).
- The `cocktail_drafts` collection is `output: false` in `_config.yml` and
  `output: true` only in `_config_local.yml`, so drafts render at
  `/cocktails/drafts/<slug>/` on the dev server and nowhere else.

**Trap: `output: false` stops Jekyll writing a document; it does not remove it
from `site.<collection>`.** A template that lists a drafts collection must be
guarded by `site.show_drafts`, a key that exists only in `_config_local.yml`
— never by a check that the collection is non-empty, which is true in
production too.

**Trap: `.gitignore` matches by directory name**, so a renamed drafts folder is
un-ignored and stageable in the public repo.
`test_every_drafts_collection_is_gitignored` derives its patterns from
`_config.yml`.

**What is public**: `_layouts/cocktail.html`, `_sass/cocktails/`,
`cocktails/index.html`, every file in `_data/cocktails/`, the glass artwork,
and every promoted drink in `_cocktail_recipes/`. So the field names and the
vocabularies are visible even where a drink is not; that is accepted.

#### Getting the drafts into a worktree

    sh scripts/git-clone-agent.sh helen-triages-cocktails-private _cocktail_drafts
    sh scripts/git-clone-agent.sh helen-triages-food-private _food_drafts

`CLAUDE.md` owns when and why (no ask, both of them). The two `dir` names are
not free choices: `tests/conftest.py`, `tests/test_cocktails.py` (`DRAFTS`)
and `scripts/tidy_drafts.py` name exactly these paths. A symlink to another
checkout's clone half-works (Edit and Write refuse it and writes land in the
other tree) and a copy goes stale silently; clone.

**A green `pytest` in a worktree without the clones is not evidence about the
drafts or the per-draft checks.** Most of what is missing is parametrised per
file, so its per-file cases are never created: each such test shows as one
bare skip, "got empty parameter set". `tests/conftest.py` prints
one line in the report header and the same fact in the terminal summary,
naming each absent clone and the command that fetches it; it reports and never
fails, and is silent when both clones are present.

**While a promotion batch is open there is one working copy to write in** —
`PUBLISHING_A_COCKTAIL.md`. Clone freely to read.

#### The three network wrappers

    sh scripts/git-clone-agent.sh <repo> [dir]
    sh scripts/git-fetch-agent.sh <dir> <repo> [ref] [--keep-head]
    sh scripts/git-push-agent.sh <refspec> [repo] [dir]

Each takes a plain `https://github.com/DeckOfPandas/<repo>.git` URL and passes
`scripts/git-credential-agent-token.sh` to git for that one invocation
(`-c credential.helper=…`, an absolute path resolved from the script's own
location). Git asks the helper when it authenticates, the helper reads the
token from the environment and answers on a pipe, and the token is never in a
URL and never on disk. A clone's `origin` is therefore a plain URL with no
credential: a bare `git fetch origin` inside a clone fails, which is correct;
use the wrapper.

What each accepts, and refuses with exit status 2:

| wrapper | accepts | refuses |
|---|---|---|
| all three | `repo` from `helen-triages`, `helen-triages-food-private`, `helen-triages-cocktails-private` | any other repo; a `dir` that is absolute, contains `..` or starts with `-` |
| clone | one or two arguments; `dir` defaults to the repo name | anything further (no option reaches `git clone`) |
| fetch | `ref` defaults to `main`; `--keep-head` as the fourth argument | a `ref` starting `-` or containing `..`, `:` or a space |
| push | `repo` defaults to `helen-triages`, `dir` to `.` | a refspec with no colon or starting `-`; a destination of `main` on `helen-triages`, however spelled (`x:main`, `x:refs/heads/main`, `:main`) |

`AGENT_WRAPPER_DRY_RUN=1` makes each print its git command instead of running
it; `tests/test_agent_wrappers.py` proves the refusals that way.

**The fetch wrapper fetches one branch and detaches onto it**, then prints the
commit it landed on. Detaching is deliberate: a detached HEAD cannot be
committed onto by accident. `--keep-head` fetches, leaves HEAD where it is and
prints how many commits HEAD is behind; use it mid-work on a branch.

**Fetch immediately before any run whose result you will act on** — before
reporting a failure, calling a change safe, or pushing — not once at the start
of the session. A stale clone's symptom is a handful of `test_cocktails.py`
failures naming real cocktails, which reads exactly like a regression you
caused. `tests/drafts_schema.py` turns the commonest case into one named
failure: each drafts repo carries a `SCHEMA_VERSION` file, `REQUIRED` declares
the version the rules here need, and a mismatch says which side is behind.

**Trap: when pushing to a private repo, give its `dir` as well as its `repo`,
every time.**

    sh scripts/git-push-agent.sh <branch>:<branch> helen-triages-cocktails-private _cocktail_drafts

`dir` is the checkout pushed from and defaults to the current directory, so
naming only the repo pushes the public checkout's branch, history and all, at
the private repo. The other direction — a drafts clone's branch pushed at
`helen-triages` — puts private cocktail names in a public repo. Nothing in the
wrapper checks that `dir` matches `repo`, and nothing on GitHub's side refuses
either push; identical branch names in both repos make the mistake silent. The
three arguments together are the only check.

**Never `git config credential.helper`, in any repo.** `.git/config` is shared
by the primary checkout and every worktree, and git runs a configured helper
from each worktree's own top level, so a configured path breaks every worktree
whose branch lacks the script. The wrappers pass it per invocation instead.

#### Local git inside a drafts clone — `scripts/git-drafts.sh`

    sh scripts/git-drafts.sh <dir> <verb> [args]

It never talks to GitHub. `dir` is `_food_drafts` or `_cocktail_drafts`,
spelled exactly. The verbs are a list, not a pattern:

| verb | accepts |
|---|---|
| `status` | `--short`, `--porcelain`, `--branch` |
| `diff` | `--stat`, `--shortstat`, `--name-only`, `--name-status`, `--cached`, then plain refs and paths |
| `log` | `--oneline`, `--stat`, `--name-only`, `-<N>`, then plain refs and paths |
| `show` | `--stat`, `--name-only`, then plain refs |
| `branch` | `--show-current` only |
| `checkout` | `-b <new-branch>` only, and not `main` |
| `add` | `--` then plain paths (`.` included) |
| `commit` | `-F <file under tmp/>` only; refused on `main` and on a detached HEAD |

"Plain" means letters, digits and `_ . / @ ~ ^ -`, not starting with `-` or
`/` and with no `..`. Everything else is refused. The commit refusal is made
in the script because `guard-main-branch.py` reads the command text, sees no
`-C`, and would check the public repo's branch. The message file is given
relative to the project root (`tmp/commit-msg.txt`); the script rewrites the
path for the clone.

#### A held cocktail is invisible

The gate (§9.1.1) fails closed: a held file stays in `_cocktail_recipes/` and
its page stops existing, and the cards deliberately do not show the flags. An
agent editing a published cocktail takes it off the live site in the commit
that sets `proofread: false`. Nothing on the site or in a green test says so.

    python3 scripts/dark_pages.py origin/main

lists every published file the gate is hiding (run `sh
scripts/git-fetch-main.sh` first). Run it after a promotion: the file count
and the page count should differ by exactly the cocktails Helen is
deliberately holding.

The staging folders in a drafts repo are `1-rewrite/`, `2-make/`,
`3-keep/`, `4-promote/` and, for cocktails, `5-final-proofread/`;
`PIPELINE.md` §3 says what each means. Anything in `4-promote/` is waiting on
Claude and anything in `5-final-proofread/` is waiting on Helen. Both drafts
repos therefore hold subfolders: a script or migration that globs `*.md` at
the top level misses files, so search them recursively.

### 9.1.1 The cocktails publication gate — three flags, and the index that reads them

§4.0 is the authority on what the flags mean; this is what differs for
cocktails.

**A cocktail in `_cocktail_recipes/` publishes only when all three hold:**

    meta.awaiting_fix: false
    meta.proofread:    true
    meta.rewritten:    true

Each is compared exactly, as a YAML boolean. A missing key, the wrong value,
the string `"true"`, the hyphenated `awaiting-fix`, or no `meta` block at all
holds the page back. Food and the magic bag have the first two legs only; the
third is cocktails' alone.

**How it works.** `_plugins/publish_gate.rb` runs at `:post_read` and removes
a failing document from its collection, for the collections in
`GATED_COLLECTIONS`, before any URL, sitemap entry or `site.cocktail_recipes`
listing exists, so nothing downstream has to filter. It logs one line naming
each held file and which flags held it (`publish gate: held back N page(s) --
<path> (proofread, rewritten)`). `show_awaiting_fix: true` in
`_config_local.yml` switches the whole gate off, so every file renders
locally; `_config.yml` sets it `false`.

**Drafts are not gated.** `cocktail_drafts` is not in `GATED_COLLECTIONS`;
`output: false` is what keeps a draft private.

Every cocktail, draft or published, carries the same `meta:` block, exactly
these keys in this order (`META_KEYS_IN_ORDER`):

    meta:
      made_before: true
      ship: "yes"
      rewritten: false
      awaiting_fix: false
      proofread: false

- **`rewritten: true` is Helen's claim and Helen's keystroke**: the prose on
  the page is hers and not the source's. An agent never writes it, on either
  site, and moving a file into a staging folder does not claim it.
- **`made_before` is deliberately not a leg.** An unmade cocktail publishes:
  Helen browses the live site to choose what to make, and what she reads there
  must be her words. The two flags answer different questions and only one
  gates. DECISIONS §9.1.1.

**Migrating a cocktail field** is a textual insertion by script, never a YAML
round-trip, so `git diff --numstat` reads N/0 on every file. Where the data
must move for a rule to be satisfiable, bump `SCHEMA_VERSION` in the drafts
repo in the migration commit and `REQUIRED` in `tests/drafts_schema.py` in the
commit that tightens the rule (§10).

**The tests.** In `tests/test_cocktails.py`,
`test_the_gate_flags_are_real_booleans` and
`test_no_drink_uses_the_old_hyphenated_awaiting_fix_key` cover drafts and
published files; `test_agent_edited_drinks_are_not_marked_proofread` covers
`_cocktail_recipes/` alone, importing `_git`, `AGENT_TRAILER` and
`_only_invisible_keys_changed` from `test_front_matter.py`, with
`COCKTAIL_BASELINE_COMMIT` as its grandfathering line (`CLAUDE.md` says who
may move it). `test_the_gate_covers_a_promoted_drink` in
`tests/test_rendered_pages.py` writes two `zzz-gate-` cocktails differing only
in `proofread`, builds, and asserts one URL exists and the other does not, so
the cocktails leg is exercised on a CI checkout with no private data.

**`cocktails/index.html` has food's shape**: `all_drinks =
site.cocktail_recipes`, the drafts concatenated only under `site.show_drafts`,
and every mood loop, the count and the sort read `all_drinks`. "Nothing to see
here yet" is the line for an empty `all_drinks`; it is a different line from
the no-results one ("Blank canvas.", on both indexes).

**The cards do not show the flags.** A work-state note on every row is a to-do
list down the side of the page used to decide what to drink. The flags live in
the file and the build log.

### 9.2 The source data

The original collection came from a spreadsheet export, `2021-01-29 Cocktails
- Book.csv`, kept in `tmp/` and never committed: one row per ingredient, with
drink-level values on the drink's first row except the multi-value ones
(method, garnish, notes, serve), which spill down. **Read it with a CSV
parser, not by eye**; it is a starting point, not a source of truth, and it is
not uniform. Its truncations are missing text: the fastest route to one is a
second source (§9.2.1).

### 9.2.1 Ingesting from photographs — the second source

Helen photographs book pages and a session transcribes them; `/ingest`
(§11.0.3) is the procedure. Four rules bind every ingest:

- **Resolve every recipe by opening its photo.** Do not infer a batch's
  contents from its folder; batches hold pages from several books and
  edge-of-frame captures Helen did not mean to include.
- **A cocktail already in the collection may share a name and not be the same
  drink.** `sazerac` and `sazerac-death-and-co` live side by side, the second
  titled with its source in brackets. Compare the formula, never the title.
- **The source is the best audit the collection gets, and none of it is
  applied.** A missing citation, an ice instruction that disagrees, an amount
  out by a factor of 24: recorded beside her figure, never applied (§9.4.1,
  the site is canon). Once she has ruled, stop tracking it: an answered QQ
  becomes a plain note recording the answer; only a QQ that was wrong to ask
  is deleted.
- **Hand back the bottles.** A bottle the book names that `bottles.yml` does
  not declare is a note, never a declaration (§9.3.2). What a photograph
  cannot give — a method cut off mid-sentence, an infusion on a page nobody
  shot — is flagged in the cocktail and raised as an issue, never
  reconstructed.

A photograph is not the only way in. Helen also hands a source to a claude.ai
chat (`CLAUDE_WEB_INGEST.md`) and pastes what comes back into an `ingest`
issue on the private repo; `/ingest-inbox` (§11.0.4) consumes it and enforces
the same-name rule mechanically by comparing a fingerprint of the amounts.

### 9.3 Cocktail front matter

```yaml
title: "Sazerac"
tagline: "QQ"                    # the one line of prose; QQ until written
snippet: ""                      # OPTIONAL and rare: the tagline rewritten for
                                 # a search result. Read by _layouts/default.html
                                 # (meta description, link preview), never by
                                 # the cocktail's own layout. Omit the key.
glass:                           # LIST, not scalar
  - "old fashioned"              # canonical spelling; `rocks` fails a test — §9.11.1
garnish: []                      # LIST, declared vocabulary — §9.12.1
  # ["no garnish"] = decided, [] = unfilled.
meta:                            # exactly five keys, in this order — §9.1.1
  made_before: true              # BOOLEAN, gates nothing; first because you
                                 # make a drink and then have an opinion
  ship: "oh gods yes"            # a closed ordered vocabulary — §9.5
  rewritten: false               # the three gate flags, food's names, food's
  awaiting_fix: false            # order. §4.0 is what they mean.
  proofread: false
mood:                            # LIST, derived and then stored — see below
  - "sharp"
  - "aperitivo"
ingredients:                     # FULL list, untriaged, in build order
  - amount: "15 ml"              # the ONLY quantity field, no US units, and
                                 # never a bare number — the unit is required
    generic: "moderately aged Jamaican rum"  # the vocabulary; see §9.3.1
    suggestion: ["Appleton Estate Signature"]  # the bottle. ALWAYS A LIST, and
                                 # `[]` where nobody has chosen one — §9.10
  - amount: "15 ml"
    generic:                     # a LIST means "or", never "and" — §9.3.1
      - "lightly aged and filtered rum"
      - "clear blended multi-region rum"
    suggestion: ["Havana Club 3"]
    note: "Whichever you prefer or are trying to use up"   # the REASON
  - amount: "15 ml"
    generic: "moderately aged rum"
    character:                   # a property of THIS RECIPE'S use of the
      - "blackstrap"             # bottle, not of the bottle in the abstract — §9.3.1
    suggestion: ["Gosling's Black Seal"]
    optional: true               # BOOLEAN, absent means required
  - amount: "10 ml"
    generic: "absinthe"
    as: "rinse"                  # how a MEASURED pour is used; closed list,
                                 # `ingredient_as` in ingredients.yml
    suggestion: []
    card_order: 9                # OPTIONAL and rare: names this entry's tier on
                                 # the CARD outright — §9.10.1
  - amount: "half"               # `half` and `whole` are UNITS.
    generic: "lime"              # A whole fruit is counted, never measured.
    suggestion: []
  - amount: "30 ml"
    generic: "QQ dark rum"       # untyped: QQ plus the source's own words
    generic_claude: "moderately aged rum"   # OPTIONAL proposal keys, legal
    suggestion_claude: ["Gosling's Black Seal"]   # only beside an open QQ,
    character_claude: ["blackstrap"]        # and each must name a declared value
    suggestion: []
serve:                           # OPTIONAL — omit the key entirely if nobody
  ice: "large cube"              # has decided. `ice: "none"` means served UP — §9.10a
  rim: "sugar half-rim"          # free text, and rare
  fill: "half"                   # HOW FULL, which `ice` deliberately never says.
                                 # Declared in serve.yml; replaces the word
                                 # `filled` in the composed clause, so it means
                                 # something only with `cubed` or `crushed`.
serves: 8                        # OPTIONAL, a recipe that makes more than one
                                 # glass (punch bowls); absent means one
method:                          # ORDERED LIST — the steps are sequential
  - "Pour absinthe into ice-filled glass."
  - step: "Muddle the lime chunks hard with the sugar."  # a step is a string OR
    note: "my giant spiky muddler not the polite smooth one"   # a {step, note} pair
to_serve: ""                     # OPTIONAL. SERVEWARE, not a further instruction — §9.4
notes:                           # {label, text}, both keys always, as food.
  - label: "QQ"                  # "" in either half is a PLACEHOLDER, which
    text: "QQ - `generic` values INFERRED, not confirmed: ..."   # neither layout prints
source: ""                       # free text, unlike food; "" where unrecorded
source_url: ""                   # external; nothing verifies it
```

**The schema is the constants at the top of `tests/test_cocktails.py`**:
`TOP_LEVEL_KEYS_IN_ORDER` (from which `TOP_LEVEL_KEYS` is derived),
`REQUIRED_TOP_LEVEL` (everything except `snippet`, `serve`, `serves` and
`to_serve`), `SERVE_KEYS`, `INGREDIENT_KEYS`, `REQUIRED_INGREDIENT`,
`CLAUDE_PROPOSALS` and `META_KEYS_IN_ORDER`. A key not listed there fails
`test_no_unknown_top_level_keys`, and having to write that line is the point.
The block above must agree with them, and `INGEST_ONE_COCKTAIL.md` with both.

#### Key order

**A draft's top-level keys are in the order the page prints them**, and the
block above is in that order. The rule covers drafts and new ingests only:
`_cocktail_recipes/` is never checked or rewritten for order, and a published
cocktail keeps the order it was promoted in. Food has no such rule.

- **The order is read off `_layouts/cocktail.html`, not chosen.**
  `test_the_declared_key_order_is_the_order_the_page_prints` strips the Liquid
  comments, starts at the element holding the page's words
  (`cocktail-head-words`) and places each key at its first mention. Move a
  section on the page and the list must move with it.
- It starts below the glass icon on purpose: the icon is looked up from
  `page.glass` before the title prints, and counting it would put `glass`
  above `title`.
- `meta` sits where SHIP IT? does: the head prints glass, garnish and
  `meta.ship` in one row, with the mood chips under it. The other four `meta`
  keys print nothing and travel with the block.
- `serve` follows `ingredients` because the page prints the ice as a clause on
  the strain step.
- `snippet` and `serves` are never named by the layout, so their places are
  declared by hand in `KEYS_THE_LAYOUT_NEVER_NAMES`, each with its reason:
  after `tagline`, and after `serve`.
- The fixer is `python3 scripts/tidy_drafts.py --site cocktails --only order`
  (§11.0.2); the default `/tidy-drafts` pass includes `order`.
- The drafts rule is `test_a_draft_drinks_keys_are_in_page_order`, and it is a
  drafts-schema requirement (`tests/drafts_schema.py`, §9.1), so a clone
  behind it fails the handshake test first.

#### `mood` — derived, then stored

`scripts/derive_cocktail_moods.py` computes `mood` from generics, characters,
glass, amounts, `serve` and method steps against the `mood_*` blocks in
`_data/cocktails/taxonomy.yml`; the stored list is what the index filters on.
**Change a cocktail's ingredients and the moods may move**: run the script dry
after any such edit, and with `--write` only if it reports a difference.
`test_every_drinks_moods_match_the_derivation` re-derives every cocktail, so a
hand-edited mood cannot outlive the rule.

- `mood_groups` in `taxonomy.yml` declares every mood. Some have a derivation
  rule; `moods_by_hand` lists the ones Helen assigns; a few are both, where
  the rule only ever adds beside whatever she typed. Read the two lists
  (`moods_by_hand`, and the rules in the deriver) rather than trusting a count.
- A newly ingested cocktail therefore lacks its hand-assigned moods until she
  is asked (§9.13), unless she named one in the ingest chat, which the ingest
  writes and the deriver keeps.
- `mood_include` / `mood_exclude` are her per-cocktail overrides, each naming
  the single mood it is about.
- **A mood that keeps coming back after Helen removes it is a wrong field
  under it** (a `serve.ice` left over from an earlier glass). Fix the field
  and the mood derives away; `mood_exclude` is for a disagreement with the
  rule, not with the data.
- **A new derived mood that lands on published cocktails ships invisible.**
  The derivation edits each file, the agent edit sets `proofread: false`, the
  gate holds the page, and `cocktails/index.html` draws no button for a mood
  with no member in the build. Nothing fails. Tell Helen before the merge how
  many published cocktails it takes off the site.
- **A `water` line is invisible to every rule** (`NOT_A_POUR`); the deriver
  drops it before anything is counted.
- **A `QQ <hint>` generic counts as what its hint names** (`qq_hint`), when
  the hint is exactly a spirit family, a family alias or a spirit generic in
  `family_of`, ignoring case. `QQ Gin` stands in for a base spirit, so a gin
  sour derives `sharp` before Helen names the gin. Any other hint, and a bare
  `QQ`, reads as nothing.
- **`no measuring` is the one rule that reads amounts**: every measured amount
  a whole-number multiple of the smallest, in `MAX_POURS` of that measure or
  fewer. The cap is what makes it a filter. A `(top)` falls out of it for
  having no volume, which is deliberately not the same rule as `easy peasy`'s
  set-aside-a-mixer; `taxonomy.yml` carries both arguments.

#### Amounts

**`amount` is the only quantity field**, and every ingredient has one.
Conversions and non-volumetric units live in `measures:` in
`_data/cocktails/ingredients.yml` (`per_ml` and `non_volumetric`);
`test_every_amount_is_readable_as_a_quantity` accepts an amount only if its
unit is declared there.

- **No cocktail may use a US unit** (`US_UNITS`,
  `test_no_amount_uses_a_us_unit`). `oz` and `tsp` stay declared in `per_ml`
  because the dictionary is what makes a conversion checkable. Convert at
  ingest from the source's own figure, with bar-standard rounding (1 oz is
  30 ml); the site is canon (§9.4.1).
- **A bare number is never guessed** — a column of 30/22.5/15 and one of
  0.75/0.5 are thirty times apart — and carries a `QQ - no unit in the source`
  note that the guard reads.
- **A dash has no millilitre figure** and is not missing one. `half` and
  `whole` are units: a whole fruit is counted, never measured, because the
  juice a lime gives is a range.
- **An unmeasured pour is a bracketed noun**: a top-up is `amount: "(top)"`, a
  rinse `"(rinse)"`, a deliberate small pour that does not fill the glass
  `"(splash)"`, a float with no figure `"(float)"`, cinnamon onto a flame
  `"(sprinkle)"`. Each is declared in `non_volumetric` and each has a method
  step saying when (`Top with champagne.`). The brackets mark the slot a
  number would occupy.
- **`"to taste"` keeps its unbracketed shape** on purpose: the bracketed words
  name what the maker does with an unmeasured pour, while `to taste` hands the
  decision to the drinker (the Ti' Punch's lime and syrup). Cost and units
  skip it and the scaler passes it through. Where the drinker adds it at the
  table, the serving goes in `to_serve` ("Lime and syrup on the side, to add
  to taste."), never a method step opening "Serve" —
  `test_no_method_step_restates_to_serve_or_garnish`.
- **A measured pour says its direction in `as:`** — `float`, `rinse`,
  `muddle`, `shell` (`ingredient_as`) — and the page prints it under the
  amount, in the amount's own type: `25 ml` with `(shell)` on the line below.
  So every direction, measured or not, is read in the amount column. In
  `_layouts/cocktail.html` the two sit in a `.cocktail-measure` cell.
  **`.cocktail-use` must stay a sibling of `.cocktail-amount`, never inside
  it**, because `cocktail-scale.js` parses that span's whole text;
  `test_a_pours_direction_sits_under_its_amount` pins it.
- Soda water, never club soda.

**Trap: an amount word is compared as a literal in several readers.** `(top)`
is matched by string in `_plugins/cocktail_costs.rb`,
`_plugins/cocktail_units.rb` and `scripts/abv_worklist.py`, and parsed in
`assets/js/shopping-list.js`. A reader left on an old spelling does not error;
it silently stops matching, and a topped drink then costs nothing and counts
no units. Rename one by dropping the old string from `measures:`, which turns
every unmigrated file into a named failure of
`test_every_amount_is_readable_as_a_quantity`.

#### Method sentences the layout owns

- **The rim wording is the Margarita's own sentence** in `methods.yml`: *"Dip
  only half the rim in water (or tequila) then coarse salt."*, with the
  drink's leading spirit swapped in where it is not tequila. The file cannot
  parameterise a step, so a non-tequila cocktail writes the sentence with its
  own spirit.
- **The twist step is the layout's, and the sentence is `methods.yml`'s.** A
  garnish naming a citrus twist makes `_layouts/cocktail.html` append *"Express
  the twist over the drink then drop it in."* (or *"…then discard it."* for
  `(discarded)`) as the last step. No cocktail writes it;
  `test_no_method_step_opens_with_express` refuses one that does. The template
  reads `canonical.express` rather than spelling the sentences out, and
  indexes the list by position;
  `test_the_layout_takes_the_twist_step_from_methods_yml` pins both. The page
  names the twist: the layout swaps the garnish, less its `(discarded)` tail,
  in for "the twist" — *"Express the lemon twist over the drink…"*
  (`test_the_express_step_names_the_twist`).

#### `generic` and `suggestion`

**There is no field for the source's own wording of a pour.** A field nothing
renders is invisible to the page, the cards, the search, costing and units
alike. The source's words go in `generic` behind a `QQ `, where they show;
anything the fields do not carry goes in a `note:`.

**`generic` is fully typed and is what the index browses by.** An untyped
ingredient is always a visible `QQ`, never an absent key
(`test_every_ingredient_has_a_generic_or_a_qq`), and a `QQ` carries the
source's own words after it — `generic: "QQ aged Jamaican rum"` — because a
bare `QQ` renders as "90 ml QQ". `_is_qq` in `tests/test_cocktails.py` is the
predicate; every check that sets a bare QQ aside sets that shape aside too. A
card shows the generic's card name (§9.10.1). There is no star axis: the index
filters and excludes by ingredient, it does not browse by spirit.

**The three `_claude` keys are a proposal, never an answer**, and are legal
only while the pour still carries a `QQ`, in `generic` or in its `note`
(`test_a_claude_proposal_only_sits_beside_an_open_question`), and each must
name a declared generic, character or bottle
(`test_a_claude_proposal_names_a_real_value`). A bottle `bottles.yml` declares
is a dictionary read: write `generic` and `suggestion` outright, no proposal.
A bare category word nobody can resolve is Helen's alone: `QQ <the words>` and
nothing else. A proposal belongs only in between. `bottles.yml` records no
character, so a character an agent infers at ingest goes in
`character_claude` beside a `QQ -` note, not in `character`.

**An ingest writes `suggestion` on every line, `[]` where nobody has chosen a
bottle**, so Helen can fill it without typing YAML. No test requires the key,
and older published files omit it on some lines. `["QQ"]` is not a shape: it
would make `test_every_suggested_bottle_resolves` skip the pour.

**Sugar is in the generic, and so is the ratio**: `cane sugar syrup 1:1`,
`cane sugar syrup 2:1`, `demerara sugar syrup 2:1`, `turbinado sugar syrup
2:1`. Type plus ratio only where the difference is real, which is why there is
one demerara and one turbinado and not every permutation. On a card the ratio
is dropped (`card_names`). Honey water is the same shape; the bare `honey
water` is the default for a cocktail whose ratio does not matter and is in
`hers_to_apply` (§9.3.1).

### 9.3.1 The ingredient vocabulary — `_data/cocktails/ingredients.yml`

**The file is the source of truth for what a `generic` may be**, and its own
comments carry every ruling; treat it as more current than this section.

**Two layers.** `generic` is the precise category on each entry — Campari,
Aperol, Cynar and Fernet are four generics, not one "amaro", because they are
not substitutable. `family` is a roll-up used only for search and exclusion
("no whisky tonight"), never a browse axis.

**`generic` is stored, never derived** — most brand-named ingredients have no
rule that recovers the category. **A preferred bottle is a `suggestion`, never
a `generic`** (Velvet Falernum is `falernum`, with the bottle in `suggestion`).
The mirror rule: **when nothing generalises a bottle, the bottle is the
generic** (Campari, Cynar, Becherovka; every member of `herbal_liqueurs` is a
proper noun and the family is a filing drawer).

**`generic` as a list means OR, and only OR.** Daisy de Santiago's two rums:
either makes the drink, so an exclusion on one must not drop it. Gosling's
Black Seal, moderately aged and blackstrap, is one bottle with two properties:
that is `character`, never a second list member. Multi-value only when both
bottles can be named and a reason given for each; "I don't know which" stays
`QQ`.

**`character` lives on the recipe line, not in a bottle dictionary.** It is
why this drink wants this bottle, so restating it across recipes is each
recipe stating its own reasoning. **It is never copied from the bottle**: a
line keeps the one character the drink wants, not everything the label lists.
`blackstrap` and `peated` are characters and never generics. A family's
characters are a closed vocabulary where `ingredients.yml` declares a
`<family>_characters` list and free text where it does not (gin). Any such
list is excluded from the declared-generic set by its suffix and enforced by
`test_a_declared_character_vocabulary_is_enforced` — declaring a list is what
switches enforcement on.

**`origin` lives on the bottle, not the recipe**, and is the mirror image of
`character`: where a distillery stands is invariant, so it sits beside the
bottle in `bottles.yml`. Closed vocabulary, `bottle_origins` in
`ingredients.yml`. Two guards: `test_bottle_origin_is_declared` and
`test_cane_juice_bottles_declare_an_origin` (every bottle on `rum_groups`'
"Cane juice" shelf has one). **The accepted cost: a recipe cannot require an
origin.** The Martinique Swizzle says `rhum agricole blanc` and is Martinican
only because its suggestions are. Two mechanisms for origin coexist on
purpose: in the generic where it changes the category (the Jamaicans, the
Demeraras, the clairins, the arracks), on the bottle where it changes the
flavour.

**Trap: any new top-level list in `ingredients.yml` declares pourable generics
unless you say otherwise.** `_declared_generics` derives the vocabulary from
the file's own shape, so a list that is not a vocabulary silently mints its
members as valid generics. The lists that are not vocabularies are registered
in `NOT_GENERIC_LISTS` in `tests/test_cocktails.py`; mappings, `retired_*`
keys and `<family>_characters` lists are skipped by shape. **Nothing detects a
missing registration.** When you add a list, list every top-level key and ask
what each one is.

**Naming.** Every generic reads as an ingredient, natural word order, spirit
word on the end, no inverted commas — `moderately aged Jamaican rum`, `London
dry gin`, `rhum agricole blanc`. `rye` and `bourbon` stay bare because that is
the name you would say; `bonded rye` is a real style. Scotch and Japanese take
*whisky*, Irish and American *whiskey*. Generics are named by what substitutes
for what: never a `flavoured X` spanning non-substitutable members (`vanilla
vodka`, `pineapple vodka`; `sloe gin` its own generic); `lavender-forward
bitters` not `lavender bitters`; `apple brandy` by the fruit, so an applejack
and a Spanish apple brandy share it, and it is not `calvados`; `cucumber` and
`kaffir lime leaves` bare — the leaf is not a variety of lime. Brand-named
styles are generalised (`pineapple-infused rum`, `blended overproof rum`,
`coconut rum-based liqueur`). `Chartreuse Verte` / `Jaune`, not green / yellow. "Pernod" names two
bottles: write the product, not the house.

**Renaming a generic is quote-anchored**: every occurrence is quoted, so match
`"<old>"` exactly, and never rewrite a quoted decision to match a later
rename — that falsifies it. The `retired_*` maps record each successor.

**`hers_to_apply`** lists styles that have bottles and no cocktail, which are
Helen's to apply and never to be typed into from a source's own words.
Removing a line is her grant, in the same commit as the cocktail that earns
the style. `test_no_drink_uses_a_generic_that_is_helens_to_apply` enforces it,
and `scripts/build_ingest_vocab.py` keeps the list out of the printed
vocabulary so a repo-less session is never offered one.

**The governing principle**: everything here serves the user, Helen, getting
the drink she wants; an encyclopaedia of drinks is busywork. Apply it to any
feature that describes a bottle in the abstract rather than in service of one
recipe decision.

**Every rum generic has a card name**, `card_names` — §9.10.1.

### 9.3.2 The bottle dictionary — `_data/cocktails/bottles.yml`

A third string per ingredient after the generic and the card name: which
bottle, its category, and its alias spellings. **Every named bottle is in it
and classified** — `test_every_suggested_bottle_resolves` is not rum-only.
**It means what Helen would pour, not what qualifies**; a bottle she no longer
reaches for is moved to `not_reached_for` with her reason, never deleted.
`unresolved_suggestions` holds any suggestion string that names no bottle,
with a reason, so the test bites on the next one; a row whose string no
cocktail says any more fails its own staleness guard. It is a worklist: read
it, do not quote its size.

**The standing rulings for any ingest:**

- **A house is not a bottle.** Briottet, Monin, Gabriel Boudier: declare each
  product she owns by name and retype the cocktail to it; a house is an alias
  only where it can mean one thing here (Luxardo → Luxardo Maraschino). Never
  add a bare brand as an alias — Bulleit makes a bourbon and a rye.
- **A spirit type beside its own generic is not a suggestion**; it goes.
- **A syrup's suggestion may name what it is made from** ("Acacia honey").
- **Spelling: in the pool, leave the cocktail as she wrote it and add the
  spelling as an alias.** In the staging folders and in `_cocktail_recipes/`
  the rule inverts and every `suggestion` is the bottle's canonical name
  (`test_a_staged_drink_writes_a_bottles_canonical_name`). `STAGED_DIRS` in
  `tests/test_cocktails.py` is the list of folders, and it is a list on
  purpose: a cocktail bounced back for a ruling sits in a folder being edited
  for longer than anything else, which is when an alias creeps in.
- **The cocktail page prints `suggestion` verbatim. It does not resolve it
  through `bottles.yml`.** `_layouts/cocktail.html` puts the recipe's own
  string in the brackets; `bottles.yml` is read by the tests, the costing, the
  units and the reference page, but not by the line a reader sees. So
  **renaming a bottle changes nothing on any cocktail page.** To change the
  page you must edit every recipe that names it, and for a live cocktail that
  is an agent edit, which sets `meta.proofread: false` and takes the page off
  the site until Helen re-reads it (§4.0). Check which recipes name a bottle
  before promising a rename is cheap.
- **Do not derive a bottle's category from the ingredient it sits beside.**
  Keep only what the collection already spells out and hand the rest back. A
  bottle she names is hers to add; what is banned is inference. Every declared
  bottle carries a price in `costs.yml` and a strength in `abv.yml`, and the
  tests fail in both directions.
- **A suggestion's bottle need not be in the ingredient's category** — that is
  the feature (cherry brandy → Cherry Heering) — but a `note` is required when
  it crosses (`test_a_cross_category_suggestion_carries_a_note`), and `QQ`
  counts: the substitution must be visible, not explained. A disjunctive
  `generic` crosses only if the bottle matches none of its options.
- **An absent suggestion is a real answer**: what is cheap and what needs
  using up are facts about the shelf on the day, never about the drink.
- **Aliases are how a bottle keeps one identity** (Planteray is Plantation
  renamed; canonical is Planteray, old spellings stay as aliases). The rule
  governs what is written, the alias map what can be read.
- **A generic with one bottle behind it is that bottle, invisibly.** Removing
  the bottle zeroes the cost and strength of every cocktail that asks for the
  generic with no bottle named. `test_every_priceable_pour_has_a_price` and
  `test_every_counted_pour_can_reach_a_strength` catch this; count the
  bottles sharing a `generic` before removing one.
- **A bottle rename spans both repos and no single-repo step stays green**:
  `test_every_suggestion_is_the_declared_bottle_name` wants the staged
  cocktail's string to equal the declared key. Merge the public and the
  drafts pull requests back to back. A generic has no alias mechanism
  (`family_aliases` maps families), so a generic rename declares both
  spellings through the gap and drops the old one in a later pull request.

**Why a bottle table is allowed when `character` has none**: a bottle's
category is bottle-invariant — Appleton 12 is a moderately aged Jamaican in
every drink — where `character` is why this drink wants it. `Demerara, aged`
and `Demerara, overproof` are appellations, checkable against a fact about the
bottle rather than argued from the glass. Jack Daniels is a bourbon here.

### 9.3.3 The cocktails index's search — three modules

`assets/js/cocktail-index.js` is DOM wiring only; `cocktail-search.js` holds
the pool, ranking, families and the two matching rules (pure, tested);
`filter-state.js` holds `COCKTAIL_FIELDS`; `ingredient-search.js` lends
`fold`, `getWords`, `orderByBand` — the discipline, not the bands.

- **Fuzzy to find, fuzzy to include, exact-or-declared-family to exclude.**
  Over-including shows you a cocktail and the card says why; over-excluding
  hides one and you never learn it existed.
- **Four bands, in order**: prefix of the first word, prefix of any word,
  prefix of any word in a bottle name, then substring. Visible beats hidden at
  equal strength; any real word beats a substring.
- **A chip must be able to explain itself**: a chip found through a name it
  does not show carries that name — the containing name alone where the card
  name is a strict abbreviation of its generic (`clear blended multi-region
  rum`), a bracket otherwise (`cachaça (Sagatiba)`), in whichever spelling
  carried the query. The chip's value never moves, only its label.
- **A multi-word query matches a hidden name from its start** ("el d" finds
  El Dorado).
- **An umbrella suppresses its own bare word**: `gin (all)` takes `gin` off
  the list beside it and leaves `sloe gin` and every ginger. In the pure
  module here; in `filters.js`, at render time, on food.
- **One chip per category, wearing the card's name**; a bottle is a way in to
  its category, not a chip beside it, which needs the pool built per
  ingredient from `data-ing`.
- **The picker answers from the first character** (`search.min_query_chars` in
  `ingredients.yml`) and offers every candidate, with no cap, as food's does.
  Short queries produce long lists; that is chosen. DECISIONS §9.3.3.
- **Prose is not a bottle name** (`search.prose_words` / `prose_marks`; `and`
  deliberately absent — Wray and Nephew is one bottle). `family_aliases` /
  `family_labels` make a family reachable however it is spelled (`whisk(e)y`).
  `not_on_cards` keeps the bare sugars, salt, water, zest and honey off a card
  and out of the search; every syrup stays.
- **A family's `(all)` chip may reach a generic outside the family**
  (`family_reach`): `rum (all)` finds every rum and rhum liqueur on include
  and never on exclude, so a Malibu or Créole Shrubb drink shows under rum
  and survives "no rum tonight". **Every generic on `rum_liqueur_shelf` must
  be reached** (`test_every_rum_based_liqueur_is_reached_by_rum`), and a
  liqueur whose name says rum or rhum must be on that shelf, so a new one
  cannot be missed. `test_family_reach_names_real_things` holds the names.
- **A search umbrella is an `(all)` button that is not a family**
  (`search.umbrellas`): `rhum agricole (all)` selects both agricoles, offered
  and matched as a family's button is, but `familiesOf` and `family_of` never
  see it, so cards and the rum family are unchanged. Its `then_offer` chips
  (the clairins) are listed straight after the chips beginning with its
  label whenever its button is on offer. `test_search_umbrellas_name_declared_generics`
  holds its names.

### 9.3.4 Units of alcohol

**On the live site, with no switch**: the cocktail page prints the line
whenever `page.units` exists. It is **UK units, not the strength of the
finished drink** — `ml × ABV% ÷ 1000` — so water and dilution do not matter
and nothing needs modelling.

**Data.** `_data/cocktails/abv.yml` holds a strength per bottle (invariant,
and a separate file from `costs.yml` because a price decays and a strength
does not), per-generic figures where no bottle is named, and `abv: 0` declared
for every non-alcoholic pour. **A missing key is a test failure; a zero is a
statement.**

**Arithmetic.** `_plugins/cocktail_units.rb` computes `page.units` once at
build:

- **A dash does not count**, the same rule as costing; the exclusion list is
  read out of `costs.yml` (`excluded_units`), never restated.
- **Bitters never count, whatever the amount**: a pour whose generic is in
  `ingredients.yml` `bitters:` is skipped before its amount is read. Cost is
  untouched.
- **An unbottled pour takes its category's mode**: the most common strength
  among the bottles declared under the generic. A `default_bottles` ruling in
  `costs.yml` wins over it (a two-bottle default is averaged), and a generic
  with no bottle reads its own `generics:` row.
- **A category with no single mode gets a default bottle, never a statistic.**
  `test_every_bottled_generic_resolves_to_one_strength` fails the build for
  the next one, naming the category; the plugin's fallback to the mean exists
  only so a page never breaks. `default_bottles` sets the unbottled pour's
  price too.
- A `(top)` spends the volume §9.3.6 gives it.
- The figure is per serving, divided by `serves:` where present. A total that
  rounds to zero is withheld rather than printed as "alcohol-free".

**The line.** It is in the footer under the notes, which prints source, then
units, then cost, above the related cards. The wording is Helen's and is not
polished: "Roughly X units of alcohol in a serving of Y ml (undiluted)." Y is
§9.3.6's `page.volume.serve_ml`; where there is no volume the sentence ends
"in a serving.", and with `serves:` above 1 it reads "in each of N servings".
The scaler reads the line's two data attributes
(`data-units-per-serve`, `data-serves`) for its batch note and never writes to
the line, which is what keeps a per-serving figure from moving with the
multiple box.

**Unsettled strengths.** A `qq:` row in `abv.yml` (always `confidence: low`)
is a strength only Helen's shelf can settle; a bitters stays `low` with no
`qq:` because it can never reach a figure. **`python3 scripts/abv_worklist.py`
is the worklist, not a grep for `qq:`**: the grep lists rows, but only the
script knows which of them change a number somebody can see, because that
depends on how a pour resolves and whether it counts. The script replays the
plugin's own resolution over the published cocktails, so it is also a second
implementation of that lookup. Its output moves whenever a cocktail is
promoted or a bottle is declared: run it, and **never write the number of
`qq:` rows into a comment.**

### 9.3.5 What a drink costs

**Local only and an incidental**: `show_costs` exists only in
`_config_local.yml`. One quiet sentence in the cocktail page's footer, under
the units line, and a price in the shortlist. Data in
`_data/cocktails/costs.yml` (public either way), arithmetic in
`_plugins/cocktail_costs.rb` once at build.

- **Two layers, and a pour takes whichever answers**: a bottle's own price
  where the pour names one, a per-generic figure where it does not — the most
  poured things are juices and syrups and none will ever be a bottle.
- **`default_bottles` is a pricing fact and never a suggestion**: which bottle
  a bare generic means on her shelf.
- **A volume counts, and so does a counted fruit or a weighed solid that has a
  price row**: `fruit_prices` is GBP per piece and prices `1 whole`,
  `4 whole`, `9 each`, `5 cubes` and `half`; `weight_prices` is GBP per kilo
  and prices `25 g`. A count or weight with no row is a flourish and free — a
  dash, a leaf, a garnish, ice, salt and the sugar cube never count; the
  excluded list lives in the data (`excluded_units`).
- **`(top)` is a declared range** (`top_up_ml`), and the shopping list spends
  it. Costing spends the declared range even where §9.3.6 sizes the top from
  the glass.
- The shopping list's rate table carries `fruit` and `weight` maps beside
  `generics` and `bottles`, and multiplies.
- **The figure is per glass and does not move with the scaler.**
- **`cost.complete` withholds a figure known to be wrong**: a drink whose
  ingredient-sized excluded pours (`CocktailCosts::SUBSTANTIAL`) are not
  outnumbered by its priced ones. `cost.exact` prints one figure instead of a
  range.

`checked:` is the file's honesty and the field to distrust first. Master of
Malt refuses automated requests, so Helen reads prices herself.
Apply her corrections by script against the parsed YAML, refusing on any name
not found; a regex over this file matches the wrong block.

### 9.3.6 How much liquid is in a drink

**One figure is printed, and it does not move**: the units line's tail, "in a
serving of Y ml (undiluted)" — one glass, invariant, exactly as the unit count
beside it is. "(undiluted)" follows the millilitres and appears only with
them: it says that 120 ml of drink will not end up in a 120 ml glass. A drink
that states no volume says "in a serving." with no bracket.

**No batch volume is printed anywhere.** Do not add a total under the scaler;
`test_no_drink_page_prints_a_batch_volume` fails if one comes back. DECISIONS
§9.3.6.

**Where it comes from.** `page.volume` (`total_ml`, `serve_ml`, `serves`,
`pours`, and `top_ml` on a topped drink) is computed by `volume_for` in
`_plugins/cocktail_units.rb` — the same generator as the units, because a unit
is millilitres times a strength and a second parse of the amounts is a second
answer waiting to disagree. **The browser does no volume arithmetic.**
`data-total-ml` carries the ×1 figure as an unprinted attribute on
`.cocktail-scale-controls`, for `scripts/glass_fit_report.py` and the volume
tests.

**A `(top)` is sized from its glass.** `fitted_top_ml` in the plugin: the
first glass listed, at its surveyed median, filled to the wash line, less the
room `serve.ice` takes, less the build once the method has watered it
(§9.11.2's `fit_rules`, the same reading the fit report takes), rounded to
5 ml. It is asked once per drink and handed to both the unit count and the
volume, so the two can never disagree about what the top pours. The precision
wanted is ±50 ml, no better.

**It falls back to the midpoint of the declared range** (`top_up_ml` in
`costs.yml`) wherever that sum has no answer: no `serve.ice` (absent means
undecided), no surveyed glass, a punch bowl, `serves:` above 1, more than one
`(top)`, or a build that already fills the glass. So `top_up_ml` still has to
declare every topper, and `test_top_up_volumes_cover_every_to_top_pour` says
so. The page carries which it did as `data-top-from="glass|range"` beside
`data-top-ml`, unprinted.

**It withholds where a figure would be wrong rather than rough.** `volume_for`
returns nothing when the excluded pours are the drink — the constant
`cost.complete` uses (`CocktailCosts::SUBSTANTIAL`), except that a counted
sugar (a generic in `ingredients.yml`'s `sugars`) never counts, because it
dissolves into what it sweetens: the Old Fashioned's sugar cube leaves it
45 ml. A Caipirinha is cachaça, half a lime and palm sugar, and its
millilitres are the cachaça's, not the drink's. It also returns nothing for an
amount nothing can read or a topper with no declared range.
`test_the_drinks_that_state_no_volume_are_exactly_the_ones_that_cannot` in
`tests/test_rendered_pages.py` pins the set by name in both directions.

**Trap, primed and not sprung**: `serve_ml` divides the whole total by
`serves:`, the top included, and a top fills one glass — four glasses need
four tops. No topped cocktail declares `serves:`, and
`test_no_topped_drink_is_also_a_punch` keeps it so: the first topped punch is
a red build rather than a quietly wrong number.

### 9.4 Rules §9.3's schema leans on: `to_serve` and the flaming shell

The schema is §9.3. This section holds the two rules its block points here for.

**Every ingredient line is poured.** The list is additive, never a choose-one;
a drink that takes cognac and rye and bourbon lists three lines. "Either would
do" is a list-valued `generic` on one line (§9.10).

**`to_serve` is serveware and nothing else** — "Straw.", "Ladle and punch
glasses.", plastic giraffes. A finishing action is a method step; the ice is
`serve.ice` (§9.10a).

- The field is one string. It is split on `.` and `,`, and each piece must be
  declared in `to_serve` in `_data/cocktails/serve.yml`, which groups the items
  as serveware, decorations, fire and on the side.
- `test_to_serve_is_a_string`, `test_to_serve_is_serveware_and_not_the_ice` and
  `test_every_to_serve_item_is_declared` hold it.
- `test_no_method_step_restates_to_serve_or_garnish` is keyed on the leading
  verb: a step opening "Serve" or "Garnish" fails; "Float the…" and "Express…"
  instruct, and stay.

**A flaming shell is one ingredient and three steps.**
`test_a_shell_pour_is_written_one_way` holds all of it.

- The rum is a measured line with `as: "shell"`, 25 ml unless Helen says
  otherwise for that drink, written last, with only a `(sprinkle)` of
  `ground cinnamon` after it.
- The method ends on a `shapes.shell` sentence from `methods.yml` ("Fill the
  passion fruit shell with the <X> and set on top of the drink."), then
  `canonical.fire`'s "Set alight." and "Sprinkle the flame with cinnamon."
- The shell itself is in `garnish`, so the meta line names it before the
  ingredients say "(shell)". The layout drops the generated "Garnish with…"
  step for a shell that an `as: "shell"` line fills; a shell with no rum keeps
  its step.
- Fire is a `to_serve` item ("more fire") and counts nothing. The rum is the
  ingredient.

### 9.4.1 The site is canon. Deviation happens in the kitchen.

A cocktail page states one figure. It does not model that Helen sweetens to
taste. When a figure looks imprecise, the question is "what single figure is
the right thing to print", never "how do we capture the imprecision".

- A cocktail whose sugar is undecided gets a `QQ`, not a range.
- A qualified measure (a scant or heaping ounce) keeps its figure and loses its
  adjective to a note.

DECISIONS §9.4.1.

### 9.5 `meta.ship` and `meta.made_before`

**`meta.ship` is a closed, ordered vocabulary**: `ship_scale` in
`_data/cocktails/taxonomy.yml`, lowest rung first: `meh`, `sure`, `yes`, `oh
gods yes` (shown as `yes²`). Two values are deliberately
off the scale, in `ship_off_scale` with the word each renders as: `who knows`
(`???`), never made; and `IOU` (`IOU`), made and liked but never rated. `QQ`
is not a ship value. `test_meta_ship_is_a_rung_or_off_scale` holds the
vocabulary, and `test_ship_agrees_with_made_before` holds `who knows` to
exactly the drinks with `made_before: false`.

`_includes/cocktails/ship.html` draws the mark on the card and on the drink
page. It asks `ship_scale` whether a value is a rung and never names a
vocabulary value itself. A rung is shown as its `ship_words` word where it
has one, on the card and the drink page alike; filters and `?ship=` URLs
match the stored value.

**`meta.made_before` is a boolean and gates nothing.** It is first in `meta:`.
An unmade cocktail may publish (§9.1.1). Nothing on the index reads it: the
YOLO filters read `ship` (§9.13), which agrees with it by test.
`_dev/no-verdict.html` lists the IOUs, the cocktails Helen has made and not yet
rated.

`garnish`'s `["no garnish"]` and `[]` are §9.12.1. The cocktails test suite is
§10.

### 9.7 Liquid traps in the cocktail layout

General Liquid traps (§12), kept here because the layout's header cites this
number.

- **Liquid parses tag delimiters inside a `comment` block.** Quoting a tag in
  an explanatory comment is a build error. Describe the tag in words.
- **An empty string and an empty array are both truthy.** A bare `if` on
  `source: ""` prints a "Source:" line with nothing after it. A list-gated
  section tests `.size > 0`; a string-gated one compares against `""`.
- **`sort` is ASCII, so a capital sorts before every lowercase letter** and
  `I want to faff` jumps ahead of `aperitivo`. Every list of moods or names a
  reader sees uses `sort_natural`; no test holds it.
- **`glass_icon` starts at `""` and is tested against `""`, and the guard is
  not removable** although every cocktail now names a glass: an empty
  filename handed to the include tag is a hard build failure.

### 9.8 What cocktails borrows from food

The two sites share `$font-headings` and `$font-body`; colour and decoration
separate them. The header tape and the footer are shared chrome, drawn from
`assets/img/chrome/` (§2.5). Cocktails has no tape of its own, because a second
tape means a second header.

### 9.9 Derive the rating from the vocabulary

The rating is `meta.ship` (§9.5). Any template or script that needs the rungs,
their order or their words reads them from `taxonomy.yml`. A hardcoded ordering
string drifts from the vocabulary it copies, and each side's tests stay green.

### 9.10 The cocktail page's ingredient line

The line is the `generic`, with the bottle (`suggestion`) in brackets, then
`character` on its own labelled line, then `note`:

    45 ml   London dry gin (Tanqueray)
    15 ml   moderately aged rum (Gosling's Black Seal)
            CHARACTER: blackstrap
    22.5 ml lime juice

- **Nothing else is printed.** A card name may be lossy (§9.10.1); a recipe
  line may not. The page prints the generic verbatim and reads `card_names`
  nowhere.
- **`character` gets a line, not a parenthetical**, because "moderately aged
  rum (blackstrap)" reads as a type of rum. `.cocktail-character-label` is
  uppercase `$font-label` in quiet grey and the words are upright in
  full-strength text, so
  the line cannot be mistaken for the italic grey `note` under it. It carries
  no hue.
- **`.cocktail-suggestion` is quieter than the generic it follows**: the
  generic is what the drink requires, the bottle what Helen reaches for.
- **`generic` and `suggestion` may each be a string or a list.** Liquid's `for`
  treats a bare string as a one-item sequence, so one loop handles both. A list
  `generic` joins with an italic "or".
- **`optional: true` prints a plain word after the name.** It is not food's
  `incidental`, which hides a line; this shows the line and marks it.
- A generic listed in `always_fresh` in `ingredients.yml` is printed with
  "fresh " in front, and `standing_notes` supplies a note for a generic that
  always carries one.

#### A unit the name already says is printed once

The data stays as written (`amount: "1 cube"`, `generic: "sugar cube"`). The
line is corrected where it is printed:

    1 cube + sugar cube            →  1    sugar cube
    12 cubes + sugar cube          →  12   sugar cubes
    8 leaves + kaffir lime leaves  →  8    kaffir lime leaves
    1.5 each + passion fruit       →  1.5  passion fruit

The unit moves into the name when it is the name's own last word (compared
folded to a singular), replacing that word as the amount wrote it, so the
plural is always the amount's and nothing pluralises a generic. `each` is never
printed. The rule applies only to a one-word unit after the number, a single
`generic`, and a name of more than one word. `16 cubes raw sugar` repeats
nothing and is untouched.

| where | what it does |
|---|---|
| `_layouts/cocktail.html` | decides at build: prints the number in `.cocktail-amount`, marks it `data-unit-quiet`, keeps the written amount in `data-amount`, and puts the unit in `.cocktail-unit-in-name` |
| `assets/js/cocktail-scale.js` | obeys the mark and decides nothing: scales `data-amount`, then writes the number to the amount and the unit to the slot (`HTF.scale.splitUnit`) |
| `assets/js/shopping-list.js` | `quietUnit`, the same rule for the index's shopping list, where the label takes the plural |

The rule is written twice, in Liquid and in `shopping-list.js`, because the
drink page is built before any script runs. `test_no_drink_page_says_a_unit_twice`
reads every built page and `tests/js/shopping-list.test.js` covers the same
amounts. Cards print no amounts.

### 9.10.1 Cards and search read the vocabulary

**The card's ingredient line is a plugin**, `_plugins/cocktail_card_ingredients.rb`.
It hides, labels, joins and emits search data from one list per cocktail
(`card_ingredients`), so the search pool and the visible line cannot drift. The
index card and the related card on a drink page both print that list.

**What a card names.** `card_names` in `ingredients.yml` maps a generic to its
card name; a generic with no entry prints itself. The card shows the category,
never the brand, and the shortest name that says what the drink is like: `gin`
for any gin, but `bourbon` and `blanco tequila` kept apart from their
neighbours.

- Two generics collapsing to one card name must be declared in
  `card_names_may_collide`; an undeclared duplicate fails a test.
- `card_name_joins` rewrites a disjunctive pair that reads badly.
- Two lines of the same rum print the name twice, correctly.
- `character` is never on a card.
- Card text is lowercased in CSS, not in the markup.

**The order** is by tier, then largest volume first inside a tier, then the
recipe's own order:

1. base spirits
2. lower-proof alcohol (liqueurs, amari, fortified and aromatised wine, wine
   and sparkling)
3. juices, citrus before the rest
4. syrups, honeys and sugars
5. everything else
6. bitters
7. anything with `as:` `float`, `rinse` or `shell`

The sections of `ingredients.yml` are the classifier (`TIERS` in the plugin). A
generic in no section warns at build and fails a test.

- **`as:`** records how an ingredient is used. Its values are the closed
  vocabulary `ingredient_as` in `ingredients.yml`. `muddle` is recorded and
  sorts nothing: a muddle covers both expressing a lime and dissolving a sugar,
  so grouping on it put the spirit last on spirit-led drinks.
- **`card_order: <n>`** on an ingredient replaces its tier. `0` is legal and
  means "before tier 1". Ruby's `||` treats 0 as truthy, so the plugin is
  right; a Python mirror must test `is not None`.

**Highlighting and search read build-time attributes, never rendered text.**
Each ingredient on an index card carries `data-ing`. The search pool is generic
plus card name plus suggestion, with alias spellings resolved through
`bottles.yml`; the canonical name joins the terms and does not replace them.
When a template stops rendering a string a script matched on, the script breaks
and nothing looks wrong, which is why no script matches on text.

**The card's three stacks share one budget.** A wrapped name caps the
ingredients and the chips at two lines each, and three rendered ingredient
lines cap the chips at two.

- The name half is CSS: `.drink-card-name--wrap` is a sibling of both stacks.
- The ingredient half is `assets/js/card-line-budget.js`, which sets
  `.drink-card--ingredients-3`, because CSS can ask how many lines are allowed
  and never how many rendered.
- **A hidden card measures zero**, so anything that measures cards must re-run
  when pagination changes what is visible. `cocktail-index.js` does.
- The same pass orders the chips (§9.13), because the cap it sets is one of the
  things the order depends on.

### 9.10a `serve` — where the ice lives

A cocktail has a build and a serve. The serve is the vessel (`glass`), the
garnish, the serveware (`to_serve`) and the ice in the glass:

```yaml
serve:
  ice: "large cube"   # a key of `ice` in serve.yml
  rim: "sugar half-rim"
  fill: "half"        # how full; cubed and crushed only
```

- **Absent means nobody has decided; `ice: "none"` means served up.**
- It is the ice in the glass, never the ice in the shaker.
- There is no `chill` key. A chilled glass is assumed; freezing or rinsing a
  glass is a method step.
- `rim` is free text.

**The page composes the strain step.** A bare `Strain.`, `Fine strain.`,
`Double strain.`, `Dump.` or `Pour.` becomes the technique, plus the glass's
phrase from `serving` in `glasses.yml`, plus the rim, plus the ice's clause
from `in_the_glass` in `serve.yml`: "Strain into an old fashioned glass, over a
large ice cube." Each fact is stored once, and a cocktail that changes glass
gets a corrected method.

- Ice you pour onto takes a comma and "over"; ice the glass is full of takes
  "filled with".
- The rim rides on the glass, before the ice, written as a garnish would be:
  *"…into a martini glass with a sugar rim."* `serve.rim` is free text that
  must hold the word "rim" (`test_a_rim_says_rim`); the layout picks "a" or
  "an" and puts a comma before a "filled with" clause — *"…with a salt rim,
  filled with ice."* It is never a step of its own. A rimmed drink with no
  strain step prints its rim under "To serve".
- **`fill` replaces the word "filled"** in the clause, so it means something
  only where the clause has one. `test_a_fill_has_something_to_fill` refuses
  the other pairings.
- **Do not add an `ice` value to say "how much".** The mood deriver tests
  `serve.ice` for crushed and blended, and `mood_serve_ice` in `taxonomy.yml`
  lists `crushed`, so a new spelling of crushed moves the moods. Quantity is
  `fill`'s job.

**The glass generator composes the build step too, on drafts only.**
`in_the_glass` in `methods.yml` maps a canonical step to the sentence the page
prints ("Add all ingredients." becomes "Add all ingredients to a highball."),
with `<glass>` filled from the same phrase.

- Only the first such step is composed.
- A later strain step then drops the glass, unless it has an ice or rim clause
  to add.
- The switch is `page.collection == "cocktail_drafts"` and nothing else. It
  stays that way until Helen has re-read the published set.
- CI builds no drafts, so it cannot exercise this. Build with
  `_config_local.yml` and read the pages.

**The page also writes the closing steps.** A declared citrus twist in
`garnish` adds an express step (`canonical.express` in `methods.yml`; a
`(discarded)` twist takes the discard form). Every other garnish adds "Garnish
with…", except `no garnish` and a filled shell (§9.4). "To serve" is what
happens to a drink that is already finished.

`test_serve_ice_is_not_restated_in_the_method` and
`test_no_method_step_ends_on_a_dangling_word` are the ratchets.

### 9.11 Glass icons — how they are sized, drawn and published

The published set is `_includes/icons/glasses/`, one SVG per name in
`all_icons` in `_data/cocktails/glasses.yml`. `icons` in the same file maps
each glass spelling a cocktail may write to a drawing. Several spellings share
one (`rocks` draws `old-fashioned`); `mug` and `mule mug` are two drawings.
`_dev/glasses.html` is the comparison page.

#### Sizing

Every use divides the icon's `heights_mm` by the tallest glass's, counted live
from `all_icons`, then compresses the ratio so short glasses stay legible.
`heights_mm` is generated (§9.11.2).

| where | compression | what the result drives |
|---|---|---|
| drink page (`_layouts/cocktail.html`) | `ratio × 0.68 + 0.32` | `--glass-fill`, a fraction of the title block's height; the drawing is never shorter than `$glass-min` in `_cocktail.scss` |
| index card and related card | `ratio × 0.5 + 0.5` | `--glass-ratio`, multiplied by `--glass-cheat` and `--card-glass-scale` in `_cards.scss` (§9.13) |
| `/cocktails/reference/glasses/` | none | `--glass-ratio`, true relative height (§9.11.2) |

A glass with no `heights_mm` falls back to the stylesheet's default. An icon
renders at the height its **viewBox** is given, so the canvas must fit the
drawing (§9.14).

#### Drawing

- **The whole published set is line art**: `.glass-icon-line`, stroke
  `currentColor`, `vector-effect: non-scaling-stroke`, so the weight is set
  once in CSS whatever the viewBox.
- **Fill-only artwork has a switch that is kept and unused.** `SOLID` in
  `scripts/normalise_glass_icons.py` is empty and `.glass-icon-solid` in
  `_cocktail.scss` is its other half. A filled icon is heavier and its ink
  scales with the drawing.
- **Ask "must this be redrawn" before "can this be traced".** Tracing is a
  lossy redraw. `scripts/trace_centrelines.py` derives centrelines and is valid
  only for uniform-width ink. `scripts/glass_ink_coverage.py` measures density;
  compare ratios within one run.
- **The site draws far thinner than Helen edits**, so a gap in a stroke that is
  invisible while drawing is open on the page. `scripts/glass_stroke_gaps.py`
  finds gaps in rendered pixels. There is deliberately no test: the set is
  replaced wholesale if at all.
- **Trap: a root `<svg>` is `overflow: hidden` in every browser's default
  stylesheet**, which shears a stroke on the viewBox edge. Every icon renders
  with an explicit `overflow: visible`.
- `scripts/svgrender.py` is the rasteriser the measuring scripts and two tests
  share.

#### Publishing a drawing

Helen's Inkscape sources are in `_design_sources/cocktails/glasses/`, one
`glass-<name>.svg` per published icon (§9.15). Jekyll ignores the folder and no
build step reads it.

- **`scripts/normalise_glass_icons.py` reads a gitignored inbox,
  `tmp/cocktail-glasses/`, not the archive.** Its `main()` empties
  `_includes/icons/glasses/` and rewrites every icon, so it refuses to run
  unless the inbox holds usable files. Regenerating the set means copying the
  archive into the inbox first.
- **To publish one new drawing, call `normalise()` on that file from a `tmp/`
  script.** Never call `main()` for one file. Importing the module is safe.
- The published name is the source's file name without `glass-`.
- The normaliser reads `<path>` and `<circle>`. A circle becomes a two-arc
  path; a filled one is a dot and carries `glass-icon-dot` beside the line
  class, which gives it back its fill. Any other shape stops the script by
  name.
- If the published set is emptied, recover with `git show HEAD:<path>`.

### 9.11.1 The canonical glass vocabulary is a rule

`canonical_glasses` in `glasses.yml` maps an alias to the spelling a cocktail
must write. `test_drinks_use_the_canonical_glass_spelling` reads its whole
vocabulary from that map, so adding a pair is what makes it enforced.

- The rule governs what is written. The `icons` map governs what can be read:
  its aliases stay, so a cocktail still renders if one slips through, and an
  ingest can absorb a source's spelling.
- An alias absent from `canonical_glasses` is permitted. Silence means "not
  asked yet".
- Every cocktail names a glass: `test_every_drink_names_a_glass`.

### 9.11.2 What each glass holds — the survey, the rules, the fit report

This is a spec, not an inventory. Nothing records Helen's cupboard, and nothing
should.

**The survey is the fact.** `_data/cocktails/glass_survey.yml` holds one row
per distinct product: a capacity and a height as the maker's or a retailer's
page states them, the page's own words in `stated`, and the URL.

- A product gets in only if the page itself names it that type.
- `capacity_basis: nominal` (a pouring or filling line) is recorded and not
  counted as a capacity.
- `exclude: "<why>"` keeps a row visible and uncounted.
- A row with neither figure is a search that came back empty; its note says
  what was looked for.

**Three blocks of `glasses.yml` are generated from it**, between marker
comments, by `python3 scripts/glass_survey_stats.py --write`:

| key | what it is |
|---|---|
| `typical_ml` | n, min, median, mean, max of capacity, per icon |
| `typical_height_mm` | the same for height |
| `heights_mm` | each icon's median surveyed height, or its `height_overrides` entry |

Fix a number in the survey, never between the markers.
`test_glass_survey_statistics_are_current` runs the script's own `check()`.

- **`height_overrides` is Helen's.** The punch bowl is held well under its
  surveyed height because the tallest glass is the denominator of every scale
  in §9.11, and the two old fashioneds keep the heights they had.
- `survey_only_types` is for a type that draws another type's icon but differs
  in size. It is empty.

**`/cocktails/reference/glasses/`** (`cocktails/reference/glasses.html`) is the
published relative-scale view: every glass on one shelf in the home green,
alphabetical by name, each with its mean and range, and nothing else.

- Figures are rounded to the nearest 10 ml on the page, never in the data.
- Each label is centred under the drawing's base, not its box. `base_centre`
  in `glasses.yml` is generated by `python3 scripts/glass_base_centres.py
  --write` from the rasterised icons.
- Its strokes are thinner than anywhere else a glass is drawn
  (`_sass/cocktails/_reference.scss`).
- **Trap: Liquid does not resolve a nested lookup.** `g.typical_ml[pair[0]]`
  is nil, silently. Assign the key to a variable first.
  `test_the_glasses_page_shows_every_glass_once_with_its_surveyed_ml` catches
  it.

**`fit_rules` in `glasses.yml` are the rules**: dilution per method family,
blended volume, wash line, ice space, the large cube, punch cups. Each is a
sourced `{low, high}` range, because the sources disagree and one figure would
hide which way. The three wet dilutions (stirred, shaken, short shake) are
Helen's own figures, written on both ends of the pair; the ranges she chose
against are in the file's comment and are not to be restored from the sources.

The rules decide something as well as flag it: a `(top)` is sized from them
(§9.3.6). `_plugins/cocktail_units.rb` reads the method into a dilution family
(`method_family`) and the layout prints what the report needs as unprinted
attributes on `.cocktail-scale-controls`:

| attribute | meaning |
|---|---|
| `data-total-ml` | the recipe as written, in ml (the plugin's own sum) |
| `data-top-ml` | how much of that total is a `(top)` |
| `data-method-family` | the dilution family |
| `data-after-ml` | in the glass but added after the shake, so never diluted |
| `data-aside-ml` | in the recipe and not in the glass (the rum in a shell) |

**`python3 scripts/glass_fit_report.py`** builds the site with the local config
(drafts render there), reads those attributes, and writes a GitHub checklist to
`tmp/glass_fit_report.md`.

- It reads the forgiving end of every range, so a flag means the drink does not
  fit even on the kindest reading.
- A drink is flagged only when it is over by more than `fit_rules.tolerance`.
- A top is judged apart: the report checks the build and says how much room is
  left. The top flag fires only when that room is under
  `fit_rules.top_room_min` of the house range's minimum.
- Both thresholds are judgements, not sourced, and `glasses.yml` says so.
- **It is a report and not a test on purpose.** Every flag is Helen's judgement
  about one drink, and a failing test on `main` stops the deploy.
- `tests/test_glass_fit_report.py` pins the arithmetic in `check` with no build.

### 9.12 The method-step dictionary — `_data/cocktails/methods.yml`

A closed vocabulary for the mechanical spine of a method, free text for
everything else. An identical repeated step is recognised; one that varies has
to be re-read.

**The test for whether a step belongs in the dictionary: does its phrasing
carry information?** "With ice" versus "over ice" carries none. "Other than the
champagne" carries all of it. The tail of a method is never canonicalised.

| key | holds |
|---|---|
| `canonical` | the literal steps, grouped by technique |
| `shapes` | sentences with one slot: `Shake all ingredients other than the <X> with ice.`, `Top with <X>.`, `Float the <X> on top.` |
| `in_the_glass` | canonical step → the sentence the page prints with the glass named (§9.10a) |
| `proposals` | Helen's exact string → a suggested canonical form |

- **A filled shape counts as canonical** everywhere a literal does: the
  proposal tests, the ingest preflight, the standalone ingest document. The
  slot takes the ingredient as the recipe names it. One slot is the ceiling; a
  step that needs two is tail.
- **Order matters among `shapes`: the first match wins.** A narrower sentence
  sits above the plain one that also matches it, as the two lime-shell lines
  do; the file's comments say which.
- **The strain group is five bare techniques**, because the glass and the ice
  are fields (§9.10a).
- **A vocabulary that keeps growing is usually absorbing a fact that belongs in
  a field.** When a step is incoherent, ask which field is wrong.
- **For a short form, the preceding step is the whole question.** "Shake all
  ingredients with ice." and "Shake with ice." mean different things, and the
  line above decides which is right.

**Changing a canonical step is propose, then let Helen delete.** A row of
`proposals` is a suggestion; she rejects one by deleting it, and a pass applies
only what survives. `proposals: {}` is the settled state. Its guard asserts the
key exists, not that it has rows: a ratchet list and a worklist look identical
and want opposite assertions (§12). Do not turn the map into an enforcing test
without asking.

### 9.12.1 The garnish vocabulary — `_data/cocktails/garnish.yml`

The same bargain as `methods.yml`. `canonical` maps a group name to its list of
garnishes, so every garnish sits in exactly one group, and the standalone
ingest document's grouping is generated from those groups.
`test_every_garnish_is_declared` is a ratchet. The vocabulary is not for
filtering; there is no garnish filter.

The rules for the awkward cases:

- **A twist is a strip of zest**: `lemon twist`, never `lemon zest twist`. Keep
  a tail that is information, such as `(discarded)`.
- **The list is conjunctive**, so "either, the maker chooses" is one string
  (`orange or lemon twist`). `generic` solves the same problem from the
  opposite default; the two fields do not share a convention.
- **A count stays only where the count is the spec** (`three coffee beans`).
- **`["no garnish"]` means decided** and may only appear alone. `[]` means
  unfilled.
- **A garnish is not** an ingredient (anything with an amount), a rim
  (`serve.rim`) or serveware (`to_serve`), and must not restate a method step.
- `no_article` lists the garnishes the generated "Garnish with…" step prints
  without "a" or "an". Any garnish ending in `s` also loses it, as a plural,
  so a singular that ends in `s` would read wrongly: none is declared, and
  one arriving wants a list of its own in `garnish.yml`, not a cleverer test.
  The step's parts are joined on `|`;
  `test_no_garnish_contains_the_join_separator` keeps it out of the names.

### 9.13 The cocktails visual language, and the index and drink page built from it

Markup is `cocktails/index.html` and `_layouts/cocktail.html`; style is
`_sass/cocktails/`, one partial per part named below. Sizes live in the Sass.
This section says what each part is and the invariants no test holds.

#### The ground

The site is black on black: "ink, paper and glass", with the paper black.
`$color-paper` is the ground you read on and `$color-ink` the marks you read;
the names keep their jobs, not their literal meanings.

- **Three surfaces, each lighter than the last**: the page (`$color-paper`),
  the header and footer bands (`$color-chrome-ground`), a card
  (`$color-surface`). That order must survive any change of value.
- The page carries the leopard print (`LEOPARD.md`), and a card sits light on
  it. The emboss for the dark ground is `_sass/cocktails/_rule.scss`
  (`LETTERING.md`).

#### The colours and their jobs

`_palette.scss` names seven hues after drinks. The `$color-heading-*` variables
at its foot are the authority for which hue a section wears; the job tables in
that file's comments describe earlier arrangements.

| variable | job |
|---|---|
| `$color-electric-absinthe` | the home colour (`$color-accent`): nav and footer chrome, the glass on a card and on the drink page, the rule under the drink page's head and under the universe line, the toggle, the top bar of every drink-page section heading |
| `$color-raucous-reposado` | YOLO? (`$color-heading-yolo`) and the verdict: the ship mark |
| `$color-banging-bellini` | MOOD (`$color-heading-mood`) |
| `$color-charismatic-cosmopolitan` | HASSLE (`$color-heading-hassle`) |
| `$color-wicked-woowoo` | HAS TO HAVE (`$color-heading-include`), the matched ingredient on a card, the bottle suggestion on the drink page, and "this one" under the cursor |
| `$color-ultra-violette` | I KNOW WHAT I WANT (`$color-heading-name`), the matched run of a drink's name, and the lower bar under INGREDIENTS, METHOD and IF YOU LIKED THIS |
| `$color-luminous-lagoon` | NOTES on the drink page: the heading's lower bar and the note's edge and label |

- **Three values per hue.** Bare is a rule or a fill, never small text. `-deep`
  is safe as type. `-wash` is a tint mixed over a card for something matched.
  Text on a wash is ink, never the `-deep`.
- **LEAVE OUT has no hue**, deliberately.
- **A heading's colour is a promise the card keeps.** A section's hue is worn
  by its heading bar (`heading-rule` in `_sass/cocktails/_rule.scss`), by its
  chosen filter chip, and by the thing it lit on a card. Down the index the
  five bars read as one ramp.
- **A chip fills when it matches; a word bands.** A chosen filter chip, a
  matched mood or hassle chip on a card, and a chosen HAS TO HAVE chip are one
  treatment: the section's hue as the fill, `$color-bg` as the letter, the
  faux-bold stroke in the letter's colour (paint only, §13.4.2). A matched
  ingredient on a card (`.drink-card-hit`) is a thick band under the words,
  because it is a name inside a line of other names and a fill there covers
  too much and wraps. `.drink-name-hit` is a band of the same thickness.
- **Hover changes colour and nothing else.** Nothing moves or resizes. A filter
  chip hovers in its own section's hue (`--drink-btn-hover`, set on the section
  wrapper, woowoo as the fallback); a card hovers in woowoo. `:hover` and
  `.is-on` have the same specificity, so the hover rule carries `:not(.is-on)`.
- **Colour that carries meaning alone must survive dichromacy**: the marks on
  a card with no word beside them, not a heading bar under its section's name.
  `python3 scripts/palette_measure.py` measures contrast and separation.
- **A new hue needs an axis**: a kind of fact no existing hue names.

#### The index — the universe line

`.universe` sits above the filters: a label, a small glass, the drink's name on
its tape, its ingredients in round brackets, and `deal again` at the end of the
row. `assets/js/universe.js` deals from the cards the section's
`data-universe-rows` selects, which names the two top ship rungs.
`data-universe-parts` names the card's child classes it copies.

- It is a line, not a card: no box, no ship mark, no mood chips, not full
  width.
- The glass sits in a fixed slot so a redeal never moves the row.
- It closes on an absinthe rule that must stay nearer the line than the
  filters below it.
- Below `$universe-stack-width` the line stacks, and the name is capped to the
  width beside the glass so a long one steps or wraps as a card's does.

#### The index — the filters

Five named questions, in Helen's order:

| section | control | reads |
|---|---|---|
| YOLO? | `no chaos please` / `I'm open to chaos` / `chaos only` | `data-chaos` (`good`, `open`, `chaos`) |
| Mood | chips: what the drink is | `data-moods` |
| Hassle | chips: what it costs | `data-moods` |
| Has to have / Leave out | a search box and a pool of chips each | `data-ingredients`, `data-ing` |
| I know what I want | a search box | `data-name` |

- **`open` applies no filter at all.** The button for "I'll try anything" must
  never narrow.
- **`no chaos please` and `chaos only` each keep one list in taxonomy.yml's
  `chaos`**, read off `meta.ship`: `yes` and `oh gods yes`; `meh` and `who
  knows`. The index stamps each card `good`, `chaos` or
  `middle`, and `middle` (`sure`, `IOU`) shows only under `open`.
- **A card's ship mark is a sixth control with no section** (#1412): a
  `<button>` that sets `state.ship` to its exact `data-ship`, ANDed with
  YOLO?. The count row's legend then reads `ship it? = <card word>` and
  `× clear ship` (`#clear-ship`) appears under it. `?ship=` sets it from a
  drink page's SHIP IT? link; a value no card carries is dropped.
- **Mood and Hassle share one `state.moods` set, and it is ORed**: a drink
  carrying any chosen word from either section survives. The order then ranks
  them: drinks answering both sections first, then more chosen words matched,
  then the shuffle key.
- **Every other filter narrows.** YOLO?, each HAS TO HAVE chip, each LEAVE OUT
  chip and the name search are ANDed with the moods and with each other.
- `mood_groups` in `taxonomy.yml` splits the moods between the two sections
  (`test_every_mood_belongs_to_exactly_one_group`). A mood no cocktail carries
  renders no chip. `test_no_mood_covers_more_than_half_the_collection` keeps a
  mood from becoming meaningless.
- **There is no glass filter and no spirit filter, and there must not be.** A
  mood meaning "contains one of these bottles" is a worse copy of HAS TO HAVE.
- **Filtering reads `data-` attributes, never rendered text.**
- A heading must not be outranked by its own buttons: a control does not dress
  as a label.
- At 600px and under the sections sit a step further apart, and the search
  block keeps one step more than the chip sections: a row of chips ends in its
  own padding, a text box ends in a hairline.

**Order and paging.** The order is shuffled once per page load; filtering
re-ranks against those fixed keys. Pagination is food's control
(`HTF.listView.paginate`, `PAGE_SIZE` in `cocktail-index.js`) and happens after
the reorder. Going back to the index restores the list as it was left, page
included; cocktails restores sort keys where food restores an array.

#### The card

`_cards.scss`. Horizontal: the glass drawn large down a fixed left column
(`$card-text-x`, also the custom property `--card-text-x`, so no rule bakes its
own copy), the words beside it. No panel sits behind the glass.

**Geometry.**

- Above 720px every anchor is fixed: `$card-height`, body anchored top-left,
  foot pinned. The cost is clamping: three lines of ingredients, three rows of
  chips, and the budget of §9.10.1.
- At 720px and under the grid is one column, so the height is the card's own
  content's and `.drink-card-foot` returns to the flow.
- At 400px and under the card un-columns: the glass becomes a band across the
  top.
- **How tall the glass is drawn**: §9.11's ratio, times `display_scale` from
  `glasses.yml` (a per-glass cheat, kept and empty), times
  `--card-glass-scale`, which caps the tall end and steps down at each
  breakpoint. Wide glasses are capped by the column's width first.
  `_dev/card-glasses.html` is the instrument; its defaults must stay the
  shipped values.

**The name.** The card title sits on punched tape (§13.4.1's device at card
size, `.drink-card-tape-word`; `LETTERING.md` has the lettering).

- **A name that does not fit shrinks one step (`$card-name-step`) or wraps. It
  never ellipsises** once `assets/js/card-name-fit.js` has run. With no script
  the ellipsis stays.
- `.drink-card-name--fitted` is a mark, not a third state: it releases the
  tape's clip once the script has run, which is what lets the click overlay out
  of the tape word.
- The script measures the word's content with a `Range`, not `scrollWidth`,
  because the overlay lives inside that box.

**The whole card is the cocktail's link.** There is one anchor per card, the
name's, with a pseudo-element stretched over the card. It is sized in `vmax`
and cut to shape by the card's own `overflow: hidden`, because the anchor's
nearest positioned ancestor is the tape word. The chips and the `+` are lifted
above it, and the ship above the chips because it masks them
(`$card-z-link`, `$card-z-controls`, `$card-z-ship`); the ship declines pointer
events so its corner still opens the cocktail.

**Under the cursor** the field lifts to the woowoo wash, the glass goes woowoo,
and the name goes woowoo wherever the cursor is on the card. It is one mixin,
with `.drink-card:has(:focus-visible)` as its own rule for the keyboard.

**The tagline is never on a card at rest and takes the card when asked.**

- Pointing at a card whose drink has a written tagline hides the ingredient
  line and the mood chips and draws the tagline in their room. The name, glass,
  ship mark and `+` do not move.
- `$card-tagline-top` puts its first baseline on the ingredients' own; it is
  derived by `scripts/card_tagline_baseline.py`.
- The keyboard's way in is the name's link alone. A card-wide
  `:has(:focus-visible)` would hide a chip as it took focus.
- Where there is no hover, the same state is `.is-tagline-shown`, toggled by a
  `?` left of the `+` (`.btn-card-tagline`). `assets/js/card-tagline.js`
  reveals and wires it, `card-line-budget.js` skips a card in that state, and
  the mark's room comes out of the title through `--card-tagline-reserve`.
- `_includes/cocktails/card-tagline.html` emits both the line and the mark, for
  the index card and the related card alike.
- At 720px and under a flipped card keeps its resting height: the ingredient
  line and chips stay in their boxes, invisible, and the tagline lies across
  them.
- A tagline is clamped on a desktop card: keep one under about 105 characters,
  or 65 where the drink's name wraps.

**The mood chips** are bare lowercase words, with a middle dot drawn on the
preceding chip's `::after`, so a chip ending a row keeps its dot and none can
lead a row. They are real `<button>`s that filter the index through one
delegated listener.

- **Their order is packed, not alphabetical.** `card-line-budget.js` measures
  the chips and orders them to show the most inside the row cap, in the fewest
  rows, with the ship's row stopping short of the ship. Alphabetical is the
  tie-break, the order the template emits, and what a card shows with no
  script.
- The script may end a row early with an inline `margin-right` on its last
  chip, reset on every pass, where the chips fit one full row but not the part
  left of the ship.
- Chips matching a filter move to the front of the row in the DOM.

**The goodness mark** is a ship and a word (§9.5), pinned to the foot's corner.

#### The drink page

`_layouts/cocktail.html`. Top to bottom: the head, the controls row,
ingredients, the scaler, method, to serve, notes, `.cocktail-footer` (source,
units, cost), and the related cards.

**The head** (`.cocktail-title-block`).

- The glass sits inside the content column at the head's left edge, in a flat
  column, sized by `--glass-fill` (§9.11).
- The name is on the card's tape, the same four classes, with a real `<h1>`
  inside at `display: contents` and `font-size: 1em`. Without that the
  browser's default `h1` size doubles it.
- At 600px and under the tape bleeds left by the artwork's own left inset
  (`$tape-art-inset-x`). Every tape SVG insets its polygon inside its viewBox
  and `decorations.js` stretches the artwork to the box, so the inset is a
  percentage of the tape's width, not a length. `scripts/tape_insets.py`
  measures it.
- The title is `$title-size`, and `$title-size-phone` at 600px and under
  (`scripts/title_phone_lines.py` counts every title's lines at each). A name
  too long for its line steps then wraps, as on a card.
- `.cocktail-head-words` is a grid of one `minmax(0, 1fr)` column, so the tape
  word's `nowrap` cannot set the head's minimum width and defeat the fit
  script. At 600px and under it is `display: contents` and its children sit on
  `.cocktail-title-block`'s grid.
- **The name is alone on its line. No control goes in the head or the meta.**
- The meta is a `<dl>` of three facts: GLASS, GARNISH, SHIP IT?. The mood chips
  under it are links to the index with `?mood=`, alphabetical, not packed.

**The controls row** sits under the head's rule: the read it / make it toggle
at the left, `_includes/page-actions.html` (the shortlist pill and the
see-shortlist link) at the right, the same include a recipe page carries
(§13.13). The shortlist button has moved several times; read DECISIONS §9.13
before moving it again.

**The section headings.** INGREDIENTS, METHOD, NOTES and IF YOU LIKED THIS wear
a two-bar mark, absinthe over the section's hue (table above). "To serve" is a
plain `.cocktail-section-heading`. IF YOU LIKED THIS is a sentence that wraps,
so it takes the `-last-line` mixin and is in `last-line-rule.js`'s `TARGETS`.

**Two states, one page.** `assets/js/cocktail-make.js` toggles one class,
`is-making`, and `_cocktail.scss` does the rest. Nothing leaves the DOM.
`make it` hides the tagline, the chips, SHIP IT?, the bottle suggestions, each
ingredient's note, the notes section and the related cards, and enlarges the
amounts and the method. A method step's note (a `{step, note}` pair) stays
visible: it is how to do the step. Print is the full read page, forced by
`_print.scss`.

**The amount column is sized by the cocktail.** `.cocktail-ingredients` is
`grid-template-columns: max-content 1fr` and each row reaches those tracks
through `subgrid`, so the column is exactly as wide as this cocktail's longest
amount, and the sub-lines sit in the second track. Nothing counts characters.

#### The scaler

One box, the word "drinks" and two step buttons under the ingredients list,
hidden until `assets/js/cocktail-scale.js` reveals it. The word is final.

- **Whole recipes only**: an integer multiple, never below 1. Counts multiply
  and re-pluralise; an amount with no measure (`(top)`, `(rinse)`, `to taste`)
  passes through.
- A value the scaler cannot apply is refused silently: the box returns to the
  last multiple that worked.
- **`serves:` is not read.** "How many does this make" and "how much am I
  making" are different questions.
- **Bitters do not scale linearly.** The layout marks an amount in dashes or
  drops `data-dashes` and prints a hidden `*` beside it. Above ×1 the script
  sets `data-struck`, which strikes the amount through and shows the star. The
  note under the scaler (`.cocktail-scale-batch`) is that caveat and nothing
  else, and is rendered only for a drink with such an amount.
- The units line is per serving and must never move with the scaler.

**One amount parser in the browser, one at build.**

- Browser: `shoppingList.parseAmount`, through `shopping-list.js`, then
  `scale.js`, then `cocktail-scale.js`. Each reads the one before at parse
  time, so the wrong order leaves the control hidden with no error.
  `test_the_scaler_scripts_load_in_dependency_order` guards it.
- Build: `HelenTriages::Amount` in `_plugins/amount.rb`, shared by the costs,
  units and card plugins. Its grammar is narrower on purpose: cocktail amounts
  only, the unit as written.
- `tests/fixtures/amounts.json` holds every distinct amount a published drink
  writes, with what each parser reads. `tests/test_amount_parser.py` runs the
  Ruby side through `scripts/parse_amounts.rb` with no Jekyll build;
  `tests/js/shopping-list.test.js` reads the same rows. A new amount shape in a
  published drink fails until it has a row.

#### "If you liked this, how about…"

Four related cocktails after the footer.

- **The ranking is more shared moods, then more shared ingredient generics,
  then title.** No `meta.ship` weighting. Only a candidate sharing a mood or a
  generic is offered.
- **The first three cards are the top three; the fourth is the candidate a
  quarter of the way down the ranking** (never above fourth), so a cluster of
  alike drinks, the tiki ones above all, cannot fill the row with each other.
- It is Liquid in the layout, not a plugin. Liquid cannot sort by a computed
  number, so each candidate becomes a `mood~generics~title~url` string, each
  count written as `99 - n`, sorted as text.
- `test_the_related_picks_are_the_scripts_picks_in_the_scripts_order` holds
  every built page, food and drink, to its script's picks in its script's
  order.
- **The collection is the published set.** `publish_gate.rb` removes a
  held-back cocktail from `site.cocktail_recipes` before the layout runs, so no
  gate check is needed here. Drafts are a different collection and are never
  concatenated in.
- `python3 scripts/related_drinks.py [slug]` is the same scoring in Python over
  the same corpus, a second implementation to check the template against.
  **Re-run it after a promotion batch or any vocabulary edit that moves
  moods.** Its `HOW_MANY` and the rendered-pages test move with the layout's
  `limit: 4`.
- `test_every_published_drink_page_offers_four_other_published_drinks` reads
  the production build and counts the name links only, since a card carries
  chip links too.

**The four are index cards, not a variant.** They are plain `.drink-card`,
the same classes in the same order, and every rule is `_cards.scss`'s. Two
differences, neither geometry: the chips are links to the filtered index, and
the index's `data-*` search attributes are absent, which is why the markup is
written in the layout and only the stylesheet is shared. **Do not add a card
modifier for this page** (DECISIONS §9.13). Four is the count because the row
wraps two and two.

The section is hidden in `make it` and in print. The heading text is final.
Food's row of the same name is its own markup and scoring in
`_layouts/recipe.html`, with `scripts/related_recipes.py` as its mirror: three
recipes, ranked by the same star ingredient, then more shared mood tags, then
more shared other tags plus main ingredients, then shared non-larder
ingredients, larder staples, and title.

Above it, a food recipe page has **"Goes with…"** (#1104): every published
recipe it links to, or that links to it, outside the ingredient lines
(tagline, method, notes), so a dish shows its sides and a side its dishes.
When either recipe links the other in an ingredient line, that is a
component, not a pairing, and the pair never shows: five-spice powder lists
nothing it is used in, and the chai tea and its spice powder skip each other
although the powder's tagline links the tea. Nothing is stored: the
layout searches the recipes for `](../<slug>/)`, so a promoted draft's links
appear by themselves, and a pairing no recipe states needs another source
when it comes. The rows are `_includes/food/recipe-row.html`, the related row's own markup;
`test_every_link_between_recipes_shows_on_the_page_it_points_at` holds every
link to its row.

### 9.14 `heights_mm` sizes the canvas

An icon renders at the height `heights_mm` gives its **viewBox**. A drawing
with empty margin therefore renders smaller than one without, and Inkscape
keeps the previous canvas silently when a glass is made by editing another.

`scripts/normalise_glass_icons.py` fits every icon's viewBox to its own artwork
as its last step (`fit_viewbox` in `scripts/svgrender.py`):

- it measures all the ink, with the whole ancestor transform stack composed;
- it grows the canvas as well as shrinking it;
- it leaves a margin in user units, not a percentage, because
  `non-scaling-stroke` needs more units the smaller the icon renders.

Three tests face three ways: `test_no_glass_artwork_has_a_slack_viewbox`
(canvas bigger than drawing), `test_no_glass_artwork_is_drawn_outside_its_viewbox`
(the reverse) and `test_the_icon_parser_applies_nested_transforms`.

**Trap: a script whose output is tracked and whose input is not.** The
normaliser's inbox is gitignored and empty in a fresh worktree, and its first
destructive step empties the published set. It checks for usable input before
deleting anything (`refuse_if_no_input`, which
`scripts/build_glass_candidates.py` shares). Any new script of that shape needs
the same check before it deletes.

### 9.15 One source per glass; git history is the record

`_design_sources/cocktails/glasses/` holds exactly one drawing per published
icon, named `glass-<published name>.svg`. Superseded drawings are in git
history, not on disk:

```
git log --diff-filter=D -- _design_sources/
git show <sha>^:<path>
```

**Publishing a redraw.** Helen saves a new attempt beside the old one as `-2`,
never over it. Publish it by deleting the old file and renaming the new one to
the plain name, in one commit. Do not add a `SKIP` or `RENAME` entry: those
registries stay in the normaliser, hold no glasses, and existed only to choose
between versions.

After any change here:

```
python3 scripts/check_glass_regen.py
python3 scripts/build_glass_candidates.py
```

The first normalises every source in memory and diffs against the published
set without deleting anything. The second rebuilds the drawer on
`/dev/glasses/` (§9.16).

### 9.16 The candidate drawer — `/dev/glasses/` sections 5 and 6

Every drawing in `_design_sources/cocktails/glasses/`, normalised into
`_includes/icons/glass-candidates/` and listed in
`_data/dev_glass_candidates.yml`. `scripts/build_glass_candidates.py` writes
both in one run so they cannot drift.

The drawer is deliberately not in `_includes/icons/glasses/`, which is the
published set and is asserted to match `all_icons` both ways, and not in
`_data/cocktails/`, which is the site's vocabulary.

## 10. Validation — how the suite and the deploy are wired

Run the suites rather than reading about them: `python3 scripts/verify.py`
(§1), or `pytest` and `node --test` singly. `ls tests/ tests/js/` lists the
modules and each module's docstring says what it covers. The rule for a red
`main` is `CLAUDE.md`'s; this section is the machinery behind it.

#### How the Python suite is organised

- **Three markers** in `pytest.ini`: `pytest -m food`, `-m cocktails`,
  `-m shared`. They are for signal, not speed: a red food half hides a real
  cocktails regression. `test_every_test_module_declares_a_suite_marker`
  fails a module without one, because every `-m` run silently deselects it.
- **`pytest.ini` runs `--tb=line`**, so the first line of an assert message is
  all a failure shows. Put the diagnosis there.
- **Two session builds, `site` (local config) and `prod_site` (production
  alone), live in `tests/conftest.py`.** A module that needs a built page asks
  for one of them. A session fixture imported into a second module is a second
  definition that builds again, so never define another.
- **A test that needs throwaway pages adds its files to the one shared fixture
  build**: `_in_the_fixture_build({...})` at import in
  `tests/test_rendered_pages.py`, then ask for `fixture_site`. It is a
  production build of a copy of the tree plus every test's `zzz-` files, so
  assert only on your own pages by name. A test about the whole build calls
  `built_with_fixtures` itself and pays for a build.
- **The cocktail corpus is `_cocktail_recipes/` plus `_cocktail_drafts/`,
  through `_load()` in `tests/test_cocktails.py`, the only door**
  (`test_every_drink_reading_test_goes_through_the_loader`). A promoted
  cocktail is therefore checked everywhere, CI included. The data files and
  collections are parsed once per run (`_parsed`, `_scan`): copy before
  changing anything a loader returned.
- **The staleness half of a guard is unanswerable on a partial corpus**: a
  cocktail merely absent looks exactly like one fixed. A check that hangs on a
  shrink-only registry, or a mood's share of the book, calls
  `_require_whole_collection` and skips with a reason; `WHOLE_COLLECTION_ONLY`
  is the registry and `test_whole_collection_only_says_what_it_does` keeps it
  true both ways.
- **Do not start a Python per test for a script that imports from `tests/`.**
  The import alone reads every recipe, draft and drink.
  `tests/test_tidy_drafts.py` calls `tidy_drafts.main(argv)` in-process.

#### What CI runs, and what it lacks

In `.github/workflows/build-and-deploy.yml`, `test` runs on every pull request
and every push to `main`. `build` and `deploy` carry
`if: github.event_name != 'pull_request'`, so a pull request shows `test`
passing and the other two **skipped**, which is the expected shape. `deploy`
declares `needs: [test, build]`: a red suite builds an artifact that is never
deployed. `test` is a required status check on `main`, so a red pull request
cannot merge. `test_the_deploy_workflow_runs_the_tests_and_gates_on_them`
holds the workflow to this.

- **`fetch-depth: 0` on the `test` checkout is load-bearing.** In a shallow
  clone `git log -- <file>` reports one commit for every file, and §4.0's
  provenance test would pass over nothing.
- **The JS suite is bare `node --test` from the repo root**; it finds every
  `*.test.js` itself. The workflow passes `tests/js/*.test.js`, which the
  runner's shell expands and the hook refuses in a session. Never pass the
  directory: node treats it as one module and reports "tests 1, fail 1".
- **CI has no private drafts.** `SKIPS_WITHOUT_DRAFTS` and `PARTIAL_IN_CI` in
  `tests/test_suite_hygiene.py` record what each draft-reading test does about
  that, and `test_every_draft_reading_test_says_what_it_does_without_drafts`
  fails one in neither set. Per-draft parametrised tests need no entry: with
  no drafts they are never created, which is why a green run without the
  clones says nothing about drafts.
- **CI has no browser.** `tests/test_browser_smoke.py` runs the production
  build in headless Chromium: both indexes, a recipe and a drink, at 360 and
  1280. It skips on whether Chromium **launches**, never on whether playwright
  imports, because CI installs the binding and no browser. The `chromium`
  fixture is the one probe
  (`test_every_browser_test_goes_through_the_launch_probe`), and `conftest.py`
  prints "Not evidence about a real browser" after any run where it skipped.
  `HT_REQUIRE_BROWSER=1` turns the skip into a failure; the workflow should
  set it in the same edit that installs Chromium.

**Before pushing anything CI will run, simulate it**: run the full suite
without the two drafts clones.

#### When `main` is not green

`sh scripts/main-ci-status.sh` reads one public endpoint with no credential.
It exits 0 when the newest push run succeeded, 1 when it failed, was cancelled
or has not finished, and 2 when GitHub returned nothing it could judge, which
is not a green result.

- **It judges pushes to this repository only.** A pull request from a fork
  whose branch is called `main` matches the same endpoint; it is listed,
  marked "a pull request, not a deploy", and kept out of the verdict.
- **A waiting deploy can be cancelled, and `main` then reads `cancelled`, not
  red.** Deploys share the concurrency group `pages`, which keeps one waiting
  run, so a deploy queued behind another is dropped when a newer push arrives.
  That is benign: the newer run carries the older merge, or Helen re-runs it
  in the Actions tab. Each pull request has its own group, `pr-<number>`, and
  never touches the deploy queue.
- **An invalid workflow file deadlocks everything.** GitHub runs no jobs,
  `test` never reports, and nothing can merge. The way out is a pull request
  that repairs the workflow: a `pull_request` run reads the file from the PR's
  own branch, so the corrected copy runs and reports.
- **A Dependabot PR opened while CI was broken does not re-run on its own, and
  closing and reopening it does nothing.** Comment `@dependabot rebase`.

#### A public test can need private data

Nothing makes a public merge and a private one arrive together. The tell is
both directions failing at once (values "not declared" and a vocabulary
"proposing changes to strings no drink says"): two files at different commits,
not a data fault.

Each private repo carries a `SCHEMA_VERSION` file; `tests/drafts_schema.py`
declares the version this checkout needs, with a changelog;
`test_the_cocktail_drafts_clone_is_in_step` and
`test_the_food_drafts_clone_is_in_step` compare them and skip when the clone
is absent. **Bump both sides in the paired commits.** It is a hand-maintained
integer that diagnoses and does not prevent: the failure's first line says
which side is behind. When a public PR depends on a private branch, name the
branch in the PR description (`PUBLISHING_A_COCKTAIL.md`).

**The drafts half merges first.** Public data may name a drafts slug
(`mood_include` in `taxonomy.yml`); drafts never name public data. With the
public half merged alone,
`test_every_mood_correction_is_reachable_and_needed` is red on any machine
holding both clones on `main`, and CI, which has no drafts, cannot see it.
The one inversion: a drafts PR that names a new public generic merges second.

### 10.1 Standing rules

- **Auditing coverage is three steps**: grep the tests for `issue #NNN`, diff
  against the closed issues from the API, and check each gap against the data
  before calling it a gap.
- **`test_oven_temperature_says_fan` and `test_milk_specifies_type` are not
  fixable blind.** Which figure is the fan one, and which milk a recipe used,
  are only in the source. A red in either is a real regression.
- **`test_ingredient_notes_are_lowercase_fragments` flags and never fixes.**
  Helen reads the violations herself, for tone of voice; whether a capital
  belongs in `proper_nouns` is her call.
- **There is one draft marker, `QQ`.** Never add another.
- **Which checks read `_food_drafts/`: ask the registries**, not this file
  (`tests/test_suite_hygiene.py`; `NOT_FOR_DRAFTS` in `tests/test_drafts.py`
  for the rules deliberately not applied to drafts). The one that fires in
  practice is `test_no_main_ingredient_spelling_collisions`. Before reporting
  a new failure, look for a new draft:
  `find _food_drafts -name '*.md' -mmin -120`.

### 10.2 The stub-DOM harness — `tests/js/dom-stub.js`, `tests/js/index-harness.js`

The fault it exists to catch: a name read off the wrong object takes out the
whole tail of `cocktail-index.js` while every pure test stays green, because
each asks a pure module a question and the fault is in the wiring.

**The canary is the `pagehide` listener**, the last statement in the file.
**Nothing is mocked that the page does not mock**: the real scripts run in the
real order through `vm.runInContext`, and only the DOM and `localStorage` are
stand-ins. `cocktail-index-startup.test.js` compares the harness's script list
with the `<script src>` tags in `cocktails/index.html`, and checks that every
id the script reaches for exists in the fixture. No jsdom, no `package.json`,
no `node_modules`: `node:test` and `node:assert` alone.

A script with no startup test (`decorations.js`) gets one by copying the
harness. Read the script order from the built `_site/`, not the layouts: a
page layout's scripts land inside `{{ content }}`.

**Food has its own, `food-index-startup.test.js`**, on the same `dom-stub.js`
with its own fixture. The whole of `filters.js` is inside one
`DOMContentLoaded` handler, so the test must `doc.dispatch('DOMContentLoaded')`
after loading the scripts or every assertion is about an untouched page; the
canary is `.recipe-list` becoming `visibility: visible`, near the end of that
handler. The stub stores `innerHTML` as a string and does not parse it, so a
control the page writes that way cannot be found with `querySelector`:
dispatch at the delegating parent with a stand-in `target`.

`tests/js/stub-dom.js` is a different, smaller file: a page of meta tags for
running `assets.js`, which attaches to `window.HTF` and cannot be `require`d.

---

## 11. Working practices

The rules for an agent — git, pull requests, issues, the token, permissions,
the Bash tool, proofreading, working with Helen — are `CLAUDE.md`'s and are
not repeated here. This section says how the machinery behind them works, and
holds the practices `CLAUDE.md` does not state.

**The procedure documents.** `model_instructions/PIPELINE.md` is the map of a
recipe's whole journey; read it first. Each step has its own authority:
`.claude/commands/ingest.md` for material coming in (§11.0.3),
`ingest-inbox.md` when it arrived as a GitHub issue (§11.0.4),
`tidy-drafts.md` for the mechanical half of a drafts pass (§11.0.2), and
`model_instructions/PUBLISHING_A_COCKTAIL.md` for a cocktail going out. The
last is not a slash command, so it is the one a session is likeliest not to
know exists: read it before touching a `4-promote/` or `5-final-proofread/`
folder.

**The hooks.** `.claude/settings.json` wires every file in `.claude/hooks/`.
Each runs as `python3 <file>`, so none needs an execute bit, and each allows
whatever it cannot read or scan, so a guard never breaks a tool call. A rule
is not enforced merely because a document states it firmly; `CLAUDE.md` names
the hook wherever there is one.

| Hook | Refuses | Lets through |
|---|---|---|
| `guard-main-branch.py` | `git commit`, `git merge` while the targeted repo is on `main` or `master` (§11.-1) | everything else on `main` |
| `guard-destructive-git.py` | a discard over a dirty tree; a stash drop while anything is stashed (§11.0) | the same on a clean tree; `git stash`, `stash pop`, `restore --staged` |
| `guard-unanalyzable-bash.py` | the shapes `CLAUDE.md` lists under the Bash tool | `?`, an escaped parenthesis, `${...}`, a bare `$VAR`, a lone `NAME=value` |
| `guard-inline-script.py` | a program given to `python -c`, or `ruby`, `node`, `perl` `-e`, at any length | a file argument; `git -c`, `sh -c`, `bash -c` |
| `guard-sed.py`, `guard-awk.py` | a command word whose last path component is `sed`, `awk`, `gawk`, `mawk` or `nawk` | the word in quotes; a token that contains it (`guard-sed.py`) |
| `guard-token-expansion.py` | a secret probed, printed, put in a URL or typed out | a secret consumed, not printed |
| `session-ground-truth.py` | nothing: it reports | — |

- **The two git guards** carry an `if: Bash(git *)` filter, so they see only a
  command that begins with `git`. The rest run on every Bash call.
- **`guard-unanalyzable-bash.py`** blanks quoted spans, then looks for
  operators. `&&`, `||`, `;`, `|`, `*` and parentheses are inert in either
  kind of quote; `$(`, a backtick and `$[` are inert only in single quotes,
  because the shell expands them in double ones. Redirections are removed
  first, so `2>&1` is not chaining. The quoted `[`, `]`, `|` shape applies
  only to a command beginning `sh scripts/`.
- **`guard-token-expansion.py`** counts as a secret any variable named
  `TOKEN`, `SECRET`, `PASSWORD` or `PASSWD`, alone or after a `_`. It refuses
  a default expansion of one (`${TOK:-x}`); any mention in an `echo` or
  `printf`; one in a URL's userinfo; a literal GitHub-token-shaped string; and
  a `gh` call, bare or through a wrapper, that mentions `env` or `$ENV`. For a
  plain `<interpreter> <file>` command it also opens the file and applies the
  URL and literal checks to it.
- **`session-ground-truth.py`** is a `SessionStart` hook. It reports the
  checkout's path, the branch, the uncommitted changes already there, the
  position against `origin/main` as last fetched, and whether the two drafts
  clones are present. It makes no network call. **Its first line names the
  checkout: if that is not the worktree you are in, trust nothing else in the
  report.** Its silence is not a guard having passed.
`tests/test_git_guards.py`, `tests/test_text_tool_guards.py` and
`tests/test_agent_wrappers.py` break each guard and wrapper on purpose.

**Branch names**: `<type>/<what-its-about>`, lowercase, hyphens, one concern.
**Commit subjects**: `(type) lowercase description`, no full stop, saying what
the change does; take the type words in use from `git log origin/main
--format=%s`. ASCII `--` in a commit message, not an em dash. **Commit
bodies**: why, not what; how you know it works; whether a fix predates the
branch; what you ruled out; the guards added, and that you broke them to
prove they bite. Before reporting an issue as done:
`git log origin/main --grep='#N'`.

**The two servers are Helen's to start, and a session never offers.** Say
which URL needs looking at and stop there (§1).

**One agent at a time in a working tree, and never one that switches
branches.** Delegate the reading and the scanning; keep the branching in the
foreground. More than one agent means a worktree each (§11.0.1).

**Helen** writes no code by choice and has strong systems judgement; write
explanations that assume both. Offer aesthetic opinions, because she asks for
them. Disagree with her when you think she is wrong, and say plainly when you
were wrong yourself. Three things no file teaches:

- **She reports symptoms, not diagnoses, and reports them accurately.** Treat
  the observation as exact and find the cause; do not stop at the thing she
  described.
- **An aesthetic objection usually has a structural reason under it.** Look
  for the reason before complying; it is generally the better fix.
- **She is the only user, and her eye finds rendering faults no test can
  see.** When you cannot see something yourself, say so and hand it over
  (§13.11). Then write the test her eye just stood in for.

**The test suite is self-sufficient by design; GitHub issues are provenance,
never a dependency.** A test's name states the rule
(`test_egg_size_is_stated`) and its assert message names the fix: the
offending value, the allowed list, why it is not safe to fix blind. A
docstring that only makes sense after reading the issue it cites is a gap to
close.

### 11.-1 The branch workflow and the main-branch hook

The four-step workflow is `CLAUDE.md`'s. What sits behind it:

**`guard-main-branch.py`** strips quoted spans and heredoc bodies, so a commit
message may discuss the commands, then looks for `git commit` or `git merge`.
It asks git for the current branch in the directory it runs in, moved by any
`cd` and then any `git -C` in the command. A detached HEAD, or a directory
that is not a repository, is allowed.

`guard-unanalyzable-bash.py` refuses a leading `cd` and `git -C`, so no
command reaches a nested drafts repo in a form this hook reads. Git there goes
through **`scripts/git-drafts.sh <dir> <verb>`**, which the hook does not see,
so the wrapper refuses a commit on that repo's `main` itself. It accepts a
list, not a pattern (its header comment is the list) and refuses push, fetch,
reset, restore, stash and merge.

**`scripts/git-fetch-main.sh`** fetches the public repository into
`refs/remotes/origin/main` and nothing else, with no credential, and prints
the commit it got. **`scripts/git-push-agent.sh`** refuses a destination of
`main` on the public repository, a refspec without a colon, one starting `-`,
and a `dir` outside the checkout; `:<branch>` deletes a remote branch.

**It pushes to a URL, not to the `origin` remote, so `origin/<branch>` never
moves and cannot answer "is this pushed?"** The tracking ref reads as commits
behind for the whole session; trusted the other way it licenses rewriting a
pushed commit. Answer by hash against what this session sent, or with a
`gh-read.sh` call on the branch or its pull request.
`scripts/git-fetch-agent.sh` does update the ref, and detaches HEAD.

**`scripts/gh-write.sh`** makes the three routine REST writes:

    sh scripts/gh-write.sh pr-create helen-triages data/some-branch "(data) the title" tmp/pr-body.md
    sh scripts/gh-write.sh pr-body   helen-triages 1081 tmp/pr-body.md
    sh scripts/gh-write.sh comment   helen-triages 1064 tmp/comment.md

The body is a plain file under `tmp/`; the repo is one of the three, named
bare; the base is always `main`; `comment` takes an issue or a PR number. It
prints the new PR's number, URL and author. It cannot merge, approve, close or
change a title, which is why it can be allow-listed where
`sh scripts/gh-agent.sh api -X ...` never can. A PR's title is Helen's to
change: `gh pr edit` goes through GraphQL, which wants `read:org`, and that is
not a scope to ask for.

**`scripts/github-public-status.sh <url>`** prints the logged-out HTTP status
of a page under `DeckOfPandas` or an agent account: 200 is visible; 404 on
something the API can see is hidden. A hidden account's issues also drop out
of issue listings, even for that account, while a GET by number still returns
them; a number missing from both the issue and the pull-request listings is a
hidden issue. Pace any sweep by number and stop at the first 403: the rate
limit is shared with every other session.

**`scripts/check-link.sh <url>`** prints one line, the HTTP status after
redirects and the final address: `200 https://where/it/ended`. It takes one
`https://` URL, or one `http://localhost:<port>/` URL for a page on the dev
server, and nothing else: no option reaches curl, the body goes to
`/dev/null`, and no credential is sent. An https check follows redirects over
https only, with a browser's user agent because several recipe sources refuse
curl's; a localhost check follows none. Use it for a `source_url` or a served
page, never a bare `curl`, which prompts.

### 11.0 The destructive-git hook

`guard-destructive-git.py` strips quoted spans and heredoc bodies, then looks
for `git checkout -- <paths>`, `git checkout .`, `git checkout <arg>` where
the argument names a file that exists (no pattern can tell a path from a
branch, so it asks the filesystem), `git reset --hard`, `git clean -f`, and
`git restore` other than `--staged` alone.

It then runs `git status --porcelain` in the repository the command targets,
found as in §11.-1 (a `cd` and a `git -C` are both read), and denies only if
that tree is dirty, naming what would be lost. Untracked files count as dirty.

**`git stash drop` and `git stash clear` have their own gate**: denied
whenever `git stash list` is non-empty, whatever the tree looks like.

Known limit: `bash -c "git reset --hard"` passes, because the command sits in
a quoted span. So does one run from inside a script, which the hook never
reads. Neither is permission: a proof that needs a commit undone (the one
that follows a baseline move, §4.0) uses a throwaway branch, checked out,
committed on, left and deleted.

If it blocks you, read the refusal. The commonest legitimate case is undoing
an edit you just made, and the answer is to re-edit the file.

### 11.0.0 Larger pull requests

`CLAUDE.md` states the rule: one pull request per sitting, topics kept apart
as commits. Every merge to `main` is a deploy (§10).

### 11.0.1 More than one agent — a worktree each

    git worktree add .claude/worktrees/<name> -b <branch> origin/main

A fresh worktree has no drafts clones and no vendored runtimes (§1, §9.1);
`CLAUDE.md` has the clone commands. If a promotion batch is open, do not open
a second writable copy of the cocktail drafts (`PUBLISHING_A_COCKTAIL.md`,
"The one working copy").

All worktrees share one `.git/config` and one stash list, so a stash made in
one is poppable from every other. Other worktrees are read-only to you and
none is ever removed; both rules are `CLAUDE.md`'s.

**The harness removes a helper's worktree that holds no tracked change when
the helper finishes, and its `tmp/` goes with it.** Work done only inside a
gitignored drafts clone counts as no change. Such a helper pushes after every
commit, and a proof script's text goes in the report that cites it.

### 11.0.2 `/tidy-drafts`

`.claude/commands/tidy-drafts.md` is the procedure and
`scripts/tidy_drafts.py` the engine, over both drafts collections. It fixes
formatting and never a judgement, never touches a `QQ` line, and imports every
rule from the test suite. On a cocktail it edits only Helen's own prose fields
and reports the rest; `--only order` alone reaches further, moving whole
top-level blocks into page order (§9.3) without editing a line.
`tests/test_tidy_drafts.py` asserts the whole output byte for byte.

Outside the mechanical pass, an agent may correct or delete a note that a
later ruling of Helen's has made false, naming the ruling in the commit
(`PIPELINE.md` §4). A note she has not ruled on, or a `QQ`, is still hers.

### 11.0.3 `/ingest`

`.claude/commands/ingest.md` is the procedure, including the finishing pass
for a file from a web chat (`CLAUDE_WEB_INGEST.md` is the web side). Its
engines run in a fixed order and each refuses the next one's job:
`scripts/resolve_pours.py` writes what `bottles.yml`, the vocabulary and
`source_wordings.yml` settle by exact match;
`scripts/derive_cocktail_moods.py` writes what the amounts and generics imply;
`scripts/ingest_preflight.py` reports what is left as one list for Helen,
grouped by decision. `scripts/derive_main_ingredients.py` is food's: by
default it reorders a list and changes no membership, and it never writes to
`_food_recipes/` (DECISIONS §6).

**A whole method of verbatim book prose in one `Write` can be refused by the
API's content filter.** Write the source wording one step-pair per `Edit`.

### 11.0.4 `/ingest-inbox`

`.claude/commands/ingest-inbox.md` is the procedure,
`scripts/ingest_inbox.py` the engine, and `INGEST_INBOX_DESIGN.md` §6 the
envelope: an issue labelled `ingest` on a private drafts repo, pasted by Helen
herself. The parser rejects and never repairs. A matching fingerprint is
reported and not written; a matching title with a different fingerprint is
written under its own slug. The version marker is checked against
`SUPPORTED_VERSIONS`. An absent drafts repo is a refusal, not a clean inbox.

### 11.1 A file with a colon in its name crashes the whole build

WSL writes `<name>:Zone.Identifier` beside anything dragged in from Windows.
`jekyll-sitemap` dies in `addressable` with `Invalid scheme format` and never
names the file. `_config.yml` excludes `"*Zone.Identifier"`; for any other
colon, `find . -name '*:*'`.

### 11.2 Do not trust this document over the code

The rule is `CLAUDE.md`'s: verify what you are about to act on, the code wins,
and the document gets fixed.

**An open issue is a document too, and it rots faster.** Nothing re-reads an
issue body, and its age is the only warning. Before acting on an issue older
than a day, or repeating what it says, run its numbers against the data. A
test stops the data regressing; it does nothing about a session re-raising a
settled question in words.

### 11.2.1 Do not ship a layout at a size you cannot look at

`scripts/browser/` (§1) answers most of this: `shoot.sh` screenshots a page at
360, 390 and 1280 and names every element past the viewport. Look before
reasoning.

What it cannot produce is a real device or a state only Helen's hand reaches.
If a change shows only there, building a way for her to see it is part of the
work: a dev page of iframes at fixed CSS widths (360, 390, 320) puts narrow
candidates side by side on any screen, including an iPad, where a 400px
breakpoint never fires. Then delete the losers and the switch.

### 11.3 CSS naming — flat noun for the thing, `--modifier` for its state

Two registers, both deliberate. Flat hyphenation names the thing
(`recipe-meta`, `btn-ingredient`). A trailing `--modifier` flags a state or
variant, with the base class always present (`badge badge--matched`); this is
why `test_every_icon_partial_class_has_a_styled_base` checks only the part
before `--`. BEM element syntax (`__content`) is not used. Do not attempt a
big-bang rename; apply it as files are touched.

---

## 12. Traps you will fall into

A trap and its way out, grouped by subject. Where a test or hook catches one,
the entry is one line naming it. The stories are in DECISIONS §12.

**Rules and documents**

**You will flag `QQ` as an error.** It is Helen's deliberate placeholder
(`CLAUDE.md`). `test_no_qq_placeholder` keeps it off a published page; in a
draft it is not a finding.

**You will write down a rule instead of following it**, in the same file, in
the same minute: a comment saying a key must be set by hand, and the line
never added. Writing an explanation of a constraint feels like satisfying it.
Do the thing first, then write the comment; and ask what would fail if the
constraint were violated, because that question is a test.

**A cross-reference to another file's behaviour is a claim nothing
re-checks.** A comment saying what another template "does" can be false from
the day it is written. `git log -S` over the file that would implement the
behaviour is the check.

**A parser will read your documentation as code.** Liquid tokenises tags
inside `{% comment %}`, so name a tag there rather than writing it out. Before
quoting syntax in a comment, ask whether what reads the file parses comments
or skips them.

**You will suggest tooling that has already been rejected** (`jekyll-seo-tag`,
Stylelint, a bundler, a CSS framework, schema.org/Recipe). Argue against the
recorded reason, under "Rejected tooling" in DECISIONS §12.

**A `Fixes owner/repo#N` trailer in a private repo's commit closes nothing.**
`CLAUDE.md` has what to do instead.

**Measuring and reporting**

**You will measure the wrong layer and report the answer as a fact.** A
measurement is evidence only about the layer it ran through, and the page is
the only layer that settles anything. Before reporting that a behaviour does
not exist, ask which file would implement it. If the answer is DOM wiring,
§10.2's harness or a screenshot is the check, not a module call.

**The data is cleaner than you think.** If a scan finds "lots of problems",
suspect your findings first: a blank `star_ingredient` is correct for a plain
sponge. And Helen adds drafts while you work, so a failure that appears
between two runs is more likely a new draft. Check mtimes (§10.1).

**You will read the patch and think you have checked the output.** For
anything that rewrites structured text, load the result and diff the parsed
form, and run it on a copy first.

**You will rewrite YAML you were only asked to edit.** Parse to check; edit as
text. A `yaml.dump()` round trip loses comments, key order, quoting and the
`[""]` that `method_short` depends on.

**A "generator" may have stopped generating, and its own docstring may not
know.** Before running anything that writes a tracked file, run it once and
diff, or copy the file to `tmp/` first. When a generator's output becomes
hand-edited, fix the comment in the generator.

**A `git fetch` is only good for the moment you ran it.** Fetch again
immediately before reporting, and say what it showed;
`session-ground-truth.py` reports only "as last fetched". `git log --branches
--not --remotes --oneline` lists work on any branch that no tracking ref
holds, but it over-reports here: a push through the wrapper moves no tracking
ref (§11.-1), so a pushed branch still shows.

**A branch that has sat for days is judged by its diff against today's
`main`, not its commit message.** The message was true the day it was
written; `git diff origin/main..<branch>` shows the lines the branch would
now delete because it predates them, which `git show <branch>` does not.

**A capability measured on the most permissive member of a set proves nothing
about the set.** What works on the public repo can fail on both private ones.
Probe the narrowest case, or all three.

**"Lost work" after a disconnect may be sitting in a worktree you have not
looked in.** `git branch -a -v` and `git worktree list` before reporting
anything as lost.

**You will see a force-push rejection and assume something is badly wrong.**
Fetch, then diff each "diverged" commit against its counterpart with the same
message. If the diffs are empty it is a rebase artefact, and the correct side
is pushed over the other.

**A photo "batch" is not one source, and an ordinal count of photos is not a
filename.** Open every photo. A capture that ends mid-recipe looks exactly
like a complete one: transcribe what is in frame and say where it ended.

**When the person who can see it says the same thing twice, stop defending the
measurement.** Every number about the box can be right while none is about
what is painted in it.

**Guards and tests**

**You will write a test that cannot fail and not notice.** The most dangerous
trap, because the symptom is green: a stale path, a non-recursive glob, a
shape the regex never considered, an early return. When you add a guard, break
the thing it guards and watch it fail, reading the output and not the exit
status. Never `return` because a scan came back empty: assert it is non-empty.
`test_no_whole_corpus_test_can_return_early` catches the bare return, but only
in a test not parametrised per recipe or draft.

**A proof by mutation can lie in three ways.** Revert the whole change, not
one branch of it: a half-mutation that passes says nothing about the test.
Give each run of an in-place mutation its own `PYTHONPYCACHEPREFIX` under
`tmp/`, because a same-length edit restored within the second leaves a
bytecode cache that still matches and the next run imports the mutated
module. And report the fault the proof showed, not the one you reasoned your
way to.

**A helper defined twice in one test module silently replaces the first**,
and the failures that follow name the data, not the code. Before defining a
helper in `tests/test_cocktails.py`, grep for `^def <name>`; when a
data-shaped failure appears the moment you add code, suspect the code.

**A scan of compiled CSS must print what it matched.** `@extend` puts the
extending class last in the compound: `&.is-on` inside a placeholder compiles
to `.is-on.btn-chaos`, so a pattern expecting the button class first misses
the rule that matters while matching others.

**A source-scanning guard will be fooled by the prose explaining it.** The
vocabulary of a rule is densest in the comment about it. Strip comments and
quoted spans before counting, match a call shape, or parse the AST. Strip
strings only when the guard's failure direction allows it: a key is read
through a string literal, so `test_invisible_keys_are_really_invisible` keeps
them.

**You will scope a guard by the value it polices, and it will not see the
rival value.** A guard that filters on the canonical spelling sees only
cocktails that are already right. Anchor on the field and ask what it holds.

**You will assert a registry is non-empty when emptying it is the goal.** A
ratchet list (`GLASSLESS_ON_2026_08_27`) empties and must stay empty, so
assert emptiness. A worklist (`proposals`) empties and refills, so assert only
that the key exists.

**A declared exception silences every check downstream of it**, not only the
one it was declared against: a suggestion that resolves to no bottle also
resolves to no category, so the cross-category check skips it too. When you
retire an exemption, expect something unrelated to go red; that is coverage
coming back.

**A registry of declared failures needs a staleness guard or it rots.**
`test_whole_collection_only_says_what_it_does` and
`test_every_draft_reading_test_says_what_it_does_without_drafts` are the
pattern to copy.

**You will exempt your own work from a rule written for somebody else's.** A
prefix rule silently widens to cover whatever is added after it: a pattern for
`QQ` also matches `QQ Claude`. When a marker gains a second meaning, revisit
every pattern that matches the first.

**A guard that has never fired may only be starved.** Coverage is proportional
to traffic. Before scaling an operation tenfold, ask which guard is about to
see real volume for the first time.

**A generated sweep over a table proves the predicate, not the table.** When a
generated test keeps missing the same bug, generate the next one from the
other end, as `test_every_text_input_on_the_index_has_state_behind_it` does by
reading the built page.

**You will add a new link shape and nothing will be watching it.**
`test_same_page_fragment_links_land_somewhere` and
`test_no_link_shape_is_silently_unresolved` catch this.

**You will trust a corpus glob that names files instead of finding them.** A
page the corpus cannot see is one whose outbound links are never scanned.
`test_the_scanned_link_corpus_is_not_empty` catches only the empty case.

**You will re-add a hardcoded search threshold.**
`test_filters_js_holds_no_literal_threshold` and
`test_the_cocktail_search_thresholds_are_not_hardcoded` catch this.

**You will rename a drafts collection and silently un-ignore it.**
`test_every_drafts_collection_is_gitignored` catches this.

**Scripts and build**

**You will describe a script tag and not write it, and the page will not tell
you.** Every unit test runs the file directly, so a script nothing loads fails
none. `test_the_card_measurement_passes_are_loaded_in_order` catches it for
the two card passes; when you delete any other tag, grep the comment you leave
behind for the names of the tags you kept.

**You will assume "end of `<body>`" means "loads first".** A page layout's
scripts land inside `{{ content }}`, above `default.html`'s own, and
`assets.js` loads in `<head>`. `test_assets_js_loads_before_any_other_script`
and the `..._load_in_dependency_order` tests catch this.

**You will loop a collection that `output: false` did not empty.** §9.1.

**An element named in a script's init guard cannot be deleted from the layout
alone.** `assets/js/cocktail-scale.js` returns early unless every element it
needs is present, and the control ships `hidden`, so the scaler vanishes from
every page with no error while a fixture that still supplies the element
stays green. When removing markup, grep the scripts and the test fixtures for
its class.

**`$wordmark-phone-scale` is the literal `0.6667`, not `math.div(2, 3)`.**
The phone sizes were tuned at it, and the exact third moves each of them by a
fraction of a pixel. `/` as division is deprecated in Dart Sass, so a ratio
that is new goes through `math.div`.

**`lightness.shift()` (shared/_lightness.scss) is how a colour is lightened or
darkened, never `color.adjust` on lightness alone.** It clamps as `lighten()`
and `darken()` did; plain `color.adjust` lets cocktails' near-white ink
overshoot into an out-of-gamut colour where it should be white (#129).

**CSS: the cascade**

**You will make markup shared and leave its CSS forked** (§2.5).
`test_every_chrome_class_has_a_rule_in_every_site_stylesheet` and
`test_the_header_and_footer_are_identical_on_every_page` catch this.

**You will assume you know how many stylesheets import `shared/`.** Grep.

**You will write a media block before the rule it overrides, and it will never
render.** At equal specificity the later rule wins. Put a narrow-width
override after the rule it changes, or nest it inside, and measure the box at
the width in question.

**You will write a bare element selector inside a component, and it will
capture something that does not exist yet.** Ask whether the container will
only ever hold one such element. If the answer is "one today", name the class.
No test can catch it.

**A class borrowed for position brings every other declaration with it.** A
head row that reuses cell classes to land in their grid tracks inherits their
colour and size too, and an accidental emphasis reads as a design decision.
Ask what else the class says and reset all of it (`color: inherit;
font-size: inherit`).

**A rule nested under a parent is a bet on where the element lives, and moving
the markup silently voids it.** When you move an element, grep the compiled
CSS for every rule that named its old ancestor. A template condition is the
same bet on which field carries the content.

**You will forget an element inherits from its parent when nesting it inside a
styled heading.** An interactive element inside a punched heading needs
`@include lettering(plain)`.

**You will write a `:not(...)` rule to take space away, and it can only ever
add.** To make a state cost nothing, the base must declare nothing.

**A property declared twice in one block is invisible to
`test_no_selector_declares_the_same_property_twice`**, which compares blocks.
So an override written after an `@include` goes unseen: give the mixin an
argument instead.

**CSS: layout and paint**

**You will check one element's width and call the row safe.** Overflow is a
property of the row: three sub-320px tracks side by side overflow a phone.
Measure the row at the width in question with `sh scripts/browser/shoot.sh`,
which reports `OVERFLOW` against the viewport. A media query is usually the
wrong fix: the row overflows at every width and a breakpoint only hides it
below one.

**You will use `display: flex` for a simple two-part row, then break it the
day one part needs more than one line.** For "a label plus arbitrary content",
prefer `position: relative` with an absolutely positioned label.

**You will give an element asymmetric padding to compensate for something, and
it is invisible until a later change makes it not.** Any asymmetry "to
compensate for X" is verified only against what is true today. Compensate for
a fact about object A on object A.

**You will assume DOM order decides what paints on top.** It decides only
among peers at the same level; `position` or `transform` promotes an element
into the positioned layer. Reach for `order` rather than moving markup when
the DOM order carries the tab order.

**`padding` cannot inset an absolutely positioned child.** Its containing
block is the ancestor's padding box, so put the inset on the child
(`inset: 0 $space-sm`).

**An inline `<svg>` clips its own content by default.** Set `overflow:
visible` on any icon that touches its own edges.

**A `--` inside an SVG comment is malformed XML, and the browser draws
nothing at all.** `test_every_shipped_svg_actually_parses` catches this, in
`tests/test_site_config.py`, not with the page the icon is on.

**You will assume every SVG is formatted the way the last one was.** Match
`<svg` plus whitespace. And you will read one transform where there are two: a
transform is a stack, so compose the ancestors and bake the result into the
geometry.

**CSS: colour**

**You will move a colour and strand the numbers tuned against it.** A number
tuned for a colour belongs to the colour. `-active` tokens are for text on a
fill, not a bare swatch. Darkening several warm hues together pulls them to
one muddy brown.

**A lightness-only colour change is not a state change at small type.** At
small sizes the eye reads hue; every interaction state that works here moves
hue.

**Three things the browser does that no test can see**

- An `<input>` does not inherit `color`, `background`, `font-family` or
  `font-size`. Set them explicitly.
- `text-shadow` paints under text decorations, so a mark that must not carry a
  shadow is a `linear-gradient` background, not a decoration.
- `<mark>` arrives with a user-agent background and colour, and only the
  `background` shorthand resets it.

**A hand-built replica of the real CSS in a dev page**

Each of these comes from replicating instead of building for real, and the
answer to all of them is to stop replicating (§13.11).

- A stray `*/` in an inline `<style>` fails silently; a `.scss` file would
  refuse to compile.
- Give every `var()` in a shorthand a fallback: one unresolvable property
  invalidates the whole declaration.
- A custom property containing `var()` is substituted where it is declared,
  not where it is used.
- Retyping a working line is not copying it.

---

## 13. The site's visual design

Both food pages use one decorative device, a blocky two-colour bar overlapping
the base of a heading with the lettering in front of it, and differ
deliberately in how much colour they spend. Cocktails is §9.13. The values
live in `_sass/`; this section says what each is for and names the token.
How each was arrived at is `DECISIONS.md` §13.

### 13.1 The mark

`box-decoration-break: clone` on an inline element with a per-line
`linear-gradient` background. Not `border-bottom` (it draws on the box) and
not `text-decoration` (it paints over glyphs). The dials are in
`_sass/shared/_rule.scss`: `$rule-thickness`, `$rule-drop` (bigger is lower
is less overlap; the single most character-defining value), `$rule-indent`,
`$rule-overhang`, and the `$rule-under-*` set for the second, thinner rule
beneath, which shares the right edge. The mixins are
`overlapping-rule-single`, `overlapping-rule-double` and
`overlapping-rule-double-last-line`.

**The under rule is flush with the lettering; the top rule is inset.** A mark
hanging into the left margin reads as broken alignment.

**The mark sits under the last line only.** `assets/js/last-line-rule.js`
wraps each word, finds the first word of the last line, and rebuilds the
element as `.rule-lines` + `.rule-last`, with `rule-split` on the element.
The double rule is emitted on the element first, so with JavaScript off the
title still wears the mark (on every line). It runs at load, on
`document.fonts.ready` and on resize.

- `box-decoration-break: slice` is not the fix (bottom-anchored bars land
  under the first line), and there is no `::last-line`.
- The targets are the script's `TARGETS` list; a heading that wears the
  double rule and can wrap must be in it.
- It rebuilds from `textContent`, so an element with child elements is
  skipped, and an element whose text another script rewrites opts out with
  `data-last-line-rule="skip"`.
- The spans it creates sit inside the target, so a descendant selector
  (`.ref-section-heading span`) redraws the rule on each of them and the mark
  wears twice; the CSS says `> span`. "The script did not run" and "the CSS
  undid it" render identically, and a DOM diff proves neither: crop a wrapped
  heading at 390.

An identical repeated mark is something the eye recognises rather than reads,
which is why it replaced the watercolour washes. "A filled field is more
visible" is a settled argument; do not re-open it.

### 13.2 The recipe page's colour budget

Four hues, and the count is the design. The swatches and the comment that
argues the budget are in `_sass/food/_palette.scss`.

| Hue | Jobs |
|---|---|
| `$color-dazzling-dragonfruit` | the rule under the title, the short-method toggle, the footer hearts (as `$color-accent`), and every cross-recipe link (as `$color-recipe-link`, its darkened form) |
| `$color-section-underline` (`$color-marauding-mint`) | the upper rule under a section name |
| `$color-section-underline-2` (`$color-blinging-blackberry`) | the lower rule under a section name, and the annotation arrow beside a note |
| `$color-blazing-banana` | the highlighter on ingredient amounts |

Everything else is `$color-text`, `$color-clear-text` or `$color-border`.
**Colour is on what you navigate by, off what you read.** Dragonfruit is the
site's one "interactive or branded" colour, which is why it also serves as
`$color-star-root`; the annotation arrow takes blackberry and not dragonfruit
because an arrow in the link colour would read as clickable. If a fifth
colour is proposed, first ask whether an existing hue can do the job.

**The device count is settled too, at what ships.** A recipe page carries
about a dozen distinct treatments (tape, mark, tagline, the tinted metadata
box, the mono source line, pills, hairlines, caps actions, the highlighter,
the stepper, list numbers, tinted note boxes, list rows). Helen has looked at
the page with fewer and kept them all (DECISIONS §13). Do not propose
flattening one as a tidy-up; a smaller count is a design change she has
declined.

### 13.3 Spacing

The scale and the named gaps are in `_sass/shared/_tokens.scss`: `$space-xxs`
to `$space-xxl` for margin, padding and gap (never font-size), then
`$spacing-block-gap` (within a section), `$spacing-section-gap` (below a
section) and `$spacing-section-top` (above a heading). The three named gaps
are deliberately far apart, because a gap only reads as hierarchy if it is
obviously bigger than the one below it.

`padding` does not collapse and `margin` does; **a flex item's margins never
collapse.**

Gaps the two sites share:

- A recipe or drink title starts `$space-lg` under the furniture line
  (`.page-furniture + .recipe .recipe-title`; a test in
  `tests/test_site_config.py` holds the selector to the include).
- A page with no furniture line (the reference pages, about) starts its title
  `$space-xxl` under the header.
- On both indexes the filter panel ends in `$spacing-section-gap` and the
  count line pads `$space-md` above itself.

Deliberately not shared: the gap above and below a section heading is bigger
on a food page than on a drink page.

**Trap:** a sibling selector goes stale silently when a wrapper is added.
Measure a gap with `scripts/browser/gaps.sh` rather than reading the Sass.

**Motion:** one `prefers-reduced-motion` query in `_sass/shared/_base.scss`
cuts every transition for a reader who asks.

### 13.4 The index page

Five sections in page order: STAR INGREDIENT, MOOD, PRACTICALITIES, then HAS
TO HAVE and LEAVE OUT side by side (`.search-pair`), then I KNOW WHAT I WANT,
the escape hatch, last on purpose. The labels are in
`_data/food/filter_sections.yml`.

- There are no work-state or `draft` filters. The `draft` and `magic bag`
  badges on a row stay: they say what you are about to click.
- Food has no "the universe says…" panel; cocktails does. On a triage site
  the panel of choices is the fold.
- Density is the index's own (`$index-section-gap`, `$index-label-gap` in
  `_tokens.scss`), not the recipe page's section tokens: the index is a
  control panel, the recipe page a document.
- The panel does not fold on a phone. A fold was built, chosen and taken
  back (DECISIONS §13); do not propose it again.

**The filter chips are one chip on both sites**, each site in its own
colours: a bold lowercase word on a torn shape. Resting, the shape is a tint
of the text colour; under the pointer it takes the section's hue and the
word a dark of it; chosen, it keeps the hue and the word goes near-black
without changing case. The slot is `.tag-shape`
(`_sass/shared/_tag-shape.scss`), the artwork is
`assets/img/chrome/tag-shapes/`, and `tagShapes()` in
`assets/js/decorations.js` fills each slot by a hash of the chip's words, so
a word wears the same shape everywhere.

**Trap:** `tagShapes()` finds a slot's host through a fixed selector list. A
new chip class missing from that list silently gets no shape.

**The chips in the two search pools are one chip too:** `@mixin index-chip`
and its companions `index-chip-word-match`, `index-chip-chosen` and
`index-chip-struck` in `_sass/shared/_rule.scss`, included by food's
`.btn-tag` and cocktails' `.btn-pool` with colours as arguments. A HAS TO
HAVE hit takes the section's colour; a LEAVE OUT hit is the resting grey,
heavier. Chosen chips sit above the candidates, carry an x, keep their case,
and choosing one clears the search.

**Every clear is `@mixin index-clear-link`:** text colour, the accent under
the pointer, never a section's hue.

#### 13.4.1 The punched-tape effect

`model_instructions/LETTERING.md` is the reference: the physics, the four
tiers, every consumer, the traps. To extend the device, say the tier with
`@include lettering(display | heading | label | plain)`, and never write
`-webkit-text-stroke` or `text-shadow` by hand. What is deliberately not
tiered, including the "N survivors" count and the wordmark's site word, is
`LETTERING.md` §7 and §8.

**No square brackets around punched-tape text.** Brackets are the wordmark's
device and name a site from `sites.yml`; the footer's reference block is the
one other legitimate use. Before adding a third, ask whether it names a site
or whether capitals merely look as if they want brackets.

#### 13.4.2 The other `-webkit-text-stroke`: faux-bold, not an edge

Check the stroke's colour. Lighter than the letter is an edge
(`LETTERING.md`); **the same colour as the letter is a faux-bold**, and
wants to stay heavy. Courier Prime ships only Regular and Bold, so
`font-weight: 900` is already Bold and a same-colour stroke
(`$faux-bold-stroke` in `_sass/food/_palette.scss`) is the only way to get
"heavier than bold", which an active filter button and a matched row badge
need. They set `text-shadow: none` explicitly, because the punched treatment
means "landmark" everywhere else.

**An active filter rule may change colour, the `.tag-shape` fill and the
stroke, and nothing that changes a box's size** (letter-spacing on an active
state shifts every tag to its right).
`test_no_active_filter_button_changes_its_own_width` reads both sites'
compiled CSS: food's `.active` and cocktails' `.is-on`.

### 13.5 The colour contract, and why the two pages differ

**Index: five hues, one per filter section, in page order.** One source, in
`_sass/food/_palette.scss`:

| Root | Hue | Section |
|---|---|---|
| `$color-star-root` | `$color-dazzling-dragonfruit` | STAR INGREDIENT |
| `$color-mood-root` | `$color-wild-wasabi` | MOOD |
| `$color-practicalities-root` | `$color-sparkling-spirulina` | PRACTICALITIES |
| `$color-ingredient-root` | `$color-torrid-tangerine` | HAS TO HAVE |
| `$color-name-search-root` | `$color-blazing-banana` | I KNOW WHAT I WANT |

Each root drives its section's rule, buttons, active states, clear link and
row badges. Each has an `-active` tone (darkened for a button label); how
far to darken is a property of the hue, so a hue that moves section takes
its step with it.
`scripts/palette_measure.py` measures the contrast.

LEAVE OUT takes no hue: `$color-exclude-active` and `$color-exclude-hover`
are neutrals. The order is Helen's (pink first, no two blues adjacent, not a
rainbow).

On the index colour is a code and must be learned; on the recipe page it is
decoration and must be rationed. **This is a principled divergence: do not
equalise the counts.**

### 13.6 The recipe list

Each row is title, ingredient line, then pills, in that order (§13.6.1).
`_sass/food/_recipe-list.scss` has the row; `_badges.scss` and
`_active-filter-states.scss` the pills.

- **Title:** Courier Prime, lowercase, weight 700. Weights 400 and 500
  render identically (two static faces).
- **Pills** rest muted (a hint of the section's hue behind grey text) and
  climb three rungs: muted, matched (`.badge--matched`: a stronger tint,
  full-ink text, faux-bold), hover (the lightened full hue, louder than
  matched).
- **Ingredient line:** clamped in CSS to one line, two below 600px
  (`-webkit-line-clamp` on `.ingredient-list`). There is no fade and no
  script measuring overflow.

There is no category-code bar; git history has it.

#### 13.6.1 Row order and why

Ingredients outrank pills because they carry the recall-lookup case the
search exists to serve: the ingredient line is what decides whether a row is
opened.

### 13.7 Results heading, pagination, shuffle

**The count line** ("N survivors") is left-aligned plain body text with no
punched treatment; `.results-heading .category-label` sets every value back
to the body default on purpose. The digits alone take `$font-label`
(`.results-count-number` in `_sass/shared/_results-bar.scss`, on
`#recipe-count-n` and `#drink-count-n`); the word stays bare.

**The sticky bar and the jump pill** are two floating copies of the count,
both driven by `assets/js/results-bar.js` and styled in
`_sass/shared/_results-bar.scss`. Both ship `hidden`, and at most one shows:

- `.results-bar`, fixed to the top, while `#results` has wholly left the
  top of the viewport. It also mirrors the top `× clear all`.
- `.results-jump` (#1441), "N survivors ↓" in a pill fixed at the foot of
  the screen, centred, while `#results` is not yet wholly on screen. Pressing
  it scrolls `#results` to the top (smoothly, unless reduced motion is
  asked for) and focuses it. No back-to-top twin, and no hiding while a
  search box has focus (DECISIONS §13.7).

Neither recomputes the count; both mirror the count spans. Where they show
is read from `#results`'s box on every `IntersectionObserver` report AND on
scroll, once a frame: the observer reports only a crossing, and a jump from
the foot of the page to the top crosses nothing. The script must load after
the index script
(`test_the_results_bar_loads_after_the_index_script_on_both_indexes`).

**Pagination:** `PAGE_SIZE` per page, prev and next, a status label,
`(see all)`. The maths is in `assets/js/list-view.js`.

**Shuffle** (Fisher-Yates, `list-view.js`) on clear-all and on every fresh
load. `.recipe-list` starts `visibility: hidden` and is revealed after the
first render, trading a visible flip for a blank instant.

**Two empty states, and they are different lines.** "Blank canvas." on both
indexes says the search was too narrow; it carries a third `× clear all`
inside the line, in the same list as the top and bottom buttons so the three
cannot disagree about whether there is anything to clear. "Nothing to see
here yet." (cocktails only) says the collection is empty.

**Going back is the one arrival that does not shuffle.** It restores shuffle
order, filters, page, see-all and scroll from `sessionStorage`, gated on
`performance.getEntriesByType('navigation')[0].type === 'back_forward'`.
That is a fact, where the back/forward cache is a favour a browser may
decline (and does on `jekyll serve`, which sends `no-store`). Half-finished
searches are not restored; a chosen result is. `filter-state.js` has no
`toQuery()` on purpose: nothing writes the URL back.

`assets/js/back-link.js` has one predicate: may this arrow call
`history.back()`? A recipe opened in a new tab carries the index as referrer
and has no history, so the answer needs both.

### 13.8 The wordmark

HELEN TRIAGES (display tier) over the bracketed site word on black tape, the
tape sized to the lettering. The sizes are the `$wordmark-*` variables in
`_sass/shared/_layout.scss`.

**Whichever row is naturally wider defines the width, through CSS Grid, not
JS.** `.site-logo` is `inline-grid; grid-template-columns: max-content;
justify-items: center`, with both rows in the one column. On food HELEN
TRIAGES is wider; on cocktails `[ COCKTAILS ]` is, and the tape adapts
rather than the word shrinking. `$tape-protrusion` is how far the graphic
extends past that core. `.site-logo-word`'s padding is in `em`, because
percentage padding here would be circular.

**Trap:** the shared column must contain only the two things being centred
on each other. A spanning grid item still contributes to an intrinsic
track's size.

**A page that belongs to no site says so twice:** `wordmark_word` (what the
tape reads, `"??"` on about and `"404"` on the 404 page) and `site_neutral:
true`, while carrying `site_key: food` for a stylesheet. Belonging to no
site for display and borrowing one site's CSS are different claims. Wherever
the about page's title would appear it reads `??`.

### 13.9 The tape background

The tapes are numbered SVGs in `assets/img/chrome/tape/`, generated by
`scripts/generate_tape.py`, whose docstring is the spec: a corner shape
(`--corner-mode`, `--seed`), machine marks (`--marks-seed`), and an edge
bevel lit from the same top-left as the lettering. There is no "good one
automatically" mode: generate a batch, look at them against the real header,
hand-pick. Each file's seed and mode are in DECISIONS §13.9.

`tape_count` in `_data/chrome.yml` must match the directory and the run must
be gapless (`test_tape_count_matches_the_tape_directory`), because
`decorations.js` rolls a random number up to it.

**Random on every load is the decision, not a default.** `tape()` picks a
fresh file per load for the wordmark and `cardTapes()` gives every
`[data-card-tape]` slot its own pick. `FIXED_TAPE_INDEX` stays in
`decorations.js` at `null` because an integer there is the whole of what
"fixed" would need. Nothing about the tapes is open.

### 13.10 Typography: three fonts, and the rule for which goes where

Self-hosted, latin subset, relative urls from `assets/fonts/`; the
`@font-face` rules are `_sass/shared/_fonts.scss` and the stacks are in each
site's palette.

| Face | Variable | Note |
|---|---|---|
| Selawik | `$font-body` | metric-compatible with Segoe UI; several weights |
| Courier Prime | `$font-headings` | Regular and Bold only |
| IBM Plex Mono | `$font-label` | one weight |

Every stack keeps a system font as fallback.

#### 13.10.1 `$font-label`: the rule

**IBM Plex Mono is for numbers you act on:** ingredient amounts on food and
cocktails, the temperature readouts and axis ticks, the timings calculator's
inputs and results, the digits of the results count. Nothing else: not
labels, not badges, not buttons, not note labels. The test for a new
consumer is neither "is this a label" nor "is this on a recipe page". The
clash only works while Plex stays the minority face. DECISIONS §13.10.1 has
the elements that tried it and came back.

#### 13.10.2 The emboss

`LETTERING.md` owns this: §2 for the physics, §3 for the tier values, §10
for the traps. The stroke is `$emboss-stroke` and the offsets are
`$emboss-offset` in `_sass/shared/_rule.scss`. The tier values are emitted as
custom properties (`--emboss-*`, `--lettering-*`), not read as Sass
variables, so a site's `_rule.scss` re-points them without a specificity
fight. There is no `.on-dark` class: a dark site inverts its palette and
every shared partial follows.

#### 13.10.3 `/dev/emboss/`: tune here, not in a mock

`_dev/emboss.html`, local only. It tunes the tape wordmark's own shadow
copies by overriding the live element at the top of the page, and writes the
settled values out as SCSS. A reproduction in a scratch file is a second
thing to keep in step with the first.

### 13.11 How a design decision actually gets made here

**Helen decides by looking, never by argument.** Every visual decision is
made on a candidates page: the real page, the real compiled CSS, fonts and
artwork, two to five treatments switchable from a bar at the top. Build the
candidates, publish them, let her pick. Do not write a paragraph arguing for
one.

- **`scripts/mock_bundle.py`** bundles a page from a local build into one
  self-contained HTML file (CSS with fonts inlined, scripts inlined, every
  SVG embedded). Build first:

      bundle exec jekyll build --config _config.yml,_config_local.yml -d tmp/site-mock

  Add candidate CSS keyed off `html[data-x="…"]` and a switcher, and publish
  it as an Artifact. `scripts/reference_candidates.py`,
  `methods_candidates.py` and `leopard_candidates.py` are worked examples.
- **Syntax-check the switcher before publishing** (a script file under
  `tmp/` that passes the source to `new Function(src)`). Use `json.dumps`
  for any text going into it, and skip `type="application/json"` blocks.
- The bundler pins `<main>` to the site's 900px column
  (`$width-content`); measure her screenshots against that, not the
  viewport.
- **Put the real state on the page, not a picture of it.** Seed
  `localStorage` for a hidden control; put the object a control is judged
  against on screen.
- **One round settles one question.** Lock what she has decided into the
  page as base CSS, and say which questions are still open.
- **Derive numbers, do not pick them, and keep the derivation in
  `scripts/`** (`universe_glass_slot.py`, `universe_line_width.py`); a
  number derived in `tmp/` is one nobody can reproduce. **And say where the
  number went:** a derivation's docstring opens with a `REPRODUCES …` line
  naming the value and the file that quotes it, or `REPRODUCES NO NUMBER`
  and what depends on it instead. `grep -rl '^REPRODUCES' scripts/` lists
  every one.
- **A worktree has no drafts.** Clone them, or the index renders nothing.
- **Delegation:** a precise spec, reviewed by diff. Tell agents to delete
  only what they created.

### 13.12 Decisions that are Helen's, not yours

Build these when she rules. Do not decide them, and do not re-open a ruling
by re-arguing it.

- **Leopard.** The cocktails page ground (`LEOPARD.md`). Every value in it
  (the pattern, its seed, how dark the page is, where the print stops) is
  one she chose by looking. A change to any of them is a new round on a
  candidates page (`scripts/leopard_candidates.py`), not an edit.
- **Any new hue.** Both palettes argue at length that the count is the
  design.
- **The voice.** Do not touch a word of copy. Where a feature needs a
  string, ship a placeholder, marked as one in a comment beside it, and say
  so in your summary. The line the rule draws: choosing U+00D7 over the
  letter x is typography; choosing the word a number is counted in is voice.
  If a string would sound like Helen, it is hers.

  **Marked is not the same as unwritten.** A marker says *she has not
  ruled*, not *these words are wrong*: strings have come back confirmed
  unchanged. Do not trust a list of markers, and do not rely on a grep for
  them either, because it finds only what was marked. A copy audit lists
  every visible string.

  **An empty slot for her words is not neutral.** It reads as a promise and
  hands her a writing task she did not ask for: show her the page without it
  first. Take the marker off a word once she has approved it. And copy her
  line, never a paraphrase of it.
- **Whether the recipe title takes the tape.** Offered and declined.
- **Which cocktails are faffy, rich, or otherwise judged.** Moods are
  derived; a disagreement goes in `mood_include` / `mood_exclude` in
  `_data/cocktails/taxonomy.yml` with its reason.
- **The `qq:` rows in `_data/cocktails/abv.yml`.** Only the label on her
  shelf settles them.

**A ruling is not permanent**, and it never moves by being re-argued. She
looks at the built page and changes her mind. Showing her the thing is
always allowed, and is how rulings move.

### 13.13 The page furniture: the same two rows on both sites

Three shared includes and one shared partial,
`_sass/shared/_furniture.scss`, which names only the palette-contract
variables; each site supplies the row it puts the shortlist pair in. The
furniture lives in the page layouts, not `default.html`: it is about where
this page sits, not about the site shell (§2.5). Read DECISIONS §13 before
moving any of it; the shortlist button in particular has had several homes.

#### The furniture line: `_includes/back-to-index.html`

`.page-furniture`, at the top of every recipe and drink page.

- **Left: the back arrow.** A real link to this site's index (from
  `sites.yml`) that works with no JavaScript; `back-link.js` upgrades it to
  `history.back()` only when it can prove you arrived from that index
  (§13.7). The artwork is `icons/arrow-right.svg`, mirrored in CSS, the same
  file as the header's door to the other site.
- **Right: print · pdf**, `_includes/page-print.html`, rendered only when a
  layout passes `actions=true`. The two page layouts do; the magic-bag
  layout does not, because no PDF is rendered beside it. The print button
  ships `hidden` and `print-link.js` reveals it. The pdf link is gated on
  `site.pdf_downloads` (off in `_config_local.yml`, where nothing renders
  the files) and is `page.url` with its trailing slash swapped for `.pdf`,
  which is where `scripts/generate_pdfs.py` writes the file for both
  collections. The dot between them is markup, `aria-hidden`, and hidden by
  CSS while the print button still is.

#### The shortlist pair: `_includes/page-actions.html`

`.page-actions`: a button that changes this page and a link to another, and
they are deliberately not drawn alike.

- **`.btn-shortlist`** is a pill, the index's `.btn-shortlist-only` shape,
  bordered in `$color-border` on `$color-surface`; hover and on take the
  border to `currentColor`, so the site's own state colours drive it.
- **`.btn-see-shortlist`** is a plain quiet-caps link in the same face as
  print and pdf: "see shortlist (N)", word first, no arrow. It links to the
  index with `?shortlist=1#results` (§8.9). N is the store's count
  (`data-shortlist-total`, from `HTF.shortlist.count()`), not the page's.
  **It stays hidden while N is 0**; `paintCounts()` in `shortlist.js`
  decides on every change.
- Both ship `hidden` and `shortlist.js` reveals them: a control that
  silently fails is worse than no control.

**Where it sits** is "the first line under the rule that closes the head, at
the right" on both sites. On a drink page that is the right-hand end of the
READ IT / MAKE IT line (`.cocktail-controls`). On a recipe it is the
right-hand end of the INGREDIENTS line (`.recipe-section-heading-row`; the
head's hairline is `<hr class="recipe-head-rule">`). Below 600px both put
the pair on a line of its own: the toggle then the pair on a drink page, the
pair then INGREDIENTS on a recipe. The shape never depends on the width or
the count.

**Trap:** SEE SHORTLIST and PDF are `<a>`s inside the article, so food's
prose-link rule is `article.recipe a:not(.badge, .btn-see-shortlist,
.btn-pdf)`. A new furniture link must join that exclusion or it takes the
link colour. The same rule beats a chrome class borrowed into the article: a
bare class loses to it silently, which is what `.not-found-ways` exists for.

#### The search box: `_includes/page-search.html`

**A local-build testing tool. The deployed site has no search box
anywhere.** It renders in the shared header of every page of a site, under
the door to the other site, only when `site.show_header_search` is true,
which only `_config_local.yml` declares, and never on a `site_neutral`
page. The include loads `assets/js/page-search.js` beside the form under
the same gate. `scripts/browser/build.sh` builds what deploys, so to look at
the box build with the local config (§13.11).

*The form.* A plain GET to this site's index with `q=`, which works with no
JavaScript and submits a name search. `HTF.filterState.parseName` reads it
(it is kept out of `KINDS` because a title may carry a comma) and each index
puts the text into its own I KNOW WHAT I WANT box and applies it as a
keystroke would. Enter or the magnifying glass submits.

*The look.* The include's own comment has each choice. The three that get
undone by accident: the input is right-aligned with the glass after it, so a
long word loses its start and never the letters being typed; **its width is
the placeholder's length**, because the placeholder (`I know what I want...`,
the only visible words) is the one string that can never scroll into view;
and it is made quiet by colour, not by size (`$page-search-quiet` mixes the
hairline and the placeholder towards each site's ground, while typed text
stays `$color-text`). Focus is an underline in `$color-accent`, never a box.

*The dropdown.* `page-search.js` fetches this site's `search.json` (the form's
`data-search-index`) through `HTF.fetchJson` the first time the box takes
focus. The pure half is `HTF.pageSearch` (`tests/js/page-search.test.js`).

- **Per site, never across sites**, grouped by kind in the index's own
  order: the pages by name first, then star, mood and practicalities on
  food or mood and hassle on cocktails, then the ingredients. The names
  group is headed by `items_label`, "food" or "cocktails"; the other
  headings are the index panel's own labels, in each site's section hue.
- **Matching is prefix-only and whole-word:** a result matches only when
  every typed word is a prefix of a whole word in it, in any order. There
  is no substring match.
- **Food's ingredient words are the index picker's.** `food/search.json`'s
  ingredient group carries `_data/food/ingredient_words.yml` as
  `vocabulary`, and `page-search.js` runs each value through
  `ingredient-search.js`'s `buildMasterList` and `entryKey` (fetching that
  script on first focus where the page lacks it), so the box offers each
  word once and every word it offers is a button the picker has.
- **Cocktails' ingredient words are the card's labels**, with a joined "X
  or Y" label offered as its parts (`search_labels` on a
  `card_ingredients` row). It falls back to `label` when `search_labels` is
  missing, on purpose: a `jekyll serve` started before a plugin gained a
  field does not have it (§1), and an imperfect list beats an empty one.
- **Every result is a real link:** to the page, or to the index with
  `?star=`, `?tag=`, `?mood=` or `?ing=` (the `KINDS` in
  `filter-state.js`), ending in `#results`, the id both indexes carry on the
  count line, so the reader lands on the answer and not the panel. Each
  index scrolls to whatever `location.hash` names after its reveal, except
  when going back.
- **`?ing=`** is handed to each index's own HAS TO HAVE: food chooses the
  picker's matching entry through the button's own click, or leaves the
  pool on screen when none is exact; cocktails matches a pool chip whole
  and drops a miss in silence.

`search.json` is generated from the same gated lists the two indexes render,
and is built on the deployed site even though nothing fetches it there;
`test_the_search_index_lists_exactly_the_published_pages` holds it to the
built pages.

**A badge or chip link on a page lands on its own filter section**, not on
`#results`: `#filter-star`, `#filter-mood` and `#filter-practicalities` on
food (`section_id` in `_includes/filter_group.html`), `#filter-mood` and
`#filter-hassle` on cocktails.

---

## 14. Reference pages and the internal-temperatures data layer

Both sites have a reference layer. Most of this section is food's, the
larger half; "The cocktails reference layer" at the end is cocktails'. What
the two share is the entry route: a footer column per site
(`reference_links` in `_data/sites.yml`), no nav link, no `index.html`. They
do not share a page anatomy, a stylesheet or a data shape, and that is
correct rather than unfinished.

### What exists (food)

`food/reference/` holds two built pages:

- `internal-temperatures.html`, the charts.
- `cooking-methods-and-timings.html`, a weight-to-schedule calculator, plus
  the fish and shellfish lists, which are on the page but not of it (nothing
  to schedule from; the page says "Not cooked by time.").

`cooking-methods-prose-archive.html` is committed but not built
(`published: false`): the sourcing notes for the timings, kept verbatim.
Read it before assuming a timing is unsourced.

The pages are look-up material for someone who already cooks, not a peer of
the two sites, which is why the footer links are the only way in.

**Page pattern:** `.recipe` / `.recipe-body-content`, the same wrapper as
`about.html`. Neither page holds a `<table>`.

**The charts page.** Every figure is a div-based chart drawn by
`_includes/food/temp_row.html` from the data.

- A row is its label and its figure on one line and the bar under them at
  the column's full width, the same at every width.
- A figure is the two numbers its bar is drawn from, never the data's
  display string, so no row says where to probe.
- A gridline sits on every multiple of five: the tens, which the ticks
  label, in `$color-border`, and the fives between them paler. They are
  generated from `$tc-min` / `$tc-max` in `_sass/food/_temperature-chart.scss`.
- There is no hover text, no note under a chart and no key entry for the
  shaded zone (its own label names the figure).
- The contents list is a row of one-word chips that wraps.
- The slow-cooked cuts are one section, `#slow-cooked-cuts`; a node's
  `chart_anchor` in the data says which section it belongs to.
- Each protein section links into the calculator with `?protein=`, because
  two views of one dataset must point at each other. Salmon's link is
  `?protein=fish`, which `cook-timer.js` reads as the dropdown's fish entry.

**The methods page.** `assets/js/cook-schedule.js` is the pure schedule
maths and `assets/js/cook-timer.js` the page wiring.

- The WHAT dropdown and the weight box are one stacked form; the weight
  hides when the dropdown says fish.
- The calculator writes one section per cut group (the data's `group`),
  each a list of method blocks. A block runs the outcome and the time on
  its first line, the method's name under them, then the oven setting, a
  line per stage.
- The protein heading's text is rewritten by `cook-timer.js`, so it carries
  `data-last-line-rule="skip"` (§13.1).
- The fish and shellfish are definition lists, one entry per fish, its forms
  as lines, hand-written in the page.

**Trap:** a method block's vertical padding is declared on the `.ct-methods
li` reset in `_sass/food/_timings.scss`, because that rule out-specifies
`.ct-method` and a padding on the block itself never applies.

The layouts are Helen's choices from candidates pages
(`scripts/reference_candidates.py`, `scripts/methods_candidates.py`;
DECISIONS §14).

### The data layer — two datasets

**`_data/food/internal_temperatures.yml`** is the single source for out-at
temperatures, endpoints and carryover. It is vocabulary-layer data. **"Out
at", never "pull at"**, in anything a reader sees.

Every figure is numeric and also a display string, because the strings
carry words a number cannot ("74–75°C in the thigh"). The recipe's doneness
section and the calculator's "Done at" print the string; the charts print
the numbers. The file's header lists the four node shapes (an endpoint with
carryover, a `doneness` map of levels with carryover, `tender_at` alone, a
`target` with carryover); a consumer checks which keys exist on the node it
resolved rather than assuming a shape from the protein.
`tests/test_reference_data.py` holds the invariants, the axis bounds, the
safety-threshold spec and note integrity.

`safety_min` / `safety_label` / `safety_summary` on a node shade the chart
below cited guidance. `git grep -n safety_min _data/food/` lists the nodes
that carry them.

**`_data/food/cooking_methods.yml`** is the source of truth and is edited by
hand. Its header documents the row schema; `shape` is the field that
matters, because a timing is not always a formula, and a calculator that
averaged the non-formula shapes into a confident time would be worse than
none. Every method row carries `oven` (a list of short stage lines) and
`outcome`, and the page renders both. Steak, fish and shellfish are absent
on purpose: they have no timings.

**Trap:** `scripts/build_cooking_methods.py` and
`scripts/build_cooking_methods_prose.py` are migration tools pinned to an
old commit. **Do not re-run them**: the data has been hand-edited since and
a re-run destroys it. Each refuses, run or imported, unless the data file
still opens with its `# GENERATED` header, which it no longer does.

### Recipe wiring

`internal_temp_ref` in a recipe's front matter is a dot-path into the
temperatures data (`beef.tender_roast`); `doneness` picks a level where the
node has levels. The resolved figure renders **below Notes, at
`#doneness`**, never in the metadata grid, and the Cook line carries a link
to it. **A live number can only render somewhere the layout controls**:
front matter is never Liquid-templated.

It is opt-in per recipe, and **a recipe that should be wired and is not is a
test failure**:
`test_every_recipe_with_a_known_protein_has_a_temperature_or_a_reason`
demands a ref or an entry in `NO_TEMPERATURE_BECAUSE`
(`tests/test_reference_data.py`). The reasons are of three kinds: the
protein is not the dish; the data has no figure for that cut (the honest
gaps, such as chicken pieces); and a figure that is right about the cut and
useless in the method, because no step probes anything. Drafts are exempt.
`test_internal_temp_ref_resolves` (`tests/test_front_matter.py`) catches a
mistyped path, which Liquid otherwise renders as no section at all.

### Fact-checking status

Every figure has been checked at least once against real sources. The
sources are in each node's `sources` string in the temperatures data and in
the prose archive page; neither built page prints them.

- If a timing looks suspiciously fast, suspect a per-500g figure read as
  per-kg first: that error has been found and corrected systematically
  once.
- **A "checked once… remove once confirmed" note in the data is Helen's own
  scaffolding**, not an error to fix.
- **Pork's "medium" and fresh ham's "hint of pink" do not clear the FSA's
  pork figure, and are deliberately not "corrected".** Whether to serve pork
  pink is Helen's call; the `safety_*` shading is how the page says so.

### The timings calculator and doneness

Very few methods have the `by_doneness` shape, so there is no page-level
rare/medium control (a control that usually does nothing reads as broken);
both figures render on those methods' blocks. `resolve()` in
`cook-schedule.js` returns a `levels` array alongside `lo` / `hi`, additive,
in data order.

### What's not done

- The temperatures data has no figure for pieces (diced, thighs in a
  sauce) or for grilled chunks; the recipes that would need one are the
  "cut the data doesn't cover" entries in `NO_TEMPERATURE_BECAUSE`.
- Almost nothing links a recipe to the methods page. Temperatures are wired
  both ways; a link into the calculator is hand-written in a method step
  (`?protein=`), and nearly no recipe has one.

### The cocktails reference layer

`cocktails/reference/` holds two pages, both in the footer's cocktails
column. A page is shipped or held back with two halves of one switch, set
and cleared in one commit: `published: false` on the page and `local_only:
true` on its `sites.yml` entry (§2.5). Nothing is marked `local_only` today.

**The test for a page here** is that it answers a question the cards moved
to the reader, not that it reprints a vocabulary. A bare list of the rum
categories would be `rum_styles` reprinted; what justifies the rum page is
its bottles column, which answers "which of mine is a Demerara rum?" now
that cards name categories and not bottles.

**`.ref-*` is its own page anatomy**, in `_sass/cocktails/_reference.scss`.
Food's reference pages reuse `.recipe` / `.recipe-body-content`, which live
in `_sass/food/`; this site's own anatomy is a drink's (a title block
reserving a column for a glass drawing, an ingredients grid built round an
amount column), so the reference layer draws a small one of its own. It
borrows where there is something to borrow: the drink page's two-colour
heading mark, and `.cocktail-suggestion`'s `$color-wicked-woowoo` for a
bottle name, because woowoo means "asked for" and a bottle name here is the
same value as one in brackets on a drink page. **One hue, deliberately**: a
second is a new-hue decision, which is Helen's (§13.12).

#### Rum categories: `cocktails/reference/rum-categories.html`

**Every string on it is a lookup, except Helen's own prose.** Nothing on the
page restates a fact the data holds.

| On the page | Read from (`_data/cocktails/`) |
|---|---|
| the shelves and their order | `rum_groups` in `ingredients.yml` |
| a category | the group's `styles` (members of `rum_styles`) |
| one row for several styles (the clairins) | the group's `combined`: the styles listed under its `origin` in the examples column |
| "site display name" | `card_names`, printed only where it differs from the category; the column is dropped from a section where no row has one |
| the example bottles | `bottles.yml` entries whose `generic` is that category, alphabetical, grouped by `origin` where bottles carry one (`bottle_origins` is the closed list and its order), through `_includes/cocktails/rum-bottles.html` |
| words after a country label, or after a bottle | the group's `origin_notes`; `rum_page_bottle_notes` |
| the rum-adjacent block and where it sits | `cane_and_palm_spirits` and `rum_adjacent_before`, through `_includes/cocktails/rum-adjacent.html` |
| the rum-based liqueurs, after every rum shelf | `rum_liqueur_shelf`: rows naming `liqueurs` generics, each with an optional page-only `label` |
| the "styles" she does not recognise | the lowercase keys of `retired_rum_styles`, alphabetical, as a bare list |
| the characters | `rum_characters`, alphabetical, with `rum_character_notes` |

- **The page walks the groups, not `rum_styles`**, so a style added and not
  placed in a group would be invisible with nothing else failing.
  `test_rum_groups_partition_the_styles` holds every style in exactly one
  group, and `test_rum_adjacent_before_names_a_real_group` holds the block's
  position. `test_no_bottle_under_a_combined_rum_row`,
  `test_rum_liqueur_shelf_names_declared_liqueurs` and
  `test_rum_page_notes_name_real_things` hold the other lookups.
- **A renamed rum generic goes in `retired_rum_names`, not
  `retired_rum_styles`**: the page prints the second's lowercase keys as
  words Helen does not recognise.
- **The case of a `retired_rum_styles` key is data:** lowercase is a word a
  recipe asks for (shown); capitalised is a bottle whose brand-generic was
  retired (hidden). `test_retired_rum_style_keys_split_by_case` guards it.
- **The retired words are a bare list**: no reasons, no definitions, no
  extra copy (DECISIONS §14). A retired word that is also in
  `rum_characters` gets a parenthetical saying so, by lookup, which is how
  one word sits on both lists.
- **A category with no bottle is correct and is not a gap to fill.** Its
  third track renders empty. The generic stays because a cocktail asks for
  it.
- **The prose is Helen's voice:** the title, the opening paragraphs, the
  numbered list, the citation and the line recommending the books, the
  arrack sentence, the characters preamble, and the three column headings
  ("category", "site display name", "examples"). §13.12 applies with full
  force: an agent ships a placeholder, never a sentence, and never polishes
  one of hers. There is no placeholder on the page.
- **Section order** is the rum shelves (the rum-adjacent block among them),
  the rum-based liqueurs, then the "styles" she does not recognise, then
  characters last.
- **The tab and the footer link say "rum categories" and the h1 says "My
  Philosophy of Rum", on purpose.** The label is wayfinding, the headline is
  voice; do not make them agree.

#### Glasses: `cocktails/reference/glasses.html`

A shelf of every glass type, each drawn at its real relative height with
the capacity it typically holds and the range. Every value is read from
`_data/cocktails/glasses.yml` (`all_icons`, `heights_mm`, `typical_ml`,
`base_centre`, and `survey_only_types` for a type that has a capacity but
borrows another type's drawing). §9.11.2 owns the survey, the rules and how
those keys are generated; the page states nothing of its own.
