# DECISIONS — the journal

**What this is.** One short entry per ruling Helen has made about this repo
that is still in force: its date, its issue, the ruling as a sentence, her
words where they were recorded, and her reason. Grouped by the same section
numbers as `MANUAL.md`, so a `MANUAL §n` pointer finds the mechanism there and
the ruling here.

**How to use it.** Before re-opening a question, find it here: grep
`DECISIONS_INDEX.md` (one generated line per entry), then this file. A ruling
is not permanent — Helen reverses one by looking at the built page, never by
being argued at (§13) — but it is settled until she does.

**How to change it.** Delete and replace. When a ruling changes, rewrite its
entry; do not add a second one beside it. An entry is a ruling of Helen's, or
a session's call the code now depends on and marked as such. It is not a bug
story: what was tried and what broke goes in the commit message. Aim for
300–700 bytes an entry. Then run `python3 scripts/build_decisions_index.py
--write`.

**Where the rest went.** Until 2026-10-11 this file was append-only and ran to
760 KB, most of it the story of how each ruling was reached. That text is in
git history: `git log --follow -- model_instructions/DECISIONS.md` finds the
commit that replaced it.

**Conventions.** `#N` is an issue on `DeckOfPandas/helen-triages` unless
stated. Italics in quotation marks are Helen's own words.

---

## §0 The document itself, and the companions

- **2026-08-02 — the instruction documents are precise rather than verbose,
  and stale text is deleted and replaced, never appended to.** Helen, asking
  for the handover's rewrite: *"precise rather than verbose"*, *"strongly
  consider deleting rather than automatically appending"*. Refined 2026-10-11
  for this journal, asked whether old entries may be deleted and replaced:
  *"Through this whole project I have begged to delete and replace rather than
  just append! Please please please do it!"* No back-catalogue of old versions
  is kept; git history is the archive.
- **2026-08-10 — the backlog is GitHub Issues: there is no jobs document and
  no grouped map of the tracker.** `DEV_JOBS` was retired for the tracker. Two
  maps drawn as issues (#755, then #787, 2026-09-06) were stale in six rows
  within a day and both were closed; on 2026-09-07 Helen asked for staleness,
  splits and a plan rather than another snapshot, and the corrections went
  onto the issues themselves, the one place that does not decay. No words of
  hers were recorded.
- **2026-08-31 — a cocktail ingest never fills `suggestion`, and a `generic`
  it cannot type is `QQ`.** Helen: *"I will update these when I make the
  drinks, so QQ is right"*. Not because the vocabulary would not fit in the
  standalone document; it does. Refined 2026-09-20: an untyped pour is `QQ`
  plus the source's own words, *"if it's not obvious write QQ then whatever
  the source said then I have a chance of being able to fix it myself."*
  `INGEST_ONE_COCKTAIL.md` carries both.
- **2026-09-02 — a check that guards the two standalone ingest documents lives
  in the suite, not in `tmp/`.** Helen, on the two scratch scripts it grew
  from: *"It sounds very much like they should form part of our suite."*
  `tests/test_standalone_docs.py`. Its retired-term check runs one way on
  purpose: a retired term left in a document teaches a value the suite rejects
  to a reader who cannot run the suite; a missing new term only under-serves.
- **2026-09-03 — the vocabulary blocks in the standalone ingest documents are
  generated; their prose stays hand-written.** `scripts/build_ingest_vocab.py`
  writes between marker pairs and `test_standalone_docs.py` checks both ways.
  The reason on record: *"a generator would flatten exactly the part that
  makes them work"*. Counts of terms are not written into any document: they
  were out of date three times in four days.
- **2026-09-09 — there are three instruction documents and no fourth: a
  separate ARCHITECTURE log was offered and declined.** Helen: *"if you think
  it's best then maybe start an architecture log? Fine either way."* The three
  split by reader: `CLAUDE.md` is rules for an agent, `MANUAL.md` the present
  tense (renamed from HANDOVER on 2026-09-06, *"because this is now more
  accurate"*), this journal the reasoning. Environment rulings have the same
  reader, so they are §1 and §11. A fourth file adds a "which file?" decision
  to every ruling. Only a genuinely separate audience would justify one. The
  decision was a session's, on her "fine either way".
- **2026-09-29, #1252 — a layout's comments are a few present-tense lines
  ending in a `MANUAL §n / DECISIONS §n (#N)` pointer; the reasoning lives in
  the documents.** `_layouts/cocktail.html` was 1,421 comment lines of 1,874,
  so reading fifty lines of Liquid cost five hundred. Stripped of comments the
  code was unchanged. No words of Helen's were recorded beyond the issue.
- **2026-10-11 — there is no claude.ai Project: a web chat is given three
  GitHub URLs.** Helen: *"I thought I would use the project system with Claude
  web, but it just hasn't been convenient -- the times I've wanted it I've been
  out without a laptop so couldn't add the files, and they go out of date so
  often there's hardly any point. Let's remove the feature, but keep the
  instructions for web Claude, and I can point it at the specific GitHub
  URLs."* `CLAUDE_WEB_INGEST.md` holds the URLs and the instructions. The
  upload stamp and the test that watched it are gone.

## §1 How to run it

- **2026-09-09 — the devcontainer publishes 4999 and 5000 outside for 4001
  and 4002 inside.** Helen: *"I'll always need to build the site locally from
  any branch so I'd expect to do so from outside the container, but inside the
  worktree, given it's bound... make it 4999 and 5000 or something I'll never
  use."* The old `-p 4001:4001` held the host's own 4001, so her
  `jekyll-local` could not bind it. The inside pair stays because the image's
  aliases serve there.
- **2026-09-09 — the container has a fixed name, so a second `run.sh` is
  refused.** A session's call, not Helen's ruling. Without `--name`, two
  terminals gave two containers on one bind mount, and on 2026-09-08 a
  session's branch moved under it four times. It does not guard host against
  container; a worktree is still the answer for several Claudes. Same fix:
  `REPO_ROOT` comes from `--git-common-dir`, because `run.sh` is tracked and
  `--show-toplevel` mounted whichever worktree you stood in.
- **2026-09-09 — worktrees are made on the host, never inside the container;
  `enter-worktree.sh` was rejected.** A session's call. Git stores worktree
  pointers as absolute paths, so a container-made worktree cannot be used from
  the host and the host-made ones report `prunable` inside: a second namespace,
  not a unification. Helen runs Claudes in host worktrees, so it bought nothing
  she needs. `chore/devcontainer-multi-worktree` is not merged and should not
  be.
- **2026-09-15 — Playwright, its Chromium and its system libraries are baked
  into the devcontainer image.** Helen: *"shall I pre-install Playwright (and
  its dependencies) into this Docker image?"*, then *"Please make those
  changes"* and *"Including allowing dependencies please."* Every fresh
  worktree was re-downloading a few hundred MB before its first screenshot,
  the step most likely to be skipped. `/opt/playwright`; a `tmp/browser/`
  install wins when one exists. The version is pinned twice (Dockerfile and
  `install.sh`) and `tests/test_browser_harness.py` fails when they differ: a
  bump is both files and a rebuild, the cost she accepted.
- **2026-09-21 — `run.sh` rebuilds when the image does not MATCH
  `.devcontainer/`, by a content hash in an image label, not by mtime.**
  Helen: *"I'd rebuilt the image, but my containers were being created from an
  older one."* She asked for "the Dockerfile is newer than the image"; mtime
  was declined because a fully cached rebuild keeps the cached layer's
  `Created` date, so the check would fire on every run for ever. Refined
  2026-09-24 (#1191): files named in `.devcontainer/.dockerignore` are left
  out of the hash. It cannot see the base image moving upstream; that is
  `docker build --pull --no-cache`.
- **2026-09-24, #1191 — the gems are not baked into the image.** A session's
  call, not Helen's ruling. One named bundle-cache volume survives every
  rebuild, so `bundle install` runs once, ever. The build context is
  `.devcontainer/`, so the Dockerfile cannot `COPY` the root `Gemfile`;
  widening the context would make every recipe edit change the build stamp;
  and an existing volume mounted over `BUNDLE_PATH` shadows baked gems anyway.

## §2 The mono-repo shape

- **2026-08-15, #204 — `/` is a bare redirect to `/food/`; there is no
  landing page.** The two-door landing page and its `root.scss` were deleted:
  a third stylesheet nobody checked, which broke at the next visit to the page
  nobody visits. Helen: *"No user is going to end up at the root without having
  tried to, which would be super weird. Everyone else will come in via food or
  drink"*.
- **2026-08-19, #374 — one header and one footer for the whole site, literally
  the same code and assets.** Helen: *"I don't want parity between two footers
  — I want one footer for the whole site. And one header. Literally the same
  code and assets."* One template had still been three things (no nav on
  cocktails, icon rules living in `_sass/food/`, two tape directories kept in
  step by hand). `$color-accent` is the contract variable that makes it
  possible. Her call too: the footer's reference block is a column PER SITE,
  gated on material, not "the current site's column".
- **2026-08-26, #487 — cocktails' `$color-accent` is menthe
  (`$color-electric-absinthe-deep`), not amber.** It is the colour that means
  "this is the thing you asked for", the mood filters' own; amber's job is a
  verdict about a drink and it has no business on a nav icon. It shipped amber
  for a few hours. No words of Helen's were recorded.
- **2026-09-10 — the header's second row is the door to the OTHER site: its
  icon, its word and an arrow.** Helen, choosing D of three readings built on
  a header-only page (her own site, the other site, both): *"the other site,
  icon and word, arrow on"*. Nothing had told a first-time visitor the small
  glass was a second site. A `site_neutral` page shows every site. The
  template is still one loop over `sites.yml`; #374's test now requires each
  site's row to name the other and never itself.
- **2026-09-10 — no words under the wordmark.** Helen, declining a one-line
  question there (*"What shall we cook?"*): *"No words under the wordmark
  section please."*
- **2026-09-11, #965 — the other-site row sits at the right-hand end of the
  header's second row and `??` at its left end, both on the cards' edges, at
  every width.** Helen: *"the design I would like is for the link to the other
  site (and icon and arrow) to be on the right-hand side at desktop width. I
  have changed my mind since seeing the centred design on mobile."* `??` is on
  the left *"so it doesn't look like the arrow from the central icon and link
  is pointing at it"*, with no margin (her answer: "Both on the cards' edge").
  `.site-header-inner` is 852px, the cards' width. (Replaces the centred row
  of 2026-09-10.)
- **2026-09-11, #969 — the footer's centre column reads about / GitHub mark /
  copyright / licences / hearts.** Helen: *"re-order the central column of the
  footer to put the heart SVG at the bottom -- everything else stays in the
  same place."* Margins and the grid placement were checked by eye at 1280px
  and 360px and left alone. (Replaces #915's order, hearts third.)
- **2026-10-21, #1086 — the link-preview image is the wordmark, one card per
  site; the about page takes food's.** Helen: *"About page shouldn't get its
  own preview, so just set it to the food one, same description line too."*
  (Earlier, #1086: *"The wordmark is fine for a start -- I don't think we have
  anything else that feels like branding anyway."*) `social_image` in
  `_data/sites.yml`; a `site_neutral` page takes its `site_key`'s, which is
  food. `scripts/render_social_images.py` renders them from the built site, so
  a changed wordmark means re-running it; the PNGs are committed and wear one
  fixed tape, because random-per-load (#779) is a ruling about a live page.
  (Replaces the [ ?? ] card for neither site, 2026-09-15.) The card is the
  one-line wordmark sized to the card's middle square, so an app's square
  crop keeps all of it. Helen: *"let's leave as one line. It's one wordmark,
  then a favicon."*
- **2026-10-21 — the icons step down by size: the wordmark, then HT over
  `[ ]`, then `[ ]` alone; each site has its own, told apart by colour.**
  Helen: *"I think I'm saying words over tape, then letters over brackets,
  then just brackets."* The wordmark is the 180px home-screen icon; HT over
  `[ ]` is the 32 and 48px favicon (*"32 and 48: HT over [], that was the
  realisation"*); `[ ]` alone is the 16px. Cocktails is white on black. Food
  is *"HT black on white, with [] white on black"*, and its `[ ]` alone stays
  black on white so the two sites still differ at 16px. Each tab icon keeps a
  hairline edge, so a white half holds its shape on a light tab strip.
  (Replaces the black H on magenta shared by both sites, #219.)
- **Undated — the about link in the header is a bare `??` in the body face: no
  circle, no border, no heading font.** Helen: *"much more minimalist... a
  naked ? in body font and style"*. `.site-about-link` in
  `_sass/shared/_layout.scss` is `$font-body` at weight 400, and its
  `letter-spacing: normal` is load-bearing: the header's 0.5em tracking is
  inherited and would pull the two marks apart. It is never spelled "about"
  where a nav shows it.
- **2026-08-16 — the footer is three tracks with the hearts page-centred,
  whether one reference column renders or two.** Helen, when only food had
  reference pages: *"if it looks really silly without cocktail ref info to
  balance it out then we can think again"*. `.site-footer-top` is `1fr auto
  1fr` and all three items are placed explicitly, so a lone column cannot pull
  the centre stack sideways. Both columns render today; the grid still has to
  hold for one.
- **2026-08-16 — a footer link rests in the footer's own colour and takes the
  accent on hover, focus and click.** Helen, on the resting colour: *"the
  normal darkened magenta link colour we use across the site won't work here,
  but I think it'll be obvious enough that those things are links."* On the
  hover: *"Those footer links don't change on mouseover or click -- please
  match normal page links (not the colour of the unclicked link)"*. The
  underline says link at rest. The hover is a hue change because a lightness
  change at 0.75rem reads as none.
- **2026-09-07 — the footer's two bracketed site words start on the same
  line.** Helen: *"vertically align [FOOD] and [COCKTAILS] in the footer --
  bring [FOOD] upwards."* `.site-footer-top` is `align-items: start`, not
  `center`: the two reference columns are different heights, so centring them
  puts their heads on different lines.
- **2026-09-17, #1139 — each footer column's site icon is small and inline
  with its heading, on the outside: left of the word for food, right for
  cocktails.** Helen: *"the footer icons look strange because food and
  cocktails are different lengths, so reduce the icon size and bring it inline
  with the heading, left for food and right for the cocktails."* The icon is
  1.3em. Refined 2026-09-21 (#1177), for the stacked footer below 600px:
  *"both food and cocktail icons should be to the left of their headings."*
  Centred, there is no outside edge to mirror towards.
- **Undated, #915 / #902 — the licences line sits close under the copyright
  line, and its two sentences stack on a phone.** Helen, on the gap (#915):
  *"to show they're one object"*. On #902: *"stack the two licences on
  narrower screens (Code: MIT. / Recipes and writing ... etc)"*.
  `.site-footer-license` has `$space-xxs` above it, less than the centre
  stack's own gap, and each `.site-footer-license-line` is a block at 600px
  and under.

## §3 The three-layer rule

No live ruling. The layering, its helpers and the traps met building it are in `MANUAL.md` §3.

## §4 Recipe front matter

- **2026-08-02 — body content below the front matter continues the recipe; it
  is not a blog post.** Helen's "least jar" of three options: its headings are
  peers of INGREDIENTS / METHOD / NOTES, at Method's reading width, written as
  the raw HTML the layout generates. MANUAL §4.1 has the markup.
- **2026-08-09, #75 — `incidental: true` hides a cooking fluid the cook will
  use as they like.** Helen: *"It's silly to write '2 tbsp olive oil' for a
  sear, when people will obviously use as much as they like. Whereas in a
  salad dressing, an amount is needed."* Her own pass deleted five generic
  frying-oil lines outright rather than hide them, and un-flagged the
  finishing butter in the plum sauce because it is worth buying. Who may set
  the flag: 2026-10-10, #1356.
- **2026-08-20 — staged drafts are read by the draft suite and are expected to
  be suite-clean.** Helen: *"your system is fine with to-rewrite, and I'll use
  it properly"*. Seven staged files had gone unscanned, the ones closest to
  publication. The folders are now `1-rewrite/`, `2-make/`, `3-keep/` and
  `4-promote/` (`PIPELINE.md`).
- **2026-08-21, #429 — `meta:` is exactly three flags in order, and promotion
  is never a step where "has it been cooked?" is open.** `cooked_before` and
  `date_last_edited` are retired; both were read by nothing. Helen's ruling: a
  recipe is cooked-and-liked (promoted), cooked-and-disliked (deleted) or not
  cooked, *"why would I put it on my battle tested site?"* And *"I never want
  to publish anything I haven't tested."* No test enforces it on food: it is
  hers to decide at promotion. The made-and-liked state short of a rewrite is
  now the drafts folder `3-keep/`, not a flag.
- **2026-08-29 — the ingest contract is one question: is the answer in the
  source document, or in Helen's head?** In the source, the ingest does it; in
  her head, it is a `QQ`. Measured that day, 266 of 342 drafts carried a gap
  whose answer was printed on the page (sugar type, egg size, butter, the fan
  figure). The fan temperature shows the timing: trivial at ingest, hard to
  get later.
- **2026-08-29 — ingredient and method groups are split at ingest, once, and
  not again afterwards.** Helen: *"Claude is requested to split out ingredient
  and method groups at ingest to help me, then not again after that"*. She had
  been typing `CLAUDE THIS IS A METHOD GROUP` into drafts by hand;
  `test_no_claude_markers_left` catches that workaround. The one later pass
  was the retro-fit she ruled on 2026-09-07 (#814).
- **2026-09-01 — Helen keeps the rewrite staging folder, and no agent deletes
  a `QQ original` line or moves a file between staging folders unasked.**
  Helen, against a session's reading that the folder was redundant: *"I'm
  likely to want to cast my eyes over what you've rewritten for me even though
  I predict it will be pretty good. At the point of being about to cook I'll
  also delete any original lines that have been totally superseded by yours,
  leaving me less to pick through in the kitchen."* The folders are how she
  tracks HER work; the folder is `1-rewrite/` today.
- **2026-09-03 — a recipe's filename is the whole title slugged, not the head
  clause.** Helen: *"Slug the whole title"*, so two "with" dishes sharing a
  head clause do not collide. Existing files keep their names.
- **2026-10-18 — every note an ingest adds is `{label, text}` with both
  fields set and both beginning `QQ`; the label may carry a topic, `QQ
  nutrition`.** Helen, 2026-09-04: *"It's annoying for me to remember how to
  type YAML every time."* On 2026-10-18 she chose to allow the topic over
  renaming 22 envelopes' labels to bare `QQ`: the label still reads
  unfinished, and when she proofreads she deletes `QQ ` and keeps the
  heading. `ingest_inbox.py` demands `QQ` or `QQ <topic>`.
- **2026-10-18 — a time the source does not print is written `Estimated N
  mins`, and promotion refuses it.** Helen: *"I would like "Estimated 10
  mins" to be written, then our tidying scripts block promotion for recipes
  with estimated times."* She chose it over keeping the guess behind a `QQ`.
  `test_no_estimated_time_reaches_promotion` fails on one in `4-promote/`.
- **2026-10-18 — an ingest ignores a nutrition box and its badges.** Helen:
  *"Drop them and add clear instructions for ingestion to ignore these."*
- **2026-10-18 — an ingest ignores a "you will need" equipment list.** Helen:
  *"the rule is "trust the cook"."* As a group it had put a cake ring on the
  shopping list.
- **2026-10-18 — page furniture: drop what sells, keep what is written about
  the dish.** Helen: *"Drop ads, keep essays."* Shows, ticket lines, book plugs,
  TV listings, "next month", web pointers and wine boxes go; essays, bios and
  boxed asides go in the body.
- **2026-10-18 — a sidebar box ingested as a recipe has no body.** Helen chose
  *"Delete the bodies"*: the body repeated the `QQ original` lines unmarked,
  and would have published the book's text.
- **2026-09-05 — a `QQ Claude` rewrite follows four patterns taken from
  Helen's own rewrite of one.** From `sticky-squidge-ginger-loaf.md`, which
  she rewrote as a comparison: do not re-narrate what the ingredient list
  already says; draw step boundaries at physical stages, one step per thing
  you would pause at; state the expected result plainly instead of hedging
  with a check; cut flourish, keep function. `.claude/commands/ingest.md`
  carries them.
- **2026-09-07, #814 — a grouping an ingest left out is derived from the
  draft and reviewed by Helen: no `proposals:` block, no calibration round, no
  re-reading of sources.** Helen, to the objection that a derivation could
  never be faithful to the print: *"Most recipes don't have them as printed,
  honestly... It doesn't matter though, I can catch easily at review if
  something is in the wrong place or if names need amending."* Ran 2026-10-04
  (food-private PR #43). Method groups must be runs of the original steps, so
  a draft where one component is made part-way through another stays flat.
- **2026-10-01 — a note is always `{label, text}`; the bare-string form is
  retired on both sites.** Helen: *"I really would like placeholders for
  labels and text on notes, for both food and cocktails."* A published note
  must have both filled; a draft note needs both keys and may be empty. A
  session's part, not hers: the layouts decide by KEYS, not values, count the
  notes that will render before printing the heading, and print nothing for an
  empty pair. (Replaces "or a bare string", 2026-08-03.)
- **2026-10-02, #1258 — every draft has a notes slot, and imported note text
  is labelled `QQ`.** Helen: *"Yes please, mark empty labels with QQ, because
  this will stop them being published by accident (i.e. without me having
  spotted and fixed the imported text). Then yes, thank god, yes yes yes
  please fix the notes: [] !!!!"* A draft never says `notes: []`, it carries
  the empty pair, because *"leave me with a notes placeholder I don't have to
  retype"*; a published food page with no notes still writes `notes: []`. `QQ`
  on a label means "Helen has not read this" whatever the text says, and text
  beginning `QQ` must be labelled `QQ`. `tidy_drafts.py --only notes`.
- **2026-10-12 — a published drink may keep the draft's empty notes pair.**
  Helen: *"Let's change that test to only allow label "" and text "", given we
  set drafts to write that out of convenience for me."* Both halves empty is
  allowed and prints nothing; one half empty is still refused. A drink is
  promoted byte-for-byte, slot and all.
- **2026-10-04, #814 — an ingredient-group name opening with "to " prints as
  itself, with no "For the".** Helen: *"Can we fix all 'for the to finish'
  cases? Both existing and when we ingest."* The layout had special-cased `to
  serve` alone. Method groups print their name bare and never had the fault.
  A noun still takes "For the", so an ingredient block headed "assemble" is
  written `to assemble`.
- **2026-10-04, #814 — the closing METHOD group is `assemble`, the verb, never
  `assembly`.** Helen: *"We use "assemble" for some published food recipes I
  believe. Let's stick with that."* An INGREDIENT group called `assembly` is
  left alone: that side names components. Where the closing step only serves
  it is `to serve` (*'"to serve" please'*, over `Serve`); where it bakes,
  *'"layer and bake" is nice where relevant. "assemble and bake" too.'*
- **2026-10-04, #814 — an ingredient used in two phases is split only where
  the method states the amount for one of them.** Helen, of a cheesecake's
  275 g of sugar: *"25g under sauce, rest where it's used."* Where no amount
  is stated she offered "the juice of 1 lemon" / "the zest of one lemon"; that
  wording was measured against the shopping list and not used (two rows,
  neither summed nor scaled). The shape applied is a session's: both halves
  open with the same words, ONE keeps `amount`, the other has no `amount` key
  and says which part it is (`"lemon, the zest of the one juiced for the
  pears"`).
- **2026-10-04, #814 — interleaved phases take narrative group names, and
  Claude suggests them.** Helen: *"We use narrative phase names already, good
  spot, so yes please suggest some. It'll be easier for me to edit than
  generate."* A component-named group cannot hold steps that leave a component
  and return to it; "Brown the beef", "Build the stew", "Finish and bake" can.
- **2026-10-04, #814 — method group names are imperatives, as a trial.**
  Helen, shown `cake`, `lemon curd`, `assemble` on one draft: *'Can we try
  "Make the cake", "Make the lemon curd", and "Assemble" here? Imperatives are
  nice, and I like verbs.'* Applied to the 21 drafts where the mixed register
  showed, not to every draft.
- **2026-10-04, #814 — a component with ingredients and no method gets a
  `QQ - MISSING:` step, not silence.** Helen: *'Leave a QQ in there for me please
  under e.g. "Make the treacle topping"'*.
- **2026-10-04, #814 — group names are quoted.** Helen, told the difference
  between `- name: cake` and `- name: "Make the batter"` was only how the name
  is typed: *"Let's make future recipes quote group titles, so add that to the
  tidy pass instructions, and ingestion instructions."*
  `fix_group_name_quoting` in `tidy_drafts.py` (`--only quoting`).
- **2026-10-07 — a source's bottle goes in that pour's note as "Originally
  X.", never in `suggestion`.** Helen, when a Difford's batch arrived naming
  148 bottles her dictionary does not know: *"Move all the suggestions to
  notes, and I can add my own suggestions where I have them or drop if not.
  For notes, just write 'Originally X'."* It holds even when she tells a chat
  to use the source's bottles.
- **2026-10-08 — a cocktail's tagline is a bare `QQ` at ingest; nothing is
  drafted.** Helen: *"Let's stop Claude drafting taglines. It turns out me
  doing them in batches works the best."* 73 had arrived as `QQ Claude <a
  line>`.
- **2026-10-08 — a food tagline at ingest is the method's pair on one line,
  where the source has an intro.** Helen: *"QQ original yes, then QQ claude
  rewrite, then I'll do my own and delete the other two."* A rewrite of the
  intro, not a quip; an ingest never drafts a tagline of its own.
- **2026-10-08 — unspecified butter is `QQ butter`.** Helen: *"Write QQ butter
  in the ingredients list where it isn't specified."* Replaces a chat's
  "salted, or plain in precise bakes".
- **2026-10-08 — a `QQ Claude` line gives the fan figure alone.** One of the
  rulings from two claude.ai chats that Helen confirmed as standing, each a
  yes. Its `QQ original` keeps everything the source printed.
- **2026-10-28 — a `makes:` line the yield reader can count needs no
  `serves_estimate`.** Helen: *"Make the test suite support our current
  design. 16 slices, 2 X-in cakes, 9 biscuits."* The recipe page counts the
  thing made and the shopping list counts batches (§8.2), so the estimate is
  needed only where `serves:` has no number or `makes:` names nothing the
  reader can count. Write `makes:` as a count of a named thing.
- **2026-10-08 — Helen's own recipes are `source: "Henry"`, `source_type:
  person`.** Confirmed as standing the same day, as the old journal recorded
  it.
- **2026-10-08 — four ingest rulings apply to Difford's alone.** Saline is a
  small pinch of salt (she does not keep saline); "rich" syrup is `cane sugar
  syrup 2:1`; the glass is the "Select and pre-chill" line; "freshly squeezed"
  and its kin are dropped. Confirmed as standing; `INGEST_ONE_COCKTAIL.md`
  has the table.
- **2026-10-08 — three things a chat did are NOT ingest rules: one question
  per recipe, hand-assigned moods, and alternative paths as method groups.**
  Helen, on the first: *"I don't know how it got in there"*; on moods: *"we
  don't add moods at first ingest -- just leave me a QQ"*. Alternative paths
  wait until she has read the two pages that have them.
- **2026-10-08 — the issue route for ingests stays, beside the bulk route of
  envelope files.** Helen: *"let's retain the feature"*. She had given two
  chats the documents by GitHub URL and dropped the envelopes into
  `tmp/inbox/` for `ingest_inbox.py --from-file`. What does not happen is a
  session filing a batch of issues: the first chat wrote a prompt asking for
  39.
- **2026-10-28 — one `QQ original` per source step, and as many `QQ Claude`
  lines under it as a dense step needs.** Helen: *"I would like Claude to
  split out method lines where the written method is unhelpfully dense, so
  multiple QQ CLAUDE lines will be very helpful."* The original stays whole and
  verbatim; the rewrite splits at the points a cook would pause. Two source
  steps are still never merged and nothing is reordered. (Replaces 2026-10-10's
  one-pair rule, the fourth answer to this question: do not propose another.)
- **2026-10-10, #1356 — the ingredient list is the source's own list; nothing
  joins it from the method.** Helen: *"We shouldn't list incidentals. We can
  trust the cook."* The one exception is a source with no ingredient list at
  all. (Replaces 2026-10-08's "an ingredient the method names with a quantity
  joins the list".)
- **2026-10-10, #1356 — a fat or flour the source lists only for the tin or
  the pan is kept and flagged `incidental: true`, at every ingest.** Put to
  Helen as one reading of #1356: *"Yes, your interpretation of #1356 is
  correct."* Asked on 2026-10-11 whether that was one pass only: *"They are
  always incidental. Please can every ingest note this in the ingredients list
  where it applies."*
  Flagged, not deleted, so the exclusion filter still sees the butter. The
  line is drawn at fats and flour: icing sugar to dust and mustard to brush
  stay ordinary lines, and an amounted "plus extra for the tin" line is not
  flagged, because that hides the real amount. Every other use of the flag
  stays hers.
- **2026-10-16, #1356 — on a real fat or flour line, ", plus extra for the
  tin" and its kin are trimmed, at tidy.** Put to Helen with the 42 draft
  lines that carry one; she chose "Trim it at tidy" over leaving the note. The
  same "we can trust the cook". A `QQ` line keeps its tail for her rewrite.
- **2026-10-16, #1356 — deep-frying oil is listed, unquantified, as "<oil>,
  for deep frying", and is not incidental.** Helen: *"Deep-frying oil should
  appear in the ingredients list, but unquantified, just saying 'for deep
  frying', because I will use different pans with different volumes."*
  Held by `test_deep_frying_oil_is_listed_without_an_amount`; `/tidy-drafts`
  drops the amount and rewords the line.
- **2026-08-20, #406 — "Adapted from" prefixes published work and only
  published work.** Helen: *"Bare labels don't need 'adapted from', only work
  published by other people."* And why the prefix is always true for the rest:
  *"When `rewritten == true`, we can always say 'adapted from' truthfully, so
  that should always be there."* `publication`, `book`, `website` and `author`
  take it; `person`, `place`, `joke` and `unknown` must not.
  `tests/test_source_attribution.py` enforces it both ways, on drafts too.
- **2026-08-20, #406 — a source with no date is a `website`; a `publication`
  is a print issue and always carries one.** Helen: *"Online magazines don't
  have a publication schedule like print ones do."* Good Food is both a
  magazine and a site, so the date is the only thing that tells them apart: 64
  drafts were retyped on it. A month and year or a bare year counts.
  `magazine` is not a `source_type`; it is `publication`.
- **2026-08-20, #406 — a source nobody has established is `source: "QQ"` with
  `source_type: unknown`, and on a published recipe it is meant to break the
  build.** Helen: *"QQ should be allowed, but will break a test and block
  build, which is fine."* Not `Unknown` and not blank: the first reads as a
  finished answer and the second as nothing to see. Each of the pair requires
  the other. Do not guess a citation to get past it.
- **2026-08-21, #406 — a `book` source names its author, as `<title>,
  <author>` or `<Author>'s <title>`; there is no authorless form and no
  exception list.** Helen: *"I can't imagine knowing the name of a book but
  not its author."* `Adapted from Wagamama Feed Your Soul` had passed on two
  published pages. The one book that seemed to have no author was not a book:
  *"it's from Good Food, from a special one-off section"*, so it is a dateless
  `website`. If a book seems authorless, check it is a book, then ask her.
- **2026-09-11, #406 — `source: "unknown"` is the closed answer, and only
  Helen closes it.** Helen, with the apple coleslaw ready to publish and its
  source still `QQ`: *"Please write 'unknown' for the source on coleslaw."*
  `source_type: unknown` takes exactly `QQ` while the question is open and
  exactly `unknown` once she has ruled nobody will know. Lowercase, no
  "Adapted from", and the only unknown-typed value that may reach
  `_food_recipes/`.
- **2026-08-20, #406 — a citation names its source and never its publisher.**
  Helen's ruling in the source-attribution pass; no words of hers were
  recorded. A trailing bracketed publisher comes off the `source:` line: it
  took "(Hodder & Stoughton)" off the beef wellington, the only one in the
  corpus. `SOURCE_ATTRIBUTION_SPEC.md` holds it as "No publishers", and
  `tests/test_source_attribution.py` refuses one on recipes and drafts alike.
  A bracket that is part of the real title is the one way through, and the
  failure message says how to declare it.
- **Undated, #69, #68 — ingredient groups are ordered by title relevance: the
  group named for the dish leads; within a group, ingredients follow call
  order.** Helen's ruling; no words of hers were recorded. A dressing,
  marinade or glaze the title does not call out never sits above the group
  the dish is named for. `test_ingredient_group_order_matches_title` holds the
  group order, conservatively: it compares only a non-matching group listed
  before a matching one. Call order within a group (#68) is the rule too, but
  it is not reliably automatable and has no test, so a green suite says
  nothing about it.

### §4.0 The gate flags

- **2026-08-18 — the gate flag is `awaiting_fix`, with an underscore, and the
  gate fails CLOSED.** Failing closed is Helen's call: the first version hid a
  page only on an explicit `true`, so a missing key and `"true"` in quotes
  both published. Liquid parses `awaiting-fix` as subtraction and would
  publish a flagged page, so the hyphenated form is never written.
- **2026-08-18 — a held-back page is REMOVED from its collection, not hidden
  from the index.** `_plugins/publish_gate.rb` drops the document at
  `:post_read`. #276 is the precedent: two pages linked from nowhere were
  published anyway; unlinked is not unpublished. There is no `published:`
  field, because it would duplicate `awaiting_fix` and two fields that must
  agree end up disagreeing in the direction that publishes.
  `show_awaiting_fix` is `true` only in `_config_local.yml`. Not recorded as
  Helen's words.
- **2026-08-18, #331, #367 — every agent edit to a recipe sets `proofread:
  false` in the same commit, whatever its size.** Twelve proofread recipes had
  been edited in one commit, every edit defensible, none flagged, nothing
  looking. The flag records whether Helen has read what is now in the file,
  not how big the change was. `test_agent_edited_recipes_are_not_marked_proofread`
  reads git history. Stage explicitly: `git add -A` swept one of her own
  uncommitted fixes into an agent commit and tripped the rule.
- **2026-08-18 — `BASELINE_COMMIT` moves only when Helen has reviewed the
  change herself, and never to turn a red test green.** It moved four times by
  2026-08-20, each on her own review: three sweeping and content-free, the
  fourth a nine-recipe backlog walked through one file at a time. A move goes
  in a commit of its own, quotes her grant, and is proved by running the test
  with the old value and watching it name the files. Her review may be of the
  diff rather than of the built pages, and may be agreed before the edit: for
  twelve method lines (2026-09-10, #705) she chose *"Line by line. I can just
  grind it out."* over re-reading twelve pages. Measure first how many recipes
  the rule is holding: a move asserts she has read every one of them.
  `COCKTAIL_BASELINE_COMMIT` is the same rule.
- **2026-08-21, #417 — a commit that changes only keys nothing renders needs
  no flip (`INVISIBLE_KEYS`).** Helen asked for it, 2026-08-20, #406: *"Adding
  source_type to every recipe doesn't change how they render, so no need to
  flip the proofread flag. Does this sound reasonable? Can we allow for this
  formally so we don't keep asking the same question?"* The mechanism is a
  session's: `source_type` and the retired meta keys, with the body
  byte-identical (`meta.rewritten` is not one: the drinks gate reads it);
  `test_invisible_keys_are_really_invisible` scans the render surface, which
  excludes pages. That list is the whole exemption. "It renders identically"
  is not a wider rule of hers (2026-10-13: *"I never asked for Claude to say
  it"*): a change outside those keys takes the flip or her grant. Declined (#428): renaming
  `rewritten` to `human_rewritten`, because `food/index.html` reads it and a
  rename would invalidate proofreads.
- **2026-09-01 — `awaiting_fix: true` is a bookmark on a page Helen HAS
  proofread, not "unfinished".** Helen: *"'awaiting_fix' means I've proofread,
  but one small thing has been raised as a ticket, meaning that once that's
  fixed I can look for just that one thing rather than having to read the
  entire file again carefully."* So the flag is not permission for further
  edits, and `true` and absent are different states.
- **2026-09-02, #667 — `proofread: false` holds a page back on both sites: a
  recipe publishes only on `awaiting_fix: false` AND `proofread: true`.**
  Helen: *"this is the very last touch that I, the human, make to the file."*
  The two flags are different facts, so requiring both is not the "two fields
  that must agree" objection, which is about `published:`. Five food recipes
  left the live site until she read them: the point, not a side-effect. A
  cocktail must also say `rewritten: true` (#1137, §9.1.1).
- **2026-09-03 — a magic-bag dish carries `awaiting_fix` and `proofread`, and
  no `rewritten`.** It must be able to publish, so `proofread` is required,
  `false` on a new entry and hers to flip; there is no source to rewrite from.
- **2026-09-06, #662 — only Helen's own read of the rendered page sets
  `proofread: true`; an agent pre-read was offered and declined.** Five
  recipes went dark when the gate tightened, and she chose to read the five
  pages and set the flags herself, because a pre-read is not a proofread.
- **2026-09-14, #1008 — after an agent touches a published file, what happens
  next comes in three sizes, and the choice is Helen's.** Helen: *"If Claude
  touches a published file, if it's only something like a single word or
  number then ask me and I will consider granting permission to make the
  change without flipping the flag. If not, then leave on public site but
  unpublished. If something big is wrong, delete from public repo and re-add
  to private."* The flag rule itself is unchanged. `PIPELINE.md` §5 is the
  procedure; it gained a row for a derived value across a batch on 2026-09-20
  (#1127).
- **2026-09-14, #1008 — a flip to `proofread: false` on a published file
  raises an issue labelled `blocked-on-helen`.** Helen: *"when Claude touches
  a published file in a way that flips proofread to false, raise a github
  issue labelled blocked on Helen so I know I need to do something"*. Refined
  2026-09-20, after one-per-file helped get the agent account flagged as spam:
  *"We need to put that rule back in place, but add the list of dark recipes
  to one issue per batch rather than one issue per file."*
  `scripts/needs_helen.py` does the flip and the body, and names the pages
  that link to each demoted one, because the gate removes the page and leaves
  the links.
- **2026-09-14 — an agent asked to promote a food draft copies it and never
  sets `rewritten` or `proofread`.** Helen: *"Please promote meringue swans
  from food drafts to published."* Promotion into the collection and the gate
  opening are two different moments: the recipe sits in `_food_recipes/`, off
  the live site, until she reads the built page and flips the flag herself.
  Mechanical suite failures on the copy are fixed and said afterwards.
- **2026-10-21 — a tag or star change Helen has agreed with a session row by
  row needs no flip.** Helen: *"No need to flip the proofread flag for tag
  changes agreed interactively -- new official ruling."* Her row-by-row answer
  is the review. The mechanism is the existing one: the tag commit leaves
  `proofread` alone and `BASELINE_COMMIT` moves to it in the next commit,
  quoting her rows and proved with the old value. A tag change she has not
  answered for, or any change to another key in the same commit, still flips.
- **2026-09-20 — there is no per-recipe exemption list: `HELEN_CLEARED` is
  deleted and is not rebuilt in that shape.** Helen: *"I don't want a
  permanent exemption list. If I change one of those files again, the flag
  will need to go back to false until I proofread it again."* It matched on
  filename, so an entry never expired and covered every later agent edit. The
  escapes that remain are `BASELINE_COMMIT` and `INVISIBLE_KEYS`. If one
  recipe must be cleared while others are held, build an entry that clears ONE
  COMMIT. (Taken from MANUAL §4.0; the old journal had no entry.)
- **2026-10-08, #1089 — if Helen reads the rendered pages on the branch and
  says so, the flags go back in a second commit and the baseline moves in a
  third.** Helen: *"#1341 is proofread! Let's go."* Fourteen recipes had gone
  to `proofread: false` with copy edits and the production build then failed
  five tests, so an agent's copy fix to a published recipe cannot merge by
  itself; it waits for her grant. Nothing left the live site. The plum sauce
  stayed `false`: it was unproofread on `main` before the branch.
- **2026-10-10 — a grant to edit live files without the flip is Helen's, is
  given per batch, and covers only what she named.** For the 17 tag changes
  from the published review: *"edit the live files without flipping the flag
  please -- this is under the 'life is too short' test"*. For the `main` tag,
  2026-10-11: *"when we're in agreement about the main tag, you can edit the
  live recipes to add it without flipping the flag."* Each landed as a
  baseline move in a commit of its own. Neither is a standing permission for
  the next tag edit.
- **2026-08-20 — a no-flip grant covers exactly the change Helen named, and a
  conditional grant is proved before the flag moves.** Helen, of a link she
  had specified herself: *"I trust you to make that change without making
  others, so no need to flip the proofread flag again."* And 2026-09-27,
  #1217: *"if those are the only changes then flip the flag back to make them
  live again"*. The condition is checked by diffing each named file against
  `origin/main` first, and the result is said. A grant covers its commit and
  nothing after it; one she bounded *"in this session only, normal rules again
  after this"* (2026-09-21) ended with the session.
- **2026-09-09, #624 — a recipe Helen proofread in the private repo is
  promoted already `proofread: true`, as an unchanged copy, and the promotion
  needs a baseline move.** Helen: *"please move all proofread: true files into
  the public repo. If you do this then I don't have to fish through one by one
  to find out which I still need to proofread."* The test reads this repo's
  history only, so a promotion looks like an agent edit. The copy is
  byte-identical to what she read, or differs only in an `INVISIBLE_KEYS`
  key; a file that changed visibly stays behind at `false`. An agent
  still never sets the flag unasked (2026-09-14).
- **2026-09-10 — Helen may grant `proofread: true` ahead of her own read, and
  only she may; a red `main` is what has made her do it.** Helen, with deploys
  blocked: *"Break the rule, explicit permission, and get everything up on the
  site with proofread=true. Then hand on heart I'll look at them myself to
  confirm everything is fine."* Again 2026-09-16, offered a flip or a baseline
  move for two mechanical fixes: *"Fix and keep proofread true"*; and
  2026-09-26: *"I'll double check, but I'm happy to do that live."* Put the
  choice to her with the fact that forces it; never take it. It lands as a
  baseline move, so the next agent edit to the file trips the test again.

### §4.3 The magic bag

- **2026-08-26 — the magic bag is its own collection with its own schema and
  test file, and its pages carry no standing caveat.** It is Helen's name for
  her brain: the dishes she cooks from memory, answering *"what shall I cook,
  out of everything I already know how to make?"* for the half the site could
  not hold. A caveat rendered on every page for about an hour and she had it
  removed on sight: *"I am the user, and I know exactly what is going on."*
  The separate test file keeps the recipe guards unconditional.
- **2026-10-04, #1201, #507 — the magic bag is filled, not retired, and it
  gets a quiet mark, not a filter.** Helen: *"I don't need to filter by this.
  Let's just give it a quiet mark, where "draft" is on the live site, and next
  to it on the local site."* One rule styles `.badge-draft` and
  `.badge-magic-bag`, so neither is louder. Still open: #508 (the word and the
  permalink), #509 (the README, in her voice), and the dishes themselves.
- **2026-10-04, #1201 — a magic-bag dish can be a draft, and `magic bag`
  always sits on the right.** Helen, on a first build that said no row could
  carry both marks: *"a recipe can have magic bag AND draft. Always sit magic
  bag on the right."* `draft` on such a row is decided the publish gate's way
  round, so it fails closed: every new dish starts marked `draft` locally and
  loses the mark when she proofreads it. A held-back recipe in
  `_food_recipes/` is still not marked; her ruling was about the magic bag.
- **2026-10-04, #1201 — the magic-bag schema is tested through a committed
  fixture entry, not by asserting the collection is non-empty.** A session's
  call, not Helen's ruling. The collection had been empty for four weeks and
  every per-entry test collected nothing and read green. The issue's own fix
  was declined: the dishes come from her head, and a non-empty assertion would
  hold `main` red, and so every deploy, until she wrote one.
- **2026-08-26 — a magic-bag entry always has a `tagline:` line, and its value
  may be empty.** Helen: *"Optional. Always add the line to file front matter
  so I don't have to remember to add it."* The tagline is optional; the KEY is
  not. `tagline: ""` renders nothing and is always a string, never null.
  `test_tagline_key_is_present_even_when_empty` in `tests/test_magic_bag.py`.
- **Undated — a magic-bag entry's minimum is an ingredients list.** Helen:
  *"as a minimum I should dash off ingredients lists."* So `ingredients` is in
  `REQUIRED` and must be a non-empty list, though it may be incomplete: the
  entry is a dish she cooks from memory, and the list is what makes it
  findable and shoppable. No method is demanded.
  `test_ingredients_is_a_non_empty_list`.

## §5 House style

- **2026-08-21, #413 — en dashes are scoped by what a reader SEES.** Helen, on
  `cook_time: "20-25 mins"`: *"These still render to the user, so correct to
  en dash please."* So house style reaches front matter that renders, the
  prose pages and the reference data, not only recipe prose.
- **2026-10-18 — on food, the formatter reaches a `QQ` line; it still never
  rewords one.** Helen, asked whether the accents test or the skip should give
  way over a printed "ragu": *"Perform mechanical formatting on QQ lines so
  when I come to rewrite or edit I already have the correct formatting
  availabe to me."* Dashes, typography, unit spaces and accents only; a drink's
  `QQ` lines stay as written. (Replaces #426, 2026-08-21: *"ideally just skip
  the whole line for simple normalisation tasks"*.) A `QQ Claude` line is
  ours and always tidied.
- **2026-09-07, #800 — a tip printed under a source's own rubric is
  transcribed without the label; `gf tip:` is Good Food, the magazine, not
  gluten-free.** Helen, asked what it meant: *"I actually have no idea what
  this means... Good Food tip, the magazine source I use a lot?"* She was
  right: six of the eight drafts cite Good Food and none of the tips is about
  gluten. Expanding it to "Gluten-free tip:" would have printed a false
  allergen claim. Each note becomes a plain sentence; `source:` already
  carries the attribution.
- **2026-10-08, #1089 — cocktail titles are Title Case, and a qualifier in
  brackets is not.** Helen: *"Title case for all titles. Qualifiers in
  brackets don't get capital letters, unless they're a proper noun, e.g.
  'Margarita (classic)' and 'Fog Cutter (Bramble style)'"*. Small words stay
  small ("and", "the"). Drafts too: *"Add title case to cocktail drafts too
  please, why not. Add that to our draft-tidying script."*
  `test_drink_titles_are_title_case`; `tidy_drafts.py --only titles` only ever
  RAISES a letter, because a script cannot decide what a proper noun is.
- **2026-10-08, #1089 — `snippet:` is an optional second tagline for the meta
  description and link preview.** A drink's tagline is also its search-result
  text, and the Negroni's is fine on its page and not there. Asked to decide,
  Helen wrote a second line rather than soften the first, and left the
  Planteray one alone (*"can stay"*). Read only by `_layouts/default.html`; a
  page without it uses its tagline. Nobody ingests a snippet.
- **2026-10-08, #1089 — copy Helen settled at the design review's sitting
  stays as she left it.** The five-spice duck legs' tagline is a joke
  (*"tagline was supposed to be a joke"*); the caramel and ganache yield notes
  are labelled "Examples of how much this makes"; the rum page's last heading
  is "A final thought: rum characters"; the Cobra's Fang note keeps its
  "Pool?" label (*"I consider the point settled"*); the Sazerac note no longer
  mentions the distillery (*"I deleted the controversial part!"*); the
  "Some"/"some" serves lines are kept by her word.
- **2026-10-01 — a number and its unit take a space (`15 ml`, `400 g`), fixed
  mechanically at ingest and by the tidy pass.** Helen: *"Please add unit
  spaces (15ml -> 15 ml) as a mechanical fix to perform at ingest, and check
  when I ask you to check drafts."* Measured that day: `amount:` read `40 g`
  1,461 times across the food collections and `40g` 13 times. A temperature
  takes none. Imperial units take one too: *"All units need them, including
  imperial."* `scripts/tidy_drafts.py` does it for drafts and
  `INGEST_ONE_RECIPE.md` carries the rule.
- **2026-09-06, #711 — every note starts with a capital letter and ends with
  a full stop, on both sites.** Helen: *"notes should always start with a
  capital letter and end with a full stop"*, and *"I'd prefer you add tests
  for this then fix them for me!!!! Or flag if my copy is too garbled to
  fix."* It covers each `notes:` entry on a recipe or a drink and a drink
  ingredient's `note:`, as method-step notes already were. A `QQ` note is a
  placeholder and is skipped; a digit or a quoted term may open a note, and
  `!` or `?` may close one. An exception is declared with its reason in
  `NOTE_EXCEPTIONS` (`tests/test_style.py`) or `DRINK_NOTE_EXCEPTIONS`. A food
  ingredient's `note:` is the opposite: a lowercase fragment.
- **Undated — "180°C fan" is correct and is not a conversion; what is banned
  is a second, conventional-oven temperature beside it, and gas marks
  always.** Helen: *"saying 'fan' isn't a conversion."* The site is fan-oven
  only, one temperature: never "180°C fan (160°C conventional)" in any form. A
  conventional figure left in place is 20 degrees too hot in her kitchen.
  `test_no_oven_conversions` in `tests/test_taxonomy.py`.
- **2026-10-13, #146 — "never add fan in bulk" is withdrawn.** It was a rule
  from before ingest supplied the fan figure: a bare oven temperature might
  have been the source's conventional number, so each was confirmed by hand.
  Asked whether that is still her wish, Helen: *"No"*. Every oven temperature
  says "fan" (`test_oven_temperature_says_fan`), and a bare one is fixed like
  any other house-style fault, with `proofread: false` on a recipe.
- **2026-10-18 — *Riverford Companions* prints a conventional oven figure;
  the fan figure is 20 lower.** Asked whether "190°C/Gas 5" there is
  conventional, Helen: *"Conventional: fan is 20 less".* A `QQ Claude` line
  says "170°C fan"; the `QQ original` keeps the printed figure.
- **2026-10-19 — Good Food prints both units; keep the metric, bakes
  included.** Asked whether its "100g/4oz" should keep only the grams, Helen
  chose *"Metric only, bakes too"*, over the general rule that baking keeps
  its ounces. Per-source rulings like this and Riverford's live in
  `_data/food/sources.yml`, which `INGEST_ONE_RECIPE.md` §5 prints.
- **2026-10-19 — an unlabelled oven pair 20 degrees apart is conventional and
  fan.** Helen: *"Oven pairings when one temp is 20 degrees lower than the
  other mean conventional / fan, I'm just so sure. Interpret that way
  please."* So "180C/160C/gas 4" is "160°C fan" on a `QQ Claude` line. Any
  other gap is still a question.
- **2026-10-19 — a title keeps its accents, and gains any the house list
  declares.** Helen: *"Accents in titles should be preserved, or added if
  missing."* "Rich ragu" is titled "Rich Ragù".
- **2026-08-10 — within one ingredient group the base spices run coriander,
  cumin, turmeric, fennel, and the warm spices follow in any order.** Helen's
  own cooking convention, confirmed that day and prompted by
  `indian-mutton-raan-roast.md`; no words of hers were recorded. The warm
  spices are cinnamon, cloves, nutmeg, cardamom, star anise, ajwain and mace,
  always after the base ones. A recipe for a named spice blend is exempt: its
  order is the blend's own (`_SPICE_BLEND_RECIPES`).
  `test_spice_order_within_group`.
- **2026-08-10, #74 — butter is always "salted butter" or "unsalted butter",
  and sugar and flour each have a closed list of allowed names.** Helen's
  ruling; no words of hers were recorded. The lists are closed, not merely "is
  not bare": "caster sugar" and "muscovado sugar" are qualified and still
  wrong, because the cook is left guessing golden or white, soft or
  muscovado. `_QUALIFIED_BUTTER`, `_QUALIFIED_SUGAR` and `_QUALIFIED_FLOUR` in
  `tests/test_style.py`; a new name joins a list on her say. At ingest an
  unspecified butter is `QQ butter` (§4). Butter that is only for greasing is
  exempt (Helen, 2026-10-13); "plus extra for greasing" is not, because that
  line is also in the dish.
- **Undated, #136 — ginger says fresh, ground or paste, in the ingredient list
  as well as in `main_ingredients`.** Helen's call; no words of hers were
  recorded. A prep word alone does not say which kind was used: "grated
  ginger" fails and "grated fresh ginger" passes.
  `test_ginger_specifies_fresh_ground_or_paste`.
- **Undated — cardamom is always green or black, and always pods, powder or
  seeds.** Helen's rule; no words of hers were recorded. Both halves are
  required: "cardamom pods" and "green cardamom" each fail. The singular forms
  pass, since a recipe can call for one pod. `_QUALIFIED_CARDAMOM` and
  `test_cardamom_specifies_type` in `tests/test_style.py`.
- **2026-08-12, #167 — milk names its type from the source, and "milk (any
  kind)" is a real answer for a recipe that does not care.** Helen's explicit
  call; no words of hers were recorded. A bare "milk" is never bulk-converted
  to "whole milk": which milk a recipe used is confirmed from its source, so
  `test_milk_specifies_type` is a checklist of what is still to confirm. "(any
  kind)" is recognised only as a trailing parenthetical on the ingredient
  line, and it then excuses a bare `milk` in `main_ingredients`.
- **Undated, #139 — dark-family chocolate carries its cacao percentage on the
  ingredient list and never in `main_ingredients`.** Helen's ruling; no words
  of hers were recorded. Dark is 70%, very dark 90%, unsweetened 100%, so the
  cook knows what to buy; `main_ingredients` names the type only, because it
  is the index's pill. Milk and white chocolate never take a percentage. Chips
  and shavings need a type word and no percentage. `_CHOCOLATE_PERCENT` and
  the three chocolate tests in `tests/test_style.py`.

## §6 `main_ingredients`

- **2026-08-29 — `main_ingredients` has no cap; the old eight had been read as
  a budget.** Helen: *"we have generally shifted to allowing more main
  ingredients where they define a dish, for example the long list of spices in
  gulai ayam... I do often find myself adding to that array by hand, which is
  plainly silly."* Her own lists run to fourteen. An ingest is generous.
- **2026-09-06, #762 — where two spellings of one ingredient exist the
  majority wins, and it is fixed in the data: `cornflour`, `beansprouts`.** An
  alias was not an option: it rewrites the picker's vocabulary but never
  `data-ingredients`, so the collapsed chip would match half the recipes it
  names.
- **2026-09-22 — `derive_main_ingredients.py` reorders a list and never
  changes its members, and never writes to `_food_recipes/`.** Helen asked for
  the field to be generated (*"I've already felt a bit funny about
  main_ingredients"*), ordered *"sort of in order of stars, how much of a game
  over it would be not to have it, proportion, and sensible larder order."*
  But every draft already had a list and hers read better than a derivation
  (0.55 agreement at best), so it derives only where there is none. The
  pantry ranks an item lower; it never excludes. Reordering, not deriving, is
  a session's call.
- **2026-09-22 — `main_ingredients` drops a size word and keeps a kind; egg
  size lives in the ingredient list.** Helen: *"'large carrot' should appear
  in ingredients lists where that's what I've stated, but main_ingredients
  should just have 'carrot'."* `whole milk`, `whole cloves`, `king prawns` and
  `baby gem` are KINDS and stay. This field is the browse axis and the
  ingredient list is the shop-and-cook one; sizes here would give the index
  three buttons for one ingredient.
- **2026-10-21 — a bake lists its flour, butter, eggs and sugar, and a
  savoury dish lists the herbs, citrus, cream or wine it tastes of.** The
  completeness test for bakes was put to Helen against leaving staples out so
  a search for "eggs" is not buried in cakes: *"If you search for eggs wanting
  e.g. turkish eggs and see loads of cake, you then hit the filters for
  breakfast and main or whatever, right??? I think everything goes in main.
  Cakes look super odd in index page rows without those kinds of
  ingredients."* On herbs: *"I know herbs shouldn't be a showstopper but I
  also think people skip the herbs and are confused about why their food
  doesn't taste of anything."*
- **2026-10-22 — a draft's `main_ingredients` says `butter`, and a `QQ
  butter` line still earns it; a published recipe's says `salted butter` or
  `unsalted butter`.** Helen: *"Published recipes need salted or unsalted
  butter for their main ingredients, but drafts don't. But drafts still need
  the butter in their main ingredients so I can discover and cook from
  them."* The kind is settled at promotion, with the rest of the proofread.

## §7 Taxonomy (food)

- **2026-08-01 — "declared" and "filterable" are the same thing: a tag shown
  on the page with no filter button was proposed and rejected.** No user
  stands in the gap between a fact you read (a note says more than a badge)
  and a fact you browse by (it needs the filter).
- **2026-08-02 — `one-pot` and `scalable` are retired, `freezable` is kept,
  and `breakfast`, `extras`, `festive` and `starter` are practicalities, not
  moods.** Helen's calls. The first two are guessable from the recipe, and
  one-pot would honestly cover 57%; the four are dictated by an external
  structure, not a craving; `freezable` is the one genuinely unguessable tag.
  `virtuous` was added, narrow. Co-tags: `ice cream → dessert, make-ahead`
  (and, from 2026-10-21, `herbivore-ish → main`).
- **2026-08-09 — `something unusual` is retired.** Culturally relative, not a
  real craving, and barely used. `retired_star_ingredients` makes a retired
  value fail with its reason.
- **2026-10-21 — `legumes` and `mushrooms` are star ingredients, and `greens`
  means leaves and brassicas.** From a tag audit once the veg-forward books
  arrived: `legumes` had been declined in August with two candidates, and now
  had about ten drafts where the pulse is the point and the star was blank;
  three mushroom dishes and the leek dishes had nowhere to go; `greens` held
  tomatoes, peppers, courgettes and beans. Helen: *"Yes"* to each. Tomatoes,
  courgettes, peppers and alliums stay blank: scattered, and rarely the point.
- **2026-10-21 — `knife and fork` and `herbivore-ish` are moods.** The audit
  found 39 draft mains with no mood: plainly cooked centrepieces, and
  vegetables as the main event. On the first Helen ruled out "proper dinner"
  (*"a bit Jamie Oliver"*) for fear of it meaning *"there has to be an animal
  on the plate"*, and chose `knife and fork`: the eating, not the plate. On
  the second, `herbivore-ish` over `plant-o-rama`, `veg VIPs` and renaming
  `carbs party`: the "-ish" says a supporting anchovy or chorizo is fine,
  where "plant" reads to a visitor as vegetarian. Then: *"Herbivoreish is only
  for mains"*, so it is a co-tag rule, `herbivore-ish → main`, and a sprout
  salad or a cauliflower cheese does not take it.
- **2026-08-09, #72 — per-recipe tag calls stand and are not "fixed" for
  consistency.** `chicken-cider-stew` and `chicken-sorrel-potato-stew` are
  `freezable`, `pancetta-white-bean-stew` is not: case by case, never added to
  match the other two. The lemony cavolo nero soup is not tagged `soup` (its
  own tagline calls it a stew). The goats-cheese squash griddle cakes are
  `root veg`: squash counts.
- **2026-08-12, #187 — `eggs` is a star ingredient only where the dish is
  about the egg.** Helen's explicit call, reinstating the value three days
  after it was retired. Kept for the ajitsuke tamago, green baked eggs, pink
  eggs and the frittata; blank where egg is technique or structure: crème
  brûlée, a soufflé (whites are leavening), fritters (binder), the udon.
- **2026-10-08 — food gets no tag deriver; it gets a report.** Helen asked for
  the cocktail-mood measurement to be run on food (*"Let's do this now
  please."*). What the data can see is what the title already says (`salad`,
  `bakes`, a few stars); most tags scored at or below chance. So
  `scripts/check_food_tags.py` reads `tag_hints` and lists recipes whose tag
  disagrees with the title; it writes nothing, fails nothing and is not in
  `verify.py`. Helen: *"Great idea, yes, please build the checker first."*
- **2026-10-10 — food tags are proposed by a session reading the draft
  against each tag's written meaning, for Helen's yes or no.** She had skipped
  most proposals at ingest (*"I was somewhere where I needed to minimise
  typing"*). Twelve tags that were only names got a drafted line each and she
  answered *"Agree on all"*; they are in `_data/food/taxonomy.yml`. Hers the
  same day: *"Drafts will be very hit and miss, so tags there should not be
  used as data"*, and *"Crab pot pies with salad is not a salad"*, where the
  checker's hint fires and the recipe is right.
- **2026-10-10 — `bakes` means "would this appear on Great British Bake
  Off?"** Helen's test, which puts chocolate mousse tartlets in. In: a quiche,
  a baked cheesecake, pizza dough, fondants, puddings, crumbles, burger buns.
  Not: a soufflé, a beef Wellington, meringue swans (*"No one gets in cosy
  baking mode and makes ad hoc swans with creme diplomat"*).
- **2026-10-10 — `sweets` is renamed `sweet snack`.** Helen: *"what if we
  rename 'sweets' to 'sweet snacks', or something else with the word 'sweet'
  in it? Biscuits should be in there, but every single time I have to remind
  myself why it's not just toffee and chocolate truffles."* Singular, as `hot
  snack`'s twin. Under the new name *"Fairy cakes are in again now"*; her
  test: *"would I serve it on a cake plate at 4 o clock after a long improving
  walk?"* A saved link filtering on `sweets` matches nothing, judged a fair
  price.
- **2026-10-10 — `fiddly and fun` is a mood for the PROCESS, and `showstopper`
  is narrowed to the RESULT.** Helen: *"I wonder if we need a 'I want to faff'
  tag ... I honestly prefer savoury things, so remembering about e.g. tomato
  tarte tatin would scratch the itch for sure."* And: *"I agree that
  showstopper has drifted"*; it sat on a 15-minute venison loin. A dish may be
  either, both or neither; slow is not fiddly. A mood, not the practicality
  she first called it: a craving, so it sits beside `dessert` and `bakes`.
  (Replaces 2026-08-02's reading of `showstopper` as the craving.)
- **2026-10-11 — `main` is a real practicality tag, seeded by subtraction, and
  the same rule is the proposal at ingest.** Helen: *"Sometimes I might just
  want to cook dinner, scrolling through a list for inspiration without
  having to visually filter out kale crisps and various cakes."* Then:
  *"Declare it, please seed by subtraction, then as we go forward from this
  baseline now, we derive."* Never with `dessert`, `sweet snack`, `ice cream`,
  `drinks`, `nibbles`; asked about with `bakes`, `extras`, `starter`,
  `breakfast`, `hot snack`. A derived "dinner" button was the alternative: it
  is wrong at the edges, which are the dishes she scrolls for. Reading "we
  derive" as a proposal, not a deriver, is a session's.
- **2026-10-21 — a frittata, baked eggs, a vegetable fritter or a griddle
  cake may be a `main`; savoury pancakes are breakfast or a snack, never a
  `main`.** Fritters first: *"veg-based fritters, which are just griddle cakes
  in another hat, right? Let's allow those to be mains."* Then, the same day,
  shown that the rule took `main` off the kale frittata and kept
  `herbivore-ish` off green baked eggs, she ruled that both are mains.
  Each is a `main` question like `starter` or `hot snack`.
- **2026-10-21 — `side` is a practicality, split out of `extras`.** Helen,
  retagging Jansson's temptation and a gratin: *"-extras +side -- let's
  discuss this, there are lots of these"*, then yes to splitting it out.
  `side` is a dish served beside a main; `extras` keeps what is not a dish at
  all: sauces, stocks, pickles, doughs, spice mixes.
- **2026-10-21 — a dish with two leads has no star.** Helen, on a chicken and
  prawn pad thai: *"recipes with multiple leads have no star"*. Kale with
  chana loses `greens` on the same ground (*"legumes vs greens"*).
- **2026-10-21 — `fruit` is a cake's star only where the fruit is the
  point.** Helen chose it over "never for a cake" and "any fruit cake". The
  old-fashioned cherry cake keeps it; a lemon drizzle does not take it.
- **2026-10-11 — no soup is `one-handed food`.** Helen: *"soup is never called
  one-handed food"*. Thick spoonable soups carried it until then.
- **2026-10-11 — melting chocolate is prep, so a fridge cake is `no-cook`.**
  Helen first agreed the opposite, then: *"pulsing chocolate in the microwave
  isn't messy like cooking!"*
- **2026-10-11 — a `sweet snack` is named for the piece.** A brownie or a bar
  is one; a cake cut up to serve is not. Helen: *"I think sweet snacks are
  individual things, not slices of something else."* So not a traybake cut
  into squares either.
- **2026-08-16, #216 — `make-ahead` means a substantial part of the dish, or
  all of it, is prepared well ahead of serving; it is a separate axis from
  `freezable`.** Helen: *"a substantial part -- or the entirety -- of the dish
  can be prepared well in advance of serving without losing quality, flavour
  or structural integrity."* Not a bake that merely keeps, an overnight
  marinade, a base recipe or a condiment, and `freezable` is never a co-tag of
  it. Refined 2026-10-10: where the advance work is the real work the tag
  stays, as on a BBQ spatchcock duck rubbed a day ahead, *"keep make ahead --
  the rub is the thing here, and roasting on the day is trivial."* A Christmas
  turkey buttered the day before is not.
- **2026-10-10 — feta does not count for `cheese-tastic`, even a whole baked
  block; burrata does.** Helen: *"oooh, yeah, feta doesn't count for
  cheese-tastic"*. The tag is for cheese as the pleasure of the dish, and the
  line is drawn by the cheese, not by how much of it there is.
  `_data/food/taxonomy.yml` carries it in the tag's meaning.
- **2026-10-10 — `fiddly and fun` needs a fiddle a cook would really do, and
  threading skewers is not one.** Helen, on a chicken satay: *"isn't fiddly"*;
  on a crab salad with homemade crispbreads: *"because, come on, who's going to
  be making those crispbreads from scratch!!!"* So a recipe is not tagged for
  a component she would buy in, nor for assembly that is only repetitive.
- **2026-10-10 — a meatball on its own is `one-handed food`; on spaghetti or
  in a broth it is not.** Helen: *"I think chasing meatballs is funny, and I'd
  call that one-handed food if I didn't also have to deal with e.g. spaghetti,
  or fish the meatballs out of a soup."* The tag's meaning says nothing that
  has to be chased; this is her exception to it, and it stops at the meatball.
- **2026-10-29 — `festive` needs the dish to be the feast's own, whatever the
  page it came from.** Helen: *"'festive' doesn't automatically follow from
  'came from a Christmas feature', and is applied at other times too."* A
  chicken that uses up the Seder horseradish is not festive; a Rosh Hashanah
  honey cake is. (Restates 2026-10-10's ruling, which recorded none of her
  words, with the source-page point added.)
- **2026-10-29 — dietary restrictions are not marked.** Helen: *"I don't mark
  dietary restrictions."* No tag, note, field or question for vegan,
  gluten-free and the like, at ingest or after; a claim in a verbatim intro
  stays in its `QQ original` until she rewrites the tagline.
- **2026-10-11 — a quiche, a tarte tatin, a soufflé and a salad that is the
  meal are a `main`; a plain cauliflower cheese and a sprout salad are
  `extras`.** Helen's answers to the "perhaps" rows. Mains: a quiche, moules
  marinière, both tartes tatin, a goat's cheese soufflé, calzones, mackerel or
  scallops with a salad, scallops à la Bretonne, a rarebit cauliflower cheese,
  a peach and burrata salad, the saucy lentils, and the cabbage wedges (*"2 as
  a main"*). Not a main: kale with chana. Sides: the plain cauliflower cheese,
  Mum's rice salad, both sprout salads, charred baby gem, beer-braised
  lentils. Per-recipe calls, so #72 applies: they are not evened out.

## §8 Ingredient search

- **2026-08-01 — the ingredient picker stays, and so does title search.**
  Measured: about 600 distinct main ingredients across 300+ files, 54% of them
  in exactly one recipe, and 26–29% of recipes with no star. That is useless
  as a pantry filter and exactly what a recall lookup needs ("the one with the
  sorrel"), so neither search replaces the other. The journal recorded it as
  kept, without Helen's words.
- **2026-08-16, #281 — a bad candidate in the exclude (LEAVE OUT) picker is
  fixed for what ships, not for the drafts.** Helen's call, re-affirmed
  2026-08-20 on the identical symptom: *"The synonym collapse on the exclude
  filter has gone wrong again... This was definitely working properly earlier
  today."* It was not the code: 73 candidates for `chi` locally against 10 in
  production, 63 of them from drafts added that evening. A draft's `item:`
  lines are rewritten before publishing, so a vocabulary entry aimed at one is
  work done twice. Costed and not taken: building the picker's vocabulary from
  published recipes only. That choice is Helen's, not a session's.
- **2026-09-15, #1092 — food's HAS TO HAVE picks several ingredients, ANDed.**
  A session's call, not Helen's ruling. The issue said the filter "no longer"
  allowed more than one chip, but it had held one string since its first
  commit and nothing had ever ruled it single. #583 had given it cocktails'
  label, whose `include` is a Set ANDed across chips, so the fix gave food the
  label's own meaning. It was reported to Helen as a new capability, not a
  restored one. `?ing=` is unchanged in effect.
- **2026-10-04, #1289 — the search-for-anything box offers the index picker's
  ingredient words, never the recipes' raw ones.** Typing `swee` offered
  `sweet potato` and `sweet potatoes`; 56 ingredients were offered two or
  three times and 81 raw words landed on a half-finished search. The box runs
  each word through the picker's own `buildMasterList` and `entryKey`,
  exported and not copied, so it has no plural rule of its own. Helen ruled
  the two pairs the picker itself still doubled: *"Plum. Almonds."* (`almond:
  almonds` against singular-wins, because 23 recipes write the plural).
  Offered and declined: an issue for the picker's multi-word search missing a
  stopword or an accent — *"No need to raise the issue as I think that
  behaviour is fine."* A typed plural's shared stem is highlighted, on her
  yes.
- **Undated, #51 — where a family button "chicken (all)" is offered, the bare
  "chicken" is not offered beside it.** Helen: *"I am always suspicious of
  searches like this, so if I read 'chicken (all)' next to 'chicken' I'd look
  at both"*. Two buttons that look like one answer make her check both, so the
  umbrella stands alone. The drinks index took the same rule (*"I think gin
  (all) should suppress gin"*), and an umbrella already chosen is not offered
  again.
- **Undated, #52 — LEAVE OUT excludes on every ingredient a recipe lists, not
  on `main_ingredients`.** Helen: *"I have invited someone for dinner and they
  hate peas, so I want to see all recipes that do NOT contain peas as an
  ingredient."* A recipe with peas in it is wrong for that guest wherever the
  peas rank, so the picker reads the derived `data-all-ingredients` on each
  row (every `item:`), while HAS TO HAVE reads `main_ingredients`.
- **Undated, #273 — in the exclude picker a descriptor that does not change
  what the thing is collapses into the plain ingredient.** Helen: *"No one is
  going to dislike sesame oil but not toasted sesame oil, and this isn't an
  allergen avoider tool."* Smoked, roasted, toasted, a cut or a prep: each is
  an alias in `_data/food/ingredient_words.yml`, phrase by phrase, never a
  rule. A different product keeps its entry (smoked haddock, cocoa powder, the
  brown sugars). The vocabulary serves avoidance, not allergy.
- **2026-08-16, #281 — an "X or Y" ingredient splits into two picker entries
  only where both halves are already known ingredients; two joined by a method
  both count; a citrus fruit covers its juice and zest.** Helen's calls,
  recorded each time without her words. "Bicarbonate of soda dissolved in 3 fl
  oz milk" still contains milk, so leaving out milk hides it; leaving out
  lemon hides a recipe that uses only the juice or the zest. Each compound is
  a named row in `_data/food/ingredient_words.yml`, not a pattern.
- **Undated — `gressingham` is stripped as a modifier, "five-spice powder" is
  "five-spice", and `to glaze` is a trailing phrase.** Each recorded as
  Helen's explicit call, with no words. Gressingham is a breed name and is not
  a precedent for stripping other brand names. The two five-spice spellings
  are one picker entry and get no "(all)" button.
  `_data/food/ingredient_words.yml`.

### §8.2 The food shopping list and its scaler — #801, built 2026-09-07

- **2026-09-07, #801 — the food index has cocktails' shopping list and scaler,
  with every feature except costing.** Helen: *"add scaler and shopping list
  feature to food recipe shortlist page. This can be copied directly from the
  food page — I would like all the same features. But there is no need to cost
  the portions. When serving size is unclear, please make your best guess.
  Group the shopping list by grocery aisle, e.g. produce, dairy, fish, meat,
  non-perishable etc."* "The food page" was read as the cocktail page, which
  had the feature since #546. A `serves:` recipe's box counts people, so a
  fractional multiplier (four portions of a recipe for six) is ordinary here,
  as it is not for drinks.
- **2026-09-07 — a scaled amount is never rounded coarser than 1 g.** Helen:
  *"For now, don't tidy/round beyond 1 g precision"*, then, unprompted: *"I
  mean don't roudn to 10 g or 5 g, round to 1g"*. Two thirds of 200 g prints
  133 g. `⅔ tsp` for exactly two thirds is notation, not tidying, which is why
  `fractionText` keeps a 1e-6 tolerance. Never ruled, and still as it was:
  whether a bare count rounds up for shopping (`2.83 onions`). The later
  rounding rulings cover by-eye measures only.
- **2026-09-07 — the shopping list has ten aisles, in shop order: produce,
  meat, fish, dairy & eggs, bakery, frozen, store cupboard, spices &
  seasonings, drinks, other.** Helen chose them from three sets offered; the
  order is a shop's, not an alphabet's. How an ingredient finds its aisle is a
  session's: a keyword table in `_data/food/aisles.yml` where the longest
  keyword wins, so an exception is an entry and never a precedence rule
  (`milk` against `coconut milk`). The recipes' `item:` strings are free text,
  so a list of ingredients was not possible.
- **2026-09-07 — within an aisle the shopping list is alphabetical.** A
  session's call, not Helen's ruling, and reversible. It departs from the
  drinks list's descending volume: the aisle heading has already done that
  job, and a food aisle mixes grams, spoons, cloves and bare counts, so there
  is no single axis to rank on.
- **2026-09-07 — the shopping list totals in grams and millilitres only; kg, l
  and cl fold into them, and tbsp, oz and bare counts are never converted.** A
  session's call, not Helen's ruling. A litre is a thousand millilitres on
  both sides of every recipe, so folding is not the conversion
  `shopping-list.js` refuses. That rule is about units with no defined
  relationship (nobody can say how many ml a dash is), and each of the
  untouched units would need one invented.
- **2026-09-07, #815 — a recipe that states no number of people carries
  `serves_estimate:` in its own front matter, estimated at ingest and printed
  with a `~`.** Helen: *"We need estimate the number of people served by 750
  ml, then add that to the front matter somehow. [...] all of these will need
  to be estimated at ingest. Claudes can check with me if unsure."* Its own
  key and not a second `serves:`, her choice: `makes:` opens with a number 66
  times and `serves:` gives none 20 times. The `~` is her ruling in the same
  message. A side file that held the estimates outside the recipes was deleted
  the same day: one home, beside the words it estimates from. A `QQ` in
  `serves:` stays untouched beside the new key. On 2026-10-18 she widened who
  estimates: a web Claude may write one *"if they want to, then for Claude
  Code to tidy at the next round"*, so an unsure figure is written and put to
  her, never left out.
- **2026-09-07 — the shopping list never prints a recipe's yield after its
  name.** Helen, on a row reading `7  Moules Marinière serves 4`: *"please
  don't say 'serves X' after the recipe name at the top of the scaler. This
  screenshot makes it look like I'm asking for 28 portions of mussels."*
  Dimming it is not a fix: a number at each end of a short line reads as one
  expression whatever the middle says, and the row must open with a number.
  The yield lives in the input's `title` and `aria-label`.
- **2026-10-04, #1125 — a by-eye measure scales; it is never held still, and
  one written with no number counts as one.** Helen: *'If a recipe calls for
  "a handful of parsley", three orders of that recipe should call for "3
  handfuls of parsley"'*. The first build held it still and named it on the
  Not-scaled line, the opposite of what she wanted. `a`, `an`, `one` or
  nothing reads as one. "a few" is not a number: the line stays as written and
  is named on the Not-scaled line by its ingredient (the measure phrase,
  anything from the first comma or bracket, and a trailing `to taste` are
  cut). A list item named by its first member is fine: *"doesn't state an
  amount, so scaling is by common sense."*
- **2026-10-04, #1286 — on a `makes:` recipe the scaler counts the thing made,
  in whole recipes: ×1, ×2, ×3.** Helen: *"Never tell me how many cookies are
  in a portion!!!"* and, on seeing it step one waffle at a time: *"the buttons
  should still multiply the recipe in integers, just showing number of
  waffles. So 1x is 5 waffles, 2x is 10 waffles. Otherwise we'll need to start
  showing eggs in units of 1/27 or something."* `makes:` is never read as
  people; `page.made` (`_plugins/food_yield.rb`) sits beside `page.portions`,
  not in place of it. Only a `serves:` recipe steps one portion at a time.
- **2026-10-04, #1286 — how a `makes:` line is read: a number word is a count,
  a dozen stays a dozen, a volume multiplies, "64+" keeps its plus, and "some"
  keeps its portions guess.** Helen, one per shape: *"Two 8-inch cakes"*; *'"1
  dozen" doubled can be "two dozen". Our scaler is integer.'*; *"950 ml for
  one order of a recipe becomes 1900 ml for 2"*; *"64+ tiny macarons, 128+
  tiny macarons"*; *'if "some" is originally guessed to be 4 portions, 2x
  should be 8 portions'*. The words are `yields:` in `_data/food/scaling.yml`.
  Not ruled: whether the "Makes" line at the top of the page moves with the
  box.
- **2026-10-04, #1286 — a `makes:` recipe is offered half a recipe only where
  the build judges the halved figures sane, and only below ×1.** Helen: *"Half
  a recipe would be great where the numbers aren't insane! Can we judge
  that?"* and *"not having half recipes in between integers, just between 0
  and 1"*. `_plugins/food_half_recipe.rb` refuses on the first line that will
  not halve: an odd count of something not `halvable`, a spoon that is not a
  multiple of ¼, a cup that is not a multiple of ½, a yield below one. Never
  special-case a recipe in the judge. Shown "⅞ cups whole milk" she said
  *"Please take the half step off the waffles. 2-3 waffles isn't enough!!!!"*,
  and the fix was the cup rule.
- **2026-10-04, #1286 — eggs never halve in a food recipe, and the `halvable`
  list is Helen's.** *"In: leaf, star anise, nutmeg, stock cube, sachet, tin,
  jar. Rest correct."*; *"Eggs: not halvable for food recipes. Given by ml or
  weight for cocktails so irrelevant."*; *"Neither mince pies nor sweet cream
  base halve"*. So a `lot` of another recipe is a count to the judge, which is
  why `half_step_counts` is a list apart from `half_step_measures` in
  `_data/food/scaling.yml`. The list is about ingredients: a yield of "1 jar"
  still does not halve.
- **2026-10-04, #1286 — a count that scales down to exactly one makes its
  item's noun singular.** Helen, on half a recipe: *"at 0.5x, that should read
  '1 large egg' not 'eggs'."* The noun is in the item, so the amount's plural
  rule never reached it. The scaler uses the house `singulars` map and leaves
  the item as written where that is not safe. It applies to a `serves:` recipe
  shown for half its people too.
- **2026-10-07 — a `makes:` range starts from its lower number.** Helen:
  *"where 'makes' is a range I want to use the lower number."* Told she had
  ruled *"Take the midpoint"* on 2026-10-04 and asked whether this replaced
  it: *"lower number please, new ruling."* "4–6 waffles" shows 4 and steps 4,
  8, 12. It is the rule `serves:` has had since 2026-09-07 (*"under-catering
  is worse for me than over-catering"*), so the two kinds of recipe agree.
  Half a recipe of an odd count still shows a range ("2–3"); her *"a range of
  one"* stands for that case. (Replaces the midpoint of 2026-10-04.)
- **2026-10-09, #1297 — on the shopping list a `makes:` recipe counts batches,
  in words; a `serves:` recipe counts portions.** Helen: *'The shopping list
  scaler could show e.g. "X batches of 18 Peanut Butter Cookies", allowing
  half-batches where that doesn't split eggs. Is that doable? That stops us
  saying 2 cookies is a portion -- not out of principle, but because that's
  meaningless.'* The figure after "of" is one batch's and does not multiply.
  The half step is the build's existing judge, and "set all" skips batch rows.
  The batch box she killed in September (#815) was wrong because it looked
  like a portions box; this one says which it is. (Replaces #815's "no
  batches", for `makes:` recipes only.)
- **2026-10-09, #1297 — the shopping list reads the zest and the juice of one
  lemon as one lemon.** Helen: *'I would like to cleverly combine e.g. "zest
  of 1 lemon" and "juice of 1 lemon" to make "1 lemon" in the shopping list.'*
  Built as a reading of the recipes, not by changing them. Within one recipe,
  different parts of a fruit take the larger and the same part adds; two
  recipes add. That rule is a session's, stated to her before building and not
  objected to. A spoonful of "lemon juice" is never turned into lemons. The
  words are `whole_fruit:` in `_data/food/scaling.yml`.
- **2026-10-10, #1125, #1297 — on a recipe page a handful, sprig or bunch
  scales to the nearest quarter; a pinch, dash, splash, knob, drop, twist, lot
  or pat to the nearest half.** Helen: *"Recipe page handfuls and sprigs in
  1/4 too please."*; *"Sprigs: Let's round to 1/4 please, and express in
  fractions not decimals."*; *"Drops, twists, lots etc, please round to the
  nearest 1/2 -- these are smaller than handfuls and sprigs."* It began with
  *"some recipes scale 1 handful to e.g. 1.17 handfuls, which is obvious
  nonsense"*. The lists are `quarter_step_measures`, `half_step_measures` and
  `half_step_counts` in `_data/food/scaling.yml`. A session's readings:
  `bunch` went with sprig, `pat` rides her "etc", and pinch, dash, splash and
  knob stayed in halves because her sentence names the handful. (Replaces
  2026-10-04's half-step handful and linear sprigs, drops and pats.)
- **2026-10-10, #1297 — on the shopping list a by-eye measure is bought as the
  next whole one, with the recipes' figure in brackets, stepped as the recipe
  page steps it.** Helen: *"I'd like the shopping list not to write 1.17 sprigs
  either, so please round that upwards to the next integer like this: '2
  handfuls fresh parsley (1 1/4 in the recipes)'."* and *"1.17 handfuls should
  buy 2, again giving the bracketed requested number."* A handful, sprig or
  bunch is quoted to the nearest quarter. Refined 2026-10-11 for the half-step
  measures: *"Half a pinch doesn't make sense, but half a handful sort of does.
  Let's round pinches to the nearest 1/2."* Dash, splash, knob, drop, twist,
  lot and pat follow the pinch, a session's reading. Declined: a decimal in
  brackets, and nearest with no bracket. The total is rounded once.
- **2026-10-10, #1297 — a counted row's label agrees with its number ("2
  lemons"), from a list of nouns and never from a general plural rule.**
  Helen: *'Can we fix the "2 lemon" thing?'* A spelling some recipe wrote is
  used first; a made form only for a noun in `count_nouns` in
  `_data/food/scaling.yml`. A rule on "the name's last word" was measured over
  both collections and was wrong for about a quarter of 251 names ("sprigs
  thyme", "goose", "skinless"). Known and accepted: "pounds yellow onions" at
  one or less reads "pounds yellow onion".
- **2026-10-10, #1297 — the shopping list names what it did not scale, and
  puts the batch rows last under a hairline.** Helen: *'we add a note to the
  scaler: "(Not scaled: extra teriyaki sauce, juice of ½ lime, a few coriander
  sprigs, a few sprigs Thai basil)" Adding this to the shopping list page
  would at least show the user in what ways the list is incomplete.'* and *"If
  we group the batched recipes at the bottom of the shopping list scaler
  section, it's clear the portions scaler multiplies portions whereas the
  batches are manual. Maybe just a little vertical space and a soft hairline
  separator?"* A row is named when any line behind it had no amount. Since
  2026-10-11 each unscaled item also carries its recipes' names in brackets:
  *"so the user knows what to do"*.
- **2026-10-11 — on the shopping list a yield that is one named thing is
  counted as that thing, not as a batch.** Helen: *'anything that creates a
  batch should get "makes" -- I don't want to tell anyone what a portion size
  of biscuits is!!!! [...] When the "makes" contains a word like cake, or
  something that doesn't make a "batch", we should do the same, so "two
  13x9-in traybakes".'* Her forms: *'"× 8-inch Beetroot Chocolate Cake"'*
  where the title names the thing; *'"[2] jars of peanut sauce", "[3] rainbow
  confetti traybakes"'* where it does not. A container comes first with "of";
  anything else follows the title. Which words are containers is
  `yields.container_words`, a session's list of nine. No colon. The recipe
  page ("2 × 8-inch cakes") was already right.
- **2026-10-11 — a batch row says the thing made once: after the title where
  the title does not name it, with the title's own noun made singular.**
  Helen: *'should say "batch of 24 Guinness, Beetroot and Chocolate Cake
  squares"'* and *'Can we get to "batch of 16 brownie squares", so where the
  thing name word in the title is plural we make it singular? I can't imagine
  this is common.'* Where the title already names the thing ("18 Peanut Butter
  Cookies") nothing is added.
- **2026-10-11 — a `makes:` that opens with a number must name the thing ("16
  bars", never "16").** Helen: *'Cookie dough bars currently just show "batch
  of Cookie Dough Bars", even though the recipe has makes 16.'* A bare count
  is fixed in the recipe, never by a rule on the list. Asked whether to add
  the noun to the drafts in that state: *"yes please"*; 33 were changed and
  the ingest document requires it. The same answer as Delia's pancakes on
  2026-10-04 (*'Can Delia's pancakes please scale as "8 pancakes", "16
  pancakes".'*) and as her own scones: *'Grandma's scones should have makes: 8
  scones (2 large rounds of 4)'*.
- **2026-10-11 — recipe names in the shopping list are links, set like the
  index row titles.** Helen: *"render the name of the recipe in this shopping
  list feature the same way we do in the recipe list row titles, just smaller
  of course, and make them links"*. The class is `.shopping-list-recipe-link`.
- **2026-09-07, #815 — a component recipe's `serves_estimate` takes its
  commonest use and a note on the recipe carries the rest; no schema is
  invented for it.** Helen: *"I have no idea how to model this. Please add all
  this as a note on the recipe and I will tidy up later."* A ganache glazes one
  cake, fills another, ices 12 cupcakes or makes 16 truffles; a caramel is a
  sauce or a tin's filling. `chocolate-ganache` and `caramel` each carry one
  number and the note. A schema for several yields is hers to ask for.
- **Undated, #1118 — the food scaler's box is as wide as the drink scaler's:
  two characters and the caret.** Helen: *"the same number of characters as
  the cocktail recipe scaler (just over 2)"*. `calc(2ch + 1.6ch)` in
  `_sass/food/_recipe-scale.scss`, the formula
  `_sass/cocktails/_cocktail.scss` uses. The wider box on a `makes:` recipe
  (five characters, #1286) is a session's value and nobody has ruled on it.

### §8.3 The shortlist is a view, not a facet — #918, 2026-09-10

- **2026-09-10, #918 — `shortlisted` is a view, not a filter: it never
  combines with another filter.** Helen, after fourteen steps of weekend
  planning on both indexes, four of them surprising: *"I'll even say a bug not
  a preference."* It had been declared an ordinary filter and so ANDed with
  everything. Pressing it on clears every other filter and shows the whole
  shortlist; setting any other filter turns it off and applies that filter to
  the whole collection; a half-typed search keeps it; `clear all` turns it
  off. Not taken: keep composing and say so in the count ("1 of 2 shortlisted
  match"). She had already ruled it a bug.
- **2026-09-15, #1093 — a shortlist link is shown, not saved, and "keep these"
  makes it yours.** Helen chose *"Show it, don't save it"* over merging the
  list in, replacing the reader's own, or parking the feature; and *"Yes, a
  'keep these' button"*, which merges the list in and never un-marks anything.
  Until then the reader's own store is untouched, and any filter or `clear
  all` leaves the view as #918 says. The link is `?shortlist=slug,slug`;
  `?shortlist=1` keeps its meaning.
- **2026-10-11 — opening a sent shortlist link shows the index with the
  shopping list open.** Helen: *"when I enter a URL for a shortlist, please
  show the index page with the shortlist open (i.e. with shopping list
  open)"*. Read as the sent-list link, since `?shortlist=1` already opened it;
  that reading is a session's. Opening still saves nothing. (Replaces #1093's
  *"Hide it in shared view"* of 2026-09-15.)
- **Undated, #546 — the shortlist lives in one browser on one device, one
  list per site, with no account; that is a ceiling, not a first step.**
  Helen: *"one browser, one device, no sharing, no account etc is truly all I
  want -- I actively don't want more."* And it *"can be food rows or cocktail
  cards ... doesn't need to be a mixed list on one page"*. `localStorage`, one
  store per site. The share link of #1093 is the one thing added since, and it
  saves nothing. Do not propose sync or sign-in.
- **2026-10-10, #1342 — the note over a shared shortlist and its "keep these"
  button keep the wording an agent wrote.** Helen, shown both: *"Both good,
  thanks!"* "a shared shortlist (N)" and "keep these" are approved strings,
  not placeholders awaiting her copy. The share panel's two lines are her own
  words (PR #1100).

## §9 Cocktails

### §9.1 Privacy, the clone, the fetch discipline

- **2026-08-16 — cocktail field names and vocabularies are public; only the
  drinks are private.** Helen accepted this once the fully private alternative
  (one private clone plus symlinks into eight canonical paths) had been costed.
  So `_data/cocktails/` and the tests live in the public repo and the drafts in
  the private `_cocktail_drafts` clone, gitignored here
  (`test_every_drafts_collection_is_gitignored`). The corollary, #624: a public
  test never requires private drink data.
- **2026-10-11 — the public repo's `main` moves only by a PR Helen merges; a
  small set of changes may be pushed straight to a private drafts repo's
  `main`.** Helen: *"PRs for the main repo, pushing to main for the private
  repos is fine for small sets of changes. Changes with a bigger footprint
  should be PRs."* Committing on any `main` is still refused by
  `guard-main-branch.py`, so the work is committed on a branch and pushed
  `<branch>:main`. `scripts/git-push-agent.sh` refuses `main` on the public
  repo only. (Replaces the ruling of 2026-08-29, *"Pushing to main in the
  private repos is fine"*, which named no limit.)

### §9.1.1 The drinks publication gate

**The gate.**

- **2026-09-02, #668 — drinks carry food's three flags, every draft starts with
  all three `false`, and `proofread` gates publication on both sites.** Helen on
  `rewritten`: it *"shows me if I have rewritten it, not an agent"*; on drafts
  carrying the flags at all: *"this is honest"*. The names and their order are
  food's. `output: false` is what keeps a draft private, not the flags.
  Declined the same day: gate flags shown on drink cards. It was built and
  reverted, because food's cards have not shown gate state since #562.
- **2026-09-10, #839 — a batch of per-drink copy goes to Helen as one CSV, not
  as a page to click through.** Helen: *"this is the least chaotic way of
  collaborating I think."* Every drink in one table (how near it is to
  publishing, ship rating, current line), worked through in her spreadsheet,
  sent back, diffed, and written into the files by a script. #839 had proposed
  a local page instead. Review such a field as a SET: her taglines were fine
  line by line and leaned on the same three devices across the set.
- **2026-09-17, #1137 — a drink publishes only on `awaiting_fix: false` AND
  `proofread: true` AND `rewritten: true`; `made_before` does not gate.**
  Helen: *"I want to block cocktails that have not been rewritten. I want to
  allow cocktails that I have not made. I will rewrite these before making
  them."* She reads a drink on the live site in order to make it, so the words
  there must be hers. Unmade is fine, unrewritten is not; the two halves were
  swapped twice while building it. Drinks only: food keeps two legs, and
  widening it is a separate ruling. `_plugins/publish_gate.rb`, held by
  `test_an_unrewritten_drink_is_held_back_but_an_unmade_one_publishes`.
- **2026-09-17, #1137 — only Helen writes `rewritten`, on either site and in
  every folder.** A flag that decides whether a page exists belongs with
  `proofread`: hers alone. If a staged drink still says `false`, say so and let
  her flip it. Moving a drink into `4-promote/` does not mean "Helen rewrote
  this", because that folder holds both kinds (replaces the ruling of
  2026-09-04, which let an agent type `rewritten: true` there).

**Moods ruled on while promoting.**

- **2026-09-09 — `on fire` is hand-assigned as well as derived.** It is on
  `moods_by_hand` in `taxonomy.yml`. The rule reads METHOD steps for alight,
  flame and burn; Cobra's Fang has its fire in `to_serve`, so only Helen's own
  tag reaches it. The rule had scored .40 against her tags on 2026-08-30, one of
  the four worst, and was left off the list by oversight.
- **2026-09-09 — swizzles are not faff: `swizzle` and `churn` left
  `mood_step_words.faff`.** Helen: *"Swizzles are not faff"*. A swizzle IS
  churning, so one technique counted as two faff moments and met the threshold
  alone. Both words stay in the `ice`, `churned` and `slushy` lists. Refined
  2026-09-10, *"A muddled Swizzle is faff"*: Sapin's Swizzle gets `I want to
  faff` from a `mood_include`, not from a lower threshold, which would retag
  every drink that muddles anything.
- **2026-09-09 — Mastiha Mojito is `sharp` by a per-drink correction, not by
  adding mastiha to the sweeteners.** Helen: *"I have tasted it and you
  haven't!!!!"* One drink uses mastiha liqueur, filed under `loud`; moving it
  to `sweet` would be a claim about the ingredient made to reach a conclusion
  about one recipe. Her question each time was *"I can't tell if this should be
  manual override or if the rule can be amended"*, and the answer is measured:
  run `scripts/derive_cocktail_moods.py` (a dry run by default) and count the
  drinks a rule change would move.
- **2026-09-17 — Hurricane gets `I want to faff` from a `mood_include`, not a
  rule change.** Helen: *"it has 50000 ingredients AND needs a blender, does
  that count?"* It misses by one on each axis. Measured first: a threshold of 8
  gives the mood to six drinks, and counting a blend twice gives it to all five
  that blend. Likewise 2026-10-02, #1268, Porn Star Martini: *"Scooping out
  three passion fruit half-shells definitely counts."* Not a new faff word:
  `scoop` would be one hit where two are wanted. A mood typed into a recipe by
  hand fails `test_every_drinks_moods_match_the_derivation`.
- **2026-09-18 — `warming` from cinnamon alone stays a rule; Gunmetal Blue
  loses it by a correction.** Helen: *"I don't just want to call anything with
  cinnamon in it 'warming' (although I accept we will often do that)."* The
  parenthesis is the ruling. Two drinks take `warming` from cinnamon alone and
  Fake ID keeps it, so deleting the trigger would be wrong.
- **2026-09-18 — Fish House Punch keeps `ice ice baby` by a `mood_include`;
  Gunmetal Blue's was withdrawn.** Helen: *"Fish House Punch: a) I call 'ice
  tea', and b) comes over lots and lots of ice"* against *"Gunmetal Blue
  doesn't have ice..."*. `serve.ice` cannot carry QUANTITY: lots of cubed ice
  and one cube are both spelled `cubed`, so the rule cannot tell them apart.
- **2026-10-22 — a `QQ` before an ingredient does not withhold a mood.**
  Helen: *"QQ before an ingredient shouldn't block tagging. It's circular,
  isn't it."* A `QQ Gin` asks which gin, not whether there is any. The
  deriver reads a hint that names a spirit family or a spirit generic; a hint
  it cannot place still reads as nothing, and she may name the bottle or
  confirm the generic to unblock it.

**Garnish, method and serve, ruled on while promoting.**

- **2026-09-17 — ginger is two garnishes, `ginger wheel` and `stem ginger
  slice`.** Helen: *"Ginger, yes, two entries (and counting)."* A wheel off a
  raw root and a slice of stem ginger out of its syrup are different objects.
  `ginger wheel` drops the drafts' "fresh": raw is the default for a root.
- **2026-09-17 — `fruit wedges` is declared, the one garnish that does not name
  its fruit.** Helen: *"Honestly fruit wedges is enough, the maker can
  choose."* Offered `pineapple wedge` or `no garnish`, she kept what she wrote:
  on a heaped tiki mug the fruit is whatever is about. A known exception, not a
  precedent. #1079 (2026-09-15) ruled the other way for an INGREDIENT, where
  the fruit changes the drink.
- **2026-09-17 — Ti' Punch keeps a method.** Her idea was no method, only a
  Serve line reading *"Assemblage au choix."*
  `test_method_is_a_non_empty_list` refuses that: a drink with no method
  renders as a drink with nothing left to do. So one method step, her phrase in
  `to_serve`, and squeeze-or-muddle in a note.
- **2026-09-19 — `half lime shell` is `half an empty lime shell`.** Both shells
  in `garnish.yml` now bring their own article. Granted on live drinks without
  a flag flip: *"Those rewords are fine for Mai Tais, no need to flip the
  flag."*
- **2026-10-01, #1256 / #1249 — a flaming shell's rum is a measured ingredient,
  25 ml, `as: "shell"`; the fire is `to_serve`.** Helen: *"let's do real ml.
  Default to 25 ml, nice and tidy. Use that for all my cocktail recipes unless
  otherwise stated, and retroapply this. But Cobra's Fang should be 25 ml
  too."* and *"Fire is to serve!"* One act had five spellings on five drinks,
  two of them counting no units. `(garnish)` as an amount is retired by it. It
  is not a float (#1256), so the direction stays `(shell)`. The cinnamon is
  listed as `(sprinkle)` wherever it is sprinkled; hers to reverse.
- **2026-10-01, #1256 — a rum-filled shell IS in `garnish`, and the layout
  drops its generated "Garnish with…" step.** Helen, reading pages where the
  shell had been kept out: *"all say (shell) after the final rum, but haven't
  mentioned a shell yet."* Offered garnish or ingredient, she took garnish. A
  shell with no rum (Mai Tai) is an ordinary garnish and keeps its step.
  `no garnish` remains a decision that renders; `[]` means nobody has decided
  (replaces the rulings of 2026-09-09 and 2026-09-19, which took the shell out
  of `garnish`).
- **2026-10-01, #1256 — `to_serve` items are a declared vocabulary; the field
  stays one string.** Helen: *"Cinnamon sparkles can sit in method. We could
  add 'more cinnamon sparkles' to our dictionary?"* Items are split on `.` and
  `,` and checked against `serve.yml`
  (`test_every_to_serve_item_is_declared`). Forcing one separator would have
  taken four live drinks off the site for punctuation. Porn Star Martini's
  "Champagne on the side." left `to_serve`: *"It's an ingredient not an
  optional serving suggestion."*

### §9.2 / §9.2.1 The sources

- **2026-10-20 — a (source) goes in a title only where two drinks share a
  name.** Helen: *"Let's only use a (source) where we have more than one, e.g.
  'Mai Tai (Difford's)' vs the one I call my signature."* Her own keeps the
  plain name (2026-08-31: *"name it 'Sazerac (Death & Co)', leaving mine as
  simply 'Sazerac'"*). So Difford's Mint Julep became "Mint Julep (Difford's)"
  beside IBA's, and "Margarita on the Rocks (Difford's)" lost its bracket. Two
  exceptions she chose: the Zombie keeps "(Difford's)" beside the live Zombie
  Intoxica, and a bracket describing the drink stays (*"keep gin (it's
  labelling the drink base, and we'll have more of these)"*). "(classic)"
  went: Hurricane and Margarita, renamed live on her grant ("Break URLs,
  it's fine").
- **2026-09-01 — a `QQ` that has been ANSWERED becomes a plain note recording
  the answer; only a `QQ` that was wrong to ask is deleted.** Helen, asked a
  third time about Pic-a-de-Crop Punch's 12 oz of overproof: *"we've agreed
  this twice now, so stop tracking it."*
- **2026-08-30 — a drink's `source` is optional and always will be;
  `sources.yml` fixes spelling, never coverage.** Helen: *"I sort of don't
  care about this. You can't copyright facts, and I am taking no prose from
  anywhere. Some will be attributable to a big-name inventor, bar or maybe
  hotel, and it's nice to note that, but I'm not going to sweat it."* So
  `source: ""` is correct, nothing requires one, and the publications list
  must not become a closed vocabulary. `scripts/build_ingest_vocab.py` prints
  it to the ingest documents as spellings only.

- **2026-10-19 — IBA drinks have no source.** Helen, in the chat that ingested them: *"No source."* `source` and `source_url` are empty and the URL is kept nowhere.

### §9.3 The schema

- **2026-08-17 — a preferred bottle is a `suggestion`, never a `generic`; and
  `glass` is a list.** Helen, on Cherry Heering: *"I'd note my preference as
  the example not the category"*.
- **2026-08-26, #291 — what a drink is served WITH lives in `to_serve`, and no
  method step restates it or the garnish.** Helen: *"things to serve with (like
  a paper umbrella) aren't written or laid out the same way."* Four drinks had
  "Serve with a straw." in `method` while three said `to_serve: "Straw."`
  (#573). `test_no_method_step_restates_to_serve_or_garnish` keys on the
  leading verb; `to_serve` is a string (`test_to_serve_is_a_string`).
- **2026-08-30, #571 — no `ml:` key on an ingredient; the amount is one string
  read through `measures:`.** Helen: *"Food YAML has this structure, and I'd
  like cocktails to match."* All 521 `ml` values derived exactly from the
  amount, and the key was absent wherever a number was hardest to get.
  `test_every_amount_is_readable_as_a_quantity` is the guard. A bare number
  with no unit in the source keeps its figure and a `QQ - no unit in the
  source` note.
- **2026-08-31 — no US units: an ingest converts to ml.** Helen: *"I don't want
  any US units, just ml, so please convert for me as part of ingestion. 1 oz =
  30 ml."* Extended to `tsp` (5 ml). `oz` and `tsp` stay declared in
  `measures:` because the dictionary is what makes a conversion checkable. A
  verbatim quoted recipe inside a note keeps its ounces.
- **2026-09-02, #669 — soda water, never club soda.** Helen is not in the US
  and doubts the difference is more than marketing. A mention inside a note
  recording a source's own words is left as the source wrote it.
- **2026-09-03 — a barspoon is `5 ml`; an egg or a sugar cube is an INGREDIENT,
  not a unit.** Helen's rulings. A barspoon is converted at ingest like the US
  units.
- **2026-09-04 — `half` and `whole` are units.** Helen's ruling, from the
  Caipirinha: `amount: "0.5"` became `"half"`. A whole fruit is counted, never
  measured, because `juice_yields` gives a range per fruit.
- **2026-09-04 — a method step may carry its own `note`.** Helen: *"separate
  note field please, although it will be used sparingly"*. So a step is a
  string or a `{step, note}` pair, every reader of `method` goes through one
  helper, and the mood deriver reads the step AND its note.
- **2026-09-04 — the rim step is the Margarita's own sentence.** Helen: *"her
  Margarita sentence is canonical, but swap the tequila for the leading spirit
  in the rare case it isn't tequila"*. `methods.yml` holds it: "Dip only half
  the rim in water (or tequila) then coarse salt." (replaces her 2026-09-02
  wording, "Salt a half-rim of the glass.").
- **2026-09-04 — the twist step is written by the layout; no drink writes
  it.** Helen: *"this should become canonical, for each type of citrus
  twist"*. Three drinks had it by hand in three wordings, and one said discard
  while its garnish said the peel stays. The sentence is `methods.yml`'s and
  `test_no_method_step_opens_with_express` refuses a hand-written one.
- **2026-10-11 — the express step names its twist.** Helen: *"When we have a
  twist of something as a garnish, let's mention it again in the autogenerated
  express line"* — "Express the lemon twist over the drink then drop it in."
  The layout swaps the garnish, less its `(discarded)` tail, into the declared
  sentence.
- **2026-09-06, #297 — `serves:` exists on punch bowls and other shared
  drinks, and the scaler does not read it.** Helen's call. Optional; absent
  means one glass.
- **2026-09-06, #754 — an ingredient may carry `as:`, a closed vocabulary.**
  Asked whether a field earned its place for three floats, a rinse and some
  muddles, against `card_order:` by hand or leaving the card order wrong,
  Helen chose the field. Helen, 2026-09-07: *"`as:` on every one, and a test
  that finds the rest"*;
  `test_a_method_that_floats_or_rinses_says_so_in_a_field` is that test.
  `float`, `rinse`, `muddle`, and `shell` since 2026-10-01 (#1256). Declare a
  vocabulary and its guard BEFORE any drink carries a new value: the suite
  gates the deploy.
- **2026-09-21 — `QQ` is a tripwire, not a grammar: nothing publishes with
  `QQ` anywhere in it, on either site.** Helen: *"QQ just means 'Helen pay
  attention to this for some reason', then 'QQ CLAUDE' means that Claude
  rewrote a method step... Honestly we don't need to disambiguate, only to
  block anything on the site from publishing with a QQ in any context, hence
  why I use 'QQ' rather than any mark that might appear in real, wanted
  text."* Declined: reconciling the five spellings of the marker.
  `test_no_published_drink_carries_a_qq` (`\bQQ\b` over the raw file) is the
  drinks half; food had `test_no_qq_placeholder` already.
- **2026-09-21 — `PLACEHOLDER` is retired for `QQ original`.** Helen: *"Let's
  revise all 'PLACEHOLDER's to QQ... we're only changing history."* Eleven
  method steps still carried the old marker and nothing matched the word, so
  one could have published. `QQ original` is the source's half of a method
  step, `QQ Claude` the rewrite.
- **2026-09-21 — a tagline Helen has not written begins `QQ`, on both sites.**
  Helen: *"a drink without a tagline written by me gets a QQ, so I protect my
  voice in the public content."* Food may keep the source's words behind it:
  *"it's less of a problem for me if source taglines remain, but please QQ at
  the start of the line"*. Which taglines are hers is read off
  `meta.rewritten`; git blame names whoever last tidied the line. Refined
  2026-10-08: a cocktail ingest writes a bare `"QQ"` and drafts nothing,
  *"Let's stop Claude drafting taglines."*
- **2026-09-21 — `item` is gone from every drink.** Helen: *"'item' needs to
  go. Kill it with fire. Data can be read straight into generic/suggestion with
  or without QQs, and anything genuinely unclear added to a page note for me
  (titled QQ so I definitely find it)."* It held the source's wording and
  nothing rendered it. The source's words now go in `generic` as `"QQ <the
  source's words>"`.
- **2026-09-21 — `suggestion` is always present, `[]` where nobody has
  chosen.** Helen: *"At ingest, please add a blank suggestion field if there
  isn't a named suggestion, because that saves me typing YAML when I come to
  it."* Never `["QQ"]`: that makes `test_every_suggested_bottle_resolves` skip
  the line.
- **2026-09-21 — a named bottle resolves the category mechanically; a
  character is only ever PROPOSED.** Helen: *"If the source says 'Gosling's'
  then the correct thing for Claude to do is give 'moderately aged rum,
  character: blackstrap'. But if a recipe gives 'blackstrap' Claude shouldn't
  suggest anything."* Proposals go in `generic_claude` / `suggestion_claude` /
  `character_claude`, her flat shape, chosen over a nested block and over a
  report, so the source's words stay behind the `QQ` beside the proposal for
  her to check one against the other (*"I'd want to make sure Claude doesn't
  always confidently write 'Gosling's' instead of both."*), and are legal only
  while that ingredient still carries a `QQ`. `scripts/resolve_pours.py` reads
  exactly and never guesses; it skips `not_reached_for` bottles and
  `hers_to_apply` generics.
- **2026-09-26, #1217 — an unmeasured amount is a bracketed noun: `(top)`,
  `(splash)`, `(float)`, `(rinse)`, `(sprinkle)`.** Helen: *"option A please,
  certain … just use '(top)' as the amount where it's an unspecified ml top,
  or '(splash)' for an unspecified splash."* Every ingredient HAS an amount
  (her ruling of 2026-09-02, #669, when the words were `to top` and `to
  rinse`). An ingredient with no measure says its use in the AMOUNT; one with
  a measure says it in `as:`, so the mark appears once. `to taste` kept its
  shape: it hands the decision to the drinker (#752).
- **2026-09-26 — `"dashes"` in the plural, `"dash"` when it is one.** Helen:
  *"Yes please to a test."* `test_a_counted_unit_agrees_with_its_count`,
  scoped to units whose singular AND plural are both declared, so `pinch`,
  `sprig` and `each` are out of scope.
- **2026-10-02, #1263 — an ingredient's direction prints UNDER its amount, in
  the amount's own type.** Helen: *"having "(float)" at the end of the
  ingredient line as it is is easy to miss"*, then *"Option 1 please, let's do
  it. Match font styling with the ingredient amount, just to be crystal
  clear."* `.cocktail-use` is a sibling of `.cocktail-amount` inside
  `.cocktail-measure`, never a child: the scaler reads the amount span's whole
  text (replaces the placement half of #1217, which put it after the bottle).
- **2026-10-04, #1213 — a cocktail DRAFT's top-level keys are in the order the
  page prints them.** Helen: *"yaml fields should be rewritten in the order
  they appear on the page, top to bottom"*; scope *"Do not apply this
  retrospectively to published recipes / Please apply to drafts / Please apply
  to new ingests"*. Cocktails only. The order is `TOP_LEVEL_KEYS_IN_ORDER`,
  derived from `_layouts/cocktail.html` by a test; where her own list and the
  layout differed, the layout won on her word. The ingest's finishing pass
  runs `tidy_drafts.py --only order`.
- **2026-10-08 — dilution water is dropped before any mood rule counts
  anything.** Helen: *"Dilution water just isn't something I care about ...
  let's say dilution water should be excluded from every mood derivation
  rule."* Difford's writes dilution as a measured line.
- **2026-10-08 — `sharp` is not widened, and egg white neither counts against
  it nor is exempt from its cap of five.** `sharp` is on 45% of drinks and the
  suite refuses 50%. Four widenings were measured (ignoring a 5 ml spoon,
  counting two spirits of one family once, a cap of six, any liqueur as the
  sweetener) and each tagged about as many drinks Helen had not as corrections
  it retired. She called the spoon variant's four drinks *"not sharp, which I'm
  saying in a spiritual sense."*
- **2026-10-08 — `tiki` takes one marker in a drink of eight ingredients or
  more; `sugar craving` gets a rule that only adds.** Helen: *"Three dots, and
  fog are absolutely tiki, so if we need to change the rules to rule them in
  then so be it."* `sugar craving`: two tiki markers in 90 ml or more, Jungle
  Bird excluded by name. Both stay on `moods_by_hand`, so a rule can only add
  to what she typed. Steel Drum, one marker in six ingredients, stays outside
  the rule: *"I could go either way, so if the data says No then so be it."* A
  floor of six tags eleven drinks she did not.
- **2026-10-08 — no rule is added for a hand mood if it would tag drinks Helen
  must then untag.** Helen: *"Don't add things I'll need to remove -- easier
  for me to notice the gaps."* Every one- and two-feature rule was searched
  per hand mood and scored on held-out drinks against shuffled tags (held-out
  / shuffled): on fire 1.00/.49, clear .71/.44, signature .70/.47, tiki
  .65/.50, sugar craving .60/.54, nightcap .49/.41, sunny terrace .44/.49,
  aperitivo .41/.47, festive .31/.42, brunch .27/.43, easy peasy .26/.40, so
  wrong it's right .19/.42. At or below shuffled, no rule will be found.
  `clear` has signal and still gets none: its best rule has six false alarms.
- **2026-10-08 — a hand mood Helen NAMES for a drink in the ingest chat is
  written at ingest.** Otherwise `mood: []`. Never offered, inferred or
  derived by the ingesting session. The instructions had said never, and she
  had asked for every one a web session typed.
- **2026-10-08 — ginger beer is not `warming`; `ice ice baby` needs no
  widening.** It already covers every swizzle, crushed-ice and blended drink
  bar Mastiha Mojito, which Helen excluded herself. Per-drink corrections the
  same day: All Jacked Up is a strong brown drink (*"feel strong and brown"*)
  and Three Dots and a Dash is faff (*"yes yes"*).

- **2026-10-19 — a step may express INTO the build.** Asked whether the express ban should give way for Metexa's "express the oils of a coin-size grapefruit zest over the base of the stirring glass", Helen chose *"Allow it inside a build"*. The garnish twist is still the layout's; a step expressing into the stirring glass, mixing glass, shaker or tin is allowed.
- **2026-10-19 — a shake means with ice, and a cook's caveat is dropped.** Helen chose *"A shake means with ice"* (IBA's "Shake well") and *"Drop 'omit if wet ice'"*.
- **2026-10-19 — ingredients are in build order even where the source lists them otherwise.** Helen: *"Build order"*, on IBA's Old Fashioned and Mint Julep.

### §9.3.1 The ingredient vocabulary

- **2026-08-21, #441 — a list `generic` means OR, and only OR.** Bali Hai
  takes `aguardiente` OR `kirschwasser`: either makes the drink. A bottle with
  two properties (Gosling's: moderately aged AND blackstrap) is a generic plus
  a `character`. Write a list only when both bottles can be named and a reason
  given; "I don't know which" stays `QQ`. Helen, 2026-08-17, of lines such as
  "Demerara or dark Muscovado sugar": *"What I have there is fine. I can do
  what I want on the spot."*
- **2026-08-23, #441 — `character` lives on the recipe line, never on a
  bottle.** It is why THIS drink wants this bottle, so restating it per recipe
  is each recipe stating its own reasoning; Helen overturned the issue's
  premise that it must not be repeated. Restated 2026-09-14: *"We don't name
  characters on bottles. We name characters on recipe lines, maybe suggesting
  a bottle, then bottle choice is up to future Helen. Because I think for the
  most part having a character is only in a context."* Never copy a bottle's
  botanicals onto a line. Strength and glass volume are bottle-invariant and
  do not get this treatment.
- **2026-08-23, #457 — `suggestion` is bottle names only; the reason goes in
  that ingredient's `note`.** Six suggestions had drifted into sentences. A
  note may stay verbatim and private in meaning, as the Caipirinha's cachaça
  ranking did: *"Future Helen will know exactly what I mean"*.
- **2026-08-24, #314 — blackstrap is only ever a `character`, never a
  generic.** Helen: *"Blackstrap is only ever given as a character for another
  rum, like this: Moderately aged (character: blackstrap)."*
- **2026-08-26 — rum and whisky characters are closed lists with a guard; a
  gin's character is free text.** Helen's call: a rum's character comes from a
  handful of production traits, a gin's is whatever went in the still.
  Declaring a `<family>_characters` list in `ingredients.yml` is what switches
  the guard on. `sherry` and `Spanish-style` had been passing as generics.
- **2026-08-26, #459 — the vocabulary serves Helen choosing a drink, not an
  encyclopaedia.** Helen: *"everything we do is focused on the user (i.e.
  Helen), and making sure the user gets the drink she wants. Being an
  encyclopaedia of drinks sounds like busywork and it's not for me."* Apply it
  to any feature that describes a bottle in the abstract.
- **2026-08-27 — a Demerara rum is an appellation: 100% DDL, Guyana.** From
  *Minimalist Tiki*. So the Pusser's Blue Label and Gunpowder are `moderately
  aged rum` despite tasting Demerara, and Planteray O.F.T.D. is its own
  category. Smith & Cross is `moderately aged Jamaican rum` (57% made it look
  unaged); Wood's at 57% is AT proof, not overproof. Skipper's needed Helen,
  not inference.
- **2026-08-27 — an absent suggestion is a real answer.** Helen, on Long
  Island Iced Tea: *"I'd rather not specify any rum at all for LIIT because
  neither I nor the drink care"*; on Milliners Punch: *"never name Spicers"*.
  What is cheap and what needs using up are facts about the shelf on the day,
  not about the drink.
- **2026-08-27, #561 — every generic reads as an ingredient: natural word
  order, the spirit word on the end.** Helen: *"they're almost always going to
  be on their own line, so eminently skippable if wanted, and I don't want to
  do the cognitive work of mapping to Minimalist Tiki every time I read
  them."* The agricoles take their French names. The three brand-generics
  became `pineapple rum`, `blended overproof rum` and `coconut rum`. Whisky and
  whiskey are each spelled correctly; `bonded rye` is a real style (*"bonded
  rye is a different thing, like overproof demerara rum"*).
- **2026-08-27 — peat is a `character`, not a style.** Helen: *"so single malt
  whisky, character: peated ???"* `peated Scotch` is retired for `single malt
  scotch whisky` with `character: [peated]`: peat is orthogonal to
  single-malt-versus-blended, as blackstrap is to a rum's age.
- **2026-08-30, #542 — a generic on `hers_to_apply` is Helen's to apply; never
  type a drink into one from the source's words.** Helen: *"I remain annoyed
  about this. I have discussed this at least twice… If I have to deal with this
  again I will simply delete those recipes."* `caramel-forward Jamaican rum`
  earned it. Removing a line is her grant, in the commit of the drink that
  earns the style; `test_no_drink_uses_a_generic_that_is_helens_to_apply`.
- **2026-08-30, #568 — there is no `aromatised wine` generic; each kind is its
  own.** Helen: *"I would never write 'aromatised wine' as a cocktail
  ingredient or generic, because it suggests some equivalence between the
  types where none or very little exists"*. Sweet, dry and blanc vermouth,
  `quinquina` and `americano`. `Punt e Mes` is not one of them: Helen demoted
  it to a bottle under `sweet vermouth` on 2026-09-05, so The Ridgwell reads
  "sweet vermouth (Punt e Mes)" beside "sweet vermouth (Martini Rosso)". A
  brand is its own generic only where no category name would help her choose.
- **2026-08-30 — `Chartreuse Verte` / `Chartreuse Jaune`, never green /
  yellow; `sloe gin` is its own generic; `pastis` is retired.** Sloe gin was
  split out of `gin liqueur`, the fault `flavoured` was retired for; no guard
  could catch it and Helen found it on a card. `pastis` went when its one
  drink became the Martinique Swizzle.
- **2026-08-31 — when nothing generalises a bottle, the bottle IS the generic
  (Becherovka).** Helen: *"'Herbal liqueur (Becherovka)' would be misleading.
  This will come up over and over and I don't know what to do about it."* Her
  *"cinnamon- or ginger-forward"* is a note. The same shape as Campari and the
  other amari: declared once, as a generic, with no bottle entry.
- **2026-08-31 — `apple brandy` is named after the FRUIT; `cucumber` and
  `kaffir lime leaves` are bare generics.** Laird's Bonded is an applejack, not
  a calvados, so one generic covers both. Helen on the two bare ones: *"will
  need to go in the dictionary naked."* "Pernod" names two bottles, an
  absinthe and a pastis: write the product. Helen pours the absinthe.
- **2026-09-04, #594 — a syrup's generic is its sugar plus a ratio, only where
  the difference is real.** Helen: *"Most 'sugar syrup' means 'cane sugar
  syrup', possibly all. Sometimes I say 'demerara sugar syrup' when I mean
  that. Let's standardise this please."* Refined 2026-09-06 (#593): not a
  cane/demerara/turbinado by 1:1/2:1 cross-product. `cane sugar syrup` at
  both ratios, `demerara sugar syrup 2:1`, `turbinado sugar syrup 2:1`.
  Turbinado is in the `sweet` mood list only: *"Turbinado is just a sugar...
  It's just a flat ingredient."*
- **2026-09-04 — honey water carries its ratio, and both ratios are
  generics.** Helen: *"Bee's Knees needs to say honey water 2:1… I really do
  need that generic here"*. Refined 2026-09-07: the drinks on the bare generic
  went to `2:1` except Chartreuse Daiquiri, whose own note says equal parts and
  stays `1:1`. `honey water 3:1` joined 2026-10-07.
- **2026-09-06, #781 — overproof comes first in a rum's generic and card
  name.** #780 and #781 contradicted each other and #781 won. So `overproof
  Jamaican rum, unaged`, `overproof Demerara rum, lightly aged` and `blended
  overproof rum`. The card names drop the age (`overproof Jamaican rum`); the
  generic keeps `unaged`, because Wray & Nephew is unaged and Smith & Cross is
  not. A card name may always be shorter than its generic, so a ruling about
  the card never has to cost the data a distinction.
- **2026-09-08, #848 — a shopping shelf is not a family: `shelf_of` is its own
  map.** Helen: *"for cocktail shopping list, list items in shelf order then
  volume"*, in her order; she added `fortified` and `fresh produce` the same
  day. An amaro and a herbal liqueur are two families on one shelf; champagne
  sits under `tops`. `dried apricots` is a dry good, `lemon zest` is fresh
  produce (you buy a lemon). Refined 2026-09-21, `flavourings` renamed
  `larder`: *"I think the general term 'larder ingredients' as a cook includes
  fridge to me. Then cream, milk and eggs can go in there."*
- **2026-09-10, #707 — four juices print "fresh"; pineapple juice always
  carries "Don't use fresh."** Helen: *"they should all display like 'fresh
  lime juice'"* and *"pineapple juice should always carry the note 'Don't use
  fresh.'"* `always_fresh` is lime, lemon, orange and grapefruit; ruby
  grapefruit is left out because she named four and widening is hers.
  `standing_notes` is keyed by generic and sits under a drink's own note,
  never in place of it. Cards do not say "fresh".
- **2026-09-14, #984 — a generic that needs coining, or a base spirit whose
  style the source does not state, is Helen's to decide.** Leave it `QQ` with
  the reasoning in the file. That sitting did add, with her, `white wine`,
  `maraschino cherry` and `orange-forward bitters` (Angostura orange bitters
  is a different product from the `Angostura` under `aromatic bitters`, and a
  bottle name is unique across `bottles.yml`). `peach schnapps` followed the
  same day (#1013): *"Add 'peach schnapps' as a generic let's say ABV 18%"*.
- **2026-09-14, #796 — the generic is `coconut-flower arrack`; `Ceylon Arrack`
  is the bottle.** Helen: *"the name of the bottle is 'Ceylon Arrack', and the
  generic is 'coconut flower-arrack'"*; she picked the lowercase hyphenated
  spelling from the options. The category had been named after where it comes
  from, not what it is made of. `Ceylon arrack` is retired as a generic
  (`retired_cane_and_palm_spirits`); `Batavia arrack` is unchanged.
- **2026-09-14 — `cherry brandy` and `cherry liqueur` are two generics.**
  Helen: *"Cherry Heering is a cherry brandy, Briottet Cerise is a cherry
  liqueur."* A new generic, not a default bottle. The Singapore Sling, which
  named both for one line, takes `[cherry brandy, cherry liqueur]`. The cherry
  eau de vie is a third thing, under `brandy_styles`, and never stands in for
  the liqueur: *"Don't use plain kirsch"*.
- **2026-09-14, #752 — `to taste` is an amount.** For the Ti' Punch's lime and
  syrup. Helen: *"typically served as rhum in a glass with lime and sugar on
  the side so people can roll their own"*. Her step "Serve the lime and the
  syrup on the side…" met the rule that a "Serve" step is presentation, and
  she chose moving it to `to_serve` over rewording it.
- **2026-09-14 — a punch's `serve: ice: block` may describe how it is MADE,
  not how it is served; no punch is precedent for another.** Helen: *"Some
  punches are indeed made over a large ice block in the punch bowl, but then
  served plain in cups/glasses, or over crushed ice. So 'serve' in some of
  those above is misapplied. I'll need to pick through one by one."* She has
  since ruled Pic-a-de-Crop Punch IS served over a block (2026-10-04, #838).
- **2026-09-15, #1079 — a muddled slice names its fruit: `orange slice`, not
  `citrus slice`.** Helen: *"'citrus slice' shouldn't be the generic because
  citrus fruits aren't interchangeable."* A lemon or lime slice gets its own
  generic the day a drink uses one.
- **2026-09-17 — Gunmetal Blue takes `peach brandy`, not `crème de pêche`, and
  no suggestion.** Helen: *"The Briottet instead of peach brandy will be
  because that's what I had at the time, so let's remove the suggestion, just
  leaving the generic."* A 20% sweetened infusion had been standing in for a
  35% distillate. It cost the drink its `fruity` mood, correctly.
- **2026-10-04, #838 — crème de cacao is two generics, brown and white.**
  Helen: *"Brown and white CdC should each be a generic, then no notes are
  needed. Drop the Giffard suggestion (I hate it!)"* The unqualified word is
  no longer a generic; a source that does not say which is a question for
  her. Briottet Crème de Cacao Blanc is the white's bottle. The brown has
  none and carries the white's category figures: *"I don't own a brown CdC,
  so fine to leave as-is."*
- **2026-10-04, #1108 — each clairin is its own generic; plain `clairin` is
  retired.** Helen: *"I've changed my mind: Each type of clairin should be a
  generic because they are not interchangeable. Clairin Vaval, Clairin
  Casimir, Clairin Communal, Clairin Sajous (three of those aren't used yet
  but will be)."* Clairin Communal is therefore not a bottle; its 43% and
  price sit under `generics:`. Do not guess figures for the other three: the
  single-village clairins run into the fifties and move batch to batch.
- **2026-10-07 — a source's bottle does not go in `suggestion`; it goes in
  that ingredient's note as "Originally X."** Helen: *"Move all the
  suggestions to notes, and I can add my own suggestions where I have them or
  drop if not. For notes, just write 'Originally X'."* 148 Difford's bottles
  had failed to resolve, most of them its sponsors' and not her shelf. A
  suggestion stands only where she names one.
- **2026-10-07 — `_data/cocktails/source_wordings.yml` maps a source's wording
  to one of Helen's generics, and holds her rulings only.** Helen: *"Agree to
  the mapping."* `resolve_pours.py` reads it. A call she made about one drink
  is not a rule and stays out (`cherry (brandy) liqueur` was asked *"one by
  one"*). Aperitivo Luxardo maps to `Aperol` and Strucchi Red Bitter to
  `Campari`; wider generics for those two families were declined. Refined
  2026-10-08: a wording that is one of her generics plus words that say
  nothing new may be listed without being asked one at a time, approved by her
  as a list: *"Yes please, let's get a list in and avoid the work."*
- **2026-10-07 — twenty generics and three units from the Difford's batch, each
  Helen's yes.** `cranberry juice drink` (*"needs to be a new generic"*),
  `lemon vodka`, `pink grapefruit juice`, `blood orange juice`, `daiquiri` /
  `grapefruit` / `peach bitters`, `coconut water`, `birch water`, `natural
  yoghurt`, `ruby port`, `pineapple syrup`, `hazelnut syrup`, `honey water
  3:1`, `black raspberry liqueur`, `crème de myrtille`, `kümmel`, `sake`,
  `tsipouro`, `lime zest with flesh`. Units: `wedge`, `cm log`, `thick coin`.
  Most prices and strengths are placeholders at `confidence: low`. Declined: a
  pressed-cane syrup generic (*"cane syrup 2:1 is good enough for me"*).
- **2026-10-07 — Cocchi Americano is an `americano`; there is no
  `fortified_characters` list.** Helen went from `quinquina` with `character:
  "americano"`, to *"I think Cocchi Americano is an americano"*, to *"I agree
  with you, thanks, your way"*: a character names a flavour trait, and "either
  works" is a list generic, `["americano", "quinquina"]`, suggesting `Cocchi
  Americano` (Picotin, North Sea Oil). A characters list was declared and
  removed the same day.
- **2026-10-07 — lowercase when the word has become the thing.** Helen:
  *"Something like when the word has become the thing we use lowercase?"* So
  maraschino cherry, parmesan, muscovado, `demerara sugar` (lowercased in five
  live food recipes on her grant). A capital stays where the word still names
  the place or a brand: `Demerara rum`, Dijon mustard, `Luxardo maraschino
  cherry`.
- **2026-08-17 — Curaçao keeps its capital, and Grand Marnier is a generic of
  its own.** Helen's calls, with no words recorded. Curaçao is the deliberate
  exception to lowercasing a commodity: it is not an appellation turned common
  noun and still reads as the island's name, the test of 2026-10-07 applied
  early. Grand Marnier stays apart from the orange Curaçaos because its cognac
  base changes a drink.
- **2026-08-26 — the gin styles are Helen's own list, and `speciality` always
  carries a `character`.** Helen: *"London Dry, Old Tom, Plymouth, Navy
  strength, Genever and speciality, where speciality should always carry a
  character field."* `speciality` replaced the retired `flavoured`;
  `test_speciality_gin_declares_a_character` holds it. `gin liqueur` is filed
  in `gin_styles` so that excluding gin rolls it up, and is not one (*"not a
  gin though"*).
- **2026-10-12 — a gin style carries the word `gin`: `Old Tom gin`, `Plymouth
  gin`.** Helen: *"'Old Tom' should be declared as 'Old Tom gin'... For ease
  of skimming a recipe."* and *"Please update to 'Plymouth gin' too."* The
  same rule made `New Western dry` into `New Western dry gin` (#1186). The
  bare names are in `retired_gin_styles`, so a drink that writes one fails
  with the reason.
- **2026-09-04 — `aguardiente` and `kirschwasser` are generics, not bottles.**
  Asked about the two things Bali Hai suggested, Helen: *"both are generics."*
  The drink carries them as a list `generic`, either would do, with no
  suggestion. `full-strength clear fruit brandy`, invented for that one drink,
  is retired. Massenez Kirsch Vieux is a bottle under `eau de vie`.
- **2026-09-05 — `Créole Shrubb` is its own generic, filed under `liqueurs`:
  where no category name would help Helen choose, the bottle is the
  category.** Helen: it *"should appear on lists with gin and cognac -- it's
  not replaceable, and calling it a type of rhum agricole isn't at all
  useful"*. It sits with the liqueurs and not under rum (decided on her
  question, 2026-08-17), so "no rum tonight" does not drop a drink whose only
  rum is a little of it (Ginger Snap, Accoutrement). The same shape as Strega
  and Bénédictine.
- **2026-09-05, #314 — `navy`, `overproof navy` and `black` are not rum
  categories and are retired for good.** Helen: *"there is no such thing as
  navy rum or overproof navy rum"*, and *"there's no such thing as black rum,
  even though it will often be requested by other people's recipes."*
  `retired_rum_styles` in `ingredients.yml` gives each its reason, so a
  source's "navy rum" fails with an explanation and is typed by what the
  bottle is: strength belongs to the bottle, and a black rum is an aged
  Jamaican or a `blackstrap` character.
- **2026-10-15, #1379 — two coconut generics by base: `coconut rum-based
  liqueur` and `coconut rhum-based liqueur`, both filed under `liqueurs`.**
  Helen, asked whether Mahina, Koko Kanu and Malibu were one row: *"two
  generics, coconut rum-based liqueur and coconut rhum-based liqueur."* They
  replace `coconut rum` (Malibu, now with Koko Kanu, 37.5%, £22) and `coconut
  rhum` (Clément Mahina), which #606 had made official two days before; both
  old names are in `retired_rum_names`. The rum-based one is priced and
  strengthed from Malibu, her meaning of the category. Both count as tiki
  markers; only the rum-based one is a pudding flavour (Helen: *"Tiki
  only"*). Neither is in the rum family, but `rum (all)` finds the rum-based
  one through `family_reach`: Helen, *"When a user filters for rum, let's
  show them Malibu. Fine for it not to be hidden by excluding rum."* So Blue
  Hawaiian answers to `rum (all)` and survives "no rum tonight". Mahina and
  Créole Shrubb are reached too, and so is every future rum or rhum liqueur:
  Helen, *"please add something to our data transformation instructions to
  mean this is automatically considered for future rum and rhum liqueurs
  rather than me having to remember."* A test ties `family_reach` to the rum
  page's liqueur shelf, and the ingest instructions say so.
- **2026-10-15, #1379 — `pineapple rum` is `pineapple-infused rum`.** Helen
  chose the rename knowing two live drinks go back to her for proofreading.
  The card still reads "pineapple rum".
- **2026-09-20, #1068 #1069 — `ginger beer` is its own generic, in no
  category.** Helen: *"Ginger Beer is a new ingredient, no category, so that's
  the name."* It is under `other` in `ingredients.yml` and shelves with the
  tops. It is not a ginger syrup or a ginger liqueur.
- **2026-09-25, #1186 — a declared generic or glass that no drink uses stays:
  the vocabulary is a spec, not residue.** Asked style by style about genever,
  navy strength gin, gin liqueur, bonded rye, blended scotch whisky, Irish
  whiskey, Japanese whisky, armagnac, grappa, americano, cider, margarita
  bitters, whole egg and the flat `honey water`, Helen: *"Please keep all the
  others."* The glass phrases for `brandy glass` and `martini glass` were kept
  the same day. Garnishes went the other way (§9.12): an unused one is
  deleted.
- **Undated, #314 — `cachaça` is its own generic, and Batavia arrack's family
  is `rum`.** Helen: *"cachaca is its own generic"*. Both sit in
  `cane_and_palm_spirits`, not in `rum_styles`: cachaça is in the rum family
  for exclusion and on no shelf of the rum page. Batavia arrack is cane and
  rice and counts as rum, her call. `coconut-flower arrack` shares only the
  name and is in no family (#796).
- **Undated — `sugars` deliberately mixes form with type: `sugar cube` is a
  generic beside `white sugar`.** Helen: *"if I don't have a sugar cube I
  won't make a Classic Champagne Cocktail"*, and *"if having this many turns
  out to feel mad once I'm using the site, then we can revisit."* A cube can
  also be brown, and that is accepted. `golden caster sugar` is its own
  generic too (her call, 2026-08-26), not folded into `raw sugar`: the
  Bellinis had been typed `molasses sugar`, which is nearly muscovado.
- **2026-10-11 — a made ingredient is named plainly, and how to make it or
  what stands in for it is a note.** On `Coco mix (3:1 Coco Lopez to coconut
  milk)`, Helen: *"Coco mix should be the ingredient, with a note giving the
  substitution. New rule, everywhere."* So the generic is `Coco mix`, and its
  ingredient note is always *"3:1 Coco Lopez to coconut milk."*, no comma —
  the line is written out beside the generic in `ingredients.yml` so the next
  drink copies it. It is sweetened cream of coconut loosened with coconut
  milk, so it is not `coconut cream`, the unsweetened tin, and `costs.yml`
  prices it from its two parts (#1108). A sugar syrup's ratio is not a recipe
  in brackets and stays in its name.

- **2026-10-19 — a list of source wordings, approved as a list.** Helen approved four groups, so `source_wordings.yml` gained twelve (Rye Whiskey, Sweet Red Vermouth, Plain Water, Vodka Citron, Becherovka liqueur, Créole Shrubb liqueur, Apple Schnapps liqueur, Pimento dram/Allspice liqueur, Clear apple juice (not cloudy), Orange flower/blossom water, and more); eleven were there already. IBA's ratio-less "Sugar Syrup" is `cane sugar syrup 1:1`. A bare IBA "Gin" is NOT mapped: *"Not all IBA gin is London Dry, so QQ every time please unless you happen to know which it is!"*
- **2026-10-19 — four new generics: raspberry syrup, orange flower water, vanilla extract, powdered sugar.** Each Helen's yes. "Bourbon or Rye Whiskey" is the OR list `[bourbon, rye]`; navy rum with no bottle stays `QQ`.
- **2026-10-23 — a batch syrup a drink makes is a note; the ingredient list is one glass.** On the Pear and Rosemary Bellini, whose list was the whole batch: *"put the syrup recipe in a note, then add 25 ml syrup to the ingredient line"*, the note titled with the syrup's name (*"Pear, apricot and rosemary syrup"*) and saying how many portions it makes, and the ingredient carrying *"See below for the recipe."* A homemade syrup is declared with no strength or price: *"Declare, but it's homemade, so no ABV or price"* (lemongrass syrup): `non_alcoholic` in `abv.yml`, 0 in `costs.yml`.

### §9.3.2 The bottle dictionary

- **2026-08-30 — every bottle a drink names is declared in `bottles.yml` and
  classified; never derive a bottle's category from the ingredient beside
  it.** Helen: *"are we now assuming every named bottle should be in it, and
  classified? That feels right to me."* Then, stopping a session that had
  declared 43 by inference: *"keep only what the collection already spells
  out; hand me back the rest."* A bottle she NAMES is hers to add and always
  was. Planteray is canonical and Plantation an alias (#529).
- **2026-08-30, #534 — a suggested bottle may sit outside the generic's
  category, and then the ingredient must carry a `note`; `QQ` counts.** Helen:
  *"a recipe might call for cherry brandy, and I suggest Cherry Heering OR
  Briottet cerise even though that's a cherry liqueur not a brandy, leaving it
  to future Helen to choose what kind of drink I want at the time."* Why the
  note: *"Substituting it isn't straightforward and will vary by drink. Please
  add notes for me on recipe pages when I've substituted in a surprising
  way."* And: *"be permissive with the test"*. A list generic crosses only if
  the bottle matches none of its options.
- **2026-09-02, #585 — a bare brand is not a bottle and is never added as an
  alias.** `Planteray` names four products and `Bulleit` a bourbon and a rye;
  Helen chose `Planteray 3 Stars` and `Bulleit Bourbon`. The bare `JM` alias
  was deleted for the same reason (#702, 2026-09-06): two JM bottles are
  stocked, in different categories.
- **2026-09-02, #585 — Jack Daniels is a bourbon here.** Offered "Tennessee
  whiskey, a different legal category", Helen: *"It meets all the legal
  requirements for being called that, and their own decision to apply a
  further qualifier on top is... vain!"*
- **2026-09-04 — a house is not a bottle: declare each product by name and
  retype the drink to it.** Helen went through every unresolved suggestion
  line by line: *"I never want to have these conversations more than once"*.
  A house is an alias only where it can mean one thing here (Luxardo for
  Luxardo Maraschino, Bob's for Bob's Peppermint Bitters). A spirit type
  beside its own generic is not a suggestion. A syrup's suggestion may name
  what it is made from (*"Acacia is a bit special"*).
  `unresolved_suggestions` has been `{}` since, and stays as a key.
- **2026-09-04 — `flavoured vodka` is retired for `vanilla vodka` and
  `pineapple vodka`; `lavender bitters` is `lavender-forward bitters`.**
  Helen: *"members aren't substitutable"*. `bonded rye` / `rye` and `dry
  orange Curaçao` / `orange Curaçao` stay distinct pairs.
- **2026-09-05 — a bottle Helen no longer reaches for moves to
  `not_reached_for` with her reason; it is not deleted.** Helen: *"the three
  Lows I skipped, let's remove them from the collection please"*. The
  dictionary means what she would POUR, not what qualifies. Do not re-add one
  because its category looks thin.
- **2026-09-06, #701 — a `suggestion` is the bottle's full declared name, not
  an alias.** A suggestion prints verbatim, so El Presidente read "(ED3 or
  Havana 3)". Helen ruled against shorthand and against a separate display
  field. Helen, 2026-09-04, on Fish House Punch: *"'ED3' isn't a bottle"*.
  `test_every_suggestion_is_the_declared_bottle_name`; aliases stay, for
  search and for reading a source.
- **2026-09-06 — `La Favorite`, no `u`, is a standing correction.** Helen:
  *"Favorite is correct, my mistyping, please always correct."* Each bottle
  key is spelled the French way and keeps `La Favourite` as an alias, so a
  suggestion typed the British way still resolves. Every bottle rename takes
  that shape.
- **2026-09-07, #591 — an agricole's origin goes on the BOTTLE, as
  `origin:`.** Helen chose it over origin-qualified generics (`Martinique
  agricole blanc`) and over a field on the ingredient. The accepted cost: a
  recipe cannot REQUIRE an origin; Martinique Swizzle is Martinican because of
  its `suggestion` list. Barbancourt is correctly `rhum agricole vieux`.
  Origin stays inside the generic where it changes the CATEGORY (Demerara,
  Jamaican); those styles are not being unpicked. `origin` is for cane
  spirits only (Helen, 2026-10-13: *"Origin isn't a thing beyond cane
  spirits."*): no tequila or pisco takes one. `bottle_origins` is a closed
  vocabulary, so a typo cannot mint an origin in silence, and adding a value
  is Helen's (`test_bottle_origin_is_declared`); every bottle on the Cane
  juice shelf declares one (`test_cane_juice_bottles_declare_an_origin`).
- **2026-09-09 — Pusser's 151 is an `overproof Demerara rum, lightly aged`.**
  Helen: *"Minimalist Tiki thinks Pusser's 151 is a Demerara rum, so so do I.
  It's 100% Guyanese."* And: *"I made a mistake, my overproof Demerara rum is
  Pusser's 151."* The 100% DDL rule is intact; this bottle passes it. The
  other two Pusser's stay `moderately aged rum`. El Dorado 151 is on
  `not_reached_for`: she never owned one (replaces the reading of 2026-08-29
  and 2026-09-06 that the 151 was a blend).
- **2026-09-14, #745 — Pierre Ferrand Ambré and Pierre Ferrand 1840 are
  different bottles.** Helen: *"I was wrong above. Pierre Ferrand Ambré and
  Pierre Ferrand 1840 are different bottles, but both £53 and both 40 % ABV."*
  Each is declared in `bottles.yml` with its own spellings (replaces her
  ruling of 2026-09-05, which made the 1840 an alias of the Ambré).
- **2026-09-14, #984 — Giffard is not suggested: not for crème de menthe, not
  for crème de cacao.** Helen: *"My mistake, mint bottle for Monte Carlo is
  Briottet Creme de Menthe. Please update, and delete Giffard from our
  dictionary (I really don't like it)."* Refused again 2026-10-04 (#838).
  `Giffard Crème de Mûre` stays declared: it is the only bottle behind `crème
  de mûre`, and deleting it zeroed the cost and strength of every drink using
  that generic unnamed.
- **2026-08-27, #314 — Rum Fire is its own bottle beside Wray & Nephew, and
  Blackwell and Myers are the markers for `caramel-forward Jamaican rum`.**
  Helen, on Rum Fire: *"choice of that or W&N is mood by mood."* So it is not
  an alias, although both are `overproof Jamaican rum, unaged`. On the other
  style: *"Blackwell is Jamaican, caramel forward"*. Myers is declared
  although no drink names it. The style itself is on `hers_to_apply`: the
  bottles mark it, and no session types a drink into it.
- **2026-08-31 — `Sazerac` is a rye Helen owns, declared although no drink
  suggests it.** Helen: *"the product name is Sazerac, though, I promise, and
  I have it and use it elsewhere."* It is a bottle under `rye` as well as the
  name of a drink. Do not delete it as an orphan or rename it.
- **2026-09-04 — the bottles are `Appleton Estate 8 Year Reserve`, `Havana
  Club 7 year old` and `3 year old`, and `Rittenhouse 100`; every Briottet is
  declared; the tiki bitters are Bittermens'.** Helen: *"Appleton Estate 8
  Year Reserve is correct, I was wrong in Cobra's Fang."* "Appleton Estate
  Reserve" is not an alias, because an unnumbered Reserve exists.
  *"Rittenhouse and Rittenhouse 100 are different, but 100 is the same as
  bottled-in-bond"*, so the bare name is not its alias either. Of the six
  Briottet products written bare: *"I own all of those."* *"the maker is
  Bittermens, 100%."*, with no leading apostrophe on Elemakule (#879,
  2026-09-10: *"delete those two apostrophes"*).
- **2026-09-05 — a bottle's name takes its diacritics and the plain spelling
  is an alias: Patrón, Añejo, Pierre Ferrand Ambré.** Helen: *"It's Patron
  with the diacritic, and Rooster Rojo Bianco."* (2026-09-02), then *"Rooster
  Rojo Tequila Anejo, Rooster Rojo Tequila Reposado, Patron Reposado, Patron
  Anejo -- all need diacritics."* The cognac is `Pierre Ferrand Ambré`,
  without the category word: *"I shouldn't have given 'Cognac' in the name,
  just Pierre Ferrand Ambré, sorry!"* The plain forms stay as aliases, so a
  suggestion typed without accents still resolves.
- **2026-09-07 — the El Dorados are `El Dorado N Year Old`, for 3, 5, 8 and
  12; `El Dorado 151` is unchanged.** Asked whether renaming the 3 alone was
  intended, Helen: *"all four"*. 15 and 21 take the same form if they appear.
  `Planteray 5 Year Old Barbados` was fixed the same day. The older spellings
  ("El Dorado 3 year old rum", `ED3`) are aliases (replaces her pattern of
  2026-09-04, *"always like 'El Dorado 3 year old rum'"*).
- **2026-09-09 — the label's name is canonical and Helen's own wording is an
  alias: `Dolin Rouge`, `Briottet Crème de Cerise`, `Ciroc Pineapple Flavoured
  Vodka`.** She writes "Dolin red", and *"Briotte Cérise turns this into a
  Haribo cherry"*; both resolve. The pineapple vodka is declared by its
  product name, in her words *"Ciroc Pineapple Flavoured Vodka"*, not by the
  house. Dolin Dry, Blanc and Rouge are three bottles, not spellings of one.
- **2026-09-14, #1012 #796 — `Ardbeg An Oa`, `Gabriel Boudier Liqueur de
  Gingembre` and `Batavia Arrack van Oosten` are the bottles; the old
  spellings are aliases.** Helen: *"Ardbeg XO should be 'Ardbeg An Oa', ABV
  46.6 %."*; *"'Gabriel Boudier Liqueur de Gingembre' is 18 % -- and please
  update the name string."*; *"the bottle I own is 'Batavia Arrack van Oosten'
  (note misspelling on current site)"*. Declared the same day: Clément Rhum
  Agricole Canne Bleue (*"Yes, add it."*), Briottet Liqueur de Sapin, and La
  Tomato Liqueur, *"the only tomato liqueur I have (shocker)"*.
- **2026-09-25, #1108 — Away Colour takes Cruzan Single Barrel with
  `character: blackstrap`; Fanny Chu's Piña Colada takes Pedro Mandinga with
  `character: raspadura`.** Helen: *"generic is moderately aged rum,
  suggestion is Cruzan Single Barrel, character is blackstrap."* and
  *"generic: lightly aged and filtered, suggestion Pedro Mandinga Panama
  silver rum, character raspadura."* `raspadura` joined `rum_characters` for
  it: the raw-cane-sugar (panela) note of a Panamanian silver rum. Her
  spelling of the bottle is its key.
- **2026-10-07 — Barbancourt 5 Star is a `rhum agricole vieux`, like the 3
  Star, and is the suggestion on Port au Prince (Smuggler's Cove).** Asked
  both, Helen: *"Yes, and bottle as suggestion."* It is cane juice, whatever
  the label calls it. Neither Barbancourt is the category's default (§9.3.5):
  both are 43% and an unbottled `rhum agricole vieux` is 45%.
- **Undated, #582 — no drink writes `plantation`; it is always corrected to
  Planteray.** Helen: *"'plantation' is not permitted as a kind of rum and
  should always be corrected to 'planteray'."* The rule governs what is
  WRITTEN: a drink's filename, title, `generic`, `suggestion` and `note`
  (`test_no_drink_writes_plantation`). The old spellings stay in `bottles.yml`
  as aliases, which govern what can be READ, so a source that still says
  Plantation resolves at ingest. Do not delete the aliases to "finish" the
  rename, and do not leave the old word in a draft because it resolves.

### §9.3.3 The drinks index's search

- **2026-08-29, #579 — fuzzy to find, exact-or-family to exclude; candidates
  rank in four bands.** Helen: *"It should be prefix matching of first word,
  prefix matching of any word, then prefix matching of any word in the bottle
  name, then substring."* The substring band is for names a chip SHOWS: a
  hidden generic or bottle alias earns its chip a place only on a word-start
  match. Helen: *"'el' returns both 'aged rum' and 'jamaican rum', which is
  counterintuitive."* Food's asymmetry, adopted because `gin` was hiding
  drinks with ginger and `apple juice` matched pineapple. The search is a pure
  module and `cocktail-index.js` is wiring. `and` is deliberately not treated
  as a connector word (Wray and Nephew).
- **2026-08-29 — the whisky family chip is labelled `whisk(e)y`.** Helen:
  *"even though it's clunky, to avoid ever having to split or claim they
  combine."*
- **2026-08-30, #580 — bare `water` is never on a card and never in the
  search.** Helen: *"never write 'water' on a cocktail card and never return
  it in a search"*. `not_on_cards` in `ingredients.yml`. The BARE thing only:
  `honey water` and `soda water` stay. Widened 2026-09-06 (#640) to the bare
  sugars, salt and zest: *"don't include things like sugar, water. lemon zest
  in the ingredient list that appears on cocktail cards."*
- **2026-08-31, #603 — a chip found through a name it does not show carries
  that name.** Helen typed `mu`, `sa`, `wr` and got `clear blended rum`,
  `cachaça`, `Jamaican overproof rum`; she picked from four candidates on a
  dev page. The bracket uses whichever spelling carried the query, since the
  canonical one may share no letter with what was typed (`ED3`, El Dorado 3).
  Where the generic that matched contains every word of the card name, the
  candidate shows the generic alone, with no bracket: it *"should be returned
  without its display name given that name is a bit of a hack. I don't know if
  this is a one-off or a principle."*
- **2026-08-31 — a multi-word query matches a hidden name from its start, and
  each category gets one chip wearing the card's name.** Helen: *"I do want to
  be able to type 'el d' and see el dorado."* A bottle is a way IN to its
  category's chip, not a chip of its own. So a bottle is never offered beside
  its own category; Helen, 2026-08-29: *"the first chip being 'falernum (all)'
  would at least stop me worrying that the two sets were disjoint."* Food's
  umbrella suppression (#51) is ported.
- **2026-08-29, #529 — one bottle written several ways is one bottle in the
  search, and no chip has an "X or Y" shape.** Helen: *"'wray and nephew' and
  'wray & nephew' should both collapse onto the latter"*; *"I don't want any
  returned search chips to be an X or Y shape"*. Every alias in `bottles.yml`
  resolves to the bottle's one declared name before the pool is built, and a
  `suggestion` string offering alternatives is never offered as a chip. The
  shopping list collapses spellings through the same aliases.
- **2026-10-15, #1376 — "rhum agricole (all)" is a search-only button over
  both agricoles, and typing "rhum" lists the clairins straight after the
  agricole chips.** Helen: *"I'd like cocktail ingredient search to collapse
  'rhum' so I don't have to specify which agricole I want to use -- I want to
  browse"*, then *"also return the clairin, just after chips with 'rhum
  agricole' directly"* and *"the chip should read 'rhum agricole (all)'"*.
  `search.umbrellas` in `ingredients.yml`. The cards and the blanc and vieux
  chips are unchanged, "rhum" still offers `rum (all)` too, and the button
  selects no clairin.
- **2026-08-29 — a family is reached by its other spellings, and the button
  always carries the family's canonical name.** Helen: *"'whiskey (all)'
  should return all whisky and bourbon and rye, and the same for 'whisky'."*
  `family_aliases` in `ingredients.yml`: `whiskey` and `scotch` reach whisky,
  `tequila` agave, `rhum` and `ron` rum. Added 2026-08-30: `bitter` and
  `amari` reach `amaro`, because `bitter` is not a mood and a family is not a
  browse axis (*"do we need families -- thinking of bitter and herbal? Why?
  They're not browsable or searchable."*). Families only: an ingredient with
  two names is a `card_names` question.
- **2026-09-02, #653 — HAS TO HAVE and LEAVE OUT mark the same chips: a prefix
  match of any word is marked in both pools, a substring match in neither.**
  Helen: *"the chip underline rule should be the same between has to have and
  leave out, namely that prefix matching of any word gets the pink whereas
  substring matching does not."* What the mark looks like has changed since
  (a stroke; hot magenta in HAS TO HAVE, heavier base grey in LEAVE OUT,
  #1219); which chips carry it has not. `hasWordMatch` in `cocktail-search.js`
  decides it once for both pools, and
  `test_the_word_match_mark_survives_in_both_pickers` fails if a section
  cancels the mark.

### §9.3.4 Units of alcohol — #297, built 2026-09-06

- **2026-09-06, #297 — a drink page states units of alcohol, not ABV.** Helen:
  *"I want the number of units in a drink, not the ABV of the drink, i.e. water
  etc don't matter."* So dilution, ice and mixers never enter the sum. An amount
  in dashes or drops is not counted either: asked, she chose the same rule as
  costing. The line has been on the live site since 2026-09-14 (#1001, §9.13);
  its first, local-only form is gone. The count is per serving and never the
  batch's: *"Give units per serving, not total, so scaler setting doesn't
  matter"*. The plugin emits no data attribute for the scaler to multiply.
- **2026-09-06, #297 — a strength belongs to a bottle and lives in `abv.yml`,
  never on a category, in `bottles.yml` or in `costs.yml`.** Helen, moving
  Smith & Cross: *"it is aged, so the unaged overproof style was never right.
  57% is what made it look like one — and strength is not what that category
  names."* Pusser's Gunpowder (54.5%) and Gosling's (40%) share a category. A
  price decays and a strength does not, so the two are not one file. The file
  layout is a session's call, resting on her point about categories.
- **2026-09-06, #713 #753 — the units line says "Roughly" on every drink, and
  its words are Helen's.** Her sentence: *"Roughly X units of alcohol in a
  serving"*. "Roughly" is on every drink, exact or not, because how accurately
  a drink is made is not something the data knows. A punch keeps "in each of N
  servings": asked about "a glass" to match the cost line, she left the
  mismatch alone. With the additions of 2026-09-17 (#1121) and 2026-10-04
  (#1291), `_layouts/cocktail.html` prints "Roughly X units of alcohol in a
  serving of Y ml (undiluted)." Do not polish it or put it into house voice.
- **2026-09-06, #713 — `units.exact` is kept although nothing reads it.** Asked
  whether to retire it along with the "About" it used to gate, Helen kept it: a
  true, computed fact whose likely readers are a reference page or an honesty
  marker. It means every alcoholic ingredient named its bottle; a vague 0% one
  (soda water) does not spoil it. Do not delete it because grep finds no
  reader; the footer comment in `_layouts/cocktail.html` says why it stays.
- **2026-09-14, #1012 — bitters are never counted in the units.** Helen:
  *"Don't include bitters in our ABV calculations."* It is a rule about
  bitters, not a side-effect of dashes going uncounted, so bitters measured in
  millilitres are excluded too. The `low`-confidence bitters rows in `abv.yml`
  carry no `qq:`, because a question about a number nothing reads is not worth
  her time.
- **2026-09-14, #1016 — an ingredient with no bottle named takes the MODE
  strength of the bottles declared for its category.** Helen: *"if a bottle
  isn't stated for a cocktail recipe, assume the MODE ABV of bottles we've
  declared. This will be more meaningful than mean or median."* The mean
  survives only as the plugin's keep-the-page-building fallback, and a test
  fails the build the moment it would be read.
- **2026-09-14, #1016 — a category with no mode gets a default bottle that
  Helen names.** Seven of the fifteen multi-bottle categories had every bottle
  at a different strength. Offered the highest, the mean or the median, she
  chose instead to name a default for each (`default_bottles` in `costs.yml`):
  Woodford's Reserve, Vieux Pontarlier, Sagatiba, Lustau, Gabriel Boudier
  Liqueur de Gingembre, Luxardo, and a split for cherry. She was told first
  that a default also sets the price where no bottle is named.
- **2026-09-06 — `abv.yml` is filled from knowledge, with a web check only for
  the doubtful rows.** Helen: *"knowledge first, web only for the doubtful
  ones"*. Each row's `confidence` records which it was. A strength does not
  decay, so the file is not re-checked on a schedule the way prices are.
- **2026-09-14, #1012 — a strength Helen states is her figure, not a guess: it
  goes in `abv.yml` at `confidence: high`.** She corrects them as they scroll
  past: *"Damoiseau Rhum Agricole Blanc Pure Cane is 50%, just saw 40% scroll
  past and wanted to correct in case I mistyped."*; *"Apple schnapps: 20% (the
  40% is the brandies)."*; *"Clement Rhum Agricole Canne Bleue is 50 %.
  Clement Rhum Agricole Blanc is 40%"*. Do not "correct" one of these from a
  web search. A row she only waved through keeps a lower confidence (white
  wine, *"12.5% is fine"*, is `medium`).

### §9.3.5 What a drink costs — #547, built 2026-09-05/06

- **2026-09-05, #547 — a drink's cost shows on the locally built site only, as
  an incidental line in the footer.** Helen: *"I only want to show price on the
  locally built site, and only as an incidental — just somewhere on the recipe
  page."* `site.show_costs` is declared in `_config_local.yml` and never in
  `_config.yml`, so a production build prints no cost line at all. Locally it
  reads "Roughly £X–£Y a glass in ingredients."
- **2026-09-05, #547 — `default_bottles` are pricing inputs and are never named
  on a recipe.** Helen: *"Don't name these on the recipes, but you can note
  them as inputs to the default prices."* Since 2026-09-14 (#1016) the same map
  also supplies a strength where a category has no mode; it is still a pricing
  fact and never a suggestion the page prints.
- **2026-09-05, #547 — dashes, garnishes and ice are not costed; a volume, a
  priced count or a priced weight is.** Helen: *"None of these come into the
  estimated cost. I'm catering for family, not running a bar."* Refined
  2026-09-06 (#748): whole fruit and weighed solids that ARE the drink are
  priced, through `fruit_prices` (per piece) and `weight_prices` (per kilo),
  built 2026-09-24. A count or weight with no row is still a flourish (the
  sugar cube). Asked on 2026-10-11 (#1371) about three things a session had
  guessed: *"Sugar should be £0 here. It just doesn't matter at this scale!"*
  (its `weight_prices` rows are zero); and the estimated prices, *"rough is
  more than fine. The expensive part of cocktails is absolutely not the
  fruit..."* A homemade syrup is priced 0 (§9.3.1).
- **2026-09-05, #547 — a `(top)` is costed as a declared range, `top_up_ml` in
  `costs.yml`.** Helen: *"We can calculate top volumes, well, slightly, can't
  we — I'd like that to be captured actually so it can be added into the
  shopping list feature."* A range was her choice over a single figure.
  Costing and the shopping list stay on the declared range although the units
  and the volume size a top from its glass since 2026-10-04 (#1179): a price is
  already a range. That is deliberate, not a bug.
- **2026-09-06, #547 — the price is per glass and does not change with the
  scaler.** Helen: *"When I scale, the price per glass you calculate needs to
  divide by the scaled number."* The opposite had shipped: n glasses cost n
  times the money, which is the same price per glass.
- **2026-09-07, #818 — the shopping list's bottle choice is made per drink, not
  once for the whole list.** Asked which, given a generic with several declared
  bottles, Helen: *"per drink"*. So two drinks that both use a reposado may
  choose differently, the buttons sit on the drink's own line, and choosing
  collapses that line's price range to the chosen bottle. The range stands
  until a choice is made. The list names its drinks one per line, at the top:
  *"list shopping list cocktail names at the top one per line"*.
- **2026-09-26, #1215 — the price per glass prints two decimal places.** Helen:
  *"price per glass should have two decimal places."* Liquid cannot pad a
  number, so `_plugins/cocktail_costs.rb` writes `min_text` / `max_text` and
  the page prints those. The numeric `min` / `max` stay on the data attributes,
  because the scripts read them as numbers and a string would break them.
- **Undated — an unqualified `London dry gin` is priced and given its strength
  from Tanqueray alone; `blanco tequila` defaults to two bottles, and that is
  a real range.** Helen: *"London dry gin let's say the default is
  tanqueray"*; *"Rooster when it doesn't matter loads, Patron Silver if it
  really does"*. `default_bottles` in `costs.yml`. The other gins stay
  declared; they are not what the bare category costs. The tequila pair is
  spanned for cost and averaged for strength, not narrowed to one.
- **2026-09-06 — what a glass of each drink costs shows beside the shortlist's
  shopping list, on local builds only, as a quiet suffix on the drink's line;
  never on the cards.** Helen: *"the only other place I care about this number
  is when I'm comparing drinks in a shortlist."* Asked how it should look:
  *"quietly again"*. So it is not a column of its own. `#drink-costs` in
  `cocktails/index.html`, behind `site.show_costs`.
- **2026-09-07, #818 — choosing a bottle on the shopping list rewrites the
  list line as well as the price, and the choice is not remembered across
  loads.** Helen asked for *"shopping list cocktail names at the top one per
  line, with radio buttons to choose from where there is a choice of declared
  bottles for high-volume ingredients"*. Offered a choice that sticks, she
  took *"price and the list line"*: *"choosing is how you decide what to buy,
  so the list should say what you decided."* In memory only, on purpose.
- **2026-09-25, #749 — the build's cost line always says how long ago the
  prices were checked, and a test fails once that date is two years old.**
  Helen: *"Build log line always with elapsed time, and also a test that
  shouts after two years."* `checked:` in `costs.yml`; `checked_age` in
  `_plugins/cocktail_costs.rb`;
  `test_the_price_check_date_is_less_than_two_years_old`. The fix for a red
  test is re-reading the prices, never moving the date alone.
- **2026-09-04 — a line on the drinks shopping list gives the generic first
  with the bottle after it in brackets, on the same line, the bottle in wicked
  woowoo.** Helen: *"show generic first, with bottle on the same line in
  brackets, like the recipes."* The same shape as the drink page's ingredient
  line (#544). `.shopping-list-bottle` takes the colour because the bottle is
  the thing chosen.
- **2026-09-06 — the drinks shopping list shows each drink's cost, quietly, on
  a local build only.** Helen: *"please add the cost, quietly again"*.
  `.shopping-list-cost` is the muted grey, and `costSuffix()` in
  `assets/js/cocktail-index.js` returns nothing unless `site.show_costs` put
  the costs block on the page, which only `_config_local.yml` does.
- **2026-09-05, #547 — a generic that names one product is priced as a point
  and carries its own strength, with no bottle entry.** Helen: *"Campari is
  just Campari, as is chartreuse. They have prices."* So Campari and both
  Chartreuses have a row under `generics:` in `costs.yml`, min equal to max,
  and one in `abv.yml`. Do not declare a bottle called Campari under a generic
  called Campari to make the lookup uniform.
- **2026-09-05, #547 — orgeat is priced from Monin, mezcal from Del Maguey
  Vida, cognac across Courvoisier and Pierre Ferrand Ambré, and `lightly aged
  and filtered rum` across Havana Club 3 and El Dorado 3.** Helen: *"orgeat is
  always Monin"*; *"Mezcal is always Del Maguey Vida unless I discover I need
  to downgrade!!!!"*; *"Cognac is Pierre Ferrand Ambre when it matters more,
  Hine/Corvoisier/Hennessey when less (not that they're really less expensive,
  just harsher)."*; *"Lightly aged and filtered rum will be one of Havana 3 or
  El Dorado 3 99% of the time."* `default_bottles` in `costs.yml`. The 1840 is
  not a cognac input. One bottle gives a point price; a pair is a real range.
- **2026-10-15, #1379 — `moderately aged rum` is priced from Planteray 5 and
  Havana 7, and Helen chooses its bottle by the drink.** Helen: *"For a
  standard sociable drink with lots of layers, I'd use Planteray 5 or Havana 7
  with normal guests! For a more opinionated drink, i.e. one without fruit
  juice in it (other than lime or lemon), or a more opinionated guest, I'd go
  Chairman's, Ango 5 or Ango 7. Ango XO is unlikely to get poured unless it's
  a two-ingredient drink and I like you! If the character is blackstrap, then
  Gosling's is the default. Pusser's blue or gunpowder would only go in where
  a bite-y character (a technical term) is actively noticable."* The first
  pair are the `default_bottles`; the rest is how a `suggestion` gets chosen,
  hers to apply. "Ango XO" is taken to be the Angostura 1824.
- **2026-09-05 — champagne is a point price, £20 for 75 cl.** Helen: *"Let's
  say champage is GBP 20 -- I buy crates of Heidsieck Blue Top on sale at
  Christmas!!!!!"* Heidsieck Blue Top is the reason for the figure, named in
  the row's `basis`, and is not declared as a bottle.
- **2026-09-14, #1014 — cream is £4.50 a litre and is non-alcoholic.** Helen:
  *"Use £4.50/litre for both sites."* and *"Cream is non-alcoholic."* A point
  price under `generics:` in `costs.yml` and a line in `non_alcoholic` in
  `abv.yml`, so it never asks for a strength.
- **2026-10-07 — an unbottled `rhum agricole vieux` is 45%, and `lemon vodka`
  is 40% from Absolut Citron.** Asked the agricole's strength, Helen:
  *"45%."* So both 45% bottles, La Favorite L'Authentique Ambré and Rhum JM
  Ambré, are its `default_bottles`, and the 43% Barbancourts stay declared
  without being inputs. *"Lemon vodka: 40% abv, default is Absolut Citron at
  £25 for 70 cl."*
- **2026-10-10, #1351 — a category may be priced and given its strength from a
  named default bottle that is not declared in `bottles.yml`.** Helen's
  figures, each a point: *"Black raspberry liqueur can default to Chambord,
  16.5%, £25 for 70 cl"*; crème de myrtille from Briottet, kümmel from
  Mentzendorff, sake from Akashi-Tai, ruby port from Taylor's Fine, Japanese
  whisky from Suntory Toki, bonded rye from *"Rittenhouse 50%, £36 for 70
  cl"*. The bottle is named in the row's `basis` only. Swedish flaggpunsch has
  had this shape since 2026-09-14 (#747): *"Carlshamns Flaggpunsch: £21
  (default)"*. Declaring any of them as a bottle is her call.

### §9.3.6 How much liquid is in a drink — #1121, built 2026-09-17

- **2026-09-17, #1121 — the units line also states the serving's volume.**
  Helen: *"an addition LOWER DOWN, to the existing units line, so it reads:
  'Roughly X units of alcohol in a serving of Y ml'"*. A punch extends its own
  tail: "in each of 8 servings of 160 ml". The figure is per serving and must
  never move with the scaler; nothing the scaler writes reaches
  `.cocktail-units`, and a rendered-page test holds that. The volume is
  computed once, at build time, in `_plugins/cocktail_units.rb`.
- **2026-09-17, #1121 — a topped drink's volume takes the midpoint of
  `top_up_ml`.** Helen: *"Midpoint please, I'll cope on the spot."* She was
  shown "say nothing" and "print the range" and chose against both: at the
  counter a soft figure beats a blank. One expression feeds the unit count and
  the volume, so they cannot disagree. Narrowed 2026-10-04 (#1179): the
  midpoint is now what a top falls back to where its glass cannot size it. No
  topped drink may declare `serves:` (`test_no_topped_drink_is_also_a_punch`),
  because `serve_ml` would share one top between the glasses.
- **2026-10-23, #1121 — a drink whose uncounted ingredients ARE the drink
  states no volume, and a counted sugar is never one of them.** Helen, asked
  whether the Old Fashioned (45 ml whiskey, one sugar cube) should stay silent
  or print: *"Print ~45 ml"*. A sugar dissolves into what it sweetens, so a
  figure without it is rough, not wrong. The Caipirinha (half a lime) stays
  silent: it fills its glass, so the cachaça alone undercounts what matters.
  The test is `CocktailCosts::SUBSTANTIAL` minus any generic in
  `ingredients.yml`'s `sugars`; `cost.complete` still counts sugars as before.
- **2026-09-17, #1121 — the note under the scaler carries the bitters caveat
  and no totals.** Helen: *"I like the line. But the cost and units line below
  has come back and I don't want it to be there."* #713's batch note had
  printed the batch's cost and units above ×1. Those went; "Don't scale bitters
  linearly — add to taste." stays, since she asked for it separately, and it
  shows only on a drink with an amount in dashes or drops.
- **2026-10-02, #1257 — nothing under the scaler prints a volume; the
  "Approximately X ml" line is removed.** The issue is its title and nothing
  more: *"remove 'approximately X ml' line from under cocktail recipe
  scaler."* She had asked for the line on 2026-09-17 and liked it; no reason
  was given for removing it and none was asked.
  `test_no_drink_page_prints_a_batch_volume` fails if it returns. The figure
  survives unprinted as `data-total-ml` on `.cocktail-scale-controls`, which
  `scripts/glass_fit_report.py` and the volume tests read.
- **2026-10-04, #1179 #1116 — a `(top)` is sized from its glass.** Helen: *"Can
  we add to that data, and find typical capacities? Then use those to estimate
  top amounts? It really doesn't need to be exact, let's say +- 50 ml would be
  fine."* The first listed glass at its surveyed median, to the wash line, less
  the serving ice and the watered build, rounded to 5 ml (`fitted_top_ml`). It
  reads the same `fit_rules` the fit report reads. The midpoint of 2026-09-17
  still decides a drink with no `serve.ice`, no surveyed glass, a punch bowl,
  `serves:` above 1, two tops, or a build that leaves no room.
- **2026-10-04, #1199 — the build has one amount parser,
  `HelenTriages::Amount` in `_plugins/amount.rb`.** A session's call, not
  Helen's ruling. The costs, units and card generators each keep only their own
  verdict on what it returns. `tests/fixtures/amounts.json` holds every
  distinct published amount with what the Ruby and the browser parser each
  read. The two grammars differ on purpose (the browser folds `dashes`, reads a
  bare `15` as a count and `half` as 0.5); the assertion is only that where
  both read a number it is the same number.
- **2026-10-04, #1291 — the units line says "(undiluted)", after the
  millilitres.** Helen: *"I just want to make it clear that 120 ml of drink
  won't end up in a 120-ml glass."* She first proposed "in an (undiluted)
  serving of 120 ml" and corrected herself: *"What do you think about 'a
  serving of 120 ml (undiluted)'"*. The article stays right and the word sits
  against the figure it qualifies. A drink that states no volume says "in a
  serving." with no bracket.
- **2026-10-04, #1293 — above ×1 an amount in dashes or drops is struck through
  and starred, and the note under the scaler carries the matching star.**
  Helen: *"make it more obvious that bitters shouldn't be scaled by updating
  the ingredient line as well as showing the note under the scaler... e.g.
  strikethrough text for the amount, then a \*, and a \* before"* the note. The
  amount still scales, so the reader can see which way to err. One trigger for
  both, so the star and the sentence it points at appear together or not at
  all.
- **2026-10-04, #1294 — one spirit used twice in a drink is "the first" and
  "the second"; never "pour" as a noun in anything Helen reads.** Offered "the
  first pour of", she refused the word: *'"pour" is a highly American word and
  I don't want to use it because it doesn't mean much to me.'* Hers: *'"Float
  the first blended overproof rum" and "fill ... with the second"? That implies
  the two could be different, which I well might do actually, so it's
  honest.'* Two `shapes:` lines in `methods.yml`. A figure in a method step was
  not an option: the scaler does not rewrite steps.
- **2026-09-04 — a drink's millilitre total counts millilitres only: drops,
  dashes and pinches are left out.** Helen: *"Ignore drops and dashes and
  pinches in target ml."* She said it of the target-volume box, which is gone
  (#721); the rule outlived it as `measures.non_volumetric` in
  `ingredients.yml`, read by `_plugins/cocktail_units.rb` for the serving
  volume and by `scale.js` for its total.

- **2026-10-19 — "few" is 2.** Helen chose 2 for IBA's "few dashes" and "few drops".
- **2026-10-19 — a dry sugar measured by the spoon keeps the spoon.** Helen: *"Dry spoons stay spoons"*, and, told the cocktail suite converts every tsp: *"Dry sugar keeps its tsp"*. A spoon of anything liquid is still ml.
- **2026-10-19 — a 7 oz scoop of ice is 200 ml**, in the method step; and a measured top-up keeps its measure (*"Keep the measure"*). Units `sprigs`, `wedges` and `disc` are declared.

### §9.4 / §9.4.1 / §9.5 Decided, canon, settled apparatus

- **2026-08-16 — a drink's ingredients are additive, never a choose-one.**
  Helen was asked directly, because guessing wrong would have shaped the whole
  model. The category and the bottle are both stored (`generic` and
  `suggestion`), and `to_serve` is presentation, not an ingredient.
- **2026-08-17 — the site is canon; deviation happens in the kitchen.** Helen:
  *"With iPad in hand, I'd rather take the site as canon, then happily break
  rules from there."* Offered and declined: modelling adjustable sugar as a
  range, a tolerance or an "approximate" flag. A page that hedges is no longer
  a reference.
- **2026-09-05, #722 — `meta.made_before` is a boolean that gates nothing, and
  an unmade drink may publish.** Helen: *"there's no prose except the tagline
  which I will always write from scratch, so no copyright or author respect
  issue. It will be much easier for me to browse drinks I want to try from the
  live site than a local build."* It is first in `meta:`. Do not add a "has
  been made" or "names a rung" publish gate: both existed and were retired by
  this ruling, the first never having been asked for.
- **2026-09-05, #722 — an unmade drink's `ship` says `who knows`; `QQ` is not
  a ship value.** Helen: *"I think that's clearer than QQ or leaving it unset,
  because it's a positive presence"*. A published drink's ship is never empty
  (Helen, 2026-08-30: *"every cocktail we publish must have the ship field
  filled in"*), and `who knows` counts as filled in. The page shows it as
  `???` (`ship_off_scale` in `taxonomy.yml`), which is not a rating. The
  word must not be a rung of `ship_scale`: *"unambiguously not on the same
  rating scale. (It's also funny)."* Helen, 2026-10-11: *"The ??? mark means
  'I've never made this so I simply don't know'."*
- **2026-10-18, #1413 — a drink Helen has made and liked but never rated says
  `ship: "IOU"`, shown as `IOU` on the card and the drink page; `who knows` is
  only ever an unmade drink.** Her issue: *"I propose 'IOU' for drinks I've
  made and liked but didn't rate."* Like `who knows`, it is off the scale, not
  a rung. `who knows` had covered two facts, never made and made-but-unrated
  (75 drinks, six of them live); the split made them agree with `made_before`
  by test (`test_ship_agrees_with_made_before`). All 75 became IOU at once,
  and on the six live ones Helen granted the mark without a proofread flip:
  *"if this mark is the only change then the proofread flag doesn't need to be
  flipped, so no recipe goes dark. Explicit grant this time only."*
  `_dev/no-verdict.html` is the worklist of IOUs.
- **2026-10-20 — the ship scale is four rungs: meh, sure, yes, yes².** Asked
  what each word meant, Helen first kept `meh` and `sure` apart (*"those are
  different"*), then merged the bottom rung into `meh`: *"let's combine meh
  and nah into meh. That is enough resolution, and perfectly communicative."*
  `not really` (shown "hmm" on cards) is gone; its drinks say `meh`, and on
  the one live drink (Champs-Élysées) she granted the change without a flip.
  The top rung is shown as `yes²` on the card and the drink page alike
  (`ship_words`); stored values are unchanged, so filters and URLs still
  match. A key on the page is parked in #1102.

### §9.7 / §9.8

- **2026-09-26, #1212 — a blank "To serve" draws no section.** Helen: *"don't
  show 'to serve' section if it's blank."* `to_serve: ""` is how an ingest
  leaves a drink with nothing to say. An empty string and an empty array are
  both truthy in Liquid, so the value is `strip`ped and tested against `""`,
  and every list-gated section tests `.size > 0`
  (`test_list_sections_are_conditioned_on_size_not_truthiness`).

### §9.9 The goodness filter, and the vocabulary that outlived it

No live ruling. The goodness-only filter of 2026-08-23 was replaced by the
designed index on 2026-08-26 (§9.13) and `_goodness.scss` is deleted.

### §9.10 / §9.10.1 The ingredient line and the card names

- **2026-08-27, #501 — a card names the category, always, even where the recipe
  names a real bottle.** Helen ruled it with `El Dorado 12 year old rum` →
  `Demerara rum` in front of her. Her card names say the spirit word out loud
  (`lightly aged rum`), so some are LONGER than their generic: never assert
  that each is shorter; the guard is aggregate
  (`test_showing_categories_still_shortens_the_index`). Two generics sharing a
  card name must be declared in `card_names_may_collide` (both Jamaicans are
  `Jamaican rum`).
- **2026-08-27, #501 — a drink using two kinds of the same rum prints the card
  name twice.** Helen: *"where a recipe wants more than one kind of the same
  rum we obviously should write the display name twice."* Do not de-duplicate
  a card's ingredient line.
- **2026-08-29, #544 — the drink page's ingredient line is the generic with the
  bottle in brackets.** Helen's example: `London dry gin (Beefeater)`.
  `character` gets a labelled line of its own, never a bare parenthetical
  (#441). The card falls back to the generic when there is no card name.
- **2026-08-29, #544 #556 — card names cover every category, not only rum, and
  are descriptive rather than brand shorthand.** Helen, on Ceylon arrack: *"is
  that a rum? Doesn't matter, the category list should eventually contain
  everything"*. A reader who met `o.f.t.d.` among `gin` and `cognac` learned
  nothing. Cards are lowercased in CSS, not in the data or markup (#543 #553),
  so real proper nouns keep their capitals where they are stored. Helen,
  2026-08-27: *"I am unhappy about capital letters on cards. It's just very
  untidy."*
- **2026-09-04 — the ingredients list shows the full name; only the card shows
  the short one.** Helen: *"Let's display the full name in the ingredients list
  please, just the short name on the card."* `card_names` is read by the card
  and nowhere on the drink page.
- **2026-09-06, #567 — a card's ingredients are ordered by tier, then by
  volume, with a per-drink override.** Tiers: base spirits, lower-proof,
  citrus and juice, syrups, everything else, bitters (floats came with #754);
  largest volume first inside a tier; the recipe's order breaks ties. Helen
  chose *volume, with a per-drink override* (`card_order`) over "most
  typifying the drink", which would have been truer and needed a judgement on
  every drink. The sort is `_plugins/cocktail_card_ingredients.rb`. The tiers
  exist because of #691: *"e.g. seeing 'mint' first in a mastiha mojito takes
  a minute! We already do this on the food site."* The override's first user
  is Port Authority (2026-09-07), whose blackberries lead: *"blackberries,
  cognac, port, cassis, lemon juice, bitters -- that's informative to a reader
  looking at cards."*
- **2026-09-06, #691 — sugar, water, salt and zest stay off the cards.** Helen:
  *"don't include things like sugar, water. lemon zest in the ingredient list
  that appears on cocktail cards"*. The list is `not_on_cards` in
  `ingredients.yml`.
- **2026-09-17, #1141 — an optional ingredient reads "(optional)" after its
  name.** `optional:` is a bare boolean, absent meaning required. It is not
  food's `incidental`: that hides a line, this shows and marks it. The earlier
  objection, that this line's brackets already mean "the bottle", was about a
  collision that had not happened: one published optional ingredient, naming
  no bottle. If the two ever meet ("syrup (Monin) (optional)"), ask Helen then.
- **2026-10-02, #1226 — the character line is a labelled fact: `CHARACTER:` in
  Plex Mono, the words upright in full-strength text, and no hue.** Helen:
  *"Let's allow it to look different from a note"*; *"Option 1 I like. I like
  conserving the plex-as-fact design idea."* Declined, in her words: absinthe
  *"wrong language"*, lagoon *"already a page subheading level"*, the mood
  corals *"mixing messages"*, chips *"might be too much, even for me"*, beside
  the name *"the lines are already long"*, an icon *"would disrupt the
  hierarchy"*. A heading rule under the label was built and dropped: at that
  size it reads as a strikethrough.
- **2026-10-04, #1132 — a unit the ingredient's name already says is not
  printed twice.** Helen's whole report: *"1 cube sugar cube"*. The data is
  right and no recipe changes; the line prints differently. The unit moves into
  the name ("12 cubes" + "sugar cube" → "12" + "sugar cubes"), so the plural is
  the amount's, and `each` is not printed. Tried and dropped: trimming the name
  ("1 cube" + "sugar") and a bare number beside an unchanged name ("2 sugar
  cube" at ×2). Stated in Liquid and in JS (`data-unit-quiet`, `quietUnit`)
  because the page is built before a script runs.
- **2026-08-27 — where a list `generic` joins badly on a card, the fix is an
  explicit row in `card_name_joins`, never a rule.** Helen: *"not perfect, but
  we can try. I expect we'll need an explicit mapping of cases like this."*
  The default is the two card names joined by " or ". The map is keyed on that
  default join and is empty today; `test_every_card_name_join_is_reachable`
  refuses a key no drink produces. Collapsing a shared word is a judgement
  about two specific names.
- **2026-08-29 — the agricoles' card names keep the spirit word: `rhum
  agricole blanc`, `rhum agricole vieux`.** Helen: *"'agricole' and 'rhum
  agricole' should both be 'rhum agricole'."* Bare `agricole blanc` asks the
  reader to know that agricole is a rum. The same rule made `single malt
  scotch whisky` read `single malt whisky` and not `single malt` (#844,
  2026-09-08): a card names one ingredient at a time, and an adjective with
  nothing after it names none.
- **2026-09-07 — on a card a `rinse` sorts last with the floats, and a
  `muddle` reorders nothing.** Helen's rulings, with no words recorded. A
  rinse, a float and a shell are each added outside the main build, so they
  close the card's ingredient line. Grouping muddled ingredients first was
  built, looked at and dropped; `muddle` stays in `ingredient_as` because it
  is a true fact the drink page may want.

### §9.10a `serve`

- **2026-09-05 — there is no `chill` field; a chilled glass is assumed.**
  Helen: *"I think it's implied that glasses should be chilled (except hot
  drinks obviously). I am the user after all."* The field existed for about an
  hour. Its `frozen` and `rinsed` values were each already a method step.
- **2026-09-05 — the strain step names the glass and the ice, composed at
  render time from `glass` and `serve.ice`, never stored.** Helen: *"I'd like
  to name the glass too where it appears"*. The ice had no field, so "strain"
  had been written seventeen ways; a stored strain step may not mention ice
  (`test_serve_ice_is_not_restated_in_the_method`). The rim rides before the
  ice: *"given that you can't sugar a rim once the glass is full, let's add
  that line earlier."* A drink with no `serve.ice` is a question for Helen,
  not a default.
- **2026-10-11 — the rim is said on the strain step, as a garnish would be,
  never as a step of its own; `serve.rim` must hold the word "rim".** Offered a
  rim step opening the method, Helen: *"I don't rim a glass straight away
  because the rim can melt in the liquid, and because i usually stand my
  glasses with chilled water and an ice cube. The rim should be mentioned in
  the strain step in the same way a garnish is, so, yes, strain into a martini
  glass with a salt half-rim or ...sugar rim."* So `"salt rim"`, never
  `"salt"`.
- **2026-09-05 — a garnish step closes the method.** Helen: *"garnish is
  important, and it's easy to miss at the top of the page."* It is a method
  step, not a serving note: "To serve" is what happens to a finished drink.
  A garnish holds only garnishes; an ingredient, a rim or a method step
  written there moves to its own field.
- **2026-09-28, #1214 — the glass generator names the glass in the first
  build-in-the-glass step, on DRAFTS ONLY.** Helen: *"Let's write the glass
  generator now please — I've come up against this a few times now, notably in
  the Sazerac on the live site."* and *"this will require re-proofreading
  everything on the live site, so for now please let's just apply it to
  drafts."* `methods.yml` `in_the_glass` maps the step to its sentence. Only
  the first such step is composed, or a drink that half-fills and then adds
  says "highball" twice.
- **2026-09-28 — a strain step repeats the glass only when the clause riding on
  it is new.** Helen ruled two cases differently. Milliners Punch, half-fill
  then *"Strain into a hurricane glass filled with crushed ice."*: *"Milliners
  method is good now."* Death & Co Sazerac, rinse then *"Strain into an old
  fashioned glass."*: *"names the glass twice."* The second adds nothing,
  because its `serve.ice` is `none`. So the rule is not "never repeat the
  glass".
- **2026-09-28 — how full the ice is goes in `serve.fill`, not in a new
  `serve.ice` value.** Helen's Milliners step wanted *"Strain into a hurricane
  glass half-filled with crushed ice."* A session's design, not her ruling: a
  sixth `ice` value would silently move three mood rules that test for
  `crushed`. `fill` replaces the word "filled" in the composed clause, so it
  is allowed only with `cubed` or `crushed`
  (`test_a_fill_has_something_to_fill`).
- **2026-09-05 — a rim is said again in the method or under "To serve", never
  only on the glass line.** Helen: *"things like half-rim should be repeated
  in the method or serve or wherever, because it's easily missed just on the
  glass mark in the metadata."* `_layouts/cocktail.html` puts `serve.rim` into
  the composed strain step; a rimmed drink with no strain step prints it under
  "To serve" instead (`rim_shown`). Do not drop the fallback as duplication.

- **2026-10-19 — `serve.ice: cracked` is its own value**, not crushed: Helen chose *"Cracked is its own value"*. Whether it counts toward a mood is still hers.
- **2026-10-19 — a drink blended with ice is `blended`**, whatever its pour step says. Helen: *"blended"*.
- **2026-10-19 — a British flag, and the straw through the ice cone.** Helen, on Navy Grog: *"I want the ice cone, and the straw running through it, then a British flag!"* `british flag` is a to_serve decoration; the ice cone is a garnish, and a method step pushes the straw through it.

### §9.11 / §9.11.1 / §9.14 / §9.15 / §9.16 Glass icons

- **2026-08-17 — the drink page draws the FIRST listed glass that has
  artwork.** `glass` is an ordered list of acceptable glasses; Daisy de
  Santiago is *"anything, but preferably a Collins"*, and the Mai Tai a double
  old fashioned *"more often"* and a tiki mug *"sometimes"*. A drink whose
  first choice has no drawing gets its second rather than nothing. A glass
  with no entry, or one naming a missing file, renders nothing, so a missing
  key never becomes a broken image.
- **2026-08-26 — on the drink page the glass is compressed and drawn as a
  fraction of the title block.** Helen: *"let the height of the glass be more
  similar to the title block, if the glass is tall. For shorter glasses, try
  half height."* and *"try drawing the glass as large as the whole title block,
  including the title line itself. I think the stability of the top edge will
  help the switch to MAKE IT mode feel less jarring."* The ratio maps onto
  0.32–1.0 (`--glass-fill`), keeping the order. `tallest_mm` is counted live,
  never hardcoded.
- **2026-08-26, #347 — `old fashioned` is the canonical glass name and `rocks`
  fails a test.** Helen: *"I decided to go with old fashioned rather than
  rocks as the canonical name, so recipes that still have rocks are fine to
  break a test."* `rocks` remains only as an alias onto the one drawing.
  `todo` and `long` became `highball`, and every swizzle is a highball.
- **2026-10-22, #299 — a stemmed glass's stem is one of three lengths: short
  15%, medium 36% or long 57% of the drawing's height.** Shown every stemmed
  glass at one height beside a candidate with only its stem changed, Helen:
  *"I like 'every stemmed glass, same height', except for Hurricane, Sling and
  Pilsner"*, and told it only alters stem length, *"If the 15 are literally
  just altering the stem length, then thanks for doing those!"* The targets
  are the medians of the three groups the measured stems fell into. Applied by
  script to eleven sources, bowl and foot untouched; brandy was already on
  target and is unchanged. Hurricane, sling and pilsner stay as drawn (she may
  redraw them), as do the punch bowl (a pedestal, not a stem) and every glass
  without a stem. This is her grant under #355 for these stems and nothing
  else. (Replaces "proportions stay as drawn", 2026-08-26.)
- **2026-08-27, #491 — `any` is not a glass.** Helen: *"when someone tells me
  to use an old fashioned glass I always automatically assume I can use any
  glass I like, so there's no need to have 'any' as a glass type."*
- **2026-08-31, #355 — a session does not redraw Helen's glasses.** Three
  fill-only glasses were traced into line art and she stopped it: *"you redrew
  these three new ones, right? They're not right."* She redrew them herself
  (2026-09-05). She also closed the open stroke ends by hand, ruled
  `old-fashioned-double`'s two largest gaps correct as drawn, and wanted no
  guard on stroke gaps.
- **2026-08-31, #601 — a card's glass has its own curve: ratio × 0.5 + 0.5,
  plus headroom.** Settled at `/dev/card-glasses/`. Helen caught that the two
  had been offered as rivals: *"Is headroom plus compression an option?"* The
  short end sits at 0.5 because on a card it must read against neighbours, not
  a title block; the headroom is `$card-glass-scale`. `display_scale` stays as
  a mechanism with an empty map. The dev page is kept as the instrument.
- **2026-09-05, #650 #738 — glass lines are stroke 2 on the drink page and 1 on
  a card, and the height curve is the same on black.** Helen: *"I can't think
  of any reason why the glass scaling would need to be different"*. The whole
  set is stroked line art since she redrew the pineapple, coconut and tiki
  mug. Run `scripts/check_glass_regen.py` after touching the normaliser's
  lists.
- **2026-09-28, #1238 #295 — the glass data is a spec, not an inventory.**
  Helen: *"I don't want inventory, just spec. I might buy new glasses (okay I
  certainly will). The 'right' glasses might be dirty. I might have more guests
  than 'right' glasses. Basically, as usual with this site, let's offer rules,
  then I'll happily break them in the kitchen."* So there is no list of what
  is in her cupboard. `glass_survey.yml` holds surveyed products per type; she
  asked for range, mean and median, and for sourced heights. The drawings are
  ahead of demand for the same reason. The goblet was published with no drink
  asking for one (2026-08-17): *"I have lots of tiki recipes that aren't in
  the database I gave you today, and given my rum obsession I bet we'll need
  it at some point."* The coconut likewise (#528, 2026-08-31): *"we might not
  use it, but why not try"*.
- **2026-09-29, #295 — `heights_mm` is generated from the survey median, with
  `height_overrides` for the glasses Helen left alone.** Helen: *"Leave
  punchbowl as we currently have it -- what we have is perfectly clear."* and
  *"Old fashioned glasses: leave them, this isn't important."* Each override
  carries its reason. The punch bowl's real 256 mm would make it the tallest
  glass and so the scale's denominator.
- **2026-09-29, #295 — the glasses reference page is Helen's brief and nothing
  more.** *"show all the glasses together, at relative scale, giving the range
  and mean ml for each (given the medians are similar we don't need to give
  those). Don't show the heights. Don't show anything else on the page body.
  Style GLASSES like a heading. And let's try the glasses in green."*
  - Order: *"Please draw them in alphabetical order so the visual effect is
    nice and messy"*, not by capacity.
  - *"round all ml measurements to the nearest 10 ml"*: on the page only.
  - Lines 1.5px, and 1px for tiki, pineapple and coconut, on this page only.
  - Each drawing stands its BASE over its label (`base_centre`). Declined:
    *"No more styling needed, so no shelf or hover."*
- **2026-09-29 — `_design_sources/` holds one source per glass.** Helen: *"Shall
  we clear out the earlier versions of drawings we've updated? I don't need to
  list them, but e.g. we're using tiki mug 9 so delete the others."* Git
  history is the record of what was tried, so the normaliser's SKIP and RENAME
  entries for superseded drawings went too. A wholesale regeneration must
  reproduce every shipped icon byte for byte (`check_glass_regen.py`).
  (Replaces the "both stay on disk" rule of 2026-08-27.)
- **2026-10-02 — `mule mug` has its own drawing, dimples included; `mug` stays
  the plain mug.** Helen redrew it and asked: *"I'm not sure about the dimples
  -- or tell me they're effective/fine!"* They stay: without them it is a
  round mug, with them it reads as hammered metal, down to card size.
  `survey_only_types` is now empty and kept for the next borrowed drawing. Her
  source is committed as she drew it. (Replaces the shared `mug.svg` of
  2026-08-26.)
- **2026-10-04, #1179 — the dilution figures are Helen's: stirred 20%, shaken
  27.5%, short shake 15%.** *"Let's use these figures for dilution please:
  stirred: 20%. Shaken: 27.5%. Short shake 15%."* Each is a share of the recipe
  volume, added as water by the ice, written on both ends of each pair in
  `fit_rules.dilution` (`glasses.yml`). A build, a swizzle and a dry shake stay
  at 0; a blended drink keeps its sourced ×1.9–2.1. Do not put the researched
  ranges back or average hers with them: she chose against them, knowing them.
- **2026-10-04, #1244 — the glass-fit report waters only what was shaken, and
  flags only what is over by more than 10%.** Helen asked for the list to be
  audited (*"could you audit the list in #1244? You have the context"*) and
  approved the fixes: *"Yes please, those four"*. Ten of 22 flags were the
  model's. Anything added after the strain, floated or held in a shell is not
  diluted (`added_after_ml`); `fit_rules.tolerance` is 10%; the top flag fires
  only under `top_room_min`; a held-back amount the method never mentions
  again still counts in the glass. Audit a report before posting it to her as
  questions.
- **2026-08-17 — `brandy glass` is the canonical name and `snifter` the alias,
  against bar convention.** Helen dislikes the word "snifter"; no words of
  hers were recorded. Do not "correct" it back.
- **2026-08-26 — `mug` is a glass: Apple and Ginger Mulled Wine is served in a
  plain mug.** Helen: *"I actually use a mug for this like I do for tea!"* The
  plain tapered drawing serves it; the Moscow Mule's hammered `mule mug` is a
  separate drawing (2026-10-02).
- **2026-09-05, #676 — the glasses are `hollowed pineapple` and `coconut
  shell`, and `martini glass` resolves to `martini`.** Helen: *"hollowed
  pineapple, coconut shell"*. The bare words name the fruit. `glasses.yml`
  maps the old spellings onto the canonical ones.
- **2026-08-27, #491 — every drink names a glass: there is no exemption list
  and no value meaning "it does not matter".** Helen: *"All recipes should
  have a glass."* Which glass is her call and is not derivable from the
  ingredients: on 2026-08-30 she named one for each of the sixteen drinks that
  had none, by taste (*"I made this up so I can say what I like!"*), and
  several read differently today. A drink with no glass is a question for her, never a
  guess from its method. A glass she wants and the vocabulary lacks goes in a
  note on the drink (the Modern Zombie's zombie glass).
  `test_every_drink_names_a_glass`; `GLASSLESS_ON_2026_08_27` is empty and a
  test keeps it empty.
- **2026-09-28 — every glass type has a surveyed capacity and height,
  including an icon no drink uses yet.** Helen: *"All 27 please."* (the
  count on the day). The glasses page states the figures for
  everything it declares, so a type is not skipped because no drink asks for
  it. `test_every_glass_type_has_a_sourced_capacity_and_height` holds
  `typical_ml` and `typical_height_mm` in `glasses.yml` to the icons plus
  `survey_only_types`; a missing figure is fixed by adding survey rows, never
  by typing a number in.

- **2026-10-19 — the julep cup, and a zombie glass is a tiki mug.** Helen: *"Declare `julep cup`"*, with `julep tin` and `julep stainless steel cup` as its aliases; `zombie glass` maps to `tiki mug`, *"but add a note somewhere to say I haven't totally ruled out adding a zombie glass to my collection"*.
- **2026-10-19 — IBA's "cocktail glass" is chosen per drink.** Helen: *"Per drink, my call"*. A draft lists `coupe` and `martini` with a `QQ glass` note.

### §9.12 / §9.12.1 Methods and garnishes

- **2026-08-26, #290 — a change to a canonical method step is proposed, never
  applied.** Helen: *"Prefer both, leaving my original too, then I delete
  whatever I don't want."* `methods.yml` `proposals:` holds each row; she
  deletes a row to keep the drink's own words. Asked later what rules she
  wanted (#705): *"If you can't Just Sort This out for me based on what it
  looks like I want then ask me questions"*, so rules are derived from the
  data and put to her as proposals.
- **2026-08-31 — a drink that takes no garnish says `no garnish`; `[]` means
  nobody has filled the field in.** Helen: *"'no garnish' actually, because
  none might read like 'not filled in' even though you and I know that's not
  the case."* `["no garnish"]` is a decision and renders; it gets no garnish
  step.
- **2026-08-31 — alternative garnishes are ONE string, the maker's choice.**
  Helen, on `orange or lemon twist`: *"either of these are lovely and the maker
  can choose. I like this approach on principle."* Refined 2026-09-14 (#984)
  to three or more: commas, then "or" before the last, declared under
  `canonical` in `garnish.yml`. Same day:
  *"Orange wheel is real and distinct new garnish — please add."* A floated
  garnish is said by `garnish:`, never by a method step.
- **2026-08-31 — a garnish carries no count.** `12 raspberries` is
  `raspberries`. Except where the count is the spec: `three coffee beans` is
  the Espresso Martini, and `three skewered maraschino cherries and a
  pineapple frond` is Three Dots and a Dash. Refined 2026-09-14: the Pink Lady's three
  cherries on a pick are `skewered brandied cherry`, singular like `skewered
  maraschino cherry`, and Helen wanted *"no note"* recording the three.
- **2026-09-08, #845 #775 — `easy peasy` goes on an equal-parts drink, or a
  short measure-and-stir one, once Helen has made it.** *"any cocktail with
  equal parts of all ingredients (bar maybe bitters) should get the tag 'easy
  peasy' once we've made it"*. Her additions set the edges: *"Julien Sorel and
  Anita's are in too, and also Long Island Ice Tea."* So a top or a mixer is
  set aside like a dash, and equal parts has no ceiling on the count. Every
  counted ingredient must be a volume, and a muddle, infusion, cook or blend
  disqualifies. It is hand-applied, so it is listed in `moods_by_hand`.
- **2026-09-08, #853 — one mood can cancel another: `mood_suppresses` in
  `taxonomy.yml`.** Helen: *"LIIT is easy peasy, and this should suppress the
  derivation."* `easy peasy` (hers, by hand) suppresses the derived `I want to
  faff`; the nine-ingredient rule itself is unchanged. Declared in the data,
  not in the script, and stated about the MOODS, so not a one-drink
  `mood_exclude`.
- **2026-09-10, #894 — an optional flame can make a drink `on fire`, but the
  Mai Tai's does not.** Helen: *"Yes in principle, but no for a Mai Tai."* The
  derivation is not widened to read `to_serve`; `on fire` stays hand-assigned
  where the method sets nothing alight, and the Mai Tai's "Optional fire if
  tiki mug" is a serving note.
- **2026-09-10, #705 — a method step that differs only in WHICH ingredient it
  names is a `shapes:` sentence with exactly one slot.** "Shake everything
  except the cola" and its kin are one canonical sentence with one `<X>`,
  filled with the ingredient as the recipe names it. One slot is the ceiling
  on purpose: two is a grammar. Short shake is its own group, "with three ice
  cubes" in every form. Helen pruned nothing and amended two (*"Rest fine,
  great, please amend."*): a build-and-stir is *"Stir all ingredients
  together."*, and a discarded twist is `lemon twist (discarded)`.
- **2026-09-14, #883 — citrus is shaken, with Helen's exceptions; a guide, not
  a test.** *"arrack-punch is muddle (citrus into solid sugar is always a
  muddle not a shake)"*; *"pic-a-de-crop-punch is stir because it's big!"*;
  *"espresso-martini is shake, to get the foam"*. Two clean exceptions (solid
  sugar, size) and one about texture, so no guard was written. Do not write
  one.
- **2026-09-17, #1138 #1143 — the garnish step reads as English: "A, B and C",
  and no "a" before a plural.** Helen: *"If there are more than two garnishes,
  separate all with a comma except for the penultimate pair, which get no
  comma."* and *"If the garnish is plural, it should not start with 'a'."* A
  final `s` marks the plural; `no_article` in `garnish.yml` keeps only what
  that cannot reach (`grated nutmeg`, `half an empty passion fruit shell`).
  A rule, not only a list, because a new spelling arrives undeclared.
- **2026-09-26 — `sharp` is disqualified by a drink being CHURNED, not by
  crushed ice.** Helen: *"Moscow Mule is sharp. The ginger beer probably
  supports this, as well as acting as a sweetener. This isn't an exception to
  the rule — it is perfectly consistent with how I intend the rule to apply."*
  `sharp` reads the narrower `mood_step_words.slushy` (swizzle, churn, blend,
  or `serve.ice: blended`); `strong brown drink` keeps the wider test. A frozen
  Margarita is still not `sharp`, because it blends.
- **2026-09-01 — "Shake with ice." stays a canonical step of its own, and
  after a rinse the step is "Shake the remaining ingredients with ice."**
  Helen: it *"should retain 'shake with ice'"*. The short form shakes what is
  already in the shaker after a build step, and is not collapsed into "Shake
  all ingredients with ice." Caribbean Sazerac's "the rest" was matched to the
  other two drinks' wording: *"match please."* The stirred form is "Stir the
  remaining ingredients with ice."
- **2026-09-09, #880 — the two generated twist steps say `then`, not `and`.**
  Helen: *"Suggest: 'Express the twist over the drink then discard it.' and
  'Express the twist over the drink then drop it in.'"* `express:` in
  `methods.yml`; the layout emits one of them for any citrus twist and no
  drink writes it.
- **2026-09-20, #606 — `fresh cherries`, `Angostura bitters`, `whipped cream`,
  `pineapple frond` and `edible orchid` are garnishes.** Helen, on the Punch
  batch: *"add all those garnishes to garnish.yml"*, and *"'Cherries' is just
  cherries, so maybe 'fresh cherries'"*, which keeps them apart from the
  maraschino and brandied ones. Bitters dashed on top at the end are a garnish
  here and an ingredient everywhere else.
- **2026-09-25, #1186 — a declared garnish that no drink uses is deleted.**
  Helen: *"Fine to delete those garnishes."* The next drink to want one
  declares it again. The opposite of the generics and glasses asked about in
  the same issue, which stay as spec (§9.3.1).
- **2026-10-07 — `lemon spiral` is a garnish of its own and gets no "Express
  the twist" step.** Helen: *"lemon spiral, no express step"*. The layout adds
  the step for the word `twist`, so a spiral, a coin or a length of peel is
  named as a different cut. Gold Florin's is `lemon spiral or mint bouquet`,
  with the source's peg dropped: *"no note, just drop"*.
- **2026-10-07 — `pineapple wheel`, `apple slice` and a second fruit stick are
  garnishes, and a floated garnish carries `(floated)` as a tail.** Helen, on
  Cannonball's quarter slice: *"a quarter of a wheel is a quarter of a disc,
  not a wedge, but let's just call that garnish 'pineapple wheel'"*; the
  quarter is not recorded. *"Apple slice is a new garnish."*, apart from
  `dried apple slice`. The second fruit stick is declared, not collapsed onto
  the first. `(floated)` follows the name as `(discarded)` does: `floated thin
  cucumber slice` was *"awkward"*. `straws`, uncounted, joined `serve.yml` the
  same day (*"Add straws."*).
- **2026-10-07 — a garnish is worded to complete "Garnish with…", and a joke
  too long for that goes in a note.** Golden Bird's is `orange peel over the
  rim (cut to look like a beak)`, from Helen's sentence *"Garnish with orange
  peel over the rim (cut to look like a beak)"*. Dead Parrot Colada's is the
  short `small stuffed dead parrot`, with *"the full thing in a note, labelled
  'Norwegian Blue'"*.

- **2026-10-19 — new garnishes, and a maker's choice stays one string.** Helen declared blackberries, dried cranberries, cocoa powder, icing sugar and ice cone, and made the dehydrated orange slice plain `orange slice`. Told that garnish.yml already writes an either/or as ONE string, she kept that rule over listing each option. A cocktail cherry is `maraschino cherry`; IBA's "N/A" is `["no garnish"]`.
- **2026-10-19 — new canonical steps.** Helen approved "Fill with ice cubes.", "Pour back into the shaker.", "Dry shake.", "Regal stir all ingredients with ice.", "Stir until the glass frosts.", the churn group, and the shapes "Add the <X>." and "Dust with the <X>." A step that carries information (a timed shake) stays free text, by the file's own rule.

### §9.13 The visual language — the rounds

**Colour.**

- **2026-08-29 — the cocktails palette is five saturated accents, "neon bar
  sign", and campari red and bitter orange are not among them.** Helen
  rejected those two as *"too red-green and inaccessible"*; simulation agreed
  (24.5 ΔE under protanopia against 101 normal). Five saturated hues that
  avoid food's six do not exist, so saturation, not hue, separates the two
  sites. The dichromacy bar applies only where colour carries meaning alone
  (the ship mark, the matched ingredient). Today's names and values are in
  `_sass/cocktails/_palette.scss`; `scripts/palette_measure.py` is the tool.
- **2026-08-29 — LEAVE OUT carries no hue at all.** Helen: *"for food,
  avoiding can be important whereas for drinks surely less so."* Violet spent
  one revision on it and read as "suddenly busy, and jarring": colour weight
  tracks how much of the page a thing occupies. Food followed on 2026-09-04,
  deleting its cobalt (§13.2); neither site's LEAVE OUT spends a hue.
- **2026-09-02, #469 — the cocktails site is black on black.** Helen: *"One
  thing for sure: we're going black on black. I wear black on black animal
  print whenever possible. I have some black on black bed linen. This is what
  we're doing."* Every `-deep` and `-wash` was re-solved for a dark ground
  (a hue is lightened to carry text) and food is byte-identical. A dark SITE
  inverts its palette; a context class (`.on-dark`, deleted) is for a dark
  section. The "card darker than the page" half was replaced on 2026-10-06
  (#733): cards sit light on the leopard.
- **2026-09-02 — on hover, magenta means "this one", and hover moves colour,
  never geometry.** Set in the black-on-black sitting, after four hover states
  were found to be lightness-only changes nobody could see: at this type size
  the eye reads hue. Nothing moves or resizes under a pointer; absinthe is the
  home colour at rest and wicked-woowoo the hover on every clickable thing.
- **2026-09-03, #679 / #680 — the index's five section headings are a colour
  ramp, one bar each, at weight 400.** Helen: *"The ramp colours are
  gorgeous!"* and, of the single bar, *"Ramp alone, gorgeous!!!!"* A pink
  under-bar was declined as *"a lot of pink up top, even for me"*. Reposado,
  coral, hot pink, magenta, violet, top to bottom (`$color-heading-*`). Weight
  400 because bold light-on-dark lettering blooms. (Replaces the five greens
  over an absinthe bar of 2026-08-30.)
- **2026-09-03 — the section's colour reaches the card: a matched thing wears
  the hue of the question it answers.** Helen, on a card carrying three:
  *"There's a lot going on... But I genuinely think it's really pretty!"* A
  matched mood chip is coral, a hassle chip hot pink, an ingredient magenta, a
  title hit violet. (Replaces "magenta means matched everywhere" of
  2026-08-30.)
- **2026-09-17, #1134 — a chosen HAS TO HAVE chip inverts, like YOLO, MOOD and
  HASSLE.** Helen: *"HAS TO HAVE chips should also invert when active, same as
  YOLO, MOOD and HASSLE"*, and *"I'm keen you copy as much of the styling as
  possible from the existing active chips because I love them!"*; then *"The
  filter chips look great! But please centre the box on the word
  vertically."* Scoped to `.drink-search--include`, because `.btn-pool` is
  also LEAVE OUT's chip. The fill may not change the chip's box (#389).
  (Replaces the magenta underline of 2026-08-30.)
- **2026-09-17, #1134 — a CHIP fills when it matches; a matched ingredient
  WORD on a card takes a band, 0.3em thick.** The fill was tried on the card
  for an afternoon. Helen: *"card ingredient chips aren't working for me at
  all. Let's go back to the underline. Can we try a thicker underline?"* Her
  first ruling, 2026-08-28: *"There's just a lot going on… underline the
  ingredient rather than highlight."* 0.3em is her own number for a title hit,
  so one thickness means "this matched". Declined: a faded fill (no alpha
  keeps the letter at 4.5:1) and the word itself in the hue.
- **Undated, #555 — each cocktails accent is named after a drink.** Helen:
  *"Yes, this is a bit silly, but humour me."* Electric absinthe, raucous
  reposado, wicked woowoo, ultra violette, luminous lagoon, banging bellini,
  charismatic cosmopolitan: the `$color-*` names in
  `_sass/cocktails/_palette.scss`. A new accent gets a drink's name, and an
  existing one is not renamed to a description of its hue.
- **2026-09-01 — cocktails' pink is food's hot magenta, `#FF00C8`.** Helen:
  *"could we please use the hot magenta from the food site as our pink? I just
  can't get away from loving it, and honestly that is my personal brand both
  at home and at work. Extra important if we're doing an inversion that we
  retain some sisterhood."* `$color-wicked-woowoo` and food's
  `$color-dazzling-dragonfruit` are the same hex on purpose; do not re-solve
  one without the other.
- **2026-09-02 — on the drink page violette marks what is in the drink, lagoon
  marks notes, reposado is the verdict's alone, and method numerals take no
  hue.** Helen's brief: violette *"shows what is in something"*; notes are *"a
  different kind of thing"*; *"the current note bar is reposado — that colour
  is the verdict's and comes off notes entirely."* Of the method: *"No colour
  has been claimed for [method]. Must not be absinthe, hot pink, hot
  curaçao."* So INGREDIENTS and METHOD are absinthe over violette, NOTES and
  its cards absinthe over lagoon, and the step numerals `$color-clear-text`.

**The nav row.**

- **2026-09-12, #993 — the arrow on the door to the other site is a drawn
  mark, not a glyph.** Helen: *"the go to the other site mark should have its
  centre horizontally aligned with the arrow"*. Courier Prime ships as a
  subset with no arrow in it, so `&rarr;` was drawn by whatever face her
  machine substituted, with that face's metrics. Offered a drawn mark, a test
  page, a measured nudge, or leaving it, she chose the drawn mark
  (`icons/arrow-right.svg`). A nudge would have been calibrated against a font
  only the container has.
- **2026-09-14 — the nav row's all-caps word sits `top: 0.1em` lower, a
  measured value.** Helen: *"please correct the snag you mentioned above, where
  the nav row's all-caps lettering sits slightly high."* Capitals have no
  descender, so centring the boxes floats the word above the marks beside it.
  The true correction is 0.0977em; it is in `em` because it is a fact about
  the face, and `position: relative` so nothing else moves. Do not re-tune it
  by eye.

**The index.**

- **2026-08-27, #478 / #479 / #480 — filters are OR within a section and AND
  between sections, more matches rank first, and chaos filters rather than
  sorts.** The order is shuffled once per page load and filtering re-ranks
  against fixed keys. Refined 2026-09-06: the ranking counts SECTIONS matched
  (#695, extend the ranking, keep the narrowing), and the list is paginated
  (#694).
- **2026-08-27, #481 — the drinks index's empty state takes food's treatment,
  value for value.** One of the six open questions Helen answered that day;
  there is no second design for "nothing matched".
- **2026-08-29 — the index asks five questions in Helen's order: YOLO?, MOOD,
  HASSLE, HAS TO HAVE / LEAVE OUT, and I KNOW WHAT I WANT last.** Helen: *"I
  feel like I am doing work to understand what to click in order to maximise
  my chance of getting the drink I want"*; *"honestly I think taste and style
  in those columns are the same, and should be called Mood. Splitting out
  Hassle though feels good."* The name search is last because *"I find
  browsing quick and inspirational… steer myself then read for a while then
  settle"*. Taste and style are not to be split again.
- **2026-08-29 — `I'm open to chaos` applies no filter at all.** Helen: *"'I'm
  open to chaos'… includes all drinks, not just
  not-known-to-be-definitely-good drinks."* The button had been backwards: "try
  anything" hid all 55 of the best drinks. It is a visible state, never a
  second narrowing.
- **2026-08-29 — the drinks index shows drafts on a local build only.** Helen:
  *"for food, we build drafts locally only, so let's do the same."*
- **2026-08-31, #595 — going back to the drinks index restores the list you
  left.** Helen: *"exactly as the food site does"*. Cocktails restores SORT
  KEYS where food restores an array.
- **2026-09-05 — "the universe says…" is one line above the five questions,
  not a box.** Helen: *"the line layout is really working for me. Really
  really… it's less obtrusive than a box and I think that's what I like about
  it."*; *"I want it to be a happy invitation"*; *"don't scale — all the same
  height"*; *"leave a fixed width for the glass so the name tape doesn't jump
  around on redeal"*; *"moods off, decision made"*. `deal again` ends the row
  (#693: the eye had read "the universe says deal again"). Kept on cocktails
  though dropped on food: *"almost always more open to persuasion about what I
  drink than what I eat"*.
- **2026-09-06, #732 — the third YOLO button is `chaos only`.** Helen: *"the
  name of the third YOLO filter should be 'chaos only'"*, replacing `never
  made it` within hours. It is a name on a scale, not a description.
- **2026-10-18, #1413 — the YOLO buttons read `ship`: `no chaos please` keeps
  `yes` and `oh gods yes`; `chaos only` keeps `meh` and `???`; `sure` and
  `IOU` show only under `I'm open to chaos`.** (`not really` was a third
  chaos value until it merged into `meh`, 2026-10-20.) Her issue: *"no chaos
  please -> only yes and yes^2 / chaos only -> only meh and not really, plus
  never made (now ???) / I'm open to chaos -> everything"*. Asked whether IOU
  belongs in `chaos only` (*"It really is chaotic, just leaning towards the
  good end. I could argue either way honestly"*), she kept it out: the dial is
  risk, an IOU's is about `sure`'s, and #1412's ship-mark filter lists IOUs
  directly. The lists are `chaos` in `taxonomy.yml`. Replaces #732's "reads
  `made_before`, never `ship`", made safe by `test_ship_agrees_with_made_before`.
- **2026-09-10 — no line of words goes under the wordmark.** Offered a
  strapline (*"What shall we cook?"*) in the design pass, Helen: *"No words
  under the wordmark section please."*
- **2026-09-10 — left alone on purpose in the design pass: the header's
  balance, the food index pills' faintness at rest, and the chip type size on
  cards.** Each was raised by a session as a possible improvement and judged a
  settled call that reads as intended once you know it is deliberate. Do not
  raise them again as defects.
- **2026-09-11, #966 / #967 — the MOOD and HASSLE buttons are in the order
  Helen typed them.** The lists under `mood_groups` in
  `_data/cocktails/taxonomy.yml` ARE the display order, and the comment there
  says not to sort them.
- **2026-09-14, #998 — the universe line has `$space-xl` between its tape and
  the rule that closes it.** Helen: *"add a small amount of space between
  universe and the horizontal rule so the top of the page feels less
  cramped."* 12px became 24px. The constraint: the rule must stay nearer the
  offer than the filters, because it belongs to the offer, and the clearance
  below it is about 37px.
- **2026-09-14, #999 — on a phone the filter sections sit a step further
  apart: `$space-xl` after a chip section, `$space-xxl` round the search
  block.** Helen: *"add a little more space at the bottom of each filter
  section on phones only. We're not prioritising above the fold on a phone,
  and it's a little hard to work out what goes where now."* A section boundary
  had been worth exactly two chip rows. The search block keeps its extra step.
- **2026-08-30 — a chosen ingredient chip carries an × at its right, and
  choosing a candidate clears the search box.** Helen: *"add an x for a clear
  button to the right of selected chips on the cocktail site, same as food."*
  Of the clearing: *"it frees the input field for more typing, and reclaims
  the space on the page."* The box is cleared on add only, never on remove.
  Food took both on 2026-10-11 (#1219).
- **2026-09-04, #546 — the shortlist ends in a shopping list that totals each
  ingredient, with a count of glasses per drink.** Helen asked for
  *"information at the bottom of my shortlist listing each ingredient (bottle
  selection if I have one, generic if not) and its amount in total if I were
  to make 1 glass of each of those drinks. Next step is a scaler."* Offered a
  count per drink rather than one number for the list: *"Per drink quantities,
  zomg yes please!"*
- **2026-09-04, #546 — a shopping-list row leads with the generic as the drink
  wrote it, with its bottles in brackets on the same line.** Helen: *"show
  generic first, with bottle on the same line in brackets, like the
  recipes."*; *"give the long rum names, not the shortened ones we generated
  for cards."* `card_names` is for cards only (#501), so the list never reads
  it: two rums that share a card name are two different things to buy.
- **2026-09-04, #546 — a juice line on the shopping list also says how many
  whole fruits it comes to, as a range.** Helen: *"Please give the range of
  whole fruits needed, like this '375 ml lemon juice (X to Y lemons)'."* The
  range comes from `juice_yields` in `ingredients.yml`, which gives each
  fruit's yield as a range, so the count is a range too and never one figure.
- **2026-10-18, #1412 — a card's ship mark is a filter to that exact value;
  the legend names the chosen value and `× clear ship` sits under it.** Helen,
  offered a fourth YOLO button or a clear in the count row: *"Neither! My guess
  is to update the ship legend to '[ship] SHIP IT? = YES' or whatever it is,
  then add a 'clear ship' button below. Vertical placement can match the X
  survivors text and shortlist button on the left."* So `.drink-count-block`
  is two by two: count and legend, then shortlisted and the clear. The value
  is the card's word, and it ANDs with the YOLO buttons rather than replacing
  them. The drink page's SHIP IT? word links to `?ship=`. This replaces
  2026-09-05's legend on the shortlisted row (*"move the ship mark into the
  same row so it's not hovering above the cards"*): the clear now holds that
  row.
- **Undated, #692 — "the universe says…" deals only from the top two ship
  rungs, `yes` and `oh gods yes`.** Helen: *"It's pretty funny when the top
  line of the site shows a drink loudly marked 'MEH', but it's still not the
  right call to allow it."* The rungs are named in `data-universe-rows` on the
  section, not through `data-chaos`, so the chaos buttons never widen the
  deal.
- **2026-09-10, #849 — the count row has no link to the share panel; the panel
  at the foot of the page is the one way in.** Helen, of the jump link she had
  asked for the day before (*"just export list as JSON and a rightwards
  arrow"*): *"the engineering is showing."* Do not add a shortcut to the panel
  from the top of the index.
- **2026-08-17 — the drinks index has no spirit filter and no glass filter,
  and neither may be added.** Helen: *"I get really bored of cocktail bars
  that have enormous bible-like menus sorted by spirit... I probably think
  browsing by spirit is basic."* Food browses by star ingredient; cocktails
  has no such axis. The spirit families in `_data/cocktails/ingredients.yml`
  exist for search and exclusion only, and the glass drawings are the site's
  identity, not a way to browse. Mood and chaos come first.
- **2026-08-30 — cocktails takes food's heading mark, index spacing and
  section-heading type from shared code, not from a lookalike; each site keeps
  its own mark colours.** Helen: *"we are putting lots of effort to almost
  exactly match styling we already have on the top of the food page. If we had
  decided upfront to use very similar styling on the new part of the site,
  would we have gone about it as we currently are???"* and *"spacing, section
  heading font and sizes, spacing between sections, I think please copy
  those"*. The panel mixins and `$rule-*` values are in
  `_sass/shared/_rule.scss`. #486 closed with the two palettes different:
  *"the design vision has moved on"*.
- **2026-08-30 — the drinks index's three text inputs take food's input type
  and food's neutral grey underline, not a section hue.** Helen: *"match the
  fonts in cocktail's include, exclude and name search input fields to
  food's."* and *"please update the border colours of the has to have and I
  know what I want input fields to the same neutral grey food's input fields
  use."* One mixin, `index-search-input-type` in `_sass/shared/_rule.scss`,
  serves every such box on both sites.
- **2026-09-02 — an index search input's placeholder disappears on focus, not
  on the first keystroke.** Helen: *"the placeholder text 'ingredient name'
  doesn't disappear when I click in the input field."* `&:focus::placeholder {
  color: transparent; }` in `_sass/cocktails/_filters.scss`. The header's
  search box took the same rule in #1096.
- **2026-09-02 — a chosen filter chip keeps its chosen colours while the
  pointer is still over it.** Helen: *"here is what a tag looks like having
  clicked it but still mouseover... the text should be white."* The
  lettering's colour has changed since (#1219: a chosen word is black on its
  section's tape); the rule has not. `:not(.is-on)` on the hover selectors in
  `_sass/cocktails/_filters.scss` is load-bearing, because `:hover` and
  `.is-on` are equally specific.
- **2026-09-05, #729 / #730 — the shortlisted-only control is a bordered pill
  in the row under the count, on both indexes.** Helen: *"Style it nicely.
  Maybe as a toggle [show shortlist]. Possibly place it below X survivors."*
  From three treatments on the real index: *"pill same, perfect."*, and *"we
  don't use any others so I'm concerned about overload"*. For food: *"Same
  location, let's say same font and pill etc too because that page already
  uses a pill as a you-can-click-me. Just take food page colours."* On is the
  border and a weight, never a fill.
- **2026-09-05 — on a narrow screen the universe line stacks in two stages and
  hides nothing.** Helen: *"please allow the line to stack, first line name,
  second line ingredients. Keep the glass and the deal again button. At even
  smaller widths, linebreak after 'the universe says...' as well."* The first
  stage is at `$universe-stack-width` (820px), the second at
  `$index-stack-width` (720px).
- **Undated — the universe line has no square brackets round the tape, and
  ingredients that are cut off end with an ellipsis and a closing round
  bracket.** Helen: *"my fault for how I explained, but no square brackets
  around the tape please."* and *"where ingredients need to cut off, end with
  an ellipsis then a closing round bracket."* The round brackets are generated
  content in `_sass/cocktails/_universe.scss`, and the closing one is placed
  where the ellipsis's clip cannot remove it.
- **Undated, #541 — the drinks index has a clear-all at the top and at the
  bottom of the filters, as food does, looking the same and in the same
  place.** Helen: *"very much like food site"* and *"I'd expect the clear all
  button to look the same and be in the same place too."* Both sites include
  `index-clear-all` and `index-clear-all-bottom` from
  `_sass/shared/_rule.scss`, so the two cannot drift.
- **Undated, #548 — no coloured bar sits above the "N survivors" count.**
  Helen, of the bar: *"distracting."* The count is not one of the filter
  sections, so `.drink-count` borrows none of their colours and has no rule
  over it.
- **2026-09-04, #546 — the drinks shopping list is ordered by descending
  volume.** Helen: *"order by descending volume required."* Since #848
  (2026-09-08) the shelf comes first and volume orders the rows within each
  shelf. Millilitres only: ranking 45 ml against 2 dashes would need a
  conversion nobody can state, so rows with no volume follow, alphabetically.
  The sort is in `shopping-list.js`. Food's list is alphabetical within an
  aisle and that is not a precedent for this one: a food aisle has no single
  axis to rank on, a shelf of bottles does.

**Cards.**

- **2026-08-26 — a drink card is horizontal, the glass in a fixed left column,
  and every anchor on it is fixed.** Helen's brief for the site: *"Ink, paper
  and glass."* Horizontal was chosen over a vertical card and a typographic
  tile, for the ingredient line. Of the fixed height: *"it's a shame to lose
  the card proportion but I can't think of another way."* The cost is
  clamping. No panel sits behind the glass (2026-09-02). Since 2026-09-15 the
  fixed height holds above 720px only.
- **2026-08-31 — below 400px a card stacks: the glass above, the words full
  width.** A width problem, not a line problem: at 360px the text column was
  157px. Three layouts were built behind `?narrow=` and Helen chose `stack`
  from a page of them. Re-measured at the 6.5rem column (174px) and kept.
- **2026-09-02 — a drink's name is on worn black Dymo tape, on the card and on
  the drink page.** Helen: *"worn black Dymo tape with white punched
  lettering."*; *"the boldness of the two near-whites with no softening shadow
  is exactly what we need."*; and the geometry is solved so *"reasonably
  lengthed names of cocktails can appear on the one line"*. The band is
  centred by moving the ARTWORK, not the text. On the drink page the tape
  wraps a real `<h1>` at `display: contents`, in a `<div>`, so there is one
  emboss and a valid heading.
- **2026-09-04 — the card's glass column is 6.5rem.** Helen: *"Narrower glass
  column please."* Down from 7.6rem, the design audit's critical #9.
  `$card-text-x`, also a custom property so no rule bakes its own copy.
- **2026-09-04 — a card has no rule or mark along its bottom edge at rest.**
  The audit read the green dash as "a progress bar stuck at 18 percent".
  Helen: *"Agree, no mark, end of."*
- **2026-09-04 — a card name that does not fit shrinks one step or wraps,
  never ellipsises.** Helen: *"shrink when it's just one short-ish word too
  long, then two lines where it's more than that. The one super-long title we
  have I'll just shorten, and retain that principle."* The step is 0.86
  (`$card-name-step`, `card-name-fit.js`). With no JavaScript the ellipsis
  stays.
- **2026-09-04 — the mood chips on a card are bare words, not pills.** The
  design audit's critical #5, answered *"100% cards take words"*. Courier,
  lowercase, a middle dot between them.
- **2026-09-04, #546 — the card's shortlist `+` sits at its top right, paid
  for out of the title's width.** Helen's placement. Refined 2026-09-11
  (#962): the mark went from 0.95rem to 1.15rem; the hit area was already
  about 44px square, it was the mark that read small. `$card-shortlist-size`
  is one variable, read by the title's reservation too.
- **2026-09-06, #552 — a card shows three lines of ingredients, paid for by
  the foot.** Helen: *"showing three lines is appropriate given the number of
  tiki drinks I have!"*, and from a screenshot: *"we could stand to move the
  chips on cards downwards, encroaching into the ship row."* A wrapped name
  gives one line back. (Replaces the two lines of 2026-09-04.)
- **2026-09-11, #886 — under the cursor a card's field lifts to the magenta
  wash and its glass turns pink.** Three treatments went on the real index.
  Helen: *"option c please, but 1. without the border above and below the
  glass, b) glass also turns pink."* The two 3px strips that were the old
  hover are deleted. Not taken: a magenta border, and the separator dots
  rising to absinthe. The keyboard gets the same state through
  `.drink-card:has(:focus-visible)`, as its own rule, never in a comma list
  with `:hover`.
- **2026-09-11, #971 — the drink's name turns pink wherever the cursor is on
  the card, and the whole card is clickable.** Helen: *"#971: agree. I
  declined the title turning pink, and should have accepted. BUT I also want
  the whole card to be clickable, which is different."* One anchor, the
  name's, with an `::after` drawn in `vmax` and cut to shape by the card's
  `overflow: hidden`; `inset: 0` cannot work under the positioned tape word.
  Do not move the anchor up the markup: the name search rewrites its
  `innerHTML`.
- **2026-09-15, #1086 — below 720px a card is as tall as its own content.** A
  session's call from the design review, not Helen's ruling, and #1323 builds
  on it. `$card-height` exists so a ROW of cards matches; a single column has
  nothing to match, and short cards carried a dead band of 50–100px. The foot
  goes from `position: absolute` to `relative` there. Above 720px nothing
  changes.
- **2026-10-06, #1292 — a card's tagline is a REVEAL: hover takes the card on
  a computer, and a `?` left of the `+` does it where there is no hover.**
  Three rounds on the real index. Helen: *"hover takes the card is
  fantastic!"*; *"Baselines match, ? next to +, but the active colour needs to
  be woowoo."*; *"I like 0.90 rem. Decision made, phew!"* Typewritten, its
  first baseline on the ingredient line's, five lines clear the ship mark
  (three under a wrapped name). The keyboard's way in is the name's link only.
- **2026-10-06, #1292 — an over-long tagline is Helen's to cut, not the
  stylesheet's to absorb.** *"I can cut some characters. I expect that should
  be my position anyway."* The working limits are about 105 characters, and
  about 65 where the name wraps on its card. Declined: sizing the line by its
  length. A test holding taglines to the limit was offered and not taken up.
- **2026-10-06 — the DRAFT badge sits at a card's top left, same size, in
  `$color-text`.** Helen: *"Do you think we could put the DRAFT label anywhere
  else? I actually already find it hard to spot."* Of two placements she chose
  *"Option 1"*, top left: *"It's for my eyes only (and I guess for any keen
  beans who build from the repo, for whatever reason), so we don't need to
  fuss too much."* Not smaller, since being hard to spot was the complaint; no
  hue (#1162). Above the title's lettering was turned down on geometry. The
  drink page's badge is unchanged.
- **2026-10-07, #1323 — on a phone a flipped card keeps its resting height.**
  Helen: *"Sometimes when the card turns over, there's lots of space under the
  tagline, and cutting it would allow the card not to change size on
  flipping."* While the tagline shows, the ingredient line and chips stay in
  their boxes, invisible, and the tagline lies across them. Its last line
  reserves the ship mark's width inline, after her second look: *"there is at
  least one clear line between tagline and ship mark each time."* A card grows
  only when the tagline is longer than the room.
- **2026-08-30 — the goodness mark on a card is a ship icon and a word, pinned
  to the card's right, not a tinted square.** Helen: *"I am worried I no
  longer like the goodness mark. It might well not be clear enough at speed.
  ... it will have to be the right to keep the icon in the same place on each
  card, otherwise I think it will create visual noise."* A word cannot be
  misread as a score out of five. `.drink-card-ship` in
  `_sass/cocktails/_cards.scss`, the icon in reposado.
- **2026-09-02 — a card's tape overhangs its lettering equally at both ends
  and bleeds left, so the lettering starts on the ingredient line's edge.**
  Helen: *"extend the tape slightly leftwards, and start the lettering
  slightly rightwards of where it is now, then balance the tape at the right
  edge with the same padding IF the cocktail name is short enough to all be
  shown on one line."* `$card-tape-pad-x` and `$card-tape-bleed` are both
  1.05em and must stay equal. Padding costs the name's width twice and the
  bleed pays it back once, so both stay small.
- **2026-09-02 — a card's name is 1rem.** Helen: *"let's change the cocktail
  names to 1rem. It's a shame but I think it's the right compromise"*. It is
  the default of `--card-name-size` in `_sass/cocktails/_cards.scss`. The
  drink page sets the same property for its title, and `--card-name-scale` is
  the fitting step, so the two decisions stay apart.
- **Undated — the tape's top rim highlight is 6% white.** Helen: *"L06 is
  looking great."* A `drop-shadow` one pixel above `.drink-card-tape-bg`, not
  a border, so it follows the tape's torn outline; `.drink-card-name` may not
  be `overflow: hidden`, which would crop it.
- **Undated — every ship rung is one short word on a card, and the word has no
  reserved width.** Helen: *"the motivation is getting everything to the same
  number of words, i.e. one, so the cards look more stable."* and *"please
  don't force the word to be fixed width, it looks weird. The words are
  similar enough length that I'm hoping the slight movement in the ship icon
  won't matter."* The card's words are `ship_card_names` in
  `_data/cocktails/taxonomy.yml`; the drink page says the rung in full.

**Chips on a card.**

- **2026-09-06, #757 — chips that match a filter lead the row.** The DOM
  moves, not flex `order`, because the separator dot is a DOM-order selector.
  How a matched chip is drawn is PR #1100's ruling (2026-09-15, *"Chip option
  B please"*: an inverted block), which replaced #756's "retain the font
  colour".
- **2026-09-08, #846 — every chip but the last carries a trailing dot, even at
  the end of a line.** Helen: *"chips which form more than one line should
  have a . in between them even if the final chip on any line before the first
  is a whole chip..."* She was shown the built thing and wanted what had been
  considered and rejected. An unconditional dot needs no measuring, so no chip
  can lead a row with one, and it stays in flow so a dot ending a row is not
  clipped. (Replaces the leading dot of 2026-09-05.)
- **2026-10-06, #1308 — a card's chips are packed, fullest row first;
  alphabetical is only the tie-break.** Helen: *"let's try allowing tags to
  wrap if we tweak the order rather than requiring them to be alphabetical."*
  Of three candidates on the real index: *"Option C, chef's kiss!"*, the one
  that packs every card. `packChips` in `card-line-budget.js`: most chips
  shown, fewest rows, the ship's row stopping short of the ship. Refined
  2026-10-07 (#1331): a row may end early. Not ruled: WHICH chip is clipped
  where one still is. (Replaces #710 on a card.)
- **2026-09-02 — a mood chip on a card is clickable and filters the index by
  that mood.** Helen: *"please make the chips on cocktail cards clickable,
  with mouseover outlining the chip in pink as when they're active from
  filtering, where clicking filters all cocktails by whatever the chip is
  for."* The whole card became a link on 2026-09-11 (#971); the chip keeps its
  own click (`.drink-card-mood` in `cocktail-index.js`).
- **2026-09-10, #760 — a chip is never shown cut off mid-word by the ship
  mark.** Helen reported chips reading "sugar crav" and "no juici". Where the
  chips on the ship's row reach its left edge, `card-line-budget.js` sets
  `--ship-w` on that card and the stylesheet pads the chips clear of the mark
  there only. #1308's packing builds on it. No fuller words of hers were
  recorded.
- **2026-09-05 — a card's mood words rest in their section's colour and hover
  in magenta.** Helen: *"in the name of more is more, would it be too much to
  colour the chips in their colours to start with, not just on mouse over? I
  really do love colour. They could then mouseover in wicked-woowoo like the
  rest of the site."* `.drink-card-mood--mood` and `--hassle` read
  `$color-heading-mood` and `$color-heading-hassle`, never a literal, so a
  chip, its matched state and the heading that selects it cannot drift apart.

**The drink page: head.**

- **2026-09-02 — the drink page's meta is three facts and nothing else: glass,
  garnish, SHIP IT?.** Refined 2026-09-05: the glass line is the glass alone.
  Helen: *"I don't think it makes sense to show 'hurricane, blended'"* and
  *"ice pedantry will be more likely to be seen at the point in the make where
  it happens."* Garnish is a list joined whole. SHIP IT? reads the card's own
  include and is unconditional (an unrated drink prints `???`, #722). No
  control goes in this row: it would claim to be a fourth thing the drink IS.
- **2026-09-05 — the drink page's glass sits inline at the head's left,
  centred, not out in the margin.** Helen: *"Inline glass please. I don't care
  if this is changing my mind!"* She had only ever seen the inline branch: the
  margin layout rendered above 1180px only. (Replaces *"glass in the margin
  and top aligned, ship it"* of 2026-09-02.)
- **2026-09-05 — the drink page's title is 2.6rem on tape padded 1.6em each
  side.** Helen: *"The title seems enormous."*, and *"more empty tape either
  side of the cocktail name. Don't move the tape further left…"* The `<h1>`
  carries `font-size: 1em` because the browser's own `h1 { 2em }` had doubled
  it. On a phone it is 1.6rem (#1357). (Replaces 3.2rem of 2026-09-03.)
- **2026-09-05, #710 — the drink page's mood chips are links to the filtered
  index, in alphabetical order.** Helen: *"Must be the same chips as on the
  cards."*; *"let's wire the chips up to show a filtered index page please,
  echoing what we do on the food site, which feels lovely."*; and *"render
  cocktail tags on cocktail pages in alphabetical order because no one cares
  which group they came from."* A real `<a href>`, so middle-click and copy
  link work. `sort_natural`, not `sort`.
- **2026-09-05 — SHIP IT? shows in `read it` only; `make it` hides it in the
  stylesheet.** Helen: *"I might have said the wrong thing, but I want ship it
  to display in read it mode, and not to display in make it mode."* Nothing
  leaves the DOM, so print and a no-JS reader keep the fuller page. It shipped
  the other way round for an hour on a mis-stated instruction; the stylesheet
  is the authority.
- **2026-09-05 — `yes²` is not renamed: the drink page says the rung's own
  words and the card keeps the compression.** A review read it as a footnote
  marker. Helen: *"that's not a footnote marker, it's a joke, a cocktail so
  good that it's yes-squared. If this isn't landing then I'd rather rename
  than re-render."* A grid of cards supplies the scale to read an escalation
  against; a single page does not.
- **2026-09-10, #897 — `read it / make it` is under the title block's rule, at
  the row's left.** Helen: *"move read it / make it toggle to the top right of
  the page main content, just under the section divider that sits between the
  metadata section and ingredients."*, then the same day: *"How about moving
  the read it make it to the left? I can imagine that feeling quite natural in
  the kitchen -- I'll be on the left of the page looking at the ingredients
  list."* Both labels always show and the active one is bold.
- **2026-09-10 — the drink page's title block starts 1rem under the back
  arrow.** Helen: *"it now feels like there's quite a bit of space at the top
  of cocktail pages. Should the top bump up a bit, closer to the back arrow?"*
  Food's own gap; the arrow stays put.
- **2026-09-10, #942 — on a phone the head is a grid: tape and tagline full
  width, the glass beside GLASS / GARNISH / SHIP IT?, chips full width
  beneath.** Helen's complaint: *"All cocktail pages have the glass
  overlapping problem."* Asked on 2026-10-11 (#1370) to choose between this
  and a glass-above alternative: *"Definitely what has shipped. I choose what
  has shipped."* #995 and #1086 were ruled on top of it. On this page only, the tape artwork is scaled so a
  wrapped title's lines stay inside the band.
- **2026-09-11, #979 — the drink page's meta ends where the title tape's
  column ends.** Helen: *"The metadata line could be bounded by whatever
  constrains the right-hand edge of the title tape. I think that would look
  nice."* The shortlist button's edge was the other candidate. The meta is
  `1fr 1fr auto` with her 5rem column gap (2026-09-03, #679), which comes down
  to `$space-xl` below `$width-content` so a long garnish does not break.
- **2026-09-12, #995 — on a phone the title tape starts on the column's left
  edge.** Helen: *"name tape can start left-aligned with the metadata, giving
  us as much space for the name as possible"*, then: *"This is for mobile
  view, I should have been clear, NOT desktop or ipad."* The box already
  started there; the black band did not, because each tape SVG insets its
  polygon by a percentage of its width. So the tape bleeds left by 4.14%, the
  modal inset (`scripts/tape_insets.py`), and its `max-width` grows to match.
- **2026-09-15, #1086 — the drink page has one shortlist button, in the
  actions row under the head's rule.** Helen, shown a page carrying two:
  *"actions row only."* The one in the head went, and with it the
  `.cocktail-title-row` wrapper. The row is `_includes/page-actions.html`,
  the include a food recipe page uses (#1005; redrawn in #1210).
- **2026-10-06, #1292 — the drink page's tagline is typewritten, upright,
  1.1rem, with `$space-xxl` above it and no separator.** Two rounds on a real
  page. Helen: *"I like the typewriter font version. I think this needs some
  more vertical space between title and tagline, otherwise some kind of
  separator."*, then of three gaps and three separators: *"more space still is
  working for me really nicely."* Taglines are *"the main avenue for personal
  voice for most uses of the site."* (Replaces the 1.05rem line of
  2026-09-05.)
- **2026-10-06, #1292 — ruled out for taglines: on the index card at rest, a
  tagline of the day, a sign-off in `make it`, a page of taglines, a share
  image.** Helen: *"no taglines back on the index cards."* (#512 stands,
  challenged with measurements and confirmed); a tagline of the day on the
  index, *"Too much even for me."*; a sign-off at the foot of `make it`, *"It
  feels messy"*; a page of nothing but taglines, *"not now, not ever"*.
- **2026-09-02 — the meta's labels are small Courier capitals in the quiet
  grey with no emboss, and its values are body text.** Helen's brief: *"labels
  in $font-headings 0.72rem 700 uppercase 0.1em $color-clear-text; values body
  0.95rem."* The emboss was tried on GLASS / GARNISH / SHIP IT? and came off:
  *"having seen it, it's too much"*.
- **2026-09-03 — the drink page's glass is absinthe, drawn bolder, and never
  shorter than 14rem.** Helen: *"I think our glass styling has fallen off. Can
  the glass be bigger, bolder and absinthe?"* and *"It looks much better on
  the narrower screen actually"*. `$glass-min` is the floor and the title
  block's `min-height` holds the head open for it; `.glass-icon-line` is a
  non-scaling 2px stroke. `make it` drops both floors, and the phone head
  (#942) has its own layout.
- **2026-09-05 — the SHIP IT? word on a drink page is set in the index card's
  face.** Helen: *"match the font on the ship mark to what we have on the
  cards on the index page."* The page has no `.drink-card-ship` container, so
  `.cocktail-ship .drink-card-ship-word` restates the heading face, at 0.88rem
  to sit with the values beside it. Without it the word inherits the body
  sans.
- **2026-09-05 — the mood chips in a drink page's head are larger than a
  card's.** Helen: *"I'd like to make the chips below them a little larger,
  which will take up more horizontal space (on the whole) and balance things
  out a bit."* 0.85rem against the card's 0.72rem, with a line-height of their
  own, because `$chip-line` is tuned to the card.
- **2026-09-05 — `make it` closes the head up: the page moves up, the glass
  shrinks to the name and what is left of the meta, and the title and the
  head's spacing do not change.** Helen: *"'make it' should move the section
  rule and the rest of the page upwards, whereas currently the metadata just
  disappears leaving empty vertical space. The glass should shrink to the
  height of the name plus remaining metadata."* Of a build that resized the
  title (#519, #520): *"clicking MAKE IT makes the fonts and spacings go back
  to before your last victory."* Glass and garnish get larger and heavier in
  place (#493): *"including moving glass and garnish somewhere more
  prominent."*
- **2026-09-09 — a long drink title stays inside the page column: it steps
  down, then wraps.** Helen: *"Long drink titles run off the cocktail page
  screen."* The page's tape is the card's markup, so `card-name-fit.js` fits
  it as it does a card. The title's size is set as `--card-name-size`, never
  `font-size`, which would opt the page out of the fit, and the name's grid
  item carries `min-width: 0` so there is an overflow to measure.
- **2026-09-10, #893 — the head's chips sit `$space-xl` under the GLASS /
  GARNISH / SHIP IT? row.** Helen: *"add a small amount of vertical space
  between cocktail glass/garnish line and chips line."* The meta carries
  `$space-md` and the chips the remainder, because `make it` hides the chips
  and the meta's own margin is what holds the head open then.

**The drink page: body, scaler, foot and print.**

- **2026-08-27, #482 — a drink page prints as the FULL page, whichever state
  is on screen.** Helen: *"The full page should be what ends up in the PDF and
  prints."* One of the six open questions; the session's expectation was
  confidently the other way. `_sass/cocktails/_print.scss` restores the read
  state and hides the controls, the universe line and the related cards.
- **2026-09-05 — INGREDIENTS, METHOD and NOTES are 1.5rem at weight 400.**
  Helen, 2026-09-03, had asked for bigger: *"INGREDIENTS and METHOD feel very
  small. They're larger on food recipe pages and I prefer that."* That gave
  1.8rem; two days later it came down, because punched Courier over a double
  rule is a lot of furniture to stand over a one-line method.
- **2026-09-05 — ingredient names carry no underline, and violet joins
  absinthe under the section titles instead.** Helen: *"we need to drop the
  violet underlines under ingredients because they look like links. This means
  we can return the violet underline to join the absinthe under the section
  titles"*.
- **2026-09-05 — the scaler is one small box under the ingredients list.**
  Helen: *"the normal scaler shouldn't get to be at the top of the page.
  Please simplify it and move underneath the ingredients list, just a single
  input text box, 2 characters wide, with a small x next to it, no other text
  at all."* Its third home; do not move it back up. The `x` became a word
  after the box in #1086.
- **2026-09-05, #720 / #721 — the scaler makes whole recipes only, and there
  is no target-volume box.** Helen: *"Logically I think we can solve the
  rounding/ratio issue by only allowing integer multiples."* Of the
  millilitre box: *"it's just baffling. Typing some numbers changes nothing,
  typing others changes the recipe but you can't see it…"* Every word was true
  and none a bug: the rounding grid was real and invisible. The page updates
  on each keystroke.
- **2026-09-10, #731 — the scaler has a `−` and a `+` either side of its
  box.** Helen's sketch: "-  [1]  x  +". `−` is U+2212. Absinthe at rest and
  wicked-woowoo on hover, by the standing colour rule. Each click calls the
  same `apply()` a keystroke reaches, never a second arithmetic path, and
  neither state changes the button's size.
- **2026-09-14, #1001 — the units line is on the live site.** Helen: *"add to
  live site"*. She overruled her own caution of 2026-09-06 (*"local only now,
  and I'll note what publishing would need"*): the `qq:` strengths in
  `abv.yml` are not cleared, and the line says "Roughly" on every drink.
  `show_units` is retired, not set to `true`. Where the line sits was replaced
  by #1099 (the footer: source, units, cost).
- **2026-09-15, #1086 — a printed drink page has its own palette, scoped to
  `.cocktail` inside `@media print`.** A session's call from the design
  review, not Helen's ruling. Every accent was solved against black and
  printed on white paper at 1.25:1 to 3.11:1. Ink and quiet grey are food's
  two values; each accent is darkened by the smallest step that clears 4.5:1.
  The name tape is artwork and is untouched.
- **2026-09-20, #1088 — the scaler says nothing when it will not go lower.**
  Helen: *"Drop the can't-go-below text, it is not needed"*, and: *"We don't
  go lower than the recipe amounts, because the scaler is an integer and
  doesn't go below 1."* The message was unreachable, and on a drink with a
  tiny written amount it would have fired on the drink's own recipe. Silence
  degrades correctly: the written amounts stay on screen.
- **2026-09-04, #545 — scaling a drink never moves its ratios: the multiple is
  snapped so every amount lands on 2.5 ml, and no amount is rounded.** Helen:
  *"The ml only matter because I love my glasses and make drinks for them
  precisely, but that isn't as important as not poisoning my friends."* A
  multiple that would take a volume under 2.5 ml is refused. `scale.js`. The
  target-volume box she asked for alongside is gone (#721); the grid is not.

**Related drinks.**

- **2026-09-28, #1090 — "If you liked this, how about…" on a drink ranks by
  shared moods, then shared ingredient generics, then title.** Helen, on the
  order star, mood, ingredients: *"That's a great ordering. Let's go."* Drinks
  have no star, so moods lead. Still no `meta.ship` weighting (#927, *"Keep it
  simple."*). In Liquid in the layout, hidden in `make it` and in print;
  `scripts/related_drinks.py` is its mirror and a test holds them equal.
- **2026-10-16, #1183 — the fourth related drink is a renegade, taken a
  quarter of the way down the ranking.** Helen, on tiki drinks all suggesting
  each other: *"make the fourth one renegade -- maybe hop to 25% or 50% down
  the list?"*, and chose 25%. Half way down often shares a single generic.
- **2026-09-11, #955 — a divider separates the end of the recipe from "If you
  liked this…".** Helen: *"Please add some kind of divider between the end of
  the recipe (whether serve or notes or anything else) and 'If you liked
  this...'"* The section wears `.cocktail-footer`'s hairline. The same issue
  asked for cards in place of the compact row, which #991 settled.
- **2026-09-12, #991 — the related cards ARE the index's cards; there is no
  variant.** Helen: *"We are fighting this design, and trying to invent a new
  design language, where we should just reuse what we've already made."* A
  `--portrait` modifier lasted one day and needed six issues. Plain
  `.drink-card` in `.drink-cards`' own 370px grid, with the index card's
  `+` (#977). Two differences, neither geometry: chips are links, and there
  are no search `data-*`. Do not make the row three across by other means.
  (Replaces #955's portrait card, #960 and #976.)

**Moods.**

- **2026-08-30, #452 — a mood is evocative, not a flat flavour descriptor.**
  Four flavour tags were proposed and killed. Helen: *"They're flat
  descriptors, which is fine in moderation, whereas I'd hoped for more
  evocative moods, you know, something I can offer beyond what one might guess
  from the ingredients list."* A tag meaning "contains one of these bottles"
  is a worse copy of HAS TO HAVE.
- **2026-08-30, #452 — `up` is not a mood.** It covered 51% of the collection.
  Helen: *"I'm not sold on up, let's retain it but with suspicion"*, and
  `test_no_mood_covers_more_than_half_the_collection` reached the same
  conclusion the same day. No mood may cover more than half the drinks.
- **2026-10-12 — no mood cues how strong a drink is.** A "school night" tag
  built from the units was proposed and refused. Helen: *"I don't want to cue
  strength. Alcohol is a drug and people dose it. A unit is a unit, and I
  declare those on every page."*
- **2026-10-12 — `nightcap` and `sugar craving` both stay.** `nightcap` sits
  mostly inside `strong brown drink` today (8 of 12 published); Helen: *"Nightcap
  will gain more drinks of the pudding in a glass variety, which addresses that
  problem too."* `sugar craving` no longer matches its written definition on
  most of its drinks, and is left alone until her own pass: *"I'll do a full
  pass over everything tag by tag when I'm closer to having all my drinks in
  the set."* Do not prune or redefine either before then.
- **2026-09-19, #1127 — `no measuring` means every measured amount is a
  whole-number multiple of the smallest, in eight measures or fewer.** Helen:
  *"for drinks I can make with just one receptacle, if that's all I have. Such
  as 1/1/1, 2/1/0.5."* The cap is the feature: uncapped the rule is 58% of
  the collection. She chose eight from a printed table of six, eight, ten and
  twelve. The name is hers, and a drink with one measured line qualifies:
  *"The tag is 'no measuring', and all your examples clear that bar."*
- **2026-09-19, #1127 — for `no measuring`, a measured top is an amount like
  any other; lengtheners are not set aside by name.** Helen: *"No ingredient
  in the Aperol Spritz is a top."* Its 90 ml of prosecco belongs to its 3:2:1.
  Champagne written `to top` has no volume and falls out on its own. Accepted
  cost: Long Island Iced Tea and Lita Grey drop out, each carrying a measured
  60 ml.
- **2026-09-20, #1127 — fifteen published drinks that gained only the `no
  measuring` chip went live without a re-read: a single grant, not a standing
  rule.** Helen: *"if the only change to those 15 files is the chip appearing,
  I don't need to proofread, please just let them be live."* The condition was
  proved by diffing all fifteen against `main`, then `COCKTAIL_BASELINE_COMMIT`
  moved. A later derived mood needs her grant again; `CLAUDE.md`'s proofreading
  rule is otherwise unchanged. Confirmed 2026-10-11: *"Not a standing
  exemption -- it was probably a one-off."*
- **2026-08-30 — Jägermeister, Strega and Becherovka count towards `warming`,
  as warm-spiced liqueurs.** Helen: *"Jagermeister, Strega and Becherovka
  could hint at warming too."* And on P-Five Punch, 2026-08-31: *"I'd reach
  for Becherovka if a recipe wanted something cinnamon- or ginger-forward."*
  `mood_ingredients.warming` in `taxonomy.yml`. Warm spice, never temperature,
  and not because they are herbal.
- **2026-08-30 — being topped up does not stop a drink being `sharp`.** Helen:
  *"I think a Tom Collins is sharp, so is Airmail and Green Flash."* A long
  drink with a base, a citrus and a sweetener still qualifies; blending and
  swizzling are what disqualify it (2026-09-26).
- **2026-09-06, #758 — Caribbean Sazerac does not carry `I want to faff`; the
  plain Sazerac does.** Helen: *"Caribbean Sazerac should not have the chip 'I
  want to faff'."* Its `mood_include` entry came out. The Sazerac keeps one,
  because icing, rinsing and discarding count as one faff moment where the
  rule wants two.
- **2026-09-26, #1216 — for `no measuring`, an amount of exactly 5 ml is a bar
  spoon and is set aside like a dash.** Helen: *"if any amounts are 5 ml, this
  is just a bar spoon, and doesn't count as needing to be measured."* It
  neither joins the ratio nor becomes the smallest measure. `BARSPOON_ML` in
  `scripts/derive_cocktail_moods.py`. For `no measuring` only: the same
  exemption was measured for `sharp` on 2026-10-08 and declined.
- **2026-09-28, #1187 — `tiki` has a derivation rule again: two tiki markers
  in a drink of four or more ingredients.** Helen: *"I'm sure we used to have
  a tiki deriver -- something like more than x ingredients, fewer than y, and
  at least two typical tiki ingredients???"* Her definition is what the
  ingredient floor stands for: *"a complex drink with lots of ingredients and
  lots of taste layers which is why it's not just a jar full of sugar"*. The
  mood stays in `moods_by_hand`, so the rule only adds. `clear` was measured
  the same day and got none. The one-marker-in-eight slice is 2026-10-08's.

**Food, ruled in the same passes.**

- **2026-09-11, #961 — the food index row's shortlist button sits level with
  the title's first line.** Not the row's middle, which on a phone is the
  ingredient line. By construction: it takes the title's line box.
- **2026-09-11, #964 — on a phone the food method's step numbers sit closer to
  the edge and closer to their text.** Helen: *"on mobile, reduce the indent
  of method step numbering from the edge, and also the distance between the
  number and the method step."* Numeral 0.5rem in, text 2rem in. This
  overrides the 2026-09-10 pass, which had left the method indent alone.

## §10 Validation

- **2026-08-12 — every closed issue is represented by a test, and the suite is
  self-sufficient.** Helen: *"I'm concerned that issues we closed in the last
  few days weren't represented as tests... I still don't want to end up in a
  mess."* and *"you should be able to bring the recipes into shape from pytest
  output and this file alone"*. So a test's name and failure message state the
  rule and the remedy. The audit that followed (grep the tests for issue
  citations, diff against closed issues) turned twenty-odd gaps into tests.
- **2026-08-18, #369 — the suite gates the deploy.** Until then the workflow
  had no test step anywhere. `deploy` needs `test`, so every guard is a deploy
  stop rather than a report, and a red `main` ships nothing (the outage of
  2026-09-12). `fetch-depth: 0` is load-bearing: in a shallow clone the
  proofread-provenance test passes over nothing. The journal recorded the
  decision without Helen's words.
- **2026-08-29, #540 — private drinks are gated at promotion and are never
  checked by a runner.** Helen chose option 4 of four. Helen: *"my preference
  is not to leave things in a state where tests fail and we have to remember
  why every time we run the suite, but the solution to that is not to turn off
  or otherwise avoid the tests."* So a test that cannot be answered on a
  partial corpus is split and its answerable half keeps running. Every drink
  test reads both `_cocktail_recipes/` and `_cocktail_drafts/` through
  `_load()`, so a promoted drink is checked everywhere, CI included. A claim
  about a whole corpus is not checkable against a partial one: the ratchet
  half of a guard runs everywhere, and the staleness half calls
  `_require_whole_collection` and skips with a reason.
- **2026-09-05 — the public and private repos are kept in step by a schema
  handshake: a hand-maintained integer.** Helen's choice among four options,
  after #624: the garnish vocabulary merged here while the drink-side rename
  sat on an unmerged private branch, red for anyone with a clone and green in
  CI. `SCHEMA_VERSION` in each drafts repo is compared with
  `tests/drafts_schema.py`; bump both in the paired commits. Declined: a
  fingerprint (not every schema change needs a migration) and `pytest.exit()`.
- **2026-09-20, #1127 — no test is expected to fail; a guard that fires on
  correct data is fixed, never learned around.** Helen, shown five failures of
  which four were drafts-only and invisible to CI: *"It's not useful to have a
  situation where we expect tests to fail, and we should rearchitect."* Two
  fixes followed. A `QQ` is a declared absence, not a name: four checks had
  looked `generic: "QQ"` up as a real generic. And a drink taken off the site
  is not a drink that gained a figure: a census against the built site runs
  over what is in the build and names what it set aside.
- **2026-09-20, #1106 — a check that verified nothing reports SKIP, never a
  pass.** A session's call, not Helen's ruling, and the tooling depends on it:
  `verify.py` reads exit code 2 as SKIP, prints SKIP, stays green because an
  absent private repo is not a defect, and names in its closing line what went
  unchecked. A green run in a fresh worktree has not checked the slug keys and
  says so. From the same group of fixes: a new guard is proved by breaking the
  thing on purpose and watching the guard name it.
- **2026-09-20, #1147 — `mood_step_words.ice` stays although it decides no
  drink today.** A session's call, not Helen's ruling. Measured: 14 drinks
  satisfy both halves of the icy rule, 24 the `serve.ice` half alone, none the
  step half alone. It stays because `serve.ice` is optional: a freshly
  ingested swizzle has no serve value until Helen rules, and the step words
  give it the mood meanwhile. Do not empty the list, see nothing move, and
  conclude it is dead.
- **2026-09-29, #1200 — the browser smoke test skips without a browser unless
  `HT_REQUIRE_BROWSER=1`, and the image sets `PLAYWRIGHT_BROWSERS_PATH`.**
  Helen's two rulings: keep the opt-in, and add the ENV. The workflow is to
  set the variable in the same edit that installs Chromium. Keying on
  `CI=true` would be red today because CI has no browser, and a skip with no
  opt-in would hide a broken install for ever. The test's own `tmp/browser/` →
  `/opt/playwright` search still overrides the ENV, because a worktree's own
  copy exists exactly when the image is older than the pin.
- **2026-09-29, #1202 — the rulings index is generated and carries no line
  numbers.** The issue proposed them. Helen chose not to bend "name files,
  never line numbers", shown the merge cost: nearly every branch adds an
  entry, one entry near the top renumbers everything below it, so two open
  branches would conflict in the index on every merge, and an index merged
  wrong is a red `main`. Run `python3 scripts/build_decisions_index.py
  --write` after any journal edit; `tests/test_decisions_index.py` holds the
  two together. Parked, not refused: moving the "why" paragraphs out of the
  templates, a week's work across the largest Liquid files.
- **2026-10-02, #1271 — tests are not skipped by changed path.** Helen asked
  whether gates could skip irrelevant tests on a small merge. Measured with
  both drafts clones: 31,961 tests in 404s, four modules holding 90% of it and
  the other 29,000 costing about 36s between them. A path gate would have
  saved seconds on the cheap tests and added a way to be green without
  looking. The three slow places were fixed instead, 404s to 128s with the
  same results. A session's answer to her question, by measurement; she did
  not rule on it in words.
- **2026-10-04, #1194 — the drafts repos get no CI of their own, and the
  question is closed.** Offered four ways to stop CI and a local run checking
  different corpora, Helen: *"I understand B. I honestly don't understand C or
  D. All I want to achieve here is not publishing embarrassing broken design
  or placeholder text."* None of the four serves that, because a draft cannot
  reach the site: it publishes only by moving into `_food_recipes/` or
  `_cocktail_recipes/` through a PR that meets the `QQ` tests, the two-flag
  gate and the rendered-page tests, with `test` a required check. She closed
  it. This does not reverse #1127 (2026-09-20).
- **2026-10-04, #1194 — a published drink's note must be a filled
  label-and-text pair.** Helen: *"Require a real label"*. Found by auditing
  whether every drafts check has a published-side twin: all did except the
  notes slot, whose docstring claimed a stricter published rule that did not
  exist. `note:` typed for `text:` made a note vanish with no error, and an
  empty label printed under the literal word "note". The rule is
  `test_a_published_drink_note_is_a_filled_pair`, published drinks only, no
  exceptions.
- **Undated — `test_ingredient_notes_are_lowercase_fragments` flags and never
  rewrites.** Helen: *"I'll look at violations myself because I care about
  tone of voice."* A failure is hers to read: the fix is her edit to the note,
  or a word added to `proper_nouns` in `_data/food/taxonomy.yml`, and whether a
  capitalised word belongs there is her call. Do not script a lowercasing
  pass to turn it green.

## §11 Working practices

- **2026-08-12 — a heading lettering change applies to every heading on the
  whole site.** Helen: *"Did your heading lettering change touch all headings
  on the whole site? That is what I want."* A design ruling the old journal
  filed under working practices; the lettering itself is §13's subject.
- **2026-08-12, #131, #128 — the CSS `--modifier` class naming is real BEM and
  stays; the full migration plan is not to be resurrected.** An architecture
  review of that date proposed renaming everything. Eight of the nine
  modifiers checked already had a base class; the ninth, `.ingredient--matched`,
  was a real bug and was fixed on its own. No words of Helen's were recorded.
- **2026-08-16 — Helen is asked each decision as it is hit, not in a batch at
  the end.** Helen: *"Give me decisions to make as you go."* Three rulings
  given mid-way through one piece of work each removed a class of guesswork.
  Bring her the fact that forces the decision ("only 2 of 73 methods have this
  shape" settled a UI in one reply), not the options in the abstract.
- **2026-08-17 — file permissions are never changed without asking Helen
  first, every single time; a yes to one `chmod` is not a yes to the next.**
  Two extracted binaries had lost their execute bit, which is why the JS suite
  had silently not been running. The fix was legitimate and was still hers to
  make, not an agent's, and that is the whole rule. `.claude/settings.json`
  denies `chmod`, `chown` and `sudo`, but Bash cannot be path-restricted by a
  pattern, so the written rule is the backstop. It is why every hook and
  wrapper runs as `python3 <file>` or `sh <file>`: none needs an execute bit.
- **2026-08-18 — never commit or merge onto `main`, in any repo in the tree;
  `guard-main-branch.py` enforces it.** Four commits had landed on
  `_cocktail_drafts`' `main` on 2026-08-17 because the rule read as if there
  were one repo, and two more on the public `main` the next day. The written
  rule was then broken again, so the hook followed on 2026-08-20. It judges
  the repo a leading `cd` or `git -C` points at. It cannot see a push, so
  `git-push-agent.sh` itself refuses any `main` destination on `helen-triages`
  (2026-09-11), and `git-drafts.sh` refuses a commit on a drafts repo's `main`.
- **2026-08-18 — `git reset --hard`, `git checkout --` or `git restore` over a
  dirty tree, and `git clean`, need Helen's yes every single time;
  `guard-destructive-git.py` enforces it.** A `git reset --hard origin/main`,
  run to move a stray commit, wiped a half-finished handover edit: no undo, no
  reflog entry. The rule was written and broken the next day, so it became a
  hook; its first version missed the bare `git checkout <path>` spelling and
  work was lost again within hours, so it asks the filesystem whether an
  argument is a file. It fires only on a dirty tree, and on `git stash drop`
  and `clear` whenever a stash exists. `git stash -u` is the reversible answer.
- **2026-08-20 — the agreed workflow: Claude branches, pushes and opens the
  PR; Helen reviews and merges and nothing else; Claude fetches `main` and
  branches afresh.** Four steps, one of them Helen's, so a session is never
  standing on `main`; the merged branch is deleted first. Step 1 was widened
  on 2026-09-07: Claude opens the PR, and neither the push nor the PR needs an
  ask. Merging has never moved, and opening a PR is not authority to merge it.
- **2026-08-20 — `main` is updated without ever checking it out:
  `sh scripts/git-fetch-main.sh`, then `git merge origin/main`.** The old
  `git checkout main` then `git pull` went after a commit landed on `main` in
  the gap it opens. Its successor, `git fetch origin main:main`, is refused by
  git inside a worktree because `main` is checked out elsewhere: git protecting
  the same invariant, never a reason to check `main` out. The wrapper
  (2026-09-11) fetches over HTTPS, since `origin` is SSH and dies in the
  container, and takes no arguments, because an allow rule for `git fetch *`
  would accept `--upload-pack=<any program>`.
- **2026-08-20 — the branch check before a commit is its own tool call: a
  check that cannot stop the thing it is checking is a narration, not a
  check.** An agent that had read the never-on-`main` rule ran
  `git branch --show-current` in the same shell command as the commit, so the
  answer printed after the commit had happened. Second reason, 2026-09-08:
  `/workspace` is a bind mount, and in one session the branch changed four
  times under a running Claude, none of them its own doing, carrying an
  uncommitted edit into somebody else's branch. The check caught it. So the
  question is also "am I still where I left off".
- **2026-08-20 — never tell Helen to stop, remark on the time, or suggest
  something wait until tomorrow.** A summary had ended "it's half past
  midnight — that's a good place to stop". Helen: *"I am aware of the time. I
  keep my own hours. Please never tell me to stop or go to bed — those things
  are up to me."*
- **2026-08-24 — larger PRs: one PR per sitting, not one per topic, because
  every merge to `main` is a deploy.** Helen: *"I have a soft limit on deploys
  per hour, so I prefer larger pull requests where that's practical."* Refined
  2026-10-10, when sessions were still opening one PR per topic: *"Please make
  larger PRs, as we're soft-limited on deploys per hour."* Four small PRs
  spend four deploys. Gather a session's work for one repo onto one branch,
  keep the topics apart as commits, and say in the description what each
  commit is. Split only where one piece must not wait for another, or she
  asks.
- **2026-08-29 — an issue is closed with a commit trailer, not the API,
  whenever a trailer can do it.** Helen: *"Close #540 (via commit message if
  possible -- this is always my preference)."* A trailer ties the closure to
  the commit that earned it. The API is for where a trailer cannot work: a
  `Fixes DeckOfPandas/helen-triages#N` written in a private drafts repo closes
  nothing and cross-references nothing (measured 2026-08-22 against #335's
  timeline). Either way, name the issues before closing them.
- **2026-08-29 — `/tidy-drafts` fixes a draft's formatting and never a
  judgement, on both sites.** Helen: *"I also want a way of saying hey,
  Claude, please tidy up my drafts files."* Widened to cocktail drafts on
  2026-09-05: *"Widen please — cocktail drafts passing will save me a lot of
  time."* Quoting, `tags` and en dashes reached zero and were adopted as draft
  rules so the backlog cannot regrow. Left out on her call: a missing
  `awaiting_fix`, which is hers to set. Size words joined on 2026-09-24
  (#577), as a scripted move in its own commit (§11). It never touches a `QQ`
  line or a drink's amount: `anitas-attitude-adjuster`'s
  `amount: "Top (30-45) ml"`, with a `QQ` note quoting it, is why.
- **2026-09-01 — a title that differs from its slug is not a finding on a
  draft.** Helen: *"let's not run the 'title matches slug'-ish test over
  drafts."* A draft's title is still the source's (`chocolate-fudge-cake` is
  titled "Cassie's Favourite Chocolate Fudge Cake"), and 19 of the 21 lines
  the pre-flight printed were this.
- **2026-09-01 — a possessive in a recipe title is for the famous and for
  Helen's family only.** Helen: *"I mostly dislike 'Cassie's Sunday Chicken'
  unless Cassie is either famous or a member of my family."* Said while ruling
  that a draft keeps its source's title unflagged.
- **2026-09-02 — the ingest envelope is an issue Helen pastes into the private
  repo herself, titled `ingest: <slug>` and labelled `ingest`.** Helen, on why
  nothing posts it for her: *"I am new to this and quite conservative."*
  `/ingest-inbox` reads those issues; its parser rejects and never repairs,
  and an absent drafts clone is a refusal, not a clean inbox.
- **2026-10-19 — an ingest batch reaches Helen as one review page, with what
  her rulings settle counted rather than asked.** Offered seven ways to cut
  her share of an ingest, she chose four: *"I would like 1, 2, 3 and4
  please!"* So the hand-back list folds every bullet a standing ruling
  settles, but never one that asks (`ingest_inbox.FOLDS`); per-source
  rulings live in `_data/food/sources.yml`; `ingest_review.py` writes one
  table of tags, star, servings and times for corrections only; and a web
  Claude runs `scripts/envelope.py`, the inbox's own parser, before handing
  back.
- **2026-09-07 — pushing a branch and opening its PR need no ask, in all three
  repos.** Helen: *"push no longer needs my say so. I had this rule because
  multiple Claudes were trampling each other and it's easier to fix that
  locally, but I now get Claudes to run Claudes and everything is less
  chaotic!"* The confirmation was never a judgement that pushing is risky; it
  was a lock against parallel sessions fighting over one checkout, and
  worktrees removed the collision. An ask is worth keeping only while the
  thing it guards against is still possible: put that question to any ask
  before proposing another. Merging did not move.
- **2026-09-08 — never `sed`, the whole tool, no safe form;
  `guard-sed.py` refuses any command that names it.** Helen's standing rule is
  "never sed, ever". Her reason, confirmed that day: `sed -i` with a subtly
  wrong regex silently corrupts a file, with none of the visible diff an Edit
  call gives her to review, in a project of hand-curated content where that is
  expensive to notice later. Python in a file does everything sed does. It is
  a hook because a deny rule matches only a command's first word, so `sed` in
  the middle of a pipeline walked past it. Deliberately not clever: it does
  not try to tell a safe sed from an unsafe one.
- **2026-09-08 — every Claude session runs in its own worktree.** Helen:
  *"I'll run Claudes in worktrees going forwards."* `/workspace` is a bind
  mount of her checkout, so a session there has the branch moved under it by
  any other session, or by her, with no signal. An agent was stranded that way
  on 2026-08-16 and an uncommitted edit rode into another branch on
  2026-09-08. Replaces "one agent at a time" (2026-08-16), and is what let the
  push ask go on 2026-09-07.
- **2026-09-08, #852 — a change that spans the public repo and a drafts repo
  merges drafts-first.** A session's practice, not a rule: asked on 2026-10-11
  whether to make it one, Helen said *"it sounds like a good rule, but
  unenforceable, if all not following it does is breaking tests, which is what
  you'd get anyway. I've noted it for myself."* Do not ask again. Public data may name a drafts slug
  (`mood_include` in `taxonomy.yml` is keyed by slug); drafts never name
  public data. A rename's public half merged while its drafts half sat on a
  branch, and Helen's local `pytest` went red. CI cannot see it: the test
  skips where the drafts are absent. Broken the same way on 2026-09-14 (#984).
  The work is finished when both halves are on their `main`s, in that order.
- **2026-09-09 — an `echo` or `printf` never names a secret, the forms that
  cannot leak included; `guard-token-expansion.py` enforces it.** The rule
  against `${TOK:-x}`, which prints the token when it is set, was broken twice
  in one session on 2026-09-08, the second caught by Helen by hand. The hook
  then allowed `${TOK:+set}`, which cannot leak, and she rejected such a call
  anyway: *"I shouldn't have to reject the call!! I'm only human!"* From
  outside it is indistinguishable from a leak. To learn whether a credential
  is there, use it and read the 401 or 403. Helen: *"I can't imagine why we
  wouldn't do that having thought of it."* A guard whose exceptions a human
  must verify has moved the work, not removed it.
- **2026-09-09 — `AGENT_GH_TOKEN` is the only credential, and because it can
  merge, the never-merge rule is held by the rule alone.** Helen deleted her
  own fine-grained token that day: it had become a strict subset of the agent
  account's classic `repo`-scoped one, and its limits were what kept
  generating rules. The cost: a fine-grained token without the permission
  could not merge a PR, and a classic token held by a collaborator can.
  Repository settings, secrets, webhooks and collaborators still need admin
  rights the agent account lacks. Never ask for a wider token or a second one.
- **2026-09-10 — every python, ruby, node or perl program goes in a file,
  however short; `guard-inline-script.py` refuses every `-c` and `-e` form.**
  Helen, 2026-09-09, of multi-line `python3 -c` calls: *"please please please
  write those long lines to files rather than running them all together."*
  Then, prompted by a 78-character one-liner: *"let's figure out how to either
  do that in a safer way, or not need to ask me!"* With
  `blockReadsOutsideWorkingDirectories` on, an inline program asks her at any
  length and under any allow rule, because the checker cannot see into it; a
  file argument is one path. Declined: a length threshold. Three were tried
  (160, 120, 100) and all measured a quantity that does not exist.
- **2026-09-10 — `gh` is called through `sh scripts/gh-agent.sh`, so no call
  names the token.** The earlier shape, an environment assignment in front of
  `gh`, was safe and Helen rejected it on sight anyway: *"Please don't print
  tokens. Is there anything we can do to stop this? If I've misunderstood then
  I apologise."* Safe is not the same as checkable: a command with a secret's
  name in it reads as a leak until someone has run the rule in their head. The
  wrapper deliberately has no check that the credential is present; a first
  draft's check both echoed the name and probed for it. Use it and read `gh`'s
  own 401.
- **2026-09-10 — a Bash command the permission checker cannot analyse is
  refused by `guard-unanalyzable-bash.py`, not put to Helen.** Helen, having
  permitted two calls by hand within minutes: *"can we either avoid needing to
  request permission, or block the command if it can't be statically
  analysed?"* Both halves were built: allow rules for the routine calls, the
  hook for the rest. Who pays is the argument: a prompt is an interruption
  that lands on her, while a denial lands on the session, which writes the
  script and carries on. Her earlier words, 2026-09-08: *"if they take or emit
  variables, please write a script in tmp/"*. Substitution is refused inside
  double quotes too, because the shell expands it there.
- **2026-09-10 — the `gh` wrapper is allow-listed per subcommand, never as
  `gh-agent.sh *`, and `pr merge` and `pr review` are in the deny list.** A
  blanket allow would have removed the last thing standing in front of a
  merge while looking like friction relief, and a deny cannot be overridden by
  an allow. When widening permissions for convenience the question is not
  "what do I want to stop prompting" but "what was that prompt the last guard
  of". The deny also names the dead `.gh-runtime/bin/gh` spelling, pinned by
  `test_merging_and_approving_stay_denied`: a deny on a dead path costs
  nothing, and removing a safety rail is not pruning.
- **2026-09-10 — pushing runs as a separate agent account over HTTPS through
  wrappers; the token is never in a URL and the credential helper never in
  git config.** Cloning and fetching likewise. `origin` is SSH, and
  Helen, 2026-09-08: *"Because you're in docker, I won't give you a GitHub
  host key."* The first HTTPS arrangement put the token in the URL; a clone
  stored it in `.git/config` and a routine `git remote -v` printed it. Helen
  rotated the token. The helper was then configured per repo, which broke
  every other worktree: `/workspace/.git/config` is shared by all of them and
  the script existed on one branch. So each wrapper passes it per invocation.
  Commits stay authored as Helen.
- **2026-09-11 — every PR's base is `main`, never another PR's branch; and a
  PR's `state` is read before pushing to any branch not checked since you last
  looked, your own included.** Two PRs missed the live site in one afternoon.
  #970 was stacked on #968's branch: GitHub retargets a stacked PR only when
  its base branch is deleted, so #970 merged into that branch and #961–#967
  never reached `main`. #960's fix was pushed to a branch whose PR had already
  merged, which accepts the push and delivers nothing. Refined 2026-09-21,
  when Helen merged #1180 mid-session and the session pushed to its own
  branch: merging is hers, so a branch's state can change at any moment.
- **2026-09-11 — a routine call gets a committed wrapper under an exact or
  argument-checked allow rule, never `<tool> *`.** Helen: *"Please work out
  how to run sh commands in a way that can be statically analysed, so things
  remain safe without harrassing me for permissions all the time."* Asking
  what each prompt was the last guard of found three holes before they
  opened: `git-push-agent.sh feature:main` moved `main` with no PR,
  `git clone --template=` runs a directory's hooks, and `git fetch
  --upload-pack=` runs any program. Ask what an option can write as well:
  a `curl` rule was pruned on 2026-09-22 because `-o <path>` writes anywhere.
  `tests/test_agent_wrappers.py` pins every open-ended rule.
- **2026-09-11 — a script in `tmp/` keeps asking Helen; no allow rule covers
  `tmp/`.** Put to her with the fact that the checker sees a script's name and
  not what it does, so such a rule would let unreviewed code read outside the
  project. Helen: *"keep asking me please."* So a `tmp/` script is for the
  genuine one-off, and anything routine earns a committed wrapper. Restated
  2026-09-15: no allow rule for `node`, `sh tmp/...` or the like.
- **2026-09-14, #1008 — the whole recipe pipeline is drawn in one document,
  `PIPELINE.md`.** Helen: *"Basically I want this process to be as smooth as
  possible. We've reinvented this hundreds of ways together recently, which
  is laborious and inefficient."* The process worked; it was spread over five
  documents and three manual sections with no picture of the whole.
- **2026-09-14, #1008 — the drafts staging folders are `1-rewrite/`,
  `2-make/`, `3-keep/`, `4-promote/`, the same four in both drafts repos.**
  Helen: *"I'd like each subfolder to appear in order at the top of my files
  list -- small usability tweak for future-Helen. So shall we try 1-rewrite,
  2-make, and so on?"* Cocktails gained `1-rewrite/` too; asked on 2026-10-11
  why it existed: *"I have the same structure in both private repos, to help
  me keep track of the work."* `3-keep/` is made and liked,
  not being rewritten yet, a state she named herself. Folders, not a flag:
  the flags are what the suite reads and the folders are hers.
  `5-final-proofread/` joined on 2026-09-18 (`PIPELINE.md`).
- **2026-10-11 — `0-not-made/` in the cocktails drafts repo is a temporary
  bucket for drinks Helen has never made.** Helen: *"I'm using this
  temporarily. I will put recipes I have wishlisted in it ... just while I get
  the site up and going, I want a temporary bucket for unmade."* The pool may
  still hold a few unmade ones. Not a pipeline stage and not required by
  `tests/test_staging_folders.py`; its drafts are tested like any other.
- **2026-09-14, #1008 — Claude moves a draft between the staging folders on
  Helen's word: `rewrite`, `make`, `keep`, `ready` or `bin`, followed by a
  slug.** Helen: *"tell me how to tell you I've tried a recipe and want to
  keep it a) and want to rewrite it now and b) don't want to rewrite it now --
  there are a few intermediate states."* This reversed "never move a file
  between these folders unless asked" by making the word the ask. Each move is
  a commit on a branch of the private repo.
- **2026-09-14 — never create issues or PRs in a burst: a batch of issues is
  one issue with a checklist.** Twenty issues and two PRs in under an hour got
  the agent account flagged as spam, and GitHub hid everything it had ever
  written from everyone but itself while its own API listed it all as open.
  Helen said three times that there were no PRs and was twice answered with
  API output. So: believe her first and check the page logged out
  (`sh scripts/github-public-status.sh <url>`). Her ruling the next day:
  separate issues are fine when she asks, one at a time, 10–30 seconds apart.
  Branches are never hidden, so a compare link still opens a PR by hand.
- **2026-09-15 — the account GitHub recorded is read off what a write
  returns, never assumed.** Helen made a new agent account,
  `DeckOfPandas-agentic-claude`, after the first was flagged. Its first PR
  (#1081) came back authored by `DeckOfPandas`: the token in the variable was
  hers until she corrected it, and nothing else would have shown it, because
  GitHub authenticates the token and ignores the name a helper gives.
  `scripts/gh-write.sh` prints `.user.login` for this reason. Equally, a new
  PR number is not evidence the session opened it.
- **2026-09-15 — a command that builds a path at run time gets a committed
  wrapper, not a prompt.** Helen: *"When you want to run commands that build
  paths at runtime, please find a way into scripts that can be statically
  analysed so read/write scope can be checked without asking me."* A session
  had opened PRs through `gh-agent.sh api -X ... -F body=@tmp/...` and checked
  visibility with `curl -o`; the `@` read and the `-o` write are invisible to
  the checker, and `api` is also the door to a merge, so no allow rule could
  cover them. Hence `gh-write.sh` (three writes, a body under `tmp/`, base
  `main`, the three repos), `github-public-status.sh` and `check-link.sh`
  (#1431: one https URL or one localhost one, body to `/dev/null`).
- **2026-09-15 — never `awk` (nor `gawk`, `mawk`, `nawk`); `guard-awk.py`
  refuses them as command words.** Helen's README draft listed "Never `awk`
  (same)" under "Never `sed`" and nothing enforced it. Asked whether she
  should have a hook: *"I feel like I should"*. The reason is stronger than
  sed's: awk is an interpreter whose program arrives inline, the opacity
  refused for `python -c`, and inside it `print > "file"` writes, `system()`
  runs anything and `gawk -i inplace` edits in place. Use Python in a file.
- **2026-09-15 — every Bash `description` says what the call reads or writes
  and where, because a prompt nobody reads guards nothing.** Helen pasted back
  a prompt on an allow-listed wrapper and said she had *"stopped reading them
  in the name of a quiet life."* Measured with her: a quoted `[`, `]` or `|`
  in a wrapper's arguments makes Claude Code ask, since it reads as a computed
  path. So `gh-read.sh --fields` and `--each` build the jq inside the script,
  and the hook refuses a quoted `[`, `]` or `|` given to `sh scripts/...`.
  Not measured, so not refused: the same characters quoted in other commands.
- **2026-09-15 — a leading `NAME=value` before a command is refused by the
  hook, and committed wrappers make it unnecessary.** A session set two
  variables in front of `node tmp/repro.js`; the checker could not tell what
  the rest would do and asked. Helen: *"I want to reduce the number of
  interruptions to a minimum."* Offered an allow rule for the exact prefix, a
  refusal, or a refusal plus more wrappers, she picked the third.
  `scripts/browser/` gained `styles.sh`, `gaps.sh` and `click-crop.sh`, which
  source `env.sh` themselves. Declined: any wrapper that runs arbitrary code
  from `tmp/`. `git -c key=value` and `--flag=value` are not leading
  assignments and pass.
- **2026-09-15 — an unquoted `(` or `)` in a Bash command is refused by the
  hook.** A `git log --format` with `%(trailers...)` unquoted could not be
  parsed, so the checker put it to Helen; she declined it and asked *"Can we
  do anything?"* An unquoted parenthesis is a subshell or a parse error, never
  an ordinary argument, so refusing it costs nothing. Quoted or
  backslash-escaped, it passes.
- **2026-09-15, #1112 — on a PR the agent account opened, the PR description
  closes the issues, not the commit trailers: one closing keyword per issue
  per line, never a comma list.** PR #1100's description ended with one
  `Fixes` and ten numbers, and ten commits carried their own `Fixes #N`. Helen
  merged it and only the first number closed. A keyword covers the one
  reference after it; and the commits' keywords closed nothing, where the
  same shape had closed an issue through a PR Helen opened. PR #1113, with a
  `Closes #N` per line, closed all 22. Keep the trailers for the history, and
  read the issue list after the merge.
- **2026-10-21 — dev servers are shared work: a session starts one when
  Helen asks, from its own worktree, and says the URL she can open.** Helen:
  *"I'm trying a new model where I interact with git at the command line as
  little as possible, so I don't keep getting tangled up... Let's work
  together on dev servers from now on."* It replaces 2026-09-18's *"I start
  my own local servers, so don't do that."* A server on a port the container
  does not publish (`scripts/browser/serve.sh`'s 4010 and up) is for a
  session's screenshots, not for her: say the host port, not the inside one.
- **2026-09-21 — the file tools may read `/workspace/.node-runtime`, and
  nothing may write there.** Helen: *"Reading /workspace/.node-runtime is
  fine, please modify your settings to allow it."* A `Read(...)` allow rule
  was tried first and does not override `blockReadsOutsideWorkingDirectories`,
  so the grant is `additionalDirectories`, which widens read and write, plus
  an `Edit(...)` deny to narrow it back. A settings edit does not reach a
  running session: `/add-dir` does. The deny is documented, not measured
  (#1191, 2026-09-24): worktree isolation refuses the write first, and testing
  further would mean writing into her Node runtime.
- **2026-09-21 — `Read(//dev/null)` and `Edit(//dev/null)` stay in the
  settings.** Helen added them on 2026-09-15 after a `curl -o /dev/null`
  prompted her: *"add to your settings that it's fine to access."* A session
  later ran the Read tool on `/dev/null`, was refused, and called the pair
  inert. Helen: *"Claude can read and write to /dev/null, so retain whatever
  means that."* They serve Bash's static path analysis (a redirection, an
  `-o`), which the Read tool's block never touches. A permission rule and a
  permission block are different mechanisms; exercising one says nothing
  about the other. They are exact paths because `/dev` holds real devices.
- **2026-09-21 — `git -C <path>` is refused wherever it appears; write the
  bare command.** Helen: *"There's no need to run git -C for commands like
  that because you're already in the folder you're targetting"*, then *"Also,
  yes, please refuse git -C across the board"*. An allow rule is a prefix
  match, so `git -C /path status` matches no rule and every such call
  interrupted her, the same cost as a leading `cd`. Lowercase `git -c
  key=value` is a different flag and must pass: every `git-*-agent.sh` hands
  git the credential helper that way.
- **2026-09-21 — Claude runs only in the container, never on the host.**
  Helen: *"Claude always runs in a container, never on the host (any more).
  This will be my setup indefinitely."* So allow rules naming host-only paths
  (`.gh-runtime/`, `.node-runtime/` binaries) were pruned; `gh` and `node` are
  at `/usr/bin`. The matching deny rules were left on purpose.
- **2026-09-22 — `CLAUDE.md` holds the rules and this journal holds the
  reasons.** Helen: *"Can we move parts of CLAUDE.md to other docs?"*, then
  *"please do this next."* It had reached 56,637 bytes, loaded into every
  session, and most of it was each rule's history. The test that decides every
  case: where a hook enforces a rule, `CLAUDE.md` keeps the rule, the hook's
  name and the one non-obvious carve-out; where only discipline enforces it,
  the paragraph is the enforcement and stays whole.
- **2026-09-22 — no test is written to fail when the private drafts clones
  are absent; the suite reports the gap at the end of the run.** Helen,
  refusing a sentinel test: *"I don't want to run tests locally with the
  expectation that some will fail, because a suite with failures starts to
  get ignored...plus it's very annoying."* Her second reason: drafts are
  legitimately unfinished until she has cooked from them, *"this isn't worth
  doing if the recipes turn out to be naff"*, so their untidiness is not a
  defect. `conftest.py` names each absent clone with the command that fetches
  it, and is silent when both are present.
- **2026-09-24, #1078 — an agent may correct or delete a recipe note that a
  later ruling of Helen's has made false.** Two notes still called a bottle
  different after she had ruled it the same, so the page printed her own
  ruling's contradiction, and the mechanical pass never touches a note's
  words. Helen: *"#1078: yes."* The boundary is the ruling: name it in the
  commit. A note she has not ruled on, or a `QQ`, stays hers.
- **2026-09-29 — `/opt` may be read, never written, and only Helen can make
  the grant live.** Helen: *"Reading from /opt is fine, please add that to
  your settings."* The image's Playwright lives there. A deny on edits under
  `/opt` went in, but adding `/opt` to `additionalDirectories` was refused by
  Claude Code as self-modification, so a session cannot widen its own read
  scope even on her word. The line is hers to add, or `/add-dir` in a running
  session.
- **2026-09-29 — every other worktree under `/workspace/.claude/worktrees/`
  may be read, and nothing in one may be written.** Helen: *"Fine to read
  from other worktrees."*, and again on 2026-10-04: *"You're allowed to read
  from other worktrees."* A helper's screenshots and scratch scripts live in
  its own `tmp/`, and a supervisor that will not open them is reporting work
  it has not looked at. The folder is in `additionalDirectories`, and a
  worktree session has been refused the read all the same: that is the
  mechanism lagging the rule, so ask her for `/add-dir`.
- **2026-10-02 — git inside a drafts clone goes through
  `sh scripts/git-drafts.sh <dir> <verb>`, a fixed list of verbs.** With a
  leading `cd` and `git -C` both refused, a drafts pass had no sanctioned way
  to branch or commit there, and a `tmp/` script asked Helen on every call.
  Shown that, Helen: *"gotcha, thanks. Yes please do it."* Each verb is
  narrowed to what its prompt was guarding: `diff` takes five named options
  (`--output=` writes anywhere), `checkout` only `-b <new>`, and `commit` is
  refused on that repo's `main`, which `guard-main-branch.py` cannot see.
- **2026-10-02 — this repository takes no outside contributions: a stranger's
  PR is not merged, and the fix ships from the agent account.** Seven minutes
  after #1273 was raised, an unknown account opened #1274 from a fork with
  "Fixes #1273". Helen: *"I love some community, but this repo was only ever
  intended to serve me, and I don't want to keep track of a community at the
  moment."* Every public issue is an invitation, so anything about the
  workflow or security is better raised as a PR, or not publicly. Approving a
  fork's run executes the fork's code. Restricting PRs is a repository
  setting, so hers.
- **2026-10-10 — `$[` outside single quotes is refused by the hook: write a
  regex in single quotes.** A read-only grep with a double-quoted regex, a
  character class after a dollar, was read as shell arithmetic and put to
  Helen. She declined it and asked *"Can we adjust settings to allow
  non-scary requests of this sort?"* Settings cannot: an allow rule is not
  consulted for a command the parser has given up on. So it is refused, and
  the cost lands on the session. `${...}` was not measured and is not refused.
- **2026-10-11 — the journal, the manual and code comments are
  delete-and-replace, never append.** Asked whether old journal entries may be
  deleted and replaced, Helen: *"Through this whole project I have begged to
  delete and replace rather than just append! Please please please do it!"*
  The journal had been append-only, so a reversed ruling stayed beside its
  replacement and a session that landed on the old one applied it. One short
  entry per live ruling; when a ruling changes, replace its entry. The old
  text is in git history. Replaces the old convention that a superseded entry
  and its successor both stay.
- **2026-10-11 — Helen promotes a recipe herself, or asks Claude to; Claude
  never decides a file is ready to promote.** Helen: *"Either I promote
  myself, or ask Claude to. Claude never decides a file is ready to promote and
  moves it to the published repo."* `PIPELINE.md` and
  `PUBLISHING_A_COCKTAIL.md` had given opposite defaults.
- **2026-09-03, #672 — the ingest inbox's outcome comment carries the
  browser's hand-back list, as bullets.** Helen: *"Bullets too please."* The
  comment `scripts/ingest_inbox.py` leaves on each envelope's issue states the
  outcome, the notes and then every item the browser session handed back, one
  bullet each, so the issue is where she reads what still needs her.
- **2026-09-15, #1080 — the drafts staging folders exist in both private repos
  even when empty.** Helen: *"These folders should always be present even if
  they don't contain any drafts."* Git keeps no empty folder, so each holds a
  `.gitkeep`; `tests/test_staging_folders.py` fails if one is missing. Do not
  delete a `.gitkeep` as clutter when a folder fills, and do not remove a
  folder because it is empty.
- **2026-09-24, #577 — the size-word move on drafts is scripted, lands as its
  own commit in the drafts repo, and the diff of that commit is Helen's
  review.** Her option 1: *"script it with a hand-review of the diff, one
  commit, before promotion"*. `/tidy-drafts`'s `size` rule moves "large" from
  `item:` to `amount:` only where the published rule would demand it; what it
  refuses is reported, never rewritten. (Replaces "left out on her call: size
  words", 2026-08-29.)
- **2026-09-21 — a SessionStart hook tells every session where it is before it
  assumes.** Helen: *"Yes please let's do this."*
  `.claude/hooks/session-ground-truth.py` reports the checkout's path, the
  branch, the count of uncommitted changes, the position against `origin/main`
  as last fetched, and whether the two drafts clones are present. `/workspace`
  is a bind mount, so another session switching branch moves the ground with
  no signal. It makes no network call and never blocks. It reports; it does
  not replace the branch check before a commit.
- **2026-09-21 — the two private drafts repos may be cloned into a fresh
  worktree whenever wanted, with no ask.** Helen's standing grant; her words
  were not recorded. Cloning is reading, and both folders are gitignored here.
  `sh scripts/git-clone-agent.sh <repo> <dir>`; never a symlink. Without the
  clones most of the suite is never collected and reports green, which is why
  the session-start hook names an absent clone and prints the command.

### §11.2 The record of this file being wrong

- **2026-08-31, #600 — a claim copied into an issue or a document is
  re-measured first, not carried over.** #600 copied another issue's "also
  outstanding" list four days on without checking it, and every claim in it
  was by then false. Helen: *"I saw Kamaniwanalaya and Swizzle and felt
  annoyed again — have we not settled this? Now three times or more?"* An
  instruction to verify is not verification, and when a document and the code
  disagree the code wins and the document is fixed.

## §12 Traps — the stories

- **Undated (by August 2026) — rejected tooling: `jekyll-seo-tag`, Stylelint,
  a bundler, a CSS framework, schema.org/Recipe.** Each was offered and
  declined. The one reason recorded: schema.org/Recipe would push adapted
  magazine recipes into Google's rich results. Anyone proposing one again
  argues against that, not as though it had never been asked. #259, a lint for
  bare element selectors, was likewise opened and closed rather than
  half-built.
- **2026-09-12 — a red `main` is a deploy outage: the merging session checks
  the run, and nobody merges over a known-red suite.** PR #996 un-proofread
  two recipes that two live recipes linked to, said in its own message that
  the link test would go red, and merged. The suite gates the deploy, so about
  twenty merges over three days shipped nothing, and the only signal was an
  Actions email. Found 2026-09-15. The honest options were to hold the two
  links back in the same PR or to proofread the two recipes there and then.
  `sh scripts/main-ci-status.sh` exists so the check costs no prompt. The
  instruction itself then sat on an unmerged branch for seven days, which
  Helen found: *"I think I might have lost work (well, not merged it)"*.
- **2026-09-16 — an agent's worktree is Helen's to keep; never remove one.**
  Offered the removal of four agent worktrees under `.claude/worktrees/` whose
  branches had merged: *"Leave the worktrees -- I may well want to go back and
  look."* They hold the scratch scripts, measurements and screenshots a helper
  worked from, which the merged branch does not. So `git branch -d` refusing a
  branch that a worktree holds is permanent and is not a problem to solve.
- **2026-10-04, #1281 — a workflow file is an ordinary PR; the Actions
  settings, secrets and rulesets stay Helen's.** Helen: *"I've added workflow
  permissions to your GitHub token, so please also look at #1281"*. That
  replaces *"Leave the rest for now please"* (2026-10-02) for this file and no
  further. The PR it licensed: pull-request runs left the `pages` concurrency
  group for `pr-<number>`, so a PR can no longer cancel a waiting deploy
  (three were lost that way on 2026-10-02), and `build` runs beside `test`
  with `deploy` needing both, the same gate about two minutes sooner. Parse
  the YAML before pushing: an invalid workflow blocks every merge, the fix
  included (2026-09-28, thirty-nine minutes).

## §13 The visual design

**§13.1 The mark.**

- **2026-07-31 — the recipe page's device is one identical repeated mark (the
  double rule), not watercolour washes.** An identical repeated mark is
  recognised, not read. The index was brought onto the same mark on 2026-08-01.
- **2026-09-04 — on a heading that wraps, the mark goes under the last line
  only.** The design audit's critical #7; `assets/js/last-line-rule.js` finds
  the rendered last line.
- **2026-09-24 — IF YOU LIKED THIS is a first-level heading and wears the mark,
  like INGREDIENTS and METHOD.** Helen: *"If you think IF YOU LIKED THIS should
  join INGREDIENTS and METHOD at first level then yes, okay, I hear it, please
  do it."* No new hue; it is a sentence, so it takes the last-line variant.
  Replaces the "has not earned one" argument that stood from #927.
- **2026-08-02 — a section heading inside a recipe's long-form body is a peer
  of INGREDIENTS, METHOD and NOTES, with the same class and mark.** Helen: *"I
  can imagine TIPS and TROUBLESHOOTING being peer headings with INGREDIENTS
  etc. I think that would cause the least jar."* Written in the body as `<h2
  class="recipe-section-heading">` round a `.section-heading-text` span; a
  bare `## Heading` gets a fallback only.
- **2026-08-12 — the single violet rule sits exactly where the double rule's
  lower bar sits, at the same thickness and drop.** Helen, of a thinner,
  higher bar under the failure names in a long-form section: *"the violet
  underline is crushing the headings"*. `overlapping-rule-single` in
  `_sass/shared/_rule.scss` takes every number from the double mixin, so the
  tiers are one mark and move together. On food it takes violet, never
  magenta, which means "interactive" there.
- **2026-08-13 — a page type changes the mark's top bar only: yellow on the
  about page's FAQ heading, lime on a reference page, both over the shared
  violet.** Helen, withdrawing a cobalt under-rule tried the day before: *"I
  love colour, but even I need to accept that adding the cobalt was too
  much."* Of lime on the reference pages: *"just for a suggestion of own
  identity"*. Neither is a new hue: `$color-blazing-banana` and
  `$color-wild-wasabi` are index section roots. The about page's own list
  marks are violet.

**§13.2 The colour budget.**

- **2026-08-02 — a cross-recipe link is magenta, not a fifth hue.**
  `$color-vivid-rose` was tried for links and reverted the same day at Helen's
  ask: magenta measures 5.26:1, and cohesion with the title rule won over
  distance from the footer hearts.
- **2026-08-03 — the annotation arrow is violet's second job.** It is the
  quiet, structural colour, which is what an annotation mark is; no hue was
  added for it.
- **2026-09-07, #651 — `$color-electric-absinthe-wash` is kept though nothing
  reads it.** A session's call, not Helen's ruling: it is one of five `-wash`
  values derived as a set, and deleting one makes the set look arbitrary. What
  #651 forbade was it sitting there unread AND unexplained, so it carries a
  comment.
- **2026-09-25 — the recipe page keeps all thirteen devices; do not propose a
  smaller number.** Helen, shown the Moules and Hollandaise pages at thirteen,
  eight and five treatments: *"all 13 I'm afraid, I really did try to like
  EIGHT, sorry."* The count of devices is a decision the way the count of hues
  is. Eight flattened the metadata box, the mono source line and the tinted
  note boxes; five also dropped the highlighter, the pills and the stepper.
- **2026-08-14, #199 — a recipe link's hover goes lighter, to the raw magenta,
  at 3.24:1 on the page ground.** That is under the 4.5:1 body floor, and
  Helen accepted it with the contrast figures in front of her because a hover
  is transient; no words of hers were recorded. `$color-recipe-link-hover` is
  `$color-dazzling-dragonfruit`, and the resting link is that hue darkened
  12%.
- **2026-09-04 — food's five section hues are in Helen's order: pink, lime,
  cerulean, orange, yellow.** Her tests: pink first; no two blues adjacent;
  star, mood and practicalities accessible and good together; not a rainbow's
  order (*"to avoid a rainbow"*). Yellow is I KNOW WHAT I WANT: *"so the
  aureolin is the I KNOW WHAT I WANT -- visible, important, and pleasingly a
  yellow highlighter over the recipe titles when they're hit, which feels
  familiar."* Cerulean and lime then swapped places. The `$color-*-root` block
  in `_sass/food/_palette.scss`.
- **2026-09-04 — cobalt is deleted and food's LEAVE OUT spends no hue.**
  Helen: *"we'd drop the cobalt, and drop the colouring on 'leave out', like
  we do for the cocktail site. It could retain its violet perhaps."*
  `$color-exclude-active` is `$color-clear-text`, and only the violet
  structural rule under the heading is left. Food has five section hues, not
  six.
- **Undated — the short-method box's tint is deliberately stronger than the
  meta grid's and the notes' wash.** Helen: *"it's just very faint... darken
  it enough to see easily."* `$method-short-tint-opacity` is 0.08 in
  `_sass/food/_recipe-header.scss` against `$box-tint-opacity`'s 0.03; do not
  fold the two into one dial.

**§13.3 Spacing.**

- **2026-08-01 — every gap comes from a named scale.** Sixteen distinct gaps
  collapsed to `$spacing-block-gap` (1.75rem), `$spacing-section-gap` (3rem)
  and `$spacing-section-top` (4.5rem) in `_sass/shared/_tokens.scss`.
- **2026-09-14, #1006 — a drink page's section headings sit 3rem / 1.25rem,
  half way to food's scale.** Helen, from three candidates on the real page (as
  it was, half way, food's 4.5rem / 2rem): *"half way, BUT with a little extra
  space between the make it read it line and the rule above it."* The gap was
  re-checked in #1093's spacing review and left alone because it is ruled.
- **2026-09-15, #1093 — on both indexes the gap from the bottom clear-all to
  "N survivors" is cocktails' (about 60px).** Helen, given 24px on food and
  about 60px on cocktails as numbers: *"Food matches cocktails"*.
- **2026-09-15, #1093 — a page with no back arrow starts 32px down.** Helen,
  given 48px on the food reference pages and about against 32px on rum
  categories: *"All at 32px"*.
- **2026-10-10, #1325 — INGREDIENTS on a food recipe sits `$spacing-section-top`
  under the head's hairline.** Helen: *"there's too much space under the
  metadata section for food recipes"*. The value is the session's reading of
  that sentence, not her pick. It replaces #1124's 6.55rem, which matched a
  drink page's distance — but a drink page has its controls row in that
  distance and food has had nothing there since #1210. On a phone the shortlist
  pill sits `$spacing-block-gap` under the line.
- **Undated, #94 / #55 — every method step takes the same indent whether or
  not the recipe has method groups, with real space before a group heading and
  after one.** Helen: *"when there are no ingredient group headings, the
  numbering should be at the same level of indentation as when there are."*;
  *"more space between the steps in a group and the next heading"*; and of a
  heading and its first step (#55), *"too cramped/close"*. The numerals are
  the plain body face, not the group headings' stroked Courier: *"confusing
  with the group headings"*. `$method-group-step-indent` in
  `_sass/food/_recipe-ingredients-method.scss`; the phone values are #964's.
- **Undated, #339 — a subtitle under a peer heading sits close under it, and
  the gap below it is `$space-xl`, not a tagline's 3rem.** Helen: *"so it
  reads like a tagline, not the first line of content."* Of the gap below: *"I
  think it's retaining the same gap as under the rest of the page's headings,
  but it isn't a heading so this gap feels like a yawning chasm."*
  `.recipe-section-subtitle` in `_sass/food/_recipe-notes-body.scss`.
- **Undated — the short method takes the long method's vertical spacing, so
  toggling does not move the top line.** Helen: *"clicking between the long
  and short methods means the top line jumps around... use the same vertical
  spacing for the short method as for the long method."* `.method-short`'s
  negative top margin cancels its own padding; change it and `.method-full`'s
  top margin together.
- **Undated — an empty LEAVE OUT pill row reserves no space above the recipe
  list.** Helen: *"reduce the amount of vertical space between LEAVE OUT and
  the recipe list."* In `_sass/food/_search.scss` the row's space is gated on
  the row having something in it, the same construction as the search pools'
  `:not(:empty)` margin.

**§13.4 The index page.**

- **2026-08-03 — the index has no category-code bar.** Removed after four
  rounds of tuning; do not rebuild it.
- **2026-08-03 — a chosen filter does not wear the emboss.** Helen took it off:
  the punched treatment means "landmark", and a filter's colour lives in its
  shape. She asked again on 2026-08-12 (*"I could argue it either way"*) and
  the answer stayed no. Tag text carries no raised emboss at all, no shadow
  and one flat stroke width for every category: *"we're fighting the raised
  font in our tags, and we're losing."* (2026-08-03.)
- **2026-08-30, #583 / #586 — the food pickers are named for what they ask and
  LEAVE OUT is always on the page.** HAS TO HAVE replaced `SEARCH MAIN
  INGREDIENTS`, which named the mechanism; LEAVE OUT came out from behind its
  reveal link, because the framing was the only thing the disclosure bought.
  Helen (#586): *"has to have then leave out on the same line"* and *"'leave
  out' always visible, so delete the show/hide button."* The two sit in one
  `.search-pair`.
- **2026-08-30, #562 — the list carries no chips about how finished an entry
  is.** Helen asked for "all metadata chips" off the rows: *"I am perfectly
  well aware of how much work I have done on each drink"*.
- **2026-09-04 — the food index has no "the universe says…" line.** It was on
  food for two days. Helen: *"This advice was the only part of the design
  review I disagreed with. Having all the dolly mixture colours visible
  together and first thing pleases me. I don't think anyone (and certainly not
  me) opens a triage website to click on a random recipe. And given the styling
  is hard, my gut says that trying to polish it is solving the wrong problem."*
- **2026-09-06 — the food index has no META FILTERS block.** Helen: *"I don't
  want this block on the index page any more. It was useful when I was still
  ingesting recipes I know, but it's not now I've done most of that."*
- **2026-09-15, #1050 / #1057 / #1059 — a link that arrives at a filtered index
  lands on what it filtered.** Helen: *"load the index page filtered as
  appropriate, with the screen snapped to the returned recipes (so don't have
  to scroll down)"*. Search results and "see shortlist" end in `#results`; a
  badge or chip on a page ends in its section's id (`#filter-star`,
  `#filter-mood`, `#filter-practicalities`, `#filter-hassle`). Both indexes
  scroll to `location.hash` after their reveal, instantly, not smoothly.
- **2026-10-08, #1288 — the I KNOW WHAT I WANT sections stay.** Helen: *"The I
  KNOW WHAT I WANT sections should probably go, but I'm not ready to drop
  their colours from my palette, and I am the main/only user here, so they
  stay!"* She then preferred their live filtering to a search box:
  *"cuter"*.
- **2026-10-11, #1219 — both indexes wear one filter chip: cocktails' type on
  food's torn tape.** 0.9rem bold lowercase at full strength; the tape is 15%
  of the text colour at rest. Helen, from six treatments: *"I'm leaning towards
  F -- cocktail chips, and tape on both sites! I do know this was supposed to
  be an exercise in editing...but at least the sites will be consistent now
  even if I'm leaning even further into more is more"*. Replaces cocktails'
  *"just not the background shape"* (2026-08-30), its underline and its filled
  block (#1086). Each site keeps its own colours. The artwork is one shared set
  in `assets/img/chrome/tag-shapes/`.
- **2026-10-11, #1219 — a chip under the pointer or chosen takes its section's
  hue on the tape; the hovered word is a dark of that hue, the chosen word is
  black.** Helen, on seeing a 40% ink hover: *"the darkened text on the
  darkened tape is hard to read, plus I'd just like some more colour. I like
  the hover behaviour we use for the chips on the recipe list below, so please
  match that"*; for cocktails, *"the same"*. On cocktails the dark is the hue
  mixed 20% into the ground, and #1086's filled block stays only as a fallback
  behind `:has(.tag-shape svg)` for when the artwork has not arrived.
- **2026-10-11, #1219 — nothing chosen changes case, on either index.** Helen:
  *"Let's stop capitalising selected search result tags, both sites please."*
  A matched row badge on food lost its capitals too and keeps its muted colour,
  its 0.75rem and its faux-bold: *"I think it's right that the colour stays
  muted, but yes, please take off the capitalisation on hit."* The title-search
  hit still goes to capitals; that was her own ask.
- **2026-10-11, #1219 — food's index section headings are 1.4rem, cocktails'
  size.** Helen: *"Please increase the size of food's headings to match
  cocktails' as well, because they're a bit lost amongst the newly chunky
  chips."* Size only: cocktails' weight 400 and 0.14em tracking are #680's
  corrections for light type on a dark ground. Replaces the 1.05rem of the
  2026-09-02 fold tightening.
- **2026-10-11, #1219 — cocktails' HAS TO HAVE and LEAVE OUT pools take ALL
  their styling from food's, from the same code.** Helen, correcting a literal
  first build: *"I would like the cocktail has to have and leave out search
  results to take all their styling from food's ... (can we reuse the code? if
  not then why not?) ... no outline or underline at rest, all of it. Same for
  leave out."* When she says match she means all of it; do not ration it
  against an older ruling. Four mixins in `_sass/shared/_rule.scss`
  (`index-chip`, `-word-match`, `-chosen`, `-struck`). A HAS TO HAVE hit is hot
  magenta, untuned at her word. Cocktails keeps the "(via)" bracket.
- **2026-10-11, #1219 — a LEAVE OUT hit is the base grey, heavier, on both
  sites.** Helen: *"hit search results should be a normal base grey (just
  heavier for hits, as currently), rather than taking their colour from the
  section."* Both pickers still mark a hit (#390); only HAS TO HAVE spends a
  hue. Replaces the borrowed HAS TO HAVE tone of 2026-09-04.
- **2026-10-11, #1219 — food's chosen LEAVE OUT pills sit above the
  candidates, as cocktails' do.** Helen: *"retains selected terms at the top of
  the list when further searches are made, which I prefer"*.
- **2026-10-11, #1219 — every clear and clear-all, on both sites, is the text
  colour and goes magenta under the pointer.** Helen: *"I'm fed up with the
  clear and clear all buttons! Please show each one in normal link colours, so
  not derived from the section colour. Normal base text, site colour on hover
  (both woo woo)."* One mixin, `index-clear-link`. Replaces food's per-section
  clear colours and cocktails' grey of 2026-09-02.
- **2026-10-11, #1219 — cocktails' ingredient pickers answer from the first
  character (`min_query_chars: 1`).** Helen: *"Mostly because I think this is
  very very cute in a static site, but also because seeing a list provides
  inspiration."* Replaces #584's three characters.
- **2026-10-11, #1219 — cocktails' pools are not capped and say no "+N
  more".** Helen: *"I don't want to have the 'N more' behaviour for cocktails
  -- please remove it. It's helpful to see the list when e.g. rum has so many
  results. (Plus super cute, as I said!)"* `pool_cap` (8) is gone from the
  data, the module and the page; one letter offers about fifty chips.
- **2026-10-11, #1219 — choosing a HAS TO HAVE candidate on food clears the
  search, and the chosen chip carries an ×, as on cocktails.** Helen: *"when a
  chip in the has to have or leave out search results is selected, it
  immediately joins others at the top and the other chips disappear. Please
  make food do the same"*; *"I do want to have the x on the chosen has to have
  chip, so please add it for food."* This trades away #1092's picking several
  from one search; the requirement is still AND. Helen asked whether it was a
  regression and was told it was #1092 as built.
- **2026-10-11, #1219 — the index panel does not fold on a phone; do not offer
  it again on the grounds that the panel is tall.** She chose *"sections fold"*
  from four treatments on the 10th, then: *"I'm afraid I've changed my mind: I
  don't want to fold the sections. The site is for me, and on my iPad I can see
  everything at the same time just fine, which is what I want. It's even fine
  on my phone too, honestly."* Also declined: three boxes on one row (*"nice
  looking, but I don't think it's clear enough"*); on 2026-09-02 a "more" link,
  a side rail and a strip of random rows. The build is on
  `design/1219-phone-fold`.
- **Undated — the search box's clear link is shown and hidden with
  `visibility`, never `display`.** Helen: *"the clear link appears cutting off
  the field rather than to the right of it"*. Toggling `display` adds and
  removes it from the row, so the field changed width as it came and went. Its
  space is reserved beside the field at all times. `filters.js`.
- **Undated — a title search highlights only the part of the title that
  matched, in the tag styling, and the hit wears one fixed shape.** Helen:
  *"could the part of the title hit gain the orange background and scratchy,
  capitalised lettering."* The shape is `tag-shape-6`, chosen by her on
  2026-08-04 for being *"slightly less square at the ends."* A hit is whatever
  is typed, so it has no stable text to hash. Its capitals survive #1219.
- **Undated — a tag's torn-tape shape is chosen by a hash of its own text,
  never at random or by position.** Helen: *"this will give some visual
  stability between the filter section and the recipe list section"*. The same
  tag wears the same shape as a filter button and as a pill on a row.
  `pickShape` in `decorations.js`; since #1219 it serves both indexes.
- **2026-08-03 — the tag-shape pool is the original shapes without their
  mirror images; shape 8 is out, and `tag-shape-2` is stretched on long
  text.** A row mixing a shape with its flip at random was, in Helen's word,
  *"drunken"*. Shape 4 keeps its flip, being torn at both ends; shape 8 is too
  diagonal. `tag-shape-2`'s torn corner was fine on "duck" and not on
  "make-ahead", so text over six characters gets `tag-shape--stretch`. The
  unused files stay in `assets/img/chrome/tag-shapes/`.
- **Undated, #562 — a `draft` row badge is styled exactly as the `magic bag`
  badge.** Helen: *"styled exactly as 'magic bag' which is already in place"*.
  It is the one work-state mark #562 left on a row, and it is a badge, not a
  filter: it writes no row attribute. `.badge-draft` and `.badge-magic-bag`
  share their rule in `_sass/food/_badges.scss`; do not give `draft` a hue of
  its own.
- **2026-08-03 — badges and filter chips sit on a torn-tape SVG shape, not a
  grey polygon.** Helen: *"the grey shapes... don't really look like anything
  in particular... hastily broken old-fashioned highlighter tape"*. The
  clip-path polygon survives only on the two marks that say what a row IS
  (`_sass/food/_badges.scss`); every tag takes a `.tag-shape` slot, and since
  #1219 the artwork is one set shared by both sites.
- **2026-08-03 — the index search row is 620px wide, both inputs on a row end
  at the same place, and the heading has a little space after it.** Helen, at
  550px: *"cut off even before typing anything -- it ends at the first '.'"*;
  *"it would look tidiest if both search input fields ended in the same
  place"*; *"A little space after the heading"*. The clear button reserves its
  space at all times and that comes out of the input's share:
  `$index-search-max-width`, and `min-width: 0` on the input.
- **2026-08-19, #389 — a chosen filter chip may not change width.** Helen:
  *"filter tags to the right of a selected one move to the right -- they
  should stay in the same position."* The chosen state declares nothing that
  re-measures the button: weight 900 is safe only because Courier Prime ships
  nothing above Bold, and the extra weight is a stroke. The same rule binds
  every control on both sites; the cocktail scaler's step buttons cite it.
- **2026-09-10 — filter sections on an index sit `$index-section-gap` apart,
  more than the gap inside a section.** Helen: *"I'd like more vertical space
  between filter sections on the index page."* And *"especially between the
  search input fields and the heading below."*: on a phone the stacked search
  pair takes a step more than the section gap beneath it. One token for both
  sites in `_sass/shared/_tokens.scss`, and deliberately not
  `$spacing-section-gap`: an index is a control panel, where every section
  should be visible at a glance. Phones take a further step (#999).
- **Undated, #586 / #901 — HAS TO HAVE and LEAVE OUT sit side by side, stack
  at 720px on both sites, and on a phone each search heading has its input
  beneath it.** Helen: *"has to have then leave out on the same line"*. Of the
  two sites' different stack widths, 2026-08-30: *"the cocktail version is
  correct."* (`$index-stack-width`, one number, so no width has one site
  stacked and the other not.) #901: *"stack HAS TO HAVE with its input field
  below it for narrower screens, and same for LEAVE OUT and I KNOW WHAT I
  WANT."*
- **Undated, #403 — a LEAVE OUT candidate darkens on hover, as every other
  section's does.** Helen: *"should darken not lighten on hover, same as for
  the include filter"*. `$color-exclude-hover` is darker than
  `$color-exclude-active` on purpose: a matched candidate already rests at the
  active tone.
- **Undated — tag-shape-2 is stretched 10% on long tags only.** Helen: *"the
  way the shape rolls off along the top left corner bothers me every time"*,
  then, of a larger factor, *"too square, sorry, Goldilocks"*.
  `.tag-shape--stretch` is `scaleX(1.1)`, added by `decorations.js` above its
  `SHORT_TEXT_MAX`. It moves the torn corner nearer the edge; more than that
  flattens the shape.
- **2026-08-03 — a search row's heading never wraps; the input absorbs the
  squeeze.** Helen reported the label breaking onto two lines ("search main" /
  "ingredients"); no words of hers were recorded. The label is pinned at its
  natural width by `@mixin index-search-row` in `_sass/shared/_rule.scss`. On
  a phone the heading takes a line of its own instead (#901).
- **Undated, #589 — an empty search-results pool reserves no space.** Helen:
  *"if I click a chip, it then jumps downwards by a few pixels"*. Clicking a
  LEAVE OUT candidate emptied the pool, which still held its top margin, and
  the chosen pill moved. The margin is set once, gated on `:not(:empty)`, and
  `test_an_empty_search_results_pool_reserves_no_space` guards it: an
  unconditional margin in `_sass/food/_search.scss` brings the jump back.

**§13.6 The recipe list.**

- **2026-09-04 — a food row's title is 1.2rem / 700 (`$recipe-title-size`).**
  The design audit's critical #2: "the list reads as metadata with a name
  attached". A punched version was tried and read as "fuzzy".
- **Undated — a row reads title, ingredient line, then pills, in that
  order.** The ingredient line outranks the pills because, in Helen's words,
  scanning it *"makes the decision about opening the page or not"*. It carries
  the recall case the search exists for ("the one with the sorrel"). Do not
  promote the pills above it to show off the colours.
- **2026-08-26 — the index's two empty-state lines are typed as recipe row
  titles.** Helen: *"doing the same job"*. `.recipe-list-empty` and
  `.recipe-list-searching` take `.recipe-title-link`'s face, size and weight
  but not its colour: a title is a link to reach for and these are not. If the
  titles change, change these.
- **2026-09-06, #552 — a food index row shows one line of main ingredients,
  two on a phone, with no fade.** Helen: *"It was actually cocktail cards I
  meant"* and *"One line of ingredients on food recipe lines please."* Three
  lines had been built on the wrong site. The clamp's ellipsis is the only
  sign of truncation (#346: *"main_ingredients line fades out downwards, but
  should not do so."*).
- **2026-09-14, #1005 — a recipe page's related recipes are drawn as index
  recipe-list rows.** Helen: *"same design as index recipe list rows as a
  baseline to build from"*. `.recipe-related` in
  `_sass/food/_recipe-list.scss` reuses the row; it is the reuse the drink
  page makes of the index card (#991).
- **Undated — the part of a row's title that matches the name search takes the
  section's tape fill and capitals, with almost no side padding.** Helen:
  *"the part of the title hit gain the orange background and scratchy,
  capitalised lettering,"* and, of the padding, *"a trailing space after the
  active substring"*. `.title-hit` in `_sass/food/_recipe-list.scss`. It is
  the one thing that still changes case when matched (#1219).
- **2026-08-03 — an ingredient that matches the search wears the active-tag
  treatment in the ingredient green, on the search button and on the row.**
  Helen: *"apply the same tag styling to active ingredient search tags, based
  on the green obviously"*. On a row, a matched word had been *"just turning
  the text green"*; it takes the tape fill and a flat stroke
  (`.ingredient-pill--matched`). Its weight is 500 (2026-08-04): 900 and 700
  beside the stroke were *"aggressive."*

**§13.7 Results heading.**

- **2026-08-03 — the results heading is left-aligned.** Right-aligned it "read
  as stray rather than placed".
- **2026-08-12 — the word in "N survivors" is bare body text, no emboss.**
  Helen: *"I liked it bare"* (it had been "fixed" once by accident). Refined
  2026-09-26 from a candidates page, *"both treatments"*: the number alone
  takes the label face (`.results-count-number`), the word stays bare. The
  other of the two treatments is the sticky results bar
  (`_sass/shared/_results-bar.scss`, `assets/js/results-bar.js`), which
  repeats the count and clear-all on both indexes once the count line has
  scrolled away; both indexes took both the same day.

**§13.8 The wordmark and the header.**

- **2026-09-14, #1007 — the header's door to the other site is the bracketed
  word and an arrow, no icon.** Her complaint, the issue's own words: *"navbar
  button for other site is too large and busy"*. Asked which of three, Helen:
  *"I am genuinely unsure! Could you advise me? I am sure that all three are
  better than what we have now."* A session's advice, which she accepted on
  the live page (*"Close this -- fixed"*): the row exists because family did
  not read a small glass as a second site, so the word does the work; a tiny
  second tape read as a mis-sized copy of the wordmark's. The `icon` key in
  `sites.yml` and the artwork stay; the footer columns use them (#1139).
- **2026-09-15, #1086 — below 600px the wordmark lockup is two thirds size
  (`$wordmark-phone-scale: 0.6667`).** Helen, from three candidates: *"B: mark
  at two thirds."* The header was a quarter of a 390px screen. 600px, not
  `$header-stack-width` (820px): 820 is where the lockup and nav stop fitting,
  a layout limit; this is a size judgement about phones, made at 600. Each
  row's `font-size` moves; nothing is `transform: scale()`d.
- **2026-09-15, #1086 — /about/ shows both doors on one line and no `??`.**
  Helen: *"C: doors on one line, no ??."* It is the one `site_neutral` page.
  The `??` is not emitted there rather than hidden: it linked to the page you
  are on and a hidden element stays in the tab order.
- **2026-09-21, #1148 — the `??` is nudged `top: -0.12em` so its ink sits level
  with the door's.** Helen reported it low twice; aligning the boxes had not
  aligned the marks. A session's measured fix. Rejected: `align-self: baseline`
  on both, because it drops the door's row 6px and that gap is hers. The row is
  the anchor; the `??` is the mark that moves.
- **2026-10-16, #1386 #1322 — the door's row hangs close under the tape:
  0.1rem over the door and the `??`, 0.1rem over the local search box under
  the door, 0.2rem from the row to the header's border, at every width.**
  Helen, shown candidates at 0.5, 0.25 and 0: *"I'd like 0.1rem margin top for
  each of the ?? and the door, then 0.1rem top for the search box. ... bottom
  edge padding of the header section ... I suspect 0.2rem would do it."* One
  variable, `$header-door-gap`, carries the 0.1rem for all three. Replaces
  *"15 over, 15 under"* of 2026-10-08. The stacked grid has no gap and there is
  no phone variant; /about/, having no `??`, carries 0.4rem under its doors so
  they sit as far from the border as a door beside a `??`.
- **2026-10-08, #1288 — the door stays at the right-hand end of the header
  (#965).** A centred door was picked only as part of the live omnisearch
  design that was not built; it is not a standing ruling. Helen: *"With no
  omnisearch visible, the [ FOOD ] -> door would never need to be centered"*.
- **2026-10-10, #1328 — below the header's stack width /about/'s two doors
  take an edge each, and the first one's arrow points outwards.** Helen: *"to
  be symmetrical"*, *"Possibly with the arrows both pointing outwards???"*, *"OR
  allow them to stack"*. A session's reading, built without a candidates page;
  the mirrored arrow is the tentative half and is two declarations to remove.
  The stack was not built.
- **Undated, #395 — the about page belongs to no site, and wherever its title
  would appear it reads `??`.** Helen: *"The name of that page is '??', so
  wherever a title would appear it should read '??'."* `site_neutral: true`
  and `wordmark_word: "??"` in `about.html`; `_layouts/default.html` gives a
  `site_neutral` page its own title with no site name appended, and the tape
  reads `[ ?? ]`.

**§13.9 The tape background.**

- **2026-08-10, #122 — the tape set mixes all three corner modes.** Helen's
  read after a real batch from `scripts/generate_tape.py`: no consistent corner
  winner among `both_acute`, `both_obtuse` and `mixed`, so use all three. There
  is no "good one automatically": generate a batch, look, hand-pick.
- **2026-09-04 — the food recipe title does not take the tape.** Offered and
  declined.
- **2026-09-11, #644 — there are fifteen tapes, and a tape whose clearest
  cluster of lines lands on the left is not used.** Helen: *"From the new set,
  don't use 1 and 7, but let's keep all the rest. Please retire tapes 2 and 5
  from my current (live) set -- the placement of that first big set of lines
  sometimes obscures the start of a cocktail name."* The set is shared between
  the wordmark and the cards, so that test applies to every future batch.
- **2026-09-11, #644 — provenance of the fifteen (marks seed = seed unless
  given as corner/marks).** tape-1..5: seeds 30 and 33 `both_acute`, 35
  `both_obtuse`, 40 and 45 `mixed` (the original 1, 3, 4, 6, 7). tape-6..15:
  102, 103/203, 104 `both_acute`; 111, 112, 114 `both_obtuse`; 121, 122,
  123/223, 124 `mixed`. Retired: seeds 32 and 36 from the original seven; 101
  and 113/213 from the batch. Renumbered because `decorations.js` rolls a
  gapless 1..N against `tape_count` in `_data/chrome.yml`.
- **2026-09-11, #779 — every tape slot draws a random tape on each page load,
  the wordmark's and the cards'.** Helen, with both states on the real header:
  *"random each page load please."* Then: *"All tape."* `FIXED_TAPE_INDEX` in
  `assets/js/decorations.js` stays at `null` as the decision, and stays a
  constant because it is the one-line change "fixed" would need. The argument
  against random wayfinding marks was never about a background texture. Replaces
  #469's stable per-card tape.

**§13.10 Typography.**

- **2026-08-26, #373 — three self-hosted faces: Selawik, Courier Prime, IBM
  Plex Mono.** With no `@font-face` every reader saw a different typeface.
  Rejected: Open Sans (*"aggressively blah"*), Cousine, Myriad Pro.
- **Undated, #185 — long-form prose is one size throughout: no lede, and a
  Tips label is the size of the prose under it.** Helen: *"I think this looks
  uneven. I'd prefer the size to be the same throughout."* and, of the labels,
  *"is the mixture of two body font sizes intentional? It feels uneven."*
  `_sass/food/_recipe-notes-body.scss`.
- **Undated, #185 — long-form lists take an em dash, Tips are labelled blocks,
  and troubleshooting items are not numbered.** Helen: *"I find the bullet
  points choppy"*; *"the numbering is definitely not working for me... the
  whole thing just doesn't scream oh my god read me now."* The failure name
  takes the single violet rule, one tier below a section heading.
- **Undated — bold inside long-form body content is weight 600, not 700.**
  Helen: *"the font still seems too heavy."* `strong { font-weight: 600; }` in
  `_sass/food/_recipe-notes-body.scss`; the Tips labels and failure names set
  their own weight.
- **Undated — the short-method toggle is a button that looks exactly like a
  body link.** Helen: *"update the short method link to the sans serif font so
  all links feel uniform."* and *"match the look of the short method link
  exactly to body links like Philosophy of Yum."* `%link-button` in
  `_sass/food/_recipe-header.scss`: sans, the article's own size, the link
  colour. Its three resets are load-bearing, because the button sits inside a
  section heading and would inherit the emboss.

**§13.10.1 `$font-label`.**

- **2026-09-02 — IBM Plex Mono is for numbers you act on, and nothing else.**
  Helen: *"Please apply Plex amounts on the drinks page, and the doneness
  charts and timing calculator. Send note labels back to Courier."* Elements
  that held the face from 2026-08-24 and came back: `.category-label` (on
  size); `.btn-tag`, `.btn-star` and `.badge` (on pairing — *"this actually
  seemed fine when the fonts were more different"*); `.recipe-title-link` (*"I
  could justify it intellectually by counting font groups, but it could well
  be that I got used to seeing the typewriter effect and now I miss it."*);
  `.note-label` last. The clash only works while Plex is the minority face.

**§13.10.2 The emboss.**

- **2026-08-10, #122 — the tape wordmark's lettering is four crisp copies on an
  off-white fill.** Rejected by Helen: a flat bigger offset (*"looks raised up
  and left... and not well"*); a gradient fill (*"looks like the lettering is
  made from twisted wire"*); gradient plus bevel (*"good, but I prefer the
  crispness of B... even if less, you know, accurate"*); higher-contrast pulls.
  `LETTERING.md` has today's values.
- **2026-08-26 — `$emboss-stroke` is 0.016em and `$emboss-offset-large` is
  1px.** Helen's re-tune for Courier Prime: the heavier face wanted more edge,
  and at 2px the offset read as "two letters, not one raised one".
- **2026-09-02 — lettering comes in tiers: T2 the wordmark, T1 large headings,
  T3 (flat with an edge) small headings; HELEN TRIAGES, `[ FOOD ]` and
  `[ COCKTAILS ]` are treated alike.** Helen: *"T2 wordmark, T1 large headings.
  Surprisingly T1 is good on the small headings too, but I prefer T3, flat with
  edge, so let's do that."* And: *"HELEN TRIAGES is not treated the same way as
  the other headings and should be"*; *"recipe title goes hard like the
  wordmark please, thanks for letting me change my mind"*. `LETTERING.md` §11
  has all seven rulings in order. Replaces the one-rule punched effect of
  2026-08-12 and *"I like the drama"* (#477).
- **2026-08-26 — the emboss tuning page has no heading dials.** Helen asked for
  them to be removed so the wordmark and its controls fit on screen together;
  no words of hers were recorded. `_dev/emboss.html` tunes the wordmark only,
  and the headings' treatment has its own numbers. Do not add heading dials
  back to it.

**§13.11 How a design decision gets made.**

- **2026-09-15, #1086 — in a design review, judgement calls go to candidates
  pages and bugs are fixed directly; one combined PR.** Helen's rulings on the
  plan. Each question went up as two to five treatments on the real page with
  the real compiled CSS and she chose by looking. Everything else the review
  raised went into one issue in sections (#1093), not a burst of issues.
- **2026-09-24 — phone is a target, not a priority.** Helen: *"I've given in,
  and phone does matter to me, I just won't prioritise it over iPad/desktop.
  But we don't strictly need to prioritise, do we."* Phone issues stay
  fileable; the about page's "I cook from my 13-inch iPad" does not close them.
- **2026-09-30, #1210 — when her answer to a candidates page is a brief rather
  than a pick, the next page builds that brief and nothing else.** Five
  treatments got: *"I'm still really struggling with this ... Please show me
  just one thing."* The one-treatment page got: *"I'm sold! No notes. Ship it
  please!!!!"* One round settles one question.
- **2026-10-06, #733 — a candidate that differs from what will be built in any
  way is a different candidate; say so on the page, not after.** The leopard
  candidates had a texture on the bands that the build could not carry, told to
  her as a footnote. Helen: *"Ahhh right, I had noticed the napping, but
  thought I could get an idea of the background colour anyway."* She re-picked.
- **2026-10-06, #733 — anything that paints a lot goes to her phone before the
  merge, as an Artifact bundle of the real build.** She had merged the leopard
  untested because *"that's the only way I can test on a phone"*, and it
  juddered. A headless desktop browser cannot show scroll cost.
- **2026-10-08, #733 — choices that interact go on one page side by side.**
  Helen asked for the fur strengths again once the base colours had dropped:
  *"it's different with the lower base"*. One switch at a time would have
  missed it.
- **2026-10-10 — a small job whose issue names its own fix may be built once
  with no candidates page, and every value in it is then the session's
  reading of her sentence, not a pick of hers.** Say so in the PR; the first
  one she looks at and dislikes is a one-line change (#1324, #1325, #1328,
  #1354, #1357, #1358).
- **2026-10-15, #1394 — the runner-up long-form design, C, is let go.** Its
  two demo pages were reachable on the live site by URL, and nothing used
  them. Helen: *"Delete the longform demos."* The pages and their stylesheet
  are in git history if C is ever wanted back.

**§13.12 Decisions that are Helen's: the words.**

- **2026-09-15, #1097 — "recipes" means recipes on both sites; "food recipes"
  and "cocktail recipes" name one site's; counts are sometimes "portions" /
  "drinks".** Helen: *"Food recipes / Cocktail recipes. 'Recipes' means recipes
  across both sites. Sometimes: Portions / Drinks."* So cocktails' name box
  says `recipe name...`, and each box reads the same on both sites with `...`.
  Code names (`drink-card`, `#drink-name`) are left alone. Not decided: whether
  the manual's roughly 280 uses of "drink" as the noun follow.
- **2026-09-15, #1086 — the cocktail scaler reads `− [1] drinks +`, the word
  after the box.** Helen: *"C: word after the box."* It replaced a `×`. The `×`
  was typography, an agent's call; a word is voice, so it shipped as a marked
  placeholder until she confirmed "drinks" and food's "portions" final on
  2026-09-20 (#1088). Markup, not CSS `content:`.
- **2026-09-15, PR #1100 — the shortlist panel is a share link and nothing
  else.** Helen: *"Remove the rest of the apparatus: no JSON export or import,
  no clear."* The summary reads *"Share or save the shortlist"* and the hint,
  on both sites, *"Loading this shows recipes without saving them."* The fear
  the export was built for (*"I just KNOW that something will go wrong and I'll
  lose my shortlist"*) is served by the link, which keeps no portions or
  glasses.
- **2026-09-20, #1088 — "If you liked this, how about…" is final.** Helen:
  *"The if you like this text isn't a placeholder. Final version."* The words
  were hers from #927's title. A placeholder marker means she has not ruled,
  not that the words are wrong.
- **2026-09-20, #1088 — the search dropdown's page groups are labelled "food"
  and "cocktails".** This does not reverse #1097: that fixes the word for
  content; this label says which pile the results came from, beside groups
  that are kinds of word (Mood, Hassle, Has to have). Both `search.json` files
  carry the argument.
- **2026-09-20, #1088 — a filtered index with no matches says "Blank canvas."
  on both sites; "Nothing to see here yet." is cocktails' empty-collection
  line.** Helen: *'Both "blank canvas."'* and *"'Nothing to see here yet' is
  fine for when the cocktail site is empty, which it currently is not."* The
  search dropdown's own no-match line is *"nothing to see here"* (#1055).
- **2026-09-20, #1088 — the recipe scaler's note reads `(Not scaled: salt,
  black pepper, olive oil)`.** Parenthesised, no full stop, commas throughout
  (her example had a comma and a semicolon; asked, she chose commas).
  Knowingly given up: a name containing a comma would read as two.
- **2026-09-20, #1088 — the 404 says "You know the drill." over two doors with
  the arrow AFTER the word, reusing the header's door.** Helen wrote the page
  out as `[ FOOD ] ->` and `[ COCKTAILS] ->`. An arrow after the word is the
  header's "over there", two ways out; `.about-ways`' arrow on the left is
  doors into one room. #991: *"we should just reuse what we've already made"*.
  `[ COCKTAILS ]` keeps its inner spaces: bracketing is typography.
- **2026-10-07, #1088 — the LEAVE OUT line reads "hiding peas", on both
  indexes.** Helen: *'"hiding peas" please.'* No count, no sentence for zero.
  Two or more read "hiding peas and ham"; the "and" is the agent's. Cocktails
  took the same line on 2026-10-11 (#1219).
- **2026-10-07, #1088 — a capped list says "+3 more" and stops.** Helen:
  *'"+3 more" is fine, then that's it.'* The "— keep typing" came off.
- **2026-10-07, #1088 — the food index with nothing chosen says "(select
  something)"; the estimated-portions tooltip is "(estimated)"; "copy link" /
  "copied" are fine.** Her words at the second sitting, which listed every
  visible string rather than grepping for markers. Lines only a local build
  prints are hers to fix or not.
- **2026-09-25, #1097 — the cocktails site's description is exactly "What to
  drink.", full stop included.** The string is Helen's own. It is
  `description` in `_data/sites.yml`, the fallback `<meta description>` for a
  cocktails page with no tagline of its own; food's is "What to cook, not how
  to cook". Do not lengthen it, drop the stop, or rewrite one to match the
  other.

**§13.13 The page furniture.**

- **2026-09-07, #783 — the footer's columns sit under the sides of the main
  page container.** Helen: *"I would like each to be under the sides of the
  main page container."* Taking `max-width` off the footer to reach the
  viewport edge was the wrong reading. All three footer items are placed
  explicitly in the grid (a session's call: a pinned column with an auto row
  is still auto-placed).
- **2026-09-14, #1005 — a recipe page and a drink page carry the same
  controls; the scaler and "if you liked this" are on both.** Helen: *"Yes."*
  Back, shortlist, see shortlist, print, pdf; read it / make it stays
  cocktails'. Where they sit is the ruling of 2026-09-30, #1210.
- **2026-09-14, #1005 — food scales by portions; drinks scale by whole
  recipes.** Helen: *"Portions. Things like '2 large' can scale, surely, then
  let's add a note to bitters and handfuls"*.
- **2026-09-28, #1090 — related recipes rank by the same star ingredient,
  then shared mood tags, then shared other tags plus main ingredients, then
  shared real ingredients, larder staples, and A–Z.** Helen: *"That's a great
  ordering. Let's go."* The poultry showstopper should suggest the duck before
  the chai. Other tags stay counted with the ingredients: weighting
  ingredients above all tags was declined on measurement in #1005 (cauliflower
  cheese got both chocolate ice creams on "whole milk"). Same key in
  `scripts/related_recipes.py`, held equal by a test.
- **2026-09-14 — every action is in Courier capitals, on both sites.** Helen:
  *"Let's try all actions in capitals (shortlist button at top of index lists
  too) to help show they're actions????"* The question marks are hers: a try
  that has stood, not a ruling.
- **2026-09-15, #1086 — below 600px the recipe's SERVES / PREP / COOK boxes
  stack.** Helen: *"I'd like to try stacking the three metadata boxes on a
  phone, avoiding the jar in length differences, but also allowing more space
  for any 'cook' line."* Desktop and tablet keep three columns.
- **2026-09-15, #1086 — below 400px a recipe title is 1.9rem at 1.1
  line-height.** A session's fix for titles stacking a word per line; it stays
  above `.recipe-section-heading`'s 1.8rem so the h1 is the biggest heading at
  every width.
- **2026-09-15, #1093 — one blanket `prefers-reduced-motion` query covers both
  sites.** Every transition on either site is a nicety.
- **2026-09-15, #1099 — a drink page runs: ingredients, scaler, method, TO
  SERVE, notes, rule, source, units, cost, rule, "if you liked this".** Helen
  gave the list; asked where TO SERVE goes, *"After method (as now)"*. Source,
  units and cost share one footer.
- **2026-09-15, PR #1100 — the rule over the controls is 1px grey on food and
  1px absinthe on cocktails, and that is settled.** Helen asked for cocktails'
  at 1px (#1099), then: *"The hairline rules are now fine, stop asking!"* Do
  not raise matching them again.
- **2026-09-20, #1149 — a footer column's head is a link drawn like the
  header's door: no underline, quiet at rest, word and icon to `$color-accent`
  on hover.** Helen, from three on the real page: *"Footer A please."*
  Declined: underlined like the links under it; underline on hover only. The
  icon is inside the anchor. The links below are a list of pages and keep
  their underline, so the footer has two link styles on purpose.
- **2026-09-24 — a drink page shows four related cards; a food recipe shows
  three.** Helen: *"Let's bump to four related cards for cocktails."* The
  two-column grid orphaned a third. Every published drink's fourth pick still
  scored above zero.
- **2026-09-30, #1210 — the four page actions are not one row: they were four
  controls of three kinds drawn alike, and no arrangement of them could
  settle.** Helen: *"The layout/styling of these has always made me unhappy"*;
  of the redraw, *"I'm sold! No notes. Ship it please!!!!"* Six issues in two
  weeks had each rearranged the row (#1086, #1163, #1164, #1176, #1182).
  Replaces the `.recipe-controls` row and every grid of it.
- **2026-09-30, #1210 — print and pdf sit at the right-hand end of the back
  arrow's line.** They are things you do WITH the page. Helen: *"so where the
  omnisearch currently is"*. `_includes/page-print.html`, only where a layout
  passes `actions=true`.
- **2026-09-30, #1210 — the shortlist pair sits at the right of the first line
  under the head's rule: the toggle's line on a drink page, INGREDIENTS' line
  on food.** Helen: *"on the same line as INGREDIENTS for Moules where it
  doesn't have the read it make it toggle."* Helen: *"when the buttons stack
  don't let them push INGREDIENTS downwards"*. Below 600px it takes the line
  above on both, so the shape never depends on width or count.
- **2026-09-30, #1210 — the shortlist button and the see-shortlist link are
  deliberately unmatched: a bordered pill, and quiet caps `SEE SHORTLIST (N)`
  with no arrow, absent while N is 0.** Helen: *"I can't make them look
  similar."* They are not similar: one changes this page, the other leaves it.
  *"I also dislike the -> arrow so please remove that at least"*. Word first,
  replacing #1164's count first.
- **2026-10-10, #1354 — once the footer stacks, a 2rem hairline sits over
  `about`.** Helen: *"whether space, a dot, a short hairline, anything"*. A
  session's reading: a line, because #916 already spent the larger gap on the
  break between the two sites' columns.
- **Undated, #387 — the back arrow returns through browser history when the
  reader came from the index in this tab, and is a plain link otherwise.**
  Helen wanted to go back *"so the index page has the same recipe list I left
  it with"*, and for the arrow to work *"both directly and then opening in a
  new tab"*. A new tab has one history entry, where `history.back()` does
  nothing, so `back-link.js` upgrades the link only when it can prove where
  you came from.
- **2026-09-16, #1119 — the back arrow is the header door's arrow graphic,
  mirrored, at 3rem.** Helen: *"back arrow and site door in navbar should use
  the same graphic"*. One file, `icons/arrow-right.svg`, flipped with
  `scaleX(-1)`. The size is hers, set by eye over a session's 1.6rem (#411),
  and it does not follow the door's arrow: it is the only control on its line.
- **2026-09-17, #1139 — each site's icon sits small and inline with its footer
  column heading, at the left for food and the right for cocktails.** The
  cloche and the martini glass came back to the footer in #1122: *"These used
  to be in the navbar but didn't make the redesign, and I miss them!"* Centred
  over the links they misled: *"the footer icons look strange because food and
  cocktails are different lengths, so reduce the icon size and bring it inline
  with the heading, left for food and right for the cocktails."*
- **Undated, #902 / #915 — the footer's two licence sentences stack on
  narrower screens and sit close under the copyright line.** Helen: *"stack
  the two licences on narrower screens"*; and the closeness is *"to show
  they're one object"*. One paragraph of two spans, inline at desktop width;
  `.site-footer-license` has a class of its own so its smaller top margin
  survives the centre column's resets.
- **Undated, #1005 — the related recipes on a food recipe page are the index's
  own rows.** Helen: *"same design as index recipe list rows as a baseline to
  build from"*. `_layouts/recipe.html` writes the row out rather than
  including it, because the index row carries filter attributes this page has
  no use for; the shortlist button is the index's exactly. A change to the
  index row's design is a change here too.
- **2026-08-14 — the short-method toggle and its print "In short:" section are
  not deployed: `short_method_enabled: false` in `_config.yml`.** Recorded as
  Helen's decision of that date; no words of hers were kept. The flag turns
  both off whatever `method_short` holds. The key stays required and the
  rendering code stays, so do not delete either as dead, and do not turn the
  flag on without her.
- **2026-08-04, #54 — the ingredient amount's highlight and lettering cover
  the unit as well as the number.** Helen: *"Ingredient amounts currently only
  get bolder, no scratchy lettering. Please simply extend this formatting
  right-wards."* The unit lives inside `.ingredient-amount-number` in
  `_layouts/recipe.html`, so one highlighter covers "400 g" as a single run.
- **2026-08-14, #86 — a printed page looks like the site: the marks keep their
  colours, the page ground is not printed, and badges are the one thing taken
  off a recipe.** Helen: *"That's simply unfair."* and *"I don't care if my
  headings don't look like label tape."* `print-color-adjust: exact` at the
  root keeps every mark, wash and chart bar, and the body background is
  `transparent`, stated, so a sheet is not flooded with a tint. No smaller
  type, no reflow, no monochrome pass, and the yellow amount highlight must
  print (`_sass/shared/_print.scss`, `_sass/food/_print.scss`).
- **2026-09-02 — the about page's `<hr>` is the footer's 1px dashed hairline,
  not an empty heading mark.** Helen overrode the empty-mark divider in a
  design review; no words of hers were recorded. `_sass/food/_about.scss`.
- **2026-10-13 — the about page's footnote is a normal asterisk footnote below
  point 2b, inside the point that calls it and not in the page gutter.**
  Helen: *"make this a normal asterisk footnote below point 2b, not a styled
  \*"*; and of the gutter position, 2026-09-04, *"puts the footnote at the
  same place in the hierarchy as the points"* and *"its block isn't aligned
  with the block that called it, so I have to do work to parse, and I do not
  like doing work."* Of where it starts: *"I'd prefer the \* lined up with
  the indent"*. The asterisk is a character in `about.html`;
  `.about-footnote` draws no mark and takes `.about-enum-sub > li`'s padding.
- **2026-09-04, #546 — the shortlist control is grey when off and the site's
  hot colour when on: wicked woowoo on cocktails, hot magenta on food.**
  Helen: *"Text and active colour wicked-woowoo on cocktails because it's a
  thing the user is choosing and that's the language"*; *"I don't have a
  strong opinion on colour for food, so hot-magenta by default I guess!"*;
  *"Grey for inactive"*. `$color-clear-text` at rest on both sites.
- **2026-09-16, #1119 — the back arrow and the header's door use one arrow
  graphic.** Helen: *"use the same graphic"*. `_includes/back-to-index.html`
  includes `icons/arrow-right.svg`, mirrored with `scaleX(-1)`; it is a
  drawing for the reason the door's is (#993). Its 3rem size is hers (#411)
  and is not the door arrow's.
- **Undated — a method step may hold a real bullet list.** Helen: *"there's a
  note for you in the ganache about bullet points [in a method step] -- work
  out formatting we can use on other pages."* A step's text is markdownified;
  the nested `ul` resets `counter-increment`, or each bullet would renumber
  every later step. Outer steps are sequential and inner bullets parallel.
- **Undated — an FAQ question's title is held to the same measure as its
  answer.** Helen: *"please constrain the width of FAQ item titles to the same
  container."* `max-width: $about-measure` in `_sass/food/_about.scss`.

**§13.13 The search-for-anything box.**

- **2026-09-15, #1050 — the box searches everything on ONE site, with results
  in a dropdown grouped by type.** Helen: *"to search per site, not across
  sites"*; *"search results should also have a group for ingredient name."*
  When a later filter left only names: *"I still want the omnisearch box to be
  able to search for everything ... Please put it back."* Data is a per-site
  `search.json`. A word no page carries is not offered.
- **2026-09-15, #1052 / #1051 — a search match is a prefix of a whole word,
  never a substring, and a card label joining two ingredients ("X or Y") is not
  offered.** Helen's issues. Every typed word must begin a word of the
  candidate, in any order.
- **2026-09-15, #1050 / #1053 — food's dropdown group titles are Selawik 700
  at 0.7rem; the five `-bright` tones no longer colour them (#1136).** Helen:
  *"food site: group headings need to be brighter, closer to core colours
  although obviously we're limited by contrast"*. A `-bright` was its root
  darkened by exactly what 4.5:1 costs; the palette no longer carries them,
  because the headings are filled with the section's root hue and lettered
  dark (§13.13). #1053: *"Switch font to the other one
  if you have to"*.
- **2026-09-15, #1096 — the box and the index's own searches both stay as they
  are; the box's placeholder is "I know what I want..." with no label, only
  the magnifying glass.** Helen: *"Retain current behaviour for both."* The
  placeholder goes transparent on focus (*"both sites, remove placeholder on
  click"*).
- **2026-09-15, #1099 — the glass is at the right, and typing grows the word
  leftwards from it.** Helen: *"like this ____r ___rh __rhu _rhum."* The input
  is right-aligned. Focus is an accent underline, not a box (*"Remove the
  bordered box around the omnisearch input field when it's active"*), drawn as
  an inset shadow so nothing moves.
- **2026-09-16, #1123 — the box is 22ch, the length of its own placeholder,
  and its line and placeholder are `$page-search-quiet` (45% of
  `$color-clear-text` mixed towards the site's ground).** Helen, after 12ch
  shipped: *"the omnisearch placeholder needs to all be visible ... To make it
  less obtrusive, which is what I actually want, please step its colour (border
  and font) closer to the background."* Typed text stays `$color-text`. Mix
  towards the ground, never `lighten()`. 40% was rejected as disappearing.
- **2026-10-08, #1288 — the search box is on local builds only, in the header
  under the door, behind `show_header_search`.** Helen (#1210): *"this is key
  for me during testing so I'm not clicking about all over the place."* On
  #1288, after a full live build (PR #1310, unmerged): *"I've decided not to
  have this feature on the live site -- I'll keep it on the local build. The
  live filtering from the IKWIW fields is cuter. ... I will return to this if I
  miss it."* An always-there box costs every phone a third header line. A
  closed grey glass was also tried. Read PR #1310's closing comment first.
- **2026-09-17, #1136 — the search dropdown's group headings are filled with
  their section's root hue and lettered dark, on both sites.** Helen:
  *"omnisearch dropdown result group headings should take their section's
  background colour with black lettering, like active chips on the index
  page."*, and *"the same for the food site"*. The root hues, not the
  `-bright` tones, which were darkened to be read as text on the panel; this replaces
  #1053's `-bright` headings. `.page-search-group--<kind>
  .page-search-group-label`.

**Cocktail cards and the drink page.**

- **2026-09-07, #704 — a drink's glass options read "A, B or C", no Oxford
  comma.** "coupe, or nick and nora" would suggest the last option is a pair.
- **2026-09-07, #776 — a card's name, ingredient lines and chips share one
  height budget.** Helen: *"if cocktail card ingredients have three lines,
  only allow the chips two lines ... if the cocktail name has two lines, only
  allow ingredients and chips two lines each"*. A wrapped name caps both
  others; three rendered ingredient lines cap the chips. `cocktail-index.js`
  re-measures on every pass, before `markChipRows()`, because a hidden card
  measures zero.
- **2026-09-07, #823 — the card's shortlist mark gets its ~44px target from an
  absolutely positioned `::after`, not padding.** Helen's report was that the
  mark was *"a little easy to mis-click"*; the construction is a session's
  call: the title's reservation is computed from the button's own metrics, so
  padding comes off the tape. It claims the card's top-right corner from the
  card link.
- **2026-09-15, PR #1100 — a matched chip on a cocktail card is inverted and
  tight.** Helen, from underlined / inverted tight / inverted padded: *"Chip
  option B please."* Replaces #756's coloured word and underline. On 2026-10-11
  she asked whether it should take the filter chip's tape and could argue it
  either way; the session's answer was no and nothing was built.
- **2026-09-20, #1088 — the drink amount column is sized by the drink.** Helen,
  shown 41.5px of empty column on a phone: *"Sizing the column by drink sounds
  perfect."* `.cocktail-ingredients` owns `max-content 1fr` and each row joins
  it by `subgrid`; sub-lines sit in `grid-column: 2`. Rejected: a narrower
  fixed column (4rem broke "3 drops"; a fixed width must fit the longest amount
  in the whole collection).
- **2026-09-21, #1161 — the drink page's glass has side inset and the
  glass / garnish / ship block a wider left margin.** Helen: *"give the glass a
  little more left and right padding, AND give the glass/garnish/ship a wider
  left margin."* `inset: 0 $space-sm` on the svg and `column-gap: $space-xl`.
- **2026-09-21, #1162 — an unpublished cocktail wears a DRAFT mark on the local
  site, in the card's quiet text colour.** Helen: *"add a DRAFT badge on the
  local site for unpublished cocktails"*; on a drink page *"to the right of the
  name tape, below if needed"*. No new hue: it says where the file is in her
  process, not anything about the drink. Food's `.badge-draft` is not shared.
  It cannot reach production: only `_config_local.yml` declares `show_drafts`.
  The card's mark moved to the top left over the glass on 2026-10-06.
- **2026-09-21, #1165 — between 400 and 720px the card glass is 7.5rem.**
  Helen: *"glasses are too large and are overflowing vertically on cocktail
  cards at medium screen widths."* A session's measured value: below 720px a
  card is `height: auto`, the shortest is 128px, and 7.5rem clips none.
- **2026-10-10, #1357 — a drink title is 1.6rem on a phone
  (`$title-size-phone`).** Helen: *"We can reduce font size a little for
  cocktail titles on mobile to reduce the linebreaking"*. A session's value:
  `scripts/title_phone_lines.py` counts one three-line title at 1.6rem against
  sixteen of 212 at 2rem. 1.75rem was the gentler candidate.
- **2026-10-10, #1324 — a long name in the universe line stays beside its
  glass.** Helen: *"The glass is on its own line with the rest below."* A
  session's fix: the name is capped to what is left of the glass's line and may
  shrink, so `card-name-fit.js` steps or wraps it as on a card.
- **2026-10-10, #1358 — both indexes have a `hide drafts` / `show drafts` pill
  under SHORTLISTED, local builds only.** The labels are the issue's words. A
  session's reading: it is not filter state, so clear-all leaves it alone and
  nothing remembers it across a load.
- **2026-09-05 — the shortlist mark and its word are centred on each other,
  and the word does not move when `+` becomes a tick.** Helen: *"please
  horizontally align the middle of the word shortlist with the middle of its
  icon."* and *"when I click +shortlist, the word jumps downwards a few
  pixels."* `✓` is not in Courier Prime, so a fallback face draws it with
  other metrics: the mark is a flex item with a declared width and height and
  `overflow: hidden`. Keep it a flex item.

**The leopard ground (cocktails).**

- **2026-10-06, #733 — the leopard print ships on the cocktails page ground:
  furry splodges, the darkest ground, the nap texture.** Helen: *"it's so
  ...furry!!!!! Cracking job. I choose furry, darkest and nap from these, in
  the page ground."* Parked since 2026-09-05; she re-opened it. `LEOPARD.md`
  has every round. Nothing was copied or traced from her reference pictures;
  any change is a new round on a candidates page. Replaces "a card stays the
  darkest thing on the page" (*"Let's try relaxing the rule about the cards
  being darkest"*).
- **2026-10-06, #733 — cocktails' header and footer are flat full-width bands
  with no print.** Helen: *"Same as the page, offset, and plain. Sold."*;
  *"Please take it off the footer"*; and, shown that the built bands lacked the
  candidates' nap, *"I prefer the flat."* The footer's rule is solid and
  full-width there. Both are custom properties with food's old values as
  fallbacks, so the shared chrome is still one header.
- **2026-10-06, #733 — the print repeats on a slanted lattice.** Helen:
  *"sometimes some of the larger splodges can be seen either side of the card
  grid which makes it clear they're repeated."* She chose it over the straight
  repeat.
- **2026-10-06, #733 — the site ships zero raster images; the device draws the
  leopard SVG once and keeps the picture.** Helen: *"one of the very coolest
  things I wanted to achieve here was great styling with zero images ... Do I
  need to choose between leopard and being cool!?!"* It is a ruling, and an old
  one. `assets/js/ground-print.js`; kept in IndexedDB (*"Can drawn once not be
  saved page to page...?"*). Declined: a baked bitmap; the slimmed vector
  (*"it all looks like spiders"*); pinning the fur to the screen; sharpening
  for dense screens.
- **2026-10-08, #733 — the fur is drawn at strength 1.5 on every device; a
  phone (600px and under) gets half the nap and nothing else differs.** Helen:
  *"it's 1.5, and nap on, for all: mobile, ipad and desktop."*; *"nap half for
  phone, everything else is the same. Ipad is same as desktop."* No second
  drawing for phones. The kept picture's key carries the strengths and the
  ground colour.
- **2026-10-08, #733 — cocktails is "black on black": `$color-paper` #030304,
  `$color-chrome-ground` #060607, `$color-surface` #0d0d0f.** Helen: *"can we
  still have the print visible, while darkening the whole thing? ... Basically
  what I'm aiming for is 'black on black', ish."* Pure black was offered and
  not taken. A card is still lighter than the page. Replaces `#060607` /
  `#111113` / *"don't touch"* the cards' `#17171a`, all of 2026-10-06.

## §14 Reference pages

- **2026-08-13 — the temperature data and charts say "Out at", never "pull
  at".** Pull is American. `tests/test_style.py` knows the phrase.
- **2026-08-14 — a recipe's internal temperature never appears in its metadata
  grid.** Helen: *"I don't like the internal temperature featuring in the
  metadata — it's ugly, it spoils the rule of 3, and it's nowhere in sight
  when you're actually cooking."* It renders below Notes, at `#doneness`. The
  same day: the single reference page split into temperatures and timings
  (#183, #189, #202); roasted duck legs use `poultry.duck`, since "in the
  thigh" is exactly what a leg is; and drafts are exempt from temperature
  wiring, which is wasted work until the dish is cooked.
- **2026-08-15, #213, #218, #272 — the reference pages are reached from the
  footer: no nav link and no index page.** Helen, on why the footer and not
  the nav: she uses them *"when I'm planning out what I've decided to cook,
  and when I'm in the kitchen about to be covered in raw chicken"*. A nav link
  (#213) was closed won't-do-for-now and `food/reference/index.html` was
  deleted (#218). Both were listed as not re-opened in the redesign of
  2026-10-08.
- **2026-08-16, #246 — the timings calculator has no rare/medium control.** A
  session's call, not Helen's ruling. Only 2 of 73 methods have the
  `by_doneness` shape, so both figures render on those two and no control was
  added: a control that usually does nothing reads as broken.
- **2026-08-19, #382 — there is no methods tables page and no steak table;
  fish and shellfish live on the calculator page.** Nine of the tables page's
  twelve sections duplicated the calculator. Helen, on the steak table: *"I
  know how to cook steak"*. On fish and shellfish: *"it's good to have the
  reminder about options of how to cook... they still have methods so they go
  on the methods page."* Both remaining pages were renamed with no redirects
  (#383–#386, #368). This overturned #207 ("the tables and the calculator do
  not merge") for the page, not for the calculator.
- **2026-08-21, #400 — the sourcing prose cut from `cooking_methods.yml` is
  kept in `cooking-methods-prose-archive.html`, committed and unpublished.** A
  session's call, not Helen's ruling: 35 paragraphs, 1,942 words and 14 links
  of original research were moved out before `groups` was deleted from the
  data. `cooking_methods.yml` has been edited by hand since; the two generator
  scripts are migration tools, and a re-run would drop 166 lines. Do not
  delete the archive as dead, and do not re-run the generators.
- **2026-08-21 — youvetsi carries no internal temperature.** Wired to
  `beef.tough_cuts` and unwired the same day by Helen, cooking it: *"it'll
  just fall off at the end, being whatever temperature the pan sits at for 3
  hours"*. It is the third kind of `NO_TEMPERATURE_BECAUSE` entry: a figure
  that is right about the cut and useless in the method.
- **Undated (August 2026) — pork "medium" and fresh ham's "hint of pink" stay
  as they are.** Both sit below the cited safety figure. They were flagged and
  deliberately not corrected: whether to serve pork pink is Helen's call, and
  no session changes those figures.
- **2026-10-08, #1326 — the reference pages have no tooltips, and nothing that
  lived in one was rehomed.** Offered the four facts that existed only in a
  hover (cured ham's packaging caveat, duck breast off the bone, the fork test
  for tough cuts, tuna served rare), Helen: *"Lose all, they're nonsense to
  me!"*
- **2026-10-08, #1327 — the temperature charts stay one scroll, with the
  contents as sticky chips; no per-protein picker.** Helen, asked: *"Honestly
  I don't know. Immediate reaction is 1, with good nav."* Then, from the
  candidates: *"Internal temp: one line sticky jump bar."* A row is its label
  and figure on one line with the bar under them at full width, at every
  width. The chips wrap rather than scroll sideways (2026-10-09: *"Option A
  please, perfect."*). The thermometer treatment lost; it is in
  `scripts/reference_candidates.py`. Not re-opened, on purpose: the split
  pages, no cards, one axis for the whole page.
- **2026-10-08, #1329, #1330 — the methods page is stacked blocks grouped by
  cut, each with its oven setting; fish and shellfish are lists with no
  notes.** Helen, asked whether the missing oven setting was what sent her to
  Google: *"Do you mean e.g. 200° fan for 10 mins then 180° fan for an hour?
  If so then yes."* Then: *"Cooking methods: stacked, by cut, fish and
  shellfish list no notes."* Shortest-first holds within a group. The decision
  table (#253) is gone, so neither page holds a `<table>`, and the fish notes
  were deleted, not hidden.
- **2026-10-09 — a chart figure is numbers only, and no chart has a note under
  it.** Helen: *"Remove all extra text from figures, e.g. 'in the thickest
  part of the thigh', 'for pink meat then rested', 'at the thickest point'.
  All of it."* and *"delete all extra notes below all tables... all of them."*
  `temp_row.html` builds the figure from the numeric fields; the display
  strings stay in the data for the recipe page and the calculator's "Done at".
  The key's "below the cited safety figure" entry and the poultry subtitle
  went with them. The cut-list subtitles stay: they say what a chart covers,
  which is not a note.
- **2026-10-16 — chart gridlines sit on every multiple of five: the tens
  labelled, the fives between them paler and unlabelled, at every width.**
  Helen: *"We ask for 1-2 degree precision by eye, then offer no help.
  Honestly I'd love something every 2 degrees....but I'll accept 5."* Every 2°C
  was declined because on a phone the lines would be 10 px apart, narrower
  than many bars. The lines sit on the figures, not at a fixed period from the
  35°C edge (2026-10-09: *"The scientist in me is upset by the x axis
  lines"*): each is its own stop, from the same `$tc-min`/`$tc-max`
  arithmetic as the ticks and the bars.
- **2026-10-09 — on the methods page the weight sits under the dropdown, the
  four birds read "(whole)", and times are compact (`4h50m – 5h30m`).** Helen:
  *"So the user is saying 'I have chicken, 3 kg'."* Of the times: *"Collapse
  timing display to e.g. '2h - 3h', '4h - 4h50m', '10m - 15 m'. En dashes."*
  (`hhmm` and `span` in `cook-schedule.js`). The two inputs are one stacked
  form above the protein heading, and the weight hides when the dropdown says
  fish. The compact time is for this column of figures only: the house rule
  "mins, never min" is about recipe pages' time lines and is not re-opened.
- **2026-10-09 — the slow-cooked cuts are one chart section of their own.**
  Asked whether pulling them out of the roasting charts would read as
  scattered, Helen: *"okay great, let's do it."* Beef, lamb, pork and venison
  draw as one chart (`#slow-cooked-cuts`, 90–96°C) near the foot of the page,
  and each roasting chart that lost a row links to it. The axis is unchanged
  and shared by the whole page: the empty right third of a roasting chart is
  the information that nothing roasts past 75.
- **2026-10-09 — a chart row's words belong to the bar directly under them:
  label and figure share a baseline, the bar sits tight below, and all the
  row's air is under the bar.** Helen: *"It's not clear, even on small
  screens, which labels belong with the data bar."* and *"the data label e.g.
  RARE sits higher than the bar, then the numbers labelling it e.g. 48-50 sit
  higher again."* Option A of three put to her, for a bar that sat as far
  below its own caption as above the next row's. B would also have moved the
  figure beside the label; C was banding. Nothing new is drawn.
- **2026-10-09 — cut-group and fish names on the methods page wear the
  heading-tier lettering with the single violet rule.** Built on Helen's
  request for jollier headings. Her next note was *"I love most of this! It's
  just the 'jollier headings' request. There is a LOT going on now."*, and
  what was cut in answer was the mix of fonts inside a method block
  (2026-10-10); the headings stayed. Scoped under `.recipe-body-content
  h3.ct-group-name`, because the body's quiet-h3 rule out-specifies the bare
  class.
- **2026-10-10 — a method block reads outcome first, then the method's name in
  small grey Courier, then the oven stages in Plex Mono; the time stays alone
  on the right.** Helen: *"The new cacophony of font styles is absolutely not
  helping visual cohesion... My favourite from your current candidates page is
  outcome first, method next in courier... let's try using [Plex] for the e.g.
  '190-200°C fan' instructions. [...] I think the violet colour for outcome is
  going to have to go as well... I like the timings on their own on the right,
  and their styling, so keep those!"* Three faces, one job each, and no
  fourth. (Replaces round one's name-first block of 2026-10-08 and the violet
  second-line outcome of 2026-10-09.)
- **2026-10-10 — the oven setting is a list of short stage lines in the data,
  and method rows have real air between them.** Helen: *"It's that the rows
  are all too close together. The e.g. 160-180 fan at the bottom of one row is
  so close to the bottom of the row it can barely be seen."* and *"Lines like
  this one should break more helpfully... Basically hardly any extra text,
  instructions not buried"*. `oven` is one line per setting ("220°C fan for 20
  min", "180°C fan for the rest"). The rows had been close because the block's
  padding lost to the list reset at (0,2,3) since round one; it is declared on
  the `li` reset now, 1.25rem above and below.
- **Undated, #244 — the timings page answers "how long does this take",
  not "what time do I put it in".** Helen, of the page with its "eating at"
  and "rest" boxes and in-at/out-at lists: *"needs to be much clearer for a
  user."* All four went. The long explanation at its foot of why some rows
  decline went as well: *"the whole bottom section can go, other than see
  also."*
- **2026-08-16, #244 — `scheduleBack`, `parseClock`, `clock`, `statedRest` and
  `restFor` in `cook-schedule.js` are kept, with their tests, though nothing
  calls them.** Helen's explicit instruction when the page lost its "eating
  at" box, until she decides whether working backwards from a serving time
  comes back; no words of hers were recorded. The next editor reconnects them
  or deletes them together with their tests, on her say.
- **Undated — every cooking time on the timings page is rounded to the nearest
  five minutes.** Helen: *"let's round cooking times to the nearest 5 mins to
  preserve sanity."* `round5` in `cook-schedule.js`. A figure like "1h37m" is
  false precision for a roast, and nobody sets a timer to it.
- **Undated, #412 — fish and shellfish is an entry in the timings dropdown
  that replaces the calculator with a static section.** Helen: *"Not cooked by
  time."* It is not a protein with a rate per kilo, so picking it hides the
  weight box and swaps `#ct-calculator` for `#ct-fish-shellfish`. The dropdown
  itself never hides: it is the way back.
- **Undated, #243 — the finishing temperature sits directly under the protein
  heading.** Helen, of its earlier position: *"it makes no sense where it
  is"*. There it reads as a property of the protein, whatever the method or
  weight, not as something the form computed. `#ct-doneat`, with its link to
  the full chart.
- **Undated, #338 / #352 — a wired recipe's cook time ends "but check internal
  temperatures chart", and the words are never "cooking temperatures".**
  Helen, on roast beef fillet: *"About 30 mins, but check beef cooking
  temperatures."* A clock figure qualified by doneness ("40 mins for medium
  rare") was rejected. Then: *"It's not cooking temperatures, it's internal
  temperatures."* The link goes to `#doneness` on the same page.
- **Undated — every temperature chart carries its own key, declaring only the
  marks it draws; the recipe page's doneness chart has one too.** Helen:
  *"add the key to this chart too (it's tiny)"*. A figure carries its own
  legend, so there is no single key at the top of the page.
  `_includes/food/temp_key.html`, called with `rested`, `carry` and `solid`
  per chart.
- **Undated — the temperature axis starts at 35°C, not 40.** Helen, of tuna's
  38°C bar: *"the bar for tuna slightly obscures the word"*. `$tc-min: 35` in
  `_sass/food/_temperature-chart.scss` keeps that bar inside the track. Ticks,
  gridlines and bars all come from the same arithmetic, so moving it moves
  everything.
- **Undated, #240 — a chart's crosslink sits in a paragraph of its own
  directly under the heading, not on the heading's line.** Helen: *"an effort
  to reduce visual confusion (mine)"*. `.tc-crosslink-line`. It replaced #215,
  which had moved the link up beside the heading because *"it gets buried"*.
- **Undated, #333 — the doneness chart's "more" link on a recipe page is
  right-aligned.** Helen: *"so it doesn't feel too close to the footer
  links"*. `.doneness .doneness-more` in `_sass/food/_temperature-chart.scss`.
- **2026-08-16, #243 — on the methods page the finishing temperature sits
  directly under the protein heading.** Helen, of where it had been: *"it
  makes no sense where it is"*. It is a caption to the heading: the one figure
  that holds however the thing is cooked.
- **2026-10-10 — a method's two-line time does not push the left column's
  content down.** Helen: *"let's not allow the extra line to push the
  left-column content down too."* The time spans all three rows of the block's
  grid in `_sass/food/_timings.scss`.
- **2026-08-13 — the notes in the cooking-methods data keep safety and sources
  and drop correction history.** Helen: *"keep safety and sources, drop
  correction history"*. A note says what is safe and where the figure comes
  from, never "Corrected from ~15 min/kg…". What changed is git's to keep.
- **2026-08-14 — the beef closed-oven-off method is not in the cooking
  methods.** Helen: *"it's just not for me"*. It is absent from
  `_data/food/cooking_methods.yml`, and so from the methods page and the
  calculator together; `EXCLUDE` in `scripts/build_cooking_methods.py` names
  it. Do not restore it for completeness.
- **Undated — every cooking method carries a short `outcome`, so methods are
  compared by what the cook gets.** Helen: *"summarising the cooking options
  by user need... the method name then the description of the chicken you
  get."* `outcome:` in `cooking_methods.yml`, held by
  `test_every_method_has_a_short_outcome`. Since 2026-10-10 the page prints it
  first in each block.
- **2026-08-14 — no test sums a method's timings against `cook_time`; the
  nudge to the temperature chart is the answer.** Helen: *"if a recipe
  contains complicated meat, a nudge to the temperature chart should catch
  most users."* Roast beef fillet said "30 mins" where its method adds up to
  nearer 40. A clock figure cannot answer "is it done", and half the methods
  say "until golden", so the test would need an exception list longer than
  its logic. Do not add it; a drifting figure is fixed in that recipe.
- **Undated — every oven figure in `cooking_methods.yml` says "fan"; none is
  left bare and none names a conventional temperature.** Helen, of the timings
  calculator: *"only one option has fan oven though, the rest say nothing...
  so 'fan' every time."* A bare figure cannot be acted on without guessing
  which oven it means, a 20°C guess either way.
  `test_every_oven_temperature_says_fan` in `tests/test_reference_data.py`
  reads each `oven` value, string or list of stage lines.

### The cocktails reference layer, #529

- **2026-09-06, #529 — a cocktails reference page must answer a question the
  cards stopped answering; a bare list does not pass #459.**
  `rum-categories.html` passes because of its bottles column: #501 moved
  *"which of mine is a Demerara rum?"* from the card to the reader when cards
  stopped naming bottles, and nothing answered it. A list of the fourteen
  names alone would be `rum_styles` reprinted. Apply the same test to any
  second page here.
- **2026-09-06 — the rum page has its own anatomy (the `.ref-` classes), in
  one hue.** A session's call, not Helen's ruling. Food's reference pages
  borrow `.recipe` and the site's only table CSS, all of it in `_sass/food/`,
  and cocktails' own anatomy is a drink's. Borrowed where there was something
  to borrow: the drink page's heading mark, and `.cocktail-suggestion`'s
  woowoo for a bottle name, because woowoo means asked for. A second hue is
  Helen's to choose.
- **2026-09-06 — the rum page is a table, with column labels on every section
  and one rum per line.** Helen, from candidates of table, stack or two
  columns: *"This is all table A"*. The other two were deleted, not left
  switchable. Labels repeat on every section, her call. One rum per line, her
  call, against a comma-separated sentence: the eight agricoles share their
  first two words and wrap into a ribbon, and a column you check your own
  shelf against is scanned, not read.
- **2026-10-15, #1379 — the rum shelves are Jamaican, "Demerara rum
  (Guyana)", "Other molasses rum", Cane juice, (rum-adjacent), Flavoured, then "Rum-based
  liqueurs".** Helen: *"Move the non-geographical section above the cane
  juice section, and rename it 'other molasses rum'"*. Guyana is in the
  Demerara heading *"to stay in step with Jamaica"*, chosen over a country
  label beside or under it. Flavoured holds only
  `pineapple-infused rum`; the coconut liqueurs and Créole Shrubb moved to the
  new last shelf. "Rum-adjacent" is still her word.
- **2026-10-15, #1379 — on "Other molasses rum" the bottles group by
  country, and a blend says "multi-country origin".** Helen: *"Add country
  names to group some of the rums… 'multi-country origin' is fine where
  applicable."* Gosling's is multi-country, with *"(blended in Bermuda)"*
  after its name on the rum page only. Her three Angosturas (5, 7, 1824) are
  the Trinidad & Tobago bottles, and `moderately aged rum`: an agent's
  reading of the shelf, which Helen confirmed (*"I agree with you!"*).
  Cruzan is under "US Virgin Islands".
- **2026-10-15, #1379 — the clairins stay four generics, and the rum page
  shows them as one "clairin" row, listed under HAITI.** Helen chose this
  over one `clairin` generic: *"closest to 1, but where a recipe lists
  clairin, every time it should note which"* — which the four generics
  already force. A bare "clairin" from a source is retired with that reason.
- **2026-10-15, #1379 — Créole Shrubb keeps its own generic; the rum page
  labels its row "fruit rum liqueur", with "(rhum-based)" after the
  bottle.** Helen chose the page-only label over a `fruit rum liqueur`
  generic, which would have let any fruit rum liqueur stand in for it
  (2026-09-05: *"it's not replaceable"*).
- **2026-10-15, #1379 — small rum-page rulings.** The "site display name"
  column is dropped from a section where no row has one. The rum-adjacent
  block has the head row. The retired-words and characters lists are
  alphabetical. `silver` and `amber` are retired as colour words.
  "Spanish-style" carries her note, and the characters take the retired
  words' face. Under rhum agricole vieux, HAITI reads *"(not strictly
  agricoles)"*.
- **2026-10-15, #1379 — the rum page's first prose paragraph is a sentence
  a paragraph, and a light dashed rule sits above "Rum tastes like
  sunshine."** Helen: *"let's split paragraph 1 please"* and *"to help the
  change of pace and temperature, let's try a light rule"*, the About page's
  pattern. Paragraph two stays whole. The rule is the column-label grey: the
  About page's border grey is invisible on the leopard.
- **2026-09-06 — `rum_groups` is declared, not derived, and the rum page walks
  the groups.** A session's call, not Helen's ruling: no rule recovers the
  shelves ("Jamaican" is in two of that shelf's three style names and absent
  from the third). The cost is that an unplaced fifteenth style would be
  invisible, which is what `test_rum_groups_partition_the_styles` is for. Any
  new top-level list in `ingredients.yml` that is not a vocabulary must join
  `NOT_GENERIC_LISTS`, or its members silently become valid generics, as
  `shopping_shelves` did.
- **2026-09-10, #813 — an agricole's country goes inside the bottles column,
  not into a row of its own.** Helen chose treatment A of three built on the
  real page. B, a row per country, rendered a cell reading "rhum agricole
  blanc, Martinique", which is the origin-qualified generic #591 had ruled
  against three days earlier. C, a tag on each bottle, interleaved the
  countries down the column. Any style whose bottles declare an `origin`
  groups; there is no special case for "Cane juice".
- **2026-09-10 — the sipping shelf is deleted, page and data both.** Helen
  removed the section from the page herself and, asked whether the ten names
  should survive in `bottles.yml` with no reader, said *"delete sipping
  entirely please"* (recorded in the page's header comment). She had asked for
  the shelf on 2026-09-06 (#782) to keep track of her collection, with a name
  *"a little against my religions because you can sip anything plus I can mix
  whatever I damn well want"*. Do not reinstate it.
- **2026-09-10, #784 — the retired rum words are a bare list: no reasons and
  no lines under them.** Helen first: *"my main wish is to get rid of most of
  the copy, to be honest! I just need to write a line or two under each rum
  label we aren't using."* Then, asked for those lines: *"I decided not to
  give silly rum words the dignity of extra copy. I want the list, bare, so
  please delete unneeded scaffolding."* The reasons stay in
  `retired_rum_styles` for the ingest and never render. The subtitles and the
  arrack note went the same way that day (#889–#891): before building a slot
  for her words, show her the page without it. (Replaces *"Leave reasons in
  full"* of 2026-09-06.)
- **2026-09-10, #921 — "blackstrap" stays on both the retired list and the
  characters list, and Characters is the page's last section.** Helen: *"It
  needs to stay in the words I don't believe in section because people say
  'use a blackstrap rum' which isn't a thing (to me). And then given I'm using
  it as a character on the site, I need to list it as a character."* On the
  retired list it reads "blackstrap (is a rum character not a rum type)", her
  whole line, written out as #975's title on 2026-09-11 after a session's
  paraphrase had shipped as copy. It is a lookup on `rum_characters`, so a
  second such word cannot arrive without it.
- **2026-09-10, #921 — links and the tab say "rum categories" and the h1 says
  "My Philosophy of Rum"; they disagree on purpose.** Helen: *"I need links to
  the page to stay as 'rum categories' because if links say 'my philosophy of
  rum' the reader expects stories about walks on the beach and my favourite
  tiki mug."* The label is wayfinding and the headline is voice. Do not make
  them agree.
- **2026-09-10, #921 — a rum category with no bottle shows an empty cell;
  "none in the house" is gone.** Helen: *"If we're not using them, delete
  them, boom."* The empty third track is the honest rendering, and a category
  with no bottle is not a gap to fill.
- **2026-09-11, #784 — the rum table's column headings are "category", "site
  display name" and "examples", all Helen's.** *"'category' is right."*, of a
  word still marked as a placeholder; *"site display name"* (2026-09-10), for
  the column that prints the shorter name a card uses. No placeholder is left
  on the page. Do not mark an approved string as one: it promises her a
  writing task she does not have and tells later sessions not to touch a
  finished word.
- **2026-09-11, #973 — the rum table's three column labels look the same, and
  pink is for bottles only.** Helen: *"also the column heading please -- leave
  the pink for the bottles."* (2026-09-10) and *"table headings use three
  different combinations of size and colour. I think they should all look the
  same."* The head row borrows the three cell classes for their grid tracks,
  and each brought a colour or a size along; the rule says `color: inherit;
  font-size: inherit` for all three. `.rum-origin-head` is untouched: she
  counted three, and its smaller size ranks the country labels below the
  column labels.
- **2026-09-11, #980 — the rum page is published.** Helen raised *"(feature)
  let's get the rum page ready for publication then publish it!"* the morning
  after *"no more until design isn't noticeably odd"*. `published: false` and
  `local_only: true` came off in one commit. The `local_only` machinery
  (`_config_local.yml`, the filter in `_layouts/default.html`, the inverted
  branch in `tests/test_page_links.py`) stays with no user on purpose, as the
  pattern for the next reference page: hiding a page with `published: false`
  alone leaves a footer link to a 404. (Replaces the local-only ruling of
  2026-09-06.)
- **2026-09-11, #972 — bottles on the rum page are listed alphabetically.**
  Helen: *"order example rums alphabetically."* Done with `sort_natural`
  (case-insensitive) wherever a list of names is built, never by hand-ordering
  `bottles.yml`, which four other consumers read and where a hand order goes
  stale at the next bottle. One consequence is hers to rule on if she dislikes
  it: El Dorado 12 sits above El Dorado 5.
- **2026-09-11, #985 — the rum page has three levels of vertical space, all
  from tokens: 1.5rem inside a section, `$spacing-section-gap` above a shelf
  heading, `$spacing-section-top` above a section rule.** Helen: *"add more
  space to breathe between sections on the rum page, especially before 'don't
  recognise' and above the section rule above it."* Section-from-section and
  table-from-table had been the same 1.5rem. The bigger half goes above the
  rule: there it divides two sections; below, it would only detach the rule
  from the heading it introduces.
- **2026-09-11, #920 — a wrapped heading on the rum page wears the mark under
  its last line only.** The rule food already had (Helen: *"Last line only
  please, 10000%."*). `.ref-section-heading > span` uses the last-line mixin
  and is its own selector in `last-line-rule.js`'s `TARGETS`, not a reuse of
  food's class. The fix of 2026-09-10 was inert for a day: a descendant `span`
  selector matched the spans the script creates and redrew the mark on them.
- **2026-09-15, #1086 — from the axe-core review: the footer's reference word
  is an 82% mix, three food controls have a real focus ring, and the ship icon
  is `aria-hidden`.** A session's calls, not Helen's rulings.
  `.site-footer-ref-word` at 65% measured 3.27:1; 82% gives 4.90:1 on food and
  4.71:1 on cocktails and still reads quieter than the links, so do not
  quieten it below 4.5:1 again. The food chips, `.page-search-input` and
  both sites' scaler − / + take a 2px `outline` on `:focus-visible`, never a
  change of size or border. The ship icon's rating word beside it already
  carries the meaning.
- **2026-10-15, #1394 — both sites' scaler − / + are one shape from one piece
  of code: 32px buttons, a 44px tap area, and the same focus ring.** Helen:
  *"the same executed code, not just the same bytes"*, and of the focus ring,
  *"the same same, not copied."* `scale-step` and `scale-controls` in
  `_sass/shared/_rule.scss`; each site passes only its colours and typeface.
- **2026-09-10 — the rum page's "two things I care about" list uses the about
  page's numbered-list styling.** Helen: *"please use the numbered list
  styling from the start of the about page for my 'two things I care about'
  bit."* `<ol class="ref-enum">` in `rum-categories.html`. It is one borrowed
  list, not a licence to bring the about page's other treatments across.
- **2026-09-10, #919 — the rum-adjacent block renders before the Flavoured
  shelf.** Helen: *"render rum-adjacent section before flavoured"*. Which
  shelf it precedes is `rum_adjacent_before` in `ingredients.yml`, and
  `test_rum_adjacent_before_names_a_real_group` fails if that shelf is
  renamed away.
- **2026-09-10 — links in the rum page's prose look like links: absinthe and
  underlined at rest, wicked woowoo on hover.** Helen: *"please format the
  links as links"*, *"or something from the cocktail palette that requests
  interaction"*. She also offered *"either as wicked woowoo and we call that a
  site decision"*; woowoo at rest was not taken, because on that page woowoo
  means a bottle. `.ref-prose a` in `_sass/cocktails/_reference.scss`.
- **2026-09-10 — the rum page's "two things" list uses the about page's
  numbered-list styling.** Helen: *"please use the numbered list styling from
  the start of the about page for my 'two things I care about' bit."*
  `.ref-enum` in `cocktails/reference/rum-categories.html` and
  `_sass/cocktails/_reference.scss`.
