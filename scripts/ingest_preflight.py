#!/usr/bin/env python3
"""Report every decision a freshly-ingested batch needs from Helen, in ONE list.

    python3 scripts/ingest_preflight.py                 # what this branch changed
    python3 scripts/ingest_preflight.py <path> [...]    # explicit files
    python3 scripts/ingest_preflight.py --all           # both whole collections

RUN IT THROUGH `/ingest`, which is the procedure; this file is only the engine.

WHY IT EXISTS. The 2026-08-31 Death & Co ingest brought Helen vocabulary gaps in
a TRICKLE -- bottles at one moment, generics at another, garnishes at a third --
so she was interrupted three times for what was really one sitting. A gap found
while transcribing drink four is not urgent; it is one line in a list she reads
once. Batching them is the whole point.

IT NEVER WRITES ANYTHING. `scripts/tidy_drafts.py` is the fixer and its boundary
is the same one: mechanical things get fixed, judgements get reported.

EVERY RULE IS IMPORTED FROM THE TEST SUITE, NEVER RE-TYPED. `tidy_drafts.py`
established that, and the reason is sharper for a REPORTER than for a fixer: a
report carrying its own copy of the vocabulary will eventually call a declared
value undeclared, or stay silent when it should not, and either way Helen stops
trusting the list. If an import here breaks because a test constant moved, that
is the mechanism working.

IT DOES NOT DUPLICATE THE SUITE. Run `pytest` for what is already enforced; a
second opinion that disagrees with the tests is worse than no opinion. This
looks only for what is VALID and still wants a human -- an undeclared word, a
near-duplicate phrasing, a silence in the source.
"""
from __future__ import annotations

import argparse
import collections
import difflib
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

from test_cocktails import (  # noqa: E402
    US_UNITS, _declared_garnishes, _declared_generics, _garnish_vocab,
    _millilitres, _vocab,
)

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---", re.S)
FOOD = ROOT / "_food_drafts"
COCKTAILS = ROOT / "_cocktail_drafts"

# How close a new method step must be to a canonical one before it is called a
# near-miss rather than a new instruction. 0.80 was picked by running it over
# the whole collection: it catches "Stir all THE ingredients with ice" against
# "Stir all ingredients with ice" and does not pair two genuinely different
# muddles. Lower it and every strain looks like every other strain.
NEAR_MISS = 0.80


def _data(name):
    return yaml.safe_load((ROOT / "_data" / "cocktails" / name).read_text(encoding="utf-8"))


def _parse(path):
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    m = FRONT_MATTER.match(text)
    if not m:
        return None
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None
    return fm if isinstance(fm, dict) else None


def _changed_in(repo):
    """Files this branch added or changed against its own main."""
    if not (repo / ".git").exists():
        return []
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "diff", "--name-only", "main...HEAD"],
            capture_output=True, text=True, timeout=20, check=False).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    return [repo / p for p in out.split("\n") if p.endswith(".md") and (repo / p).exists()]


def _targets(args):
    if args.paths:
        return [Path(p).resolve() for p in args.paths]
    if args.all:
        return sorted(COCKTAILS.rglob("*.md")) + sorted(FOOD.rglob("*.md"))
    return _changed_in(COCKTAILS) + _changed_in(FOOD)


def _site_of(path):
    names = {p.name for p in path.parents}
    if names & {"_cocktail_drafts", "_cocktail_recipes"}:
        return "cocktails"
    if names & {"_food_drafts", "_food_recipes"}:
        return "food"
    return None


class Report:
    """Grouped by DECISION, never by file.

    Helen rules on a CLASS -- "all cane syrups are 2:1" -- far more cheaply than
    on twelve separate files, and a per-file report makes her derive the class
    herself, twelve times.
    """

    def __init__(self):
        self.groups = collections.OrderedDict()
        self.seen = 0

    def add(self, heading, detail, where, why=None):
        g = self.groups.setdefault(
            heading, {"why": why, "items": collections.defaultdict(list)})
        if why and not g["why"]:
            g["why"] = why
        g["items"][detail].append(where)

    def render(self):
        if not self.seen:
            return ("Nothing to check -- no recipe files found. Pass paths, or "
                    "--all, or check you are on an ingest branch with commits "
                    "against main.")
        if not self.groups:
            return f"{self.seen} file(s) checked. Nothing needs Helen."
        out = [f"{self.seen} file(s) checked.", ""]
        total = 0
        for heading, g in self.groups.items():
            out += ["=" * 76, heading, "=" * 76]
            if g["why"]:
                out += [g["why"], ""]
            for detail, wheres in sorted(g["items"].items()):
                total += 1
                shown = sorted(set(wheres))
                out.append(f"  {detail}")
                out.append("      " + ", ".join(shown[:6])
                           + (f"  (+{len(shown) - 6} more)" if len(shown) > 6 else ""))
            out.append("")
        out.append(f"{total} decision(s) across {len(self.groups)} group(s).")
        return "\n".join(out)


