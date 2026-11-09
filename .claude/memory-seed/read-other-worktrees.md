---
name: read-other-worktrees
description: Reading other agents' worktrees under .claude/worktrees/ is allowed; just read them, don't ask or hedge
metadata:
  type: feedback
---

Reading any other agent's worktree under `/workspace/.claude/worktrees/` is allowed. Read it directly: never ask permission, never call it a workaround, never apologise for it. Writing to another worktree is not covered.

**Why:** `.claude/settings.json` lists the folder in `additionalDirectories` and the rules say so, yet the user has had to repeat it.

**How to apply:** a refused read elsewhere under `/workspace/` (the main checkout's gitignored `scripts/github.local.conf`, say) is a different path, not this permission failing: name the path that was refused. See also [[relative-paths-no-cd]].
