---
name: kit-sync
description: Sync this project's kit-owned files (hooks, wrappers, rules, devcontainer) from helen-contains-claude-webdev and open one PR. Use when the user says "sync the kit", "/kit-sync", or the session-start line says the kit is behind.
---

# Sync the kit

Brings this project up to the kit's `main` in one PR. `tools/kit/sync.py`
does the work; this is the order around it. Follow the kit's rules
throughout: one plain command per Bash call, branch check in its own call.

1. **Refuse to start in the kit itself:** `python3 tools/kit/sync.py --status`.
   "this repo is the kit" means stop and say so.
2. **Start from an up-to-date `main`,** on a clean tree:
   `git status --porcelain` must print nothing (if it doesn't, stop and ask),
   then `sh scripts/git-fetch-main.sh`.
3. **Fresh kit clone:** `rm -rf tmp/kit`, then
   `sh scripts/git-clone-agent.sh helen-contains-claude-webdev tmp/kit`.
   A refusal naming GH_REPOS means the kit repo is missing from
   `scripts/github.local.conf`: tell the user, who adds it.
4. **Dry run:** `python3 tools/kit/sync.py --dry-run`.
   - "Nothing to sync": say so and stop. No branch, no PR.
   - A refusal listing kit-owned files changed here: those changes go to the
     kit first. Show the user the list and each file's difference from the
     kit (`diff -u tmp/kit/<file> <file>`); with their go-ahead, open a PR in
     the kit with the changes, and sync after it merges.
   - "never been synced": this is a first adoption. Stop and ask the user;
     it needs `--adopt` and a file-by-file comparison with them.
5. **Branch** from `origin/main`, named after the kit commit in the report:
   `git checkout -b chore/kit-sync-<first 12 characters of the commit> origin/main`.
6. **Sync:** `python3 tools/kit/sync.py`. Its report is in
   `tmp/kit-sync-report.md`.
7. **Test:** `python3 -m pytest`. Red: stop, report it, open no PR.
8. **Commit** everything the sync changed: `git add -- .` is too broad if the
   tree had anything else, so add the paths the report lists, plus
   `.claude/kit/kit.lock` and the generated files. Message in
   `tmp/msg.txt`: `(chore) Sync the kit to <commit>`, then the report.
   `git branch --show-current` in its own call, then `git commit -F tmp/msg.txt`.
9. **Push and open the PR:** `sh scripts/git-push-agent.sh <branch>:<branch>`,
   then `sh scripts/gh-write.sh pr-create <repo> <branch> "(chore) Sync the kit to <commit>" tmp/kit-sync-report.md`.
10. **Tell the user** the PR link, and whether the report says to run
    `.devcontainer/run.sh` from the host after merging.
