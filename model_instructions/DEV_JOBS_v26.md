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

### 1.5 Evaluate `normalize_recipes.py` (issue #114)

A candidate script exists — `DO_NOT_RUN_normalize_recipes DOT PY` in the repo
root (untracked, from a web Claude session per `git log`, 2026-08-09; not
reviewed or run). Its own docstring is the spec: mechanical, deterministic
fixes only, one per existing pytest check, edited as text in place (never a
YAML round-trip — see `HANDOVER_v26.md` §12's `yaml.dump()` trap), dry-run by
default. Explicitly excludes anything needing a judgement call or a fact
about the recipe (a missing tagline, an `Estimated` time, `QQ`, which oven
figure is the fan one, an undeclared tag/star, a spelling collision, the
ingredient-note style rule Helen reviews herself — see `HANDOVER_v26.md` §10).
Issue #114 is "find out if this will save time and whether it covers
everything" — that's the job: read it, run it dry, spot-check its report
against a few files by hand, tell Helen what it'd actually fix before anyone
runs it with `--write`. Move it into `tmp/` or `scripts/` once it's actually
being used — it shouldn't live in the repo root long-term.

---

## 2. Content passes

### 2.1 Newly surfaced test failures, not yet triaged (found 2026-08-09)

A full `pytest` run turned these up; nobody's read the actual files yet to
say whether each is a real bug or a deliberate call worth documenting. Not
the same category as `test_ingredient_annotation_style` (`HANDOVER_v26.md`
§10), which is confirmed deliberate — these are just unread:

- `test_typography` — `indonesian-chicken-curry-gulai-ayam.md` (slash
  fractions, double hyphen), `mixed-spice.md` (slash fractions)
- `test_brown_sugar_is_soft_brown_sugar` — `citrus-soy-salmon-sticky-rice.md`,
  `miso-salmon-veg-traybake.md`

(Oven conversions in `_food_drafts/` and the nine `Estimated` timings, both
previously tracked here, are fully resolved as of 2026-08-09 — `grep`/pytest
both come back clean. Removed rather than left as a stale "re-derive the
count" placeholder, since zero isn't a count that needs re-deriving.)

### 2.2 Loose ends in individual recipes
- `beef-wellington` — Dijon is in the ingredients, no method step mentions
  it (belongs in "Assemble"); also `QQ link to beef bone stock recipe`
- `schmaltzy-lentils-chicken-lemon` — reconstructed from a transcript, check
  breasts vs thighs; `source:` is only ever "magazine"
- `tom-kerridge-flourless-chocolate-cake` — 120°C fan set on reasoning, not
  experience; worth a note in Helen's voice once made
- `beef-bourguignon` — placeholder only. **Do not auto-generate content**

### 2.3 Draft tidying is not urgent and not yours
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
  extending it. (The dead `draft` fixture that used to live here was deleted
  2026-08-10 — it had zero consumers, and the three tests that do read
  `_food_drafts/` use `ALL_DRAFTS` directly, a separate mechanism.)
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
- **GitHub issue #68 (ingredient order within a group) is closed.** Helen
  confirmed 2026-08-09 the behaviour's fine and she doesn't remember what
  she originally wanted fixed. The manual discovery tool from when this was
  active work still exists if she ever wants to resume the corpus sweep —
  `scripts/find_ingredient_order_candidates.py` ranks recipes by how much
  their ingredient order seems to disagree with the method (a pointer for a
  human to read, not a source of truth; several top-ranked "inversions" per
  run turn out to be word-collision artefacts). First and only round
  (2026-08-05) covered its top ~13 candidates; most of the corpus was never
  looked at. Not worth restarting without her asking.
- **Stretch goal: ice cream recipes clickable from an index page list.**
  Parked here 2026-08-03 from a `CLAUDE` marker in
  `ben-jerrys-sweet-cream-base-1.md`'s `notes:` — the idea was a list on the
  index page (or somewhere) of all ice cream recipes, so a base recipe like
  this one can link out to what's built on it. No design or scoping done
  yet; this is the idea, not a spec.
