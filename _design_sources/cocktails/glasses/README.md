# Glass icon sources

Helen's raw Inkscape drawings for the cocktail glass icon set, committed here
**in their current, unmodified form** — untouched by the normalisation pass
that produces `_includes/icons/glasses/*.svg` (stripped metadata, bare
`viewBox`, `.glass-icon-line`/`.glass-icon-solid` classes, no inline styles).

This directory is a backup, not a build input: nothing in Jekyll reads it, the
leading underscore keeps it out of `_site/`, and nobody should point a template
at a file in here. When a drawing is adopted for the live site it is normalised
into `_includes/icons/glasses/` by `scripts/normalise_glass_icons.py`.

**One file per published glass, under its plain name, since 2026-09-29.** The
superseded versions (the three earlier tiki mugs, five pineapples, four
coupes and the rest) were deleted at Helen's request and live in git history:
`git log --diff-filter=D -- _design_sources/` lists them. A file's own
`sodipodi:docname` may still carry the working title it was drawn under
(`glass-tiki-9.svg`); that is Inkscape's metadata and is left as it is.

A new redraw lands here beside the old one; to publish it, delete the old file
and rename the new one to the plain name in the same commit
(MANUAL §9.15).
