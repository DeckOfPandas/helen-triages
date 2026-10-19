# INGEST INBOX — the envelope an ingest issue carries, and why it is an issue

A Claude with no repository (a claude.ai chat, `CLAUDE_WEB_INGEST.md`) hands a
recipe back as an **envelope**. `scripts/ingest_inbox.py` turns an envelope
into a draft file or says why not, and `.claude/commands/ingest-inbox.md` is
the procedure for running it.

Two sections, under the numbers other files cite. §6 is the envelope's shape;
`parse_envelope` in `scripts/envelope.py` is the authority, and where this
page and the parser disagree the parser is right. §8 is the argument for the
route.

`envelope.py` imports nothing from this repository, so a web Claude fetches
it from `main` and checks its own envelopes before handing them back
(`CLAUDE_WEB_INGEST.md` §2). `ingest_inbox.py` imports it rather than keeping
a copy, so what passes there is exactly what the inbox accepts;
`tests/test_ingest_inbox.py` holds the import rule.

The principle both rest on: the browser transcribes and writes `QQ` for every
judgement; the repo side parses, never interprets. A malformed envelope is
rejected with one line saying which rule it broke. It is never repaired,
because a guess here would be an invention in the one place built to keep
inventions out.

---

## 6. The envelope — one GitHub Issue per recipe

**Where.** The private repo matching the site: `helen-triages-food-private`
or `helen-triages-cocktails-private`. Never the public repo: the body carries
source text that may be copyright.

**Who raises it.** Helen, pasting the browser's output into a new issue. The
browser session has no issue-writing access of its own, and giving it any is
her decision. The same text saved as a local file is read with
`--from-file <path>` and no issue at all; the path may be a folder.

**A batch.** One body may carry several envelopes, each under a line reading
`# ingest: <slug>`. `split_batch` cuts there first, outside any fence, drops
the text above the first heading and a horizontal rule ending a section, and
every rule below then applies to each envelope alone. A heading whose slug
disagrees with the title's is reported, and the title's is used. A body with
no such heading is one envelope.

**The issue.** Title `ingest: <slug>`, label `ingest`. The script fetches the
open issues carrying that label and does not read the title. `--issue <N>`
reads that one issue, whatever its label or state.

**The body.** In this order:

````
<!-- ingest v1 food -->

```yaml
---
title: "Crispy Sage Butter Gnocchi"
…
---
```

## What I could not know
- …

## Fingerprint
crispy sage butter gnocchi | 500 g | 60 g | 12 | 1 | 30 g
````

**What the parser enforces.** Each line is a rejection if broken.

- **The marker** is the first non-blank line: `<!-- ingest v<N> <site> -->`.
  The site is `food` or `cocktail` and must be the `--site` the script was
  run with. The version is an integer in `SUPPORTED_VERSIONS`; the script
  refuses a version it does not implement.
- **Exactly one fenced block** in the whole body, with the info string `yaml`
  or none. Every fence must be closed.
- **The block is the complete file**, exactly as it should be saved. It begins
  with `---`, its front matter is closed by a second `---`, and the front
  matter parses as YAML with a mapping at the top and a non-empty `title`.
- **Every entry in `notes`** is labelled `QQ` or `QQ <topic>`, with text
  beginning `QQ`. A note with no label is titled "note" on the page and looks
  finished, so an unread note would publish under a heading that says nothing
  is wrong; a topic after the `QQ` still reads unfinished. An envelope carries
  no note of Helen's, so the rule is demanded of every entry: a bare string,
  another label, or `QQ` text under a different label is a rejection.
  The one exception is the empty pair, `label: ""` with `text: ""`, which is
  a slot for Helen and not a note.
- **`## What I could not know`** is present. Its non-blank lines, up to the
  next `## ` heading, are the hand-back list; each is carried into the report
  with its leading `-` or `*` dropped.
- **`## Fingerprint`** is present and holds exactly one non-blank line: the
  title lowercased, then every amount in the file's own order, joined with
  ` | `. An ingredient with no amount contributes nothing. The parser rebuilds
  the line from the block and rejects an envelope whose printed line differs.
- Both headings are looked for outside the fenced block, so a `##` line inside
  the file being carried is never mistaken for one. Anything else in the body
  is ignored.

**What happens to a parsed envelope.**

- **Duplicates are found by fingerprint, never by title.** The script builds
  the same line for every draft already under the drafts folder, staging
  subfolders included. An envelope whose fingerprint matches one is reported
  as a probable duplicate and not written.
- **A matching title with a different fingerprint** is a different recipe
  under the same name (the Sazerac case). It is written, and reported for
  Helen to name.
- **The slug** is the whole title: apostrophes dropped, accents folded,
  everything outside `[a-z0-9]` turned to a hyphen. If a draft with that slug
  exists the script appends `-2` (then `-3`, and so on) and reports it.
- **The file written** is the fenced block byte for byte, never a YAML
  round-trip, as `<slug>.md` at the top level of the drafts folder, at a path
  that does not yet exist. One line may differ: an empty
  `notes:` becomes the empty `{label, text}` pair, so there is somewhere to
  type a note.

## 8. Security and failure modes

- **Why an issue and not a branch.** A branch would be written by a session
  that runs neither git guard hook (`guard-main-branch.py`,
  `guard-destructive-git.py`). An issue is only text: the private repos have
  no build, so nothing an issue carries can publish, and the session that
  writes the file is a local one, under every guard this repo has. The
  credential could push a branch, so the issue route is a choice and not a
  limit of the token. Letting a browser session write branches would be a new
  decision for Helen.
- **What a bad body can do.** Nothing beyond a rejection. The parser accepts
  one fenced block and one YAML mapping; it does not `eval`, does not follow
  URLs, writes only inside the drafts folder, and refuses a slug containing
  anything but `[a-z0-9-]`.
- **Copyright.** The issue holds source text. It is in a private repo, which
  is the protection the drafts have. Never copy an envelope into the public
  repo; a pasted copy for `--from-file` goes in `tmp/`, which is gitignored.
- **Idempotence.** The script never overwrites. Run again over an issue it
  has already written, it finds the same fingerprint among the drafts and
  reports a probable duplicate.
- **Nothing is committed, pushed or closed by the script.** Without `--write`
  it is a dry run. Its one write to GitHub is the outcome comment `--comment`
  posts on the issue. Committing and closing the issue are steps of the
  procedure in `ingest-inbox.md`.
- **The one thing that can go wrong silently** is a version bump: a document
  teaching `v2` to a browser while the script implements `v1`. The marker
  carries the version so the mismatch is loud, and
  `test_both_documents_name_a_supported_version` in
  `tests/test_ingest_inbox.py` holds each `INGEST_ONE_*.md` §0 to
  `SUPPORTED_VERSIONS`.
