# Helen Triages [Food, Cocktails]

About the site: https://deckofpandas.github.io/helen-triages/about/

This Jekyll repo serves two personal decision-support sites: **food** (what shall we cook?) and **cocktails** (what shall we drink?). A GitHub Actions workflow runs the tests, builds, then deploys to Pages.

This public repo holds both the food and cocktails sides, with private repos holding drafts for each.

---

## Initial setup:

1. Set up Claude's GitHub access
   - Create a new GitHub user for Claude so it doesn't act as me / use my SSH keys
   - Add Claude's account as a Collaborator to the three repos
   - Logged in as Claude, create a new personal access token scoped to "repo"
      - Classic token because fine-grained tokens can only target repos owned by their own account or an organisation
      - Blast radius is only the three repos the account was invited to
      - Can't push any change under .github/workflows/
      - Merging is always done by me
   - Set `AGENT_GH_TOKEN` in `.claude/settings.local.json`
      - Note that the token goes under the env key in `settings.local.json` (`run.sh` reads `['env']['AGENT_GH_TOKEN']`), and that file is gitignored
2. Check the three repos out locally
3. Run the container (running bash):
   - `.devcontainer/run.sh`
      - Builds the image from the Dockerfile if it doesn't exist yet
      - Plenty of packages are pre-installed, including Playwright and its dependencies
      - Bind-mounts the primary checkout at /workspace, even when run from inside a worktree
      - Reads `AGENT_GH_TOKEN` from `settings.local.json` and passes it in as an environment variable
      - Mounts ~/.gitconfig read-only
      - Mounts dotfiles if present, read-only, for quality of life
      - Publishes container ports 4001 and 4002 on host ports 5998 and 5999, picked as I had to state something, and I'm unlikely to try and use those for anything else
         - Jekyll isn't in the image anyway -- `bundle install` inside the container puts it in the cache volume
4. Run Claude inside the container, in worktrees
   - `claude --worktree NAME`
5. To get terminal (bash) access to the container while running:
   - `docker exec -it helen-triages-primary bash`

