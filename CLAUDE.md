# Claude Code Rules for Jekyll

## Environment Constraints
- OS: Ubuntu/Debian inside Windows Subsystem for Linux (WSL).
- Environment: Local Jekyll development.
- Target Directory: ONLY operate within this folder. Do not traverse to `../` or `/mnt/c/`.

## Critical Restrictions
- NEVER run `rm -rf` except in tmp/ without explicit human confirmation.
- Do not attempt to run `rm -rf` in the middle of a long job EXCEPT in folder "tmp/" within this working directory you were launched in. Complete the job first, then tidy up afterwards, to reduce interruptions.
- NEVER alter system configurations, `.bashrc`, `.bash_profile`, `.bash_aliases`, or install global apt packages.
- NEVER access or create `.env` files containing deployment API keys.
- NEVER run commands using the `--dangerously-skip-permissions` flag.
- **NEVER change file permissions without asking me first, every single time.** No `chmod`, no `chown`, no `sudo`. Ask, name the exact files, and wait -- a blanket "yes" to one chmod is not a standing permission for the next one. `.claude/settings.json` denies these three commands outright, but as with the `/tmp` rule above, Bash can't be perfectly restricted by permission patterns, so this line is the actual backstop. The one time this came up (2026-08-17) the fix was legitimate -- `.gh-runtime/bin/gh` and `.node-runtime/node/bin/node` had been extracted without their execute bit, which is why the JS test suite had silently not been running -- and it was still Helen's call to make, not mine.
- NEVER read, write or execute above the folder you're in.
- NEVER read, write or execute in `~` (my home directory) or anywhere outside this project folder, for any reason -- if Claude Code config/settings storage is ever needed, it belongs in this project's own `.claude/` folder, never `~/.claude/`.
- NEVER read, write or execute using the system `/tmp` directory (an absolute path starting `/tmp`). Use this project's own `tmp/` folder for all scratch and temporary files. Settings-level deny rules block this for the Read/Write/Edit tools, but Bash can't be perfectly path-restricted by permission patterns -- this rule is the actual backstop.
- NEVER use `$CLAUDE_JOB_DIR` or any path under `/home/helen/.claude/jobs/` as a scratch location, even though background-job tooling suggests it by default. All scratch/temporary files -- including any helper script written to a file specifically to avoid a shell-quoting/brace-expansion warning -- belong in this project's own `tmp/` folder, always.

## Build Commands
- Dev Server: `jekyll-local`, deploying to localhost:4001
- Prod Server: `jekyll-prod`, deploying to localhost:4002

## Git workflow
- If we're starting new work, and we're currently on main, please check out a new branch.
- Before creating a new branch, checkout out the main branch, then `git pull origin main`.
- Commit freely without asking.
- **NEVER commit or merge directly onto `main`, for any reason, even a one-line fix or an untangle/cleanup task.** The real workflow: work happens on a local branch; I push that branch myself; a PR is opened against `main`; I merge it (on GitHub); I pull `main` locally to update it. If you're on `main` and about to run `git commit` or `git merge`, stop and check out a branch first instead. `main` only ever moves via a pulled merge, never a direct local write.
- **This applies to EVERY repo in the working tree, not just `helen-triages`.** The nested private drafts repos (`_food_drafts/`, `_cocktail_drafts/`) are separate repos with their own `main`, and the same rule governs them: branch, never commit to `main`. Got this wrong on 2026-08-17 -- four commits went straight onto `_cocktail_drafts`' `main` because the rule read as if there were only one repo. They were moved to a branch and `main` reset to `origin/main`; nothing had been pushed.
- Never `git push` without my explicit confirmation first.
- **ALWAYS tag issues in commit messages.** If a commit resolves a GitHub Issue, add a `Fixes #N` (or `Closes #N`) trailer for every issue it resolves; if it only advances or touches one, cite it in the body (`Towards #N`, `See #N`). GitHub auto-closes on `Fixes`/`Closes` once the commit reaches `main`. Do this at commit time -- while nothing is pushed a message can still be rewritten, but after a push it is fixed. When summarising work, list the issue numbers involved.
- **A bare `#N` only resolves within its OWN repository.** The nested private drafts repos have their own (empty) trackers, so `Towards #314` in a commit there links to nothing. Cross-repo references need the full form: `Towards DeckOfPandas/helen-triages#314`.

## GitHub Issues -- read/write, and nothing else
- **Changed 2026-08-17.** This used to say read-only, always. Claude may now READ, RAISE, CLOSE, REOPEN, COMMENT ON, LABEL and ASSIGN issues on `DeckOfPandas/helen-triages`, `helen-triages-private` and `helen-triages-cocktails-private`, using the fine-grained token I supply via the `GH_TOKEN` environment variable. Those three repositories and no others.
- **Verified by measurement on 2026-08-17, not assumed** -- issues: raise 201, comment 201, assign 201, label 200, close 200. Everything else refused: writing a file 403, reading Actions secrets 403, commenting on a pull request 403, opening a pull request 403. Re-run those probes if the token is ever regenerated; a widened token is invisible until something unexpected succeeds.
- **`GET /user/repos` DOES NOT REVEAL A FINE-GRAINED TOKEN'S SCOPE.** It lists what the account owns -- all 59 repos -- regardless of which three the token selected, and reading that as the token's reach produced a confident, wrong report that the token covered everything. The honest probe is a permission-requiring call against a specific repo, or Helen's own token settings page, which lists the selected repositories outright.
- **That is the entire permission.** Never push code, never open or merge a pull request, never change repository settings, secrets, Actions, webhooks or collaborators, and never act on any other repository. The token is scoped so these are impossible; do not treat a 403 as a problem to route around.
- **Never attempt to broaden access.** No `gh auth login`, no requesting a wider token, no suggesting a classic token, no adding scopes. If something genuinely needs a permission the token lacks, say so and stop -- I will do it by hand.
- **Never print, echo, log or commit the token**, and never write it into a file in this repo. Read it from the environment at the point of use.
- Closing an issue is still a real action on a shared, outward-facing thing: say which issues you are about to close and why before doing it, unless I have just told you to close them.

## Normal workflow
- If you need a scratch temporary folder, create one in this project folder and add it to .gitignore
- Don't delete handover or jobs list documents.
- You don't need to ask permission to cd into folders at or below /home/helen/projects/helen-triages/food.
- You don't need to ask permission to read or write to tmp in /home/helen/projects/helen-triages/food.