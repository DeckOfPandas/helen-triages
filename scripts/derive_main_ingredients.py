#!/usr/bin/env python3
"""Derive a food recipe's `main_ingredients` from its ingredient list.

    python3 scripts/derive_main_ingredients.py            # report, write nothing
    python3 scripts/derive_main_ingredients.py --write    # write the drafts
    python3 scripts/derive_main_ingredients.py --score    # score against the
                                                          # published lists

HELEN'S SPEC, 2026-09-21: "Ingredients sort of in order of stars, how much of a
game over it would be not to have it, proportion, and sensible larder order."

AND HER BAR, which is the reason this ships at 0.53 rather than waiting for
0.9: "It only needs to 'possibly be better than Helen writing them all from
scratch', which is what I currently expect." So this runs over `_food_drafts/`
and NEVER over `_food_recipes/` -- the published lists are the ones she has
read, and they are also the yardstick this is scored against, which a writer
must not be allowed to overwrite.

=============================================================================
WHAT WAS MEASURED BEFORE ANY OF IT WAS WRITTEN
=============================================================================
THE INDEX'S OWN NORMALISER CANNOT BE REUSED, and finding out why is the most
useful thing in this file. `buildMasterList` in assets/js/ingredient-search.js
turns an item into a match key, and was the obvious reuse. Run over the
published recipes it produces `egg` where Helen writes `eggs`, `carrot, grated`
where she writes `carrot`, and it keeps cold water and black peppercorns.

    THE INDEX STRIPS EXACTLY WHAT THIS FIELD KEEPS.

They are opposite transformations of one string: the index wants `chopped
pistachios` to match `pistachios`, and this field wants the words you would say
in a shop. Stripping `modifiers` and applying `aliases` -- both right for the
index -- cost 10 points of agreement here, measured.

THE PANTRY IS A RED HERRING, AND THAT WAS THE SECOND SURPRISE. "How much of a
game over it would be not to have it" reads like `pantry.yml`, so excluding
pantry staples was the obvious selection rule. It scored WORSE -- 0.53 down to
0.38 -- because Helen keeps flour, butter, sugar and eggs. A cake IS its flour.
Tagging the bake and exempting it only recovered 0.02. So the pantry ranks an
ingredient LOWER; it never excludes one.

A SIZE IS NOT A KIND, AND THIS IS THE CAUTIONARY ONE, because the number was
right and my reading of it was wrong. Stripping `large|small|medium|big|baby|
whole|thick|thin|fat|jumbo|mini|king` scored WORSE (0.55 -> 0.50) and I reported
that as "she keeps size words". She does not. Of the 30 hits in her published
lists, TWENTY-EIGHT ARE `whole` -- and `whole milk`, `whole cloves`, `whole
nutmeg`, `whole duck` are kinds, as are `king prawns`, `baby gem lettuce` and
`baby corn`. The list under test conflated sizes with kinds, and the five points
were the kinds being destroyed. Helen's actual rule -- "'large carrot' should
appear in ingredients lists where that's what I've stated, but main_ingredients
should just have 'carrot'" -- costs NOTHING: 0.55 either way. **A measurement
that agrees with the code is not the same as one that agrees with the rule.**

WHAT IT SCORES, against her 89 published lists, intersection over union:

    naming as the index does it ............ 0.43
    keeping the modifiers the index strips . 0.53   <- this file
    also dropping pantry staples ........... 0.38
    dropping pantry except in a bake ....... 0.40

0.53 IS NOT A GOOD SCORE AND IS NOT CLAIMED AS ONE. For comparison, the mood
rules Helen KEPT scored 0.73-1.00 and the four she moved to `moods_by_hand`
scored 0.23-0.67 (taxonomy.yml records the table). By that standard this rule
is one she would hand-assign -- for a recipe that already has a list. For a
draft with none, the comparison is not against her list but against a blank.

WHAT IS STILL WRONG, so the next reader does not rediscover it: the residue is
SELECTION, not naming. She drops background aromatics (garlic cloves, bay leaf,
celery, black peppercorns, red wine vinegar) and keeps structure (eggs, plain
flour, salted butter, golden caster sugar). That is "is this what the dish IS",
and it is not in the ingredient list.
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import re
import statistics
import unicodedata

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "_data" / "food"
DRAFTS = ROOT / "_food_drafts"
RECIPES = ROOT / "_food_recipes"

FRONT_MATTER = re.compile(r"\A(---\s*\n)(.*?\n)(---\s*\n)", re.S)
MAIN_LINE = re.compile(r"^main_ingredients:.*$", re.M)

# HOW MANY TO KEEP, AND NO CUT-OFF EARNS ITS PLACE ON THE SCORE. Thirteen were
# measured against the published lists -- fixed caps from 4 to 10, and
# proportions of the ingredient count from a half to three quarters:
#
#     everything ranked   0.54      top 7            0.50
#     top 10              0.55      75% of items     0.50
#     top 8               0.50      60% of items     0.45
#     top 6               0.45      half the items   0.40
#
# CAPPING HURTS, because intersection over union punishes a miss as hard as an
# extra and this ranking removes true positives about as fast as false ones.
# That is worth stating plainly: the ranking is good at ORDER -- the star
# first, the pantry last -- and is NOT good at membership, which is the same
# conclusion the selection experiments reached from the other side.
#
# SO THE CAP IS CHOSEN ON OTHER GROUNDS, the score being flat between 10 and no
# limit at all. Ten bounds a 38-item recipe, sits nearer Helen's own median of
# six, and keeps the index from growing a button per lentil. A list slightly
# too long is also the cheaper error for her: trimming is faster than
# remembering what was left out.
KEEP = 10

# A SIZE IS DROPPED; A KIND THAT LOOKS LIKE ONE IS KEPT. Helen, 2026-09-21:
# "'large carrot' should appear in ingredients lists where that's what I've
# stated, but main_ingredients should just have 'carrot'."
#
# THIS CORRECTS A CONCLUSION I REPORTED AS MEASURED AND WAS NOT. An earlier test
# stripped `large|small|medium|big|baby|whole|thick|thin|fat|jumbo|mini|king`,
# scored worse (0.55 -> 0.50), and I read that as "she keeps size words". The
# number was right and the reading was wrong: of the 30 hits in her published
# lists, TWENTY-EIGHT ARE `whole` -- and `whole milk`, `whole cloves`, `whole
# nutmeg`, `whole duck` are not sizes at all. Neither are `king prawns`, `baby
# gem lettuce`, `baby corn`. They are KINDS, and stripping them destroys a real
# product distinction, which is exactly what those five points were measuring.
#
# Strip the sizes alone and her rule costs nothing: 0.55 median either way.
# Across BOTH collections exactly one main ingredient starts with a real size --
# `medium eggs` on ajitsuke-tamago -- so this rule is almost entirely about what
# a future ingest writes rather than about the data today.
SIZE = re.compile(r"^(large|small|medium|medium-sized|big)\s+", re.I)

# Seasoning and water. NOT the pantry -- see the module docstring for why that
# was tried and abandoned. Nobody chooses a recipe by its salt.
NEVER = re.compile(
    r"^(sea |flaky |fine |table |kosher |freshly ground |ground )*"
    r"(salt|pepper|black pepper|white pepper|water|cold water|boiling water|"
    r"ice|seasoning|salt and pepper"
    r"|sea salt and freshly ground black pepper)$", re.I)


def _yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def fold(text: str) -> str:
    """Lowercase, curly apostrophe flattened, whitespace collapsed.

    THE SAME FOLD `_plugins/food_shopping.rb` APPLIES, and deliberately so --
    this file reads that plugin's own keyword table out of `aisles.yml`, so the
    two must agree on what a key is. `tests/test_main_ingredients.py` pins them
    against each other on the real corpus rather than trusting the comment.
    """
    return re.sub(r"\s+", " ", str(text).replace("’", "'").strip().lower())


class Tables:
    """Everything the ordering reads, loaded once."""

    def __init__(self):
        words = _yaml(DATA / "ingredient_words.yml")
        aisles = _yaml(DATA / "aisles.yml")
        self.units = {fold(u) for u in (words.get("quantity_units") or [])}
        self.measures = sorted((words.get("measure_phrases") or []),
                               key=len, reverse=True)
        self.trailing = sorted((words.get("trailing_phrases") or []),
                               key=len, reverse=True)
        self.pantry = {fold(p) for p in (_yaml(DATA / "pantry.yml") or [])}

        # LONGEST KEYWORD WINS, which is aisles.yml's own rule and the reason
        # `coconut milk` beats `milk`. Sorted exactly as the plugin sorts, so
        # the two readers of one table cannot disagree on precedence.
        self.aisle_order = [a["key"] for a in (aisles.get("order") or [])]
        pairs = []
        for aisle, keys in (aisles.get("keywords") or {}).items():
            pairs += [(fold(k), aisle) for k in keys]
        pairs.sort(key=lambda p: (-len(p[0]), p[0]))
        self.aisle_patterns = [
            (re.compile(rf"(?<![a-z0-9]){re.escape(k)}(?![a-z0-9])"), aisle)
            for k, aisle in pairs]
        self.never_aisle = {fold(n) for n in (aisles.get("never") or [])}

        tax = _yaml(DATA / "taxonomy.yml")
        self.stars = set(tax.get("star_ingredients") or [])

    def aisle(self, name: str) -> int:
        """The aisle's rank in Helen's walk round the shop; last if unmatched."""
        key = fold(name)
        if key in self.never_aisle:
            return len(self.aisle_order)
        for pattern, aisle in self.aisle_patterns:
            if pattern.search(key):
                return self.aisle_order.index(aisle)
        return len(self.aisle_order)


def bare(text: str, t: Tables) -> str:
    """An item's text, cut back to the words you would say in a shop.

    KEEPS THE MODIFIERS, DROPS THE SIZE. `fresh ginger`, `ground almonds`,
    `salted butter`, `whole milk` and `king prawns` are how Helen writes them --
    stripping those is what the INDEX does, see the module docstring. But a
    genuine size goes: "`large carrot` should appear in ingredients lists where
    that's what I've stated, but main_ingredients should just have `carrot`."
    `SIZE` above is where the two are told apart, and why.

    What else goes: the amount, the prep clause after a comma, a parenthetical,
    and a trailing `to serve` / `to taste`.
    """
    s = str(text).strip()
    s = re.sub(r"\s*\([^()]*\)", "", s)
    for phrase in t.measures:
        s = re.sub(rf"^\s*{re.escape(phrase)}\s+", "", s, flags=re.I)
    for phrase in t.trailing:
        s = re.sub(rf"[,;]?\s*{re.escape(phrase)}\b.*$", "", s, flags=re.I)
    s = re.sub(r"\s*,\s*such as\b.*$", "", s, flags=re.I)
    s = re.sub(r"\s*,.*$", "", s)
    s = re.sub(r"^\s*[\d¼½¾⅓⅔⅛.,/–-]+\s*", "", s)
    parts = s.split()
    while parts and fold(parts[0]) in t.units:
        parts.pop(0)
    s = " ".join(parts).strip(" .,;–-")
    while SIZE.match(s):
        s = SIZE.sub("", s, count=1)
    return s


def millilitres_ish(amount: str) -> float:
    """A rough comparable size for an amount, for the PROPORTION signal.

    ROUGH ON PURPOSE AND ONLY EVER A SORT KEY. This is not the drinks' side,
    where `measures:` declares a conversion and a test checks it; a food amount
    is `2 large`, `a good pinch`, `400 g` and `1 x 400g tin` in the same
    collection. A number with `g`/`ml` is taken at face value, a bare count is
    worth 100 so it outranks a spoonful, and anything unreadable is 0 -- which
    puts it after the things that could be measured and before nothing at all.
    """
    s = fold(amount)
    m = re.match(r"^([\d.]+)\s*(kg|g|l|ml|tbsp|tsp)?", s)
    if not m:
        return 0.0
    n = float(m.group(1))
    return {"kg": n * 1000, "g": n, "l": n * 1000, "ml": n,
            "tbsp": n * 15, "tsp": n * 5, None: n * 100}[m.group(2)]


def derive(fm: dict, t: Tables) -> list[str]:
    """The ordered `main_ingredients` for one recipe.

    THE SORT IS HELEN'S FOUR SIGNALS IN HER OWN ORDER:

      1. the STAR first -- `star_ingredient` is a CATEGORY (`poultry`) and the
         list holds an INSTANCE (`chicken breast`), so this asks whether the
         item's aisle keyword is the star's rather than comparing strings;
      2. how much of a GAME OVER it would be -- a pantry staple ranks lower,
         because you already have it. It never excludes: see the docstring;
      3. PROPORTION, biggest first;
      4. the LARDER ORDER, as a tie-break, so a tie reads like a shopping list.
    """
    stars = fm.get("star_ingredient")
    stars = {stars} if isinstance(stars, str) else set(stars or [])

    rows, seen = [], set()
    for group in (fm.get("ingredient_groups") or []):
        for item in (group.get("items") or []):
            if not isinstance(item, dict) or not item.get("item"):
                continue
            name = bare(item["item"], t)
            key = fold(name)
            if not name or not key or key in seen or NEVER.match(key):
                continue
            seen.add(key)
            is_star = any(fold(s) in key or key in fold(s) for s in stars)
            rows.append((
                0 if is_star else 1,
                1 if key in t.pantry else 0,
                -millilitres_ish(item.get("amount") or ""),
                t.aisle(name),
                key,
                name,
            ))
    rows.sort()
    return [r[-1] for r in rows][:KEEP]


def reorder(fm: dict, t: Tables) -> list[str]:
    """Helen's own members, in Helen's stated order. Membership untouched.

    THIS IS THE DEFAULT, AND THE MEASUREMENT IS WHY. She cleared a rewrite of
    the drafts on the understanding that she would otherwise "write them all
    from scratch" -- and NOT ONE of the 341 drafts is empty. Every one carries a
    list, median five, and a sample reads better than the derivation does:
    `best-of-the-best-lasagne` already says lasagne sheets, pork mince, beef
    mince, pancetta, passata, red wine, mozzarella, parmesan, where `derive`
    drops the pancetta and the parmesan and adds celery and whole milk.

    SO THE MEMBERSHIP IS HERS AND THE ORDER IS THE PART THAT IS MISSING. Across
    both collections 295 of 430 lists do not follow the ingredient list's own
    order, which is to say they are in no order at all -- and an order is
    precisely what she asked for. Reordering cannot lose an ingredient, so it is
    the half of the job with no downside.

    EACH MEMBER IS MATCHED BACK TO THE ITEM IT CAME FROM, which is what gives it
    an amount and an aisle. 96% of members are a substring of some item's text
    (37% are one exactly), measured across both collections; a member that
    matches nothing keeps its position relative to the others it cannot be
    ranked against, at the end.
    """
    ranked = {}
    for group in (fm.get("ingredient_groups") or []):
        for item in (group.get("items") or []):
            if isinstance(item, dict) and item.get("item"):
                ranked[fold(item["item"])] = item

    stars = fm.get("star_ingredient")
    stars = {stars} if isinstance(stars, str) else set(stars or [])

    rows = []
    for i, name in enumerate(fm.get("main_ingredients") or []):
        key = fold(name)
        item = ranked.get(key) or next(
            (v for k, v in ranked.items() if key and key in k), None)
        amount = (item or {}).get("amount") or ""
        is_star = any(fold(s) in key or key in fold(s) for s in stars)
        rows.append((
            0 if is_star else 1,
            1 if key in t.pantry else 0,
            -millilitres_ish(amount),
            t.aisle(name),
            i,            # her own order, as the final tie-break
            name,
        ))
    rows.sort()
    return [r[-1] for r in rows]


def load(root: pathlib.Path):
    out = []
    if not root.is_dir():
        return out
    for path in sorted(root.rglob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        m = FRONT_MATTER.match(text)
        if m:
            out.append((path, text, yaml.safe_load(m.group(2)) or {}))
    return out


def as_line(names: list[str]) -> str:
    inner = ", ".join('"' + n.replace('"', '\\"') + '"' for n in names)
    return f"main_ingredients: [{inner}]"


def score(t: Tables) -> int:
    """Against the PUBLISHED lists, which this never writes to."""
    rows = load(RECIPES)
    if not rows:
        print("no published recipes to score against")
        return 2
    scores, extra, missed = [], [], []
    for path, _, fm in rows:
        hers = {fold(x) for x in (fm.get("main_ingredients") or [])}
        if not hers:
            continue
        mine = {fold(x) for x in derive(fm, t)}
        union = hers | mine
        scores.append(len(hers & mine) / len(union) if union else 1.0)
        extra += sorted(mine - hers)
        missed += sorted(hers - mine)
    print(f"scored over {len(scores)} published recipes")
    print(f"  intersection over union   median {statistics.median(scores):.2f}"
          f"   mean {statistics.mean(scores):.2f}")
    print(f"\n  most often ADDED that she leaves out:")
    for w, n in collections.Counter(extra).most_common(12):
        print(f"    {n:3}  {w}")
    print(f"\n  most often MISSED that she keeps:")
    for w, n in collections.Counter(missed).most_common(12):
        print(f"    {n:3}  {w}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write", action="store_true",
                    help="write the derived list into each draft")
    ap.add_argument("--score", action="store_true",
                    help="score against the published lists and stop")
    ap.add_argument("--derive", action="store_true",
                    help="REPLACE the list rather than reordering it. For a "
                         "recipe that has none; every draft today has one, and "
                         "hers are better than this (see `reorder`).")
    ap.add_argument("--only", help="one recipe's slug")
    args = ap.parse_args(argv)

    t = Tables()
    if args.score:
        return score(t)

    if not DRAFTS.is_dir():
        print(f"{DRAFTS.name}/ is not here -- clone it first "
              f"(CLAUDE.md, Normal workflow).")
        return 2

    rows = load(DRAFTS)
    if args.only:
        rows = [r for r in rows if r[0].stem == args.only]
        if not rows:
            print(f"no draft called {args.only!r}")
            return 2

    changed = same = 0
    for path, text, fm in rows:
        names = (derive(fm, t) if args.derive or not fm.get("main_ingredients")
                 else reorder(fm, t))
        if not names:
            continue
        if list(fm.get("main_ingredients") or []) == names:
            same += 1
            continue
        changed += 1
        if not args.write:
            print(f"\n{path.relative_to(DRAFTS)}")
            print(f"  was  {fm.get('main_ingredients')}")
            print(f"  now  {names}")
            continue
        line = as_line(names)
        if MAIN_LINE.search(text):
            text = MAIN_LINE.sub(lambda _: line, text, count=1)
        else:
            head, front, fence = FRONT_MATTER.match(text).groups()
            text = head + front + line + "\n" + fence + text[len(head + front + fence):]
        path.write_text(text, encoding="utf-8")

    print(f"\n{changed} draft(s) would change, {same} already match.")
    if not args.write and changed:
        print("Nothing was written. Re-run with --write.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
