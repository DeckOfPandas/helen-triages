"""What "If you liked this, how about …" would offer, and how thin it gets.

THE FEATURE (#927, 2026-09-10) is three related drinks at the foot of every
drink page, chosen in Liquid by `_layouts/cocktail.html`. The score is:

    shared moods  +  shared ingredient generics

with ties broken by title, and nothing else -- Helen: "Not a full recommendation
engine! But I expect we can do something with coincidental tagging.", and then
"Keep it simple." This script is that scoring, in Python, over the same corpus,
and it exists for one reason:

THE TEMPLATE ONLY OFFERS A DRINK SCORING ABOVE ZERO, so the row would silently
render two items, or a heading over nothing, for a drink that shares no mood and
no generic with anything in the collection. That is invisible on every page but
that drink's. When this was built the answer was comfortable -- 48 published
drinks, and every one of them had a THIRD pick still sharing 3 or more -- but
that is a fact about today's collection, not a property of the rule.

    python3 scripts/related_drinks.py            # the distribution, and the tail
    python3 scripts/related_drinks.py negroni    # one drink's picks, with why

RE-RUN IT AFTER A PROMOTION BATCH, and after any vocabulary edit that moves
moods (`scripts/derive_cocktail_moods.py` is the one that says whether they
moved). A new drink whose ingredients and moods are unlike everything else is
exactly the drink this would find, and
`test_every_published_drink_page_offers_three_other_published_drinks` is what
turns that into a red build rather than a quiet row of two.

It reads `_cocktail_recipes/` directly rather than a build, so it needs no
`jekyll build` first -- and it applies the publication gate itself
(`awaiting_fix: false` AND `proofread: true`), because the row a reader sees is
built from the published set.
"""
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRINKS = os.path.join(ROOT, "_cocktail_recipes")

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


def generics(doc):
    """Every `generic` on the drink, flattened.

    `generic` is a STRING OR A LIST (MANUAL §9.3.1; a list means "or"), and the
    Liquid loops over it either way -- Liquid treats a bare string as a
    one-item sequence. This has to flatten the same way or the two disagree.
    """
    out = []
    for ing in doc.get("ingredients") or []:
        value = ing.get("generic")
        if isinstance(value, str):
            out.append(value)
        elif isinstance(value, list):
            out.extend(value)
    return out


def published():
    """The gate, applied here rather than assumed: both flags, explicitly.

    `_plugins/publish_gate.rb` fails closed on anything other than
    `awaiting_fix: false` and `proofread: true` -- a missing flag, the old
    hyphenated spelling, a quoted string. Same test here, for the same reason.
    """
    out = []
    for name in sorted(os.listdir(DRINKS)):
        if not name.endswith(".md"):
            continue
        doc = front_matter(os.path.join(DRINKS, name))
        if not doc:
            continue
        meta = doc.get("meta") or {}
        if meta.get("awaiting_fix") is False and meta.get("proofread") is True:
            out.append((name[:-3], doc))
    return out


def scored_against(slug, doc, corpus):
    """Every other published drink, best first, ties by title -- the template's
    order. The Liquid does this by sorting `999 - score` as TEXT; the effect is
    the same and is what this reproduces."""
    moods = set(doc.get("mood") or [])
    mine = generics(doc)
    rows = []
    for other_slug, other in corpus:
        if other_slug == slug:
            continue
        shared_moods = len(moods & set(other.get("mood") or []))
        shared_gens = sum(1 for g in generics(other) if g in mine)
        score = shared_moods + shared_gens
        if score > 0:
            rows.append((score, other.get("title", ""), other_slug,
                         shared_moods, shared_gens))
    rows.sort(key=lambda r: (-r[0], r[1].lower()))
    return rows


def main():
    corpus = published()
    print(f"{len(corpus)} published drinks in {os.path.relpath(DRINKS, ROOT)}")
    if not corpus:
        print("nothing published -- is this a fresh worktree?")
        return 1

    if len(sys.argv) > 1:
        wanted = sys.argv[1]
        for slug, doc in corpus:
            if slug != wanted:
                continue
            print(f"\n{doc.get('title')}")
            print("  moods:    ", ", ".join(sorted(doc.get("mood") or [])))
            print("  generics: ", ", ".join(generics(doc)))
            print("\n  offered (the first three are what the page shows):")
            for row in scored_against(slug, doc, corpus)[:8]:
                print(f"    {row[1]:38s} score={row[0]}  "
                      f"moods={row[3]} generics={row[4]}")
            return 0
        print(f"no published drink called {wanted!r}")
        return 1

    # THE INTERESTING NUMBER IS THE THIRD PICK, not the first. A drink always
    # has something at the top of its list; what says whether the row can be
    # filled at all is how much the LAST of the three still shares.
    thin = []
    for slug, doc in corpus:
        rows = scored_against(slug, doc, corpus)
        if len(rows) < HOW_MANY:
            thin.append((0, slug, f"ONLY {len(rows)} CANDIDATES -- the row "
                                  f"would render {len(rows)} items"))
            continue
        thin.append((rows[HOW_MANY - 1][0], slug,
                     ", ".join(f"{r[2]} ({r[0]})" for r in rows[:HOW_MANY])))
    thin.sort()

    print(f"\nthe {HOW_MANY}rd pick's score, distribution:")
    counts = {}
    for score, _, _ in thin:
        counts[score] = counts.get(score, 0) + 1
    for score in sorted(counts):
        print(f"  {score}: {counts[score]} drink(s)")

    print("\nthe ten drinks sharing the least with their third pick:")
    for score, slug, detail in thin[:10]:
        print(f"  {slug:42s} {detail}")

    if thin and thin[0][0] == 0:
        print("\nA DRINK CANNOT FILL ITS ROW. The page will render fewer than "
              f"{HOW_MANY} items and the rendered-pages test will go red.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
