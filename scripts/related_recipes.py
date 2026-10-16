"""What "If you liked this, how about …" would offer on a RECIPE page, and how
thin it gets. Food's twin of scripts/related_drinks.py.

    python3 scripts/related_recipes.py                     # the distribution, and the tail
    python3 scripts/related_recipes.py roast-beef-fillet   # one recipe's picks, with why

The related recipes at the foot of a recipe page are chosen in Liquid by
`_layouts/recipe.html` (#1005, DECISIONS §13). This is that choice in Python
over `_food_recipes/`, read directly, so it needs no build; it also reads
`_data/food/taxonomy.yml` and `_data/food/pantry.yml`, and writes nothing.

  1. the same star ingredient;
  2. then more shared mood tags;
  3. then more shared other tags plus shared main_ingredients;
  4. then more shared non-pantry main ingredients, then more shared pantry
     staples, then A-Z.

The template offers only a candidate sharing something, so a recipe unlike
everything else would render a short row on its own page.
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

    The Liquid sorts `star~mood~rank~real~larder~title~url` as TEXT, each
    number written as a fixed-width `99 - n` or `999 - n`, so ascending text
    order is the ranking in the module docstring. This reproduces that. Each
    row is a dict; `picks` reads its slug."""
    larder = pantry() if larder is None else larder
    tags = lowered(doc.get("tags"))
    mine = lowered(doc.get("main_ingredients"))
    star = (doc.get("star_ingredient") or "").strip().lower()
    rows = []
    for other_slug, other in corpus:
        if other_slug == slug:
            continue
        shared_tags = tags & lowered(other.get("tags"))
        shared_moods = shared_tags & moods
        shared_ings = mine & lowered(other.get("main_ingredients"))
        real = {i for i in shared_ings if i not in larder}
        score = len(shared_tags - shared_moods) + len(shared_ings)
        other_star = (other.get("star_ingredient") or "").strip().lower()
        same_star = bool(star) and other_star == star
        if score > 0 or shared_moods or same_star:
            rows.append({
                "slug": other_slug, "title": other.get("title", ""),
                "star": same_star, "moods": len(shared_moods),
                "score": score, "real": len(real),
                "larder": len(shared_ings) - len(real),
            })
    rows.sort(key=lambda r: (not r["star"], -r["moods"], -r["score"],
                             -r["real"], -r["larder"], r["title"].lower() + "~"))
    return rows


def picks(slug, doc, corpus, moods, larder=None):
    """The slugs the page shows, in its order."""
    return [r["slug"] for r in scored_against(slug, doc, corpus, moods, larder)[:HOW_MANY]]


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
                flag = "  same star" if row["star"] else ""
                print(f"    {row['title']:44s} moods={row['moods']}  "
                      f"score={row['score']} (real {row['real']}, "
                      f"larder {row['larder']}){flag}")
            return 0
        print(f"no published recipe called {wanted!r}")
        return 1

    thin = []
    short = False
    for slug, doc in corpus:
        rows = scored_against(slug, doc, corpus, moods)
        if len(rows) < HOW_MANY:
            short = True
            thin.append((-1, slug, f"ONLY {len(rows)} CANDIDATES -- the row "
                                   f"would render {len(rows)} items"))
            continue
        last = rows[HOW_MANY - 1]
        thin.append((last["moods"] + last["score"], slug,
                     ", ".join(f"{r['slug']} ({r['moods'] + r['score']})"
                               for r in rows[:HOW_MANY])))
    thin.sort()

    print(f"\nthe {HOW_MANY}rd pick's shared moods plus score, distribution:")
    counts = {}
    for score, _, _ in thin:
        counts[score] = counts.get(score, 0) + 1
    for score in sorted(counts):
        print(f"  {score}: {counts[score]} recipe(s)")

    print("\nthe ten recipes sharing the least with their third pick:")
    for score, slug, detail in thin[:10]:
        print(f"  {slug:46s} {detail}")

    if short:
        print("\nA RECIPE CANNOT FILL ITS ROW. The page will render fewer than "
              f"{HOW_MANY} items and the rendered-pages test will go red.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
