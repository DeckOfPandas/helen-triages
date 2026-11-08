# The kit's rules

**These are the RULES.** `CLAUDE.md` imports them into every session, so keep
them short. Where a rule names a hook, the hook enforces it. Where it names
none, this paragraph is the only enforcement. The kit
(helen-contains-claude-webdev) owns this file: change it there, never in a
project. A project's own rules, and any it sets against these, are in its
`CLAUDE.md`.

## Environment
- Claude runs inside the container started by `.devcontainer/run.sh`. Only this
  project is mounted, at `/workspace`. The SessionStart hook says if a session
  is NOT in the container: say so before doing anything else.
- **A session starts at the project root or in one of its worktrees, never
  inside a nested clone.** There, neither these rules nor any hook load. A
  container-wide SessionStart hook (`.claude/hooks/session-place.py`) warns:
  if it does, say so before doing anything else.
- A change to `.devcontainer/` (packages, toggles) reaches the container when
  I run that worktree's `.devcontainer/run.sh` from the host, or after merge.
  Tell me which.
- **Scratch files go in this project's `tmp/`** (gitignored), never the system
  `/tmp`, never `~`, and never `$CLAUDE_JOB_DIR` or the jobs folder that
  background-job tooling suggests.
- **Show me a branch on a server; never ask me to pull and build.** Read
  `PORTS` in `.devcontainer/kit.env` (`host:container` pairs), run `ss -ltn`
  and take a free container port, serve your own worktree in the background on
  `0.0.0.0:<container port>`, and give me `http://localhost:<host port>/`, plus
  the `baseurl` from `_config.yml` for a Jekyll site. Never stop a server you
  did not start. No free pair in `PORTS` means I can't reach it: ask me to add
  one.
- **Tests:** one test run at a time, never two. The whole suite is
  `python3 -m pytest`; part of it is `sh scripts/pytest.sh [-q] [-x] [-v]
  [-k <expr>] tests/<path>...`, never `python3 -m pytest <args>`, which asks
  me. A green run proves only what
  ran: an empty parametrisation reports as one skip, not as missing tests, so
  never let a check return early because a scan came back empty.
- Visual checks (Playwright on): `node tools/dev/shoot.js <base-url> <label>
  [--engine webkit] [--scheme dark] [--click <text>] [--type <text>] <page>...`
  writes `tmp/shots/` (WebKit is the engine nearest Safari), and
  `node tools/dev/slice-png.js tmp/shots/<file>.png` cuts a tall one. For one
  element up close, `node tools/dev/crop.js <base-url> <label> <selector>
  [<page>] [--click <selector>]`; for its box and computed styles,
  `node tools/dev/styles.js <base-url> <selector> [<page>]`; for the spacing
  under it, `node tools/dev/gaps.js <base-url> <selector> [<page>]`; for
  where the ink sits inside a crop, `python3 tools/dev/inkbox.py
  tmp/shots/<file>.png`. Use these rather than writing new ones in `tmp/`. A page is relative to the base URL
  (`.`, `about/`), never `/about/`: a leading `/` reads as a path outside.
- Reads outside the working directory are refused, except `/opt` and other
  agents' worktrees. Use `/dev/null` only as a redirection (`> /dev/null`,
  `2>/dev/null`, `< /dev/null`), which is never checked. As a command argument
  (`curl -o /dev/null`) it is a read outside that no allow rule lifts:
  name a file under `tmp/` instead. `guard-dev-null.py` enforces it.
- **Paths are relative to the working directory.** No leading `cd`, no
  `git -C`, no absolute paths into the project.
- **One plain command per Bash call.** Anything that needs a loop, a chain, a
  pipe, or a variable or `$(...)` expanded into a command goes in a script in
  `tmp/` with every argument written out literally, run as `sh tmp/<name>.sh`.
  Programs go in files too: never `python3 -c` or `node -e`. Keep `=` off
  the start of a word or a regex alternative (`'a|=b'`), quoted or not: the
  checker reads it as zsh's `=cmd` and asks me. To find text in a file, the
  Read tool asks nothing. `guard-unanalyzable-bash.py` and
  `guard-inline-script.py` enforce it.
