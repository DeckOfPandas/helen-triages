#!/usr/bin/env python3
"""How much does a `to top` actually pour? The arithmetic, and what it is missing.

#1076. `top_up_ml` in `_data/cocktails/costs.yml` declares ONE range per topper
whatever the drink -- champagne and prosecco 75-100 ml, soda water 100-150 --
and that range prices the pour, counts its units (`cocktail_units.rb` takes the
midpoint) and gives the shopping list a volume. Helen, 2026-09-14, on Anita's
Attitude Adjuster, whose source prints `Top (30-45)` against the house 75-100:
*"Calculate ml for top, because we can totally work this out"* -- a top fills
the glass, so it is

    glass capacity  -  what the recipe has already poured  -  room for the ice

THE SECOND TERM IS THE ONLY ONE THIS REPO CAN ANSWER TODAY, and that is why
this script exists rather than a patch to `top_up_ml`. No glass records a
capacity (`glasses.yml` holds `heights_mm` for the icons and nothing about
volume -- #295 is the real version of that list, "the glasses I own with their
volumes", and it is open), and `serve.ice` says what KIND of ice, never how
much room it takes. Two of the three terms are measurements only Helen's
cupboard can make.

So this runs the sum in the direction the data allows, and prints the two
numbers it is waiting for:

  1. EVERY TOPPED DRINK, with the volume its other pours measure to.
  2. WHAT THE HOUSE RANGE IMPLIES -- build plus the top, which is the liquid
     that has to fit in the glass. Run backwards like this the arithmetic is
     already decisive for one drink: see the report.
  3. A CAPACITY FLOOR PER GLASS, derived from the collection itself -- the most
     liquid any drink already asks that glass to hold. Not a capacity, but a
     number no capacity may fall below, and it comes free.
  4. THE FORWARD CALCULATION, the moment the two missing inputs exist. It reads
     `capacity_ml:` from `glasses.yml` and `displacement:` from `serve.yml`;
     with either absent it says which, and stops rather than guessing.

A BUILD VOLUME IS A FLOOR, NOT A TOTAL, WHENEVER A POUR WILL NOT CONVERT. The
Pear, Apricot and Rosemary Bellini is the case that forces the distinction: its
`ingredients:` are a batch SYRUP (a whole pear, four apricots, 75 g sugar) and
only its method knows that a serving is `25 ml syrup`. Six of its eight pours
have no millilitre figure, so summing the two that do says 10 ml and means
nothing. The report marks such a drink incomplete and never quotes its figure
as a build -- the same honesty `cost.complete` keeps for a price known to be
wrong.

AND IT IS PER GLASS, SO IT IS DIVIDED BY `serves:`. The Modern Zombie pours
410 ml and says `serves: 2`; read undivided it claims a collins glass holds
410 ml, which is a third again what one holds. Absent means 1, exactly as
`cocktail_units.rb` reads it. **The plugin divides the TOP by `serves:` too**,
which is right for a unit count (the bowl's alcohol shared out) and wrong for
this sum (a top fills one glass, and four glasses need four tops). No topped
drink declares `serves:` today, so the two rules have never disagreed on a real
drink -- but the first punch to be topped will make them.

    python3 scripts/top_up_ml.py            # the report, as markdown
    python3 scripts/top_up_ml.py --counts   # just the numbers

Nothing here writes. The conversions and the exclusion list are read out of
`ingredients.yml` and `costs.yml`, never restated, so this cannot drift from
what the plugins price and count.
"""
import glob
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "_data", "cocktails")
RECIPES = os.path.join(ROOT, "_cocktail_recipes")
# A worktree has no drafts (MANUAL 9.1). Absent is normal, not an error.
DRAFTS = os.path.join(ROOT, "_cocktail_drafts")
FRONT = re.compile(r"\A---\n(.*?)\n---", re.S)

TOP = "to top"


def load(name):
    with open(os.path.join(DATA, name)) as fh:
        return yaml.safe_load(fh)


class Measures:
    """The amount -> millilitres lookup the plugins use, over the same data."""

    def __init__(self, ingredients, costs):
        self.per_ml = ingredients["measures"]["per_ml"]
        self.ignored_words = ingredients["measures"].get("ignored_words") or []
        self.excluded = set(costs.get("excluded_units") or [])
        self.non_volumetric = set(
            ingredients["measures"].get("non_volumetric") or [])

    def volume_ml(self, amount):
        """Millilitres, or None when the amount is not a volume."""
        a = str(amount).strip()
        if a in self.excluded or a in self.non_volumetric:
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


def generics(ing):
    raw = ing.get("generic")
    if isinstance(raw, list):
        return [str(x) for x in raw]
    return [str(raw)] if raw else []


