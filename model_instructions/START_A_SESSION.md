# Starting a session — the prompt

Paste everything below the line into a new Claude Code session, then say what
the session is for. It points the session at the three documents that matter
and the habits that cost most when forgotten. Keep it short; the documents do
the explaining.

---

We're working on my website, a Jekyll mono-repo serving two personal
decision-support sites: **food** (what shall we cook) and **cocktails** (what shall we drink). You are in a git worktree; do not leave it. Before anything else, read these three
in this order:

1. **`CLAUDE.md`** at the repo root — the rules for you as an agent: git,
   pushing, the two hooks, the token, the proofread flag, `tmp/`, and the
   claude.ai Project. Every line was earned. Read all of it.
2. **`model_instructions/MANUAL.md`** — the manual: how to run it, the repo
   shape, the schemas, the vocabularies, the tests, the traps. Read the header
   and its "read this first, by what you are here to do" guide, then the
   sections for your task. It is the present tense only; a `MANUAL §n` in a
   code comment points into it.
3. **`model_instructions/DECISIONS.md`** — the journal: every ruling I have
   made, dated, with my reason and my words, grouped by the manual's section
   numbers. **Before you propose, reverse or "tidy" anything, find its section
   there.** A settled question asked again is the thing that annoys me most.
   A ruling changes when I look at the built thing and change my mind, never
   by being argued at.

Then, depending on the task, the procedure document that owns it:
`.claude/commands/ingest.md` (getting recipes and drinks in — the boundary is
*is the answer in the source, or in Helen's head?*), `ingest-inbox.md` (when
they arrived as GitHub issues), `tidy-drafts.md` (the mechanical half of a
drafts pass), `model_instructions/PUBLISHING_A_DRINK.md` (getting a drink out;
read it before touching `_cocktail_drafts/to-promote/`),
`model_instructions/LETTERING.md` (punched-tape type),
`model_instructions/CLAUDE_WEB_INGEST.md` (the claude.ai Project).
`INGEST_ONE_RECIPE.md` and `INGEST_ONE_COCKTAIL.md` are for a Claude with no
repository, not for you.

Things to know before your first tool call:

- **Do not trust a document over the code.** Verify anything you are about to
  act on; if they disagree, the code wins and the document gets fixed. Name
  files, never line numbers, in anything you write into `model_instructions/`.
- **The two drafts collections are private repos and are absent in a
  worktree.** Clone the one you need (MANUAL §9.1 has the command); never
  symlink. `git fetch` immediately before any run whose result you will act
  on. Both are their own repos with their own `main`: branch there too; push
  there without asking.
- **Every recipe edit sets `meta.proofread: false` in the same commit**, and a
  drink is gated the same way. `QQ` is my placeholder — never fix it
  or convert it, and never delete a `QQ original` line.
- **One `pytest` at a time**, never two.
- **Ask me the decisions as you hit them, inline, not in a batch at the end**,
  and bring me the fact that forces the decision, not options in the abstract.
  For anything visual, build candidates on the real page and let me look
  (MANUAL §13.11); do not argue for one.
- **Tag the issue in every commit** (`Fixes #N`, `Towards #N`); check
  `git branch --show-current` in its own tool call immediately before every
  commit. **Push and open the PR yourself when the work is done — no ask.**
  Name the issues the PR will close first. **Merging is mine**, in every repo,
  always.
- **If you learn something that is not written down — a ruling, a reversal, a
  trap — add it to `DECISIONS.md` under its section, dated, and fix the manual
  if the manual is now wrong.** If you touch `INGEST_ONE_*.md` or
  `CLAUDE_WEB_INGEST.md` §2, tell me the Project needs re-uploading.
- My hours are mine. Never suggest stopping.

When you finish, tell me: what changed and where, what you verified and how,
which issues the commits close or touch, which PRs are waiting on me to merge
(in this repo and the private ones — opening them is yours, merging is mine),
and anything you left undone and why.
