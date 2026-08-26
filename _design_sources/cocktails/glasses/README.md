# Glass icon sources

Helen's raw Inkscape drawings for the cocktail glass icon set, committed here
**in their current, unmodified form** — untouched by the normalisation pass
that produces `_includes/icons/glasses/*.svg` (stripped metadata, bare
`viewBox`, `.glass-icon-line`/`.glass-icon-solid` classes, no inline styles).

This directory is a backup and a working archive, not a build input: nothing
in Jekyll reads it, the leading underscore keeps it out of `_site/`, and nobody
should point a template at a file in here. When a drawing here is adopted for
the live site, it gets normalised into `_includes/icons/glasses/` by hand —
that step doesn't happen automatically, and this directory is not updated to
remove or mark the file once that's done.

Several files here are superseded options, rejects, or not-yet-adopted drafts
(e.g. `glass-old-fashioned.svg` vs `-2` vs `-3`, `glass-rocks.svg` /
`glass-rocks-tall.svg` retired 2026-08-25) rather than the current state of
any single glass. `_data/cocktails/glasses.yml` is the source of truth for
which drawing is actually live.
