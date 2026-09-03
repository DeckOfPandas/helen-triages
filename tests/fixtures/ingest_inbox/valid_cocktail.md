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
    item: "blackstrap rum"
    generic: "QQ"
  - amount: "22.5 ml"
    item: "Campari"
    generic: "QQ"
  - amount: "15 ml"
    item: "lime juice"
    generic: "QQ"
  - amount: "15 ml"
    item: "simple syrup"
    generic: "QQ"
  - amount: "45 ml"
    item: "pineapple juice"
    generic: "QQ"
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
  ship: "QQ"
  date_last_edited: "2026-09-02"
  rewritten: false
  awaiting_fix: false
  proofread: false
---
```

## What I could not know

- **No `generic` on any pour, per the standing rule.**
- **`mood: []` needs deriving** -- run `python3 scripts/derive_cocktail_moods.py --write`.
- **No source recorded** -- tell me the book and I will write the citation.
- **Jungle Bird is a well-known drink and may already be in your collection in a different form.** Compare the formula, not the name.

## Fingerprint

jungle bird | 45 ml | 22.5 ml | 15 ml | 15 ml | 45 ml