def _us_units_in(text, ignored):
    words = {w.strip(".,()").lower() for w in re.findall(r"[A-Za-z]+", text)}
    return (words - ignored) & US_UNITS


# =============================================================================
# Cocktails
# =============================================================================

def check_cocktail(path, fm, rep, ctx):
    slug = path.stem

    for item in (fm.get("ingredients") or []):
        if not isinstance(item, dict):
            continue

        gen = item.get("generic")
        for g in (gen if isinstance(gen, list) else [gen]):
            if g == "QQ":
                rep.add("UNTYPED INGREDIENTS -- a generic is needed, or a new one declaring",
                        f"{item.get('amount') or '?'} -- {item.get('note') or 'no note'}",
                        slug,
                        why="Nothing declared fitted, so it was left QQ rather than\n"
                            "filed under something close. Each is either a new generic\n"
                            "for ingredients.yml or a category that already exists.")
            elif isinstance(g, str) and g not in ctx["generics"]:
                rep.add("UNDECLARED GENERICS -- not in ingredients.yml", repr(g), slug)

        sug = item.get("suggestion")
        for s in (sug if isinstance(sug, list) else [sug]):
            if isinstance(s, str) and s.lower() not in ctx["bottles"]:
                rep.add("BOTTLES THE SOURCE NAMES THAT bottles.yml DOES NOT KNOW",
                        repr(s), slug,
                        why="HANDOVER 9.3.2 -- a bottle's category is NOT derived from\n"
                            "the ingredient beside it. Declare it, or leave it off until\n"
                            "you have poured it. Helen, 2026-08-31: \"I will update these\n"
                            "when I make the drinks, so QQ is right.\"")

        amt = item.get("amount")
        if amt is None:
            continue
        hit = _us_units_in(str(amt), ctx["ignored"])
        if hit:
            rep.add("US UNITS IN AN AMOUNT -- convert to ml",
                    f"{amt!r} ({', '.join(sorted(hit))})", slug,
                    why="1 oz = 30 ml, 1 tsp = 5 ml, from `measures:`. Helen,\n"
                        "2026-09-01: \"I don't want any US units, just ml.\"")
        else:
            try:
                _millilitres(amt, ctx["measures"])
            except ValueError as why:
                notes = " ".join(str(n) for n in (fm.get("notes") or []))
                if "no unit in the source" not in notes:
                    rep.add("AMOUNTS THAT CANNOT BE READ AS A QUANTITY",
                            f"{amt!r} -- {why}", slug)

    for g in (fm.get("garnish") or []):
        if isinstance(g, str) and g not in ctx["garnishes"]:
            rep.add("UNDECLARED GARNISHES -- not in garnish.yml", repr(g), slug,
                    why="Either a new garnish, or a second spelling of one already\n"
                        "there. Plurals and case both count.")

    for gl in (fm.get("glass") or []):
        canon = ctx["canonical_glasses"].get(gl)
        if canon:
            rep.add("GLASS SPELLINGS THAT ARE NOT CANONICAL", f"{gl!r} -> {canon!r}", slug)
        elif gl not in ctx["glass_icons"]:
            rep.add("GLASSES WITH NO ICON AND NO ENTRY", repr(gl), slug)

    for s in (fm.get("method") or []):
        if not isinstance(s, str) or s.startswith("QQ"):
            continue
        hit = _us_units_in(s, ctx["ignored"])
        if hit:
            rep.add("US UNITS IN A METHOD STEP -- convert to ml",
                    f"{s[:66]!r} ({', '.join(sorted(hit))})", slug,
                    why="The amount fields are not the only place a unit hides. Three\n"
                        "punch steps carried ounces after the 2026-09-01 conversion had\n"
                        "already fixed every `amount:` in the collection.")
        if s in ctx["canonical_steps"] or s in ctx["proposed_steps"]:
            # A step already on the left of a methods.yml proposal is TRACKED,
            # not undecided. Re-reporting it makes an ingest report look like a
            # backlog and buries the handful of things that are genuinely new --
            # which is the whole failure this script exists to fix.
            continue
        close = difflib.get_close_matches(s, ctx["canonical_steps"], n=1, cutoff=NEAR_MISS)
        if close:
            rep.add("METHOD STEPS THAT ARE NEARLY A CANONICAL ONE (#630)",
                    f"{s[:60]!r}\n        -> {close[0]!r}", slug,
                    why="A near-variant, not a new instruction -- 'a' vs 'the',\n"
                        "'with ice' vs 'over ice', 'large ice block' vs 'large block\n"
                        "of ice'. methods.yml's test: does the phrasing carry\n"
                        "information? If not, use the canonical form.")

    ts = fm.get("to_serve")
    if isinstance(ts, str) and re.match(r"\s*[A-Z][a-z]+\s+(the|a|an|with|into|over)\b", ts):
        rep.add("`to_serve` THAT READS LIKE AN ACTION", repr(ts), slug,
                why="`to_serve` is a NOUN PHRASE -- 'Straw.', 'Without ice.'. If it\n"
                    "instructs, or its position in the sequence matters, it is a\n"
                    "method step.")

    if not (fm.get("mood") or []):
        rep.add("DRINKS WITH NO MOOD", "run scripts/derive_cocktail_moods.py", slug)

    ship = (fm.get("meta") or {}).get("ship")
    if ship in (None, "QQ"):
        rep.add("DRINKS WITH NO `meta.ship` RATING", f"ship={ship!r}", slug,
                why="Ten of the nineteen moods are Helen's and no rule produces them\n"
                    "(#452), so a new drink is missing half the browse axes until she\n"
                    "looks. Worth doing in the same sitting.")


