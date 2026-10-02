"""Which drinks do not fit their glass -- the flag half of #1238.

    python3 scripts/glass_fit_report.py                 # build, then report
    python3 scripts/glass_fit_report.py --site tmp/x    # reuse a local build

Writes `tmp/glass_fit_report.md`, a GitHub checklist, and prints a summary.

A REPORT AND NOT A TEST, deliberately. A red `main` is a deploy outage, and
every line this prints is a judgement for Helen about ONE drink -- the glass
may be right and the recipe generous, or the reverse, or she may simply like
it that way ("let's offer rules, then I'll happily break them in the
kitchen"). A test would force an answer; a checklist asks the question.

THE VOLUME IS THE SITE'S OWN, READ OFF THE BUILT PAGE. `volume_for` in
`_plugins/cocktail_units.rb` computes it at build time and the drink page
carries it as `data-total-ml`; a second parse of the amounts here would be a
second answer to "how big is this drink" waiting to disagree with the page. So
this builds the site with the local config (drafts render there) and reads the
attribute. A drink the plugin withholds a figure for is listed as unchecked
rather than guessed at.

WHAT GOES IN THE GLASS IS NOT THE RECIPE. Shaking or stirring with ice adds
water, and ice served in the glass takes up room. The factors are data --
`fit_rules` in `_data/cocktails/glasses.yml`, each a sourced {low, high}
range -- because they are the rules the glasses page states, and one copy read
twice beats two. THIS REPORT READS THE FORGIVING END OF EVERY RANGE, so a flag
means the drink does not fit even on the kindest reading of the sources; the
first run took the middles and flagged a Tom Collins in a highball.

What this file owns is only the READING of a drink's method into a dilution
family, which is a heuristic over the method steps and says so.
"""
import argparse
import html
import pathlib
import re
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "_data" / "cocktails"
BUILD = ROOT / "tmp" / "_glass_fit_site"
OUT = ROOT / "tmp" / "glass_fit_report.md"

# On the scaler's controls since #1257 (2026-10-02), when the visible
# "Approximately X ml" line that used to carry it was removed.
TOTAL_ML = re.compile(r'class="cocktail-scale-controls" data-total-ml="([\d.]+)"')