def drinks(directory, stage):
    """(title, stage, front matter) for every drink file under `directory`."""
    if not os.path.isdir(directory):
        return
    for path in sorted(glob.glob(os.path.join(directory, "**", "*.md"),
                                 recursive=True)):
        with open(path) as fh:
            m = FRONT.match(fh.read())
        if not m:
            continue
        try:
            fm = yaml.safe_load(m.group(1))
        except yaml.YAMLError:
            continue
        if not isinstance(fm, dict) or not fm.get("ingredients"):
            continue
        yield fm.get("title") or os.path.basename(path), stage, fm


def published(fm):
    """The publish gate's own answer -- both flags, as publish_gate.rb reads."""
    meta = fm.get("meta") or {}
    return meta.get("awaiting_fix") is False and meta.get("proofread") is True


class Report:
    def __init__(self):
        glasses = load("glasses.yml")
        costs = load("costs.yml")
        serve = load("serve.yml")

        self.measures = Measures(load("ingredients.yml"), costs)
        self.top_up = costs.get("top_up_ml") or {}
        self.canonical = {k.lower(): v
                          for k, v in (glasses.get("canonical_glasses") or {}).items()}
        # THE TWO MISSING INPUTS. Read, never invented; absent is the finding.
        self.capacity = glasses.get("capacity_ml") or {}
        self.displacement = serve.get("displacement") or {}

        self.all = list(drinks(RECIPES, "live")) + list(drinks(DRAFTS, "draft"))

    def glass_names(self, fm):
        raw = fm.get("glass") or []
        if isinstance(raw, str):
            raw = [raw]
        return [self.canonical.get(str(g).lower(), str(g)) for g in raw]

    @staticmethod
    def serves(fm):
        """How many glasses the ingredient list fills. Absent means 1."""
        try:
            n = int(fm.get("serves") or 1)
        except (TypeError, ValueError):
            return 1
        return n if n >= 1 else 1

    def build(self, fm):
        """(millilitres in ONE glass, [amounts that would not convert]).

        Divided by `serves:`, because the question is how much room is left in
        the glass in front of you, not how much the batch made.
        """
        total, unmeasured = 0.0, []
        for ing in fm.get("ingredients") or []:
            if not isinstance(ing, dict):
                continue
            amount = str(ing.get("amount", "")).strip()
            if amount == TOP:
                continue
            ml = self.measures.volume_ml(amount)
            if ml is None:
                unmeasured.append((amount, ", ".join(generics(ing))))
            else:
                total += ml
        return total / self.serves(fm), unmeasured

    def toppers(self, fm):
        out = []
        for ing in fm.get("ingredients") or []:
            if isinstance(ing, dict) and str(ing.get("amount", "")).strip() == TOP:
                out.extend(generics(ing))
        return out

    def topped(self):
        """Every drink with a `to top`, with everything derivable about it."""
        rows = []
        for title, stage, fm in self.all:
            tops = self.toppers(fm)
            if not tops:
                continue
            build_ml, unmeasured = self.build(fm)
            declared = [self.top_up.get(t) for t in tops]
            rows.append({
                "title": title,
                "stage": stage,
                "live": stage == "live" and published(fm),
                "glasses": self.glass_names(fm),
                "ice": ((fm.get("serve") or {}).get("ice")
                        if isinstance(fm.get("serve"), dict) else None),
                "toppers": tops,
                "serves": self.serves(fm),
                "build_ml": build_ml,
                "unmeasured": unmeasured,
                "complete": not unmeasured,
                "declared": [d for d in declared if d],
            })
        rows.sort(key=lambda r: (r["stage"], r["title"].lower()))
        return rows

    def floors(self):
        """The most liquid the collection already asks each glass to hold.

        A LOWER BOUND ON CAPACITY AND NOTHING MORE, but a real one and derived
        rather than picked: if a drink pours 135 ml into a flute and then tops
        it with up to 100 ml of champagne, a flute has to hold 235 ml of liquid
        before any question of ice or headroom. A glass whose floor exceeds
        what such a glass holds is the signal that the house range is wrong for
        that drink -- which is the whole of #1076 stated backwards.

        Only drinks whose every pour converts are counted: an incomplete build
        is a floor of its own and would drag the glass's floor DOWN, which is
        the one direction a bound must never move.
        """
        out = {}
        for title, stage, fm in self.all:
            build_ml, unmeasured = self.build(fm)
            if unmeasured:
                continue
            top_max = 0.0
            for t in self.toppers(fm):
                row = self.top_up.get(t)
                if row:
                    top_max = max(top_max, float(row.get("ml_max") or 0))
            total = build_ml + top_max
            for g in self.glass_names(fm):
                cur = out.get(g)
                if cur is None or total > cur[0]:
                    out[g] = (total, title, build_ml, top_max,
                              self.serves(fm))
        return dict(sorted(out.items(), key=lambda kv: -kv[1][0]))

    def cancellations(self):
        """Drinks sharing a glass and an ice, where the unknowns cancel.

        THIS IS THE ONE PART OF HELEN'S SUM THAT RUNS TODAY, and it runs
        because it is a DIFFERENCE. Two drinks in the same glass with the same
        ice are filled to the same line, so

            top(A) - top(B)  =  build(B) - build(A)

        and capacity, fill level and ice -- every term nobody has measured --
        drop out of both sides. The answer is not a figure but a SHAPE: one
        unknown per glass instead of a capacity table, and the unknown is a
        question that can be answered by pouring one drink and reading the
        bottle.

        Grouped on the glass and the ice, never on what is being topped with:
        the glass does not care whether the last 80 ml is champagne or soda.
        Only complete builds take part -- an incomplete one has no difference
        to take.
        """
        groups = {}
        for row in self.topped():
            if not row["complete"] or len(row["glasses"]) != 1:
                continue
            groups.setdefault((row["glasses"][0], row["ice"]), []).append(row)
        out = []
        for key, members in sorted(groups.items()):
            members.sort(key=lambda r: -r["build_ml"])
            ref = members[0]
            out.append((key, ref, [(m, ref["build_ml"] - m["build_ml"])
                                   for m in members]))
        return out

    # --- the forward sum, for the day the inputs land ------------------------
    def forward(self, row):
        """capacity - build - ice, per glass, or the reason it cannot run."""
        # `capacity_ml` IS THE POURED VOLUME, NOT THE BRIM. Asking for the brim
        # would need a fill fraction beside it, and a fill fraction is a second
        # judgement with nothing to check it against -- where "how much does
        # this glass hold when you pour a drink into it" is one measurement
        # with a measuring jug.
        if not self.capacity:
            return None, "no `capacity_ml:` in _data/cocktails/glasses.yml (#295)"
        if not row["complete"]:
            return None, "build volume unknown -- see the unmeasured pours"
        out = []
        for g in row["glasses"]:
            cap = self.capacity.get(g)
            if cap is None:
                out.append((g, None, f"no capacity declared for `{g}`"))
                continue
            ice = row["ice"]
            if ice is None:
                out.append((g, None, "no `serve.ice` -- nobody has decided"))
                continue
            share = self.displacement.get(ice)
            if share is None:
                out.append((g, None,
                            f"no `displacement:` for ice `{ice}` in serve.yml"))
                continue
            usable = float(cap) * (1.0 - float(share))
            out.append((g, max(0.0, usable - row["build_ml"]), None))
        return out, None


