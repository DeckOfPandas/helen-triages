"""What "If you liked this, how about …" would offer, and how thin it gets.

    python3 scripts/related_drinks.py            # the distribution, and the tail
    python3 scripts/related_drinks.py negroni    # one drink's picks, with why

The related drinks at the foot of a drink page are chosen in Liquid by
`_layouts/cocktail.html` (MANUAL §9.13): score = shared moods + shared
ingredient generics, ties broken by title, and nothing else. This is that
scoring in Python over `_cocktail_recipes/`, read directly, so it needs no
build. It writes nothing.

The template offers only a drink scoring above zero, so a drink unlike
everything else would render a short row on its own page and nowhere else.
`test_every_published_drink_page_offers_four_other_published_drinks` turns
that red; this shows which drink and why. Re-run it after a promotion batch,
and after a vocabulary edit that moves moods.

A drink counts as published here on `awaiting_fix: false` and `proofread:
true`. It does not read the gate's third cocktail flag, `rewritten`.
"""
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRINKS = os.path.join(ROOT, "_cocktail_recipes")

HOW_MANY = 4        # the template's `limit: 4` -- four since 2026-09-24, Helen:
                    # "Let's bump to four related cards for cocktails." The cards
                    # sit two across, so three always orphaned one.


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
    """Drinks with `awaiting_fix: false` and `proofread: true`, explicitly.

    `_plugins/publish_gate.rb` fails closed on a missing flag, the hyphenated
    spelling or a quoted string, so this tests identity, not truthiness. It
    does not read the gate's third cocktail flag, `rewritten`.
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
            print(f"\n  offered (the first {HOW_MANY} are what the page shows):")
            for row in scored_against(slug, doc, corpus)[:8]:
                print(f"    {row[1]:38s} score={row[0]}  "
                      f"moods={row[3]} generics={row[4]}")
            return 0
        print(f"no published drink called {wanted!r}")
        return 1

    # The number that matters is the last pick, not the first: what says
    # whether the row can be filled is how much the last one still shares.
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

    print(f"\nthe {HOW_MANY}th pick's score, distribution:")
    counts = {}
    for score, _, _ in thin:
        counts[score] = counts.get(score, 0) + 1
    for score in sorted(counts):
        print(f"  {score}: {counts[score]} drink(s)")

    print(f"\nthe ten drinks sharing the least with their {HOW_MANY}th pick:")
    for score, slug, detail in thin[:10]:
        print(f"  {slug:42s} {detail}")

    if thin and thin[0][0] == 0:
        print("\nA DRINK CANNOT FILL ITS ROW. The page will render fewer than "
              f"{HOW_MANY} items and the rendered-pages test will go red.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
