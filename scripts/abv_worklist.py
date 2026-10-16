#!/usr/bin/env python3
"""Which strengths in abv.yml are still guesses, and which LIVE drinks read them.

    python3 scripts/abv_worklist.py              # the worklist, as markdown
    python3 scripts/abv_worklist.py --counts     # just the numbers

Prints the rows of `_data/cocktails/abv.yml` that are not settled (a `qq:`, or
`confidence: low`), each with the published drinks whose unit figure moves if
the row changes. It writes nothing.

A grep for `qq:` lists the rows but cannot say which of them reach a figure,
because that depends on how an ingredient resolves to a strength. So this
replays `_plugins/cocktail_units.rb`'s resolution, in the same order (MANUAL
§9.3.4):

  * an amount that does not parse to millilitres does not count; the
    exclusion list and the per-unit table are read from the data the plugin
    reads;
  * a `suggestion:` resolving through bottles.yml's aliases to a bottle with a
    strength wins outright;
  * otherwise each `generic:` resolves to `default_bottles[g]` where there is
    one, else to every bottle declared under that generic, else to the
    generic's own row.

It is a second implementation of the plugin's lookup: re-run it after a change
to the vocabulary, the bottle list or `default_bottles`. A drink counts as
published on the gate's three flags: `awaiting_fix: false`, `proofread:
true` and `rewritten: true`.
"""
import glob
import os
import re
import sys

import yaml

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "_data", "cocktails")
RECIPES = os.path.join(os.path.dirname(DATA), "..", "_cocktail_recipes")
FRONT = re.compile(r"\A---\n(.*?)\n---", re.S)


def load(name):
    with open(os.path.join(DATA, name)) as fh:
        return yaml.safe_load(fh)


class Resolver:
    """The plugin's strength lookup, over the data files it reads."""

    def __init__(self):
        abv = load("abv.yml")
        bottles_yml = load("bottles.yml")
        costs = load("costs.yml")
        ingredients = load("ingredients.yml")

        self.abv_bottles = abv.get("bottles") or {}
        self.abv_generics = abv.get("generics") or {}
        self.non_alcoholic = set(abv.get("non_alcoholic") or [])
        # Bitters never count (#1012). Read from the list a bitters is
        # declared in.
        self.bitters = set(ingredients.get("bitters") or [])

        self.per_ml = ingredients["measures"]["per_ml"]
        self.ignored_words = ingredients["measures"].get("ignored_words") or []
        self.excluded = set(costs.get("excluded_units") or [])
        self.top_up = costs.get("top_up_ml") or {}
        self.defaults = costs.get("default_bottles") or {}

        self.alias = {}
        self.by_generic = {}
        for name, row in (bottles_yml["bottles"] or {}).items():
            row = row or {}
            self.alias[name.lower()] = name
            for a in row.get("aliases") or []:
                self.alias[str(a).lower()] = name
            self.by_generic.setdefault(row.get("generic"), []).append(name)

    def volume_ml(self, amount):
        """Millilitres, or None when the amount does not reach the arithmetic."""
        a = str(amount).strip()
        if a in self.excluded:
            return None
        m = re.match(r"\A([\d.]+)\s+(.*)\Z", a)
        if not m:
            return None
        unit = m.group(2).strip()
        for w in self.ignored_words:
            unit = re.sub(r"\A" + re.escape(str(w)) + r"\s+", "", unit)
        if unit in self.excluded or unit not in self.per_ml:
            return None
        return float(m.group(1)) * float(self.per_ml[unit])

    def has_abv(self, bottle):
        row = self.abv_bottles.get(bottle)
        return bool(row and row.get("abv") is not None)

    def rows_for_generic(self, g):
        # Every bottle under the generic, though the plugin reads only their
        # mode (#1016): an unsettled strength on any one of them can change
        # which value is the mode, so every one reaches the figure.
        if g in self.non_alcoholic:
            return []
        names = self.defaults.get(g) or self.by_generic.get(g) or []
        used = [("bottle", n) for n in names if self.has_abv(n)]
        if used:
            return used
        return [("generic", g)] if g in self.abv_generics else []

    def rows_for_pour(self, ing):
        """Every abv.yml row this ingredient's strength is computed from."""
        amount = str(ing.get("amount", "")).strip()
        raw = ing.get("generic")
        generics = [str(x) for x in raw] if isinstance(raw, list) else \
                   ([str(raw)] if raw else [])

        if generics and all(g in self.bitters for g in generics):
            return []

        if amount == "(top)":
            if not [g for g in generics if g in self.top_up]:
                return []
        elif self.volume_ml(amount) is None:
            return []

        sug = ing.get("suggestion") or []
        if isinstance(sug, str):
            sug = [sug]
        named = [self.alias.get(str(s).lower()) for s in sug]
        named = [n for n in named if n and self.has_abv(n)]
        if named:
            return [("bottle", n) for n in named]

        out = []
        for g in generics:
            out.extend(self.rows_for_generic(g))
        return out

    def row(self, key):
        kind, name = key
        table = self.abv_bottles if kind == "bottle" else self.abv_generics
        return table.get(name) or {}


