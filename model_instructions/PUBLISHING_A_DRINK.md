# Publishing a drink — the steps, who does each, and what the words mean

Written 2026-09-04, on the day the first sixteen drinks went through it, for
Helen to check and for the next session to follow. It is short on purpose.
**Since 2026-09-14 (#1008) the same six steps carry a FOOD recipe too, and
`model_instructions/PIPELINE.md` §4 is the map both sites follow; this file
keeps the detail and the history of each step.**
**THERE ARE TWO STAGING FOLDERS FOR DRINKS SINCE 2026-09-18**: `4-promote/`,
which means waiting on Claude, and `5-final-proofread/`, which means waiting
on Helen. PIPELINE.md §3 is the authority on both. This preamble used to
promise that "every `to-promote/` below" meant `4-promote/` — a redirection
note that made sense for a week and had become a thing every reader held in
their head; the old name is gone from the steps instead.
**MANUAL §9.1.1 has the gate's mechanics and §4.0 says what the flags MEAN;
`.claude/commands/ingest.md` is how a drink gets INTO the drafts and where the
mechanical/non-mechanical boundary is stated in full.** This is the procedure
that carries a drink from there to the public repo, and it is linked from
MANUAL §11.

## The one working copy

For a batch in progress there is **one** working copy of the private drinks
repo: the clone inside the coordinating Claude's worktree, on a branch named
for the batch (`content/<what-the-batch-is>`). Helen edits there, Claude
commits and pushes there, and the dev server builds from there. Helen's own
local clone is not used while a batch is open — it is where promotion happens
afterwards (step 6), from `main`, after the branch is merged.

Two copies is how the first batch got tangled: sixteen files sat only on one
disk for an evening. One copy, always pushed, is the rule.

**NEVER START A DEV SERVER, AND NEVER OFFER TO. HELEN STARTS HER OWN.** Her
instruction, 2026-09-18, given to an offer to serve a finished batch for her
proofread: *"As a greater point, I start my own local servers, so don't do
that."* This paragraph used to say the batch was "served on a port the session
names when it opens the batch", which invited exactly the wrong thing. A
session's job is to say WHICH pages need reading and at what URLs —
`/cocktails/drafts/4-promote/<slug>/` — and stop there. `jekyll-local` and
`jekyll-prod` are hers to run; a background server a session starts is a
process she did not ask for, on a port she may already be using, outliving the
turn that made it.

## The steps

1. **Helen moves** a drink into `_cocktail_drafts/4-promote/`. The move is the
   signal; nothing else is needed. She tells Claude when a round of moves is
   done, because Claude will be editing the same files next.
   - **She sets `rewritten: true` herself — #1137, 2026-09-17.** The move used
     to be how she claimed it for a batch, and the mechanical pass flipped the
     flag for everything in this folder. It does not any more: `rewritten` is a
     LEG OF THE PUBLISH GATE for drinks now, and a flag that decides whether a
     page exists belongs with `proofread` — hers to type, never an agent's.
     **If a drink in here still says `rewritten: false`, it will not publish:
     say so and let her flip it.** Never infer it from the folder.
2. **Claude runs the mechanical pass** over everything in `4-promote/`:
   **touches no gate flag at all** — `rewritten` joined `proofread` and
   `awaiting_fix` as Helen's alone on 2026-09-17, and `ingest.md`'s TIER 3 says
   the same — runs the suite, fixes what
   the suite names — spellings the vocabularies already declare, a missing key,
   a hyphen that should be an en dash, a house name where a bottle belongs, an
   alias where the canonical name belongs, a scalar `suggestion` that should be
   a list — and never
   touches a tagline, a note's words, a method's words or an amount. **One
   exception, Helen's ruling on #1078 (2026-09-24): a note that a LATER ruling
   of hers has made false may be corrected or deleted by an agent**, naming the
   ruling in the commit — the case was two notes on a Sazerac draft still
   saying the Ferrand 1840 was a different bottle after she had ruled it the
   Ambré (#745). A note that is merely unconfirmed, or that she has not ruled
   on, is still hers. Commits and
   pushes. **The full boundary is in `ingest.md` under "Fixing a draft the
   suite is complaining about"; the two say the same thing on purpose.**
3. **Claude lists the non-mechanical things**, one line each, and Helen rules
   on them. Each ruling is written into the vocabularies, the manual and
   the ingest documents the same day, so it is never asked twice.
   - **Move those drinks into `5-final-proofread/` in the same commit as the
     list** (PIPELINE.md §3, 2026-09-18). It is the one folder an agent puts a
     file in, and the move IS the report: `4-promote/` then means *waiting on
     Claude* and `5-final-proofread/` means *waiting on Helen*, so neither she
     nor the next session has to re-read a chat message to tell them apart. It
     was asked for when a batch of seventeen produced ten bounce-backs and
     `4-promote/` stopped answering the question.
4. **Claude says "final: <slugs>".** That word means: the suite is green over
   those drinks, every open ruling is applied, and Claude will not touch
   those files again except to flip a flag Helen asks for or to open an
   `awaiting_fix` round. **Until Helen sees that word, the served pages are
   work in progress and not for proofreading.** (This is the step that was
   missing on the first day.)
5. **Helen proofreads** by reading each drink's built page on her own dev
   server — `/cocktails/drafts/<folder>/<slug>/` — and flips `proofread: true`
   in the file, or tells Claude the slugs and Claude flips them on her word.
   Reading the served page *is* the proofread; the flag says "I read this
   rendered and it is what I want". Claude commits, pushes, and Helen merges
   the branch on GitHub.
   - **SAY WHICH REPO THE BRANCH IS IN, AND HOW TO GET IT. THE URLs ARE
     USELESS WITHOUT THE FILES.** `_cocktail_drafts/` is a SEPARATE private
     repo, gitignored here (`.gitignore`), so **checking out the public branch
     brings no drink files at all** — not the folder move, not the flag flips,
     not a single edit from the batch. Her clone stays on its own `main` and
     the pages she is being sent to simply do not exist.

     This cost a session on 2026-09-19: ten URLs were handed over with no
     mention of the private branch, she checked out the public one, saw
     nothing change, and reasonably concluded something was broken. The fix is
     two commands and they belong in the message that gives the URLs:

         git -C _cocktail_drafts fetch origin
         git -C _cocktail_drafts checkout content/<the-batch-branch>

     **The general rule: "pushed" is not "she can see it".** Every handover in
     this file crosses two repos, and the drinks half is always the one that
     needs the extra step.
   - If a small thing is wrong: `awaiting_fix: true` in a commit that says
     what; fix between them; Helen re-reads (the whole page — drinks are
     short); flag back.
   - Claude does a final read-only review after the proofread; sometimes Helen
     does too.
   - **If a public PR depends on a private branch, name the branch in the PR
     description.** A public merge that lands before its private half leaves
     `main` red with failures naming real drinks (2026-09-06, the Caribbean
     Sazerac's `I want to faff`: `taxonomy.yml` merged, the drink file's
     correction sat on `data/caribbean-sazerac-faff`), and nothing else says
     which branch fixes it.
6. **Helen promotes**, herself, always, unless she explicitly asks Claude to:
   in her own checkouts, copy the proofread drink into `_cocktail_recipes/`
   in the public repo and commit; delete it from the private repo and commit.
   The public commit deploys.

   **SHE DELEGATED IT FOR THE FIRST TIME ON 2026-09-09/10, AND THE FIRST 48
   DRINKS WENT OUT THAT WAY.** Her reason was not that the step is hard, it
   was that the staging folder had become a haystack: *"please move all
   proofread: true files into the public repo. If you do this then I don't
   have to fish through one by one to find out which I still need to
   proofread."* Promotion is what keeps `4-promote/` meaning "waiting for
   Helen" rather than "everything, sorted by nothing".

   **PROMOTE FROM WHICHEVER FOLDER THE DRINK IS IN.** Since 2026-09-18 that
   is `4-promote/` or `5-final-proofread/` — both are the published tense
   (`STAGED_DIRS`), and a bounced-back drink that Helen has now passed goes
   straight out rather than taking a ceremonial hop back through `4-promote/`
   with a commit attached.

   **SIX THINGS THAT PROMOTION TURNED OUT TO NEED, none of them obvious
   until it was done for real:**

   - **RE-CHECK THE GATE, do not trust the flag as found.** All THREE legs
     since #1137 — `rewritten: true` AND `awaiting_fix: false` AND `proofread:
     true` — read out of the file at copy time, explicitly, failing closed.
     Copying a drink the gate would have hidden is the one mistake no later
     commit undoes, because the file is public the moment it merges.
   - **COPY, COMPARE, THEN DELETE.** Byte-for-byte, asserted. What publishes
     must be what she read, and a silent truncation between two repos is
     exactly the failure nothing else would catch.
   - **`git rm` WILL REFUSE, AND IT IS RIGHT TO.** It will not remove a file
     with changes in the worktree or the index, and flipping a flag in the
     same pass is exactly that. **Do not reach for `-f`**: forcing gets past
     it by DISCARDING those changes, so if a copy had failed there would be
     nothing left to notice. Unlink the file and let `git add -A` record it,
     after the byte comparison.
   - **`COCKTAIL_BASELINE_COMMIT` HAS TO MOVE, and that is Helen's to grant.**
     `test_agent_edited_drinks_are_not_marked_proofread` reads the PUBLIC
     repo's history only (#624), so it cannot tell a promotion from an edit:
     it sees drinks marked `proofread: true` appearing in an agent's commit.
     Move the constant to the promotion commit, in a commit OF ITS OWN so she
     can revert just that, and prove the guard still bites afterwards by
     breaking it on purpose. See the constant's own comment in
     `tests/test_cocktails.py`.

     **The proof is cheap and it is not optional: run the test with the OLD
     value and read the names.** It should name exactly the drinks you
     promoted and nothing else. Four moves went through on 2026-09-18/19 and
     each one was proved that way; a move that names a drink you did not
     touch is a move that is grandfathering something you have not looked at.

   - **CHECK THE PROMOTED PAGES BY NAME IN THE PRODUCTION BUILD.** `sh
     scripts/browser/build.sh`, then assert each slug exists at
     `tmp/site/cocktails/recipes/<slug>/index.html`. **The gate fails closed,
     so a drink with a flag wrong is simply ABSENT — which looks exactly like
     nothing going wrong.** Copying the file and committing it proves nothing
     about whether it publishes.

     It is also the only thing that finds a drink held back for an unrelated
     reason: that check printed 65 files against 64 pages on 2026-09-19 and
     turned up Smokestack Lightning, `proofread: false` since 2026-09-16 and
     off the live site for three days with nobody looking. **Count the files
     and count the pages; the difference should be exactly the drinks Helen is
     deliberately holding.**

   - **RUN `scripts/verify.py`, NOT THE SUITE YOU HAVE BEEN RUNNING.** A
     promotion batch makes `tests/test_cocktails.py` feel like the whole
     world, and it is not: the moment a commit touches `_data/`, the generated
     standalone documents go stale and only the full run notices. A garnish
     rename on 2026-09-19 passed the cocktails suite and failed two
     `test_standalone_docs.py` checks plus the ingest-vocabulary check, all of
     which `verify.py` runs and MANUAL §1 calls "the two checks that get
     forgotten". **A narrow suite stops being the right check the moment you
     edit a vocabulary, however green it is.**

## What the flags mean, in one line each

- `rewritten: true` — the words are Helen's. **Only she writes it, and since
  #1137 (2026-09-17) that is literal: no folder, no batch and no agent sets it.**
  It is the drinks gate's third leg, so a drink with it `false` does not
  publish at all.
- `made_before: false` — she has not made it yet, and **it publishes anyway**
  (#722, 2026-09-05): the live site is where she picks what to try next, and
  she reads the drink there while making it, which beats exporting a PDF. The
  pair is the rule and the two halves are easy to swap by mistake: **unmade is
  fine, unrewritten is not.** She rewrites a drink before she makes it.
- `awaiting_fix: true` — one thing is ticketed; she has read it; it will not
  publish until the flag is false again.
- `proofread: true` — she read the rendered page. Any agent edit after that
  sets it false again in the same commit (issue #367), which takes the drink
  off the live site until she reads it again. That is the point.

## What "promotion-ready" means for the data

In `4-promote/`, in `5-final-proofread/` and in `_cocktail_recipes/` a drink is
in its published tense: every `suggestion` is a bottle's canonical name
(aliases are for reading drafts, never for a published file) **and is a LIST
even when it names one bottle**, and every generic is a declared one. Tests in
`tests/test_cocktails.py` hold all of that, so the mechanical pass cannot
forget it.

**`STAGED_DIRS` IS THE LIST, AND IT IS A LIST FOR A REASON.**
`5-final-proofread/` joined on 2026-09-18 (`PIPELINE.md` §3): a drink is there
because it was staged and bounced back for a ruling, so it is going live the
moment Helen answers, and it sits in a folder being edited for longer than
anything else in the pipeline — which is precisely when a shorthand alias or a
stray `item` creeps in. Had the constant stayed singular, the two staged rules
would have stopped applying to exactly those drinks, quietly and green.

**`item` IS NO LONGER A PROMOTION CONCERN, since 2026-09-05.** It used to be
one of the things the staging folder checked for, on the reasoning that the
transcription field lives in drafts only. It now has to be gone from ANY pour
whose `generic` is filled in, drafts included —
`test_item_is_gone_once_the_generic_is_filled_in` — so by the time a drink is
promotable the field went long ago. A fresh ingest still writes it, beside
`generic: "QQ"`; that is the one state where it is correct.

## Where the rulings live

- Bottles and their aliases, and the "a house is not a bottle" rule:
  `_data/cocktails/bottles.yml`, MANUAL §9.3.2. **A bottle she no longer
  reaches for is MOVED to `not_reached_for` with its reason, never deleted** —
  five went that way on 2026-09-05 and the reasons are why nobody re-adds them.
- **What things cost: `_data/cocktails/costs.yml`, MANUAL §9.3.5.** Prices are
  LOCAL-ONLY on the site (`show_costs` in `_config_local.yml`) but the data is
  public, and it is the one file in `_data/cocktails/` that goes stale on its
  own — `checked:` says when it was last true. **Retiring or renaming a bottle
  means editing this file too**; `test_every_declared_bottle_carries_a_price`
  fails in both directions if you forget.
- Generics, syrups, honey water, the whole-fruit units: `_data/cocktails/ingredients.yml`.
- Method steps and the automatic twist step: `_data/cocktails/methods.yml`.
- **The ice and the rim: `_data/cocktails/serve.yml`** — a `serve` block on the
  drink, not prose in a method step. The page COMPOSES "Strain into an old
  fashioned glass, over a large ice cube." from `method`, `glasses.yml`'s
  `serving` phrase and `serve.yml`'s `in_the_glass` clause, so a promoted drink
  stores each fact once. MANUAL §9.10a.
- The garnish vocabulary and the articles the generated garnish step uses:
  `_data/cocktails/garnish.yml`.
- The ingest rules a session with no repo can use: `INGEST_ONE_COCKTAIL.md`.
  Its vocabulary blocks are generated — `scripts/build_ingest_vocab.py --write`
  after any ruling that changes `_data/`, never a hand edit — and the file is
  re-uploaded to the claude.ai Project (`CLAUDE_WEB_INGEST.md`) whenever it
  changes.
- The in-repo procedure: `.claude/commands/ingest.md`.
- The flags' meaning and the gate: MANUAL §4.0 and §9.1.1.
- The one-working-copy rule, restated where a worktree is set up: MANUAL §9.1
  and §11.0.1.
