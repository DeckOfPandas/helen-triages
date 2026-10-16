"""What "If you liked this, how about …" would offer, and how thin it gets.

    python3 scripts/related_drinks.py            # the distribution, and the tail
    python3 scripts/related_drinks.py negroni    # one drink's picks, with why

The related drinks at the foot of a drink page are chosen in Liquid by
`_layouts/cocktail.html` (MANUAL §9.13): ranked by more shared moods, then
more shared ingredient generics, then title. The page shows the top three,
then the candidate a quarter of the way down the ranking (#1183). This is
that rule in Python over `_cocktail_recipes/`, read directly, so it needs no
build. It writes nothing.

The template offers only a drink sharing something, so a drink unlike
everything else would render a short row on its own page and nowhere else.
`test_every_published_drink_page_offers_four_other_published_drinks` turns
that red; this shows which drink and why. Re-run it after a promotion batch,
and after a vocabulary edit that moves moods.

A drink counts as published on the gate's three flags: `awaiting_fix: false`,
`proofread: true` and `rewritten: true`.
"""
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRINKS = os.path.join(ROOT, "_cocktail_recipes")

HOW_MANY = 4        # the template's `limit: 4`; the cards sit two across
RENEGADE_PERCENT = 25 # the fourth card's depth into the ranking, the
                        # template's `times: 25`


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
    """Drinks with `awaiting_fix: false`, `proofread: true` and `rewritten:
    true`, explicitly.

    `_plugins/publish_gate.rb` fails closed on a missing flag, the hyphenated
    spelling or a quoted string, so this tests identity, not truthiness.
    """
    out = []
    for name in sorted(os.listdir(DRINKS)):
        if not name.endswith(".md"):
            continue
        doc = front_matter(os.path.join(DRINKS, name))
        if not doc:
            continue
        meta = doc.get("meta") or {}
        if (meta.get("awaiting_fix") is False and meta.get("proofread") is True
                and meta.get("rewritten") is True):
            out.append((name[:-3], doc))
    return out


def scored_against(slug, doc, corpus):
    """Every other published drink, best first -- the template's ranking.

    The Liquid sorts `mood~generics~title~url` as TEXT, each count written as
    `99 - n`; the title sorts with its `~` so a title that is the start of
    another sorts after it, as there. Each row is a dict."""
    moods = set(doc.get("mood") or [])
    mine = generics(doc)
    rows = []
    for other_slug, other in corpus:
        if other_slug == slug:
            continue
        shared_moods = len(moods & set(other.get("mood") or []))
        shared_gens = sum(1 for g in generics(other) if g in mine)
        if shared_moods or shared_gens:
            rows.append({"slug": other_slug, "title": other.get("title", ""),
                         "moods": shared_moods, "generics": shared_gens})
    rows.sort(key=lambda r: (-r["moods"], -r["generics"],
                             r["title"].lower() + "~"))
    return rows


def picks(slug, doc, corpus):
    """The rows the page shows, in its order: the top three, then the one
    RENEGADE_PERCENT of the way down, never above the fourth."""
    rows = scored_against(slug, doc, corpus)
    at = max(HOW_MANY - 1, len(rows) * RENEGADE_PERCENT // 100)
    return rows[:HOW_MANY - 1] + rows[at:at + 1]


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
            print("\n  what the page shows:")
            for row in picks(slug, doc, corpus):
                print(f"    {row['title']:38s} "
                      f"moods={row['moods']} generics={row['generics']}")
            print("\n  the ranking it draws from, the first eight:")
            for row in scored_against(slug, doc, corpus)[:8]:
                print(f"    {row['title']:38s} "
                      f"moods={row['moods']} generics={row['generics']}")
            return 0
        print(f"no published drink called {wanted!r}")
        return 1

    # What the row shares is told by its weakest card, which is usually the
    # fourth: the renegade is there to share less.
    thin = []
    short = False
    for slug, doc in corpus:
        shown = picks(slug, doc, corpus)
        if len(shown) < HOW_MANY:
            short = True
            thin.append((-1, slug, f"ONLY {len(shown)} CANDIDATES -- the row "
                                   f"would render {len(shown)} items"))
            continue
        weakest = min(r["moods"] + r["generics"] for r in shown)
        thin.append((weakest, slug, ", ".join(
            f"{r['slug']} ({r['moods']}+{r['generics']})" for r in shown)))
    thin.sort()

    print("\nthe weakest card's shared moods plus generics, distribution:")
    counts = {}
    for score, _, _ in thin:
        counts[score] = counts.get(score, 0) + 1
    for score in sorted(counts):
        print(f"  {score}: {counts[score]} drink(s)")

    print("\nthe ten drinks whose row shares least (moods+generics):")
    for score, slug, detail in thin[:10]:
        print(f"  {slug:42s} {detail}")

    if short:
        print("\nA DRINK CANNOT FILL ITS ROW. The page will render fewer than "
              f"{HOW_MANY} items and the rendered-pages test will go red.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
