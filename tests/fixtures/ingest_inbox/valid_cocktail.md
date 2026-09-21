<!-- ingest v1 cocktail -->

```yaml
---
title: "Jungle Bird"
tagline: "QQ"
glass:
  - "double old fashioned"
garnish:
  - "pineapple wedge"
ingredients:
  - amount: "45 ml"
    generic: "QQ blackstrap rum"
    suggestion: []
  - amount: "22.5 ml"
    generic: "QQ Campari"
    suggestion: []
  - amount: "15 ml"
    generic: "QQ lime juice"
    suggestion: []
  - amount: "15 ml"
    generic: "QQ simple syrup"
    suggestion: []
  - amount: "45 ml"
    generic: "QQ pineapple juice"
    suggestion: []
method:
  - "Shake all ingredients with ice."
  - "Strain over crushed ice."
to_serve: "Straw."
mood: []
notes:
  - label: "QQ"
    text: "QQ - `generic` and `suggestion` not filled in. The source names one bottle (Campari) and otherwise gives categories, and a category is not derivable from a bottle name."
source: "QQ"
source_url: ""
meta:
  made_before: false
  ship: "who knows"
  rewritten: false
  awaiting_fix: false
  proofread: false
---
```

## What I could not know

- **No `generic` typed on any pour, per the standing rule** -- each carries `QQ` and then the source's own words, so you can see what the page said.
- **`mood: []` needs deriving** -- run `python3 scripts/derive_cocktail_moods.py --write`.
- **No source recorded** -- tell me the book and I will write the citation.
- **Jungle Bird is a well-known drink and may already be in your collection in a different form.** Compare the formula, not the name.

## Fingerprint

jungle bird | 45 ml | 22.5 ml | 15 ml | 15 ml | 45 ml
