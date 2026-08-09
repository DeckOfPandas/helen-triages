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
- NEVER read, write or execute above the folder you're in.

## Build Commands
- Dev Server: `jekyll-local`, deploying to localhost:4001
- Prod Server: `jekyll-prod`, deploying to localhost:4002

## Git workflow
- If we're starting new work, and we're currently on main, please check out a new branch.
- Before creating a new branch, checkout out the main branch, then `git pull origin main`.
- Commit freely without asking.
- Never `git push` without my explicit confirmation first.
- If a commit resolves a GitHub Issue, add a `Fixes #N` (or `Closes #N`) trailer to the commit message for every issue it resolves. GitHub auto-closes the issue once that commit reaches `main`. Never attempt to gain GitHub write access (`gh auth login` or similar) to close issues directly -- read-only access only, always. When summarising work, list the issue numbers involved so I can close anything the trailer mechanism didn't reach by hand.

## Normal workflow
- If you need a scratch temporary folder, create one in this project folder and add it to .gitignore
- Don't delete handover or jobs list documents.
- You don't need to ask permission to cd into folders at or below /home/helen/projects/helen-triages/food.
- You don't need to ask permission to read or write to tmp in /home/helen/projects/helen-triages/food.