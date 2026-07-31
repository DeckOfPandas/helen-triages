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
- Dev Server: `jekyll-local`
