# Publishing a cocktail — the steps, who does each, and what the words mean

The procedure that carries a recipe from `4-promote/` in a private drafts repo
to the public repo. `PIPELINE.md` §4 is the short version of these six steps,
under the same numbers; this file is the detail. The steps are written for a
cocktail and carry a food recipe too, with `_food_drafts/`, `_food_recipes/`,
`BASELINE_COMMIT` and `test_agent_edited_recipes_are_not_marked_proofread` in
`tests/test_front_matter.py`, no fifth folder, and a gate of two legs
(`awaiting_fix: false` and `proofread: true`).

Owned elsewhere, and not restated here: the folders and the words that move a
file (`PIPELINE.md` §3); what the gate flags mean and how the gate works
(MANUAL §4.0, §9.1.1); how a cocktail gets into the drafts, and the full
boundary between mechanical and not (`.claude/commands/ingest.md`); git,
pushing and PRs (`CLAUDE.md`).

## The one working copy

For a batch in progress there is **one** writable copy of the private
cocktails repo: the clone inside the coordinating Claude's worktree, on a
branch named for the batch (`content/<what-the-batch-is>`). Helen edits there
and Claude commits and pushes there. Helen's own local clone is not written to
while a batch is open. One copy, always pushed: a commit that sits unpushed on
one disk exists in one place.

**Never start a dev server, and never offer to. Helen starts her own:** *"I
start my own local servers, so don't do that."* A session says which pages
need reading and at what URLs (`/cocktails/drafts/4-promote/<slug>/`) and
stops there. `jekyll-local` and `jekyll-prod` are hers to run; a server a
session starts is a process she did not ask for, on a port she may already be
using, outliving the turn that made it.

## The steps

1. **Helen moves** a cocktail into `_cocktail_drafts/4-promote/`, or says
   `ready <slug>`. She tells Claude when a round of moves is done, because
   Claude will be editing the same files next.
   - **She sets `rewritten: true` herself.** It is a leg of the publish gate
     for cocktails, and a flag that decides whether a page exists is hers to
     type, never an agent's. If a recipe in this folder still says
     `rewritten: false` it will not publish: say so and let her set it. Never
     infer it from the folder.
