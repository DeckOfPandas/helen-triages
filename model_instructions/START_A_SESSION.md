# Starting a session — the prompt

Paste everything below the line into a new Claude Code session, then say what
the session is for. `CLAUDE.md` is loaded automatically and holds the rules, so
this only points at what to read next.

---

We're working on my website, a Jekyll mono-repo serving two personal
decision-support sites: **food** (what shall we cook) and **cocktails** (what
shall we drink). You are in a git worktree; do not leave it.

1. **`model_instructions/MANUAL.md`** — how everything works today. Read its
   header and "read this first, by what you are here to do", then the sections
   for your task. A `MANUAL §n` in a code comment points into it.
2. **`model_instructions/DECISIONS.md`** — one entry per ruling I have made,
   with my reason. **Before you propose, reverse or "tidy" anything, find its
   section there**: grep `model_instructions/DECISIONS_INDEX.md` first. A
   settled question asked again is the thing that annoys me most. A ruling
   changes when I look at the built thing and change my mind, never by being
   argued at.
3. **For anything that moves a recipe through the system**,
   `model_instructions/PIPELINE.md` — the one map — and the procedure it names
   for your step: `.claude/commands/ingest.md`, `ingest-inbox.md`,
   `tidy-drafts.md`, or `model_instructions/PUBLISHING_A_COCKTAIL.md` (read it
   before touching `4-promote/`). `LETTERING.md` is the punched-tape type.
   `INGEST_ONE_RECIPE.md`, `INGEST_ONE_COCKTAIL.md` and `CLAUDE_WEB_INGEST.md`
   are for a Claude with no repository, not for you.

The two drafts collections are private repos and are absent in a fresh
worktree: clone the one you need (`CLAUDE.md` has the commands).

# TASK
If no brief is given in the command line prompt, do this:
1. Please read all the GitHub issues
2. Tell me which are stale
3. Tell me which should be split out into separate issues
4. Write a work plan for addressing groups of them, including asking me questions to unblock streams