- **A subagent you brief gets these rules from you**: one plain command per
  call, relative paths because it is already in the root, no `cd`, cleverness
  in a `tmp/` file. A brief that names an absolute working directory gets that
  path typed into its commands, and every one asks me.
- **Every Bash `description` says what the call reads or writes, and where**
  ("Read-only GitHub GET of PR 12's state"), not just its goal. A prompt I have
  stopped reading guards nothing.
- **Never `sed` or `awk`**, in any form. Use the Edit tool, or Python in a
  file. `guard-sed.py` and `guard-awk.py` enforce it.
- **A command that must reach outside the working directory becomes a script
  in `scripts/`** with one fixed action and validated arguments, its safety
  stated in its header, and dry-run tests. Ask me before allowing it in
  `.claude/settings.json`. `scripts/git-diff-main-checkout.sh` is the model.
- **An allow rule is only as narrow as what it lets through.** Before adding
  one, ask what the prompt it removes was the last guard of: a rule ending
  ` *` accepts any option, and `git clone --template=`, `node --import` and
  `curl -o <path>` run a program or write anywhere.
- **Never conclude a permission rule does nothing from one tool's refusal.**
  An allow rule, a deny rule and the read block are different mechanisms;
  find which one refused before changing any of them.

## The kit
- **Never edit a kit-owned file in a project.** `.claude/kit/kit.lock` lists
  them, and `tests/kit/test_kit_lock.py` turns the suite red when one changes.
  Make the change in helen-contains-claude-webdev as a PR there, then sync
  with `/kit-sync`. A project-only need goes in a project-owned file instead.
- **`.claude/settings.json` and `.devcontainer/devcontainer.json` are
  generated.** Edit `.claude/settings.project.json` or
  `.devcontainer/kit.env`, then run `python3 tools/kit/build.py`.
- **A path in `.claude/kit/watched` is the project's own** (`<path> [<kit
  source>]` per line): the sync never overwrites or deletes it, the builder
  never generates it, and the sync report names it when its kit source
  changes. Compare those by hand; the kit never applies them.
- **A project allow rule never undoes a kit deny.** The builder refuses one.

## Critical restrictions
- NEVER run `rm -rf` outside `tmp/` without asking me first.
- **NEVER change file permissions without asking me first, every time.** No
  `chmod`, `chown` or `sudo`. A yes to one is not a yes to the next.
  `.claude/settings.json` denies all three.
- NEVER read or create `.env` files or `.claude/settings.local.json`.
- NEVER alter shell dotfiles or system configuration.

## Git workflow
- A new worktree starts from the current HEAD (`worktree.baseRef` in
  `.claude/settings.json`), not `origin/main`. If one lacks work you expect,
  `git merge --ff-only <branch>`.
- **Never commit or merge on `main`**, in any repo in the tree.
  `guard-main-branch.py` enforces it. Starting new work on `main`? Branch first.
- **Check `git branch --show-current` in its own tool call immediately before
  every commit.** Run it in the same command and it prints after the commit has
  already happened.
- Commit freely. Write the message to a file: `git commit -F tmp/msg.txt`.
- A commit subject starts with a prefix: `(feature)`, `(fix)`, `(styling)`,
  `(design)`, `(data)`, `(docs)`, `(refactor)`, `(test)`, `(devops)` (the
  container, CI, hooks and wrappers) or `(chore)`.
- **Never `git reset --hard`, `git checkout --`, `git restore` or `git clean -f`
  over a dirty tree without asking me.** `guard-destructive-git.py` enforces it.
  To set work aside, use `git stash push -u -m <tag>`.
- **Never remove, prune or tidy an agent's worktree** under
  `.claude/worktrees/`, even once its branch is merged: its `tmp/` is the
  record of how the work was checked. `git worktree remove` and `prune` are
  mine. Deleting a merged branch is fine.
- **From a worktree, see my uncommitted edits in the main checkout** with
  `sh scripts/git-diff-main-checkout.sh` (`--stat`, or `--patch
  tmp/<name>.patch` for `git apply`).
- **Git inside a nested clone** (a folder in `NESTED_DIRS` in the GitHub
  config) is `sh scripts/git-nested.sh <dir> <verb>`: `status`, `diff`, `log`,
  `show`, `branch --show-current`, `checkout -b`, `add --`, `commit -F tmp/...`.
  The branch check before a commit is still its own call.
- **Update main without checking it out:** `sh scripts/git-fetch-main.sh`, then
  `git merge origin/main`.
- **The workflow:** push the branch with
  `sh scripts/git-push-agent.sh <branch>:<branch>`, then open the PR with
  `sh scripts/gh-write.sh pr-create <repo> <branch> "<title>" tmp/body.md`.
  **I review and merge. Claude never merges, approves or closes a PR as
  merged.** After I merge: fetch, delete the branch locally and remotely
  (`sh scripts/git-push-agent.sh :<branch>`), and branch afresh.
- **After a merge, check `main`:** `sh scripts/main-ci-status.sh [<repo>]`. A
  red `main` is the first thing to report, before the work you came for: where
  the suite gates a deploy, nothing merged after it ships.
- **One PR per piece of work**: a feature, a fix, a data model change, or an
  obvious group of work. Not one per sitting, and not one per commit.
- **Every PR's base is `main`.** Never stack PRs. Before pushing to a branch,
  read the PR's state:
  `sh scripts/gh-read.sh repos/<owner>/<repo>/pulls/<N> --fields state,merged`.
- Put `Fixes #N` in the commit, AND one closing line per issue in the PR
  description. A PR the bot account opens does not close issues from commit
  messages alone. Name the issues you are about to close before pushing. A
  bare `#N` resolves only in its own repo: elsewhere write `<owner>/<repo>#N`.

