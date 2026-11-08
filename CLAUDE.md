# Claude Code Rules for helen-triages

@.claude/kit/RULES.md

## This project
The rules above come from the kit (helen-contains-claude-webdev) and change
only through `/kit-sync`; an improvement to one is a kit PR, never an edit
here. These are helen-triages' own. Helen's rulings and her reasons live in
`model_instructions/DECISIONS.md`, the journal; how the machinery works today
lives in `model_instructions/MANUAL.md`. A `DECISIONS §n` points you at the
argument. **Do not re-open a settled question without reading its section
there first** — that is the thing Helen least wants. Grep
`model_instructions/DECISIONS_INDEX.md` to find it: one generated line per
ruling.

## Environment
- A Jekyll site, in the kit's container on WSL. **Only operate within this
  folder**: never `../`, `/mnt/c/`, `~`, the system `/tmp` or
  `$CLAUDE_JOB_DIR`.
- **Read-only exceptions: `/opt` (the image's Playwright) and
  `/workspace/.claude/worktrees/`.** Use the second: a helper agent's
  screenshots and scratch scripts are in its worktree's `tmp/`, and a
  supervisor that will not open them is reporting work it has not looked at.
  Never write in a worktree that is not yours. If the session refuses the
  read, that is the mechanism lagging the rule: ask Helen for `/add-dir`.
- **`Read(//dev/null)` and `Edit(//dev/null)` stay in the settings**
  (DECISIONS §11), whatever one tool's refusal suggests.
- NEVER run commands with `--dangerously-skip-permissions`, and never
  install a global apt package.
- Tidying `tmp/` waits until a job is finished, so the job is not
  interrupted.
- Dev server `jekyll-local` (container 4001, host **5998**); production
  `jekyll-prod` (4002, host **5999**); both need `bundle install` once per
  fresh bundle volume. **This project overrides the kit's server rule**:
  serve your own worktree with `bundle exec jekyll serve --config
  _config.yml,_config_local.yml --port <4001|4002> --host 0.0.0.0
  --destination tmp/site-<port>` and give Helen `http://localhost:5998/helen-triages/`
  (or 5999). MANUAL §13.11.

## The kit, here
- `_kit_upstream/` is the working clone for kit PRs (`git-nested.sh` works in
  it); `tmp/kit` is the clean clone `/kit-sync` reads. Both are gitignored.
- **`.devcontainer/devcontainer.json` is watched** (`.claude/kit/watched`):
  ours, and a sync only reports kit changes to its template.
- **No kit-owned, generated or watched path is ever part of the site build**;
  `tests/kit/test_site_excludes_kit.py` holds `_config.yml`'s `exclude:` to it.
- **`scripts/github.local.conf` is Helen's**, in the main checkout: the repos,
  `MAIN_PUSH_REPOS`, `PR_ONLY_REPOS` and `NESTED_DIRS`. Never edit it.
- Our allows and denies are in `.claude/settings.project.json`; each
  open-ended one has its note in `_reviewedOpenRules`. Run
  `python3 tools/kit/build.py` after editing it.

## Git and GitHub
- **Four repos and no others**: `DeckOfPandas/helen-triages`,
  `helen-triages-food-private` and `helen-triages-cocktails-private` (read,
  raise, close, reopen, comment on, label and assign issues; open PRs), and
  the kit, `DeckOfPandas/helen-contains-claude-webdev` (read and open PRs,
  never push to its `main`). That is the entire permission. DECISIONS §11.
- **MERGING IS PREVENTED BY NOTHING BUT THIS LINE, SO TREAT IT AS ABSOLUTE.**
  `AGENT_GH_TOKEN`, the agent account's classic PAT with `repo` and
  `workflow` scope, CAN merge. Never merge, close as merged or approve a PR.
  Never change repository settings, secrets, Actions, webhooks or
  collaborators. Never ask for a wider token, more scopes or a second
  credential: if something needs one, say so and stop.
- **Pushing runs as `DeckOfPandas-agentic-claude`; commits stay authored as
  Helen** with the `Co-Authored-By: Claude` trailer. Read `.user.login` off
  what a write returns rather than assume it.
- **The two private drafts repos: a small set of changes may be pushed
  straight to their `main`; a bigger footprint is a PR.** You still commit on
  a branch there. **Pushing from a drafts clone, give its `dir` as well as its
  `repo`, every time**: a drafts branch pushed at the public repo publishes
  private recipes.
- **ONE PR PER FEATURE OR OBVIOUS GROUP OF WORK** — not one per sitting, not
  one per commit. Every merge to `main` is a deploy, so keep each topic its
  own commit and say in the description what each commit is. DECISIONS §11.
- **A RED `main` IS A DEPLOY OUTAGE, NOT A RED BUILD.** The suite gates the
  deploy, so one red merge stops every later merge going live, silently.
  `sh scripts/main-ci-status.sh` after any merge you make or hear of, and a
  red one is the first thing to report. Never merge over a known-red suite.
  If you have been told nothing about a merge, check rather than assume.
  MANUAL §10, DECISIONS §12.
- **Close an issue with a commit trailer, not the API, whenever a trailer can
  do it**, and the closing line in the PR description too, one keyword per
  issue per line, never a comma list. The API is for where a trailer cannot
  work, such as work in a drafts repo. Read the issue list after the merge.
- **A workflow file is an ordinary PR**, but an invalid one blocks every
  merge: parse the YAML and run `tests/test_site_config.py` before pushing.
- **NEVER `git reset --hard`, `git checkout --`/`git restore` over a dirty
  tree, or `git clean -fd` without asking Helen first, every time.** Check
  `git status` and say what it shows.
- `gh` is `sh scripts/gh-agent.sh <args>`, which never names the token.
  **`gh pr edit` fails on this token**: change a PR's body with
  `sh scripts/gh-write.sh pr-body <repo> <N> tmp/<file>.md`.

## Proofreading — Helen is the last judgement before a recipe publishes
- **If you edit a recipe file, on either site, set `meta.proofread: false` in
  the SAME commit.** Helen proofreads every one by hand before it goes live;
  if Claude changes the file afterwards, her proofread no longer covers what
  is in it. **This applies to any change, including ones that look safe.**
  The one standing exception: a tag or star change Helen has agreed row by
  row keeps her flag, and `BASELINE_COMMIT` moves to it in the next commit.
  DECISIONS §4.0.
- **THE GATE FAILS CLOSED: a food or cocktail recipe publishes only if it
  says `awaiting_fix: false` AND `proofread: true`, and a cocktail must also
  say `rewritten: true`.** **`rewritten` is Helen's to write, like
  `proofread`: an agent never sets it, on either site.** Either flag missing,
  the old hyphenated `awaiting-fix`, or a quoted string: all held back, and
  all break a test. **Never write the hyphenated form** — Liquid parses
  `page.meta.awaiting-fix` as SUBTRACTION. The mechanism is
  `_plugins/publish_gate.rb`, whose build-log line names the flag that held
  each page back.
- `tests/test_front_matter.py::test_agent_edited_recipes_are_not_marked_proofread`
  enforces it from git history: a recipe whose newest commit carries a
  `Co-Authored-By: Claude` trailer must say `proofread: false`. Cocktail
  recipes have the same test.
- **The exception is Helen's to grant, not yours.** If she has reviewed the
  change line by line, move `BASELINE_COMMIT` (or `COCKTAIL_BASELINE_COMMIT`
  in `tests/test_cocktails.py`) forward in a commit of its own, quoting her
  grant, and prove it by running the test with the old value and watching it
  name the files. **Never move it to make a red test go green.** Cheapest: if
  she reads the rendered pages on the branch and says so, flip the flags back
  in a second commit and move the baseline in a third.
- **`QQ` is Helen's placeholder.** Never fix it or convert it, and never
  delete a `QQ original` line.
- **Promotion is Helen's to start.** Claude never decides a file is ready and
  never moves one to the public repo unasked. `model_instructions/PIPELINE.md` §4.

## The drafts and the suite
- **CLONE THE TWO PRIVATE DRAFTS REPOS INTO A FRESH WORKTREE WHENEVER YOU WANT
  THEM. NO ASK.** Cloning is reading; both folders are gitignored. Never
  symlink them.

      sh scripts/git-clone-agent.sh helen-triages-cocktails-private _cocktail_drafts
      sh scripts/git-clone-agent.sh helen-triages-food-private _food_drafts

  **WITHOUT THEM TWO THIRDS OF THE SUITE DOES NOT EXIST**, and it reports
  green rather than absent. **A green `pytest` in a bare worktree is not
  evidence about the cocktail recipes or the drafts** — the session-start
  hook and `conftest.py` both say so. Fetch a clone
  (`sh scripts/git-fetch-agent.sh <dir> <repo>`) immediately before any run
  whose result you will act on. MANUAL §9.1.
- `python3 scripts/verify.py` is the full check before a push; part of the
  suite is `sh scripts/pytest.sh tests/<path>`, never `pytest <args>`.

## Writing — replace, never append
Helen: *"Through this whole project I have begged to delete and replace
rather than just append!"* `tests/test_comment_rule.py` holds a comment's
length and its dates, as a ratchet over what predates the rule; for the rest,
these lines are the enforcement.
- **A comment: one pointer at most** (`#N`, `MANUAL §n` or `DECISIONS §n`),
  no quotations, at most eight lines a block, fifteen for a file header.
- **`MANUAL.md` is the present tense**: what is true today, with no history.
  When something changes, rewrite the paragraph that describes it.
- **`DECISIONS.md` holds one short entry per LIVE ruling of Helen's**: the
  date and issue, the ruling, her words, her reason. **When a ruling changes,
  REPLACE its entry**; a bug story is not a ruling. Then
  `python3 scripts/build_decisions_index.py --write`.

## Working with Helen
- **Ask her the decisions as you hit them, inline**, with the fact that forces
  each. For anything visual, build candidates on the real page and let her
  look (MANUAL §13.11); do not argue for one.
- When you finish, say: what changed and where, the local URL serving it,
  what you verified and how, which issues the commits close or touch, which
  PRs are waiting on her (here, in the private repos and in the kit), and
  anything left undone and why.
- Don't delete handover or jobs list documents.
