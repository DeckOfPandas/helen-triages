# DECISIONS — the journal

**What this is.** Every ruling Helen has made about this repo, with its date,
its reason and her words where they were recorded; every alternative tried
and rejected; every finding that changed a rule; and every time the handover
was wrong and how it was found. **Append-only, dated, grouped by the same
section numbers as `MANUAL.md`**, so a `MANUAL §n` pointer in a code
comment finds both the rule (there) and its history (here).

**How to use it.** Before re-opening a question, find its section here. A
ruling is not permanent — Helen reverses one by LOOKING at the built page,
never by being argued at (§13.11, §13.12) — but it is settled until she does,
and asking a settled question a third time is the one thing she has said
annoys her (§11.2). When a ruling changes, add a dated entry; do not edit the
old one.

**Where it came from.** Split out of HANDOVER v26 on 2026-09-06, which by then
was 9,900 lines: about 2,000 of rules inside 7,800 of this. Entries below are
condensed from that file's paragraphs; the full prose, with every measurement,
is in git history at the commit before the split: `git log --diff-filter=D --
model_instructions/HANDOVER_v26.md` names the deleting commit, and
`git show <that commit>^:model_instructions/HANDOVER_v26.md` prints the file. Issue numbers are `DeckOfPandas/helen-triages`
unless stated.

**Conventions.** `#N` is an issue. A quote in italics is Helen's own words.
"Reversed" means a later entry supersedes it and both stay.

---

## §0 The document itself, and the companions

- **2026-08-02** — HANDOVER v26 written as a rewrite, not a revision, at
  Helen's request: *"precise rather than verbose"*, *"strongly consider
  deleting rather than automatically appending"*. v25 (~1,300 lines) was
  deleted, not kept — house practice: no back-catalogue, only the current
  version. Cut hard; anything cut was resolved, superseded or recoverable
  from a commit message written for the purpose.
- **2026-08-10** — `DEV_JOBS_v26.md` retired; the backlog is GitHub Issues.
  It recorded the stated reasons for rejected tooling (§12); git log has them.
- **2026-08-11** — `RECIPES_SEEN_v23.md` (a slug/publish-status inventory)
  retired; it saved compute during large photo ingests before the Max plan
  made that a non-issue.
- **2026-08-20** — `SOURCE_ATTRIBUTION_SPEC.md` became the first companion
  document (§4). The handover header had said "No companion documents" since
  2026-08-02 while §4 cited the file by name; corrected 2026-08-21. Lesson:
  an instruction to verify (`ls model_instructions/`) is not verification.
- **2026-08-21** — The "read §12 first" box had said "§10" since the first
  draft, pointing every reader at the validation section. Corrected.
- **2026-09-01 / 2026-09-02** — `INGEST_ONE_RECIPE.md` and
  `INGEST_ONE_COCKTAIL.md` added at Helen's request for a Claude with no
  repository. The cocktail one leaves `generic` and `suggestion` as `QQ` by
  her standing ruling (*"I will update these when I make the drinks, so QQ
  is right"*), not because the vocabulary would not embed — the header had
  claimed five data files "do not embed", measured 2026-09-02: four of the
  five are between 41 and 1,034 characters. The estimate was made from the
  number of files rather than their size.
- **2026-09-02** — `tests/test_standalone_docs.py` became the guard for those
  two documents, one-directional on purpose: a retired term left in a
  document teaches a value the suite rejects to a reader who cannot run the
  suite; a newly declared term the document lacks merely under-serves. Helen,
  on the two `tmp/` scripts it grew from: *"It sounds very much like they
  should form part of our suite."* The header called their absence from
  `tests/` a gap until 2026-09-05, three days after it was closed.
- **2026-09-02** — Fable's architecture audit (`ARCHITECTURE_PLAN_2026-09-02.md`,
  retired into this file on 2026-09-06; its rulings D1–D11 are under §9.1.1,
  §9.3 and §11.0.4 below) and the ingest-inbox design (`INGEST_INBOX_DESIGN.md`,
  kept for its §6 envelope and §8 security argument).
- **2026-09-03** — The vocabulary blocks in the two standalone documents
  became generated (`scripts/build_ingest_vocab.py`, marker pairs), with a
  two-way check in `test_standalone_docs.py`; the prose stays hand-written
  because *"a generator would flatten exactly the part that makes them work"*.
  The header carried the counts 23/42/28 from 2026-09-02 to 2026-09-05, three
  rulings out of date; then 26/43/32; the counts were dropped 2026-09-06.
- **2026-09-04** — `PUBLISHING_A_DRINK.md` written on the day the first
  sixteen drinks went through it. Helen's standing instructions in it: the
  mechanical pass flips `rewritten: true` for files in `to-promote/` only;
  "final: <slugs>" is the word that means the served pages are ready to
  proofread.
- **2026-09-05** — The header's "THREE slash commands" had said two since
  `/ingest-inbox` landed on 2026-09-03. Corrected.
- **2026-09-06** — DOCS_REVIEW read all thirteen documents together: 25
  stale or contradictory lines fixed, then the split that produced this file.
  `CLAUDE_WEB_INGEST.md` added: a claude.ai Project holding the two standalone
  documents, so Helen sends dumps of several recipes and gets one envelope
  each.