## GitHub
- The agent account's token is `AGENT_GH_TOKEN`. It reaches only the
  repositories in `scripts/github.local.conf` (`scripts/github.conf` is the
  placeholder template). **Use the wrappers in `scripts/`, never
  bare `gh` or `git push`.** **Never edit `scripts/github.local.conf`, by any
  tool**: it decides what every wrapper may reach. Settings deny the Edit and
  Write tools on it; for Bash, this line is the guard.
- **Never print, echo, log or commit the token, and never put its name in an
  `echo` or `printf`.** `guard-token-expansion.py` enforces it. To find out
  whether it works, use it and read the 401/403.
- **Never create issues or PRs in a burst.** Many creations in an hour get the
  account flagged as spam, and GitHub then hides everything it ever wrote. A
  batch is ONE issue with a checklist. `guard-github-burst.py` enforces it.
  **When I say I cannot see something the API says exists, believe me** and
  check it logged out: `sh scripts/github-public-status.sh <url>`. A 404
  there beside a 200 from the API is the flag. Only I can appeal it.
- Never change repository settings, secrets, Actions settings or collaborators.
  A Pages workflow publishes nothing until I set Settings → Pages → Source to
  GitHub Actions: when you add one, say so in the PR description.

## Writing
- **A code comment states a constraint the code cannot show**, in the present
  tense. No dates, no history, no "used to". The story goes in the commit
  message.
- **When code changes, rewrite its comment.** Never append a paragraph beneath
  the old one. Delete the comment when its code goes. Before a comment names a
  file, test or function, check it exists; never write a count a command can
  print.
- Name files, never line numbers, in documents and comments.

## Working with me
- Ask me decisions as you hit them, and bring the fact that forces the
  decision.
- Do not trust a document over the code. If they disagree, the code wins and
  the document gets fixed.
- My hours are mine. Never suggest stopping.
- When you finish, say what changed and where, the local URL serving it, what
  you verified and how, which issues are touched, which PRs are waiting on me,
  and what is undone and why.
