# CI changes that need Helen's hands, staged for pasting

**Everything in this folder is inert.** Nothing here runs. GitHub only executes
workflows in `.github/workflows/`, and these are deliberately not there.

## Why they are staged rather than applied

The agent account's credential is a classic `repo`-scoped PAT. It has no
`workflow` scope, so **GitHub refuses any push that creates or modifies a file
under `.github/workflows/`**, in any of the three repos. That is not a rule this
project invented and not one to route around — CLAUDE.md's line is "if something
genuinely needs a permission not covered here, say so and stop".

So the work an agent *can* do is write the exact text, check every fact in it,
and explain what it changes. The part that needs a person is the pasting.

## What is here

| file | issue | where it goes |
|---|---|---|
| `pull-request-trigger.md` | #1195 | edits to `.github/workflows/build-and-deploy.yml` in **this** repo, plus one repository setting |
| `drafts-checks.yml` | #1194 (option B), #1196 (option 2) | `.github/workflows/drafts.yml` in **each private drafts repo** |

## The order to do them in

1. **`pull-request-trigger.md` first.** It is two small edits plus a settings
   change, and it closes the hole that caused the three-day silent deploy outage
   in September — the suite currently runs only *after* a merge, so nothing can
   stop a red merge, only report one.
2. **`drafts-checks.yml` second**, and it wants a decision from you before it is
   worth pasting: #1194 lays out four options and recommends B, which is what
   this file implements. If you would rather do C (make a local run complete by
   default) or D (explicit markers), this file is the wrong answer and should be
   deleted rather than applied.

## Once applied

Delete the file you used. This folder is scaffolding, not documentation — a
staged copy of a workflow that is now live is just a second copy to drift.

`.github/` starts with a dot, so Jekyll excludes it from the build and nothing
here can reach the site.
