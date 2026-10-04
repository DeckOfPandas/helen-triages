# CI changes that need Helen's hands, staged for pasting

**Everything in this folder is inert.** Nothing here runs. GitHub only executes
workflows in `.github/workflows/`, and these are deliberately not there.

## Why they are staged rather than applied

Until 2026-10-04 the agent account's token had no `workflow` scope, so GitHub
refused any push that created or modified a file under `.github/workflows/`,
and the work an agent could do was write the exact text for Helen to paste.
She has since added the scope (DECISIONS §12, #1281), so a workflow change in
this repo now goes up as an ordinary PR. What is left here is waiting on a
decision, not on a permission.

## What is here

| file | issue | where it goes |
|---|---|---|
| `drafts-checks.yml` | #1194 (option B), #1196 (option 2) | `.github/workflows/drafts.yml` in **each private drafts repo** |

`pull-request-trigger.md` (#1195) was applied on 2026-09-28 and has been
deleted.

## Before applying it

**`drafts-checks.yml` wants a decision from Helen first**: #1194 lays out four
options and recommends B, which is what this file implements. If she would
rather do C (make a local run complete by default) or D (explicit markers),
this file is the wrong answer and should be deleted rather than applied.

## Once applied

Delete the file you used. This folder is scaffolding, not documentation — a
staged copy of a workflow that is now live is just a second copy to drift.

`.github/` starts with a dot, so Jekyll excludes it from the build and nothing
here can reach the site.
