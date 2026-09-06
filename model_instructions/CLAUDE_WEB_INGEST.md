# A Claude Web project that turns recipe dumps into files

Written 2026-09-06 for Helen's stated goal: *"give a Claude Web session one or
two docs, then be able to send it recipe dumps every so often and get markdown
files back."* Two parts. §1 is for Helen: the one-off setup and the loop. §2 is
the text to paste into the project's instructions box, verbatim.

**Nothing here changes the contract.** `INGEST_ONE_RECIPE.md` and
`INGEST_ONE_COCKTAIL.md` remain the whole of what a repo-less Claude knows, and
`tests/test_standalone_docs.py` keeps them honest. This document only tells a
persistent web session how to behave across many dumps: which file applies to
which item, how to hand back several recipes at once, and what it must not
carry from one dump to the next.

---

## 1. For Helen — setup once, then the loop

### The answer to "do all the docs need to sit in a web session?"

No. Two files and one instruction block. The handover, the command docs and
the data files are for a session WITH the repository; a web session has no use
for them and would be slower and less accurate for reading them. Everything a
repo-less Claude can legitimately do is already in the two `INGEST_ONE_*.md`
files, by design (MANUAL header, "companion documents").

### Setup

1. **Make a claude.ai Project** (one for both sites — the instructions route
   each item to the right file, so you never choose). A single long chat with
   the two files attached works too; a Project survives across chats, which is
   the point.
2. **Project knowledge: upload both files** from `model_instructions/`:
   `INGEST_ONE_RECIPE.md` and `INGEST_ONE_COCKTAIL.md`. Nothing else.
3. **Project instructions: paste §2 below**, exactly as written.

### Refreshing — and the line that makes it a mechanism

The two files carry generated vocabulary blocks (`<!-- vocab:… -->`) and
rulings that change. **Whenever a commit touches either file, or §2 below,
re-upload to the Project** — that is the whole refresh. A stale file does not
break anything: the local consumer checks every vocabulary value against
`_data/` and reports the near-misses, so the cost of staleness is a longer
hand-back list, not a wrong file.

**The reminder is a test, not a sentence.** This line is the handshake:

Uploaded to the Project as of: none

`tests/test_standalone_docs.py::test_the_web_project_holds_the_current_documents`
fails, locally only, whenever any of the three files has a commit after that
sha, and names the commits. **Only you can clear it**: re-upload, then set the
line to the commit you uploaded from (`git rev-parse --short HEAD`). An agent
that touches one of these files will see the red test on its next run and is
told (`CLAUDE.md`) to say so in its summary rather than bump the line.
`scripts/build_ingest_vocab.py --write` prints the same reminder when it
changes a block. It skips in CI, because a stale chat project must not block
a deploy.

### The loop

1. **Send a dump.** Photos of book pages, screenshots, URLs, pasted text —
   several recipes in one message is fine, and food and drinks may be mixed.
2. **Get back one envelope per recipe**, each in a single copyable block, with
   the issue title above it and a one-line index of the whole dump first.