def front_matter(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    return yaml.safe_load(text.split("---", 2)[1]) or {}


def drinks():
    """(label, where, front matter, built page path relative to the site root)."""
    for path in sorted((ROOT / "_cocktail_recipes").glob("*.md")):
        yield path.stem, "published", front_matter(path), \
            pathlib.Path("cocktails/recipes") / path.stem / "index.html"
    drafts = ROOT / "_cocktail_drafts"
    for path in sorted(drafts.rglob("*.md")):
        if path.name == "README.md":
            continue
        rel = path.relative_to(drafts).with_suffix("")
        yield str(rel), "draft", front_matter(path), \
            pathlib.Path("cocktails/drafts") / rel / "index.html"


def method_family(steps):
    """The dilution family a drink's method reads as. First match wins.

    Blend first (a frozen drink may be shaken too). A short shake, a whip, or a
    shake "with a few pieces" of ice is the light one. A shake whose every
    mention is `dry` has no wet dilution and gets its own family so the report
    can say so. A pitcher filled with ice and stirred is a stir.
    """
    text = " ".join(str(s).lower() for s in steps or [])
    if "blend" in text:
        return "blended"
    if re.search(r"short shake|whip|shake with (a few|three)", text):
        return "short_shake"
    if re.search(r"(?<!dry )shake", text):
        return "shake"
    if "dry shake" in text:
        return "dry_shake_only"
    if re.search(r"stir[^.]*with ice|pitcher[^.]*ice", text):
        return "stir"
    if "swizzle" in text:
        return "swizzle"
    return "build"


def top_ml(ingredients, top_up):
    """(midpoint, ml_min) of what the `(top)` pours spend.

    The midpoint is what the plugin's `top_up_ml` spends, so it is what is
    inside the page's total and has to come back out of it. `ml_min` is the
    least the declared range allows, which is what a glass must leave room for.
    """
    mid = least = 0.0
    for ing in ingredients or []:
        if str(ing.get("amount", "")).strip() != "(top)":
            continue
        generics = ing.get("generic")
        generics = generics if isinstance(generics, list) else [generics]
        tops = [top_up[g] for g in generics if g in top_up]
        if tops:
            mid += max((t["ml_min"] + t["ml_max"]) / 2 for t in tops)
            least += max(t["ml_min"] for t in tops)
    return mid, least


def stats_key(glass, glasses):
    for key, spec in (glasses.get("survey_only_types") or {}).items():
        if glass in spec.get("spellings", []):
            return key
    return glasses["icons"].get(glass)


def room(capacity, ice, family, key, rules, fill=None):
    """Millilitres of drink a glass of this capacity takes, on the forgiving end."""
    if family == "blended":
        return capacity  # the ice is IN the drink, and a frozen drink is heaped
    wash = capacity * rules["washline"]["stemmed" if key in rules["stemmed"] else "tumbler"]
    if ice in rules["ice_space"]:
        space = rules["ice_space"][ice]["low"] * (rules["half_fill"] if fill == "half" else 1)
        return wash * (1 - space)
    if ice == "large cube":
        return wash - rules["large_cube_ml"]["low"]
    return wash


def served_ml(base, family, rules):
    """What the BUILD becomes in the glass, on the forgiving end.

    A top is not in `base`. It is poured after the shaker, so it takes no
    dilution, and it FILLS WHAT IS LEFT -- which is the #1076 argument, a top
    being capacity less build less ice -- so a topped drink is judged on
    whether its build fits and on how much room that leaves for the top.
    """
    if family == "blended":
        return base * rules["blended_multiplier"]["low"]
    return base * (1 + rules["dilution"][family]["low"])


HOW = {
    "blended": "blended, the ice in the drink (x{m:g})",
    "dry_shake_only": "dry shake only, no dilution counted",
    "build": "built, no dilution counted",
    "swizzle": "swizzled, the crushed ice does the work",
    "shake": "shaken, +{d:.0%} water",
    "short_shake": "short shake, +{d:.0%} water",
    "stir": "stirred with ice, +{d:.0%} water",
}


def check(fm, total, glasses, rules, top_up):
    """(context line, [(glass, verdict, detail)]) for one drink."""
    serve = fm.get("serve") or {}
    ice = serve.get("ice") or "none"
    fill = serve.get("fill")
    family = method_family(fm.get("method"))
    serves = int(fm.get("serves") or 1)
    top, top_least = top_ml(fm.get("ingredients"), top_up)
    served = served_ml(total - top, family, rules)
    per_glass = served / serves

    results = []
    for glass in [str(g).lower() for g in fm.get("glass") or []]:
        key = stats_key(glass, glasses)
        s = (glasses.get("typical_ml") or {}).get(key)
        if not s:
            results.append((glass, "unchecked", f"no surveyed capacity for {glass!r}"))
            continue
        if key == "punch-bowl":
            # The bowl holds the batch; the ladle fills the cups.
            limit = rules["washline"]["tumbler"]
            cup = rules["punch_cup_ml"]
            batch = served + top
            verdict = ("over" if batch > s["max"] * limit
                       else "tight" if batch > s["median"] * limit else "ok")
            if serves > 1 and per_glass > cup["high"]:
                verdict = "cup" if verdict == "ok" else verdict
            note = (f"batch ~{batch:.0f} ml in a bowl typically {s['median']} ml "
                    f"(surveyed {s['min']}–{s['max']})")
            if serves > 1:
                note += f"; ~{per_glass:.0f} ml a cup, against a usual {cup['low']}–{cup['high']}"
            results.append((glass, verdict, note))
            continue

        typical, smallest, largest = (room(c, ice, family, key, rules, fill)
                                      for c in (s["median"], s["min"], s["max"]))
        up_in_a_stem = ice == "none" and family != "blended" and key in rules["stemmed"]
        if per_glass > largest:
            verdict = "over"
        elif per_glass > typical:
            verdict = "tight"
        elif top and typical - per_glass < top_least:
            verdict = "top"
        elif up_in_a_stem and per_glass + top < rules["lost_below"] * smallest:
            verdict = "lost"
        elif up_in_a_stem and per_glass + top < rules["lost_below"] * typical:
            verdict = "small"
        else:
            verdict = "ok"
        what = "the build" if top else "the drink"
        note = (f"~{per_glass:.0f} ml of {what} in the glass; a typical {glass} takes "
                f"~{typical:.0f} ml served this way (holds {s['median']} ml, surveyed "
                f"{s['min']}–{s['max']})")
        if top:
            note += (f"; that leaves ~{max(typical - per_glass, 0):.0f} ml for a top "
                     f"the site counts as {top:g} ml (at least {top_least:g})")
        results.append((glass, verdict, note))

    how = HOW[family].format(d=rules["dilution"].get(family, {}).get("low", 0),
                             m=rules["blended_multiplier"]["low"])
    context = (f"recipe {total:g} ml" + (f" incl. ~{top:g} ml top" if top else "")
               + f"; {how}; ice: {ice}" + (f", {fill}" if fill else "")
               + (f"; serves {serves}" if serves > 1 else ""))
    return context, results


WORDS = {
    "over": "**too big even for the largest surveyed glass**",
    "tight": "too big for a typical one",
    "lost": "**lost even in the smallest surveyed glass**",
    "small": "under half a typical one",
    "top": "no room for the top the site counts",
    "cup": "a big pour for a punch cup",
    "unchecked": "not checked",
}
ORDER = ["over", "lost", "tight", "top", "small", "cup", "unchecked"]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--site", type=pathlib.Path,
                        help="an existing local build to read instead of building")
    args = parser.parse_args(argv)

    site = args.site
    if site is None:
        site = BUILD
        result = subprocess.run(
            ["bundle", "exec", "jekyll", "build", "--quiet",
             "--config", "_config.yml,_config_local.yml", "--destination", str(BUILD)],
            cwd=ROOT, capture_output=True, text=True, timeout=900)
        if result.returncode != 0:
            print(result.stdout[-2000:] + result.stderr[-2000:])
            return 1
    site = site if site.is_absolute() else ROOT / site

    glasses = yaml.safe_load((DATA / "glasses.yml").read_text(encoding="utf-8"))
    costs = yaml.safe_load((DATA / "costs.yml").read_text(encoding="utf-8"))
    rules = glasses["fit_rules"]

    flagged, cups, unchecked, fine = [], [], [], 0
    for label, where, fm, page in drinks():
        if not fm:
            continue
        built = site / page
        if not built.exists():
            unchecked.append(f"- {label} ({where}): no built page at `{page}`")
            continue
        m = TOTAL_ML.search(built.read_text(encoding="utf-8"))
        if not m:
            unchecked.append(f"- {label} ({where}): the site withholds its volume")
            continue
        context, results = check(fm, float(m.group(1)), glasses, rules,
                                 costs.get("top_up_ml") or {})
        # A drink with several glasses is fine if ANY of them fits: the list is
        # alternatives, and Helen picks at the cupboard.
        if any(v == "ok" for _, v, _ in results):
            fine += 1
            continue
        worst = min(ORDER.index(v) for _, v, _ in results)
        title = html.unescape(str(fm.get("title") or label))
        # ONE QUESTION, ASKED ONCE. Every punch whose only problem is the cup
        # has the same problem, so they share a checklist item.
        if all(v == "cup" for _, v, _ in results):
            cups.append(f"  - {title} (`{label}`): {results[0][2]}")
            continue
        lines = [f"- [ ] **{title}** ({where}, `{label}`): {context}"]
        lines += [f"  - {g}: {WORDS[v]}. {n}" for g, v, n in results]
        flagged.append((worst, title.lower(), lines))

    flagged.sort()
    count = len(flagged) + len(cups)
    body = [f"{count} drinks flagged, {fine} fit, {len(unchecked)} not checked.", ""]
    body += [line for _, _, lines in flagged for line in lines]
    if cups:
        body += [f"- [ ] **{len(cups)} punches pour more a cup than a punch cup holds** "
                 f"(usual {rules['punch_cup_ml']['low']}–{rules['punch_cup_ml']['high']} ml). "
                 "The bowls are fine; the question is `serves:`, or whether these are "
                 "served in bigger glasses than punch cups."] + cups
    if unchecked:
        body += ["", "Not checked:", ""] + unchecked
    OUT.write_text("\n".join(body) + "\n", encoding="utf-8")
    print(body[0])
    print(f"Written to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
