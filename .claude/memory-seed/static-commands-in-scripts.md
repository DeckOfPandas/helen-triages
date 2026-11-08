---
name: static-commands-in-scripts
description: "Put complex Bash (loops, pipes, chains, several steps) in a tmp/ script with literal arguments; never expand variables or $(...) into a command; /dev/null only as a redirect; pass these rules to subagents"
metadata:
  type: feedback
---

Anything beyond one plain command goes in a script under the project's `tmp/`, written with the Write tool and run as `sh tmp/<name>.sh` (or `python3 tmp/<name>.py`). Inside it, spell every argument out literally: no `for f in ...; do cmd "$f"`, no `$(basename ...)`, no `"$var"` in a command position or as a path.

`/dev/null` only as a redirection target (`> /dev/null`, `2>/dev/null`, `< /dev/null`), which Claude Code never checks. As a command argument (`curl -o /dev/null`, `diff a /dev/null`) it is a read outside the working directory, and no setting exempts that one file: name a file under `tmp/` instead.

**Why:** A command whose arguments come from expansion cannot be statically analysed, so neither the permission checker nor the user can see what it will run, and the user gets asked. Subagents don't inherit these habits unless told.

**How to apply:** Every Bash call. When spawning a subagent that may run Bash, state these rules in its prompt: relative paths, no `cd`, no reads outside the project, complex commands as literal scripts. See also [[relative-paths-no-cd]].