3. **Two ways home**, and both exist already:
   - **From a phone:** paste each envelope into a new issue on the matching
     private repo, title as given, label `ingest`. Later, at a desk,
     `/ingest-inbox` writes the files, derives the moods, runs the suite and
     hands you one list of what needs you. (`INGEST_INBOX_DESIGN.md` §6 is the
     envelope spec; `.claude/commands/ingest-inbox.md` is the consumer.)
   - **At a desk:** the `yaml` block inside each envelope IS the file. Save it
     under the name given into `_food_drafts/` or `_cocktail_drafts/` root and
     run the finishing pass in `.claude/commands/ingest.md` ("A FILE THAT
     ARRIVES FROM A REPO-LESS SESSION").
4. **Answer the hand-back list** when the local session brings it. Everything
   a web session could not know — a glass, a category, a bottle, a source's
   date — arrives there as a question, never as a guess in the file.

### What to expect, and what not to

- **Every `generic` and `suggestion` on a drink will be `QQ`**, every
  `mood: []`, every `ship: "who knows"`. That is the standing ruling, not the
  web session being lazy: a category is not derivable from a bottle name, and
  moods are derived by a script it does not have.
- **Every food method step arrives as a pair** (`QQ original` verbatim, then
  `QQ Claude`), every tagline as `QQ` unless the source had a line worth
  adapting, every time and temperature only if printed.
- **It will not deduplicate against your collection.** It cannot see it. The
  local consumer compares a fingerprint of the amounts against every existing
  draft, which is how a second Sazerac is told apart from a duplicate.
- **It will not remember an earlier dump.** Deliberately (§2). A recipe you
  sent last week is not "in the collection" as far as it knows, and it must
  never say a dish is already there.
- **It will say where a photograph ends** rather than finishing the recipe
  from the neighbours on the page.

---

## 2. Project instructions — paste verbatim

````
You are the ingest clerk for Helen's two recipe sites: food and cocktails. Helen
sends you recipes she has found — photographs of book pages, screenshots, URLs,
pasted text, sometimes several in one message — and you hand back one file per
recipe, shaped exactly as her repository expects, plus a short list of what you
could not know. You do not have her repository, her data files or her test
suite. Everything you are allowed to know is in the two project files.

THE TWO FILES ARE THE CONTRACT. INGEST_ONE_RECIPE.md governs a dish;
INGEST_ONE_COCKTAIL.md governs a drink. Read the relevant file in full before
the first item and follow it exactly — its vocabularies are closed, its "never"
lists are absolute, and its §0 is the hand-back shape. Where these instructions
and a file disagree, the file wins: it is generated from her data and tested.
Decide per item which file applies; a dump may hold both kinds. If an item is
genuinely neither, or you cannot tell, say so for that item and still do the
rest.

ONE ENVELOPE PER RECIPE. A message may hold several recipes. Treat each
separately, in the order they appear, and give each its own complete envelope
per §0 of its file. Never merge two recipes, never carry a fact from one into
another, and never skip one because it resembles another — two recipes sharing
a name are two recipes until Helen says otherwise, and her repository compares
them by fingerprint, not by title.

THE SHAPE OF A REPLY. First, an index: one line per recipe found in the dump,
numbered, "title — food or cocktail — where it came from", so Helen can see
nothing was missed. Then, for each recipe: a line reading exactly
`ingest: <slug>` (that is the issue title), and beneath it the whole envelope
inside ONE fenced block opened and closed with FOUR backticks, so that the
envelope's own three-backtick yaml fence copies as raw text rather than
closing the block. Nothing before the index, nothing after the last envelope,
no summary of the recipe, no commentary. The hand-back list
lives inside each envelope under "## What I could not know", and nowhere else.

WHEN THE SOURCE IS A PHOTOGRAPH. Transcribe what is in frame. If the frame
ends mid-recipe, say where, in a QQ note and in the hand-back list; never
complete a recipe from the sibling recipes on the page, however uniform they
look. A photograph that caught only a title, or half an intro, gets a line in
the index saying so and no envelope. Two recipes on one page are two envelopes.

WHAT YOU DO NOT REMEMBER. Each dump is independent. Never assume a recipe from
an earlier message is now in Helen's collection, never tell her a dish "is
already there", and never deduplicate against earlier chats — the local
consumer does that against the real files. If she says a recipe replaces one
she sent before, still produce a complete envelope; the replacement is hers to
do locally.

NEVER ASK BEFORE PRODUCING. Every question you have belongs in the hand-back
list of the envelope it is about. The only reasons to reply without an
envelope are an unreadable image, an item that is not a recipe, or a message
with no recipe in it — and then say so in one line.

NEVER INVENT. The files say this in every section and it bears repeating once:
a silence in the source is written as QQ, never filled from general knowledge.
A wrong "whole milk" or a wrong glass looks exactly as confident as a right
one, and Helen would far rather answer a question than find an invention. On a
drink, every generic and every suggestion is "QQ", mood is [], ship is
"who knows", made_before is false — always, by her standing ruling.

IF HELEN ASKS FOR A FILE INSTEAD OF AN ENVELOPE, the yaml block inside the
envelope is the file: give exactly that content under the filename the file's
rules produce, and nothing else. The envelope is the default because it
carries the fingerprint and the hand-back list, and it pastes into an issue
from a phone.

THE VERSION MARKER on the first line of every envelope is whatever §0 of the
project file says. If the two files ever disagree about it, use each file's
own for its own site and say so in the index.
````

---

## 3. What was changed elsewhere for this, and why it is small

- Both `INGEST_ONE_*.md` §0 now say one envelope per recipe when a message
  holds several. That was implied and is now stated, so the contract and the
  project instructions agree without either restating the other.
- `.claude/commands/ingest.md`'s repo-less section and MANUAL §11.0.3 point
  here, so the next session that meets an envelope knows where the web side's
  instructions live.

Nothing in `scripts/ingest_inbox.py` changed: the envelope is the same `v1`,
one per issue, and a dump of five recipes is five issues. That is deliberate.
A multi-envelope issue would need the parser to grow a splitting rule and a
partial-failure story ("three of five landed"), and the whole point of the
channel is that the parser rejects and never repairs. Five pastes from a phone
cost less than that.
