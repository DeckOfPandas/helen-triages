# DEV_JOBS v26

Written 2026-08-02. Supersedes `DEV_JOBS_v25.md` — deleted, not kept, same as
`HANDOVER_v26.md`. A rewrite, not a revision: closed items removed rather
than logged, per Helen's steer — "between me and a cheap Claude we'll know
where most things are." If you need the forensic record of what a past
version got wrong, it's in git history and in `HANDOVER_v26.md` §11.2, not
here.

---

## 1. Next up

### 1.1 Deploy — the Actions workflow

Written 2026-08-02 on branch `chore/deploy-github-pages`
(`.github/workflows/build-and-deploy.yml`) — not yet merged or pushed;
paused mid-session so Helen could fix design bugs first. **GitHub Actions**
(`bundle exec jekyll build`), not native GitHub Pages build — keeps Jekyll
at 4.3 (`test_gemfile_does_not_pin_jekyll_backwards` already assumes this).
Native build pins Jekyll to 3.9. When picked back up: push the branch,
merge to `main`, set Settings → Pages → Source → "GitHub Actions", and
watch the first run together in the Actions tab, as agreed with Helen up
front (she hasn't deployed this site before).

Repo rename to `helen-triages` and `origin` repoint are already done; `url:`
in `_config.yml` already confirmed to match the GitHub username.

(MVP styling for recipe body content, previously listed here as a second
blocking item, is done — see `HANDOVER_v26.md` §4.1.)

### 1.2 The tape SVG itself needs a redesign — conversation parked mid-2026-08-02, pick it back up

Raised by Helen right after the wordmark restyle (`HANDOVER_v26.md` §13.8)
landed: "let's discuss the SVG of the tape itself, as that work was parked
with another Claude before being finished." Nobody has picked it back up yet
— this is a placeholder for that conversation, not a spec for it.

What's actually there now: `assets/img/food/tape/tape-1.svg`..`tape-4.svg`
(and, since §13.8, a direct copy of the same four files under `assets/img/
cocktails/tape/` as a placeholder). Each is **one plain, slightly skewed
polygon** (`fill="#0d0d0d"`) inside a `0 0 1400 170` viewBox, textured with a
few hundred short, low-opacity `<line>` elements for machine marks and edge
shading. **No separate corner geometry at all** — the "protrusion" §13.8's
sizing mechanism supports (tape extending past the core lettering width) is
currently just more of the same plain polygon showing at the ends, not a
distinct torn or cut corner tab. That's why protrusion was trimmed small
(`$tape-protrusion: 0.2rem`) rather than designed around — there's nothing
interesting to reveal yet.

One more thing worth raising in that conversation rather than deciding here:
`decorations.js` currently picks one of the four SVGs **at random on every
page load** (`data-tape-count`). That's the exact pattern §13.1 records as
having been tried and rejected for the recipe/index section marks — "an
identical, repeated mark becomes something you recognise rather than
something you read" — though the tape may be a genuinely different case
(background texture behind a fixed wordmark, not a wayfinding device you
need to re-find on every page) rather than the same mistake. Worth deciding
out loud either way, not by default.

### 1.3 Delete the stale draft duplicates

List was in `RECIPES_SEEN_v23.md`, now stale — draft count has grown
significantly since. Re-derive before acting on the old list.

### 1.4 Derive the cocktails schema from real recipes

Scaffold is in, deliberately empty — `HANDOVER_v26.md` §9 is the only record
of what's known. Helen will paste 5–10 real cocktail recipes; front matter
comes from what those actually need. **Do not design it top-down.**

### 1.5 Finish implementing `incidental: true`

So far it only does half of what its own name implies. What exists:
`test_incidental_not_in_main_ingredients` (`test_taxonomy.py`) and the
schema note in `HANDOVER_v26.md` (see "Easy to get wrong") — a flagged item
is kept out of `main_ingredients`, so it correctly never shows as an
index-page pill or an ingredient-search hit. What's missing: nothing reads
the flag in `_layouts/recipe.html`, so a flagged item still renders in the
recipe page's own Ingredients section exactly like a core one — no
different styling, no exclusion. First two real uses landed 2026-08-05
(`chicken-cider-stew.md`, `chicken-a-la-king.md`, both a bare/near-bare
olive oil never named again in the method). Helen: "don't include olive oil
in the ingredients list this time" — that's the ask this job doesn't
satisfy yet.

---

## 2. Content passes

### 2.1 Oven conversions in `_food_drafts/`
`180C/160C fan/gas 4` and similar. `_food_recipes/` is clean. Keep the fan
figure and **check which of the pair is the fan one before deleting** — not
always in the same order; getting it wrong bakes 20° too hot. Count is stale
(was 71 in v25) — re-derive with
`grep -lE '[0-9]{2,3} ?C ?/ ?[0-9]{2,3} ?C|gas ?[0-9]|gas mark' _food_drafts/*.md`.

### 2.2 The nine `Estimated` timings
`best-ever-chocolate-sponge-cake`, `caesar-salad-dressing`, `caramel` (×2),
`cauliflower-cheese`, `chicken-cider-stew`, `dark-chocolate-ganache` (×2),
`dark-chocolate-souffles`, `delias-classic-pancakes`, `peanut-butter-cookies`.
Leave them rather than convert to `QQ` — a poor estimate publishes, a `QQ`
blocks.

### 2.3 Loose ends in individual recipes
- `beef-wellington` — Dijon is in the ingredients, no method step mentions
  it (belongs in "Assemble"); also `QQ link to beef bone stock recipe`
- `schmaltzy-lentils-chicken-lemon` — reconstructed from a transcript, check
  breasts vs thighs; `source:` is only ever "magazine"
- `tom-kerridge-flourless-chocolate-cake` — 120°C fan set on reasoning, not
  experience; worth a note in Helen's voice once made
- `peanut-butter-ice-cream` links to `sweet-cream-base-1`, still a draft
- `beef-bourguignon` — placeholder only. **Do not auto-generate content**

### 2.4 Draft tidying is not urgent and not yours
Helen adds drafts in batches, several times a day. Only three tests read
`_food_drafts/` at all (`HANDOVER_v26.md` §10) — in practice only the
spelling-collision one ever fires. Oven conversions and placeholder steps in
drafts are invisible to the suite. **Don't tidy a draft you weren't asked to
tidy** — see `HANDOVER_v26.md` §12 for telling a new draft from a real
regression.

---

## 3. Rejected, don't re-propose without a new argument

`jekyll-seo-tag`, Stylelint, a bundler, a CSS framework, schema.org/Recipe
structured data (would push adapted magazine recipes into Google's rich
results). Each considered and declined for the stated reason.

---

## 4. Smaller, no urgency

- **One CSS naming convention.** Four schemes in use at once
  (`component-element`, BEM `__element`, BEM `--modifier`, bare nouns).
  Apply opportunistically, not as a big-bang rename across ~1,400 lines for
  no functional gain. Must also work under `_sass/shared/`, where a class
  may not name a site (`test_shared_scss_names_no_site` enforces this).
- **Should the test suite cover `_food_drafts/` more?** Current scope is
  "almost never, by accident" — the actual job is making it deliberate, not
  extending it. The `draft` fixture in `conftest.py` is dead — used by
  nothing. Either use it or delete it.
- **Mobile / narrow-device check**, deferred deliberately. No fixed widths
  overflow, no media queries needed yet, but nobody has actually looked at
  either page on a real narrow device across three redesigns — Helen's
  explicit call (2026-08-03): deployment can't be on the critical path to
  itself, and a design mistake is embarrassing, not a real-world harm, so
  this isn't a pre-deploy gate. Worth doing once things are live, not
  before.
- **`_includes/` is shared but its contents are food-specific**
  (`filter_group.html`, `recipe_badges.html`). Fine until cocktails needs
  includes of its own — decide the convention (`food_`/`cocktail_` prefix,
  or `_includes/food/…` subdirectories) before it has three of them.
- **`--annotation-gutter: 200px`** on `article.recipe` is declared and read
  by nothing. Delete, or comment that it's a placeholder.
- **Sass deprecation warnings** (~50/run): `@import`→`@use`,
  `darken()`→`color.adjust()`. Harmless now, breaking in Dart Sass 3.0. The
  `@use` migration is more invasive than it looks — it namespaces variables,
  so every `$color-*` reference site-wide needs qualifying. Not now, not
  never.
- **`_data/food/common_ingredients.yml`** holds one `pantry:` key, could be
  `pantry.yml`.
- **Stretch goal: ice cream recipes clickable from an index page list.**
  Parked here 2026-08-03 from a `CLAUDE` marker in
  `ben-jerrys-sweet-cream-base-1.md`'s `notes:` — the idea was a list on the
  index page (or somewhere) of all ice cream recipes, so a base recipe like
  this one can link out to what's built on it. No design or scoping done
  yet; this is the idea, not a spec.
