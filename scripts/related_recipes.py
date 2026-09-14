"""What "If you liked this, how about …" would offer on a RECIPE page, and how
thin it gets. Food's twin of scripts/related_drinks.py -- #1005, 2026-09-14.

THE FEATURE is three related recipes at the foot of every recipe page, chosen
in Liquid by `_layouts/recipe.html`. The score is:

    shared tags  +  shared main_ingredients

with ties broken by title -- the drinks rule ported directly, at Helen's word
("Yes"). ONE THING ON TOP OF IT, hers as well: "prioritise (star*mood)". A
candidate that shares this recipe's STAR INGREDIENT and at least one MOOD tag
outranks every candidate that does not, whatever the counts say; among the
prioritised, and among the rest, the score then decides. Nothing else -- no
weighting, no per-field multiplier -- for the reason the drinks version gives:
every knob one could add is a claim about what makes two recipes alike, and
nobody has made that claim.

WHY THIS SCRIPT EXISTS: the template only offers a candidate scoring above
zero (or prioritised), so a recipe sharing no tag and no main ingredient with
anything would quietly render a row of two, or a heading over nothing, on its
own page and nowhere else. `test_every_published_recipe_page_offers_three_other_published_recipes`
turns that into a red build; this is where to look when it fires.

    python3 scripts/related_recipes.py                 # the distribution, and the tail
    python3 scripts/related_recipes.py roast-beef-fillet   # one recipe's picks, with why

It reads `_food_recipes/` directly, so it needs no `jekyll build` first, and
it applies the publication gate itself (`awaiting_fix: false` AND
`proofread: true`), because the row a reader sees is built from the published
set. Re-run it after a promotion batch or a taxonomy edit that moves tags.
"""
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECIPES = os.path.join(ROOT, "_food_recipes")
TAXONOMY = os.path.join(ROOT, "_data", "food", "taxonomy.yml")

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


def scored_against(slug, doc, corpus, moods):
    """Every other published recipe, best first -- the template's order.

    The Liquid sorts `prio~rank~title~url` as TEXT with `prio` 0 for a
    prioritised candidate and 1 otherwise and `rank = 999 - score`, so
    ascending text order is prioritised first, highest score first within
    each, A-Z within a score. This reproduces that."""
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
        score = len(shared_tags) + len(shared_ings)
        other_star = (other.get("star_ingredient") or "").strip().lower()
        prio = bool(star) and other_star == star and bool(shared_tags & moods)
        if score > 0 or prio:
            rows.append((0 if prio else 1, score, other.get("title", ""),
                         other_slug, len(shared_tags), len(shared_ings), prio))
    rows.sort(key=lambda r: (r[0], -r[1], r[2].lower()))
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
                      f"tags={row[4]} mains={row[5]}{flag}")
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
