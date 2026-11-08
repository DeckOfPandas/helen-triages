# Hooks

Each hook is one Python file with no imports beyond the standard library. Each is
run as `python3 <path>`, so none needs an execute bit. All are wired in
`.claude/kit/settings.kit.json`, from which `tools/kit/build.py` writes
`.claude/settings.json`.

| Hook | Event | Does |
|---|---|---|
| `session-ground-truth.py` | SessionStart | Reports the checkout, container or host, branch, dirty tree, position against `origin/main`, and how far `.claude/kit/kit.lock` is behind the kit clone in `tmp/kit` (fetching that clone in the background for the next session) |
| `guard-main-branch.py` | PreToolUse Bash | Refuses `git commit` / `git merge` on `main` or `master` |
| `guard-destructive-git.py` | PreToolUse Bash | Refuses `reset --hard`, `checkout --`, `clean -f`, `restore` on a dirty tree; `stash drop/clear` while stashes exist |
| `guard-token-expansion.py` | PreToolUse Bash | Refuses commands that would print a secret, embed one in a URL, or dump the environment |
| `guard-github-burst.py` | PreToolUse Bash | Refuses an issue or PR creation within 5 minutes of the last, or over 20 issues or 5 PRs in 24 hours, counted in the Claude config volume across sessions and worktrees; refuses any creation inside a script, since a script can loop |
| `guard-git-output.py` | PreToolUse Bash | Refuses `--output`, `--no-index`, `--ext-diff` and `--textconv` (and prefixes of them) after `git diff`/`log`/`show`, which the allow list lets run unasked as reads |
| `guard-dev-null.py` | PreToolUse Bash | Refuses `/dev/null` as a command argument (`ls /dev/null`, `curl -o /dev/null`), which `blockReadsOutsideWorkingDirectories` turns into a prompt; a redirection to it passes |
| `guard-unanalyzable-bash.py` | PreToolUse Bash | Refuses what the permission checker cannot read statically: heredocs, `$(...)` and backticks, pipes, `&&`/`\|\|`/`;` chains, a lone `&`, globs, a leading `cd`, `git -C`, a leading `NAME=value`, unquoted parentheses, `$[`, an unquoted word starting with `=`, and a quoted `[`/`]`/`\|` in a `sh scripts/...` call |
| `guard-inline-script.py` | PreToolUse Bash | Refuses `python3 -c`, `node -e`, `ruby -e`, `perl -e`, at any length |
| `guard-sed.py` | PreToolUse Bash | Refuses any `sed` |
| `guard-awk.py` | PreToolUse Bash | Refuses any `awk` / `gawk` / `mawk` / `nawk` |

The last five push Claude towards commands the permission checker can analyse,
so it prompts you less: each refusal says what to do instead, which is
usually a script in `tmp/` with its arguments written out literally. A
command that has to reach outside the working directory becomes a committed
script in `scripts/` with a fixed action, validated arguments and an allow
rule; `scripts/git-diff-main-checkout.sh` is the model.

`tests/kit/test_hooks.py` and `tests/kit/test_text_tool_guards.py` cover what
each refuses and lets through, and that each is wired in.

One more hook lives in the image, not here: `.devcontainer/session-place.py`,
wired in `/etc/claude-code/managed-settings.json`. A project's hooks don't run
in a session started inside a nested clone, so it warns there, in every
session in the container, and nothing inside can switch it off.
`tests/kit/test_session_place.py` covers it.