# =============================================================================
# Food
# =============================================================================

QUALIFIERS = {
    "sugar": r"(caster|granulated|icing|demerara|muscovado|brown|palm|coconut|vanilla|golden|jaggery)",
    "butter": r"(unsalted|salted|clarified|browned|ghee)",
    "flour": r"(plain|self-raising|strong|wholemeal|00|rye|spelt|gram|corn|rice|buckwheat)",
    "milk": r"(whole|semi|skimmed|full[- ]fat|coconut|almond|oat|soya|evaporated|condensed|buttermilk)",
    "egg": r"(large|medium|small|free[- ]range|quail|duck)",
    "garlic": r"(clove|bulb|granule|powder|purée|puree|paste|smoked|black|wild)",
    "ginger": r"(fresh|ground|stem|pickled|root|paste|grated)",
    "chocolate": r"(dark|milk|white|plain|bitter|couverture|%)",
    "mustard": r"(dijon|english|wholegrain|american|seed|powder)",
    "vinegar": r"(white|red|cider|sherry|balsamic|rice|malt|wine)",
}


def check_food(path, fm, rep, ctx):
    slug = path.stem

    for group in (fm.get("ingredient_groups") or []):
        for item in (group.get("items") or []):
            if not isinstance(item, dict):
                continue
            text = str(item.get("item") or "")
            low = text.lower()
            for word, qualified in QUALIFIERS.items():
                if re.search(rf"\b{word}", low) and not re.search(qualified, low):
                    rep.add("INGREDIENT QUALIFIERS THE SOURCE MAY HAVE PRINTED (#578)",
                            f"{word}: {text[:56]!r}", slug,
                            why="Which sugar, which butter, which milk. If the page says,\n"
                                "write it -- that is READING, and this is the only session\n"
                                "with the page open. If it is SILENT, leave it: a wrong\n"
                                "'whole milk' looks exactly as confident as a right one.")
            if item.get("amount") is None and re.match(r"\s*[~\d½¼¾⅓⅔]", text):
                rep.add("QUANTITY INSIDE `item:` INSTEAD OF `amount:` (#111)",
                        repr(text[:60]), slug,
                        why="The highlighter is driven by `item.amount` and never scans\n"
                            "item text, so this renders UNSTYLED with no error anywhere.")
            if re.match(r"\s*(large|small|medium)\b", low) and item.get("amount") \
                    and not re.search(r"(large|small|medium)", str(item["amount"]).lower()):
                rep.add("SIZE WORD IN `item:` RATHER THAN WITH THE COUNT (#577)",
                        f"{item.get('amount')!r} + {text[:44]!r}", slug)

    steps = [s.get("step") if isinstance(s, dict) else s for s in (fm.get("method") or [])]
    steps = [s for s in steps if isinstance(s, str)]
    originals = [s for s in steps if s.startswith("QQ original")]
    claudes = [s for s in steps if s.startswith("QQ Claude")]
    plain = [s for s in steps if s.startswith("QQ PLACEHOLDER")]

    if originals and len(originals) != len(claudes):
        rep.add("INTERLEAVED REWRITE IS UNBALANCED",
                f"{len(originals)} `QQ original` vs {len(claudes)} `QQ Claude`", slug)
    if plain and not originals:
        rep.add("METHOD USES BARE `QQ PLACEHOLDER` RATHER THAN THE INTERLEAVED PAIR",
                f"{len(plain)} step(s)", slug,
                why="Helen's default since 2026-09-01: keep the source's wording as\n"
                    "`QQ original` and put the paraphrase under it as `QQ Claude`, so\n"
                    "she can judge the rewrite rather than trust it blind. It used to\n"
                    "be a per-batch ask, which is why it got missed.")

    for step in steps:
        if step.startswith("QQ original"):
            continue          # the source's own words; house style stops here
        for m in re.finditer(r"(\d{2,3})\s*(?:°C|C\b|degrees)", step):
            if "fan" not in step.lower():
                rep.add("OVEN TEMPERATURES NOT STATED AS FAN (#146)",
                        f"{m.group(1)}C in {step[:42]!r}", slug,
                        why="Fan only on this site. WHICH of a printed pair is the fan\n"
                            "figure is answerable from the source and nowhere else, so it\n"
                            "is free now and a hand-worked backlog later.")

    for field in ("prep_time", "cook_time"):
        if str(fm.get(field) or "").strip() in ("", "QQ"):
            rep.add("TIMES THE SOURCE DID NOT STATE", f"{field}={fm.get(field)!r}", slug,
                    why="Left QQ deliberately -- `Estimated N mins` is banned outright\n"
                        "(HANDOVER 5). Fill in from the source, or from cooking it.")

    # A BLANK `star_ingredient` IS NOT REPORTED, and the playtest is why. It
    # fired on 118 drafts -- about a third, which is the rate HANDOVER §7
    # documents as CORRECT ("~a quarter are legitimately blank"). §12 uses this
    # exact field as its worked example of a false finding: "be suspicious of
    # your own findings before reporting them -- check whether what you found is
    # a documented convention (a blank star_ingredient is correct for a plain
    # sponge)". A report that cries wolf on a third of the corpus teaches Helen
    # to skim it, which costs more than the check could ever buy.
    #
    # Proposing a star for a NEW recipe is still tier-2 work and belongs in the
    # ingest doc -- it is just not a defect to flag on an existing file.


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--all", action="store_true", help="scan both whole collections")
    args = ap.parse_args()

    vocab = _vocab()
    methods = _data("methods.yml")
    glasses = _data("glasses.yml")
    bottles = _data("bottles.yml")
    known = set()
    for name, entry in (bottles.get("bottles") or {}).items():
        known.add(name.lower())
        known |= {a.lower() for a in ((entry or {}).get("aliases") or [])}
    known |= {s.lower() for s in (bottles.get("unresolved_suggestions") or {})}

    measures = vocab.get("measures") or {}
    ctx = {
        "generics": _declared_generics(vocab),
        "garnishes": _declared_garnishes(_garnish_vocab()),
        "bottles": known,
        "measures": measures,
        "ignored": {w.lower() for w in (measures.get("ignored_words") or [])},
        "canonical_glasses": glasses.get("canonical_glasses") or {},
        "glass_icons": glasses.get("icons") or {},
        "canonical_steps": sorted(
            {s for grp in (methods.get("canonical") or {}).values() for s in grp}),
        "proposed_steps": set(methods.get("proposals") or {}),
    }

    rep = Report()
    for path in _targets(args):
        site = _site_of(path)
        if site is None:
            continue
        fm = _parse(path)
        if fm is None:
            continue
        rep.seen += 1
        (check_cocktail if site == "cocktails" else check_food)(path, fm, rep, ctx)

    print(rep.render())
    return 0


if __name__ == "__main__":
    sys.exit(main())
