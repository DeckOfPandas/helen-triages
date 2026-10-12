"""Which drinks do not fit their glass -- the flag half of #1238.

    python3 scripts/glass_fit_report.py                 # build, then report
    python3 scripts/glass_fit_report.py --site tmp/x    # reuse a local build

Without `--site` it builds the site with the local config (drafts render
there) into `tmp/_glass_fit_site`. It reads the built drink pages, every `.md`
in `_cocktail_recipes/` and `_cocktail_drafts/`, and `glasses.yml` and
`costs.yml` in `_data/cocktails/`. It writes `tmp/glass_fit_report.md`, a
GitHub checklist, and prints a summary.

The rules:

  - A report and not a test. Every line is a judgement for Helen about one
    drink: the glass may be right and the recipe generous, or the reverse, or
    she may like it that way (DECISIONS §9). A test would force an answer.
  - The volume is the site's own, read off the built page. `volume_for` in
    `_plugins/cocktail_units.rb` computes it and the page carries it as
    `data-total-ml`, with `data-top-ml`, `data-after-ml`, `data-aside-ml` and
    `data-method-family` beside it. Nothing is parsed a second time here, so
    the report and the page cannot disagree. A drink the plugin withholds a
    figure for is listed as unchecked.
  - What goes in the glass is not the recipe: shaking or stirring adds water,
    and ice in the glass takes room. The factors are `fit_rules` in
    glasses.yml, each a sourced {low, high} range. This report reads the
    forgiving end of every range, so a flag means the drink does not fit on
    the kindest reading.
  - Only what was shaken or stirred is watered: `after` is in the glass
    undiluted and `aside` is not in the glass at all.
  - A drink is flagged only when it is over by more than `tolerance`, and a
    drink with several glasses is fine if any one of them fits.
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

# On the scaler's controls (#1257).
TOTAL_ML = re.compile(r'class="cocktail-scale-controls" data-total-ml="([\d.]+)"')
# Beside it (#1179): how much of that total is a `(top)`, and the dilution
# family the plugin read the method as.
TOP_ML = re.compile(r'class="cocktail-scale-controls"[^>]* data-top-ml="([\d.]+)"')
FAMILY = re.compile(r'class="cocktail-scale-controls"[^>]* data-method-family="([a-z_]+)"')
# What is in the glass but was added after the shake, so never watered, and
# what is in the recipe but not in the glass at all (#1244).
AFTER_ML = re.compile(r'class="cocktail-scale-controls"[^>]* data-after-ml="([\d.]+)"')
ASIDE_ML = re.compile(r'class="cocktail-scale-controls"[^>]* data-aside-ml="([\d.]+)"')


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


def top_least(ingredients, top_up):
    """The least the declared range allows a `(top)` to be.

    That is what a glass must leave room for. What the top actually spends is
    the plugin's figure, `data-top-ml` (#1179).
    """
    least = 0.0
    for ing in ingredients or []:
        if str(ing.get("amount", "")).strip() != "(top)":
            continue
        generics = ing.get("generic")
        generics = generics if isinstance(generics, list) else [generics]
        tops = [top_up[g] for g in generics if g in top_up]
        if tops:
            least += max(t["ml_min"] for t in tops)
    return least


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
    """What the build becomes in the glass, on the forgiving end.

    A top is not in `base`: it is added after the shaker, so it takes no
    dilution, and it fills what is left (#1076). A topped drink is judged on
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


def check(fm, total, top, family, glasses, rules, top_up, after=0.0, aside=0.0):
    """(context line, [(glass, verdict, detail)]) for one drink.

    `total`, `top`, `family`, `after` and `aside` are the plugin's, read off
    the built page. Three rules keep a flag honest (#1244):

      1. Only what was shaken is watered. `after` is in the glass undiluted
         (a float, a champagne added after the strain); `aside` is not in the
         glass at all (the rum in a fruit shell).
      2. A flag needs a margin: `tolerance` in fit_rules. Every figure is a
         survey median times a wash line times an ice allowance.
      3. The top flag fires only when the room left is under `top_room_min`
         of the house range's minimum.
    """
    serve = fm.get("serve") or {}
    ice = serve.get("ice") or "none"
    fill = serve.get("fill")
    serves = int(fm.get("serves") or 1)
    least = top_least(fm.get("ingredients"), top_up)
    over_by = 1 + rules["tolerance"]
    served = served_ml(total - top - after - aside, family, rules) + after
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
            if serves > 1 and per_glass > cup["high"] * over_by:
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
        if per_glass > largest * over_by:
            verdict = "over"
        elif per_glass > typical * over_by:
            verdict = "tight"
        elif top and typical - per_glass < least * rules["top_room_min"]:
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
                     f"the site counts as {top:g} ml (the house range says "
                     f"at least {least:g})")
        results.append((glass, verdict, note))

    how = HOW[family].format(d=rules["dilution"].get(family, {}).get("low", 0),
                             m=rules["blended_multiplier"]["low"])
    context = (f"recipe {total:g} ml" + (f" incl. ~{top:g} ml top" if top else "")
               + (f", {after:g} ml of it added after and not watered" if after else "")
               + (f", {aside:g} ml of it not in the glass" if aside else "")
               + f"; {how}; ice: {ice}" + (f", {fill}" if fill else "")
               + (f"; serves {serves}" if serves > 1 else ""))
    return context, results


WORDS = {
    "over": "**too big even for the largest surveyed glass**",
    "tight": "too big for a typical one",
    "lost": "**lost even in the smallest surveyed glass**",
    "small": "under half a typical one",
    "top": "hardly any room for a top",
    "cup": "more than a punch cup holds",
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
        text = built.read_text(encoding="utf-8")
        top = TOP_ML.search(text)
        family = FAMILY.search(text)
        after = AFTER_ML.search(text)
        aside = ASIDE_ML.search(text)
        if not family:
            unchecked.append(f"- {label} ({where}): the page carries no "
                             "`data-method-family`; is the build stale?")
            continue
        context, results = check(fm, float(m.group(1)),
                                 float(top.group(1)) if top else 0.0,
                                 family.group(1), glasses, rules,
                                 costs.get("top_up_ml") or {},
                                 after=float(after.group(1)) if after else 0.0,
                                 aside=float(aside.group(1)) if aside else 0.0)
        # A drink with several glasses is fine if ANY of them fits: the list is
        # alternatives, and Helen picks at the cupboard.
        if any(v == "ok" for _, v, _ in results):
            fine += 1
            continue
        worst = min(ORDER.index(v) for _, v, _ in results)
        title = html.unescape(str(fm.get("title") or label))
        # Every punch whose only problem is the cup has the same problem, so
        # they share one checklist item.
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
        body += [f"- [ ] **{len(cups)} punches make a bigger cup than a punch cup holds** "
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