2. **Claude runs the mechanical pass** over everything in `4-promote/`. It
   touches no gate flag. It runs the suite and fixes what the suite names:
   spellings the vocabularies already declare, a missing key, a hyphen that
   should be an en dash, a house name where a bottle belongs, an alias where
   the canonical name belongs, a scalar `suggestion` that should be a list. It
   never touches a tagline, a note's words, a method's words or an amount.
   - **One exception: a note that a later ruling of Helen's has made false may
     be corrected or deleted by an agent**, naming the ruling in the commit
     (#1078). A note that is merely unconfirmed, or that she has not ruled on,
     is still hers.
   - Commit and push. The full boundary is in `ingest.md`, under fixing a
     draft the suite is complaining about; the two say the same thing on
     purpose.
3. **Claude lists the non-mechanical things**, one line each, and Helen rules
   on them. Each ruling is written into the vocabularies, the manual and the
   ingest documents the same day, so it is never asked twice.
   - **Move those cocktails into `5-final-proofread/` in the same commit as
     the list** (`PIPELINE.md` §3). The move is the report: `4-promote/` then
     means waiting on Claude and `5-final-proofread/` means waiting on Helen,
     so nobody re-reads a chat message to tell them apart.
4. **Claude says "final: <slugs>".** That word means: the suite is green over
   those cocktails, every open ruling is applied, and Claude will not touch
   those files again except to open an `awaiting_fix` round or change a flag
   Helen asks for. **Until Helen sees that word, the served pages are work in
   progress and not for proofreading.**
5. **Helen proofreads** by reading each cocktail's built page on her own dev
   server, at `/cocktails/drafts/<folder>/<slug>/`, and sets `proofread: true`
   in the file. Reading the served page is the proofread; the flag says "I
   read this rendered and it is what I want".
   - **Say which repo the branch is in, and how to get it. The URLs are
     useless without the files.** `_cocktail_drafts/` is a separate private
     repo, gitignored here, so checking out the public branch brings no
     cocktail files at all: her clone stays on its own `main` and the pages
     she is being sent to do not exist. "Pushed" is not "she can see it". Put
     these in the message that gives the URLs. **They are Helen's, to run on
     her own machine; a session cannot run them** (the hooks refuse `git -C`,
     and a session fetches with `sh scripts/git-fetch-agent.sh`):

         git -C _cocktail_drafts fetch origin
         git -C _cocktail_drafts checkout content/<the-batch-branch>

   - If a small thing is wrong: `awaiting_fix: true` in a commit that says
     what; fix between them; Helen re-reads the whole page (a cocktail recipe
     is short); flag back.
   - Claude does a final read-only review after the proofread; sometimes Helen
     does too.
   - **If a public PR depends on a private branch, name the branch in the PR
     description.** A public merge that lands before its private half leaves
     `main` red with failures naming real cocktails, and nothing else says
     which branch fixes it.
6. **Promotion happens on Helen's word.** The proofread cocktail is copied
   into `_cocktail_recipes/` in the public repo and deleted from the private
   repo, each as a commit; the public one reaches `main` by a PR Helen merges,
   and the merge is the deploy. Promoting what she has passed is what keeps
   the staging folders meaning "still waiting" rather than "everything".

   **Promote from whichever folder the cocktail is in**, `4-promote/` or
   `5-final-proofread/`. Both are the published tense (`STAGED_DIRS`), and a
   bounced-back cocktail that Helen has passed goes straight out rather than
   back through `4-promote/`.

   `scripts/promote.py` does not exist, so these six paragraphs are the
   procedure:

   - **Re-check the gate; do not trust the flag as found.** All three legs,
     `rewritten: true` and `awaiting_fix: false` and `proofread: true`, read
     out of the file at copy time, explicitly, failing closed. Copying a
     cocktail the gate would have hidden is the one mistake no later commit
     undoes, because the file is public the moment it merges.
   - **Copy, compare, then delete.** Byte-for-byte, asserted. What publishes
     must be what she read, and a silent truncation between two repos is the
     failure nothing else would catch.
   - **`git rm` will refuse, and it is right to.** It will not remove a file
     with changes in the worktree or the index. Do not reach for `-f`: forcing
     gets past it by discarding those changes, so if a copy had failed there
     would be nothing left to notice. Delete the file after the byte
     comparison and stage the deletion: `sh scripts/git-drafts.sh
     _cocktail_drafts add -- <paths>`.
   - **`COCKTAIL_BASELINE_COMMIT` has to move, and that is Helen's to grant.**
     `test_agent_edited_drinks_are_not_marked_proofread` reads the public
     repo's history only, so it cannot tell a promotion from an edit: it sees
     cocktails marked `proofread: true` appearing in an agent's commit. Move
     the constant to the promotion commit, in a commit of its own so she can
     revert just that. **Then prove it: run the test with the old value and
     read the names.** It should name exactly the cocktails you promoted and
     nothing else; a move that names a cocktail you did not touch is
     grandfathering something you have not looked at. The constant's own
     comment in `tests/test_cocktails.py` and `CLAUDE.md` (Proofreading) have
     the rule.
   - **Check the promoted pages by name in the production build.** `sh
     scripts/browser/build.sh`, then check each slug exists at
     `tmp/site/cocktails/recipes/<slug>/index.html`. The gate fails closed, so
     a recipe with a flag wrong is simply absent, which looks exactly like
     nothing going wrong; copying the file and committing it proves nothing
     about whether it publishes. Count the files and count the pages: the
     difference should be exactly the cocktails Helen is deliberately holding.
     `python3 scripts/dark_pages.py` lists them.
   - **Run `python3 scripts/verify.py`, not the suite you have been running.**
     A promotion batch makes `tests/test_cocktails.py` feel like the whole
     world, and it is not: the moment a commit touches `_data/`, the generated
     standalone documents go stale, and only the full run, with its
     `build_ingest_vocab.py --check`, notices. A narrow suite stops being the
     right check the moment you edit a vocabulary, however green it is.

## What the flags mean, in one line each

- `rewritten: true` — the words are Helen's. Only she writes it: no folder, no
  batch and no agent sets it. It is the cocktails gate's third leg, so a
  recipe with it `false` does not publish at all.
- `made_before: false` — she has not made it yet, and **it publishes anyway**:
  the live site is where she picks what to try next, and she reads the recipe
  there while making it. The two halves are easy to swap by mistake: unmade is
  fine, unrewritten is not. She rewrites a cocktail recipe before she makes it.
- `awaiting_fix: true` — one thing is ticketed; she has read it; it will not
  publish until the flag is false again.
- `proofread: true` — she read the rendered page. Any agent edit after that
  sets it false again in the same commit, which takes the recipe off the live
  site until she reads it again. That is the point.

## What "promotion-ready" means for the data

In `4-promote/`, in `5-final-proofread/` and in `_cocktail_recipes/` a
cocktail recipe is in its published tense: every `suggestion` is a bottle's
canonical name (aliases are for reading drafts, never for a published file)
and is a list even when it names one bottle, every generic is a declared one,
and no `QQ` is left. Tests in `tests/test_cocktails.py` hold all of that over
`STAGED_DIRS`, so the mechanical pass cannot forget it. A file in
`5-final-proofread/` is edited for longer than anything else in the pipeline,
which is when a shorthand alias creeps in, and why the constant lists both
folders.

## Where the rulings live

- Bottles and their aliases, and the "a house is not a bottle" rule:
  `_data/cocktails/bottles.yml`, MANUAL §9.3.2. A bottle she no longer reaches
  for is moved to `not_reached_for` with its reason, never deleted; the
  reasons are why nobody re-adds it.
- What things cost: `_data/cocktails/costs.yml`, MANUAL §9.3.5. Prices show
  only locally (`show_costs` in `_config_local.yml`) but the data is public,
  and it is the one file in `_data/cocktails/` that goes stale on its own;
  `checked:` says when it was last true. Retiring or renaming a bottle means
  editing this file too: `test_every_declared_bottle_carries_a_price` fails in
  both directions if you forget.
- Generics, syrups, honey water, the whole-fruit units:
  `_data/cocktails/ingredients.yml`. Source wordings Helen has ruled on:
  `_data/cocktails/source_wordings.yml`.
- Method steps and the automatic twist step: `_data/cocktails/methods.yml`.
- The ice and the rim: `_data/cocktails/serve.yml`, as a `serve` block on the
  cocktail, not prose in a method step. The page composes "Strain into an old
  fashioned glass, over a large ice cube." from `method`, `glasses.yml`'s
  `serving` phrase and `serve.yml`'s `in_the_glass` clause, so a promoted
  recipe stores each fact once. MANUAL §9.10a.
- The garnish vocabulary and the articles the generated garnish step uses:
  `_data/cocktails/garnish.yml`.
- The ingest rules a session with no repo can use: `INGEST_ONE_COCKTAIL.md`.
  Its vocabulary blocks are generated: `python3 scripts/build_ingest_vocab.py
  --write` after any ruling that changes `_data/`, never a hand edit. A
  claude.ai chat reads it from `main` by URL (`CLAUDE_WEB_INGEST.md`).
- The in-repo ingest procedure: `.claude/commands/ingest.md`.
- Working in a worktree with a drafts clone: MANUAL §9.1 and §11.0.1.