Extra things to remind Claude sometimes:
   - Use REST, not GraphQL
   - Space out writes (a batch of Issues got the first agent account flagged as spam)
   - Tag Issue numbers in commit messages because it's annoying when this doesn't happen (this is in Claude's instructions)

## General dev workflow:

1. Pull
   - Helpful script to update drafts repos:
      - `scripts/update-drafts-repos.sh`
2. Run the Docker container:
   - `.devcontainer/run.sh`
3. Run Claude in a worktree inside the container
4. Claude will push branches and open PRs
5. Fetch the branches (local checkout)
6. View on the host before merging on GitHub:
   - `bundle exec jekyll serve --config _config.yml,_config_local.yml --port PORT_NUMBER`

WSL leaves Zone.Identifier files behind when I copy things in from Windows. They're gitignored, but I still don't want them:
   - `find . -name '*Zone.Identifier*' -delete`


## Rebuilding the image after changes

```
docker image list
docker image rm helen-triages-devcontainer
```
Then build and run the container again:
   - `.devcontainer/run.sh`


## Recipe data pipeline

https://github.com/DeckOfPandas/helen-triages/blob/main/model_instructions/PIPELINE.md

There's a Mermaid diagram at the top, ooOoooh.

Three ways in:
1. claude.ai Project
2. An `ingest` issue on a private repo
3. I dump files in `tmp/inbox-*` 

Then an intake pass results in ONE list of questions for me. Anything the source doesn't say is `QQ`.

The private drafts repos have numbered folders showing state to help me keep track of recipes I want to try: `1-rewrite/` (food only because cocktails are usually less garbage on the way in), `2-make/`, `3-keep/`, `4-promote/`. 

Then Claude does a mechanical pass on what's in `4-promote`, then I proofread the rendered page, Claude promotes it in a PR, I merge, and the merge deploys.

If Claude edits a live file, it sets `proofread: false` and raises a `blocked-on-helen` issue because the recipe will disappear from the live site. If something big is wrong, the file goes back to `4-promote/`.


## To reduce harassment by Claude, but safely

Principles:
1. Don't constantly ask me for permission to run commands that are obviously fine.
2. Don't print secrets.
3. Don't annihilate my repos.
4. Don't publish anything I haven't proofread.

### Don't harass me

Aims:
1. Claude Code only runs commands without asking when the command matches an allow rule and its static check finds no path outside the project.
2. Anything clever (paths built at run time, variable expansions) goes in a committed script the checker can read.
   - Claude being clever at the prompt means me clicking "yes" all day after 2-min instalments of not being able to get anything else done

How I try to achieve this:

Steps 1 to 4 exist because Claude read the written rules and then broke most of them anyway.

1. Hook:
   - `guard-unanalyzable-bash.py` refuses commands that would otherwise have to ask me:
      - heredocs, `$(...)` or backticks, a leading `cd`, pipes, `&&`/`||`/`;` chains, and globs in arguments
   - Claude gets told no and writes a script instead, so I don't get a prompt -- it still allows redirection to a named file and plain `$VAR`

2. Allow-list:
   - `sh scripts/gh-read.sh`: any REST read, GET only, my three repos only
   - `gh-agent.sh` subcommands for listing, viewing, commenting on and creating issues and PRs
   - Three git wrappers: `git-push-agent.sh`, `git-fetch-agent.sh`, `git-clone-agent.sh`.
   - `git-fetch-main.sh` then `git merge origin/main`, `git branch --show-current`, `git add -- <paths>`, `git commit -F <file>`, and read-only git (`status`, `diff`, `log`, `show`, `blame`, `ls-tree`, `check-ignore`)
   - `pytest`, `node --test`, `python3 scripts/verify.py`
   - The browser harness: `install.sh`, `build.sh`, `serve.sh`, `shoot.sh`, `crop.sh`
   - `gh-write.sh` (open a PR, replace a PR body, comment) and `github-public-status.sh` (the logged-out visibility check)
   - Reading and writing to `/dev/null`, as an exact path

3. Wrappers that check their own arguments:
   - Allow rules ending in * can obviously accept arguments that run programs (`git clone --template=`, `git fetch --upload-pack=`, `node --import`)
      - Kept to a reviewed list, mostly wrappers
      - Dry-run tests prove what each wrapper refuses
   - `git-push-agent.sh` refuses a push to the public `main`, a bare refspec, other repos, and folders outside the checkout
   - `git-clone-agent.sh` and `git-fetch-agent.sh` refuse extra options such as `--template=` and `--upload-pack=`, which can run programs
   - `gh-read.sh` refuses every write flag, other repos, and any `--jq` expression that mentions `env`
   - `gh-write.sh` only makes its three writes, with the base always `main`, the body a real file under `tmp/`, and my three repos only
   - `github-public-status.sh` only accepts my GitHub pages and sends no credential

4. Tests guarding the allow list (`tests/test_agent_wrappers.py`):
   - Every wrapper is run dry to prove what it refuses and what it passes through
   - Every allow rule that accepts arbitrary extra arguments must be on a reviewed list
   - No allow rule may open `gh ... api`, because it can merge
   - No allow rule may run a `tmp/` script: I chose "keep asking me please" 
   - Every allow-listed script exists

5. Habits, written in CLAUDE.md:
   - One command per call
   - Every python, ruby, node or perl program goes in a file, however short
      - Eventually achieved by me typing "please please please write those long lines to files"
   - Commit messages and PR or issue bodies go in files (`-F`, `--body-file`)
   - Anything that builds a path at run time goes in a committed wrapper, so no prompts for Helen

6. Brackets and pipes in quotes triggered prompts even in an allow-listed call:
   - Claude Code reads arguments as possible paths, so `--jq '[.state] | @tsv'` harasses me even though `gh-read.sh` is allow-listed
   - `gh-read.sh --fields state,merged_at` (or `--each` for lists) builds the jq inside the script, and `guard-unanalyzable-bash.py` refuses a quoted `[`, `]` or `|` in any `sh scripts/...` call
   - Every Bash description has to say what the call reads or writes, because I'd stopped reading prompts in the name of a quiet life

7. Misc:
   - Never `sed` (`guard-sed.py`)
   - Never `awk` (`guard-awk.py`)
   - Scratch files live only in the project's `tmp/`, never the system `/tmp`, `~`, or job directories (written rule)
   - `blockReadsOutsideWorkingDirectories=true` blocks `Read`, `Grep` and `Glob` outside the project 

But unfortunately:




### Don't print secrets (again)

The GitHub token is visible in the container, passed in as an environment variable. So any process in the container can read it, and `docker inspect` on the host shows it -- fine for a single-user dev box.

Mitigations:
   - `gh-agent.sh` keeps the token's name out of every command, and every `gh` call goes through it
   - `git-credential-agent-token.sh` gives git the token over a pipe, never in a URL or in `.git/config`
   - `guard-token-expansion.py` refuses:
      - any `echo` or `printf` that mentions a secret, including through a pipe
         - even the harmless ones, because I shouldn't have to read a regex to know whether to reject a call -- I'm only human
      - the default-value expansions (`${TOK:-x}` and friends), which print the value when it's set
      - a token embedded in a URL (`https://user:$TOKEN@...`), in a command or inside a script it runs
      - anything shaped like a real GitHub token (`ghp_`, `github_pat_...`)
      - a `gh --jq` that reads the environment

### Don't annihilate my repos (twice and counting)

   - `guard-main-branch.py` refuses `git commit` or `git merge` while on `main`, in any repo, including through `cd` or `git -C`
   - `guard-destructive-git.py` refuses `reset --hard`, `checkout`/`restore` over changed files, and `clean -fd` when there's uncommitted work, naming what would be lost
   - Deny rules block `pr merge` and `pr review` 
      - `pr merge` is denied in three spellings (`gh`, `.gh-runtime/bin/gh`, `sh scripts/gh-agent.sh`)
      - `pr review` is denied only through `gh-agent.sh`
      - A merge through the raw API (`sh scripts/gh-agent.sh api -X PUT .../pulls/N/merge`) is not denied -- it asks me, and a test forbids any allow rule for it
   - Deny rules block `chmod`, `chown` and `sudo`
   - A deny can't be overridden by an allow.
   - Written rules:
      - never merge -- the token can merge, so this rests on the rule, the deny list, and the API prompt
      - every PR's base is `main`, never stacked
      - check `git branch --show-current` in its own call before every commit
      - work in worktrees
      - no bursts of issues or PRs, since the spam flag
      - when I say I can't see something, believe me (and check it logged out with `github-public-status.sh`)
      - never broaden access

### Don't publish anything I haven't proofread.

   - Publish gate (`_plugins/publish_gate.rb`): content goes live only with `proofread: true` and `awaiting_fix: false` -- a missing or misspelled flag blocks it
   - Tests `test_agent_edited_recipes_are_not_marked_proofread` and `test_agent_edited_drinks_are_not_marked_proofread` reads history -- if Claude's commit is the newest on a recipe or drink, the file must say `proofread: false`
   - CI runs the tests before deployment

### Dear future Helen

1. If you value sanity, don't run `git worktree prune` on the host while container sessions are open:
   - Container worktrees are recorded as `/workspace/...`, which doesn't exist on the host, so `prune` orphans them
2. `run.sh` uses --rm, so exit the container before `docker image rm helen-triages-devcontainer`, or the removal is refused
3. Claude config and bundle cache are named volumes and survive a rebuild

---

## License

Code: [MIT](LICENSE).
Recipes and writing: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — reuse freely, just credit me.