- **2026-09-06, later** — Helen: rename the handover to MANUAL, *"because this
  is now more accurate"*. `HANDOVER_v27.md` → `MANUAL.md` and every `HANDOVER
  §n` in code became `MANUAL §n` (85 files; the history forms `HANDOVER v26`
  and `HANDOVER_v26.md` kept). `START_A_SESSION.md` added: the prompt she
  pastes to start a session, pointing at `CLAUDE.md`, the manual and this
  journal. The claude.ai Project's copy of the two standalone documents got a
  mechanism instead of a sentence — the `Uploaded to the Project as of:` line
  in `CLAUDE_WEB_INGEST.md`, `test_the_web_project_holds_the_current_documents`
  (fails locally when a document has a commit after that sha; skips in CI,
  and while the line says `none`), a `CLAUDE.md` rule that an agent touching
  those files says "the Project needs re-uploading" and never moves the line,
  and a reminder printed by `build_ingest_vocab.py --write`. The architecture
  plan's and the review's leftovers checked: everything done or discarded
  except two, raised as #778 (delete the `--emboss-*` alias block once its
  three readers name a tier) and #779 (decide whether the header tape is
  random per load or fixed); #759 and #733 already covered the other two.

---

- **2026-09-06, #787** — The backlog map moved from a document to an issue and
  then widened. #755 mapped the 33 design issues of 66 on 2026-09-06 and was
  stale in six rows **within a day** — #694, #695, #674, #633, #511 and #612 all
  closed, and the open count moved 66 → 73 → 71. #787 replaces it with all 71
  open issues in nine streams and says of itself what #755 said: *a map, not a
  worklist; tick nothing here.* **The format's hazard is the lesson**: any
  grouped snapshot of a live tracker decays at the rate the tracker moves, so it
  must carry its measurement date and defer to the issues for state. Helen kept
  #755 open to close herself.

- **2026-09-07 — the triage that acted on the map's lesson instead of drawing a
  new one.** #755 and #787 were both closed the night before, so the backlog had
  no map, and Helen asked for staleness, splits and a plan rather than another
  grouped snapshot. **The corrections went onto the issues themselves**, which
  is the only place that does not decay.

  **What was measurably stale, having been believed for a day or more:** #828
  asked for a DOM harness that had shipped two days earlier (`index-harness.js`
  plus the two `*-startup.test.js` files; only the third of its three boxes was
  real) · #778's "three remaining readers" of `var(--emboss` were seven ·
  #297's seventeen `qq:` ABV rows were thirteen · #806 pointed at
  `_data/food/servings.yml`, **a file that has never existed in this repo's
  history** — #815 shipped the same idea as a `serves_estimate:` front-matter
  key hours after #806 was written · #814 asked for a rule
  `.claude/commands/ingest.md` has carried since 2026-09-01.

  **And what was NOT stale, which matters as much:** #747's headline (83 of 127
  bottles priced by guess) was right to within two bottles — a first pass had
  called it stale by counting `confidence:` across the whole of `costs.yml`
  instead of per block, mixing `bottles:`, `generics:` and `fruit_prices:`
  together. **Count the block, not the file.** The real finding there was the
  eleven `confidence: low` rows in `generics:` that the issue does not mention
  at all, several with `min == max`. #752 and #744 were also called stale and
  were not: both already carried a 2026-09-07 comment doing the correction.

  **#728 was split into six (#834–#839) and closed.** It was measured, correct
  and unreadable — six kinds of question in one checklist, decaying as a whole
  rather than in the parts that had moved. Its own header makes that argument
  about handover documents; it had become the thing it was raised to avoid. The
  two blocks that change what the SITE says — 16 unfilled garnishes, 9 drinks
  with no method — re-measured **unchanged** from 2026-09-05.

  **Closed by Helen's word:** #435 (cook from drafts — *"What I'm doing is
  working fine"*; #801 and #815 turned the local site into the shopping half of
  that loop, so the PDF is only the cooking half now), #350, #305, #569, #708.
  **Closed on evidence:** #795 (her own comment answered it, and the sipping
  shelf already renders on the rum reference page), #798. **Merged:** #605 into
  #337, #821 into #642.

- **2026-09-09 — a separate ARCHITECTURE log was considered and declined, and
  the reason is the numbering rather than taste.** Helen, offering it: *"I know
  we've mostly used that for design decisions so far -- so if you think it's
  best then maybe start an architecture log? Fine either way."*

  **The environment content already has three homes, all of them established.**
  `§1 How to run it` is the smallest section in this file and the container is
  how you run it. MANUAL's `§11` already sub-numbers the machinery — `§11.-1`
  the branch workflow and the second hook, `§11.0` the destructive-git hook,
  `§11.0.1` more than one agent shares this checkout. And `§11.2` is *"Do not
  trust this document over the code"*, which is the exact subject of the
  commit-message-versus-diff lesson recorded there today. A fourth document
  would be inventing a home for content that has three.

  **`§11.1` is also taken** — a file with a colon in its name crashes the build
  — so an "architecture" section could not even take the obvious number without
  breaking what §0 promises above: the numbers are v26's, unchanged, so every
  `MANUAL §n` in a code comment resolves here.

  **And the cost of a fourth file is paid at every session start.**
  `START_A_SESSION.md` says read these three, in this order. A fourth adds a
  "which file does this go in?" decision to every future ruling, whose honest
  answer would often be "both" — which is how a document set starts drifting,
  the failure this file already records twice (the v26 split, and #755/#787's
  maps going stale within a day).

  **What WOULD justify one**: a genuinely separate audience. The three
  documents split by WHO READS THEM — `CLAUDE.md` is rules for an agent,
  `MANUAL.md` is the present tense, this is the reasoning. Environment rulings
  have the same reader as everything else here, so they are not a fourth
  audience; they are more §1.

## §1 How to run it

- **2026-08-29** — `.node-runtime/` and `.gh-runtime/` do not come with a
  worktree; cost a session that read "No such file or directory" as a broken
  checkout. Use the system `node`.
- **2026-08-18** — Two `pytest` sessions at once: the gate test's `zzz-gate-`
  recipes are collected by the other run as 14 real failures.
- **2026-09-06** — §1 had said `_config_local.yml` "overrides two things"
  since 2026-08-02; it sets seven keys and three collection outputs.
- **2026-09-07 — in the devcontainer, `git fetch origin` fails and it is not a
  credentials problem.** `origin` is `git@github.com:...`, and the container has
  no GitHub host key, so every SSH git operation dies on
  `Host key verification failed` — including `git fetch origin main:main`, the
  command `CLAUDE.md`'s git workflow is built on. **The working substitute for a
  fetch is the HTTPS URL**, which needs no credentials at all on a public repo:
  `git fetch https://github.com/DeckOfPandas/helen-triages.git main:main`. It
  fast-forwards local `main` exactly as the SSH form does. Note this does NOT
  solve pushing — `git push` over SSH fails the same way, and the fine-grained
  PAT deliberately carries no `Contents` scope, so there is no HTTPS substitute
  for it. Do not read the SSH failure as a broken checkout or a revoked token;
  it is a missing `known_hosts` entry in the image.

---

- **2026-09-09 — the devcontainer keeps three fixes and loses the worktree
  machinery.** Distilled from `chore/devcontainer-multi-worktree`, which is NOT
  merged and should not be.

  **Ports: 4999/5000 outside, 4001/4002 inside.** Helen: *"I'll always need to
  build the site locally from any branch so I'd expect to do so from outside
  the container, but inside the worktree, given it's bound... make it 4999 and
  5000 or something I'll never use."* The old `-p 4001:4001` was not merely
  useless but **actively in her way**: a running container HELD the host's own
  4001, so her `jekyll-local` could not bind it. The inside pair stays 4001/4002
  because the image's aliases serve there — though nothing listens today, the
  image carrying no jekyll, which is the same gap that stops `verify.py`
  running in the container.

  **`REPO_ROOT` comes from `--git-common-dir`, not `--show-toplevel`.** A real
  bug: `run.sh` is a TRACKED file, so a copy sits in every worktree, and
  `--show-toplevel` resolves to whichever one you are standing in — running it
  from `.claude/worktrees/foo` mounted THAT worktree as `/workspace` instead of
  the primary clone.

  **The container has a fixed name, so a second run is refused.** Without
  `--name`, `docker run` invents one each time and two terminals gave two
  containers on ONE bind mount — the trampling of 2026-09-08, when a session's
  branch moved under it four times. Docker refuses a duplicate name outright.
  It does NOT guard host-versus-container; a worktree is still the answer for
  running several Claudes at once (§11.0.1).

  **What was rejected, and why it is not merely unfinished.**
  `enter-worktree.sh` creates worktrees INSIDE the container, because git
  stores worktree pointers as absolute paths and `/workspace` in here is not
  `/home/helen/projects/...` out there. Its own header states the trade: a
  container-made worktree cannot be used from the host, and the 21 host-made
  ones report as `prunable` inside. That is a second, parallel worktree
  namespace rather than a unification, and Helen runs Claudes in HOST
  worktrees — so it buys nothing she needs, for 179 lines.

## §2 The mono-repo shape

- **2026-08-02** — Collections cannot live inside `food/`: Jekyll only
  discovers `_<name>` under the source root. Tested, not assumed.
- **2026-08-15, #204** — The two-door landing page and `root.scss` deleted;
  `/` is a bare redirect to `/food/`. `PALETTE_OWNERS` down to two. `root.scss`
  had been the third stylesheet importing `shared/` and the one nobody
  thought to check when the punched-tape mixin moved (§13.4.1): it failed at
  the next visit to the page nobody visits.
- **2026-08-19** — §2.2 had said "two stylesheets import `shared/`, and that
  is now the whole list"; grep found three (`longform-demo.scss`). The count
  is a fact about the repo today, not a constant.
- **2026-08-19, #374 (closing #288, #289)** — One header, one footer. Helen:
  *"I don't want parity between two footers — I want one footer for the whole
  site. And one header. Literally the same code and assets."* The chrome was
  already one template and was still three things: cocktails rendered NO nav
  (its per-site keys were undeclared), the nav icons rendered as raw SVG on
  cocktails because their rules lived in `_sass/food/` ("cocktails gets a
  plainer version until it wants its own" was the bug), and two tape
  directories held seven byte-identical files kept in step by hand (#223).
  `$color-accent` added as the tenth contract variable to make it possible;
  seven `sites.yml` keys retired (`RETIRED_SITE_KEYS`). Footer reference
  block is a column PER SITE gated on material — Helen's call, not "the
  current site's column". Two guards, rendered HTML and compiled CSS, and
  neither would have caught the other's fault.
- **2026-08-19** — `about.html` moved to the repo root and shipped with no
  stylesheet: the `site_key` default stopped applying, a four-sentence comment
  said the key must be set by hand, the line was never written, 17,529 checks
  passed. `test_every_published_page_links_a_stylesheet` (§12).
- **2026-08-26, #487** — Cocktails' `$color-accent` is
  `$color-electric-absinthe-deep` (menthe), the same value as
  `$color-mood-root`: the colour that means *this is the thing you asked for*
  is the mood filters', and the nav is the way out of a page. It shipped as
  amber for a few hours (amber's job is a verdict about a drink and has no
  business on a nav icon). §2.3 had said "a documented placeholder, grey on
  grey" until 2026-09-03, a week out of date — the grey was the lightness-only
  no-op that made the footer unreadable on cocktails.
- **2026-08-29** — `helen-triages-private` renamed `helen-triages-food-private`
  so both drafts repos say which site they belong to. GitHub redirects the
  old name silently; a fine-grained token follows a rename by repo ID.
- **2026-09-06** — The §2.1 tree omitted `_plugins/` (four plugins), three
  cocktail data files and `_cocktail_drafts/`; a plugins paragraph added.

---

- **2026-09-10 — THE NAV ROW IS THE DOOR TO THE OTHER SITE, and it is the
  second thing the shared header varies per site.** Asked for an unseeded
  design opinion before the family weekend, the first finding was that
  nothing told a first-time visitor the small glass in the corner was a
  second site: three same-weight icons, unlabelled, none marked current.
  Two candidates pages later (labels under the icons; the other site's
  bracketed word beside the wordmark) Helen brought her own idea — *"the icon
  and e.g. [ food ] centrally under the wordmark, with an arrow pointing
  right-wards... Then we would leave ?? on the right, possibly a little
  larger"* — and asked for an honest read rather than a build. The read: the
  arrow-as-swipe cue is the weak part (nothing swipes), and the current site's
  word under a tape that already says it is the same word twice; the strong
  version shows the OTHER site. A header-only page put three readings in front
  of her, C (her site), D (the other site) and E (both), on both grounds.
  **She chose D: *"the other site, icon and word, arrow on"*, with *"the ??
  horizontally aligned with the new arrow line."*** Shipped the same night:
  row 2 of the header grid, centred in the wordmark's column, `??` in column 3
  of that row at 1.05rem, icons 24px, a `site_neutral` page showing every
  site. **What this cost #374's guard**: the nav row is no longer
  byte-identical across sites, and the test's own docstring had said such an
  exception "wants arguing rather than accommodating". It was argued: the
  template is still one loop over `sites.yml` with no per-site key, and the
  output varies by the wordmark's own rule (it says where you are, from the
  other side). The test now compares the row within a site and requires each
  site's row to name the other and never itself. **What she declined the same
  night**: a one-line question under the wordmark (*"What shall we cook?"*) —
  *"No words under the wordmark section please."*

## §3 The three-layer rule

- **2026-08-01** — The ingredient search confirmed as earning its
  complexity (§8).
- **2026-08-16** — `back-link.js`'s first version got the new-tab case wrong
  within an hour: a recipe opened in a new tab carries the index as referrer
  while the tab has no history, so `back()` did nothing. The clearest argument
  for the pure-module split: "came from the index, but this tab has no
  history" is trivial to pose once the decision takes its inputs as arguments.
- **2026-08-19, #374** — `HTF.chromeAsset` added as a third helper rather
  than a call to `asset()`, so `test_artwork_fetches_go_through_site_asset`
  can keep banning every image path built through `asset()` with no
  exception. That test greps source and cannot tell a comment from code.
- **2026-08-29/30, #579** — `filter-state.js` grew `create(spec)` and two
  tables; `orderByBand` shared as a discipline, not the bands.
- **2026-08-31, #506** — The food index's two DECISIONS moved out of
  `filters.js` (`rowMatchesFilters`, `entriesMatchKey`); the exclusion stayed
  a second call at the call site so the excluded COUNT means "survived
  everything else". Behaviour preservation measured: 429 rows × 890 filter
  states, 381,810 decisions, identical — then the check was broken on purpose
  to confirm it could see a difference.
- **2026-08-31** — `cocktail-index.js` read `arrivedByGoingBack` off the
  BINDING instead of the MODULE; `undefined`, and the whole tail of the file
  stopped running while every JS test stayed green.
  `test_a_filter_state_binding_is_only_asked_for_what_it_has`, and #633
  (§10.2).
- **2026-09-06, #619** — `entriesMatchKey` matched CONTAINMENT while its
  comment had said "prefixes" for as long as it existed; Helen found it from
  the output (`salt` → twelve recipes whose only salt is unsalted butter).
  Measured over all 429 recipes and drafts: 136 pairs stop matching, none
  start; 104 outright defects (`ice` reaching rice, five-spice and citrus
  juice), 17 real and carried by a `nuts` synonym family instead (a net gain:
  containment had also MISSED almonds, pistachios, pecans, cashews), 15
  deliberate losses written down where they happen (`raw king prawns` only
  ever matched because `raw` sits inside p-RAW-n; `corn flour`/`cornflour`
  want fixing in the DATA; an `aliases:` entry was tried and makes it worse,
  recorded in `ingredient_words.yml`).
- **#686** — `escapeHtml` and the sessionStorage index memory, duplicated
  between the two index scripts, moved into `assets.js`.

---

## §4 Recipe front matter

- **2026-08-02** — Cross-recipe links must be relative (`../slug/`): a
  root-relative link was silently broken locally and deployed, because the
  suite checked only that the slug existed. `[[wikilinks]]` retired.
- **2026-08-02** — Body content below the front matter continues the recipe
  (Helen's "least jar" of three options): peer headings, Method's reading
  width, raw HTML for the heading markup. MVP styling closed the same day.
- **2026-08-02** — A bullet list inside one method step needed `.method-full
  li` to stop being flex; nested `<li>`s reset the step counter. Verified
  against `beef-wellington.md`'s grouped method rather than assumed.
- **2026-08-03** — `notes:` items became `{label, text}` or a bare string.
- **2026-08-09, #75** — `incidental: true`: Helen — *"It's silly to write '2
  tbsp olive oil' for a sear, when people will obviously use as much as they
  like. Whereas in a salad dressing, an amount is needed."* Her interactive
  pass deleted five generic frying-oil lines outright rather than hide them
  (nobody starting toad in the hole lacks a frying oil) and un-flagged the
  finishing butter in `plum-sauce-for-duck.md` because it is worth buying. No
  published recipe uses the flag; the mechanism stays.
- **2026-08-10, #111** — Five `~`-prefixed quantities in
  `thai-green-chicken-curry.md` and "zest and juice of N" in two recipes
  rendered unhighlighted because the quantity sat in `item:`. No test can
  catch it.
- **2026-08-12, #169** — `short_name` retired: every recipe carried it,
  nothing read it. `test_no_retired_fields` guards it and six others.
- **2026-08-18** — The gate flag renamed `awaiting-fix` → `awaiting_fix`:
  Liquid parses the hyphen as subtraction and would publish a flagged page.
  Same day: **it fails CLOSED** (Helen's call) — the first version hid a page
  only on explicit `true`, so a missing key and `"true"` in quotes both
  published.
- **2026-08-18, #331, #367** — THE RULE: every agent edit sets
  `proofread: false` in the same commit. Twelve proofread recipes were edited
  in one commit (a wording change to eight, a note on two, a group renamed)
  and no flag touched; every edit defensible, none flagged, nothing looking.
  `test_agent_edited_recipes_are_not_marked_proofread` reads git history.
  Same day: `git add -A` swept one of Helen's own uncommitted typo fixes into
  an agent commit and correctly tripped the rule — stage explicitly.
- **2026-08-18 to 2026-08-20** — `BASELINE_COMMIT` moved four times
  (`dc2a7bf` → `9c70675` → `366f392` → `9306cef`), each time Helen reviewing
  the change herself: three sweeping and content-free, the last a
  nine-recipe citation backlog walked through one file at a time (two she
  changed rather than approved). Measured before each move: zero recipes
  held, which is what made the moves cheap; a week earlier, over eight held
  recipes, the same move would have asserted something false about all eight.
- **2026-08-20, #378** — Which tests read drafts, and what each says in CI
  (§10).
- **2026-08-20** — All three staging subfolders read by the draft suite
  (`rglob`): seven staged files had been silently unscanned, and they were
  the ones closest to publication. Helen: *"your system is fine with
  to-rewrite, and I'll use it properly"* — staged files are expected to be
  suite-clean.
- **2026-08-20, #406** — `source_type` required; `test_source_attribution.py`
  over recipes AND drafts. Sixty-four drafts retyped on the date rule.
  `SOURCE_ATTRIBUTION_SPEC.md` has every ruling.
- **2026-08-21, #413** — En dashes are scoped by what a reader SEES: Helen on
  `cook_time: "20-25 mins"` — *"These still render to the user, so correct to
  en dash please."* House style reaches prose pages (`test_prose_pages.py`);
  checking only the `.html` found 0 of the 4 real violations, which were in
  the reference data.
- **2026-08-21, #417** — `INVISIBLE_KEYS` and `HELEN_CLEARED` as the two
  narrower escape hatches beside the baseline; 13 of `HELEN_CLEARED`'s 14
  entries from one session where she reviewed 14 en-dash edits line by line.
- **2026-08-21, #418** — `meta.claude_rewritten` and the three-stage staging
  pipeline (`to-rewrite/` → `to-cook/` → `to-promote/`), built out by Helen
  the same day. The issue says the subfolders are unscanned; it predates the
  `rglob` change above.
- **2026-08-21, #426** — House style stops at a `QQ` line: correcting the
  source's dash edits someone else's words about to be deleted. Worth 66 of
  67 violations in the drafts folder.
- **2026-08-21, #428** — `meta.rewritten` joined `INVISIBLE_KEYS` once the
  guard stripped comments per language (a comment in `ingredient-search.js`
  using the English word "rewritten" had blocked it for two days). Measured
  first: releases ZERO recipes. Three earlier accounts of the rename's cost
  were confidently wrong, in three directions. Renaming `rewritten` →
  `human_rewritten` for symmetry: considered, and the honest finding is that
  `food/index.html` reads `meta.rewritten` (pages are outside
  `RENDER_SURFACE`), so a rename WOULD invalidate proofreads.
- **2026-08-21, #429** — `meta:` is exactly three flags in order;
  `cooked_before` and `date_last_edited` retired (both read by nothing; the
  date was one git already knew). `cooked_before`'s guard had been a
  promotion gate in disguise (all 82 recipes `true`, 330 of 344 drafts
  `false`); Helen's ruling: promotion is not a step where the question can be
  open — a recipe is cooked-and-liked (promoted), cooked-and-disliked
  (deleted) or not cooked (*"why would I put it on my battle tested
  site?"*). Same pass: "nothing changed" and "I cannot tell what changed"
  had been conflated, costing 86 recipes their flags on a meta-reorder.
- **2026-08-21** — Generating a `QQ original` line from a full method's worth
  of verbatim book prose in one `Write` triggered "API Error: 400 Output
  blocked by content filtering policy", twice. One step-pair per `Edit`
  avoided it for ~30 recipes.
- **2026-08-21** — A 34-file ingest copied the old hyphenated flag from a
  template draft before catching it. §4.0 had said "roughly 90 drafts still
  carry the old spelling" from 2026-08-21 to 2026-08-29, when it was measured:
  zero, across 342.
- **2026-08-26** — The magic bag (§4.3).
- **2026-08-29** — THE INGEST CONTRACT settled with Helen: *is the answer in
  the source document, or in Helen's head?* Measured that day: 266 of 342
  drafts (77%) carry a gap whose answer was printed on the page — sugar type
  117, egg size 103, butter 92, ginger 58, warm spices 42, fan oven 39, milk
  36, garlic 33, flour 30. The fan temperature proves the timing: hard to get
  LATER, trivial at ingest. Same day, Helen restated the split-groups rule,
  which had never been written anywhere (*"Claude is requested to split out
  ingredient and method groups at ingest to help me, then not again after
  that"*) — she had been typing `CLAUDE THIS IS A METHOD GROUP` into drafts by
  hand; `test_no_claude_markers_left` catches the workaround.
- **2026-08-29** — The `main_ingredients` cap read as a budget (§6).
- **2026-08-31** — Every draft that can carry a `QQ Claude` line has one (264
  of 267; #637/#638/#639 are sources too corrupt to paraphrase).
  `tmp/rename_markers.py` renamed 1,074 markers (270 `QQ PLACEHOLDER`, 804
  `PLACEHOLDER - rewrite:`) to `QQ original` across 236 files; one spelling.
  `tmp/insert_rewrites.py` placed the pairs by script, idempotent, never
  reproducing source text. The interleaved pair became the standard format
  (a per-batch opt-in since 2026-08-21).
- **2026-09-01** — Helen keeps `to-rewrite/` after the universal rewrite
  pass, against a session's reading that it was redundant: *"with all the love
  in the world, I'm likely to want to cast my eyes over what you've rewritten
  for me even though I predict it will be pretty good. At the point of being
  about to cook I'll also delete any original lines that have been totally
  superseded by yours, leaving me less to pick through in the kitchen."* The
  folders are how she tracks HER work; never delete a `QQ original` line.
- **2026-09-01** — The §4 schema block had shown `serves: 4`, a bare `lemon`
  and the retired tag `one-pot` since 2026-08-02, having been written before
  the quoting rule; every one of 86 recipes quoted everything.
- **2026-09-02, #667** — `proofread` GATES PUBLICATION on both sites (§4.0
  entry below).
- **2026-09-03** — Slug from the whole title, not the head clause: Helen,
  *"Slug the whole title"*, so two "with" dishes sharing a head clause do not
  collide. Existing files keep their names.
- **2026-09-04** — Every note an ingest ADDS is `{label, text}`, both fields
  set, both beginning `QQ`: *"It's annoying for me to remember how to type
  YAML every time."*
- **2026-09-05** — Helen's own rewrite of a `QQ Claude` line
  (`sticky-squidge-ginger-loaf.md`), asked for as a comparison, holds four
  patterns: don't re-narrate what the ingredient list already says; draw step
  boundaries at physical stages, not clauses (one step per thing you would
  pause at); state the expected result plainly instead of hedging with a
  check; cut flourish, keep function. Recorded in `ingest.md`.
- **2026-09-06** — §4 had ended with "Cocktails front matter does not exist
  yet and must not be invented" since 2026-08-02, three weeks after the first
  drinks were ingested.
- **2026-09-07, #814** — **Ingests split the ingredient side and leave the
  method side flat, and have always done.** `.claude/commands/ingest.md` has
  said to split both *"once, here, and never again afterwards"* since
  2026-09-01, and the corpus says half of it happens: of 340 drafts, **142 have
  named `ingredient_groups` and no `method_groups`, and exactly ONE is the
  other way round.** 172 have neither, 25 have both. That ratio is a habit, not
  a lapse.

  **Derive the missing side rather than re-reading sources, and REVIEW rather
  than propose.** Helen ruled this and corrected the reasoning that had been
  offered against it. The claim was that the source printed the groups and
  transcribing flat threw them away, so a later derivation could be plausible
  but never faithful. Her answer: *"Most recipes don't have them as printed,
  honestly... It doesn't matter though, I can catch easily at review if
  something is in the wrong place or if names need amending."* So no
  `proposals:` block and no calibration round — the shape `methods.yml` uses is
  for a vocabulary that rewrites her prose, and this is not that.

  **It runs in both directions and they are not equally cheap.** For the 142,
  the phase names already exist and a human wrote them, so deriving the METHOD
  groups from them invents nothing — assign each step to the phase whose
  ingredients it names. For the 172, both sides have to be proposed together
  and the names are genuinely new, which is the half to look hardest at. Two
  batches, not one pass.

  **The known failure mode**: a step saying *"add the remaining ingredients"*
  names nothing, so nothing lands in it. An ingredient no step mentions is the
  signal, and those get flagged rather than assigned.

### §4.0 The gate flags

- **2026-08-18** — Hardened (above). Six tests guard it because every failure
  mode is silent; the seventh writes two throwaway recipes into the build.
  `_config.yml` `show_awaiting_fix: false`, `_config_local.yml` `true`.
  Removing the document (`:post_read`) rather than hiding it from the index is
  the whole feature — #276 is the precedent: two swatch pages linked from
  nowhere were published anyway; unlinked is not unpublished. No second field
  (`published: false` would do the job and two fields that must agree
  eventually disagree in the direction that publishes).
- **2026-08-26** — `food_magic_bag` joined `GATED_COLLECTIONS` with the
  collection; §4.0 said two until 2026-09-02.
- **2026-09-01** — What `awaiting_fix: true` means to Helen: *"'awaiting_fix'
  means I've proofread, but one small thing has been raised as a ticket,
  meaning that once that's fixed I can look for just that one thing rather
  than having to read the entire file again carefully."* A bookmark, not
  "unfinished"; `true` and absent are different states.
- **2026-09-02, #667** — `proofread: false` blocks a page on both sites.
  Helen: *"this is the very last touch that I, the human, make to the file."*
  The plugin had published on `awaiting_fix: false` alone and never read
  `proofread`; the same morning's audit had recommended leaving that, citing
  the plugin header's "two fields that must agree" argument — wrong, because
  that argument is about `published:` duplicating `awaiting_fix` and
  `proofread` is a different fact. `hide_awaiting_fix.rb` renamed
  `publish_gate.rb`; log line names the flag. **Five food recipes went off
  the live site until she reads them**: `wagamama-yakitori-sauce`, `youvetsi`,
  `sweet-potato-chocolate-brownies`, `wagamama-teriyaki-sauce`,
  `duck-a-lorange-sanguine` — the point, not a side-effect. A sixth in the
  log was the magic bag's one entry, whose schema forbade `proofread`.
- **2026-09-02** — `meta.rewritten` left `INVISIBLE_KEYS` for one commit (a
  local-only drinks badge include read it) and returned when the include was
  reverted; measured ZERO recipes affected both ways.
- **2026-09-03** — The magic bag must be able to publish, so `proofread` joins
  its schema (required, `false` on a new entry, hers to flip); `rewritten`
  stays out — no source to rewrite from.

- **2026-09-06, #662** — **Tightening the gate took five already-published
  recipes dark, and nothing noticed.** `wagamama-yakitori-sauce`, `youvetsi`,
  `sweet-potato-chocolate-brownies`, `wagamama-teriyaki-sauce` and
  `duck-a-lorange-sanguine` all say `awaiting_fix: false, proofread: false` —
  which published them under the one-flag gate and holds them back under the
  two-flag one. #662 was raised precisely to proofread them BEFORE the plugin
  changed (*"means nothing disappears at that deploy"*) and the deploy went
  first. Helen's ruling: she reads the five rendered pages and sets the flags
  herself, declining an agent pre-read, because a pre-read is not a proofread.
  **The trap generalises: tightening a gate silently unpublishes whatever only
  passed the loose version.** Measure the count before the change, not after.

### §4.3 The magic bag

- **2026-08-26** — Built: Helen's own name for her brain, answering the
  README's problem #1 — *"what shall I cook, out of everything I already know
  how to make?"* — for the half the site could not hold. A separate
  collection and test file so the recipe guards stay unconditional. A
  standing caveat rendered on every page for about an hour; Helen had it
  removed on sight — *"I am the user, and I know exactly what is going on."*
  Liquid tokenised a bare `if` written out inside a `{% comment %}` and took
  the build down (§12).
- **2026-08-30, #562** — The three meta filters (and the three-valued
  `data-meta-short` they needed — `'true'`, `'false'`, `'n/a'`, because the
  short-method filter was a PAIR wanting opposite answers) deleted with the
  rest of the work-state filters. The `magic bag` badge became one of two.
- **2026-09-06** — #507 (include/exclude the magic bag in production) can no
  longer be answered "put it in META FILTERS"; Helen: *"I need to think about
  that more."* Open: #508 (the word and the permalink), #509 (the README, in
  her voice).

---

## §5 House style

- **2026-08-09** — All nine `Estimated N mins` an earlier Claude had invented
  are gone; Helen replaced them by hand rather than have them converted to
  `QQ`.
- **2026-08-21, #413, #426** — En-dash scope and the `QQ` stop (§4 above).
- **2026-08-31** — The `QQ` exemption had also matched `QQ Claude` for eleven
  days across 32 drafts and showed nothing; ~1,000 new `QQ Claude` lines in
  one day surfaced 15 hidden violations. Both patterns gained
  `QQ\b(?!\s+Claude\b)`; `/tidy-drafts` fixed the fifteen. **A hole in a guard
  is proportional to the data flowing through it.**
- **2026-09-07, #800** — **`gf tip:` is GOOD FOOD, the magazine, not
  gluten-free.** #800 and the `GF_TIP` exemption in `tests/test_style.py` were
  both written on the gluten-free reading and both offered `GF tip:` /
  `Gluten-free tip:` as answers — the third of which would have printed a false
  allergen claim on a recipe page. Helen, asked what it meant: *"I actually
  have no idea what this means... Good Food tip, the magazine source I use a
  lot?"* She was right. **Six of the eight drafts say `source: "Adapted from
  Good Food, ..."` outright**, and not one of the eight tips is about gluten —
  they are the magazine's standing tip box (freeze half the lasagne, use mutton
  instead of lamb, what to do with a spent vanilla pod, and one that names the
  magazine inside the tip: *"the magazine likes Kallo"*). It is **eight** drafts,
  not the fourteen both the issue and the test comment claim. **The lesson is
  the shape, not the abbreviation**: an unexplained two-letter prefix was
  expanded by guess, the guess was written into an issue AND a test comment as
  fact, and it survived there because both then cited each other. Ask what a
  transcribed abbreviation means; do not infer it from the letters.
- **2026-09-07, #800** — **The label is DROPPED, not expanded.** Each of the
  eight notes becomes a plain sentence, capital to full stop, like every other
  note; `source:` already carries the attribution on six of them. This also
  disposes of the two the capitalisation question could never have covered —
  `gf tips:` and `gf tip on stock cubes:` — because with the rubric gone there
  is no varying prefix to have a house form for.

## §6 `main_ingredients`

- **2026-08-15, #130** — `common_ingredients.yml` became `pantry.yml`, a bare
  list; the wrapping `pantry:` key flattened in the same pass.
- **2026-08-29** — The cap of eight read as a budget. Helen: *"we have
  generally shifted to allowing more main ingredients where they define a
  dish, for example the long list of spices in gulai ayam... I do often find
  myself adding to that array by hand, which is plainly silly."* Measured:
  `_food_recipes/` median 6, max 14, 16 recipes over eight; `_food_drafts/`
  median 5, max 9, one over eight (which Helen wrote herself). §6 had said the
  gulai ayam had eleven since 2026-08-02; it has fourteen.

- **2026-09-06, #762** — `cornflour`/`corn flour` and `beansprouts`/`bean
  sprouts`: **the majority spelling wins**, `cornflour` and `beansprouts`.
  Re-measured, the issue's own numbers were pessimistic — 18 files against 1,
  and 3 against 1, with **both minority spellings in `_food_drafts/` only**, so
  no published recipe and no proofread flip. Two draft files, not seven. #762's
  alias analysis stands and is why a data fix was the only option: an alias
  rewrites the picker's vocabulary but never `data-ingredients`, so the
  collapsed chip would match half the recipes it names.

## §7 Taxonomy (food)

- **2026-08-01/02** — Reclassified, Helen's calls: `one-pot` and `scalable`
  retired (guessable from the recipe, and one-pot would honestly cover 57%);
  `breakfast`, `extras`, `festive`, `starter` moved mood → practicalities (not
  cravings; dictated by an external structure); `showstopper` stayed in mood
  (checked against every meat recipe — it IS a craving, for Helen);
  `virtuous` added, narrow; `freezable` kept as the one genuinely unguessable
  tag. Co-tags: only `ice cream → dessert, make-ahead`.
- **2026-08-09** — `something unusual` retired (culturally relative, not a
  real craving, barely used); `legumes` considered and not added (two
  candidates, both covered). `eggs` retired the same day for six recipes where
  egg was technique or structure.
- **2026-08-09, #72** — Freezable: `chicken-cider-stew` and
  `chicken-sorrel-potato-stew` yes, `pancetta-white-bean-stew` no — case by
  case, do not add it to "match the other two". Same day: the lemony cavolo
  nero soup is not tagged `soup` (its own tagline calls it a stew);
  `goats-cheese-squash-rosemary-griddle-cakes` is `root veg` (squash counts).
- **2026-08-12, #187** — `eggs` reinstated, Helen's explicit call, because
  eight drafts had `star_ingredient: eggs` sitting invalid (not blank, as a
  previous version of §7 had claimed — checked against the files). Each judged
  on the retirement's own test: kept for `ajitsuke-tamago`, `green-baked-eggs`,
  `pink-eggs-beetroot-yogurt-chilli-butter`, `spring-onion-feta-frittata`;
  blanked for the crème brûlées, the goats cheese soufflé (whites are
  leavening — same reasoning that keeps the chocolate soufflés on
  chocolate), the udon (head clause is the udon), the ricotta fritters (egg
  as binder). Same day: five drafts still carried `something unusual` three
  days after its retirement — `retired_star_ingredients` and its test, so a
  retired value fails with its reason.
- **2026-08-01** — Splitting "declared" from "filterable" (point
  `recipe_badges.html` at `taxonomy.tags`) proposed and rejected: no user
  stands in the gap between a fact you read (a note says more) and a fact you
  browse by (needs the filter).

## §8 Ingredient search

- **2026-08-01** — Kept: 600 distinct main ingredients across 300+ files, 54%
  in exactly one recipe; 26–29% of recipes have no star. Title search stays.
- **2026-08-16, #281** — Why the exclude picker's words are worse: same code,
  harder input (every `ingredient_groups` item, chosen deliberately by #52).
  Measured production vs local: 402 bad entries of 1,421 locally against 28 of
  348 shipping, all six source bugs in drafts. Helen's call: fix what ships,
  revisit drafts as they are proofread.
- **2026-08-20** — Re-affirmed on the identical symptom: Helen — *"The synonym
  collapse on the exclude filter has gone wrong again... This was definitely
  working properly earlier today."* Right that it had been, right that it was
  not the code: 73 candidates for `chi` locally against 10 in production, 63
  draft-only, nine drafts added at 22:06 and 22:54 that evening. Cosmetic,
  local-only, leave it. The costed-and-not-taken option (vocabulary from
  published recipes only) is Helen's, not a session's.
- **2026-08-19, #390** — "One code path" is a claim about the algorithm: the
  exclude builder took no `wordMatch` argument, so the flag was computed and
  dropped. Helen saw the two boxes stacked with the same three letters.
- **2026-08-16, #365; #403** — The exclude pool's hover: "a lighter shade"
  became a LIGHTENING once matched candidates rested at the active tone, so
  `$color-exclude-hover` is a deeper cut, guarded by relative luminance.
- **`measure_phrases`** — `bicarbonate of` and `cream of` end in "of" and lead
  real entries; a bare `little` would turn "little gem lettuce" into "gem
  lettuce"; `can ` cannot fire on "cannellini" only because the match includes
  the trailing space.

### §8.2 The food shopping list and its scaler — #801, built 2026-09-07

- **The brief, 2026-09-07** — *"add scaler and shopping list feature to food
  recipe shortlist page. This can be copied directly from the food page — I
  would like all the same features. But there is no need to cost the portions.
  When serving size is unclear, please make your best guess. Group the shopping
  list by grocery aisle, e.g. produce, dairy, fish, meat, non-perishable etc."*
  **"The food page" was read as the COCKTAIL page**, and the three other
  bullets are why: costing exists only on cocktails (#547), serving sizes and
  grocery aisles are food's own. The cocktails index has had exactly this
  feature since #546 and the food index had none of it.
- **PORTIONS, NOT BATCHES, and it follows from her own words.** A drink's box
  counts glasses; asking for a serving-size guess only earns its keep if the
  number on screen is PEOPLE, and *"no need to cost the portions"* is her word
  for the unit. So four portions of a recipe that serves six is ×0.67 — which
  is exactly what #545's drink scaler refuses (whole recipes only, clamped at
  ×1, because every drink amount sits on the 2.5 ml grid). Put to her as the
  fork it is, with the 200 g → 133 g example.
- **Her answer, 2026-09-07, and it settled the rounding rather than the fork:**
  *"For now, don't tidy/round beyond 1 g precision"*, then, unprompted, to be
  sure it had been understood: *"I mean don't roudn to 10 g or 5 g, round to
  1g"*. So: scale exactly, print whole grams, tidy nothing. `⅔ tsp` rather than
  `0.67 tsp` is NOTATION and not tidying — ⅔ prints for exactly two thirds and
  never for 0.7 — and it is the reason `fractionText` keeps a 1e-6 tolerance
  instead of a generous one.
- **Ten aisles, hers.** Offered three sets; she chose *produce, meat, fish,
  dairy & eggs, bakery, frozen, store cupboard, spices & seasonings, drinks,
  other*, in that order, which is a shop and not an alphabet.
- **A KEYWORD table, not a list of ingredients**, and the data forced it: 500
  distinct `item:` strings, 395 after truncation, all free text ("thumb-sized
  piece of fresh ginger"). **The longest keyword wins** and every exception is
  therefore an entry rather than a precedence rule — `milk`/`coconut milk`,
  `butter`/`peanut butter`, `garlic`/`garlic paste`, `mint`/`dried mint`. Two
  ingredients out of 782 end in `other` that are not cross-recipe links.
- **`garlic` and `cloves` are the same length**, which is the one place the
  longest-wins rule has nothing to decide with, and the tie sent every clove of
  garlic in the collection to the spice rack. Caught by the built-output test,
  which is the whole argument for having one: the matcher is Ruby inside
  Jekyll, so nothing that reads YAML can exercise it, and a Python
  reimplementation would have passed while the site was wrong.
- **The 44 guesses live in `_data/food/servings.yml` and NOT in the recipes.**
  43 of the 86 open `serves:` with a number; the rest say `makes: "one 8-inch
  cake"` or *"I mean, who cares, make double anyway"*. Putting a figure in 44
  files means §4.0's rule un-proofreads more than half the collection to add a
  number Helen never wrote. One reviewable file, every entry flagged
  `estimated`, every one printed with a `~`. **Not decided for her**: if she
  wants the number in the front matter, that is a schema change and its own
  piece of work.
- **Grams and millilitres are the only units totalled in.** `1½ l` of stock and
  `500 ml` of stock were two rows, and a twelfth of the first printed as
  `0.125 l`. Folding kg/l/cl in and re-expressing on the way out is NOT the
  conversion `shopping-list.js` refuses: that rule is about units with no
  defined relationship (nobody can say how many ml a dash is), and a litre is a
  thousand millilitres on both sides of every recipe here. `tbsp`, `oz` and
  bare counts are untouched, because each of those would need inventing.
- **Alphabetical within an aisle**, which departs from the drinks list's
  descending volume (Helen, 2026-09-04: *"the big pours are what you shop
  for"*). The aisle heading has already done that job — you are standing in
  front of the vegetables — and a food aisle mixes grams, spoons, cloves and
  bare counts, so there is no single axis to rank on. **A session's call, not
  hers; reversible.**
- **Open, and deliberately not decided:** whether a bare count should round UP
  for shopping (`2.83 onions` → 3). She said not to tidy, so it does not; but
  a whole vegetable is a different case from a gram and she may want the
  ceiling. Bring her the page, not the argument.
- **2026-09-07, ON THE REAL PAGE — the scaler did nothing for a quarter of the
  drafts.** Helen: *"Changing the amount of blackberry gelato I want doesn't
  change anything (that I can see) in the shopping list — e.g. whipping cream
  is always 125 ml."* Exactly right, and it was `scaleFor()`:
  `henrys-blackberry-gelato-sicilian-style` says `makes: "About 750 ml"` with
  no `serves:`, so `portions` came through null and the first version returned
  `1` whatever had been typed. **The control rendered, accepted a number and
  silently did nothing** — the failure this codebase already has a rule
  against ("a control that silently fails is worse than no control", quoted
  wherever a control ships `hidden`), and worse than the rule's own case
  because it looked like it had worked.
  - **The fix is not a guess and not a missing box.** `makes:` cannot become
    people without inventing a portion size, so the box counts BATCHES for
    those and PORTIONS for the rest, with a `×` drawn on the batch ones. One
    concept — how much of this do I want, relative to what it makes — with the
    recipe's own yield naming the unit.
  - **84 of 336 drafts are this shape**, measured, which is what ruled out
    both "no box" (fails her actual need) and "guess them all" (84 unchecked
    numbers in a file whose value is that its guesses are reviewable).
    `_data/food/servings.yml` stays published-recipes-only.
  - **Two of my own tests asserted the wrong thing** and had to change with
    it: a draft legitimately has no portion count now. The aisle-coverage
    ratchet also met the drafts for the first time (373 of 3,985 unmatched)
    and is now measured per collection — MANUAL §8's own rule for the
    ingredient picker, word for word: *measure production, not your local
    build*. 99 keywords added for the draft vocabulary took drafts to 171.
  - **The worktree had no drafts, which is why this reached her.** They are
    gitignored (§9.1) and I had not cloned them, so every measurement behind
    #801 was taken against 86 recipes that all happen to have a numeric
    `serves:`. **Clone the drafts before believing a measurement about the
    food collection** — the starting prompt says so and it was still skipped.
- **2026-09-07, #815 — the batch box lasted a few hours and Helen killed it.**
  *"increasing it to 50+ does nothing either and clearly 750 ml of gelato
  doesn't feed 50. We need estimate the number of people served by 750 ml, then
  add that to the front matter somehow. [...] all of these will need to be
  estimated at ingest. Claudes can check with me if unsure."*
  - **The lesson, and it is worth more than the feature.** Three fixes in a
    row had been downstream of one absence: a recipe that does not say how many
    it feeds. The batch box, the `×`, the "set all leaves those alone" note and
    a test for each were all machinery built around a hole. **Batches were a
    workaround for missing data, and the fix was the data.** When a fix needs
    a second concept to explain it, look up the chain for the missing fact.
  - **Not every file, and the measurement is what made it decidable.** 294 of
    423 already open `serves:` with a number; 129 needed an estimate; only 43
    of those were `proofread: true`. Bringing that table rather than "quite a
    lot of files" is what turned an open-ended migration into one question.
  - **Her ruling on the proofread cost**, quoting the documented exception
    back: *"Use the documented exception. If she reviews the change herself
    line by line, she was the last judgement, and BASELINE_COMMIT ... moves
    forward."* So `serves_estimate:` went into the front matter of all 129 and
    `_data/food/servings.yml` was deleted — one home for the number, beside the
    words it estimates from. The second home had existed only to avoid this
    question, and her answer removed its reason.
  - **`serves_estimate:` and not a second `serves:`, her choice**, and the data
    supports it: `serves` xor `makes` holds perfectly (0 files carry both), but
    `makes:` OPENS WITH A NUMBER 66 times ("950 ml", "12 slices") and `serves:`
    gives NO number 20 times (2 published, 18 drafts, 11 of them `QQ`). So
    neither "makes means no number" nor "serves means a number" is true, and
    the estimate has to be its own key. **`makes:` is never read as people.**
  - **An estimate is marked with a `~`**, her ruling in the same message — the
    only thing saying a figure was reasoned rather than written down.
  - **Twelve draft estimates are read off the DISH, not its yield**, because
    their `serves:` is `QQ` — the source said nothing and she has not rewritten
    them. Those are named in the PR as the ones to check first, and their `QQ`
    is untouched: it is her placeholder, and this adds a key beside it rather
    than answering it.
  - **Found while migrating: `_food_drafts/` has subfolders.** `to-cook/` and
    `to-promote/` track her own work, a non-recursive `*.md` glob missed two
    files, and the built-page test caught it. Glob recursively in that repo.
- **2026-09-07 — "this is all I can see": boxes, no totals, and it was not the
  code at all.** A screenshot of three shortlisted recipes, three number boxes
  and nothing underneath — with a `×` on every one, including
  `moules-mariniere`, which states `serves: "4"` and therefore could not
  possibly be a batch recipe. That was the tell: `×` on a recipe with a
  serving count means its portion count never reached the page.
  **`_plugins/food_shopping.rb` had not run.** Jekyll loads `_plugins/` ONCE AT
  BOOT and never reloads them on watch, so Helen's `jekyll-local`, started
  before the plugin existed, had been serving a plugin-less build ever since —
  no log line, no error, no clue. Reproduced deliberately with `--plugins`
  pointed at an empty directory: 427 recipes, 0 with a portion count, 0 with
  ingredients, which is the screenshot exactly.
  - **The lesson is about diagnosis, not about Jekyll.** Two reports in a row
    had been real bugs in my code, and the third looked like a third. The
    thing that settled it in one step was asking which observation was
    IMPOSSIBLE under the theory — a `×` on the mussels — rather than starting
    from the missing totals, which every theory explains.
  - **The page now says so**, because this was the third silence in a row and
    the previous two were also mine. A shortlist with recipes in it and no
    entries to total prints the reason and the remedy instead of a blank, and
    the console carries the plugin detail. MANUAL §1 gained the restart rule.
- **2026-09-07 — the yield came off the row, and dimming it was not the fix.**
  Helen, with a screenshot of `7  Moules Marinière serves 4`: *"please don't
  say 'serves X' after the recipe name at the top of the scaler. This
  screenshot makes it look like I'm asking for 28 portions of mussels."* It
  was already the quietest thing on the line — Plex, 0.78rem, the
  de-emphasised grey — so this is not a contrast problem: **a number at each
  END of a short line reads as one expression whatever the middle says**, and
  this row must open with a number. Moved into the input's `title` and
  `aria-label`. The `×` on a batch box survives because it is a MARK and not a
  second number, which is the whole distinction.

---

### §8.3 The shortlist is a view, not a facet — #918, 2026-09-10

- **Helen, having used both indexes for a weekend's planning:** fourteen
  steps written out, four of them surprising, and *"I'll even say a bug not a
  preference."* Shortlist a recipe; type "lasa"; shortlist the lasagne; press
  `shortlisted (2)` — see ONE recipe, because the title search is still on.
  Clear all — see everything, not the shortlist, because clear-all clears the
  shortlist flag too. Press `shortlisted` again — both. Type "duck" — see
  NOTHING, because nothing shortlisted has duck in its name. Press
  `shortlisted` to find out whether it is on — it turns OFF and the ducks
  appear; the button still says (2), and pressing it empties the list again.
- **Every one of those is the same fact**: `shortlisted` was declared as an
  ordinary filter in `filter-state.js` and so ANDed with everything else.
  `food/index.html`'s own comment sold that as a feature (*"shortlisted AND
  make-ahead is a question you can now ask"*). Nobody had asked it on
  purpose; she asked it by accident fourteen steps running.
- **The rule now, held in two pure functions and generated tests across BOTH
  field tables (`tests/js/shortlist-view.test.js`):** the view is exclusive.
  Pressing `shortlisted` ON clears every other filter — state, boxes, pools,
  lit buttons, the same reset clear-all uses — and shows the whole shortlist.
  Setting any other filter while it is on turns it OFF and applies that
  filter to the whole collection (`reconcileShortlistView`, run at the top of
  every `update()`/`apply()`, so no handler can forget it). A half-typed
  search (`isSearching` and its siblings, marked `keepsView`) does not leave
  the view; choosing a result does. `clear all` still turns it off, because
  "show me everything" is what those words mean.
- **The alternative not taken**: keep composing but say so in the count ("1 of
  2 shortlisted match"). It keeps a power nobody had used and keeps every
  surprise in the list above, smaller. Rejected without a candidates page:
  Helen had already ruled it a bug.
- Walked on the built food index with the browser harness after the change:
  step 5 shows two, step 10 shows nine ducks with the view off and the button
  reading (2) unpressed, step 12 shows two again with the search box emptied,
  clear all shows everything.

## §9 Cocktails

### §9.1 Privacy, the clone, the fetch discipline

- **2026-08-16** — The first three drinks ingested (Julien Sorel, Sazerac,
  Cobra's Fang) and the schema derived from them. The fully-private
  alternative (one private clone plus symlinks into eight canonical paths)
  costed; Helen accepted that field names and vocabularies are public.
  The directory was created as `_cocktails_drafts` (plural) and sat UNIGNORED
  and stageable until spotted — `test_every_drafts_collection_is_gitignored`
  derives its patterns from `_config.yml` and was broken on purpose to confirm
  it bites.
- **2026-08-22** — "Lost work" after a Windows Terminal crash (eight commits of
  rum typing) was on a local-only branch checked out in a SEPARATE worktree;
  `git worktree list` names the path (§12).
- **2026-08-29** — A zip of Helen's local checkout was two merges behind, so
  five red tests read as work never done and a day was retyped from scratch,
  including DELETING a drink the remote had merely replaced. **One clone is
  not the repo.** Same day, `GH_TOKEN` probed: `contents` 403 on both private
  repos, 200 on the public one. Helen: pushing `main` in the private repos is
  fine — widened to branches 2026-09-05.
- **2026-08-30** — The fetch discipline fires once per MERGE, not per session;
  it caught one session three times in an afternoon.
- **2026-09-01** — `git checkout --detach origin/main` is how a test clone is
  brought up to date without standing on `main` (the hook refuses a merge
  there; `fetch main:main` refuses on a checked-out branch).
- **2026-09-03** — Sixteen files sat on one disk for an evening: the one-
  working-copy rule (`PUBLISHING_A_DRINK.md`).
- **2026-09-05** — §11.0.1 had said `ln -s` into the main checkout since
  2026-08-23 while §9.1 had said since 2026-08-29 that a symlink half-works.
  Clone.
- **2026-09-06** — §9.1 had said "ask Helen every time" for a private push, a
  week after `CLAUDE.md` changed.
- **2026-09-10** — `CLAUDE.md`'s own documented pattern for cloning/pushing in
  the devcontainer (build the URL by hand, token embedded) leaked the token: a
  routine `git remote -v`, run for the reason this section's own 2026-08-29
  paragraph two above gives, printed it in full, because git had stored the
  token-bearing URL as the clone's `origin` remote. Fix is
  `scripts/git-credential-agent-token.sh`, a per-repo git credential helper
  that reads `AGENT_GH_TOKEN` from the environment at the moment git asks for
  it and never writes it to a URL or to `.git/config`; §9.1 above now
  documents the HTTPS-clone paragraph. `.claude/hooks/guard-token-expansion.py`
  was widened the same day to refuse the old embedded-URL shape outright, and
  to also scan the content of any script file a command runs (not just the
  command line itself) for that shape or for a literal token string, closing
  the gap where the risky text was moved into a `tmp/` script specifically to
  get past a different guard's complaint about the command line. Not the
  first time this file's own §12 has that shape of lesson, and won't be the
  last: a written rule survives exactly as long as nothing enforces it.
  **"Per-repo" lasted an afternoon** — the helper is passed per invocation by
  the three git wrappers and configured nowhere; §11's entry of the same
  date says why.

### §9.1.1 The drinks publication gate

- **2026-09-02, #668, rulings D1–D5 (architecture plan §8)** — D1: reuse all
  three of food's flag names, in food's order, after the two drink keys.
  `rewritten` ported too: it *"shows me if I have rewritten it, not an
  agent"*. D2: every draft carries all three, `false` — *"this is honest"*;
  `output: false` is what keeps them private. D3: `proofread` gates
  publication, both sites (§4.0). D5: drink cards show the flags as food's
  do — **built and reverted the same day**: food's cards had not shown gate
  state since #562, and shown that argument Helen ruled the same for drinks;
  `_includes/cocktails/gate_badges.html` existed for one commit. The
  migration (`tmp/migrate_drink_gate_flags.py`) inserted three lines after
  `date_last_edited:` on all 124 files, `git diff --numstat` 3/0 each. The
  index rewritten to food's shape: it had read `site.cocktail_drafts` alone,
  so a promoted drink would have rendered and been listed nowhere.
- **2026-09-02** — `COCKTAIL_BASELINE_COMMIT = "2381444"`, the tip of
  `origin/main` that day; grandfathers nothing while the collection is empty.
- **2026-09-04** — The one place an agent may type `rewritten: true`:
  `to-promote/`, where the move is how Helen claims it.
- **2026-09-05** — 108 drinks with all three `false`, 16 `rewritten: true` (all
  staged), none proofread, 22 staged — a worklist snapshot.

- **2026-09-09 — the first sixteen are not stranded, and the branch holding
  them must not be merged (#864).** All sixteen are alive in
  `_cocktail_drafts/to-promote/`, and the drafts beat
  `worktree-opus-cocktail-data`'s promoted copies on every field that differs:
  list `suggestion`s where the branch has scalars, canonical bottle names where
  it has aliases, `serve:` blocks it lacks entirely, `{label, text}` notes,
  richer methods.

  **The taglines are the sharp case and the timestamps settle it.** Every
  promoted copy carries a different tagline, and the promoted ones read like an
  agent's — *"The Manhattan's less famous neighbour: drier, and with a bitter
  edge."* against the draft's *"Achingly cool. You're either this or PBR."*
  Promotion was 17:55; the drafts commit titled *"sixteen drinks into
  to-promote/, exactly as Helen wrote them"* was 20:48. **The drafts are three
  hours newer, so merging the branch would overwrite sixteen of her own
  taglines with an agent's.**

  **Everything else on it is superseded too**: its `bottles.yml` is 727 lines
  SMALLER than main's, and the three ratings she revised to `oh gods yes` are
  already in the drafts — checked, not assumed.

  **What stands between the sixteen and the live site is one proofread.**
  Measured against the gate and against the extra bar that promotion set
  itself: 16 of 16 have no `QQ`, a written tagline, a real rung on
  `ship_scale`, `rewritten: true`, `awaiting_fix: false` and every `suggestion`
  a list. 16 of 16 say `proofread: false`. That is step 5 of
  `PUBLISHING_A_DRINK.md` and it is hers alone.

  **Why the batch stalled, which its own document predicted.** Promotion ran
  while the proofread was still in progress — the promotion commit says so in
  its body — and `PUBLISHING_A_DRINK.md` puts promotion at step 6, AFTER the
  proofread at step 5, noting of this very batch that "the promotion order is
  what made this land in two repos instead of one". The document was written
  the same day, out of this.

- **2026-09-10 — THE DEPLOYMENT. 48 DRINKS LIVE, AND `to-promote/` EMPTY.**
  The collection was built, schema'd, designed, tested and gated over three
  weeks with nothing in it; `_cocktail_recipes/` did not exist on disk and the
  index rendered "Nothing to see here yet" because the collection was empty
  rather than because the template refused to look. It looks now.

  **IT STARTED AS A DEADLINE, NOT A MILESTONE.** Helen raised #869 as "(GOAL)
  I want to deploy the cocktail's site with at least these drinks by the end
  of the day", named eleven, and the whole day's work fell out of that list:
  the ones that were ready, the ones that were nearly ready, and the two that
  turned out to be broken in ways nothing was looking for. All eleven are
  live, with 37 more.

  **THE SEQUENCE WAS PROOFREAD → FIX → PROMOTE, REPEATED, and the fixing half
  is the part worth recording.** Helen proofread in batches and pushed; each
  batch broke a handful of tests, and her framing of why was exactly right in
  advance: *"I know some will break tests, but not all of that will be
  mistakes -- there are things we need to add to our data model / dictionary."*
  Across three rounds that split about evenly. Slips: `proofread: trues`, a
  blank line before the front-matter opener, a duplicated mood, four drinks
  whose `notes` KEY was deleted rather than emptied. Dictionary gaps: Dolin
  Rouge, Ciroc Pineapple, a ninth Briottet, and the margarita glass. Neither
  half was a surprise to her, and treating every red test as a mistake would
  have thrown away half the signal.

  **WHAT PROMOTION ITSELF NEEDED** is now in `PUBLISHING_A_DRINK.md` step 6,
  because none of it was obvious until it was done: re-check the gate rather
  than trusting the flag, copy-compare-then-delete byte for byte, do not force
  `git rm` past its refusal, and move `COCKTAIL_BASELINE_COMMIT` — which is
  Helen's to grant and went in a commit of its own so she could revert it
  alone.

  **AND THE GATE STOPPED BEING THEORETICAL.** Every one of the 48 is
  `proofread: true`, so every one is live, and #367 now has teeth: an agent
  editing any of them takes it straight off the site until she reads it again.
  Every guard that had only ever run against drafts on her machine now runs in
  CI too.

- **2026-09-10 — 61 TAGLINES IN ONE SITTING, AND THE SHAPE THAT DID IT WAS A
  CSV.** #839 had 99 of 125 drinks at `tagline: "QQ"` and proposed a local
  page as the way to clear them. What worked instead: every drink in one
  table — tier by nearness to deploying (live / made and only the tagline
  missing / made with other placeholders / not made), ship rating, current
  line, a verdict on each — sent to Helen as a CSV, worked through in a
  spreadsheet, sent back, diffed, and written into the files by a script.
  Three rounds. Her words: *"this is the least chaotic way of collaborating I
  think."* Four live drinks and 57 drafts (PR #932; private PR #56); 16 drafts
  left, all hers to write, listed on #839.

  **Voice review before the writing, and the finding was repetition, not
  quality.** Line by line her drafts were fine; as a SET they leaned on the
  same three devices — the drink as a person at a party (six), the adjective
  fragment (six more), "Chartreuse doesn't care about you" (a third). She cut
  to two or three of each. Worth knowing for any per-drink copy field: review
  the set, not the lines.

  **The Ridgwell was deleted the same day**, at her word in the tagline column
  itself (*"QQ CLAUDE LET'S JUST DELETE THIS RECIPE"*), private PR #54. The
  public repo's three comment mentions of it (Punt e Mes's history in
  `ingredients.yml`, the aperitivo mood in `taxonomy.yml`, Carpano Antica in
  `bottles.yml`) are history and stay; the taxonomy one now says so.

  **`COCKTAIL_BASELINE_COMMIT` MOVED A FIFTH TIME, AND THIS ONE IS THE RULE
  RUNNING END TO END RATHER THAN BEING GRANTED PAST.** The four live drinks
  flipped to `proofread: false` in the tagline commit, as #367 requires. She
  read the four built pages ON THE BRANCH, before the merge, and said so
  (*"I've checked those four live drinks, and they're perfect. Please flip
  their proofread flags back to true and push for me."*). Second commit flips
  them back; third moves the constant, alone; the test was run with the old
  value and named exactly the four. **Nothing left the live site.** That is
  the cheapest shape the gate allows and `CLAUDE.md`'s proofreading section
  now names it. Five moves in one day is also the "promotion is a habit"
  case the constant's own comment predicted — raised as #933 rather than
  designed here.

- **2026-09-09 — A PROMOTED DRINK IS INDISTINGUISHABLE FROM AN EDITED ONE, AND
  THAT IS BY DESIGN.** `test_agent_edited_drinks_are_not_marked_proofread`
  reads the PUBLIC repo's history only — #624, a public test must never
  require private drink data — so a promotion looks exactly like the thing it
  exists to catch: drinks marked `proofread: true` appearing in an agent's
  commit. There is no way to tell them apart from inside that constraint, and
  loosening the constraint would be worse than the problem.

  **SO THE BASELINE IS THE LEVER, and the constant's own comment had
  anticipated the day**: "once drinks are actually promoted this stops being a
  formality". It moved to the promotion commit.

  **MOVING A BASELINE IS THE ONE CHANGE THAT CAN SILENTLY TURN A GUARD OFF**,
  so a green run afterwards proves nothing — §12's "test that cannot fail,
  whose symptom is green". It was verified by breaking it: a promoted drink
  edited in a fresh agent commit without setting `proofread: false` went RED
  and named the drink. It grandfathers nothing forward, because the check
  skips a commit only when that commit is an ANCESTOR of the new SHA.

  **THE FIRST DRAFT OF THAT PROOF WAS ITSELF A RULE BREAK**, and it is the
  more useful half. It undid its own commit with `git reset --hard` called
  from Python — which would have ROUTED AROUND `guard-destructive-git.py`,
  because the hook reads Bash commands and cannot see a subprocess call.
  **"The hook did not notice" is not permission.** A throwaway branch that is
  checked out, committed on, left and deleted needs no destructive command at
  all.

- **2026-09-09/10 — FOUR MOOD RULINGS, AND THE INTERESTING PART IS WHICH ONES
  BECAME RULES.** Helen asked the question directly on one of them: *"I can't
  tell if this should be manual override or if the rule can be amended."* The
  answer each time was a blast radius, not an opinion.

  - **`on fire` is hand-assigned** — and `moods_by_hand`'s own comment said it
    should have been for ten days. It ranks the rules by fit and says "the
    bottom four are here now"; by its own numbers `on fire` (.40) is one of
    the bottom four and was never added. Nothing noticed because the
    derivation happened to agree with her on all five drinks that carried it.
    Cobra's Fang was the sixth: she put the fire in `to_serve` and the rule
    reads METHOD steps for 'alight'/'flame'/'burn'.
  - **Mastiha Mojito's `sharp` is a correction, not a widened sweetener
    list.** The rule wants a base, a citrus and a sweetener; the sweetener
    here is mastiha liqueur, filed under `loud`. **One drink pours mastiha**,
    so adding it to `sweet` would be a claim about the INGREDIENT made in
    order to reach a conclusion about the RECIPE. A correction says the
    smaller, truer thing. Her evidence was unanswerable: *"I have tasted it
    and you haven't!!!!"*
  - **"Swizzles are not faff" IS a rule change** — `swizzle` and `churn` left
    `mood_step_words.faff`, because the list was making one mistake twice: a
    swizzle IS churning, so one technique counted as two faff moments and hit
    the threshold on its own.
  - **"A muddled Swizzle is faff" is a correction that REPAIRS that rule
    change.** The rule was right about Coffey Park Swizzle, the drink she was
    looking at, and took Sapin's Swizzle with it — that one MUDDLES and
    swizzles, so two faff moments became one, below the threshold.

  **THE BLAST-RADIUS MEASUREMENT WAS WRONG THE FIRST TIME AND THE SCRIPT
  CAUGHT IT.** It checked whether ANY faff word survived, where the rule wants
  TWO — so it reported "exactly one drink changes" and missed the drink that
  had two and was left with one. `derive_cocktail_moods.py` disagreed and was
  right. **Counting the wrong thing confidently is the failure to expect when
  measuring a blast radius**, because the shortcut ("does it still match?")
  looks like the question and is not.

- **2026-09-09 — THE MARGARITA'S MOOD WAS A SYMPTOM, NOT A DISAGREEMENT.**
  Helen removed `ice ice baby` by hand and the derivation kept restoring it.
  The cause was one field over: she had moved the drink from an old fashioned
  glass to a `margarita`, and `serve.ice` was still `large cube` from the old
  glass. *"Not served with an ice cube in the margarita glass, you're correct.
  Extra misleading here because this margarita does not come out of a frozen
  drink machine!"* With the serve corrected the mood derives away on its own,
  no correction needed and nothing to remember later. **A hand-edit fighting a
  derivation is worth reading as a bug report about the data it derives
  from.**

- **2026-09-09 — A GARNISH THE METHOD ALREADY PLACES IS NOT A GARNISH.** Modern
  Zombie's page printed "Garnish with half an empty passion fruit shell."
  after the fire, and Helen: "Garnish step at the end of Modern Zombie needs
  to be deleted." **The step is GENERATED from `garnish:`, so there was no
  method step to delete** — deleting one would have removed the fire. The
  method fills that shell with overproof rum and sets it alight, which makes
  it part of the BUILD. It is `no garnish` now: a DECISION that renders and
  never generates a step, as against `[]`, which means nobody has decided.

  **THE MIRROR OF #880's 18th CENTURY**, where the duplicate was the method
  step and the fix was to delete it. Same repetition, opposite lever, and
  which one to reach for depends entirely on which field is generating.

- **2026-09-09 — TWO MODERN ZOMBIES, AND THE NEWER CONTENT WAS UNDER THE OLDER
  NAME.** Dropping "(makes 2)" from the title left Helen's edits in
  `modern-zombie-makes-2.md` and a copy of the pre-edit content in a new
  `modern-zombie.md`. Which was which was decidable rather than a guess: the
  old file had the float step whose OWN NOTE said the ingredient was written
  wrong. **No test could see it** — two drinks, same title, both valid.

  **ONE NOTE DIED WITH THE DUPLICATE AND WAS REPORTED, NOT RESTORED**:
  "Swapping the grenadine for 20ml Falernum 10ml cane sugar syrup was great
  (Mum was a big fan)." Rewriting the notes into labelled form looked
  deliberate; losing a note about her mum to a copy-paste accident would not
  have been, and only she could say which it was. She ruled it out the next
  day. **The rule: when a delete is ambiguous between "chosen" and
  "accidental", the report is the deliverable.**

### §9.2 / §9.2.1 The sources

- **2026-08-16** — The CSV (118 drinks over 656 rows): pasted into a chat its
  empty tabs collapsed and put Cobra's Fang's "Honestly this just gets better
  and better" in `Notes` when the file has it in `Method`; kept as a note,
  flagged. Known defects: `Corvoisier`, `La Fee Parisienne`, `Creme de Pêche`.
- **2026-08-31** — The Death & Co photo batch: ten drinks from fifteen
  photographs; two caught only a title (dropped on Helen's say); four already
  here, three gained citations, the fourth was a different Sazerac —
  *"name it 'Sazerac (Death & Co)', leaving mine as simply 'Sazerac'."* Found
  and recorded, changed nothing: four missing citations, an ice instruction
  (half vs three-quarters), a serving count, an amount out by 24×
  (`pic-a-de-crop-punch`, 12 oz of overproof Demerara against half an ounce).
  Eleven bottles handed back, one taken (Dolin Blanc). Two drinks unmakeable
  from what was shot (#627 a method cut mid-sentence, #628 an infusion on a
  page nobody photographed), paired deliberately — *"I'm not digging the book
  out for just two!"* The Sazerac's truncated last step, a QQ since
  2026-08-16, was completed by Helen from Death & Co's wording in one line.
- **2026-08-31 / 2026-09-01** — On the 12 oz, asked again: *"we've agreed this
  twice now, so stop tracking it."* A QQ that has been ANSWERED becomes a
  plain note; only a QQ that was wrong to ask gets deleted.
- **2026-09-03** — The second way in: the standalone document via claude.ai
  and an `ingest` issue (§11.0.4).

### §9.3 The schema

- **2026-08-17** — `glass` became a LIST (corrected from scalar). Helen on
  Cherry Heering: *"I'd note my preference as the example not the category"*
  — a preferred bottle is a `suggestion`, never a `generic`.
- **2026-08-26, #291** — `to_serve` live and filled by a bulk move of three
  fragments; two were serveware and one ("Without ice.", Gin Sour) was ice,
  deleted 2026-09-05 when ice got a field. `test_to_serve_is_a_string`
  because `markdownify` stringifies a list rather than raising. #573: four
  drinks had written "Serve with a straw." into `method` while three said
  `to_serve: "Straw."` — one fact, two fields, decided by whichever session
  last touched it; moved, and `test_no_method_step_restates_to_serve_or_garnish`
  keys on the leading VERB. Helen's report of the two fields drifting into
  each other: *"things to serve with (like a paper umbrella) aren't written or
  laid out the same way."*
- **2026-08-29** — `generic` fully typed: 619 entries, 0 untyped, 0 `QQ`
  (parsed, not grepped); #335 closed on the measurement — its "526+ of 594"
  figure was two passes out of date and the issue one more behind.
- **2026-08-30, #571** — `ml:` retired. Helen: *"Food YAML has this structure,
  and I'd like cocktails to match."* Measured first: 521 entries carried both
  and all 521 derived exactly from `measures:`; the other 98 non-volumetric
  and none carried an `ml`. What the key was buying — a guaranteed number, which
  #545, #294/#297 and #547 all need — it never delivered (absent on all 19 unitless amounts);
  `test_every_amount_is_readable_as_a_quantity` is stronger. Nineteen bare
  numbers (Port-au-Prince's 30/22.5/15/7.5 is plainly ml, Drunken Skull's
  0.75/0.5 plainly oz) carry a `QQ - no unit in the source` note the guard
  reads. §9.4's "store the quantity both ways" bullet stood contradicting
  §9.3 for six days; kept struck.
- **2026-08-31** — *"I don't want any US units, just ml, so please convert for
  me as part of ingestion. 1 oz = 30 ml."* Extended to `tsp`. 191 amounts
  across 44 drinks converted; three punch steps kept their ounces in prose
  through the first pass; two files kept theirs on purpose (a verbatim
  quoted recipe in a note, Helen's own experiment note). `oz` and `tsp` stay
  declared because the dictionary is what makes a conversion checkable.
- **2026-09-02, #669, D4 and Helen's second ruling** — Eleven entries had no
  `amount`. First ruling: a top-up is a METHOD STEP. Second, the same day:
  *every ingredient HAS an amount, and for these it is a verb phrase* —
  `to top` (six champagnes, two soda waters), `to rinse` (Sazerac Death & Co's
  absinthe, Tailspin's Campari), and `man-o-war`'s salt goes IN the drink,
  `amount: "1 small pinch"`, its `item: "Tiny pinch of salt"` deleted. All
  declared in `measures:` `non_volumetric`; the strings appear nowhere in the
  test. **Soda water, never club soda** — she is not in the US and doubts the
  difference is more than marketing; eight drinks normalised, the one
  surviving mention inside a QQ note recording a source. Her rim wording that
  day, *"Salt a half-rim of the glass."*, was replaced 2026-09-04 by her own
  Margarita sentence.
- **2026-09-02, #670** — Every hyphenated range and `--` in the collection
  fixed (2026-09-03).
- **2026-09-03** — Ruled by Helen: a barspoon is `5 ml`; an egg or a sugar cube
  is an INGREDIENT with `amount: "1"`, not a unit.
- **2026-09-04** — Rulings, all Helen's: **`half` and `whole` are units** (the
  Caipirinha's `amount: "0.5"` → `"half"`; a whole fruit is counted, never
  measured, because `juice_yields` says 20–30 ml); **a method step may carry a
  `note`** — *"separate note field please, although it will be used
  sparingly"* (the pair turned a proposals test red with *cannot use 'dict' as
  a set element*, so every reader of `method` goes through one helper; the
  deriver reads step AND note, because the Caipirinha's `muddler` was the
  second faff hit); **the rim is the Margarita's own sentence**, *"her
  Margarita sentence is canonical, but swap the tequila for the leading
  spirit in the rare case it isn't tequila"*; **the twist step is the
  layout's** (answering `el-presidente`'s QQ: *"this should become canonical,
  for each type of citrus twist"*) — three drinks had written it by hand in
  three wordings and `man-o-war` said discard while its garnish said the peel
  stays; **#594's vocabulary half**: *"Most 'sugar syrup' means 'cane sugar
  syrup', possibly all. Sometimes I say 'demerara sugar syrup' when I mean
  that. Let's standardise this please."* — 43 drinks retyped, the card
  untouched; `honey water 1:1`/`2:1` flattened to one in the afternoon and put
  back beside it the same evening — *"Bee's Knees needs to say honey water
  2:1… I really do need that generic here"*.
- **2026-09-05** — `item` gone from every pour (§9.10 below); `serve` (§9.10a);
  #572: about half the notes in the collection are the ingest-audit trail
  (`QQ - generic values INFERRED, not confirmed`), counted not quoted;
  `date_last_edited` retired from drinks (read by nothing); `made_before` and
  the `???` word (§9.5).
- **2026-09-06** — `serves:` added on nine drinks (#297): seven punch bowls,
  the mulled wine, the Modern Zombie; the scaler does not read it.

- **2026-09-06, #754** — **`as:` added to an ingredient**, a closed vocabulary
  of `float` / `rinse` / `muddle`. Asked whether a new field earns its place for
  three floats, one rinse and a handful of muddles — against `card_order:` by
  hand, or leaving the order wrong and saying so — Helen chose the field. It
  gives #567's tier 7 its members, lets the muddle clause group by `as: muddle`,
  and takes the fact out of QQ prose on `tiki-max`, `zombie-intoxica` and
  `modern-zombie-makes-2`. **Declare the vocabulary and its guard before any
  drink carries it**: `rum_characters` sets the same trap (#530) and the suite
  gates the deploy.

### §9.3.1 The ingredient vocabulary

- **2026-08-21, #441** — `generic` as a list means OR and only OR. Daisy de
  Santiago (Havana 3 OR Clément Agricole Blanc: either makes the drink)
  against Gosling's Black Seal (moderately aged AND blackstrap: one bottle,
  two properties). Disjunctive only when both bottles can be named and a
  reason given; "I don't know which" stays `QQ`. Getting it right first
  mattered because #292's exclusion logic ("no whisky tonight") would silently
  misbehave on whichever was encoded wrong.
- **2026-08-22** — `ingredients.yml` written (#322 the spec, #314 the rum
  half). Blackstrap listed under `rum_untyped` with a comment saying it could
  be either field.
- **2026-08-23, #441** — `character` lives on the recipe, not a bottle table.
  The issue's first draft argued the opposite ("must not be repeated across
  594 entries"); Helen, walked through from scratch, overturned the premise:
  it is *why this drink wants this bottle*, so restating it is each recipe
  correctly stating its own reasoning. Airmail's `character: [sherry,
  "Spanish-style"]` was right all along. #297 (ABV) and #295 (glass volumes)
  explicitly do NOT get the same pass — bottle-invariant.
- **2026-08-23, #457** — Six suggestions had drifted into sentences with
  reasoning ("Beefeater is nice for a brighter drink against the mint"); the
  reason gets its own per-ingredient `note`, `suggestion` goes back to names.
  Caipirinha's cachaça ranking ("Sagatiba = Leblon > Viero Barriero > Abelho
  > Yaguara Organic") stayed a note verbatim — *"Future Helen will know
  exactly what I mean"*.
- **2026-08-24, #314** — *"Blackstrap is only ever given as a character for
  another rum, like this: Moderately aged (character: blackstrap)."* Applied
  2026-08-26 to Don's Own Grog, Georgetown Punch and Jungle Bird.
- **2026-08-25, #460** — `character`, `note` and list-form fields render on
  the drink page; #460 stayed open for the rest of the page.
- **2026-08-26** — `character` had been guarded by nothing; `sherry` and
  `Spanish-style` had been passing AS generics. `test_rum_character_is_declared`;
  gin's characters free text by Helen's call. #459: *"everything we do is
  focused on the user (i.e. Helen), and making sure the user gets the drink
  she wants. Being an encyclopaedia of drinks sounds like busywork and it's
  not for me."*
- **2026-08-27** — `card_names` (#501, §9.10.1). Smith & Cross moved to
  `Jamaican, moderately aged` (it is aged; 57% made it look unaged) and
  carries the first bottle-level note ("be sensible about how much you
  use"). `Demerara, aged` / `overproof` are appellations — 100% DDL, from
  *Minimalist Tiki*; both Pusser's are `moderately aged` despite tasting
  Demerara; Skipper's needed Helen; Wood's at 57% is AT proof, not overproof.
  Two absent suggestions as real answers: Long Island Iced Tea's rum, and
  Milliners Punch's "cheapest white rum to hand; sometimes JW Spicers" — what
  is cheap and what needs using up are facts about the shelf on the day.
  `caramel-forward Jamaican rum` has bottles and no drink and is hers to
  apply — Helen dropped the two Blackwell suggestions (*"I never use Blackwell
  there"*). An earlier draft of the section had the Frozen Fruit Daiquiri
  dropping its suggestion by misattribution; the resolve test caught it.
- **2026-08-27/29, #561** — Every generic reads as an ingredient: natural word
  order, spirit word on the end. Helen on the mouthfuls: *"they're almost
  always going to be on their own line, so eminently skippable if wanted, and
  I don't want to do the cognitive work of mapping to Minimalist Tiki every
  time I read them."* The agricoles take their French names. The three
  brand-generics generalised (`pineapple rum`, `blended overproof rum`,
  `coconut rum`) — they had been permitted *"because nothing generalises
  them"*, and all three have been; Pusser's 151 found a home in `blended
  overproof rum`.
  `peated Scotch` retired for `single malt scotch whisky` + `character:
  [peated]`. Whisky/whiskey named correctly; `bonded rye` a real style
  (*"bonded rye is a different thing, like overproof demerara rum"*); the
  guard for characters derived from the `_characters` suffix so declaring a
  list switches enforcement on.
- **2026-08-30, #542** — A session put cobra-effect into `caramel-forward
  Jamaican rum` from its own `item` text, the exact thing the paragraph
  above forbade. Helen: *"I remain annoyed about this. I have discussed this
  at least twice… If I have to deal with this again I will simply delete
  those recipes."* `hers_to_apply` and its test built that morning. The four
  #542 rulings: `hurricane-classic` → `moderately aged rum` + Pusser's
  Gunpowder; `tiki-max` → the same + Pusser's Blue Label; `cobra-effect` →
  `moderately aged Jamaican rum`, no suggestion, deliberately;
  `georgetown-punch` → `lightly aged and filtered rum` then `moderately aged
  rum` + blackstrap + Gosling's (its note carries the source's own figures,
  which differ: 22.5 ml vs her 20 ml of each juice, Koko Kanu vs Malibu).
  Same day, the four #542 rulings recorded here because the last set was
  recorded only in an issue comment and reversed inside three days.
- **2026-08-30** — Five vocabulary rulings: `Chartreuse Verte` / `Jaune`
  (agreed earlier and written down NOWHERE — the reason the other four are
  recorded); `sloe gin` its own generic (split out of `gin liqueur`, the same
  fault `flavoured` was retired for; no guard could catch it — Helen found it
  on a card); five aromatised-wine generics (#568; *"I would never write
  'aromatised wine' as a cocktail ingredient or generic, because it suggests
  some equivalence between the types where none or very little exists"*;
  `americano` added); `Punt e Mes` stays (The Ridgwell pours it AND Martini
  Rosso — the retirement had been proposed on a bad measurement); `pastis`
  retired as a consequence of the Swizzle becoming the Martinique Swizzle.
- **2026-08-31** — Four more, forced by the Death & Co batch: `apple brandy`
  (Laird's Bonded is an applejack, not calvados, so named after the FRUIT);
  `Becherovka` (Helen: *"'Herbal liqueur (Becherovka)' would be misleading.
  This will come up over and over and I don't know what to do about it."* —
  it never renders that way; when nothing generalises a bottle, the bottle
  IS the generic; her *"cinnamon- or ginger-forward"* went in a note; its
  `warming` entry executed a standing instruction — `taxonomy.yml` had said
  since 08-30 *"Becherovka is the third and the collection has none; add it
  here the day a drink does"*);
  `cucumber` and `kaffir lime leaves` bare (*"will need to go in the
  dictionary naked."*). "Pernod" names two bottles and misled twice in two
  days; Helen pours the absinthe.

- **2026-09-06, #594 / #593** — **Syrups: type + ratio, only where the
  difference is real** — the rum-styles test, not a cane/demerara/turbinado ×
  1:1/2:1 cross-product. The issue's premise was already half false: cane is
  declared at both ratios (`cane sugar syrup 2:1` ×34, `1:1` ×5). Three gaps
  ruled on — `demerara sugar syrup` (×4) gains a ratio; `turbinado sugar syrup
  2:1` is declared, closing #593 and retyping `sapins-swizzle`; `honey water`
  settles on the `2:1` form (split 5/2 for the same thing). **And the 43 QQ
  notes are stale in their own right**: they read `Cane sugar syrup -> sugar
  syrup 2:1` where the files say `cane sugar syrup 2:1` — the right-hand side
  was never updated when the vocabulary gained the type, which is why #728's
  largest block reads as 43 open questions when it is 43 confirmations.
- **2026-09-07, #594 / #593 — built, and the honey-water half of the entry above
  was WRONG.** It says honey water "settles on the `2:1` form". Measuring the
  five drinks on the bare generic showed they **contradict each other**, and one
  of them settles itself: `chartreuse-daiquiri`'s own note reads *"Honey water is
  equal parts honey and water"*, which is 1:1. Helen ruled the other four to 2:1
  and that drink keeps its 1:1. **A ruling taken on a summary is only as good as
  the summary** — this one would have overwritten a fact the drink already
  stated, and the fix was to measure before applying rather than after.
  - **Two QQ notes were citing a fact that does not exist.** `brown-derby` and
    `green-flash` justified their 2:1 as *"taken from Airmail, which Helen typed
    2:1 by hand"*. Airmail carries no ratio at all and has no notes. Deleted.
  - **29 QQ notes named a generic no drink has.** They read `-> sugar syrup 2:1`
    where every file says `cane sugar syrup 2:1`: the right-hand side was never
    updated when the vocabulary gained the type. Rewritten, and verified by
    parsing every drink afterwards — zero notes now claim a generic its drink
    does not carry. **The check that found it generalises**: compare a note's
    stated value against the file's actual data rather than reading the note.
  - **`blue-hawaiian` and `georgetown-punch` had the arrow backwards.** *"Coconut
    rum -> Malibu"*: the generic is `coconut rum`, which the source states and
    which is not inferred at all, while Malibu is the `suggestion` and IS a
    guess. The note hid the real inference behind a false one.
  - **`demerara sugar syrup 2:1` was what `costs.yml` had assumed all along** —
    its `basis` string already read `"demerara @ GBP 1.80/kg, 2:1"` while the
    generic carried no ratio. The pricing was ahead of the vocabulary.
  - **`honey water 1:1` had no price and no ABV row**, because nothing had ever
    used it; `test_every_priceable_pour_has_a_price` and
    `test_every_counted_pour_can_reach_a_strength` both caught it the moment
    chartreuse-daiquiri moved. Priced at three quarters of 2:1 — the ratio is
    honey:water, so 2:1 is two thirds honey against 1:1's half, and honey is all
    of the cost.
  - **A non-question I raised as a question, and the correction is the useful
    part.** I asked Helen whether `turbinado sugar syrup 2:1` should join
    taxonomy's `aged:` list, describing it as "a flavour mood" that would change
    `sapins-swizzle`'s derived moods. **Both halves were wrong.** `aged:` is not
    a mood at all — it is a `mood_ingredients` set feeding ONE mood, `strong
    brown drink`, whose rule was rewritten on 2026-08-30 precisely to stop
    firing on "a swizzle over crushed ice" and now reads *"nothing lengthens it
    and it is not crushed, swizzled or blended"*. Sapins Swizzle is a swizzle,
    and is the only drink pouring turbinado.
    Helen's answer was the right one: *"Turbinado is just a sugar... It's just a
    flat ingredient. Does this matter?"* **Measured rather than argued**: adding
    turbinado to `aged:` and re-running `scripts/derive_cocktail_moods.py` gives
    `124 drinks: 124 already agree, 0 differ` — identical to leaving it out. It
    is in `sweet:` only, and that is correct.
    **The lesson: run the derivation before asking whether a vocabulary change
    moves a mood.** The script is committed, defaults to a dry run, and answers
    in seconds; a question costs Helen more than the measurement does.
- **2026-09-06, #781 over #780** — **Overproof first, in the generic and the
  card name both.** The two issues contradicted each other and needed a ruling:
  #780 said the card name *"can remain"* `Demerara overproof rum`, #781 said
  update the card names to the Overproof-first order. #781 wins. So `overproof
  Demerara rum, lightly aged` → `Overproof Demerara rum`; `overproof Jamaican
  rum` → `Overproof Jamaican rum`; `blended overproof rum` → `Blended overproof
  rum`. #780's `, lightly aged` survives — only the card-name half was in
  conflict.

  **Built the same afternoon by a parallel session (#786), and it resolved the
  one risk this ruling carried.** Offered the chance to keep `unaged` on the
  Jamaican, Helen took the plain form — but Wray & Nephew is unaged and Smith &
  Cross is not, so dropping the word would have collapsed a real distinction.
  The build kept it **in the generic and dropped it from the card name only**,
  which is the shape that loses nothing:

      "overproof Jamaican rum, unaged"   -> "overproof Jamaican rum"
      "overproof Demerara rum, lightly aged" -> "overproof Demerara rum"
      "blended overproof rum"            -> "blended overproof rum"

  **The general lesson, and it is why the generic/card-name split exists**: a
  card name is free to be shorter than the generic, so a naming ruling about
  what the CARD says never has to cost the data a distinction. Reach for the
  split before accepting a lossy rename.

- **2026-09-08, #848** — **A shopping SHELF is not a taxonomy, and gets its own
  map.** Helen: *"for cocktail shopping list, list items in shelf order then
  volume"*, with her own order; `fortified` was added on her ruling the same
  day, because her list had nowhere for vermouth and vermouth is in a lot of
  drinks. `fresh produce` followed on her first reading — it was the soft edge
  of the first cut, where a pear, a cucumber and a sprig of mint sat under
  `flavourings` with the olive oil and `flavourings` was carrying 24 rows
  against every other shelf's handful.

  **`shelf_of` rather than more columns on `family_of`, because they disagree on
  purpose in three places**: an amaro and a herbal liqueur are different
  FAMILIES and one shelf; champagne is `fortified` by family and sits under
  `tops` because that is what you do with it; the dry sugars share a shelf with
  the syrups because they do the same job in a drink. A family says what a
  spirit IS, a shelf says where you find it.

  **All 153 generics in use are placed, and the mapping was DERIVED**:
  `top_up_ml` gives the tops, `juice_yields` the squeezed juices, `family_of`
  the spirits and fortified wines, name rules the rest. The 38 left over are
  named one at a time in the generator with a reason each — chiefly that
  absinthe and Ceylon arrack are base spirits with no `family_of` row, and that
  a case-sensitive rule missed the capitalised Curaçaos.

  **`dried apricots` stayed in `flavourings` while `lemon zest` moved**: dried
  fruit is a dry good, and what you buy for a zest is a lemon.

  **No guard yet that every generic in use has a shelf**, deliberately: an
  unshelved generic sorts to the END rather than breaking anything, and a
  pytest-less container is the wrong place to ship a test that stops the deploy
  if it is wrong. Noted on the issue.

### §9.3.2 The bottle dictionary

- **2026-09-07, #591** — **An agricole's origin goes on the BOTTLE, as
  `origin:`.** Helen's choice from three shapes: origin-qualified generics
  (`Martinique agricole blanc`), `origin` on the bottle, or `origin` on the
  ingredient. The fact that framed it: **origin is already inside five of the
  fourteen `rum_styles`** — `aged Demerara rum`, the three Jamaicans, and
  `clairin`, which is Haiti-specific by definition — so agricole was the one
  cane family that stopped halfway. And the house owns **eight bottles under
  `rhum agricole blanc`**: five Martinique, three Guadeloupe (the Damoiseaus),
  with Barbancourt sitting in `vieux` behind a comment saying it is Haitian
  because no field could.

  **The accepted cost, stated so it is not rediscovered as a bug**: a recipe
  cannot REQUIRE an origin. `martinique-swizzle`, `island-of-martinique` and
  `lisle-martinique` are all named after a place none of them can name in
  `generic:`; what makes them Martinican is their `suggestion:` list, and the
  bottle dictionary is what says those bottles are Martinique.

  **What it settles for free**: `coffey-park-swizzle` and `port-au-prince` stop
  being mis-typed. Both pour Barbancourt as `rhum agricole vieux` behind a `QQ`
  admitting the guess — and under this ruling that typing is *correct*, because
  agricole is what the bottle is by production and where it is from lives
  elsewhere. Two notes to delete rather than answer.

  **Two mechanisms for origin now coexist deliberately**: in the generic where
  it changes the CATEGORY (Demerara, Jamaican), on the bottle where it changes
  the FLAVOUR (agricole). The five existing styles are not being unpicked.

- **2026-08-27, #529** — Added, rum-only. Planteray canonical, Plantation an
  alias.
- **2026-08-30** — Not rum-only any more, and neither are the two tests that
  made it worth having: 54 of 91 suggestions had resolved to nothing with no
  test minding. Helen: *"are we now assuming every named bottle should be in
  it, and classified? That feels right to me."* The session declared 43
  bottles by deriving the category from the ingredient beside them before
  Helen stopped it: *"keep only what the collection already spells out; hand
  me back the rest."* One was outright wrong (Pernod declared an absinthe),
  nine were fragments completed from memory. `unresolved_suggestions` born:
  34 that day, 30, then 16 on 2026-09-02, empty 2026-09-04. "A brand is not a
  bottle" (Briottet beside six generics; *"Briottet creme de peche is the
  bottle, that's its name"*).
- **2026-08-30, #534** — A suggestion whose bottle sits in a different
  category than the generic must carry a `note`, and `QQ` counts — Helen:
  *"be permissive with the test, but given we're pre-first-human-read please
  add the note field with QQ in it if we don't have anything else."* Its first
  run found four of six were #314 rulings not yet applied rather than
  substitutions; Helen dropped those four suggestions, knowingly leaving
  hurricane-classic and tiki-max on `Demerara, aged` against items called
  navy rum (reversed by the #542 rulings above). The feature, in Helen's
  words: *"a recipe might call for cherry brandy, and I suggest Cherry Heering
  OR Briottet cerise even though that's a cherry liqueur not a brandy, leaving
  it to future Helen to choose what kind of drink I want at the time."*
- **2026-09-02, #585** — A bare brand is not a bottle: `Planteray` names
  four products, `Bulleit` a bourbon and a rye. Helen chose `Planteray 3
  Stars` and `Bulleit Bourbon`; never add the bare name as an alias. Jack
  Daniels is a bourbon — the session had offered it as "Tennessee whiskey, a
  different legal category" and was wrong; Helen: *"It meets all the legal
  requirements for being called that, and their own decision to apply a
  further qualifier on top is... vain!"* Royal Bermuda Yacht Club's `ED3,
  Planteray` split and resolved, whereupon #534 fired — Helen widened the
  generic to a disjunctive pair (*"the generic wants two categories. Both
  make excellent drinks, just quite different ones"*). Seven
  `unresolved_suggestions` rows named strings no drink said any more; both
  registries gained a staleness guard.
- **2026-09-04** — `unresolved_suggestions` emptied: Helen went through every
  synonym line by line (*"I never want to have these conversations more than
  once"*). Rulings: a house is not a bottle (declare the product, retype the
  drink; Luxardo → Luxardo Maraschino, Bob's → Bob's Peppermint Bitters as
  the only house aliases); a spirit type beside its own generic is not a
  suggestion (aguardiente, kirschwasser); a syrup's suggestion may name what
  it is made from (*"Acacia is a bit special"*); `flavoured vodka` retired
  for `vanilla vodka` / `pineapple vodka` (*"members aren't substitutable"*);
  `lavender bitters` → `lavender-forward bitters`; `bonded rye`/`rye` and
  `dry orange Curaçao`/`orange Curaçao` stay distinct; leave the drinks as she
  wrote them and add aliases. Twenty-three bottles declared, thirty-three
  drinks retyped. Same day, from `to-promote/fish-house-punch.md`: every
  suggestion in the published tense is the CANONICAL name (*"'ED3' isn't a
  bottle"*; nine retyped) and no staged drink carries `item` (*"This has
  'item' everywhere too."*; ten went, four facts survived into notes; Patrón
  Reposado, undeclared, went in a note and the suggestion was left for her).
- **2026-09-05** — Bottles Helen NAMES are hers to add and always were:
  *"Rooster Rojo Tequila Anejo, Rooster Rojo Tequila Reposado, Patron
  Reposado, Patron Anejo -- all need diacritics"*. Five bottles moved to
  `not_reached_for` with reasons (*"the three Lows I skipped, let's remove
  them from the collection please"* — Anchor Junipiero and Ottoman 10 Year
  Tawny among them); Pierre Ferrand 1840 was never a separate bottle and is
  an alias of Pierre Ferrand Ambré. The dictionary went 107 → 130 → 127.
- **#701** — One declared name per bottle: `Ophir` (Opihr) and `Amaro
  Ciociano` (Ciociaro) are misspelt in `bottles.yml` and are not corrected in
  `abv.yml` alone, or the files would disagree.

- **2026-09-06, #701** — **Every drink writes the full declared bottle name.**
  The editorial question this was blocked on — a `suggestion` renders verbatim,
  so El Presidente reads `(ED3 or Havana 3)` — is answered against shorthand,
  and against a display field. Re-measured by parsing all 124 drinks, the
  issue's table is stale in both directions: **129** declared bottles not 77
  (127 before the rum-reference work of #786 landed the same afternoon),
  **264** mentions not 216, **27** alias-only spellings not 19, and **zero**
  unmatched not 16 — `unresolved_suggestions: {}` since 2026-09-04, which is why
  #585 closed into this. The drift guard is the part that lasts:
  `test_every_suggested_bottle_resolves` tests resolution **through aliases**,
  so it can never catch a drink writing `Havana 3` forever.
- **2026-09-07, #701** — **A BOTTLE rename and a GENERIC rename are different
  operations, and neither is a simple find-and-replace across two repos.** Both
  of #701's last two names were fixed on this day — `Ophir` → **Opihr** (the
  product is Opihr Oriental Spiced) and `Amaro Ciociano` → **Amaro Ciociaro**
  (Paolucci, Lazio). They needed opposite handling.
  - **A bottle has aliases; a generic does not.** `bottles.yml` keeps every old
    spelling as an alias, so nothing fails to resolve. `ingredients.yml` has no
    such mechanism — `family_aliases` maps FAMILIES, not generic names — so a
    generic rename has no safety net at all.
  - **Hence the two-spellings-at-once transition for the generic.** The drink
    (`to-promote/brooklyn.md`) lives in the private repo and the vocabulary in
    the public one, and **the two cannot land in one commit**. Declaring both
    `Amaro Ciociano` and `Amaro Ciociaro` through the gap is what keeps the
    suite honest; the old one comes out in a later PR. Helen chose this over
    accepting a red window.
  - **THE BOTTLE RENAME HAS NO SUCH ESCAPE, AND THIS IS A NEW COST OF A GOOD
    TEST.** `test_every_suggestion_is_the_declared_bottle_name` (added
    2026-09-06) requires a suggestion to EQUAL the declared key rather than
    merely resolve through an alias — which is exactly its value, and it makes
    a bottle rename a **two-repo atomic operation**. Both orderings are red:
    `key Opihr / drink Ophir` fails the guard, and `key Ophir / drink Opihr`
    fails it too. No single-repo step stays green. The window is local-only (CI
    has no drafts, so the test skips) and the mitigation is merging the pair
    back to back. **A plan that claims otherwise is wrong** — this one did, and
    the guard caught it on the first full run.
  - **Not a design question, and I twice said it was.** `Amaro Ciociaro` was
    described as possibly wanting to be a declared bottle. `ingredients.yml`
    already answers that: it sits in `amari:` beside Campari, Aperol, Cynar,
    fernet and Amaro Nonino, all generics named after single products with no
    bottle entry, because *"swapping Campari for Fernet is a different drink,
    not a variation."*
  - Helen priced it the same day: *"Amaro Ciociano is £36"* — £51.43/litre,
    and one of the last `confidence: low` rows in `costs.yml` becomes `high`.
- **2026-09-06, #702** — **#701's rename does not fix the `JM` alias, and must
  not be allowed to close it.** Retyping `cobra-effect` to `Rhum JM Ambré`
  leaves the bare `JM` alias resolving to one of two stocked bottles in
  different categories, so the next ingest that photographs a JM bottle walks
  into the trap with the issue closed. Delete the alias in the same commit.
- **2026-09-06, #782** — **Sipping bottles are declared, with a flag.** Twelve
  rums, two of them mixing (Pusser's 151, Ceylon Arrack) and ten sipping. Asked
  whether a spec of what a recipe may reach for should hold bottles no recipe
  will pour, Helen chose all twelve, with the ten marked so no recipe suggests
  them and no cost or ABV pass treats them as pourable. **Built the same
  afternoon by a parallel session (#786), and in a better shape than the flag
  this ruling imagined**: a separate `sipping:` list, whose members are not
  bottles as far as the site is concerned — no generic, so no card can name one,
  and no row wanted in `abv.yml` or `costs.yml`. That answers the open question
  this ruling left about `test_every_declared_bottle_has_an_abv` by removing it
  rather than exempting anything. Pusser's 151 and Ceylon Arrack are declared as
  real bottles; Pusser's 151 does **not** fill #750's `overproof Demerara rum`
  hole, being a Guyana/Trinidad blend.
- **2026-09-06** — **`La Favorite`, no `u`, is a STANDING CORRECTION.** Helen:
  *"Favorite is correct, my mistyping, please always correct."* The distillery
  is Martinican and spells it the French way; `La Favourite` was hers and
  reached the data before the correction did. Briefly visible as a
  contradiction when #786's `sipping:` list landed spelling it correctly beside
  three bottle keys spelling it wrongly — **fixed the same afternoon by #788**,
  which renamed all three keys and **kept `La Favourite` as an alias on each**,
  per this file's rename rule: a suggestion typed the British way must keep
  resolving whether or not the drink that wrote it has been retyped. That is
  the shape every one of these takes, and it is not a half-finished rename.
  `Ophir`/Opihr and `Amaro Ciociano`/Ciociaro are the same class and are
  **still outstanding**, under #701.

### §9.3.3 The drinks index's search

- **2026-08-29/30, #579** — `cocktail-index.js` (428 lines reusing nothing)
  became wiring; the search a pure module. Food's asymmetry adopted: fuzzy to
  find, exact-or-family to exclude — before this `gin` hid twelve drinks whose
  only gin-shaped ingredient was ginger and `apple juice` matched fifteen with
  PINEapple. Four bands in Helen's order: *"It should be prefix matching of
  first word, prefix matching of any word, then prefix matching of any word
  in the bottle name, then substring."* Five passes over three sessions on
  chips that could not explain themselves (*"'el' returns both 'aged rum' and
  'jamaican rum', which is counterintuitive"*); a sweep of all 676 two-letter
  queries — possible only because the module is pure — found 25 more via
  connectors (`an` → Smith AND Cross). The connector half is narrower than it
  read for two days: `and` is deliberately not a prose word (Wray and Nephew).
- **2026-08-31, #603** — The answer that held: **a chip found through a name
  it does not show carries that name.** Helen typed `mu`, `sa`, `wr` and got
  `clear blended rum`, `cachaça`, `Jamaican overproof rum`; four candidates on
  a dev page; she picked. Three shapes (its own name; a containing name
  alone; a bracket), the bracket in whichever spelling carried the query
  (canonicalising it gave a bracket with none of the typed letters — #603
  arriving through its own fix). 15 of 27 card names are strict abbreviations
  of their generic.
- **2026-08-31** — *"I do want to be able to type 'el d' and see el dorado."*
  A multi-word query matches a hidden name from its start. The umbrella
  suppression (#51's rule) ported: Helen was sure it was a food rule and was
  told it was not, on a measurement that called the module while the rule
  lives in `filters.js` at render time (§12). One chip per category wearing
  the card's name (eleven of fifteen pairs selected identical drinks); a
  bottle is a way IN (14 of 15 pairs strictly nested; pool built per
  ingredient from `data-ing`).
- **2026-08-31, #584** — Three characters: at two, 31% of queries overflow the
  cap of 8; at three, 3%, median 2; four buys 2% for a keystroke. The first
  measurement was taken with the new minimum already live and reported a
  tidy zero — lift the thing under test before measuring it. `whisk(e)y`
  label — *"even though it's clunky, to avoid ever having to split or claim
  they combine."* The alias gap closed (search reads `bottles.yml`: 240 pool
  terms → 142); hidden terms went through the same door the same day, the
  canonical name joining rather than replacing (`ED3` shares no letter with
  `El Dorado 3`).
- **#580** — `not_on_cards` keeps bare `water` off a card and out of the
  search: *"never write 'water' on a cocktail card and never return it in a
  search"*.

### §9.3.4 Units of alcohol — #297, built 2026-09-06

- Helen: *"I want the number of units in a drink, not the ABV of the drink,
  i.e. water etc don't matter."* — why it was a week and not a month.
  *"local-only now, and I'll note what publishing would need."* Placement:
  *"Only in the bottom section with source and cost, so the line below
  those."* ABV cannot live on a category (the rum categories are appellation
  and production categories — #314 says so outright: *"`moderately aged` says
  nothing about strength."*; Pusser's Gunpowder 54.5%, Gosling's 40%, same
  category; Helen's own reclassification of Smith & Cross: *"it is aged, so
  the unaged overproof style was never right. 57% is what made it look like
  one — and strength is not what that category names."*) and not in `bottles.yml` (127 numbers interleaved with 900 lines
  of rulings), and not in `costs.yml` (a price decays, a strength does not).
  Dashes: asked, and she chose the same rule as costing. The web pass
  corrected three figures (Suze 15 → 20 in the UK; Clairin Communal 53.5 → 43,
  it is the blend; Boudier Crème de Menthe 18 → 21). Seventeen `qq:` rows down
  to eleven. Three data faults found on the first run (#752): Ti' Punch's 15
  ml of rhum in a 35 ml drink, Pic-A-De-Crop's 360 ml of 57% into 675 ml, the
  pear Bellini with no alcohol recorded at all.

### §9.3.5 What a drink costs — #547, built 2026-09-05/06

- Helen: *"I only want to show price on the locally built site, and only as an
  incidental — just somewhere on the recipe page."* Her original framing —
  *"adding costs to each bottle in our dictionary"* — would have priced a third
  of each glass; the four most-poured things are juices and syrup.
  `default_bottles`: *"Don't name these on the recipes, but you can note them
  as inputs to the default prices."* What is not counted: *"None of these
  come into the estimated cost. I'm catering for family, not running a bar."*
  `to top` back in as a range: *"We can calculate top volumes, well,
  slightly, can't we — I'd like that to be captured actually so it can be
  added into the shopping list feature."* A range, her choice over a single
  figure; squeezed juices reuse #546's own `juice_yields`. Per glass, not scaled — fixed 2026-09-06 after shipping the
  opposite: *"When I scale, the price per glass you calculate needs to divide
  by the scaled number."* The price-check loop that worked: rank bottles by
  SPEND, hand her the order with a confidence flag; two rounds took 31
  checked rows to 44 and 16 guesses to none. Master of Malt 429s every
  automated request. Median glass £3.16–£3.39; 122 of 124 show a figure.

- **2026-09-06, #748** — **Whole fruit and weighed solids are priced.** *"I'm
  catering for family, not running a bar"* excluded dashes, garnishes and ice
  and still does; what changes is that a solid which **is** the drink is no
  longer treated as a garnish. The Pear, Apricot and Rosemary Bellini costed at
  7p under the volume-only rule and so printed nothing at all; about ten rows
  (pear, dried apricot, passion fruit, blackberry, cucumber, pineapple, and the
  sugars and honey by weight) make all 124 price. **The file's rule becomes "a
  volume or a weight counts; a dash, a garnish and ice never do"**, which is a
  subtler line than `costs.yml`'s header currently draws and should be written
  there when this lands.

- **2026-09-07, #818** — **The shopping list's bottle choice is per drink, not
  once for the whole list.** Asked which, given a generic with several declared
  bottles: *"per drink"*. So two drinks that both pour a reposado may choose
  differently, the buttons sit on the drink's own line, and choosing collapses
  that line's range to the chosen bottle. The range stands until a choice is
  made.

### §9.4 / §9.4.1 / §9.5 Decided, canon, settled apparatus

- **2026-08-16** — Ingredients are additive, never a choose-one (asked
  directly: guessing wrong would have shaped the whole model). Store the
  quantity both ways — REVERSED by #571, 2026-08-30. `to_serve` is
  presentation. Both brand and generic stored.
- **2026-08-17** — The site is canon: *"With iPad in hand, I'd rather take the
  site as canon, then happily break rules from there."* Modelling adjustable
  sugar (a range, a tolerance, an "approximate" flag — the ratios were stated
  on 2 of 27 entries) was a real proposal and was declined: a page that hedges
  is no longer a reference.
- **2026-08-23** — A goodness-only filter built in twenty minutes (§9.9 below).
- **2026-08-29** — `meta.status` retired; its only consumer was `chaos`'s
  "haven't tried" bucket. `test_cocktails.py` stopped skipping wholesale
  without drafts (§10, #540).
- **2026-08-31** — §9.5 retitled from "Open, and worth deciding out loud":
  nothing in it was open, and a section promising open questions to a reader
  looking for them is worse than no section. `garnish: []` vs "none" closed
  in §9.12.1.
- **2026-09-05, #722** — `meta.made_before`, a boolean, gates nothing, first
  in `meta:`. `QQ` retired from `ship`: an unmade drink says `who knows`
  (*"I think that's clearer than QQ or leaving it unset, because it's a
  positive presence"*). An unmade drink MAY publish — *"there's no prose
  except the tagline which I will always write from scratch, so no copyright
  or author respect issue. It will be much easier for me to browse drinks I
  want to try from the live site than a local build."* This retired two
  publish gates (`test_every_published_drink_names_a_rung_on_the_ship_scale`,
  `test_every_published_drink_has_been_made`), the second never asked for.
  20 of 124 say `false`; the other 104 `true` by inference from #722's own
  premise (a rung is a verdict, a verdict means she drank it), the 22 she
  ruled on being the ones where the inference did not hold. She said she did
  not require the `???` front-end feature; it was built the same day
  (`ship_unrated_word`) — the handover called it unbuilt until 2026-09-06.
  `_dev/no-verdict.html` is the worklist.
- **2026-09-06** — `ship_tints` deleted from `taxonomy.yml` with
  `test_every_ship_rung_has_a_tint`. Nothing had read it since the card's
  tinted square became a ship and a word (2026-09-02), and the one reason for
  keeping it — #511 and #612 wanted a graduated goodness scale on the DRINK
  page, and the ramp's shape was the argument that scale would need — lapsed
  when both closed on 2026-09-02 with the page showing the rung word instead.
  The ramp was `not really` 0, `meh` 16, `sure` 42, `yes` 100, `oh gods yes`
  100, `who knows` 0 — deliberately not linear: `yes` and `oh gods yes` both
  full because both mean "make this"; `sure` and `meh` were 62 and 30 for one
  afternoon, and at 62 a `sure` was mistakable for a `yes` at a glance. The
  square's border never changed at any rung (an empty square reads as rated
  low; a faded one as not rated, which `who knows` holds separately), and it
  sat AFTER the label so its position did not depend on the word's length.
  Read it as an argument if a graduated scale is ever built.

### §9.7 / §9.8

- **2026-08-16** — Liquid parses tags inside `comment`; `source: ""` drew a
  bare "Source:" line on all three drinks.
- **2026-08-15, #223** — Cocktails at PARITY with food's tape, copying across
  as part of regeneration — after the two directories drifted for five days.
  OVERTAKEN 2026-08-19 by #374: one directory.

### §9.9 The goodness filter, and the vocabulary that outlived it

- **2026-08-23** — Built in twenty minutes from `meta.ship`'s existing words
  ("oh gods yes" was on 18 drinks). Its template hardcoded its own ordering
  string while the `meh` collapse landed in a different, unmerged PR the same
  day: 17 drinks would have sorted dead last the moment both merged, each
  branch green in isolation, caught only by rebuilding the combined state.
- **2026-08-26** — Replaced by §9.13's designed index; `_goodness.scss`
  deleted. Section cut 2026-08-29.

### §9.10 / §9.10.1 The ingredient line and the card names

- **2026-08-27, #501** — The card had rendered `item`, and the problem was
  ambiguity, not length: `Overproof Navy rum` named three different rums,
  `White rum` two. `card_names` added. Helen, with `El Dorado 12 year old rum`
  → `Demerara rum` in front of her: category ALWAYS, even where the recipe
  names a real bottle. Her names say the spirit word out loud (`filtered rum`
  → `lightly aged rum`), so two card names are LONGER than their generic — a
  first test asserting brevity was wrong within a day; the guard became
  aggregate (`test_showing_categories_still_shortens_the_index`: 39 shorter, 4
  same, 19 longer, median −8). Both Jamaicans collapse to `Jamaican rum`
  (declared in `card_names_may_collide`); both Demeraras and both agricoles
  keep their names. Swizzle's pair is `Demerara rum or overproof`
  (`card_name_joins`; *"I expect we'll need an explicit mapping of cases like
  this"*). Two pours of the same rum print twice (*"where a recipe wants
  more than one kind of the same rum we obviously should write the display
  name twice"*). `character` only on the recipe; #530 (`hogo`) the follow-on.
- **2026-08-29, #544 / #513 / #558** — The drink page's line is the generic
  with the bottle in brackets (Helen's example: `London dry gin (Beefeater)`).
  `item` does not render: 385 of 617 item/generic pairs restated one another.
  `character` gets a line, not a parenthetical (#441's ban on the bare form
  stands). Card names renamed from rum-only maps; Ceylon arrack the first
  non-rum member (*"is that a rum? Doesn't matter, the category list should
  eventually contain everything"*). The three brand-generics' card names went
  descriptive — lowercasing surfaced `o.f.t.d.`; a reader had met `O.F.T.D.`
  among `gin`, `cognac` and `sugar syrup` and learned nothing (#556 exactly).
  Cards are lowercased in CSS, not markup (#543/#553): the 37 surviving
  capitals were all real proper nouns. The search pool dropped `item` (380 →
  239 terms). The card falls back to the generic, never to
  `item`.
- **2026-08-30** — #544 promoted 61 bottles out of `item`; coverage 18% → 29%.
- **2026-09-02, D8** — `item` is a draft-only transcription field, not
  retired: *"ignore everything in `item` as we'll throw it away."* Reversed
  the "retire it" sentence that stood for a fortnight, on the right grounds:
  the field was never the fault, the rendering was.
- **2026-09-03** — Ten restating entries deleted; 111 not, because a
  SUBSTRING test would have deleted brands (`Tanqueray London dry gin`). The
  residue tabled for Helen in `tmp/item_census.md`.
- **2026-09-04** — The deadline moved to the staging folder (§9.3.2 above):
  "promotion is the deadline" was in the wrong place, because a drink only
  reaches `_cocktail_recipes/` by being moved.
- **2026-09-04** — Which surface reads `card_names`: *"Let's display the full
  name in the ingredients list please, just the short name on the card."* The
  layout was already doing it; the paragraph describing a DERIVED "cane sugar
  syrup, 2:1" with a comma had described something that never existed.
  §9.10.1's "substitute only when every generic has a card name" rule was a
  design that was discussed and not the one in the file (corrected
  2026-09-05).
- **2026-09-05** — `item` gone from every pour, and ENFORCED
  (`test_item_is_gone_once_the_generic_is_filled_in`). Helen: *"we agreed to
  drop item, but then I was persuaded to allow it back as somewhere to hold
  incoming data, but it's become a dumping ground again."* Of 204 fields at
  the end, 165 redundant; 39 named something the repo did not know; **23 were
  real bottles existing nowhere else** (Elijah Craig 12, both Lustaus,
  Barbadillo Principe, Bitter Truth Aromatic, Anchor Junipiero, Massenez
  Kirsch Vieux, King's Ginger, Combier, Courvoisier, Pierre Ferrand 1840,
  Kahlua, Passoa, Ottoman 10 Year Tawny, Ketel One, Giffard Crème de Mûre,
  Liquore Strega, Bénédictine D.O.M., Galliano L'Autentico, Patrón Reposado,
  Ophir). Helen: *"All those bottles should be in our collection (possibly
  with some names tidied up)."* The plan of record had said delete. The drink
  page's line was gated on `item.item` and printed a raw hash when one was
  removed; fixed before any deletion.
- **2026-09-06, #567 / #640 / #691** — The card's ingredient line became a
  plugin; the 1,400-character Liquid statement doing four jobs could not take
  a seven-tier sort. Order: base spirits, lower-proof, citrus and juice,
  syrups, everything else, bitters; largest volume first inside a tier; the
  recipe's order breaks ties — Helen ruled the tie-break *volume, with a
  per-drink override* over "most typifying the drink", which would have been
  truer and needed a judgement on 124 drinks. `not_on_cards` to ten entries
  (*"don't include things like sugar, water. lemon zest in the ingredient
  list that appears on cocktail cards"*; `salt` was the tenth item on the Mai
  Tai's line). Tier 7 (floats) not built (#754). The `searchable` capture had
  been a near-copy of the card loop with a comment saying "the two must stay
  in step" and nothing making them.

### §9.10a `serve`

- **2026-09-05** — The ice had no field, so "strain" was written seventeen
  ways; collapsing 31 spellings to five surfaced three TRUNCATED steps nobody
  had read ("Fine strain into a chilled.", "Fine-strain into pre-chilled.",
  Chartreuse Swizzle's "Add to the."). Of 156 mentions of ice, 86 were the
  shaker's. `chill` existed for about an hour (`chilled` on 21 drinks) — Helen:
  *"I think it's implied that glasses should be chilled (except hot drinks
  obviously). I am the user after all."*; its `frozen` and `rinsed` values
  were each already a method step. She asked for the glass and the ice BACK
  in the method — *"I'd like to name the glass too where it appears"* — which
  is composition, not undoing the field. The rim before the ice — *"given that
  you can't sugar a rim once the glass is full, let's add that line
  earlier."* A garnish step closes the method — *"garnish is important, and
  it's easy to miss at the top of the page."* Is a garnish step a serving
  step? No: "To serve" is what happens to a finished drink. Gin Sour's
  `to_serve: "Without ice."` deleted. Pic-a-de-Crop Punch is the one drink
  left without `serve.ice` — a question for Helen, not a default.

### §9.11 / §9.11.1 / §9.14 / §9.15 / §9.16 Glass icons

- **2026-08-25, #298** — Sized by real height from `heights_mm`. `_dev/glasses.html`
  section 1 was stale for a day, still claiming equal heights.
- **2026-08-26** — Scale 2.6rem → 10.4rem when the glass became the drink
  page's hero; width cap moved in proportion. Goblet and mule-mug looked
  oversized on the uncapped dev page (mule-mug's drawing is 1.25:1). #347
  resolved by one fresh redraw: `rocks` a plain alias to `old-fashioned`; the
  double redrawn 2026-08-26 as the same body scaled up. `mule-mug.svg` became
  `mug.svg` — *"I actually use a mug for this like I do for tea!"*; the rename
  went into the normaliser's `RENAME` map, the edit that sticks. All three QQ
  glasses resolved (`todo`, `long` → `highball`; every swizzle onto highball);
  an unmapped glass is now likelier a typo than a decision, and #500 tracks
  the flag-only test.
  Root `<svg>` UA `overflow: hidden` found shearing rim strokes. Goblet and
  nick-and-nora redrawn with new bowl proportions (not #299 reopening).
  `heights_mm` unmeasured (#295 open); capacity-based scaling shelved for the
  same reason. Stem/base proportions parked: *"these graphics are the thing
  on the site that the least serves function over form... let's leave things
  as they are."* (#299). The canonical glass vocabulary became a RULE: *"I
  decided to go with old fashioned rather than rocks as the canonical name, so
  recipes that still have rocks are fine to break a test."* 17 drinks retyped
  at once, safe only because `rocks` was already one drawing (#347).
- **2026-08-26/27, #295** — `heights_mm` sizes the CANVAS: Helen's redrawn
  double old-fashioned drew 0.90× the single (75.7% ink fill) despite a
  1.29× viewBox. *"I created the coupe and goblet drawings by editing others,
  which will be how the height issue happened. I am not able to do anything
  other than this as I can't draw."* The normaliser fits the viewBox as its
  last step; it found goblet at 69.5% and the coupe — 40 drinks — 15% shorter
  than the highball it was declared equal to. The normaliser deleted all 26
  icons twice (an import running a bare `main()`; an empty gitignored inbox)
  — it refuses without input now.
- **2026-08-27** — Helen's Inkscape sources committed to `_design_sources/`.
  `/dev/glasses/` recovered a drawing from `git show` once (#484): the
  redraw-suffix convention and the `RENAME`/`SKIP` switch. #498: the tracer and
  rasteriser made permanent scripts (tiki mug: 103,817 ink pixels → 7,073
  skeleton → 46 strokes; a degree-based skeleton walk had returned 2,966
  fragments).
- **2026-08-27, #491** — `any` retired: *"when someone tells me to use an old
  fashioned glass I always automatically assume I can use any glass I like,
  so there's no need to have 'any' as a glass type."* Daisy de Santiago
  `[collins, any]` → `[collins]`.
- **2026-08-30** — Sixteen drinks named no glass; Helen named all sixteen in
  three sittings once shown the TOTAL VOLUME. A sling and a zombie glass she
  wants and does not own are notes, not data.
- **2026-08-31, #355, #599, #601** — Three fill-only glasses were traced and
  Helen stopped it: *"you redrew these three new ones, right? They're not
  right."* Published solid instead (an erode filter can thin ink without
  touching a path). Open stroke ends: *"I assume this is because you're
  drawing them with a different stroke width than when I edited the files,
  meaning my lines didn't quite go far enough."* — she closed 25 of 27 in an
  afternoon; a stub-appending wand closed 4 of 6 on the coupe and was not
  good enough; `old-fashioned-double`'s two largest gaps ruled correct as
  drawn; no guard, her call. #599: four icons nested a `matrix()` the parser
  dropped, so the coupe's bowl hung 11.8 units above its own canvas and was
  painted (`overflow: visible`); the clip-and-shrink-only fit was wrong on
  both halves and the creep it prevented was a property of measuring clipped
  ink. Card glass sizing settled at `/dev/card-glasses/` (#601): curve `ratio
  × 0.5 + 0.5` plus headroom 10.4rem (the reference glass had been 13rem in a
  12.9rem panel); Helen caught the drafting error of offering them as rivals
  — *"Is headroom plus compression an option?"* `display_scale`'s two entries
  came off (collins 1.74× → 1.34× the old-fashioned; collins and hurricane
  +7/+11 points, put to her with both numbers first). The dev page kept as
  the instrument, an exception to the comparison-switch rule.
- **2026-09-05/06, #650, #738** — The artwork re-judged on black: the drink
  page drops to stroke 2, the card keeps 1, the universe line 0.7; the curve
  untouched (*"I can't think of any reason why the glass scaling would need
  to be different"*). Helen redrew the pineapple, coconut and tiki mug as line
  art; the whole set is stroked (`glass_ink_coverage.py` is the number #525
  and #738 set redraw targets with); `check_glass_regen.py` written on
  2026-09-05 found the mug's hand-added filter divergence immediately, nine
  days after the instruction to check by hand was written. Three comments
  had said the card template "raises every ratio to a power"; it never had
  (§12).

### §9.12 / §9.12.1 Methods and garnishes

- **2026-08-26, #290** — `methods.yml` added: 277 steps across 105 drinks, 144
  distinct; one instruction 43 uses in three wordings, Strain in eleven. The
  census found three truncated steps, two typos, three notes filed as steps,
  four instructions split across two lines. Helen's design: *"Prefer both,
  leaving my original too, then I delete whatever I don't want."* — propose,
  never apply.
- **2026-08-31** — `garnish.yml` at Helen's request: 130 entries, 65 distinct
  strings, perhaps 35 garnishes; 55 after unambiguous collapse, 49 after her
  rulings. `none` → `no garnish` — *"'no garnish' actually, because none might
  read like 'not filled in' even though you and I know that's not the
  case."*; found because ti-punch already said it and the guard could not see
  it. A twist is a strip of zest; `12 raspberries` → `raspberries`; fake-id's
  `orange or lemon twist` — *"either of these are lovely and the maker can
  choose. I like this approach on principle."* The `proposals` guard asserted
  non-empty for one day and was wrong (§12).
- **2026-09-02, #630** — The methods pass done: 161 distinct steps → 146, 110
  canonical uses → 177, 24 proposals → 0; 65 steps across 64 drinks. The four
  QQ rows: `north-sea-oil` "Stir with ice." is step 1 → "Stir all ingredients
  with ice."; `sapins-swizzle` "Shake with ice." after a build — Helen
  *"should retain 'shake with ice'"*, now canonical; `caribbean-sazerac`
  "Shake the rest with ice." after a rinse — *"match please."*;
  `smokestack-lightning` "Fine strain with ice." into a `coupe` — *"'fine
  strain with ice' doesn't mean anything — I bet I meant 'fine strain over
  ice'."* — the GLASS was wrong, now `old fashioned`. "Stir with ice." not
  declared: no drink stirs after a build. This box was written twice from
  opposite sides of a merge, agreeing on everything but the count.
- **2026-09-04** — A "slot for ice pedantry" grew the strain group from
  eleven to seventeen — a vocabulary that keeps growing is absorbing a fact
  that belongs in a field.
- **2026-09-05** — Strain group to five (§9.10a). Garnish had absorbed pours
  ("3 dashes red creole-style bitters", "5 drops of olive oil"), a rim and a
  restated method step; each moved to its home. `pineapple wedge (cut to
  resemble a bird's plumage)` and five others were declared but not printed
  by the standalone document until the blocks were generated.

- **2026-09-08, #775 and #845** — **`easy peasy`, and what her three additions
  taught.** #845: *"any cocktail with equal parts of all ingredients (bar maybe
  bitters) should get the tag 'easy peasy' once we've made it"*, widened the
  same day to cover the short pour-and-stir drinks, which brings in the Negroni
  family.

  **Shown eleven candidates she answered: "All your 9 from 11 are right. Julien
  Sorel and Anita's are in too, and also Long Island Ice Tea."** Those three
  additions are the rule: Julien Sorel and Anita's are equal parts PLUS a
  sparkling top, and Long Island Iced Tea is EIGHT ingredients every one of them
  12.5 ml with only the cola different. **So a top or a mixer is set aside like
  a dash is, and the equal-parts branch carries no ceiling on the count** —
  Anita's is seven equal pours and she wants it in. The two unmade candidates
  are out, which is the "once we've made it" clause working.

  **A rule that could not see the faff was no use for a chip about faff.** The
  first pass counted only VOLUME pours and so called the Caipirinha and the
  Pear-and-Apricot Bellini easy — their work is a muddled lime, 20 g of palm
  sugar, a whole pear and four dried apricots, none of which is a volume. It now
  requires every counted ingredient to BE a volume and reads the method for
  muddle/infuse/cook/simmer/blend.

  **`moods_by_hand` IS THE TRAP, and it is silent.** A hand-applied mood missing
  from that list is stripped off every drink the next time
  `derive_cocktail_moods.py` runs, and `verify.py` runs it — so it reports as a
  diff rather than as an error. `easy peasy` is earned, not derived ("once we've
  made it" is a fact about Helen, not about the liquid), so it belongs there.

- **2026-09-08, #853** — **One mood can now cancel another: `mood_suppresses`.**
  Long Island Iced Tea carried `easy peasy` AND `I want to faff`, which say
  opposite things, and both rendered as chips side by side. Helen: *"LIIT is
  easy peasy, and this should suppress the derivation."*

  **Neither was wrong by its own rule**, which is what made it a vocabulary
  question rather than a bug. `I want to faff` is *"muddling, flaming, shells,
  blending, swizzling, or nine-plus ingredients"* — **five OPERATIONS and one
  COUNT, and the count is the odd one out.** It is a proxy for effort that holds
  for a tiki drink with nine things happening to it and fails for this one,
  whose whole method is "shake the first 8 ingredients with ice" and pour the
  ninth on top.

  **Suppressing rather than re-scoring is the cheaper correction**: the
  nine-ingredient rule stays exactly as it is for the 124 drinks it is right
  about. Her hand-applied judgement wins over a derived one, which is the
  precedence `moods_by_hand` already sets.

  **Declared in taxonomy.yml, not hardcoded** — §9.9's lesson is that the script
  must never keep its own copy of the vocabulary, and two mood names in a Python
  literal would be exactly that. **A one-drink `mood_exclude` entry would also
  have worked and was not taken**: she stated the rule about the MOODS, not
  about the drink.

- **2026-09-08, #852** — **Coney Park Swizzle is Coffey Park Swizzle**, for
  Coffey Park in Red Hook. Helen: *"delete the Coney Park one please, I remember
  this now."* Read as "the name goes", not "that file goes", because two files
  held the drink and the wrong one had the better content: an untracked
  `coffey-park-swizzle.md` was an OLDER revision — `oz` amounts with the retired
  `ml:` key, `item:` where the tracked file had `suggestion:`, bare-string notes,
  and **no gate flags at all**, so it would have failed the publish gate and
  reintroduced the only `oz` in 579 pours.

- **2026-09-08, #836** — **Nine of the eleven glass questions were already
  answered correctly, and the value of the ruling was DELETING THE NOTES.** Both
  sazeracs were already old fashioned, Between the Sheets a nick and nora, both
  martinis martini glasses. Seven QQ notes went; those notes RENDER, so
  "Double-check this one by eye" was the thing a reader saw. Two real changes:
  `martinique-swizzle` was still collins, missed by the 2026-08-26 sweep that
  moved "all four" swizzles, and `mastiha-mojito` lost its second glass.

- **2026-09-10, #894** — **An optional flame can make a drink `on fire`, and
  the Mai Tai's does not.** Helen: *"Yes in principle, but no for a Mai Tai."*
  So the derivation is not widened to read `to_serve`, `on fire` stays
  hand-assigned where the method does not set anything alight, and the Mai
  Tai's "Optional fire if tiki mug" is a serving note rather than a hassle.
  Recorded in `taxonomy.yml` beside the mood.

- **2026-09-10, #705 — the second census, and what `canonical:` could not
  say.** With 48 drinks live: 313 steps across 124 drinks, 119 distinct, and
  45 of the LIVE strings outside the dictionary. Three patterns were most of
  it, and only one was a missing group. **Short shake** (six wordings, four
  live) is a group now, "with three ice cubes" in every form because three
  cubes is the technique. **The exclusion tail** — "everything except the
  cola", "first four ingredients", "the first seven", "all the other", "except
  the bitters", "with three ice cubes, other than the soda water" — was one
  instruction differing only in WHICH ingredient stays out, which a flat list
  of literals cannot hold. **So `shapes:` exists**: a canonical sentence with
  exactly one `<X>`, filled with the ingredient as the recipe names it, and a
  filled shape is canonical wherever a literal is (`_is_canonical_step`,
  `test_every_shape_has_exactly_one_slot`, the preflight, the standalone
  document). One slot is the ceiling on purpose: two is a grammar. **Floats**
  ("on top" / "on the surface" / "on the top" / bare) went the same way.
  Helen's answer to "what rules do you want?" was *"If you can't Just Sort
  This out for me based on what it looks like I want then ask me questions"*
  — so the rules were derived from the data and put in front of her as
  `proposals` rows (31, four `QQ`), which is the mechanism she designed for
  exactly this: delete a row to keep the drink's own words. The literal
  champagne forms stay declared beside the shape that generalises them; they
  were first, they are exact, and retiring them is churn with no reader.

  **She pruned nothing and amended two, the same night** (PR #906: *"Rest
  fine, great, please amend."*): the Martinique Swizzle's build-and-stir is
  *"Stir all ingredients together."* — *"'Add all ingredients.' doesn't need
  to be a step on its own. I'd prefer something more concise"* — declared
  under `stir:`; and Sazerac (Death & Co)'s twist *"can be 'lemon twist
  (discarded)'"*, so the hand-written squeeze step went and the layout's
  express step took over. Applied as text edits to 12 live drinks and 16
  drafts; `proposals` is empty again. **The live drinks kept `proofread:
  true` on her grant** — asked how she wanted to re-proofread 48 drinks after
  a methods pass: *"Line by line. I can just grind it out."* — so
  `COCKTAIL_BASELINE_COMMIT` moved to the apply commit, in a commit of its
  own, and nothing left the live site for the review.

### §9.13 The visual language — the rounds

- **2026-09-10 — the family-weekend design pass, in one entry.** Helen asked
  for an unseeded opinion: *"Where do you think we can make material
  improvements in a day or so?"* Every page family was screenshotted at 360,
  390 and 1280 in a headless Chromium first (the container gained one that
  night, `tmp/browser/`, Helen's grant), and the list was ranked by what a
  visitor looking once would meet. What she ruled, in order:
  - **Chips clipped under the ship mark** (#760's mask read as words cut
    mid-word): *"you're right, and that's new this evening."* Fixed by
    measurement in `card-line-budget.js` — only a card whose last row reaches
    the ship gets padded clear — and the pass turned out not to have been
    LOADED since #846 (§12 has the trap).
  - **The drink head's void (#887)**: *"I'm not seeing the problem I had any
    more."* Closed.
  - **A line under the wordmark** (*"What shall we cook?"*): *"No words under
    the wordmark section please."* Declined.
  - **The engineering showing** (the "export list as JSON →" link): *"Okay."*
    Gone; the panel's summary reads in plain words and gained a **clear
    button with a second-click confirm** — *"we also need a 'clear shortlist'
    button somewhere"* — because the list is passed round a table on an iPad.
  - **The nav** became the door to the other site, §2 above.
  - **The drink page's controls row**: *"How about moving the read it make it
    to the left? I can imagine that feeling quite natural in the kitchen --
    I'll be on the left of the page looking at the ingredients list. Then top
    right for a save this feels more natural."* Toggle left, shortlist right.
  - **The drink page's top**: *"it now feels like there's quite a bit of space
    at the top of cocktail pages. Should the top bump up a bit, closer to the
    back arrow?"* The title block starts 1rem under the arrow, food's own gap;
    the arrow stays put.
  - **Left alone, on purpose**: the header's balance, the recipe page's method
    indent, the food index pills' faintness at rest, the chip type size on
    cards — each a settled call that reads as intended once you know it is
    deliberate, and none would change a visitor's evening.

- **2026-09-10 — the scaler grew two buttons, #731.** Helen's sketch: "-  [1]
  x  +". `−` (U+2212, not a hyphen) and `+` either side of the box, shipped in
  the same `hidden` wrapper so they reveal with it in one script pass. Coloured
  by the standing rule rather than a new decision: absinthe at rest — the home
  colour, already worn by everything else clickable on this page — and
  wicked-woowoo on hover, the hue this site keeps for "this one" the instant a
  pointer is over it (above, the 2026-08-26 entry and the accent table).
  Neither state touches the box's own size (#389's rule, generalised past the
  one selector it was written for — `test_no_active_filter_button_changes_its_
  own_width` reads only food.css's filter-button classes and does not reach
  cocktails, so this one is enforced by construction, not by that guard). Each
  click calls `apply()` in cocktail-scale.js — the exact function a keystroke
  reaches — as `apply(last ± 1)`, never a second arithmetic path, so the ×1
  floor and a refusal's note are the same code answering to both. Checked
  against real drinks: no written recipe can actually make that refusal fire
  (scale.js's own floor is capped at ×1, and the header's proof says why), so
  `tests/js/cocktail-scale.test.js` proves the wiring by patching
  `HTF.scale.scale`'s answer rather than assuming a dataset the floor can no
  longer produce.

- **2026-08-26** — One sitting with Helen against a mockup
  (`_dev/cocktails-design.html`, since deleted: eleven card framings, four
  hovers, six greens, five second accents, three thirds; a page of rejected
  candidates is #276's trap). *"Ink, paper and glass."* Horizontal card chosen
  over vertical and typographic tile for the ingredient line. Every anchor
  fixed — *"it's a shame to lose the card proportion but I can't think of
  another way."* Framing: a rule in the home green along the column's bottom
  edge, no vertical rule; hover brackets the column with painted strips.
  Helen asked for "a very subtle lightening of the white part" and it was not
  available — the card was already the brightest thing (reversed by the
  inversion, and the lesson kept: check which end of the range the surface
  sits at).
- **2026-08-27** — The six open questions answered: ordering (#478/#479, one
  question — OR within, AND between, more matches rank first; randomised
  once per load); chaos filters rather than sorts (#480); the empty state
  takes food's treatment value for value (#481); **print is the FULL page**
  (#482) — the expectation was confidently wrong the other way; two traps
  caught reading the built CSS (rules compiled to top level; the class is
  `btn-make`; #86's guard then failed honestly on `.is-making`, which comes
  from JS, and searches `assets/js/*.js` too now); narrow screens (#483) — *"are screens realistically going to be
  narrower than about 380px????"* Yes: 360 and 375 are the two commonest.
  #485 closed (the glass out of flow entirely).
- **2026-08-28** — On a card carrying three filled things: *"There's just a lot
  going on… underline the ingredient rather than highlight."* Bands and washes,
  not fills. A shared `darken(…, 22%)` put MOOD at 10.99:1 and HAS TO HAVE at
  3.61:1 — every pair is solved, not darkened by a shared step. Violet spent
  one revision on LEAVE OUT — "suddenly busy, and jarring" — colour weight
  tracks how much of the page something occupies.
- **2026-08-29** — Five accents, "neon bar sign" (one → three on 08-26 → five).
  Three measurements: five saturated hues avoiding food's six do not exist
  (the best set comes within 21°; saturation, not hue, separates the sites —
  ΔE 31 muted vs 15 neon); the dichromacy bar applies to exactly two of the
  five and was applied to all five first, costing two palettes; ultra-yvette
  cannot take dark text at all (3.14:1, nothing darkened clears 4.5). Helen
  rejected campari red and bitter orange as "too red-green and inaccessible"
  — simulation agreed (24.5 ΔE under protanopia against 101 normal). The
  names are the bottles (#555; `radiant-reposado` is arguably Aperol's hue
  and is her name). The five questions restructured (*"I feel like I am
  doing work to understand what to click in order to maximise my chance of
  getting the drink I want"*) — the page had asked ONE question and offered
  ten answers belonging to three different ones, and *"No juicing" is not a
  flavour and "I want to faff" is not a mood*: taste and style NOT split (*"honestly I think
  taste and style in those columns are the same, and should be called Mood.
  Splitting out Hassle though feels good."*); I KNOW WHAT I WANT last because
  *"I find browsing quick and inspirational… steer myself then read for a
  while then settle"*; YOLO had been backwards (the "try anything" button hid
  all 55 best drinks) — *"'I'm open to chaos'… includes all drinks, not just
  not-known-to-be-definitely-good drinks."*; LEAVE OUT with no hue at all —
  *"for food, avoiding can be important whereas for drinks surely less so."*;
  it reads drafts locally on her call — *"for food, we build drafts locally
  only, so let's do the same."*; the
  headings were outranked, not illegible (5.12:1, but `.btn-chaos` dressed as
  a heading). `tmp/neon_values.py` and `tmp/greens2.py` were named as tools and
  were gone; `scripts/palette_measure.py` is tracked now (2026-09-02).
- **2026-08-30, #452** — Nineteen moods, nine derived, ten Helen's. Four flavour
  tags proposed and killed: *"They're flat descriptors, which is fine in
  moderation, whereas I'd hoped for more evocative moods, you know, something
  I can offer beyond what one might guess from the ingredients list."* Every
  rule scored against her full pass over 114 drinks (IoU: no juicing 1.00,
  fruity .94, ice ice baby .88, warming .79, sharp .78, strong brown drink
  .76, I want to faff .73; clear .67, tiki .53, aperitivo .36, sugar craving
  .23 moved to `moods_by_hand`). `up` proposed and killed the same day — 51% of
  the collection; *"I'm not sold on up, let's retain it but with
  suspicion"*, and the suite reached her conclusion independently. Only four
  cases where a rule tagged something she did not. Thirty-one `mood_include`
  entries over looser rules, each relaxation measured (dropping `sharp`'s cap:
  fixes 9, wrongly tags 20). `fruity` changed: orange juice in, crème de
  banane out (nobody builds a sour on orange juice; the orange LIQUEURS
  tested and rejected). Fourteen mood buttons; `pudding in a glass` has two
  drinks (#337).
- **2026-08-30** — Index headings to five greens over a shared absinthe bar.
- **2026-08-31, #595** — Back-navigation restore on the drinks index, *"exactly
  as the food site does"*; cocktails restores SORT KEYS where food restores an
  array.
- **2026-09-01, #469** — Cocktails goes black-on-black; its heading values
  become what `.on-dark` had been solving for.
- **2026-09-02, #469** — *"One thing for sure: we're going black on black. I
  wear black on black animal print whenever possible. I have some black on
  black bed linen. This is what we're doing."* A card darker than the page.
  Every `-deep` and `-wash` re-solved; the emboss inverted — *"the wordmark
  text is weirrrrrd… I would like the same lettering you created for our new
  white on black headings."* — (`.site-logo-top`
  had hardcoded `#dad7d8` and half-opacity ink — two pale blobs on a dark
  ground; five values became custom properties, food byte-identical). The
  card title on punched tape: *"the boldness of the two near-whites with no
  softening shadow is exactly what we need."*; the band centred by moving the
  artwork after three rounds of compensating on the text; the geometry
  solved for the name's width (*"reasonably lengthed names of cocktails can
  appear on the one line"*); dropping the title 1.08rem → 1rem silently
  removed the deliberate 1.6px overlap onto the glass panel. Nine rounds, five
  spent on bugs in a hand-built replica of the card's CSS in a dev page
  (§12); Helen: *"the tape was perfect in layout earlier, and since we've
  been changing colours, yet the layout has been all over the place."* The
  drink page rebuilt whole against her written brief; margin layout — *"glass
  in the margin and top aligned, ship it"* (reversed 2026-09-05). The mood
  chips filter the index (her ask). `make it` became a three-part toggle, so
  #494's ambiguous-label problem (one button whose label read two ways)
  cannot arise. The hover language: magenta means "this
  one" — four hover states had been lightness-only no-ops. The panel behind
  the glass went (its wash was the lightest thing on a card, L* 19.40, and
  the arrangement was backwards — a near-white glass on a green field).
  `.on-dark` deleted — its four values had finally been exercised, approved,
  and are cocktails' defaults; a dark SECTION wants a context class, a dark
  SITE wants its palette inverted. The universe says… placed above the five
  questions.
- **2026-09-03, #679, #680** — The title had rendered at twice its stated size
  (UA `h1 { 2em }` inside `display: contents`): *"the font is too big"*, *"no
  space (spare tape) at all either side of the name"* were one default;
  3.2rem chosen by looking. Section headings 1.8rem / weight 400 — *"INGREDIENTS
  and METHOD feel very small. They're larger on food recipe pages and I
  prefer that."* Index headings to weight 400 (bold light-on-dark blooms). The
  ramp: reposado → coral `#FD6758` → hot pink `#FD5289` → cosmopolitan →
  yvette, interpolated in OKLCH — *"The ramp colours are gorgeous!"*; one
  bar — *"Ramp alone, gorgeous!!!!"* (a pink under-bar was *"a lot of pink
  up top, even for me"*); the section's colour reaches the card, reversing
  08-30's "magenta means matched everywhere" — on a card carrying three:
  *"There's a lot going on... But I genuinely think it's really pretty!"*
  Helen's brief's "yvette over absinthe" had been aimed at the section
  headings, *"not ingredients, my apologies"*.
- **2026-09-04 (design audit)** — The mood chips are bare words, "100% cards
  take words" (critical #5); the glass column 7.6rem → 6.5rem (*"Narrower
  glass column please."*, critical #9); no bottom rule at rest (the audit read
  the dash as "a progress bar stuck at 18 percent"; *"Agree, no mark, end
  of."*); a name shrinks one step or wraps, never ellipsises (*"shrink when
  it's just one short-ish word too long, then two lines where it's more than
  that. The one super-long title we have I'll just shorten, and retain that
  principle."*); two ingredient lines chosen — *"when we get issue #691 done
  (ingredients in importance order) I expect two lines will get the point
  across."* (reversed 09-06); the shortlist toggle top-right, Helen's
  placement with her own reservation recorded (#546); the scaler moved onto the INGREDIENTS heading's
  row (reversed 09-05); food's universe section removed.
- **2026-09-05** — The universe line: four rounds took it from a collapsed
  card to one line — *"the line layout is really working for me. Really
  really… it's less obtrusive than a box and I think that's what I like about
  it."*; `deal again` moved to the end of the row (the eye had read "the
  universe says deal again" — *"lol"*, #693); *"I want it to be a happy
  invitation"*; *"don't scale — all the same height"*; *"leave a fixed width
  for the glass so the name tape doesn't jump around on redeal"*; moods off
  the pick — *"moods off, decision made"*; kept on cocktails though dropped on
  food, *"almost always more open to persuasion about what I drink than what I
  eat"*. The drink page: *"Inline glass please. I don't care if this is
  changing my mind!"* (she had only ever seen the inline branch — the margin
  rendered above 1180px only); the drawing centred, not top-aligned; title
  2.6rem (*"The title seems enormous."* — the column had narrowed by 10rem);
  tape padding 1.6em (*"more empty tape either side of the cocktail name.
  Don't move the tape further left…"*); ingredient underlines dropped (*"we need
  to drop the violet underlines under ingredients because they look like
  links. This means we can return the violet underline to join the absinthe
  under the section titles"*); headings 1.5rem, because punched
  Courier over a double rule is a lot of furniture to stand over *"Pour
  ingredients into ice-filled glass"*, the whole of Aperol Spritz's method;
  the tagline 1.05rem in ink — *"the only real voice this part of the site
  gets"*; mood chips became links; the scaler, in its third home (#545 had put
  it at the FOOT of the page), to one box and a `×` under the list (*"the normal scaler
  shouldn't get to be at the top of the page. Please simplify it and move
  underneath the ingredients list, just a single input text box, 2 characters
  wide, with a small x next to it, no other text at all."*); **whole recipes
  only** (*"Logically I think we can solve the rounding/ratio issue by only
  allowing integer multiples."*); the target-ml box gone (#720, #721 — *"it's
  just baffling. Typing some numbers changes nothing, typing others changes
  the recipe but you can't see it… It is not clear how the numbers in each box
  relate to each other."* — every word true and none a bug: the grid was
  real and invisible); the bitters caveat gone (fired on Aperol Spritz);
  `.cocktail-section-row` had cost 36px on every page (a flex item's margins
  never collapse; Helen on #720: *"the presence of the scaler has moved the
  whole page downwards."*); `yes²` read as a footnote marker by a review —
  *"that's not a footnote marker, it's a joke, a cocktail so good that it's
  yes-squared. If this isn't landing then I'd rather rename than re-render."*
  — nothing renamed: the page says the rung's own words, the card keeps the
  compression, because a grid supplies the scale to read an escalation
  against; SHIP IT? read-mode only (shipped the other way round for an hour
  on a mis-stated instruction). Helen dropped the ship mark from `make it`.
  The floor: *"say you can't go below X ml if any ingredient wants to go
  below 2.5 ml"* — the message reads *"can't go below ×1 (112.5 ml): the cider
  vinegar would be under 2.5 ml"* (carta switchel); #721 *"changes on single character typing or deletion"*.
- **2026-09-06** — Three ingredient lines (#552; *"showing three lines is
  appropriate given the number of tiki drinks I have!"*), paid for by the foot
  (Helen from a screenshot: *"we could stand to move the chips on cards
  downwards, encroaching into the ship row."*); matched chips keep their
  colour (#756: *"cocktail chips hit by filters should retain the font colour
  from its section, and the underline in the same colour."*) and lead the
  row (#757; the DOM moves, not flex `order`, because the separator dot is a
  DOM-order selector; #710 alphabetical inside each group); ranking counts
  sections (#695, *extend the ranking, keep the narrowing*); pagination
  (#694); `chaos only` (#732, *"the name of the third YOLO filter should be
  'chaos only'"*, replacing `never made it` within hours); the third YOLO
  button reads `made_before`, never `ship`. `recipe-list.js` is on the
  cocktails page now and its name is wrong; renaming is its own change.
  Still not seen on an iPad.

- **2026-09-08, #846** — **The chip separator moved to a TRAILING `::after`,
  reversing a decision of 2026-09-05, and that deleted a whole measurement
  pass.** Helen, on a card whose chips ran to several lines: *"chips which form
  more than one line should have a . in between them even if the final chip on
  any line before the first is a whole chip... creme de peche is at the end of a
  line, but still gets a ."*

  **`chip-rows.js` had listed exactly this as considered and rejected** — "only
  relocates the orphan to the end of row one, where it reads as a sentence cut
  off". She looked at the built thing and wanted it, which is how a ruling
  changes here. The old reasoning is kept in the stylesheet beside the new rule
  rather than deleted.

  **#698 is now satisfied by construction rather than by measurement**: "no dot
  before the first chip" is true because no chip has a leading dot at all. So
  `chip-rows.js`, which measured `offsetTop` to mark row-starting chips, had
  nothing left to do and went — one fewer of the three passes #828 is about.

  **The feedback loop that forced absolute positioning was never about being in
  flow.** It was that the dot was drawn CONDITIONALLY, so its width fed the wrap
  decision that decided whether to draw it. An unconditional dot cannot do that,
  which is what lets it go back in flow — and in flow is *wanted*, not merely
  safe: an absolutely positioned `::after` has no width, so a dot ending a row
  would sit past the container's right edge and be clipped away by the row cap,
  invisible in precisely the case the issue is about.

- **2026-09-08, #760 — THE PROPOSED FIX DOES NOT WORK, and the issue had said it
  would.** #760 proposed making `.drink-card-moods` block flow and floating the
  ship right "at the end", so chips would "flow around the ship on the last row
  only". **A float reserves space from the TOP of its block, downwards.** Float
  it first and the chips wrap around it on row ONE; float it last and nothing
  comes after it, so nothing flows around it at all — it is simply placed where
  it fits, and **dropped to a new row when the chips already filled the last
  one, where `overflow: hidden` clips it away entirely**. That would have
  silently removed the verdict word from the busiest cards and looked fine on
  every card anyone checked.

  **What would work, in order of cost**: take the ship out of flow
  (`position: absolute`, bottom-right), which alone fixes the stated complaint
  because every row above the last gets its width back; or the float-bottom-right
  hack, a zero-width `::before` float of height *(container − one line)*, which
  needs the container's height known and ours is not; or re-introduce a
  measurement pass, which #846 has just removed. Tried, abandoned, branch
  deleted, reported on the issue rather than shipped.

- **2026-09-10, #942 — the drink page head on a phone, rebuilt from the
  numbers.** Helen: *"All cocktail pages have the glass overlapping problem.
  Ones with longer titles have tape cut too close to the upper and lower edge
  of the text."* Measured at 390px rather than reasoned: the 600px block that
  had set the glass to 4.5rem that morning sat BEFORE `.cocktail-glass-icon`'s
  own rule, which is equally specific and set it back to 7rem, so the override
  had never rendered — a 112px drawing in an 88px reservation. **A media
  block only wins if it comes after the rule it overrides**, and the phone
  head now lives beside the rules it changes. But the column itself was the
  design fault: a glass beside EVERYTHING — title, tagline, three stacked
  facts, chips, 574px on the Bellini — is a desktop layout squeezed. Below
  600px the head is now a grid where only one row has two columns: the tape
  and tagline take the full width, the glass sits beside GLASS / GARNISH /
  SHIP IT? at the height of that stack (still at its `--glass-fill` relative
  size), and the chips run full width beneath. The svg is out of flow inside
  its box so its intrinsic height cannot size the row (a flute at 72px wide is
  257px tall; the first cut spread the three facts down a 257px row). Both
  tape bleeds are cancelled on a phone, or Cobra's Fang scrolls sideways at
  360. **The tape complaint was a long-title fault, not a phone one:** every
  tape SVG's band is 70.59% of its box (polygon y 28–148 of 170), so four
  wrapped lines of lettering are taller than the band under them. On this
  page only, the artwork is scaled so the band is the box and the vertical
  padding recomputed to hold a one-line band at exactly its approved height
  (59px before and after on the Negroni at 1280). Cards untouched. A
  candidates artifact carried this and a glass-above alternative; **her pick
  is not yet recorded — write it here when she makes it.**

- **2026-09-10, #927 — "If you liked this, how about …", three related drinks
  at the foot of every drink page.** Helen's own scoping, in the issue: *"Not a
  full recommendation engine! But I expect we can do something with coincidental
  tagging."* And, mid-build, when a Ruby plugin and a `meta.ship` weighting were
  on the table: **"Keep it simple."** So the score is `shared moods + shared
  ingredient generics`, ties broken by title, and nothing else — no ship
  preference, no per-field weight, no tuning. Every knob one could add is a
  claim about what makes two drinks alike and nobody has made that claim yet.
  **In Liquid, in the layout**, not a plugin: 48 drinks is 48 iterations per
  page, where a generator would have cost a file, a hook-order question and a
  `jekyll serve` that silently serves a site it never ran on (§1).
  **The sort is the interesting part.** Liquid cannot sort by a computed
  number, so each candidate becomes one `rank~title~url` string and the array is
  sorted as TEXT, with `rank = 999 - score` — ascending text order then puts the
  highest score first and breaks ties A-Z by title in the same pass, with no
  second loop. **Measured before it was written, and the measurement is kept** —
  `scripts/related_drinks.py` is the same scoring in Python over the same
  corpus, so it doubles as a second implementation to check the Liquid against
  (§13.11: a number derived in `tmp/` is one nobody can reproduce). Across the
  48 published drinks every drink's third pick shares at least 3, most share 4,
  the best 6 — so filtering to `score > 0` never leaves a heading over an empty
  row. The Negroni gets South Sider (3 moods, 2 generics), Aperol Spritz (4
  moods, 0) and Boulevardier (2, 2), and the script and the built page agree on
  all three. **A compact row, not a card**: the index
  card is written inline in `cocktails/index.html` rather than in an include, so
  reusing it meant copying ninety lines of markup, and a third card design is
  §13.12's to refuse — so it borrows the three parts the universe line borrows
  (tiny glass, name on tape, one ingredient line) and none of the card's
  geometry. **No new hue** and a plain `.cocktail-section-heading`, the one "To
  serve" uses; the three coloured modifiers each carry a job and this section has
  not earned one. **Three across, then one, with no media query** —
  `repeat(auto-fit, minmax(13rem, 1fr))` asks the 900px column rather than the
  viewport, which is what §12's "you will check one element's width and call the
  row safe" is about. Hidden in `make it` (an invitation to make something else
  is the last thing wanted with your hands full) and in PRINT, where it is the
  opposite direction from that state's usual restore: print puts back what says
  more about THIS drink, and this is three links off it. **The heading is a
  marked PLACEHOLDER in Helen's own words from the issue** (§13.12) — the voice
  is hers and an agent must not write a line of it.
  **Deliberately not built**: food (*"the priority is cocktails"*, and the
  mechanism is only worth porting once she has looked at this one); any weighting
  by `meta.ship`; any hand-tuned per-field score.
  **And then she asked for the card, 2026-09-11, on #955:** *"1. Please add some
  kind of divider between the end of the recipe (whether serve or notes or
  anything else) and 'If you liked this...' 2. Please turn the suggestions into
  cards -- 1. Allow 2 or 3 lines of ingredients to show, 2. show the chips.
  It's fine for the cards to be portrait orientation. 3. Take the styling from
  index page cards, including the new styling in #953 when it's finished.
  3. Bring the glass drawing inline in the row with the name tape, so its left
  margin is aligned with the left margin of the ingredients line."* So the
  "compact row, not a card" above lasted a day, and the third card design is
  hers rather than refused. **The section sits under `.cocktail-footer`'s own
  rule** (gap, hairline, padding), so the page's tail is two objects drawn one
  way. **Each item is `.drink-card.drink-card--portrait`**: the index card's
  classes on the index card's parts, so face, tape, the three-line clamp, the
  chips and their dots, the ship and its mask, and #953's hover are all
  `_cards.scss`'s unchanged; the modifier moves geometry only (glass in a head
  row beside the tape, foot back in flow, height from content, the grid
  stretching a row to one height). **The markup is written in the layout, not
  shared as an include**, because the two cards differ in four flag-shaped ways
  (glass placement, chips as links vs filter buttons, no shortlist `+`, no
  search `data-*`), and four flags on ninety commented lines is a worse object
  than twenty-five plain lines naming the same classes; the stylesheet is the
  shared half and the one that cannot drift by accident. **The drawing is flush
  left in its slot** — centred it sat 12px in from the ingredient line, measured
  — and at the index's own compression, not one height for all. **Two classes in
  the grid selector**, because `cards` is imported after `cocktail` and
  `.drink-cards`' 370px floor won on order: the first build drew two across the
  900px column, measured, instead of three.
  **Then, the same day, the ship:** *"Please fix the text wrapping of chips
  above the ship... Keep the ship in the bottom right-hand corner, on the same
  line as that row of chips."* The index's clear-the-ship pass pads every row of
  a colliding card, and at 13rem that put the Boulevardier's chips one per row.
  A ship placed last in a normal flex flow takes a row of its own the moment
  the last row is full. The first answer filled the rows from the bottom
  (`row-reverse` + `wrap-reverse`, ship first, chips reversed), which keeps the
  ship in the corner but puts the SHORT row at the top, and she sent it back
  within the hour: *"These still aren't right."* **The answer that stands: the
  last chip and the ship are one flex item**, `.drink-card-tail`, that a line
  cannot split. The chips wrap top-down like text, in order; if the pair fits
  after the previous chip it sits there, and if not the pair wraps together,
  so the last row always ends with the ship at the right and the short row is
  the last one, as in a paragraph. DOM order is natural. The three-row cap is
  off on portrait cards, because the card grows and the cap would clip the
  ship's row on a busy drink.

- **2026-09-10, #886 — what a drink card does under the cursor.** The issue was
  a sentence with no body: *"do something more attractive with cocktail cards on
  mouseover."* The card had one hover state and it was two 3px strips bracketing
  the glass column (2026-09-02), which is the smallest possible answer to *"you
  can touch this"* on the biggest object the index has. Three treatments went on
  the real index behind `html[data-hover]`, each obeying §9.13's rule that colour
  moves and geometry does not, and each a HUE move rather than a lightness one
  (§12: at this type size the eye reads hue, and four of this site's hover states
  had already been caught as lightness-only no-ops):
  - **A, the edge and the words.** The strips grow into the card's whole magenta
    border; the drink's name takes magenta wherever on the card the cursor is,
    rather than only off its own letters; and both rows of separator dot — the
    ingredient line's `·` and the chip row's — come up from their greys to
    absinthe, which is the glass drawing's own colour reaching the words.
  - **B, the glass answers.** One declaration, because the artwork strokes with
    `currentColor`: the whole drawing moves absinthe → magenta and nothing else
    changes. The largest piece of colour on a card, and the loudest of the three.
  - **C, the field lifts.** The card stops receding — its field goes to
    `$color-wicked-woowoo-wash` — which is the one candidate that overturns the
    inversion's *"a card is a darker field cut into a lighter one"*. It is also
    the only one with a coupling to keep in step: `.drink-card-ship`'s mask is
    the card's own `$color-surface`, and a lifted card leaves the verdict sitting
    on a rectangle of the old colour unless the mask follows.
  A shipped on the branch first, with the other two one class swap away. Keyboard
  gets the identical state through `.drink-card:has(:focus-visible)`, written as
  a SEPARATE rule and never in a comma list with `:hover`: `:has()` is not
  forgiving, so a browser that does not know it drops every selector beside it —
  which would take the hover down too. `:focus-within` was rejected for firing on
  a mouse click, which would leave a card lit after the cursor had gone. Nothing
  at rest changed, so a phone is exactly where it was.
  **Her pick, 2026-09-11: *"option c please, but 1. without the border above and
  below the glass, b) glass also turns pink."*** So what shipped is C plus B's one
  declaration, minus the two 3px strips that had been the card's whole hover
  since 2026-09-04: the field lifts to `$color-wicked-woowoo-wash`, the glass
  drawing goes magenta, and `.drink-card-ship`'s mask lifts with the field from
  the same mixin. The strip pseudo-elements are deleted outright (a strip with
  no resting colour and no hover colour is a rule about nothing), and A's three
  pieces — the magenta border, the name lighting from anywhere on the card, the
  absinthe dots — are not in it; the name keeps only its own 2026-09-02 hover.
  Two of the candidates page's states were each built ON TOP of the strips,
  which is why "without the border above and below the glass" was a change to
  C rather than a description of it.

### §9.13 — the index and drink page, earlier
- **2026-08-30, #583 / #586 / #562** — see §13.4.
- **2026-08-31** — The narrow-screen table (360px: 157px text column, 39%
  glass) measured at the 7.6rem column; at 6.5rem it reads 174/189/226px.
  Losing the tagline (#512) freed a LINE; this is a WIDTH problem. Three
  layouts behind `?narrow=`; Helen chose `stack` from an iframe page (§11.2.1).

---

## §10 Validation

- **2026-08-12** — Helen: *"I'm concerned that issues we closed in the last
  few days weren't represented as tests... I still don't want to end up in a
  mess."* The audit: grep tests for issue citations, diff against closed
  issues, check each gap against the data. Most had a test; a cluster did
  not. Twenty-odd became tests; §10.1's 157-line table of them was cut on
  2026-08-29 because each test states its own rule. Same day: the suite is
  self-sufficient — *"you should be able to bring the recipes into shape from
  pytest output and this file alone"*; test names and messages expressive.
  `PLACEHOLDER` was a second marker for one day (08-09 to 08-10).
- **2026-08-14** — `test_print_neutralises_the_screen_page_background`
  passed while broken: two vacuity bugs stacked (a matcher that could not see
  `body`, an early return on "found nothing"). Rule: never `return` early
  because a scan came back empty; `test_suite_hygiene.py` enforces it;
  `test_accents_in_prose` was doing the subtler variant.
- **2026-08-18, #369** — The suite gates the deploy. Until then the workflow
  had no test step anywhere. `fetch-depth: 0`; the JS glob.
- **2026-08-20, #378** — Which tests read drafts, split by what each reads
  (`SKIPS_WITHOUT_DRAFTS`, `PARTIAL_IN_CI`) and enforced by a registry test
  that derives the list from source — which flagged ITSELF (its docstring
  names the corpus) and then misclassified two others because "does it skip?"
  asked whether the word appeared; it parses the AST now.
- **2026-08-21** — `test_no_main_ingredient_spelling_collisions` caught
  `"demerara sugar"` against four recipes' `"Demerara sugar"` on a new draft.
- **2026-08-29, #540** — Helen chose option 4 of four: gate at promotion,
  leave the private drinks out of a runner. `_load()` reads both roots; 24 of
  41 tests had skipped in every deploy run. #540's own account was too
  optimistic — the loader had never read `_cocktail_recipes/`, so promotion
  would have moved a drink permanently out from under every guard. Building
  the CI shape showed five guards failing on correct data (shrink-only
  registries, a mood's share of the book): the ratchet half runs everywhere,
  the staleness half calls `_require_whole_collection`.
- **2026-08-31, #624** — The garnish vocabulary merged here while the drink-side
  rename sat on an unmerged private branch: red for anyone with a clone,
  green in CI. The tell is both directions failing at once.
- **2026-09-05** — The schema handshake (`SCHEMA_VERSION`, `tests/drafts_schema.py`),
  Helen's choice among four options; a hand-maintained integer, not a
  fingerprint; not `pytest.exit()`. Both repos at version 1.
- **2026-09-06, #633** — The stub-DOM harness made permanent
  (`tests/js/dom-stub.js`, `index-harness.js`) after the 08-31 binding fault;
  it earned itself within the hour (#694 added `recipe-list.js` and
  `cocktail-index.js` threw on `apply()`), made pagination and the chip
  reorder testable, and found a bug writing the second (clearing a mood left
  its chip stranded at the front). Its selector engine had one real bug: a
  whitespace split broke `[data-mood='no juicing']`.

---

## §11 Working practices

- **2026-08-12** — Helen: *"Did your heading lettering change touch all
  headings on the whole site? That is what I want."*
- **2026-08-14** — The four interaction rules written down (show don't
  describe; symptoms not diagnoses; a structural reason under an aesthetic
  objection; UAT is first-class — every filled bar on the site vanished once
  while 16,806 tests passed). Two demo pages decided the longform styling and
  the whole reference layer.
- **2026-08-16** — *"Give me decisions to make as you go."* Three rulings
  mid-way through the exclude vocabulary each removed a class of guesswork;
  "only 2 of 73 methods have this shape" settled the doneness UI in one
  reply. Same day: a background agent given #274 was stranded when Helen ran
  `git checkout main` and pulled — one agent at a time, never one that
  switches branches. Four issues in one session (#52, #273, nearly #274/#281)
  shipped without trailers and sat open.
- **2026-08-17** — `GH_TOKEN` widened from read-only to issues read/write on
  three repos, probed by measurement (§11's paragraph saying "read-only by
  choice" stood until 08-21, contradicting §10.1). Four commits landed on
  `_cocktail_drafts`' `main` because the rule read as if there were one
  repo.
- **2026-08-18** — `git reset --hard origin/main` to move a stray commit wiped
  a half-finished handover edit; two commits landed on `main` directly. Rules
  written into `CLAUDE.md`.
- **2026-08-19** — The rule was read and broken the same day (`git checkout
  -- <two files> 2>/dev/null || true`), so `guard-destructive-git.py` was
  written — the first executable rule about the AGENT. Its first version
  patterned only the ` -- ` spelling; `git checkout tests/test_style.py`
  walked past it hours later and discarded work — the guard's own author fell
  into the hole. It asks the filesystem now. Both quoted mentions and heredoc
  bodies were found by testing: the hook blocked the commit that introduced
  it. A hook, not a `deny` entry, because the offending line was a compound
  with a redirect and a fallback. `python3`, no execute bit. Same day: Helen
  merged and pulled mid-task, deleting the working branch under a session
  with three staged files; `git checkout -b` carried them across.
- **2026-08-20** — THE AGREED WORKFLOW (**step 1 widened 2026-09-07, below —
  Claude opens the PR now**): Claude branches and pushes; Helen opens,
  reviews, merges and does nothing else; Claude `git fetch origin main:main`,
  deletes the branch, branches afresh. `guard-main-branch.py` the same day,
  because the written rule was broken again by an agent that RAN the check —
  in the same shell call as the commit: *a check that cannot stop the thing it
  is checking is a narration, not a check.* Helen, after a summary ended with
  "it's half past midnight — that's a good place to stop": *"I am aware of the
  time. I keep my own hours. Please never tell me to stop or go to bed — those
  things are up to me."* She added *"I'm sure this used to be in the
  handover"* — it never was, checked with `git log -S`.
- **2026-08-21** — Commit type words counted rather than asserted (`content`
  and `docs` alone were 133 commits and absent from the stated list).
- **2026-08-22** — A `Fixes owner/repo#N` trailer from a private repo
  cross-references nothing — measured against #335's timeline after a day of
  correctly-formed trailers (`Towards DeckOfPandas/helen-triages#335`, `Fixes
  DeckOfPandas/helen-triages#442`).
- **2026-08-23** — Use a worktree when more than one agent shares the checkout.
- **2026-08-24** — *"I have a soft limit on deploys per hour, so I prefer
  larger pull requests where that's practical."*
- **2026-08-29** — `/tidy-drafts` at Helen's request (*"I also want a way of
  saying hey, Claude, please tidy up my drafts files."*): run for real in
  three commits — scalar quoting 295 → 0, `main_ingredients` quoting 279 → 0,
  `tags` 248 → 0, en dashes 58 → 0, `meta:` 341 → 5 — and all four zeroes
  adopted as draft rules so the backlog cannot regrow. Its `meta:` rewrite
  had swallowed the trailing newline and broken 341 of 342 drafts while the
  diff looked plausible; caught by parsing both sides, on a COPY. Size words
  (108 drafts) and a missing `awaiting_fix` (Helen's to set) excluded, her
  call. Same day: `unpushed=0` reported from `git log @{u}..HEAD` while one
  of Helen's own edits sat on a walked-away-from branch; recovered because
  `git branch -d` refused and the refusal was read. Helen's standing
  preference on closing: *"Close #540 (via commit message if possible -- this
  is always my preference)."* #558 and #561 found fully delivered and still
  open. `test_note_dicts_have_label_and_text` found mislabelled as a
  mechanical gap in `NOT_FOR_DRAFTS` (would have invented 256 note labels).
- **2026-08-31** — `/ingest` and `scripts/ingest_preflight.py`: one list
  grouped by decision. The playtest changed three things — absences became
  near-misses, steps already proposed stopped being reported, the
  `star_ingredient` check deleted (it fired on 118 drafts, a third of the
  corpus, which §7 says is correct).
- **2026-09-01** — Title/slug divergence is NOT a finding on a draft: *"let's
  not run the 'title matches slug'-ish test over drafts."* — a draft's title
  is still the source's (`chocolate-fudge-cake` titled "Cassie's Favourite
  Chocolate Fudge Cake"); her rule on possessives: *"I mostly dislike
  'Cassie's Sunday Chicken' unless Cassie is either famous or a member of my
  family."* 19 of the 21 lines the script printed were this.
- **2026-09-02** — The round trip for a repo-less file, asked directly: *"is
  this in the case where I get files back from a Claude web and we need to
  ingest them properly once I'm back at a desk? Is the pipeline very clear in
  the handover?"* It was not; proved end to end (125 drinks, 124 agreeing, 1
  written).
- **2026-09-02, D8–D11 (inbox design §9)** — D8 `item` draft-only; D9 label
  `ingest`, title `ingest: <slug>`; D10 Helen pastes the envelope herself —
  *"I am new to this and quite conservative."*; D11 every garnish carries a
  `group:`.
- **2026-09-03, #672** — `/ingest-inbox` built; an absent drafts repo is a
  refusal, not a clean inbox (#537's lesson). Slug the whole title.
- **2026-09-05** — Cocktail drafts joined `/tidy-drafts`: *"Widen please —
  cocktail drafts passing will save me a lot of time."*; the first real run
  found nothing (#670 had cleared every range two days earlier), so the claim
  rests on the byte-for-byte fixture test. The drinks boundary uses the
  SUITE's QQ predicate (the food one matches none of a drink's `QQ` shapes);
  `anitas-attitude-adjuster`'s `amount: "Top (30-45) ml"` with a QQ note
  quoting it is the recorded harm behind not touching amounts.
- **2026-09-05** — Pushing a branch in the private repos needs no ask.
- **2026-09-06** — `CLAUDE.md`: `${GH_TOKEN:-unset}` prints the token (it did).
- **2026-09-07 (later the same session) — and then the ask went entirely.**
  Helen: *"push no longer needs my say so. I had this rule because multiple
  Claudes were trampling each other and it's easier to fix that locally, but I
  now get Claudes to run Claudes and everything is less chaotic!"* So push and
  PR are unattended in all three repos, and `helen-triages` stops being the
  exception it had been since the workflow was written.
  - **THE PR HALF DOES NOT ACTUALLY WORK ON THE PRIVATE REPOS, measured later
    the same day.** `POST /pulls` succeeds on `helen-triages` and returns 422
    *"not all refs are readable"* on both private ones. The same five calls
    against each repo:

    | | issues | pulls list | branches | contents |
    |---|---|---|---|---|
    | `helen-triages` (public) | 200 | 200 | **200** | **200** |
    | `helen-triages-food-private` | 200 | 200 | **403** | **403** |
    | `helen-triages-cocktails-private` | 200 | 200 | **403** | **403** |

    Helen asked whether she had misconfigured the token and sent its settings
    page. **She had not.** The repository list is right and Issues + Pull
    requests read/write is granted on all three, exactly as her screenshot
    showed. What is missing is `Contents` — and **opening a PR must READ THE
    HEAD REF** to check it exists and compute the diff, which is a Contents
    operation. A public repo's refs need no permission at all, so the public
    one works and the private two cannot.
  - **THE ORIGINAL VERIFICATION WAS SOUND AND STILL MISLED, which is the
    transferable part.** It ran `gh pr create` on a throwaway branch, got a real
    PR URL, and concluded the widening worked. It was run against
    `helen-triages` — the ONE repo of the three where the missing permission is
    invisible. **A capability check on the most permissive member of a set
    proves nothing about the set.** Probe the narrowest case, or probe all of
    them; §0's rule about measuring rather than assuming is not satisfied by one
    measurement in the easiest place.
  - **Helen left the permission ungranted, shown the trade, 2026-09-07.**
    `Contents: Read` would fix PR creation and would also let the token read
    every drafts file through the API — which MANUAL §9.1 states as a property
    the repo relies on (*"reads file contents on none of the private ones (403).
    Git can."*). That separation is deliberate: access to the drafts goes
    through git and SSH, where it appears in commits. Against that, pushing to
    the private repos already needs no ask, so the only manual step left is the
    PR form itself, usually on a branch she is about to merge anyway. Cheap to
    keep, so it was kept.
  - **The reason matters more than the rule, and it is the transferable
    part.** The confirmation was never a judgement that pushing is risky — it
    was a lock against parallel sessions fighting over one checkout. Worktrees
    and an orchestrating Claude removed the collision, so the lock was cost
    with nothing behind it. A confirmation step is worth keeping only while
    the thing it guards against is still possible; **this is the question to
    ask of an ask, before proposing another one.**
  - **Merging did not move, and this is the third time it has been written
    down in one day** — the workflow, the token section, and here. That is not
    redundancy: it is a rule whose whole job is to survive the day somebody
    finds it inconvenient, on the day the rules around it all loosened.
  - The bundling ruling below is what this superseded, hours old. Both are
    kept, because the intermediate state is what makes the reason legible.
- **2026-09-07 — Claude opens the PR, and the ask is bundled with the
  push.** *(Superseded by the entry above the same day: there is no ask at
  all now. Kept for the reasoning, which still holds.)* Helen: *"I've added
  permissions on GitHub for you to open PRs. Please do so now with this work,
  to test the setup!"* She widened the
  fine-grained PAT to `Pull requests: Read and write` herself and rewrote
  `CLAUDE.md` herself; step 1 of the agreed workflow is now one confirmed
  action covering both the push and the PR, because asking twice for one
  action was overhead she was paying for nothing. **Merging did not move and
  is not going to** — she wrote it into `CLAUDE.md` twice, in the workflow and
  in the token section, which is the right amount for a rule whose whole job
  is to survive the day someone finds it inconvenient.
  - **The "never broaden access" rule is unchanged, and reading it as changed
    would be the error.** It is about a session asking for or granting itself
    scope; documenting a widening Helen has made is the opposite of that. The
    2026-08-17 measurement (`opening a pull request 403`) stays on the page
    with the flip noted beside it rather than being deleted, so the next
    session can see that this was measured twice and not assumed once.
  - **Measured, not assumed, both times.** Helen's own probe was a throwaway
    branch and PR #805, closed unmerged. Mine was the real one: `POST
    /repos/DeckOfPandas/helen-triages/pulls` → 201, PR #808, and then read
    back to check `head`/`base`, `mergeable_state: clean` and that the body
    really carried `Closes #801` — a 201 says a PR exists, not that it points
    where you meant.
  - **`gh` does not exist in a worktree**, so `CLAUDE.md`'s `gh pr create`
    cannot be followed there: `.gh-runtime/` is gitignored and absent, exactly
    like `.node-runtime/` and the two drafts repos. The REST API is the
    mechanism instead. Worth knowing before reaching for the command the rules
    name — this is the second time a documented `gh` invocation has had to be
    done another way from a worktree.
  - **The token's new scope stops short of ref deletion.** Helen measured
    `gh pr close --delete-branch` 403 on the delete while the PR close itself
    succeeded; plain `git push origin --delete` works, because that is SSH and
    not the PAT. So step 3's branch cleanup keeps going through git.
  - **A false start worth recording, because it is the general case.** Told
    the permission change was merged, `git fetch origin` showed `main`
    unmoved, no branch on the remote touching `.claude/` or `CLAUDE.md`, and
    `.claude/settings.json` last changed by the old hook commits. It had not
    been pushed. Stopping was right for a specific reason rather than caution
    in general: she had said her change edited `CLAUDE.md`, and the section
    being edited was the same one — writing then would have put the same rule
    in the governing document twice, on the day it changed. She found and
    merged it (#809), and her text already said both things this session had
    proposed, better; **so the correct amount of `CLAUDE.md` for this session
    to write was none.**

- **2026-09-08 — step 1 splits: in the devcontainer Claude commits and Helen
  pushes.** One day after the ask was removed entirely, the container turned
  out not to be able to push at all, for two independent reasons neither of
  which is fixable from inside: `origin` is SSH and the image has no GitHub
  host key (**`Host key verification failed`** on every SSH git operation,
  `git fetch origin main:main` included), and the fine-grained PAT carries no
  `Contents` scope, so the HTTPS fallback is **403 `Permission to
  DeckOfPandas/helen-triages.git denied`** — the token behaving exactly as
  §9.1's measured table says it should.

  Helen: *"Because you're in docker, I won't give you a GitHub host key. Make
  your changes, then tell me which branches to push and I'll push them -- I
  always review locally anyway so this isn't really an extra step as otherwise
  I'd only pull from what you pushed before I merged."*

  **This is an environment fact, not a reversal of 2026-09-07.** Step 1 stands
  wherever pushing works. What is new is 1a: name the branch, give her the
  command, and go on opening and maintaining the PR — which still works,
  because a PR needs `Pull requests: write` and not `Contents`.

  **`/workspace` is a BIND MOUNT of Helen's own checkout**, which is what makes
  this cheap and was got wrong before it was got right: a commit is already in
  her tree the moment it is made, so nothing travels and nothing is stranded.
  An unpushed commit here should never be described as trapped.

  **A fetch, unlike a push, has a working substitute** — the HTTPS URL needs no
  credentials at all on a public repo and fast-forwards `main` exactly as the
  SSH form does.

- **2026-09-08 — the shared checkout, and the second reason to check the branch
  before committing.** The bind mount means another session, or Helen, moving
  the checkout moves the ground under a running Claude with no signal. In one
  session the branch went `main` → `docs/bash-friction-followups` →
  `chore/devcontainer-per-worktree-bundle-cache` → `docs/multiline-arg-friction`,
  none of them that session's, and an uncommitted `DECISIONS.md` edit rode
  along into somebody else's branch. **The pre-commit `git branch
  --show-current` check caught it**, which is the first time that rule has
  earned its keep for a reason other than the one it was written for: the
  question it answers is not only *am I on `main`* but *am I still where I left
  off*, and the answer can be no when nothing you did changed it.

  **This is the 2026-08-16 stranding again** — an agent lost when Helen ran
  `git checkout main` and pulled — and the answer has moved on. That day it was
  *one agent at a time*; 2026-09-07 replaced that with worktrees plus an
  orchestrating Claude, which is what let the push ask be dropped. What this
  showed is that the guarantee only holds when **every** session is actually in
  a worktree, and `/workspace` is not one. Helen: *"I'll run Claudes in
  worktrees going forwards."*

- **2026-09-08 — A RENAME THAT SPANS BOTH REPOS MUST MERGE DRAFTS-FIRST, and
  getting that backwards turned Helen's local `pytest` red.** #852 renamed
  `coney-park-swizzle` to `coffey-park-swizzle`: the file lives in the private
  drafts repo, and `mood_include` in the public `taxonomy.yml` is keyed by
  SLUG. Both halves were written and the commit message said the slug was
  "renamed in the same breath there" — **true of the work and false of the
  merge.** The two repos merge independently. The public half went in, the
  drafts half sat on an unmerged branch, and
  `test_every_mood_correction_is_reachable_and_needed` then reported
  `mood_include.coffey-park-swizzle: names no drink in the collection`.

  **CI could not have caught it**, which is the sharp end: that test is
  `_require_whole_collection`, so it skips wherever the private drafts are
  absent — which is CI. Only Helen's machine, with both repos cloned, sees it.

  **The rule, and it generalises past renames**: public data may name a drafts
  slug; drafts never name public data. So **the drafts side merges first**, and
  a change that crosses the boundary is not finished when both commits exist —
  it is finished when both are on their `main`s, in that order.

- **2026-09-08 — the token-expansion guard, and the third time is what earned
  it.** `CLAUDE.md` has said since 2026-09-06 that `${GH_TOKEN:-unset}` prints
  the whole token when it is set, and that `${GH_TOKEN:+set}` is the only safe
  probe. In one session on 2026-09-08 the rule was broken twice more by an
  agent that had read it: `${GH_TOKEN:-unset-marker-check}` at the start, which
  the permission checker happened to refuse for an unrelated reason and which
  the agent then explicitly promised not to repeat; and
  `${AGENT_GH_TOKEN:-MISSING}` on the NEW token an hour later, which **Helen
  caught and rejected by hand**. Twice of three, the only thing between the
  token and the transcript was luck or a human watching.

  **So it is a hook now** — `.claude/hooks/guard-token-expansion.py`, the
  fourth in the family, and the reasoning is verbatim the one this repo reached
  for `git commit` on `main` and for `sed`: **a rule I read and break needs
  enforcement, not rewording.**

  **WHAT IT BLOCKS IS NARROW ON PURPOSE**, because a guard that gets in the way
  of legitimate use is a guard people route around. Two shapes, neither with a
  defensible use: the four default-value expansions (`:-`, `:=`, `-`, `=`),
  every one of which evaluates to the variable's own value when it is SET — so
  the case you were probing for is exactly the case that leaks — and any
  `echo`/`printf` of a secret. It allows `${TOK:+set}`, allows the `?` forms,
  and allows `${TOK}` wherever it is CONSUMED rather than printed, which is how
  the credential helper and `GH_TOKEN="$AGENT_GH_TOKEN" gh ...` both work.

  **THE ONE REAL SUBTLETY, AND THE PIPE-TEST FOUND IT.** `guard-sed.py` strips
  single AND double quoted spans, which is right for detecting a command NAME.
  It is WRONG for detecting an expansion: the shell expands `$VAR` inside
  double quotes, so `echo "$GH_TOKEN"` is a live leak wearing quotes. This hook
  strips only the spans where expansion genuinely cannot happen — single-quoted
  spans and quoted-delimiter heredocs. A first draft also denied
  `echo "${GH_TOKEN:+set}"`, the very probe the rule recommends; the 18-case
  pipe-test caught it before the hook was wired to anything.

- **2026-09-09 — A COMMIT MESSAGE IS A DOCUMENT. THE DIFF IS THE CODE.** §11.2
  says do not trust this document over the code; the same applies to any prose
  about a change, including an excellent commit message, and this is the day
  that cost something.

  `chore/devcontainer-multi-worktree` carries a long, careful, well-argued
  message describing verified end-to-end testing. On the strength of it alone
  this session recommended merging the branch. **Reading the diff the next turn
  showed its `run.sh` DELETES the two lines that read and pass
  `AGENT_GH_TOKEN`** — because the branch predates that token. Merging it would
  have silently removed the container's ability to push, the capability being
  used to push at the time. Its `CLAUDE.md` was stale the same way, still
  asserting the container cannot push.

  **The message was not wrong; it was TRUE ON THE DAY and the world moved.**
  That is the failure mode to expect from a branch that sat for four days, and
  no amount of care in the writing protects against it. **Read the diff of any
  branch you are about to recommend, and diff it against TODAY's main rather
  than against its own merge base** — `git diff main..branch` is what showed
  the deletion, where `git show branch` alone would not have.

- **2026-09-09 — THE SAFE PROBE IS BANNED TOO, AND THE REASON IS NOT THAT IT
  LEAKS.** `guard-token-expansion.py` was written on 2026-09-08 with one
  deliberate exception: `${TOK:+set}` and `${TOK+set}` evaluate to the
  replacement WORD and can never render a value, so an `echo` of one is not a
  leak, `CLAUDE.md` named it "the only safe probe", and a first draft that
  denied it was treated as a bug the 18-case pipe-test had caught.

  **A session then ran `echo "${GH_TOKEN:+GH_TOKEN set}"` and Helen rejected
  the call by hand.** The hook allowed it, correctly. Nothing leaked, and
  nothing would have. **She rejected it anyway, because from the outside it is
  indistinguishable from a leak** — deciding it was safe meant reproducing this
  file's regex in her head, on sight, at speed. *"I shouldn't have to reject
  the call!! I'm only human!"*

  **THE LESSON, AND IT GENERALISES PAST TOKENS: A GUARD WHOSE EXCEPTIONS A
  HUMAN HAS TO VERIFY HAS MOVED THE WORK, NOT REMOVED IT.** Every exception in
  a guard is a rule the human must also know, and the rejection cost her more
  than the exception ever saved. The narrowness that was a virtue on 2026-09-08
  ("a guard that gets in the way of legitimate use is one people route around")
  was the wrong trade here, because the "legitimate use" it protected had no
  value: **the probe was only ever asking whether a credential existed, and the
  honest way to ask that is to USE it and read the status code.** A 401 or 403
  answers it exactly and renders nothing. Helen: *"I can't imagine why we
  wouldn't do that having thought of it."*

  So the hook now refuses **any** mention of a secret by `echo`/`printf` — the
  `+` forms, the `?` forms, and `${#TOK}`, which is a length rather than a
  value and would otherwise have been the obvious next reach. The default
  expansions (`:-`, `:=`, `-`, `=`) are still refused everywhere, echoed or
  not. **The rule a human can now check at a glance: an `echo` never mentions
  a secret.** Verified by breaking it on purpose — 15 cases, 9 denials and 6
  allowances, including that single-quoted prose about these forms is still
  legal and that `GH_TOKEN="$AGENT_GH_TOKEN" gh ...` still passes.

  **The counter-argument, recorded because it is the one that lost.** Denying
  the `+` form removes the ability to answer "is this variable set?" without
  side effects. That is a real capability, and it is worth nothing: no task
  here has ever needed the answer in isolation, and every task that thought it
  did was about to make an API call that would have answered it better.

- **2026-09-09 — `GH_TOKEN` DELETED. ONE CREDENTIAL NOW, AND THE PRIVATE-REPO
  PR GAP CLOSED WITH IT.** Helen deleted her own fine-grained PAT on GitHub the
  same day and removed the read from `.devcontainer/run.sh`. `AGENT_GH_TOKEN` —
  `DeckOfPandas-agentic`'s classic `repo`-scoped PAT, created 2026-09-08 — is
  now the only credential, for every repo and every operation.

  **The reason is that the second token had become a strict subset of the
  first.** `AGENT_GH_TOKEN` already did issues, pull requests, contents, push
  and ref deletion on all three repos; `GH_TOKEN` did issues everywhere and
  pull requests on the public repo only. Two credentials where one was enough
  — **and the smaller one was the one generating rules.** The 2026-09-07 scope
  table, the 422 `not all refs are readable` on the private repos, the `gh pr
  close --delete-branch` 403 needing `git push --delete` as a fallback, the
  §9.1 line about the API reaching drafts contents where git could: every one
  of those was a description of `GH_TOKEN`'s limits, and every one is now
  history. **They are kept in this file and deleted from `MANUAL.md` and
  `CLAUDE.md`**, which is the split those files exist for.

  **WHAT THIS COST, AND IT SHOULD BE SAID PLAINLY: MERGING IS NO LONGER
  MECHANICALLY IMPOSSIBLE.** `CLAUDE.md` used to end the permissions section
  "the token is scoped so the rest is impossible", and for merging that was
  true — a fine-grained token without the permission simply could not. A
  classic `repo`-scoped token held by a collaborator **can merge a pull
  request.** The rule is unchanged and absolute; what changed is that it is now
  held by the rule alone. Repo settings, secrets, Actions, webhooks and
  collaborators still need admin rights the agent account does not have, so
  those remain mechanically out of reach.

  **The second thing it cost is smaller and worth writing down**: the "why an
  issue and not a branch" argument in `INGEST_INBOX_DESIGN.md` §8 and
  `scripts/ingest_inbox.py` rested partly on there being no credential that
  could write a branch to a private repo. There is one now. The conclusion
  survives on its other leg — the session that writes the file is local and
  runs every guard, and the private repos have no build — but **the ingest
  envelope travelling as an issue is a choice now, not the only option.**
- **2026-09-09 — THE INLINE-SCRIPT GUARD, AND THE RULE THAT ACTUALLY BITES IS
  NOT THE ONE I BUILT FIRST.** `CLAUDE.md` has said since 2026-09-08, in
  Helen's words, "if they take or emit variables, please write a script in
  tmp/", and "when a command needs to be clever, put the cleverness in a file
  and run the file". It was read and broken twice in one session, both times
  with a multi-line `python3 -c` — once rejected by hand, once allowed with
  *"please please please write those long lines to files rather than running
  them all together."* Fifth hook, same verdict as the other four: **a rule I
  read and break needs enforcement, not rewording.**

  **THE CALIBRATION TOOK THREE GOES AND EVERY CORRECTION CAME FROM A
  MEASUREMENT**, which is the part worth keeping:

  1. **160 characters.** The probe caught a 155-character one-liner carrying a
     dict comprehension — the exact "cleverness" the rule is about, with no
     newline in it. Caught before the hook was wired to anything, by breaking
     it on purpose (§12).
  2. **120.** Helen then hit a prompt on an **89-character** command and said
     "it looks like you need to drop your character threshold".
  3. **100, plus the rule that mattered.** She was right that it prompted and
     right that the threshold was loose, but **length was not why that command
     prompted.** The allow rule is `Bash(python3 -c ' *)` — SINGLE-quoted. That
     command contained single quotes, so it had to be double-quoted, so it
     matched no allow rule and would have prompted at any length. `CLAUDE.md`
     had always said "short snippets WITH NO EMBEDDED SINGLE QUOTES"; only the
     length half had been enforced.

  **THE LESSON GENERALISES PAST THIS HOOK: A GUARD BUILT FROM THE HALF OF A
  RULE THAT IS EASY TO MEASURE WILL LOOK RIGHT AND MISS THE COMMON CASE.**
  Length is easy to count and quoting is not, so the first draft counted
  characters and ignored the clause sitting next to it in the same sentence.
  The symptom was a guard that passed its own tests and still let Helen be
  interrupted.

  **What it deliberately allows**: short single-quoted one-liners (`CLAUDE.md`
  permits these and the existing allow rule covers them), any command running a
  FILE, `-c` on something that is not an interpreter (`git -c
  credential.helper=...`), and `sh -c`, which is how a git credential helper is
  spelled and whose blocking would break the documented push shape. Verified by
  breaking it on purpose, twice: 12 cases then 9, including the 89-character
  command that had slipped through.

- **2026-09-09 — "THERE ARE EXACTLY TWO HOOKS" HAD BEEN FALSE FOR A WHILE.**
  MANUAL §11 carried that sentence, with the useful warning attached that a
  rule is not mechanically enforced merely because the file states it firmly.
  The warning was right and the count was three short: `guard-sed.py`,
  `guard-token-expansion.py` and `guard-inline-script.py` had all arrived
  without it being revisited. **A count in prose is a fact that rots, and the
  only honest version of such a sentence is one that names the members** — so
  it now lists all five and says `ls .claude/hooks/` settles it. Same failure
  as every stale number this file records; §11.2 is the family.

- **2026-09-09 — I READ AN EXIT CODE THAT MEANT NOTHING, TWICE, AND REPORTED
  IT AS GREEN.** `scripts/verify.py` exits non-zero if anything fails, which is
  true and was not what I was reading. Both commands ended in something else:

      python3 scripts/verify.py 2>&1 | tail -14      <- tail's status
      python3 scripts/verify.py > log 2>&1; tail log <- tail's status

  A pipeline reports its LAST stage and a `;` list reports its LAST command, so
  in both cases the 0 belonged to `tail`. I told Helen "exit code 0, all green"
  with real failures underneath, including one a guard had correctly caught.

  **§12 already says this in one line — "every one was caught by breaking the
  thing on purpose and reading the OUTPUT, not the exit status" — and I broke
  it while quoting the same section about something else.** The fix is not a
  hook: it is that a verification's evidence is its OUTPUT, and if the output
  is not in front of you then nothing has been verified. Redirect to a file in
  `tmp/` and read the file.

- **2026-09-09 — I RAN TWO `pytest` SESSIONS AT ONCE AND DIAGNOSED THE RESULT
  AS A REGRESSION.** MANUAL §1 warns about this by name and even gives the
  tell: `test_rendered_pages.py` writes throwaway `zzz-gate-` recipes and
  deletes them, so a concurrent run collects them as real files and reports
  schema failures that vanish on a clean rerun. I launched `verify.py` twice
  because the first appeared to hang, got a screenful of `zzz-gate-` failures,
  and started reading them as real. **The tell is in the test IDs and it is
  unmistakable once you know it.** One at a time, and if a run seems slow, wait
  for it rather than starting a second.

- **2026-09-09 — `git log --branches --not --remotes` REPORTS FALSE POSITIVES
  IN THE DEVCONTAINER, and §12 recommends it as the sweep for unpushed work.**
  It is right on the host and wrong here, for a reason that is structural
  rather than a bug: the container pushes by explicit HTTPS URL (`origin` is
  SSH and dies on `Host key verification failed`), and **pushing to a URL never
  updates the local `origin/*` tracking refs**. So every branch pushed that way
  looks unpushed forever. It said a commit was unpushed that was demonstrably
  on the remote and already had a PR open against it.

  **`git ls-remote <url> <branch>` IS THE HONEST CHECK HERE** — it asks the
  remote rather than a local cache of it, and comparing its SHA to
  `git rev-parse HEAD` answers the actual question. Worth knowing before
  reporting work as lost.

- **2026-09-09 — A GUARD FOOLED BY THE PROSE EXPLAINING IT, ON ITS FIRST RUN.**
  `test_the_layout_takes_the_twist_step_from_methods_yml` scans
  `_layouts/cocktail.html` for a spelled-out twist sentence, and the first
  version fired on the UNBROKEN file: the template's own comments quote that
  sentence while explaining the rule. §12 predicts this in as many words — "a
  source-scanning guard will be fooled by the prose explaining it… the
  vocabulary of a rule is densest in the comment explaining it" — and the
  prediction was six-for-six before this made it seven.

  **The fix is the one §12 names: match a call SHAPE rather than a string.** It
  looks for a literal ASSIGNED to `twist_step`, so a comment saying what the
  sentence is stays documentation. **And the tell was running the guard against
  the correct file and getting RED** — a break-it-on-purpose harness that only
  ever runs the broken case would have reported a pass.

- **2026-09-09 — ONE FACT IN TWO PLACES, FOUND BY CHANGING IT.** `methods.yml`
  declared the two twist sentences and `_layouts/cocktail.html` ALSO spelled
  them out. Helen changed the wording (#880, `and` → `then`); editing the
  declaration left the page emitting the old string, with the whole suite
  green.

  **WHAT CAUGHT IT WAS THREE STEPS AWAY AND LOOKED LIKE SOMETHING ELSE**: the
  standalone ingest document prints that vocabulary, so
  `test_every_vocabulary_the_cocktail_doc_prints_is_still_declared` went red
  and reported a DOCUMENTATION problem. The actual fault was that the page had
  kept the old sentence and would have gone on printing it indefinitely.
  **A test failing about a copy of a thing is worth reading as a question about
  the thing.** The template reads the data now, and a guard watches the pair.

### §11.2 The record of this file being wrong

Each is a lesson in §11.2's one sentence: an instruction to verify is not
verification. Dates are when the correction landed.

- 2026-08-19: "two stylesheets import shared/" (three). 2026-08-21: "no
  companion documents" (one existed); the "read §10 first" box (§12);
  `about.html`'s written-but-not-done `site_key`; §11's "read-only gh". 2026-08-21
  to 08-29: "roughly 90 drafts carry the old hyphen" (zero). 2026-08-29: §6's
  gulai ayam count (eleven; fourteen); §9.3's "526+ of 594" generics;
  §9.3.2's "eleven" unresolved suggestions (34, 30, 16). 2026-09-02: §4.0's
  "two gated collections" (three since 08-26); §9.5's retired square; the
  header's standalone-docs guard "gap". 2026-09-03: §2.3's "grey placeholder"
  accent (a week stale). 2026-09-04: §9.10.1's all-or-nothing card rule (never
  in the file); §9.10.1's derived syrup name (never existed); §9.10's
  "promotion is the deadline". 2026-09-05: the header's `tmp/` scripts named
  as the guard; §11.0.1's `ln -s`; §9.13's "raises every ratio to a power"
  (three comments, never true); §13.7's "right-aligned, punched" survivors
  line (three weeks, and #615 was written from it). 2026-09-06: DOCS_REVIEW's
  twenty-five (§0).
- **2026-08-30 / 2026-08-31, #600** — An issue rots faster: #600 copied #542's
  "Also outstanding" without re-measuring, four days on, and every claim was
  false (six half-empty disjunctions — zero; Kamaniwanalaya already had the
  fix; `swizzle` no longer existed; two strings no longer outstanding). Helen:
  *"I saw Kamaniwanalaya and Swizzle and felt annoyed again — have we not
  settled this? Now three times or more?"*
- **2026-08-31, #539** — Do not ship a layout at a size you cannot look at:
  three narrow layouts shipped behind a switch that neither Helen nor the
  agent could look at (a desktop will not drag below ~500px; her iPad is
  768–834px); one was broken outright and had been pushed. A dev page of
  iframes fixed it in one look.
- **2026-08-12, #131, #128** — CSS naming: `--modifier` is real BEM, 8/9
  checked had a base class; `.ingredient--matched` was the ninth and a real
  bug; a 2026-08-12 architecture review's full migration plan is not to be
  resurrected. #131's `Closes` trailer never closed it.

- **2026-09-10 — TWO GUARDS LOOSENED BY A FACT NEITHER OF THEM CHECKED: AN
  ALLOW RULE THAT DOES NOT EXIST.** Helen hit a permission prompt on this:

      python3 -c 'import json;d=json.load(open("tmp/issues-open.json"));print(len(d))'

  78 characters, one line, single-quoted — inside every limit
  `guard-inline-script.py` set, and exactly what `CLAUDE.md` called a "short
  snippet" and explicitly permitted. She asked: *"let's figure out how to
  either do that in a safer way, or not need to ask me!"*

  **The carve-out was justified, in three places, by `Bash(python3 -c ' *)` —
  and there is no such rule in `.claude/settings.json`.** Not in the allow
  list, not anywhere; `Bash(python3 *)`, which `CLAUDE.md` also cited, is
  absent too. The hook's docstring asserted it, `CLAUDE.md` asserted it, and
  the 2026-09-09 entry above reasoned from it. **Three documents agreeing is
  not evidence when they are copies of each other** — §11's standing rule is
  "do not trust a document over the code", and the code here was 17 lines long
  and never opened.

  **AND THE ALLOW RULE WOULD NOT HAVE HELPED, WHICH IS WHAT SETTLES IT.**
  `settings.json` sets `blockReadsOutsideWorkingDirectories: true`. Under that
  block a command the shell parser cannot analyze asks Helen *whatever the
  allow list says* — the checker must prove the command reads only inside the
  working directory, and it cannot prove that about code it cannot see. The
  prompt said so in as many words. So:

      python3 -c '<anything at all>'   unanalyzable  -> ALWAYS asks
      python3 tmp/thing.py             one path      -> silent

  **THE THRESHOLD WAS MEASURING A QUANTITY THAT DOES NOT EXIST.** Its three
  calibrations (160 → 120 → 100, each from a real measurement, each recorded
  above as a correction) were all hunting for a length at which an opaque
  command stops being opaque. Every one of them was a better estimate of a
  number that isn't there. **A guard tuned by measurement can still be tuning
  the wrong dimension, and repeated corrections in one direction are the
  symptom** — three times the answer was "shorter", and the real answer was
  "not at all". The hook now refuses every interpreter `-c`/`-e` program;
  `sh -c`/`bash -c` (the credential helper) and file arguments still pass.
  Verified by breaking it on purpose, 19 cases, including the 78-character
  command above.

- **2026-09-10 — `scripts/gh-agent.sh`, BECAUSE SAFE IS NOT THE SAME AS
  CHECKABLE, AND THIS IS THE SECOND TIME THAT DISTINCTION HAS WON.** The
  documented shape for `gh` was `GH_TOKEN="$AGENT_GH_TOKEN" gh ...`. It is
  genuinely safe: an environment assignment hands the value to `gh` and prints
  nothing, and `CLAUDE.md` sanctioned it explicitly. Helen rejected such a call
  on sight anyway — *"Please don't print tokens. Is there anything we can do to
  stop this? If I've misunderstood then I apologise."*

  She had not misunderstood; she had done the only thing available to her.
  **This is verbatim the argument that retired `${TOK:+set}` on 2026-09-09**
  (§11, the entry above): from the outside, a command with a secret's name in
  it is indistinguishable from a leak until you have run the rule in your head,
  and *"I shouldn't have to reject the call!! I'm only human!"* The fix that
  worked there works here — **make it checkable at a glance rather than merely
  safe.** The name now lives in one file, read once; every call site reads
  `sh scripts/gh-agent.sh issue list --repo ...` with no secret in it.

  Run via `sh`, so no execute bit and so no chmod (which is Helen's call, every
  time). It deliberately has **no check that the credential is present**: the
  first draft had one, and that guard clause both named the token in an `echo`
  and probed for it — two things §11 already forbids, reintroduced inside the
  very file meant to clean this up. Use it and read `gh`'s 401.

  **The generalisation, now that the same shape has produced two rulings:** a
  rule whose safety a human must verify per-call has moved the work onto the
  human, not removed it. Prefer the form that needs no verification, even when
  the form being replaced was never unsafe.

- **2026-09-10 — THE SIXTH HOOK, AND THE FIRST ONE THAT ENFORCES A RULE THIS
  FILE HAD ALREADY WRITTEN IN FULL.** Helen, having permitted two calls by hand
  within minutes of each other: *"can we either avoid needing to request
  permission, or block the command if it can't be statically analysed?"* Both
  halves were built — allow rules in `.claude/settings.json` for the routine
  calls, and `guard-unanalyzable-bash.py` for the rest.

  **THE RULE WAS ALREADY THERE, STATED BETTER THAN THE HOOK STATES IT.**
  `CLAUDE.md`'s working-practices section already ended: *"All of these rules
  are one rule... The permission checker proves, before anything runs, that a
  command touches only the working directory. It can do that only for a command
  whose text is its whole meaning."* Six shapes named, one consequence each,
  and nothing but care behind any of them. **That is now six hooks, and every
  one exists because a written rule was read and then broken.** The generalised
  version of this repository's most-repeated lesson: a rule that depends on
  care will be broken at a rate proportional to how often it is met, and the
  well-written ones are met most often.

  **WHO PAYS IS THE WHOLE ARGUMENT FOR BLOCKING RATHER THAN ASKING.** A prompt
  is not a refusal. It is an interruption, and it lands on Helen rather than on
  the session that earned it; a denial lands on the session, which writes the
  script and carries on. Every friction rule in `CLAUDE.md` ends on that same
  sentence — *"the cost is never a refusal, always an interruption to Helen"* —
  and until now the mechanism did the opposite of what the sentence asked.

  **A REAL BUG, FOUND BY BREAKING IT ON PURPOSE, AND IT WAS A CORRECTNESS ONE
  RATHER THAN A FRICTION ONE.** The first draft blanked BOTH quote kinds before
  looking for `$(...)`, so `git commit -m "$(cat tmp/msg.txt)"` walked straight
  through. **The shell expands substitution inside double quotes** — the exact
  distinction `guard-token-expansion.py` draws for `$VAR`, and the guard's own
  docstring claimed to draw. So: both quote kinds are stripped before the
  `&&` / `||` / `;` / `|` / glob tests, and only single quotes before the
  substitution test. Prose about substitution belongs in single quotes.
  35 cases, 0 failing.

  **What it deliberately allows**, because a guard that fires on harmless
  invocations is one you learn to route around: redirection to a static path
  (`2>&1` and `>/dev/null` included — a redirection names its file, so only a
  PIPE hides a later stage); quoted operators and globs; and a bare `$VAR`,
  left to `guard-token-expansion.py` because a `$` in a regex is far too common
  to pattern-match. The probe deliberately loads its ALLOW cases with commands
  actually run in the session that built it, so a guard that would have blocked
  real work fails at the probe rather than mid-task.

  **The honest cost, stated so it is not a surprise:** `| tail -3` after a
  pytest run is gone, and so is every other convenience pipeline. That is what
  `CLAUDE.md` has asked for since 2026-09-08 in Helen's own words — *"if they
  take or emit variables, please write a script in tmp/"* — and the second
  payoff is the one she named then: the script is a record of exactly what was
  measured, which a one-off pipeline never is.

- **2026-09-10 — THE MERGE DENY, WHICH IS THE PART OF THAT SETTINGS CHANGE
  WORTH READING TWICE.** Allow rules for the `gh` wrapper were written per
  subcommand rather than as `sh scripts/gh-agent.sh *`, and `pr merge` and
  `pr review` were added to the DENY list in all three spellings.

  **Because a blanket allow would have removed the last thing standing in front
  of a merge.** §11's own entry for 2026-09-09 says it plainly: `CLAUDE.md`
  used to end the permissions section *"the token is scoped so the rest is
  impossible"*, and for merging that stopped being true when the classic
  `repo`-scoped token replaced the fine-grained one. **Merging is now held by
  the rule alone.** A convenience allow-list is exactly the kind of change that
  would have quietly removed even the prompt, while looking like nothing but
  friction relief — and a deny rule cannot be overridden by an allow.

  The general shape, worth keeping: **when widening permissions for
  convenience, the question is not "what do I want to stop prompting" but
  "what was that prompt the last guard of".**

- **2026-09-10 — `pr edit` IS THE FIRST `gh` CALL THE CLASSIC TOKEN CANNOT
  MAKE, AND IT FAILS ON SCOPE, NOT ON PERMISSION.** `sh scripts/gh-agent.sh pr
  edit 932 --body-file ...` returned GraphQL errors asking for `read:org` on
  the `login`, `name` and `slug` fields — `gh` resolves the PR through
  GraphQL for that subcommand, and the classic `repo` scope does not cover
  those. `pr create`, `pr view`, `pr comment`, every `issue` subcommand and
  `api` are REST and unaffected. **The finding is a narrowing, which is the
  rarer kind**: §11's rule that a widened token is invisible until something
  unexpected succeeds has a mirror — a scope gap is invisible until something
  routine fails, and this one waited a day. The fix needed nothing the token
  lacks: `sh scripts/gh-agent.sh api -X PATCH repos/<owner>/<repo>/pulls/<N>
  -F body=@tmp/body.md`. Recorded in `CLAUDE.md`'s `--body-file` bullet and
  MANUAL §11; "never broaden access" is untouched.

  **AND A THIRD WRAPPER, FOR THE SAME REASON AS THE FIRST TWO.** A worktree in
  the container cannot clone the drafts repo by the SSH form MANUAL §9.1 gave,
  so the session that needed it hand-wrote the HTTPS URL — token name and all —
  into a `tmp/` script, which is exactly the call-site shape the two wrappers
  above exist to retire. `scripts/git-clone-agent.sh <repo> [dir]` now; the
  manual gives it beside the SSH form. Proved by cloning into `tmp/` and
  deleting the result.

- **2026-09-10 — THE TOKEN LEAKED THROUGH THE DOCUMENTED PATTERN, AND THE
  FIX'S FIRST VERSION BROKE EVERY OTHER WORKTREE.** Two lessons in one
  afternoon, both worth more than the incident.

  **THE LEAK WAS NOT A RULE BEING BROKEN.** §9.1's entry of the same date has
  the mechanism: `CLAUDE.md` said to clone with the token in the URL's
  userinfo, git stored that URL as `origin`, and a routine `git remote -v`
  printed it. Four hooks had been written against `echo`, `printf` and the
  default expansions, and none could see a secret that had been written to
  disk hours earlier by a command every rule allowed. The session that found
  it built the right thing — `scripts/git-credential-agent-token.sh`, so the
  token is handed to git on a pipe at the moment of use and is never in a
  string at all — and widened `guard-token-expansion.py` to refuse the URL
  shape and, for the first time, to read the script FILE a command runs.
  That last part closes the hole every other guard's advice opens: "put it in
  a file" had been a way past the checker, and now the file is checked. The
  wrappers that still built the URL (push, clone, and #937's fetch) were
  converted to plain URLs plus the helper; nothing in the repo embeds a
  credential in a URL any more. **Helen rotated the token**, which is the only
  thing that actually undoes a leak; every hook is a bandage over an exposed
  credential until that is done.

  **"CONFIGURE IT PER REPO" WAS WRONG, AND THE WAY IT WAS WRONG IS THE KEEPER.**
  The helper was set with `git config credential.helper` in
  `/workspace/.git/config` — a file the primary checkout and every worktree
  share, which nobody had needed to know until then. Git runs a configured
  helper from each worktree's own top level with the relative path as written,
  and the script existed on one branch. Result, measured from an unrelated
  worktree: `sh: 0: cannot open scripts/git-credential-agent-token.sh: No such
  file` on every push, silently tolerated by git because the token was still in
  the URL, and a hard failure the moment the URL was made plain. **So the
  ruling is per invocation, never persisted**: each wrapper passes the helper
  with `-c` and an absolute path resolved from its own location, the shared
  entry was removed, and nothing depends on which branch any worktree is on.
  The general shape: a per-repo setting in this repo is a per-worktree
  setting for everyone, and a path in it is only as real as the branch it was
  typed on. #937 and #938 were superseded by one PR carrying both, this ruling,
  and the converted wrappers, so neither merges with the old advice in it.

- **2026-09-10 — CLOSING ONE HOLE OPENED ANOTHER, IN A DIFFERENT FILE, THE SAME
  DAY.** `guard-unanalyzable-bash.py` refuses a leading `cd`. `CLAUDE.md`
  documents `cd _food_drafts && git ...` as the way the nested drafts repos are
  edited. So the new guard left `git -C <path>` as the only route into a nested
  repo — **and neither git guard could read it.**

  **`guard-main-branch.py`** recognised the form (its comment even says
  "allowing for global flags like `git -C x commit`") and then resolved the
  TARGET DIRECTORY from a leading `cd` alone. No `cd`, so it asked the outer
  worktree which branch it was on, saw a feature branch, and allowed the commit
  — while the drafts repo sat on `main`. That is the 2026-08-17 failure exactly:
  four commits straight onto `_cocktail_drafts`' `main`.

  **`guard-destructive-git.py` was worse and in a different way.** Its command
  pattern was `\bgit\s+(?:-\S+\s+)*`, which allows a FLAG but not the VALUE
  after it — so in `git -C _food_drafts reset --hard` the `-C ` matched,
  `_food_drafts` did not, and the whole pattern failed. Every destructive
  command aimed at a nested repo this way **walked past the hook unrecognised**:
  not judged and permitted, never looked at. It also ran `git status` in the
  process's own directory, so even once recognised it would have judged the
  wrong tree.

  **THE LESSON IS ABOUT GUARDS AS A SET, NOT ABOUT REGEXES.** Each hook was
  correct when written and stayed correct in isolation. What changed was the
  behaviour they push you towards: a new guard made the documented form
  impossible, and the only remaining form was the one two older guards could not
  read. **A guard that redirects behaviour has to be checked against every guard
  that reads the same commands** — the question is not "is my rule right" but
  "what will people do instead, and who is watching that".

  Both are fixed and both were proved by building a throwaway repo in `tmp/`
  that actually sits on `main` (or actually holds uncommitted work) and asking
  the hook about it — 11 cases and 7 cases, 0 failing. **The probe found a
  second bug in the first fix**: `cd a && git -C b` runs in `a/b`, because a
  `cd` moves the shell and a later `-C` moves git again relative to it. The
  first fix took the `-C` path alone and resolved it against the worktree root,
  which reopened the same hole one case to the left. The two compose; they do
  not compete.

  **And a false positive in the new guard, found by tripping it.** Its
  quote-stripper did not honour backslash escapes, so
  `grep -n "PATTERNS\\|re.compile(r\\"x" f.py` — an escaped quote inside a
  double-quoted pattern — read as an unterminated span, exposed the `|`, and was
  refused as a pipe. Escapes are honoured now (and deliberately not inside
  single quotes, where the shell treats a backslash as literal). A guard that
  refuses a legitimate command is one you learn to route around, which is the
  failure this repository names in three other hooks and had just committed a
  fourth time.

---

- 2026-09-10: "There is no `gh` at all in a worktree" (§1) was true of a
  worktree on the host and false inside the devcontainer, whose image installs
  it; a session spent a turn writing a REST call before `which gh` answered
  `/usr/bin/gh`. Now stated per environment.
- 2026-09-10: §1 gained the headless browser. Until then the manual's own
  advice for anything visual was to build candidates and let Helen look,
  which was right, and the fixes themselves shipped "reasoned rather than
  seen" (#895's own words). Helen's grant, the Dockerfile's fifteen packages,
  and `scripts/browser/` are what changed; the phone pass (#899, #900, #901,
  #903) was the first work done by looking.

## §12 Traps — the stories

- **The rule written instead of followed** — 2026-08-19, `about.html`'s
  `site_key` (§2.4).
- **Markup shared, CSS forked** — 2026-08-19, #374 (§2.5).
- **The wrong layer measured** — 2026-08-31, the umbrella suppression
  (§9.3.3).
- **A source-scanning guard fooled by its own explanation, six times**,
  2026-08-19 to 08-31: the destructive-git hook's own commit; `r.hasWordMatch`
  counted in a comment above the function; the draft-registry test flagging
  itself; "skip" matched as a word; `ingredient-search.js`'s comment containing
  "rewritten" (#428); `test_a_filter_state_binding_is_only_asked_for_what_it_has`
  failing on the paragraph explaining its own bug, within a minute of
  existing.
- **The parser reading documentation as code** — 2026-08-26, the magic bag's
  Liquid comment.
- **The third link shape** — #353's `](#fragment)`; the ganache tagline
  pointed at `#nonexistent-anchor` and 18,886 checks passed; the obvious test
  failed thirty recipes because `#doneness` belongs to the layout.
- **The corpus glob that named files** — `about.html` invisible to
  `test_page_links.py`'s literal list.
- **The guard scoped by the value it polices** — 2026-08-31, ti-punch's `no
  garnish` invisible to a guard that skipped lists not containing `none`.
- **The registry asserted non-empty** — 2026-08-31, `proposals`, wrong within a
  day.
- **The exemption that silenced downstream checks** — 2026-09-02, #585, Royal
  Bermuda Yacht Club; seven stale rows.
- **Our own work exempted** — `QQ Claude`, eleven days (§5).
- **The stale fetch** — 2026-08-31, reported branch state from before four
  tool calls of work; wrong in both directions after Helen said "I thought
  I'd merged that".
- **The test that cannot fail** — a stale `JS_DIR`; a non-recursive SCSS glob;
  `garam-masala-powder.md`'s `step:` singular with no `name:` (2026-08-10,
  `test_method_groups_have_name_and_steps`); a tagline link to
  `../garam-masala-powder.md)` (`test_internal_links_are_well_formed`); the
  print-background guard (2026-08-14, above).
- **Script order** — `assets.js` moved to the end of `<head>` after weeks of a
  silent bug; guards for `ingredient-search.js`/`recipe-list.js` before
  `filters.js`.
- **Colours moved, numbers stranded** — aureolin between filter slots; the
  category-code bar's `-active` tokens.
- **Asymmetric padding** — 2026-08-02, `.site-logo-top`'s `padding-right:
  0.18em` doubling the letter-spacing trailing gap, invisible until
  cocktails' wider word defined the column.
- **SVG formats** — `backgrounds-headers/`'s 100 Inkscape exports open with
  `<svg\n   width=`. **Two transforms** — #599 (§9.11).
- **The cross-reference nothing re-checks** — the "raises every ratio to a
  power" comments, one of them an instruction.
- **Rename un-ignores** — the plural `_cocktails_drafts`, 229 files.
- **The generator that stopped generating** — 2026-08-21,
  `cooking_methods.yml`: both scripts said "re-run", a re-run would have
  dropped 166 hand-edited lines; caught by taking a backup first.
- **The unpushed branch** — 2026-08-29 (§11).
- **The patch read as the output** — 2026-08-29, the tidy pass's 341 files.
- **YAML re-serialised** — never, across several hundred edits.
- **The force-push rejection** — 2026-08-02, a rebase artefact.
- **Rejected tooling** — `jekyll-seo-tag`, Stylelint, a bundler, a CSS
  framework, schema.org/Recipe (it would push adapted magazine recipes into
  Google's rich results).
- **Flex for a two-part row** — `.method-full li` (§4.2).
- **The bare element selector** — `article.recipe a` (caught, #40) and
  `.recipe-row-content a` (missed; every index badge took the title's 1rem
  until Helen's screenshot, #258). #259 opened to build a lint and closed
  rather than half-built.
- **Inheritance into a nested control** — `.btn-method-toggle` wearing its
  heading's emboss, found by Helen comparing it side by side.
- **The nested rule voided by a markup move** — 2026-08-16, #275, `.btn-reveal`
  shipped with no styling while 17,170 tests stayed green. **The Liquid
  condition on the wrong field** — `item.item`, 2026-09-05.
- **The `:not()` that could only add** — 2026-08-30, #589: the results pool was
  4px TALLER empty than full, and the visible symptom was a chip jumping
  after a click (*"if I click a chip, it then jumps downwards by a few
  pixels, but should stay in the same place."*).
- **Lightness-only state** — 2026-08-16, the footer links and the reveal link;
  Helen's sentence both times: it "doesn't change on mouseover or click".
- **The generated sweep** — `nameQuery`, `isSearching`, two rival predicates,
  then the LEAVE OUT box (#274, 2026-08-16).
- **The photo batch** — 2026-08-21, 43 photos, an ordinal survey, three
  cookbooks and an AI-chat screenshot; 2026-08-31, two captures that ended
  mid-recipe ("Stir until cold,").
- **The worktree with the lost work** — 2026-08-22 (§9.1).
- **The private-repo trailer** — 2026-08-22.
- **The un-emptied collection** — #235, twice available.
- **The row that overflowed** — the footer on a phone: `1fr` will not shrink
  below min-content, 240px of hearts plus gaps ≈ 392px against 360.
- **DOM order and the positioned layer** — `.site-nav-icons` under the rotated
  tape on a phone; fixed structurally (its own line below 600px), not with a
  z-index.
- **The clipping `<svg>`** — 2026-08-26.
- **Four browser facts** — 2026-09-02: the black-on-black inputs (black text
  on black); the shadow under the search-hit underline; `<mark>`'s yellow
  returning an hour after the comment warned; `index-section-label`'s
  arguments.
- **Five traps from one design session** — 2026-09-02 (§9.13 above): nineteen
  unbalanced `*/`; `--tape-pad-top` invalid at computed-value time and
  computing to zero on all four sides; the frozen `var()`; the retyped
  `height="100%"`; the text nudged for a fact about the artwork. And: told
  twice the tape was "still small", every measurement of the BOX was right
  and none was about what was painted in it.

---

- **2026-09-10 — A SCRIPT TAG DESCRIBED IN A COMMENT AND NOT WRITTEN, FOR TWO
  DAYS.** #846 (2026-09-08) deleted `chip-rows.js` and its `<script>` tag from
  `_layouts/default.html`, and the comment that replaced them explained the
  two remaining measurement passes — including `card-line-budget.js` — in
  full, while the tag for that one had gone with the other. `cocktail-index.js`
  guards its call (`if (HTF.cardLineBudget)`), so #776's budget never ran again
  and nothing went red: the pure tests run the file inside a stubbed window and
  never ask whether a page loads it. Found only because the pass gained the
  ship-collision check the same night and marked nothing on a first deal where
  seven cards collided; the probe reported `hasFn: "undefined"` and
  `scripts: []`, which is the kind of answer only a browser gives. The tag is
  back, `test_the_card_measurement_passes_are_loaded_in_order` names the pair,
  and MANUAL §12 carries the trap beside its cousin about load order. The
  generalisation: a guard that reads a FILE proves the file; only a test that
  reads the LAYOUT proves the page.

## §13 The visual design — the road to each value

- **2026-07-31 / 2026-08-01 / 2026-08-02** — Recipe page redesigned; index
  brought onto the same mark, then reworked (row layout, category-code bar,
  pagination, shuffle). The mark replaced watercolour washes because an
  identical repeated mark is recognised, not read. A fifth hue tried for links
  (`$color-vivid-rose`, 08-02) and reverted the same day for magenta — 5.26:1,
  cohesiveness with the title rule over distance from the footer hearts.
  Sixteen distinct gaps collapsed to a named scale.
- **2026-08-03** — The category-code bar removed after four rounds of tuning.
  Helen took the emboss OFF the active filter states: the category colour
  lives in `.tag-shape` and the punched treatment means "landmark". Results
  heading left-aligned (right-aligned it "read as stray rather than placed").
  Violet's second job: the annotation arrow.
- **2026-08-10, #122** — The tape background redesigned (`generate_tape.py`,
  seven files: tape-1 30 both_acute, tape-2 32 both_acute, tape-3 33
  both_acute, tape-4 35 both_obtuse, tape-5 36 both_obtuse, tape-6 40 mixed,
  tape-7 45 mixed; marks seed = seed). Helen's read after a real batch: no
  consistent corner winner — mix all three. `.site-logo-word`'s fill pulled off
  white to `#e7e2e3` so a brighter copy has room; four copies. Rejected: a
  flat bigger offset ("looks raised up and left... and not well"); a gradient
  fill ("looks like the lettering is made from twisted wire"); gradient plus
  bevel ("good, but I prefer the crispness of B... even if less, you know,
  accurate"); higher-contrast pulls (the lighter one read as raised).
  `[ FOOD ]` excluded from the shared treatment — reconfirmed 08-12: *"please
  note in the docs that [ FOOD ] is handled differently — I think it needs the
  special treatment."*
- **2026-08-11/12** — The reference pages (§14).
- **2026-08-12** — The punched effect on EVERY heading from one base rule;
  the three fixed stroke tokens retired for `$emboss-stroke` (0.014em then);
  the ratios came from where two working elements sat (HELEN TRIAGES at 6.3%
  offset; the Tips label — *"it looks better than the lettering for my
  existing page headings — am I imagining this?"* — she was not). Helen asked
  again whether active filter states should take the emboss (*"I could argue
  it either way"*) — no on both counts. "N survivors" bare — *"I liked it
  bare"* (it was "fixed" once by accident). `.recipe-body-content h3` stopped
  being an exception.
- **2026-08-16, #275** — The reveal link centred under I KNOW WHAT I WANT with
  the wordmark's grid trick; the first attempt was ~116px too wide because a
  spanning grid item sizes an intrinsic track. The stack and the link were
  deleted 2026-08-30 (#586).
- **2026-08-19, #387** — Going back restores the index (§13.7). Built on the
  back/forward cache first, which was wrong: `jekyll serve` sends `no-store`
  (measured with `curl -I`), so bfcache can never apply on :4001 and the page
  Helen looks at all day would have disagreed with the live one. Helen saw
  the reshuffle with her own back button. Why `toQuery()` stays unwritten.
- **2026-08-19, #389** — Active filter tags shifted their neighbours: two
  bugs in one placeholder (`font-size: 0.74rem`, `letter-spacing: 0.04em`
  matching neither resting base); the fix a deletion.
- **2026-08-21, #396** — Icon-coverage test checks only the BASE class (31 of
  41 icon classes are modifiers).
- **2026-08-24 to 08-26** — `$font-label`: the recipe list spent two days in
  IBM Plex Mono and came back; five elements held the face and returned
  (`.category-label` on size; `.btn-tag`/`.btn-star`/`.btn-meta` and `.badge`
  on pairing — *"this actually seemed fine when the fonts were more
  different"*; `.recipe-title-link` on nothing measurable — *"I could justify
  it intellectually by counting font groups, but it could well be that I got
  used to seeing the typewriter effect and now I miss it."*). #373 (PDF fonts)
  led to self-hosting three faces; rejected Open Sans (*"aggressively blah"*),
  Cousine, Myriad Pro. #470: the tape word re-tuned for Courier Prime (fill
  `#ECE9EA`, offsets 1.0/1.8px). Helen re-tuned `$emboss-stroke` to 0.016em
  (the heavier face wanted MORE edge); `$emboss-offset-large` 2px → 1px ("two
  letters, not one raised one"); the emboss shadow 0.38 → 0.68 and the
  highlight to white (the ceiling argument) — both superseded by the tiers on
  09-02. The heading dials removed from `/dev/emboss/` at Helen's ask (she
  could not get the wordmark and its controls on screen together). #477:
  HELEN TRIAGES kept its heavier numbers — *"I prefer the old HELEN TRIAGES...
  I like the drama."* (reopened 09-02).
- **2026-08-26** — `.badge--matched` gained the faux-bold so a matched badge and
  its filter button read as one idea.
- **2026-08-30, #583 / #586 / #562** — The food index converging on cocktails'
  shape: HAS TO HAVE was `SEARCH MAIN INGREDIENTS` (named the mechanism);
  LEAVE OUT came out from behind its reveal link (the framing was the only
  thing the disclosure bought); META FILTERS from five buttons to one —
  Helen asked for "all metadata chips" off the rows (*"I am perfectly well
  aware of how much work I have done on each drink"*).
- **2026-09-02 (design review, PR #660)** — The fold: the first recipe sat
  ~1,200px down; Helen chose "tighten" over three louder candidates (a
  "more" link — "loses what the page is here for"; a side rail — "makes the
  page look like even more work"; a strip of random rows). The universe says…
  on food for two days. `.on-dark` deleted. The tiers (`LETTERING.md` §11 has
  the seven rulings in order): *"off black front letter with a very thin
  darker outline, and a lighter black (or even light grey) up and left...
  similar aggression, without asking physics to go lighter than white"*;
  *"T2 wordmark, T1 large headings. Surprisingly T1 is good on the small
  headings too, but I prefer T3, flat with edge, so let's do that."*; *"HELEN
  TRIAGES is not treated the same way as the other headings and should be"*;
  the tape word matched to cocktails' wordmark, then *"Please treat
  [ COCKTAILS ] the same way we now treat [ FOOD ]"*; *"FAQ headings need to
  be darker, possibly simply matching SERVES / PREP / COOK"*; *"recipe title
  goes hard like the wordmark please, thanks for letting me change my
  mind"*. $font-label settled: *"Please apply Plex amounts on the drinks page,
  and the doneness charts and timing calculator. Send note labels back to
  Courier."* — `.note-label` the last to return, after holding the face since
  08-24 under a rule that was a proxy for the true one.
- **2026-09-04 (design audit)** — Food's universe turned down: *"This advice
  was the only part of the design review I disagreed with. Having all the
  dolly mixture colours visible together and first thing pleases me. I don't
  think anyone (and certainly not me) opens a triage website to click on a
  random recipe. And given the styling is hard, my gut says that trying to
  polish it is solving the wrong problem."* The mark under the last line only
  (critical #7). Row titles to 1.2rem / 700 (critical #2, "the list reads as
  metadata with a name attached"; a punched version "fuzzy"). Pills muted at
  rest with her three-rung ladder: *"leave the buttons entirely muted until
  hit by a filter, when they should take your middle saturation, then the
  loudest active state for mouseover."* Index colours reordered to her five
  tests; `$color-electric-cobalt` deleted, LEAVE OUT with no code colour.
  Whether the recipe title takes the tape: offered and declined.
- **2026-09-05** — Leopard tracked as its own issue; Helen holds it
  (`LEOPARD.md`: round one L3 sheen — *"The sheen really brings it to
  life"*; *"Leave leopard with me… don't ship anything."*).
- **2026-09-06** — META FILTERS gone entirely: *"I don't want this block on the
  index page any more. It was useful when I was still ingesting recipes I
  know, but it's not now I've done most of that."* Two rulings reversed by
  looking (§9.13).

---

- **2026-09-07, #783 — a pinned grid COLUMN does not reserve its cell, and a
  DATA edit is what exposed it.** The footer is `1fr auto 1fr` with
  `.site-footer-centre` carrying `grid-column: 2`. The comment beside it claimed
  that pin "resolves it before auto-placement runs". **It does not**: a definite
  column with an AUTO ROW is still auto-placed, so the two reference navs were
  positioned first, in DOM order — nav 2 took row 1 column 2 and the hearts,
  still needing column 2, dropped to ROW 2.
  - **It could not have been seen until the day it broke.** A neighbouring
    comment said so in as many words — *"UNVERIFIED BY EYE: nothing renders a
    second column yet"* — and the rum reference page (#529) made cocktails
    render one. So the fault arrived with a change to `_data/sites.yml`, no CSS
    edit, on every page of both sites at once. That is exactly the failure the
    pinning comment said it was preventing, which is why the sentence was
    corrected rather than deleted.
  - **The fix is to place all three explicitly**, so auto-placement has nothing
    to decide. A guarantee that depends on DOM order is not one.
  - **AND THE FIRST ATTEMPT WAS THE WRONG FIX, which is the part worth keeping.**
    Reading "right-align with whole page" as the viewport, `max-width` came off
    `.site-footer`. That sent the LEFT column to the viewport edge, left the
    right one exactly where it was, and broke an alignment another comment in the
    same file had deliberately built. Helen: *"I would like each to be under the
    sides of the main page container."* **A CSS change that compiles correctly
    can still be the wrong change** — the compiled output was verified and
    reported as reassurance, which was true and useless. Her screenshot found in
    one image what grepping the stylesheet could not.
- **2026-09-07, #776 — the card's three stacks share one budget.** `$card-height`
  is fixed, and the ingredient clamp (#552) and the chip cap were each raised to
  three on their own, with nothing stopping all three being spent at once. A
  wrapped name now caps both; three rendered ingredient lines cap the chips.
  - **Only half of it needed a script.** `.drink-card-name--wrap` already exists
    from card-name-fit.js and is a SIBLING of both, so `~` reaches them. The
    other half does: CSS can ask how many lines an element is ALLOWED, never how
    many it rendered, and most cards do not reach the clamp.
  - **A hidden card measures zero.** The index paginates with `card.hidden`
    rather than by removing cards, so the load-time pass classified page one and
    nothing else; every later page kept the cap it should have lost.
    cocktail-index.js re-runs it on each pass, BEFORE `markChipRows()`, because
    the budget decides the chips' max-height and the row marks describe where
    they broke. **The same trap applies to any future card measurement.**
- **2026-09-07, #823 — grow the TARGET, not the control.** The card's shortlist
  mark was a ~22x25px hit area and padding could not fix it: the title's
  reservation is computed from the button's own metrics, so every millimetre of
  padding is a millimetre off the tape. An absolutely-positioned `::after` takes
  it to ~44x42px without entering layout, using space that was already empty —
  the card's own padding above and right, and the gap the reservation already
  keeps clear of the tape on the left. It claims the top-right corner from the
  card link, which is the trade: that corner is the worst place to aim for "open
  this" and the best place to aim for the mark.
- **2026-09-07, #777 — a hover says WHICH question, not just "touchable".** The
  filter chips hovered to hot magenta in every section; the section colours
  already mean the thing hover was saying, and `.is-on` has worn them since #548.
  Hover and selected now agree on hue and differ in how they wear it. Done as a
  custom property re-pointed on the section wrapper (#636's proven shape), so a
  fourth section is one line.
- **2026-09-07, #704 / #651 — two small ones with a rule in them.** Three glass
  options read as a comma list with a final "or" (`old fashioned, coupe or nick
  and nora`), no Oxford comma, because "coupe, or nick and nora" would suggest
  the last option is a pair. And `$color-electric-absinthe-wash` is KEPT with a
  comment rather than deleted: it is one of five `-wash` values derived as a set,
  and deleting one member makes the set look arbitrary. What #651 forbade was it
  sitting there unread AND unexplained.
- **2026-09-10, #644 / #779 — batch offered, pick not yet recorded.** Twelve
  candidate tape backgrounds from `scripts/generate_tape.py`, four each of
  `both_acute` / `both_obtuse` / `mixed`: seeds 101-104 (acute), 111-114
  (obtuse), 121-124 (mixed), marks seed = seed except three that deliberately
  pair a corner seed with a different marks seed to show that axis varying too
  (103/203, 113/213, 123/223). Shown alongside the live seven (tape-1..7, this
  section's 2026-08-10 entry above) at wordmark size and at a real card's size
  on one candidates page, MANUAL §13.11's own recipe — reproducible byte for
  byte from the seeds above, nothing kept only in `tmp/`. The same page carries
  a "header tape: random / fixed 1..7" switch on the real header wordmark for
  #779. Nothing shipped on that day: no file added to `assets/img/chrome/tape/`,
  `_data/chrome.yml`'s `tape_count` untouched. The one code change made is
  `assets/js/decorations.js`'s `FIXED_TAPE_INDEX` constant, added so #779's
  "fixed" answer is a one-line flip rather than a future edit to `tape()`
  itself — `null`, today's random-every-load behaviour, unchanged until she
  says otherwise.
- **2026-09-11, #644 — Helen's pick: fifteen tapes.** *"From the new set,
  don't use 1 and 7, but let's keep all the rest. Please retire tapes 2 and 5
  from my current (live) set -- the placement of that first big set of lines
  sometimes obscures the start of a cocktail name."* So ten of the twelve
  candidates ship (b02–b06 and b08–b12) and two of the original seven go
  (old tape-2, seed 32, and old tape-5, seed 36 — her reason is the one above,
  a big set of lines placed where a card name begins). The
  directory is renumbered because `decorations.js` rolls a gapless 1..N: **new
  tape-1..5 are old 1, 3, 4, 6, 7** (seeds 30, 33, 35, 40, 45 — the provenance
  in the 2026-08-10 entry above reads with that map), and **tape-6..15 are
  b02, b03, b04, b05, b06, b08, b09, b10, b11, b12** (seeds 102, 103/203, 104,
  111, 112, 114, 121, 122, 123/223, 124), regenerated from those seeds and
  checked byte-for-byte against the files the candidates page was built from.
  The reason she gave is a rule worth keeping for the next batch: a cluster on
  the left flank competes with the first letters of a card name, so a tape
  whose clearest cluster lands left is a wordmark tape rather than a card tape,
  and the set is shared.
- **2026-09-11, #779 — random each load.** Helen, on the same day, with the
  fifteen in front of her: *"#958/#779: random each page load please."* The
  #956 candidates page had put the two states on the real header wordmark (a
  sticky switch between today's random pick and each fixed tape), and she chose
  random. `FIXED_TAPE_INDEX` stays in `decorations.js` at `null` — that is now
  the decision rather than a placeholder — and stays a constant because it is
  still the one-line change "fixed" would need. The §13.1 argument against
  random wayfinding marks was never about a background texture, and she has
  now said so by looking rather than arguing (§13.11). **Then, straight after:
  *"All tape."*** Read as: the ruling covers every tape slot, the card tapes as
  well as the wordmark's. Until then `cardTapes()` dealt each card tape
  `((index - 1) % count) + 1` from its `data-card-tape`, so a card wore the
  same shape on every visit (#469's reasoning: a reload is a comparison, not a
  lottery); now every `[data-card-tape]` slot draws its own random tape per
  load, the same draw the wordmark makes. The attribute stays in the templates
  because `universe.js` selects the slots by it. If "all tape" meant something
  else, the one line in `cardTapes()` is the whole change back.

## §14 Reference pages

- **2026-08-11/12** — Built at Helen's request from 15 draft tables in
  `_food_drafts/reference-info/`. A systematic ~2× timing error found and
  corrected 08-12 (Helen's recollection: 500g/lb muddled with 1kg).
- **2026-08-13** — "Out at", never "pull at": pull is American.
- **2026-08-14** — The single page split into temperatures and timings
  (#183/#189/#202). The internal-temperature line removed from the metadata
  grid — *"I don't like the internal temperature featuring in the metadata —
  it's ugly, it spoils the rule of 3, and it's nowhere in sight when you're
  actually cooking."* Roasted duck legs use `poultry.duck` ("in the thigh" is
  exactly what a leg is). Drafts exempt from wiring — wasted work until
  cooked.
- **2026-08-15** — `sustainability.html` removed entirely (#224), never
  fact-checked; `food/reference/index.html` deleted (#218); no nav link (#213,
  won't-do-for-now). #207: the tables and the calculator do not merge.
- **2026-08-16, #246** — `cook-timer.js` opened `render()` with `var doneness =
  "rare"` and shipped no control; only 2 of 73 methods have `by_doneness`, so
  both figures render on those two cards and no control was added.
- **2026-08-16, #272** — Two footer links; deliberately the footer and not the
  nav — used *"when I'm planning out what I've decided to cook, and when I'm
  in the kitchen about to be covered in raw chicken"*.
- **2026-08-19, #382, #383, #384, #385, #386, #368** — The methods tables page deleted (nine of
  twelve sections duplicated the calculator; the steak table dropped — *"I
  know how to cook steak"*; fish and shellfish moved onto the calculator page
  — *"it's good to have the reminder about options of how to cook... they
  still have methods so they go on the methods page."*). Both pages renamed;
  no redirects. Overturned #207 for the PAGE, not the calculator.
- **2026-08-21, #400** — `groups` removed from `cooking_methods.yml` — but
  moved first: 35 paragraphs, 1,942 words, 14 links of original sourcing
  research, invisible for eight days and 30% of the JSON blob, into
  `cooking-methods-prose-archive.html` (`published: false`).
  `test_every_method_belongs_to_a_declared_group` had PASSED when `groups`
  left, having compared nothing. The generator scripts said "re-run" and now
  say the opposite.
- **2026-08-21** — `youvetsi` wired to `beef.tough_cuts` and unwired the same
  day by Helen, cooking it: *"it'll just fall off at the end, being whatever
  temperature the pan sits at for 3 hours"* — the third kind of
  `NO_TEMPERATURE_BECAUSE` entry.
- Two food-safety gaps (pork medium, fresh ham pink) flagged, not corrected —
  Helen's call.

### The cocktails reference layer, #529

- **2026-09-06, #529** — Cocktails gets its first reference page,
  `rum-categories.html`. **Why it passes #459 when a bare category list would
  not:** the bottles column. #501 moved *"which of mine is a Demerara rum?"*
  from the card to the reader when cards stopped naming bottles, and nothing
  answered it. A list of the fourteen names alone would be `rum_styles`
  reprinted. Apply that same test to any second page here.
- **2026-09-06** — The `[ COCKTAILS ]` footer column arrived with it and cost
  **no template change**, which is what `sites.yml`'s own note had predicted
  since 2026-08-19: the footer's loop always asked every site rather than
  food. The asymmetry recorded in §2.5 as "an open question, not an oversight"
  is closed.
- **2026-09-06** — **`.ref-*` is a new page anatomy, and that is not a failure
  to reuse.** Food's reference pages borrow `.recipe`/`.recipe-body-content`
  and the site's only table CSS; every one of those lives in `_sass/food/`,
  and cocktails' own anatomy is a DRINK's — a title block reserving a column
  for a glass drawing, an ingredients grid built round an amount column.
  Borrowed what there was to borrow: the drink page's absinthe-over-violette
  heading mark, and `.cocktail-suggestion`'s woowoo for a bottle name, because
  woowoo means ASKED FOR and a bottle name here is the same value as one in
  brackets on a drink page. One hue, since a second is hers (§13.12).
- **2026-09-06** — **Round one of candidates: table, stack or two columns; and
  the retired words with reasons, words-only, or off.** Helen: *"This is all
  table A"* and *"Leave reasons in full — I'll copyedit when I get to it
  (please raise an issue)"*. The other two treatments were deleted rather than
  left switchable. #784 raised for the copy.
- **2026-09-06** — **Round two: column labels, and two headings that were
  mine.** Labels repeat on **every section** (her call, and already what the
  page did). *"By age"* → **`Non-geographical`** and *"Next to rum, and not
  rum"* → **`Rum-adjacent`**, both hers. Worth recording why the first is
  better rather than merely different: "By age" named the SORT ORDER and left
  the membership rule to be worked out, while "Non-geographical" states the
  rule — the other three shelves are Jamaica, Guyana and the cane-juice
  islands, and this is what is left once origin stops being the answer. The
  styles inside are still in age order, so the name and the order now say two
  different true things instead of one twice.
- **2026-09-06** — **One rum per line, her call**, against a first version that
  ran them as a comma-separated sentence arguing three-to-eight names are one
  answer. The eight agricoles are why that was wrong: names sharing their first
  two words wrap into a ribbon, and a column you check your own shelf against is
  scanned, not read.
- **2026-09-06** — **`rum_groups` is DECLARED, not derived, and the page walks
  the groups rather than `rum_styles`.** No rule recovers the shelves —
  "Jamaican" is in two of that shelf's three style names and absent from the
  third. The cost is that an unplaced fifteenth style would be invisible with
  nothing else failing, which is what `test_rum_groups_partition_the_styles`
  exists for. `rum_groups` also had to join `NOT_GENERIC_LISTS`, and is its
  first member whose values are not strings — so omitting it raises on an
  unhashable dict instead of quietly minting fourteen generics. Luck, not
  design; the next such block will not be so obliging.
- **2026-09-06, #782** — **The sipping shelf is a shelf and not a rule**, and
  the page must not imply otherwise. Helen, asking for it: *"the name of which
  is a little against my religions because you can sip anything plus I can mix
  whatever I damn well want... but this section would help me keep track of my
  collection a bit."* It gates no search, excludes no drink, forbids no pour —
  so the block gets no category column, no card name and no "reach for this
  instead". **The DATA shape it takes, and why its members carry no `generic`,
  is §9's** — recorded there with the ruling that produced it.
- **2026-09-06** — Helen's own prices and strengths replaced my guesses in the
  same pass (Pusser's 151 £40 → £52, Ceylon Arrack £28 → £37, and Ceylon
  arrack's ABV 33 → 40, which cleared a `qq:` rather than adding one). Both
  guesses were about a quarter under. The bottles themselves are §9.
- **2026-09-06** — **Local-only is TWO switches because it is two questions.**
  Helen: *"please set it to build only locally."* `published: false` on the
  page decides whether it exists; `local_only: true` on the `sites.yml` entry,
  filtered on `show_local_reference_links`, decides whether anything points at
  it. A production build with only the first is a footer link to a 404, so
  `test_site_nav_links_resolve_to_real_pages` INVERTS for a local-only link
  rather than exempting it. Deleting both lines is the whole of shipping.
- **2026-09-10, #784** — **Most of the copy came off, and the reasons are not
  the reader's.** The page had rendered `retired_rum_styles`' reasons in full
  on the understanding Helen would copyedit them in place. She ruled the other
  way: *"my main wish is to get rid of most of the copy, to be honest! I just
  need to write a line or two under each rum label we aren't using."* So the
  reasons stay in `ingredients.yml` for the ingest and stop rendering; the
  page's lines live in `_data/cocktails/rum_page.yml`, one empty key per
  retired word, and an empty key prints nothing (§13.12: a placeholder, never
  agent prose). #888–#891 went in the same pass: "examples" for "what I'd
  reach for", the arrack note and both subtitles deleted. **Nice-to-have, not
  shipping**: *"no more until design isn't noticeably odd"*, her words, so the
  page stays unpublished. #813 (agricole rows by country) waits on #591.
- **2026-09-10, #813 — TREATMENT A: THE COUNTRY GOES INSIDE THE BOTTLES COLUMN,
  NOT INTO A ROW OF ITS OWN.** Helen asked to "split the rhum agricole rows in
  the rum reference table into countries", which most plainly means separate
  rows. Three treatments were built on the real page and she chose A: one row
  per category still, with `MARTINIQUE` / `GUADELOUPE` labels inside the third
  column.

  **THE CANDIDATES PAGE EXISTED TO SHOW A TENSION, NOT TO OFFER VARIETY**, and
  that is the reusable part. B — a row per country — renders a left-hand cell
  reading "rhum agricole blanc, Martinique", and **#591 had ruled three days
  earlier against exactly that**, choosing `origin` on the bottle over
  origin-qualified generics. A reader cannot tell a row from a category, so B
  would have reinstated visually what the data ruling rejected. Writing that
  out as a paragraph would have been arguing; building it let her see it and
  decide in one word.

  **C FAILED FOR A REASON ONLY THE BUILD COULD SHOW.** Tagging each bottle with
  its country read fine in the head; on the page the bottles sort alphabetically,
  so Martinique and Guadeloupe interleave down the column and the country becomes
  noise rather than structure. Grouping them would have turned C into A. **That
  is §13.11's whole argument in one case**: the objection was invisible until it
  was rendered.

  **The implementation follows the DATA, not the shelf.** Any style whose
  bottles declare an `origin` groups; every other row is untouched. No special
  case for "Cane juice", and it will follow `origin` wherever the field spreads.

- **2026-09-10 — "EXAMPLES" WAS PINK BECAUSE OF A GRID TRACK, AND IT READ AS A
  DECISION FOR FOUR DAYS.** Helen, choosing A: *"also the column heading please
  -- leave the pink for the bottles."* She was right that it was wrong, and it
  turned out never to have been chosen at all.

  The rum page's header row reuses `.rum-cat-bottles` on its third cell **purely
  to land in the same grid column** — and inherited `wicked-woowoo` with it. So
  one of three sibling column labels was pink and the other two were
  `$color-clear-text`. Nothing about that was intended; the class was borrowed
  for geometry and brought a colour along.

  **A CLASS CARRIES EVERY DECLARATION, NOT THE ONE YOU WANTED.** Reusing a class
  for LAYOUT imports its COLOUR, and on a page whose header says "one hue,
  deliberately — there is one kind of coloured string here, and it is the bottle"
  that turned a label into a bottle. The general form is worth keeping: when a
  class is reused for position, ask what else it says.

  It also survived a design review, a copyedit and a promotion, because an
  accidental emphasis is indistinguishable from a deliberate one once it is on
  the page. Only Helen looking at it and saying "why is that pink" found it.

- **2026-09-10, #591 — `origin` IS BUILT, THREE DAYS AFTER IT WAS RULED, AND
  THE BUILD FOUND A LIVE BUG IN SOMETHING ELSE.** Helen ruled on 2026-09-07 that
  origin goes on the BOTTLE; `origin:` appeared nowhere in `bottles.yml` until
  today. Fifteen cane-spirit bottles seeded (7 Martinique, 3 Guadeloupe, 2 Haiti,
  3 Brazil), a closed `bottle_origins` vocabulary, and two guards — one that
  refuses an undeclared value, one that requires an origin on every bottle on
  `rum_groups`' "Cane juice" shelf.

  **THE ARRACKS ARE DELIBERATELY OUTSIDE THE GUARD**, and the reason is the
  ruling's own: origin lives in the generic where it changes the CATEGORY and on
  the bottle where it changes the FLAVOUR. `Batavia arrack` and `Ceylon arrack`
  carry it in the word already, exactly as the three Jamaicans and both
  Demeraras do. Cachaça is seeded but not required, being Brazilian by
  definition. Agricole is the one cane family whose generic spans three
  countries, which is the whole reason the field exists.

  **AND THE TRAP FIRED FOR REAL, FOR THE FIFTH TIME, WITH NOBODY NOTICING.**
  `tests/test_cocktails.py` derives the permitted generics from every top-level
  LIST in `ingredients.yml`, so a list that is not a vocabulary mints its
  members as pourable generics unless it is named in `NOT_GENERIC_LISTS`. Four
  entries were already there, each added by somebody who happened to think of
  it. Listing every top-level key while adding the fifth turned up
  **`shopping_shelves`: ten AISLE NAMES — `spirits`, `fortified`, `liqueurs`,
  `fresh produce`, `flavourings`, `tops` and four more — silently valid as
  generics since the shelves were declared.**

  The prediction was on the record and exact. `rum_groups`' own note says it was
  caught only because its members are dicts and `set(value)` raises on those:
  *"that is luck, not design, and the next such block will not be so obliging."*
  `ingredient_as`, `bottle_origins` and `shopping_shelves` are all lists of
  plain strings. Two were caught while being added. One was not.

  **A GUARD FOR THIS WAS ATTEMPTED AND WAS WRONG, WHICH IS WORTH MORE THAN THE
  GUARD.** The obvious invariant — "nothing in a `NOT_GENERIC_LISTS` list may
  also be a declared generic" — is FALSE: `not_on_cards` is a list *of*
  generics, the ones deliberately kept off a card, and `families` overlaps on
  purpose (`vodka` is both a family and a pour). It went red on real data
  immediately and was deleted. **The registry says where generics are SOURCED
  from, not what is or is not a generic**, and those are different questions.

  The real fix is to invert the default: an explicit positive registry of the
  lists that DO declare generics, so a new list declares nothing until
  classified and the silent failure becomes a loud one. That is a change to the
  derivation every generic check runs through, so it is its own piece of work
  and is raised rather than smuggled in here.

- **2026-09-10 — I SHADOWED A HELPER AND NINE TESTS BLAMED THE DATA.** Adding
  `_bottles()` for the two new guards, without checking the name was free.
  `_bottles()` has existed since #529 at the top of the bottle-dictionary
  section and returns the WHOLE document; mine returned only the `bottles:`
  mapping. **Python takes the last definition**, so every pre-existing caller
  silently got the wrong shape.

  **THE FAILURE POINTED AT THE WRONG THING, WHICH IS THE PART TO REMEMBER.**
  Nine tests went red at once saying *"bottles.yml declares no bottles, so every
  check here is vacuous"* — a message written to describe a corrupted or empty
  data file. So the first move was to parse `bottles.yml` and check the block
  boundaries, and it parsed fine, 132 bottles. The message was accurate about
  what the test SAW and misleading about why.

  **An assertion message names what the test observed; it cannot name what
  caused it.** When a data-shaped failure appears the moment you have added
  code, suspect the code — and `grep -n '^def <name>'` before defining a helper
  in a 7,000-line module.

- **2026-09-10, #784 — AND THEN THERE WERE NO LINES AT ALL. The entry above
  describes a mechanism that lasted a few hours.** `rum_page.yml` was built to
  hold "a line or two under each rum label we aren't using", seven empty keys
  in her gift. Asked to fill them, she ruled the other way:

  > *"I decided not to give silly rum words the dignity of extra copy. I want
  > the list, bare, so please delete unneeded scaffolding."*

  So the file is deleted, the lookup that read it is gone, and the `<dl>` is a
  `<ul>` — **a definition list whose definitions can never exist is a promise
  the markup cannot keep.** The reasons stay in `retired_rum_styles` for the
  ingest, which is what they were always for.

  **THE PATTERN IS WORTH MORE THAN THE RULING, AND IT HAS NOW HAPPENED THREE
  TIMES ON ONE PAGE IN ONE DAY.** The subtitles (#890, #891), the arrack note
  (#889) and now these seven lines were each built as a slot for Helen's words,
  and each time the answer was that no words were wanted there. Her own summary
  was on the board the whole time — *"my main wish is to get rid of most of the
  copy, to be honest!"* — and it was read as "replace the agent's copy with
  hers" when it also meant "there should be less of it".

  **So an empty slot is not neutral.** It reads as a promise that something goes
  there, it makes the page look unfinished until someone fills it, and it puts a
  writing task on Helen that she never asked for. §13.12 says an agent ships a
  placeholder and never a sentence; this is the other half of that rule —
  **before building a slot, ask whether the thing wants saying at all.** The
  cheapest version of that question is showing her the page WITHOUT it first.

  Two dead CSS rules went with the two deletions (`.rum-retired-why`,
  `.rum-sipping`), and `.rum-cat-note` had already gone the same way earlier in
  the day. Three rules in one file styling markup nothing emitted, all within
  hours, is what a page being actively cut down looks like — worth sweeping at
  the end of such a pass rather than one at a time.

- **2026-09-10, #921 — THE COPY REVIEWED, AND THREE RULINGS OUT OF IT.** The
  first read of her prose by anyone: it needs leaving alone (the refrain
  paragraph, "sticky, impractical effort", the arrack apology), with two
  sentences flagged as anyone's ("The below is almost identical to…", "taste
  component") and left for her. The rulings were about structure, not words:

  **"blackstrap" IS ON TWO LISTS ON ONE PAGE, AND STAYS ON BOTH.** It sat under
  "These words are useful to me" and under "Rum 'styles' I do not recognise",
  and a reader sees the same word praised and dismissed on one screen. Helen:
  *"It needs to stay in the words I don't believe in section because people
  say 'use a blackstrap rum' which isn't a thing (to me). And then given I'm
  using it as a character on the site, I need to list it as a character."*
  Her fix, both halves hers: **Characters moves to the END of the page**, so
  the reader meets the word as a not-a-style first and its real job second —
  which also makes "Addendum" true, since it had been sitting in the middle —
  and the word carries a parenthetical in the retired list, *"(rum character
  not rum type)"*. The parenthetical is a lookup: any retired word that is
  also in `rum_characters` gets it, so a second such word cannot arrive
  without the note.

  **THE TAB, THE LINK AND THE h1 DISAGREE ON PURPOSE.** The page's `title` and
  the footer link say "rum categories"; the h1 says "My Philosophy of Rum".
  Asked which she wanted: *"I need links to the page to stay as 'rum
  categories' because if links say 'my philosophy of rum' the reader expects
  stories about walks on the beach and my favourite tiki mug."* So the label is
  wayfinding and the headline is voice, and the page's own header now says not
  to make them agree.

  **"none in the house" IS GONE**, the placeholder for a category with no
  bottle: *"If we're not using them, delete them, boom."* The empty third
  track is the honest rendering. Its CSS rule went with it, per the sweep
  note above. **One placeholder remains**, the column heading "category". The
  middle column's heading was the other, and it could not simply go because
  the column IS in use (it prints the shorter name a card uses, "Jamaican rum"
  for `moderately aged Jamaican rum`); told that, she named it: *"site display
  name"*. #784 stays open for the one word.

  **AND THE RUM WARMED UP THE SAME EVENING.** Told the page was nearly all
  what she does not care about, she wrote a fifth paragraph — what rum does
  taste like — through three drafts in one sitting. What she settled on the
  way is the reusable part: the list of forty-odd flavours stays whole because
  its length is the argument (*"sugar sugar, it's just endless"* is the same
  joke as the ganache's "= bad, = bad, = bad"); "freedom" came out because two
  lines after dismissing Caribbean colonialism it was the one word a reader
  could not read innocently; "a glorious rainbow of expressions" came out
  because "expressions" is the word on the back of the bottle, on a page whose
  joke is not being that; and the last sentence ends on "taste" so the next
  paragraph's "if you don't care how a drink tastes" hangs off it — her
  own requirement, stated before the wording was found. A line recommending
  Pietrek's books followed. #921 closed with the PR that carried them.

  **THE VOICE ACROSS THE SITE, since she asked how the five sit together** —
  about page, hollandaise, ganache, the taglines, this page: one voice at five
  volumes. The about page explains itself with anecdotes; the two recipes are
  the instructor who has suffered, jokes inside a formal structure; the taglines
  are that instructor at eight words; this page is the manifesto, least funny
  per line and funny in its structure. Two things hold it together: the "you"
  is always someone in the kitchen being told off, and the jokes come from
  precision (temperatures, counts of rums, a bar with a pint of fun). The
  loosest register (BRB, gap yah, hi Sue) lives only in the taglines, and
  should. Her one open note to herself: *"I'll have a think about warming the
  rum slightly"* — the page is nearly all what she does not care about, and
  "I really really like rum" carries the whole positive side.

- **2026-09-10, #920 — THE MARK WORE TWICE ON A WRAPPED HEADING, AND TWO STALE
  COMMENTS SAID IT COULDN'T HAPPEN.** `.ref-section-heading span` used
  `overlapping-rule-double` directly, the mixin the drink page's
  INGREDIENTS/METHOD/NOTES headings use — but those never wrap (always one
  word) where every heading on this page is a real sentence. `box-decoration-
  break: clone` paints a full copy of the double rule on every line fragment,
  so "Rum "styles" I do not recognise" and "Addendum: Rum Characters" wore the
  mark under BOTH lines at 390px, measured by screenshot before it was
  touched — exactly what MANUAL §13.1 and `assets/js/last-line-rule.js` exist
  to prevent on food (Helen: "Last line only please, 10000%.").

  **TWO COMMENTS (this file's header, and `_layouts/default.html`'s) SAID
  "COCKTAILS HAS NO WRAPPING CONSUMER OF THE MARK", AND BOTH WERE RIGHT UNTIL
  THIS PAGE GREW REAL SENTENCES FOR HEADINGS.** A cross-reference to another
  file's behaviour is a claim nothing re-checks (MANUAL §12); the fix corrects
  both rather than working around them. `.ref-section-heading span` now uses
  `overlapping-rule-double-last-line`, and `last-line-rule.js`'s `TARGETS`
  gains `.ref-section-heading span` as its OWN selector — not a reuse of
  food's `.section-heading-text`, which would work today only by accident (it
  carries no bare styling of its own outside `.recipe-section-heading` or a
  `--modifier`) and is exactly the "a class carries every declaration, not
  the one you wanted" trap this same file's EXAMPLES-heading bug (above,
  same date) already cost a design review to find.

  **THE NARROW-WIDTH FONT-SIZE OVERRIDE WAS ITSELF A SYMPTOM, AND IT STAYS
  ANYWAY.** `.ref-section-heading--major`'s 1.5rem at 34rem-and-under first
  shipped to cut a three-line heading to two, its own comment naming the
  goal as fewer stripes. With the mark now correct at any line count, the
  original reason is gone; the value is kept on its own remaining legibility
  merits (three lines of a 2rem major heading is still a lot of a phone
  screen), and the comment says so rather than leaving a now-false
  justification standing.

  **THE RETIRED-WORDS LIST TAKES THE SAME BORROWED FORMAT AS CHARACTERS.**
  "Rum 'styles' I do not recognise" was still a bare vertical run with no
  gutter mark, sitting five paragraphs above the Characters list wearing the
  arrow-marked `ref-marked-list` format built for this page the same day
  (2026-09-10, cited in that mixin's own header as #920's "borrow list format
  from about page"). Same shape as Characters — a flat list of members
  introduced by a colon sentence — and the about page's own `about-ways` is
  reused verbatim for two different lists rather than earning a second mark
  each, so `.rum-retired` takes the mixin's default "→" rather than a new
  glyph.

  Verified: `python3 scripts/verify.py` green; screenshots at 360/390/1280
  before and after; the DOM-level fix confirmed directly (a debug script
  diffing the heading's rendered `outerHTML`), because the shared browser-
  harness port (4010) turned out to belong to a different worktree's server
  (`fable-final-day`, confirmed via `/proc/<pid>/cwd`) — a caution for any
  session assuming a green "ok" from the harness proves it measured ITS OWN
  build rather than whatever else answers that port.
