#!/usr/bin/env python3
"""Derive a food recipe's `main_ingredients` from its ingredient list.

    python3 scripts/derive_main_ingredients.py            # report, write nothing
    python3 scripts/derive_main_ingredients.py --write    # write the drafts
    python3 scripts/derive_main_ingredients.py --only <slug>
    python3 scripts/derive_main_ingredients.py --derive   # replace, not reorder
    python3 scripts/derive_main_ingredients.py --score    # score `derive`
                                                          # against the
                                                          # published lists

It reads every draft under `_food_drafts/` (a README.md aside) and, from
`_data/food/`, `ingredient_words.yml`, `aisles.yml`, `pantry.yml` and
`taxonomy.yml`. With `--write` it replaces the `main_ingredients:` line of
each draft that changes, as text. It never writes to `_food_recipes/`: the
published lists are the ones Helen has read, and `--score` reads them as the
yardstick. DECISIONS §6.

The rules:

  - A draft that has a list is REORDERED and its members are left alone; a
    draft with none gets a derived list. `--derive` replaces every list.
  - The order is Helen's four signals: the star ingredient first, then how
    much of a game over it would be not to have it (a pantry staple ranks
    lower and is never excluded), then proportion, then the aisle order as a
    tie-break.
  - A name keeps its modifiers (`fresh ginger`, `salted butter`) and its kind
    (`whole milk`, `king prawns`, `baby gem lettuce`), and loses a size
    (`large carrot` -> `carrot`), the amount, a prep clause and a
    parenthetical. `buildMasterList` in assets/js/ingredient-search.js does
    the opposite, stripping modifiers to make a match key, so that normaliser
    is not reused here.
  - Seasoning and water are never main ingredients.
  - A derived list is capped at KEEP.

The derivation is good at order and weak at membership: Helen drops background
aromatics and keeps structure, which an ingredient list does not say. That is
why reordering is the default.
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

# The cap on a derived list. Agreement with the published lists is flat between
# ten and no limit, so it is chosen on other grounds: it bounds a long recipe
# and keeps the index from growing a button per item. A list slightly too long
# is the cheaper error, since trimming is faster than remembering.
KEEP = 10

# A size is dropped; a kind that looks like one is kept (DECISIONS §6).
# `whole`, `king` and `baby` are deliberately absent: `whole milk`,
# `king prawns` and `baby corn` are kinds.
SIZE = re.compile(r"^(large|small|medium|medium-sized|big)\s+", re.I)

# Seasoning and water, not the pantry: a pantry staple only ranks lower.
# Nobody chooses a recipe by its salt.
NEVER = re.compile(
    r"^(sea |flaky |fine |table |kosher |freshly ground |ground )*"
    r"(salt|pepper|black pepper|white pepper|water|cold water|boiling water|"
    r"ice|seasoning|salt and pepper"
    r"|sea salt and freshly ground black pepper)$", re.I)


def _yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def fold(text: str) -> str:
    """Lowercase, curly apostrophe flattened, whitespace collapsed.

    The same fold `_plugins/food_shopping.rb` applies: this file reads that
    plugin's keyword table out of `aisles.yml`, so the two must agree on what
    a key is.
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

        # Longest keyword wins, which is aisles.yml's own rule (`coconut milk`
        # beats `milk`). Sorted as the plugin sorts, so the two readers of one
        # table agree on precedence.
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

    Keeps the modifiers and the kind (`fresh ginger`, `whole milk`,
    `king prawns`); `SIZE` drops a genuine size. Also dropped: the amount, the
    prep clause after a comma, a parenthetical, and a trailing `to serve` or
    `to taste`.
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
    """A rough comparable size for an amount, for the proportion signal.

    Only ever a sort key. A number with a unit is taken at face value, a bare
    count is worth 100 so that it outranks a spoonful, and anything unreadable
    is 0, which sorts it after everything that could be measured.
    """
    s = fold(amount)
    m = re.match(r"^([\d.]+)\s*(kg|g|l|ml|tbsp|tsp)?", s)
    if not m:
        return 0.0
    n = float(m.group(1))
    return {"kg": n * 1000, "g": n, "l": n * 1000, "ml": n,
            "tbsp": n * 15, "tsp": n * 5, None: n * 100}[m.group(2)]


def derive(fm: dict, t: Tables) -> list[str]:
    """The ordered `main_ingredients` for one recipe, capped at KEEP.

    The sort is Helen's four signals in her own order:

      1. the star first: an item whose name contains a `star_ingredient`
         value, or is contained in one;
      2. how much of a game over it would be: a pantry staple ranks lower,
         because you already have it. It never excludes;
      3. proportion, biggest first;
      4. the aisle order, as a tie-break, so a tie reads like a shopping list.
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

    This is the default: a draft's list is hers and reads better than
    `derive`'s, so only the order is supplied. Reordering cannot lose an
    ingredient.

    Each member is matched back to the item it came from, exactly or as a
    substring, which gives it an amount. A member that matches nothing has no
    amount to rank by, and her own order is the final tie-break.
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
