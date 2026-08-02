# Claude Code Rules for Jekyll

## Environment Constraints
- OS: Ubuntu/Debian inside Windows Subsystem for Linux (WSL).
- Environment: Local Jekyll development.
- Target Directory: ONLY operate within this folder. Do not traverse to `../` or `/mnt/c/`.

## Critical Restrictions
- NEVER run `rm -rf` without explicit human confirmation.
- NEVER alter system configurations, `.bashrc`, or install global apt packages.
- NEVER access or create `.env` files containing deployment API keys.
- Do not run commands using the `--dangerously-skip-permissions` flag.

## Build Commands
- Dev Server: `jekyll-local`, deploying to localhost:4001
- Prod Server: `jekyll-prod`, deploying to localhost:4002

## Git workflow
- If we're starting new work, and we're currently on main, please check out a new branch.
- Before creating a new branch, `git pull origin main` first in case Helen has forgotten to.
- Commit freely without asking.
- Never `git push` without my explicit confirmation first.

## Normal workflow
- Please do not try to write to /tmp. If you need a scratch temporary folder, create one here and add it to .gitignore