"""What "If you liked this, how about …" would offer on a RECIPE page, and how
thin it gets. Food's twin of scripts/related_drinks.py.

    python3 scripts/related_recipes.py                     # the distribution, and the tail
    python3 scripts/related_recipes.py roast-beef-fillet   # one recipe's picks, with why

The related recipes at the foot of a recipe page are chosen in Liquid by
`_layouts/recipe.html` (#1005, DECISIONS §13). This is that choice in Python
over `_food_recipes/`, read directly, so it needs no build; it also reads
`_data/food/taxonomy.yml` and `_data/food/pantry.yml`, and writes nothing.

  score     shared tags + shared main_ingredients, with no per-field weight.
  priority  a candidate sharing this recipe's star ingredient and at least one
            mood tag outranks every candidate that does not.
  ties      more shared non-pantry main ingredients first, then more shared
            pantry staples, then A-Z.

The template offers only a candidate that scores above zero or is prioritised,
so a recipe unlike everything else would render a short row on its own page.
`test_every_published_recipe_page_offers_three_other_published_recipes` turns
that red; this shows which recipe and why. Re-run it after a promotion batch
or a taxonomy edit that moves tags. A recipe counts as published on
`awaiting_fix: false` and `proofread: true`.
"""
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECIPES = os.path.join(ROOT, "_food_recipes")
TAXONOMY = os.path.join(ROOT, "_data", "food", "taxonomy.yml")
PANTRY = os.path.join(ROOT, "_data", "food", "pantry.yml")

HOW_MANY = 3        # the template's `limit: 3`


def front_matter(path):
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    return yaml.safe_load(text[3:end])


def mood_tags():
    with open(TAXONOMY, encoding="utf-8") as handle:
        return set(yaml.safe_load(handle)["tags"]["mood"])


def pantry():
    """The larder staples, lowercased -- a bare list in pantry.yml, matched
    exactly, as food/index.html matches it."""
    with open(PANTRY, encoding="utf-8") as handle:
        return {str(p).strip().lower() for p in yaml.safe_load(handle)}


def published():
    """The gate, applied here rather than assumed: both flags, explicitly."""
    out = []
    for name in sorted(os.listdir(RECIPES)):
        if not name.endswith(".md"):
            continue
        doc = front_matter(os.path.join(RECIPES, name))
        if not doc:
            continue
        meta = doc.get("meta") or {}
        if meta.get("awaiting_fix") is False and meta.get("proofread") is True:
            out.append((name[:-3], doc))
    return out


def lowered(values):
    return {str(v).strip().lower() for v in (values or [])}


def scored_against(slug, doc, corpus, moods, larder=None):
    """Every other published recipe, best first -- the template's order.

    The Liquid sorts `prio~rank~real~larder~title~url` as TEXT -- `prio` 0
    for a prioritised candidate and 1 otherwise, `rank = 999 - score`,
    `real = 99 - shared non-larder ingredients`, `larder = 99 - shared larder
    staples` -- so ascending text order is prioritised first, highest score
    first within each, most real ingredients within a score, most larder
    staples within that, A-Z last. This reproduces that."""
    larder = pantry() if larder is None else larder
    tags = lowered(doc.get("tags"))
    mine = lowered(doc.get("main_ingredients"))
    star = (doc.get("star_ingredient") or "").strip().lower()
    rows = []
    for other_slug, other in corpus:
        if other_slug == slug:
            continue
        other_tags = lowered(other.get("tags"))
        shared_tags = tags & other_tags
        shared_ings = mine & lowered(other.get("main_ingredients"))
        real = {i for i in shared_ings if i not in larder}
        score = len(shared_tags) + len(shared_ings)
        other_star = (other.get("star_ingredient") or "").strip().lower()
        prio = bool(star) and other_star == star and bool(shared_tags & moods)
        if score > 0 or prio:
            rows.append((0 if prio else 1, score, other.get("title", ""),
                         other_slug, len(shared_tags), len(shared_ings), prio,
                         len(real), len(shared_ings) - len(real)))
    rows.sort(key=lambda r: (r[0], -r[1], -r[7], -r[8], r[2].lower()))
    return rows


def main():
    corpus = published()
    moods = mood_tags()
    print(f"{len(corpus)} published recipes in {os.path.relpath(RECIPES, ROOT)}")
    if not corpus:
        print("nothing published -- is this a fresh worktree?")
        return 1

    if len(sys.argv) > 1:
        wanted = sys.argv[1]
        for slug, doc in corpus:
            if slug != wanted:
                continue
            print(f"\n{doc.get('title')}")
            print("  star:  ", doc.get("star_ingredient") or "(none)")
            print("  tags:  ", ", ".join(sorted(lowered(doc.get("tags")))))
            print("  mains: ", ", ".join(sorted(lowered(doc.get("main_ingredients")))))
            print("\n  offered (the first three are what the page shows):")
            for row in scored_against(slug, doc, corpus, moods)[:8]:
                flag = "  star+mood" if row[6] else ""
                print(f"    {row[2]:44s} score={row[1]}  "
                      f"tags={row[4]} mains={row[5]} (real {row[7]}, "
                      f"larder {row[8]}){flag}")
            return 0
        print(f"no published recipe called {wanted!r}")
        return 1

    thin = []
    for slug, doc in corpus:
        rows = scored_against(slug, doc, corpus, moods)
        if len(rows) < HOW_MANY:
            thin.append((0, slug, f"ONLY {len(rows)} CANDIDATES -- the row "
                                  f"would render {len(rows)} items"))
            continue
        thin.append((rows[HOW_MANY - 1][1], slug,
                     ", ".join(f"{r[3]} ({r[1]})" for r in rows[:HOW_MANY])))
    thin.sort()

    print(f"\nthe {HOW_MANY}rd pick's score, distribution:")
    counts = {}
    for score, _, _ in thin:
        counts[score] = counts.get(score, 0) + 1
    for score in sorted(counts):
        print(f"  {score}: {counts[score]} recipe(s)")

    print("\nthe ten recipes sharing the least with their third pick:")
    for score, slug, detail in thin[:10]:
        print(f"  {slug:46s} {detail}")

    if thin and thin[0][0] == 0:
        print("\nA RECIPE CANNOT FILL ITS ROW. The page will render fewer than "
              f"{HOW_MANY} items and the rendered-pages test will go red.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