def ml(x):
    return f"{x:g} ml"


def markdown(r):
    rows = r.topped()
    live = [x for x in rows if x["live"]]
    floors = r.floors()

    out = [
        "# What a `to top` pours — #1076",
        "",
        "`top_up_ml` in `_data/cocktails/costs.yml` declares one range per "
        "topper whatever the drink. Helen's calculation is "
        "**glass capacity − what is already poured − room for the ice**. "
        "This repo can measure the middle term and nothing else: no glass "
        "records a capacity (#295) and `serve.ice` says what kind of ice, "
        "never how much room it takes.",
        "",
        f"## The {len(rows)} drinks with a `to top`"
        f" ({len(live)} of them published)",
        "",
        "| drink | | glass | ice | measured build | topper | house range | "
        "build + top |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for x in rows:
        tops = ", ".join(x["toppers"])
        ranges = " / ".join(f"{d['ml_min']}–{d['ml_max']} ml"
                            for d in x["declared"]) or "—"
        if x["complete"]:
            build = ml(x["build_ml"])
            span = (f"{ml(x['build_ml'] + min(float(d['ml_min']) for d in x['declared']))}"
                    f" – {ml(x['build_ml'] + max(float(d['ml_max']) for d in x['declared']))}"
                    ) if x["declared"] else "—"
        else:
            build = f"≥ {ml(x['build_ml'])} (incomplete)"
            span = "—"
        flag = "live" if x["live"] else x["stage"]
        out.append(f"| {x['title']} | {flag} | {', '.join(x['glasses'])} | "
                   f"{x['ice'] or '—'} | {build} | {tops} | {ranges} | {span} |")

    incomplete = [x for x in rows if not x["complete"]]
    if incomplete:
        out += ["",
                "### Builds that cannot be measured",
                "",
                "Every pour has to convert to millilitres before "
                "`capacity − build` means anything. These do not, so their "
                "build figure is a floor and the report never spends it.",
                ""]
        for x in incomplete:
            out.append(f"- **{x['title']}** — "
                       + "; ".join(f"`{a}` {g}".strip() for a, g in x["unmeasured"]))

    out += ["",
            "## What a glass is already asked to hold",
            "",
            "Derived from the collection, not picked: the most liquid any "
            "drink puts in that glass, counting a `to top` at the house "
            "range's maximum. **A lower bound on capacity**, before any "
            "allowance for ice or headroom — so a glass that does not really "
            "hold this much is one whose drinks' numbers are already wrong.",
            "",
            "| glass | floor | set by | build, per glass | + top |",
            "|---|---|---|---|---|"]
    for g, (total, title, build_ml, top_max, serves) in floors.items():
        who = title + (f" (serves {serves})" if serves > 1 else "")
        out.append(f"| {g} | {ml(total)} | {who} | {ml(build_ml)} | "
                   + (ml(top_max) if top_max else "—") + " |")

    out += ["",
            "## Where the unknowns cancel",
            "",
            "Two drinks in the same glass with the same ice fill to the same "
            "line, so the difference between their tops is the difference "
            "between their builds — and capacity, fill level and ice all drop "
            "out. **This is the only part of the sum that runs today**, and it "
            "turns the missing capacity table into one question per glass: "
            "how much goes into the drink with the least room left?",
            ""]
    for (glass, ice), ref, members in r.cancellations():
        head = f"**{glass}**" + (f", ice `{ice}`" if ice else "")
        if len(members) == 1:
            only = members[0][0]
            out += [f"- {head} — only {only['title']} tops in it, so nothing "
                    f"cancels. Its top needs the capacity, or an answer of "
                    f"its own.", ""]
            continue
        out += [f"- {head} — {len(members)} topped drinks. "
                f"{ref['title']} has the least room left, so call its top "
                f"**T**:", ""]
        for m, offset in members:
            tail = "**T**" if offset == 0 else f"**T + {ml(offset)}**"
            out.append(f"    - {m['title']} ({ml(m['build_ml'])} built, "
                       f"{', '.join(m['toppers'])}) — {tail}")
        widest = max(o for _, o in members)
        declared = {f"{d['ml_min']}–{d['ml_max']} ml"
                    for m, _ in members for d in m["declared"]}
        out += ["",
                f"    `top_up_ml` gives every one of them "
                f"{' and '.join(sorted(declared))} today, so it is saying "
                f"these drinks fill to lines {ml(widest)} apart.",
                ""]

    out += ["## The forward calculation", ""]
    blocked = set()
    any_run = False
    for x in rows:
        got, why = r.forward(x)
        if got is None:
            blocked.add(why)
            continue
        for g, value, reason in got:
            any_run = True
            if value is None:
                blocked.add(reason)
            else:
                out.append(f"- **{x['title']}** ({g}) — tops with {ml(value)}.")
    if not any_run or blocked:
        out += ["Cannot run. What it is waiting for:", ""]
        for why in sorted(blocked):
            out.append(f"- {why}")
        out += ["",
                "`capacity_ml:` belongs beside `heights_mm:` in "
                "`glasses.yml`, keyed on the canonical glass name exactly as "
                "`serving:` is. **It wants the volume the glass holds WHEN "
                "POURED, not to the brim** — one number rather than a brim "
                "capacity and a fill fraction, because a fill fraction is a "
                "second judgement nobody would be able to check. "
                "`displacement:` belongs in `serve.yml` beside "
                "`in_the_glass:`, keyed on the same ice values — the fraction "
                "of that volume the ice takes, so `none` is 0."]

    drafts = "read" if os.path.isdir(DRAFTS) else (
        "**NOT read — `_cocktail_drafts/` is absent**, which is the normal "
        "state of a worktree (MANUAL §9.1). Anita's Attitude Adjuster, the "
        "drink that raised #1076, is one of them, so clone the drafts repo "
        "before taking these counts as the whole collection")
    out += ["", "---", "",
            f"{len(rows)} topped drinks, {len(live)} of them published. "
            f"Drafts {drafts}. "
            "Regenerate with `python3 scripts/top_up_ml.py`."]
    return "\n".join(out) + "\n"


def main():
    r = Report()
    rows = r.topped()
    if "--counts" in sys.argv:
        print("drafts collection:       "
              + ("read" if os.path.isdir(DRAFTS) else "ABSENT (worktree)"))
        print(f"drinks read:             {len(r.all)}")
        print(f"with a `to top`:         {len(rows)}")
        print(f"  published:             {sum(1 for x in rows if x['live'])}")
        print(f"  build measurable:      {sum(1 for x in rows if x['complete'])}")
        print(f"glasses with a floor:    {len(r.floors())}")
        print(f"capacities declared:     {len(r.capacity)}")
        print(f"ice displacements:       {len(r.displacement)}")
        return
    print(markdown(r), end="")


if __name__ == "__main__":
    main()