def published_drinks():
    """(title, front matter) for every drink the publish gate lets through."""
    for path in sorted(glob.glob(os.path.join(RECIPES, "*.md"))):
        with open(path) as fh:
            m = FRONT.match(fh.read())
        if not m:
            continue
        try:
            fm = yaml.safe_load(m.group(1))
        except yaml.YAMLError:
            continue
        if not isinstance(fm, dict):
            continue
        meta = fm.get("meta") or {}
        if (meta.get("awaiting_fix") is False and meta.get("proofread") is True
                and meta.get("rewritten") is True):
            yield fm.get("title") or os.path.basename(path), fm


def build():
    r = Resolver()
    live = list(published_drinks())

    users = {}
    for title, fm in live:
        for ing in fm.get("ingredients") or []:
            if isinstance(ing, dict):
                for key in r.rows_for_pour(ing):
                    users.setdefault(key, set()).add(title)

    # A bitters bottle is never on the worklist: it cannot reach a unit
    # figure (#1012).
    bottle_generic = {}
    for generic, names in r.by_generic.items():
        for n in names:
            bottle_generic[n] = generic

    unsettled = []
    for kind, table in (("bottle", r.abv_bottles), ("generic", r.abv_generics)):
        for name, row in table.items():
            row = row or {}
            generic = bottle_generic.get(name) if kind == "bottle" else name
            if generic in r.bitters:
                continue
            if row.get("qq") or row.get("confidence") == "low":
                unsettled.append((kind, name, row))
    unsettled.sort(key=lambda e: e[1].lower())
    return r, live, users, unsettled


def label(kind, name):
    return name if kind == "bottle" else f"_{name}_ (category)"


def markdown(r, live, users, unsettled):
    reached = [e for e in unsettled if users.get((e[0], e[1]))]
    dark = [e for e in unsettled if not users.get((e[0], e[1]))]

    out = [
        "#1001 put the unit count on the live site, so every strength "
        "`_data/cocktails/abv.yml` is still guessing at is now a number a "
        "stranger can read. This is the worklist.",
        "",
        "Each row shows what the build assumes today, so entering the real "
        "figure is a one-line edit — and where the assumption turns out to be "
        "right, saying so (raise `confidence`, drop the `qq:`) is just as "
        "useful.",
        "",
        "**The affected lists are not a grep.** They replay "
        "`_plugins/cocktail_units.rb`'s own resolution: a named `suggestion:` "
        "wins, otherwise the generic resolves to `default_bottles` or to every "
        "bottle declared under it, and an ingredient whose amount does not parse to "
        "millilitres does not count at all. That last rule is why bitters sold "
        "in dashes affect nothing, however unsure their strength is.",
        "",
        f"## {len(reached)} that change a number on the live site",
        "",
    ]
    if reached:
        out += ["| bottle / category | assumed | what I could not settle "
                "| published drinks affected |", "|---|---|---|---|"]
        for kind, name, row in reached:
            q = str(row.get("qq") or "a guess, with no note saying why"
                    ).replace("|", "\\|")
            who = ", ".join(sorted(users[(kind, name)]))
            out.append(f"| {label(kind, name)} | {row.get('abv')}% | {q} | {who} |")
        out.append("")
    else:
        out += ["None — every unsettled row is one no published drink reads.", ""]

    out += [f"## {len(dark)} that cannot move a published figure today", "",
            "Worth filling in only for the data's own sake. Each is either "
            "poured in dashes (which never reach the arithmetic) or named by "
            "no published drink.", ""]
    for kind, name, row in dark:
        q = row.get("qq") or "a guess, with no note saying why"
        out.append(f"- **{label(kind, name)}** — assumed {row.get('abv')}%. {q}")
    out += ["", "---", "",
            f"Counted against the {len(live)} drinks the publish gate lets "
            f"through. Regenerate with `python3 scripts/abv_worklist.py`."]
    return "\n".join(out) + "\n"


def main():
    r, live, users, unsettled = build()
    if "--counts" in sys.argv:
        reached = sum(1 for e in unsettled if users.get((e[0], e[1])))
        print(f"published drinks:        {len(live)}")
        print(f"unsettled rows:          {len(unsettled)}")
        print(f"  read by a live drink:  {reached}")
        print(f"  reachable by nothing:  {len(unsettled) - reached}")
        return
    print(markdown(r, live, users, unsettled), end="")


if __name__ == "__main__":
    main()
