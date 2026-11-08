---
name: relative-paths-no-cd
description: "In Bash commands, use paths relative to the working directory; never prefix with `cd` or write absolute /workspace/... paths"
metadata:
  type: feedback
---

Write Bash commands with paths relative to the current working directory (e.g. `cat scripts/gh-read.sh`), not `cd /workspace/... && ...` and not absolute `/workspace/...` paths.

**Why:** The shell already starts in the project, or in its worktree. A `cd` in a compound command, or an absolute path, makes the permission checker stop and ask the user.

**How to apply:** Every Bash call. In a worktree session the cwd is the worktree root, so relative paths resolve there. Reach outside it only when there's a real need, and say why when you do. See also [[static-commands-in-scripts]].
