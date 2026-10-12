"""Emit _data/food/cooking_methods.yml from cooking-methods.html's own tables.

DO NOT RUN THIS. It is a spent migration tool, kept as the record of how the
data file was made. It has no flags and no `__main__` guard: running or
importing it OVERWRITES `_data/food/cooking_methods.yml`, which has been
edited by hand since and is the source of truth (DECISIONS §14, MANUAL §14).
Edit the data file directly.

It reads `food/reference/cooking-methods.html` as it stood at the commit
PRE_MIGRATION, through `git show`, and expects the repository root as the
working directory. Rows are parsed, not retyped: no figure is changed and no
method is reworded.

What it does to a row on the way through:

  - classifies the Timing cell into a `shape` (`classify`), reading the cell
    without its parenthetical asides;
  - labels a bare oven temperature `fan` and drops a conventional figure
    (`fan_only`);
  - splits Notes into sentences, drops correction history, and moves sourcing
    sentences to `source_note` (`clean`);
  - adds the short `outcome` from OUTCOMES and skips the rows in EXCLUDE.
"""
import pathlib
import re
import subprocess

SRC = pathlib.Path("food/reference/cooking-methods.html")
OUT = pathlib.Path("_data/food/cooking_methods.yml")
# The source is pinned to git, not read from the working tree: the page now
# renders from this script's output, so the working copy holds no tables and
# would yield an empty data file. A re-run reproduces the migration and
# overwrites every hand edit made to the data file since.
PRE_MIGRATION = "8bdbd27"
html = subprocess.run(
    ["git", "show", f"{PRE_MIGRATION}:food/reference/cooking-methods.html"],
    capture_output=True, text=True, check=True).stdout
assert html.count("<table>") == 15, (
    f"expected the pre-migration page with 15 tables, got {html.count('<table>')} "
    f"-- has PRE_MIGRATION drifted off the right commit?")


RANGE = r"(\d+(?:\.\d+)?)(?:\s*[–-]\s*(\d+(?:\.\d+)?))?"

# Which internal-temperature node each protein's finished figure lives at, so
# a schedule can end on a thermometer reading instead of a clock.
TEMP_REF = {
    "chicken": "poultry.chicken", "turkey": "poultry.turkey",
    "goose": "poultry.goose", "duck": "poultry.duck",
    "beef": "beef.tender_roast", "pork": "pork.roasting",
    "lamb": "lamb.roasting", "ham": "ham.cured",
}

def text(fragment):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", fragment)).strip()


def num(s):
    return float(s) if "." in s else int(s)


# --- notes: drop correction history without damaging the sentence ------------
# Split into sentences first and drop whole ones. The splitter requires
# whitespace and a capital after the full stop, so the decimal point in
# "a 1.7-2 kg bird" cannot end a sentence. Every sentence lands in `notes`,
# lands in `source_note`, or is recorded in `dropped_sentences`.
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\u201c])")

DROP = re.compile(
    r"corrected from|used to (say|claim|be)|which was (roughly|actually)"
    r"|didn't even match|doesn't match the formula|the previous \w+ (here|figure)"
    r"|this used to claim|corrected 20\d\d", re.I)

# Sourcing belongs beside the figure it vouches for, so that `notes` reads as
# an outcome.
SOURCE = re.compile(
    r"^(confirmed|rate confirmed|drop-to temperature confirmed|widely-cited"
    r"|not independently|timing temperature|temperature itself|estimated by analogy"
    r"|sources?[:\s])",
    re.I)

dropped_sentences = []
source_sentences = []


def clean(note):
    """-> (notes, source_note). Every sentence is accounted for in one of
    three places: kept, moved to sourcing, or recorded as a deliberate drop."""
    if not note:
        return None, None
    kept, sourced = [], []
    for sentence in SENTENCE_SPLIT.split(note.strip()):
        s = sentence.strip()
        if not s:
            continue
        if DROP.search(s):
            dropped_sentences.append(s)
        elif SOURCE.match(s):
            sourced.append(s)
            source_sentences.append(s)
        else:
            kept.append(s)
    notes = " ".join(kept).strip(" .,;") or None
    src = " ".join(sourced).strip() or None
    return notes, src


# --- oven temperatures: fan, always -------------------------------------------
# House style is fan-only (MANUAL §5). A bare figure on the source page is
# already fan: the rows that state a fan/conventional pair match the bare
# figures elsewhere in the same protein. So a bare figure is labelled, not
# converted, and no number changes. That is also the safer error: a
# conventional figure labelled "fan" runs 20°C hot, where subtracting 20 from
# a fan figure would undercook.
CONVENTIONAL = re.compile(
    r"\s*[/(]?\s*≈?\s*\d+(?:\s*[–-]\s*\d+)?\s*°C\s*conventional\s*\)?")
BARE_TEMP = re.compile(r"(\d+(?:\s*[–-]\s*\d+)?\s*°C)(?!\s*fan)")


def fan_only(oven):
    if not oven:
        return None, None
    basis = "stated" if "fan" in oven.lower() else "inferred"
    out = CONVENTIONAL.sub("", oven)
    out = BARE_TEMP.sub(r"\1 fan", out)
    out = re.sub(r"\s{2,}", " ", out).strip().rstrip(",").strip()
    return out, basis


# --- what you get, in a few words --------------------------------------------
# A short answer to "which method?", drafted from each row's notes, which stay
# beside it as the fuller answer. test_every_method_has_a_short_outcome checks
# presence and length.
OUTCOMES = {
    "chicken/standard_constant_roast": "Reliable default",
    "chicken/high_heat_start_then_reduce": "Crisp skin, moist meat",
    "chicken/low_and_slow_high_heat_blast_at_end": "Juiciest meat",
    "chicken/foil_tented_roast": "Protects the breast",
    "chicken/fully_foil_wrapped_steam_roast": "Very moist, pale skin",
    "chicken/roasting_bag": "Fast, least mess",
    "chicken/spatchcocked_flattened": "Fastest, most even",

    "turkey/standard_constant_roast": "Reliable default",
    "turkey/high_heat_start_then_reduce": "Browned skin, gentle finish",
    "turkey/foil_tented_throughout_removed_at_end": "For the biggest birds",
    "turkey/fully_wrapped_steam_roast": "Very moist, pale skin",
    "turkey/roasting_bag": "Fastest enclosed method",
    "turkey/low_and_slow_blast_at_end": "Most tender, long haul",
    "turkey/spatchcocked": "Fastest overall",

    "goose/standard_constant_roast": "Reliable default",
    "goose/high_heat_start_then_reduce": "Crisp skin first",
    "goose/low_and_slow_blast_at_end": "Best fat render",
    "goose/foil_tented_removed_at_end": "Protects the breast",
    "goose/steaming_parboil_assisted": "Traditional, crispest skin",

    "duck/standard_constant_roast": "Reliable default",
    "duck/high_heat_start_then_reduce": "Fast crisp skin",
    "duck/low_and_slow_blast_at_end": "Maximum fat render",
    "duck/steaming_parboil_assisted": "Crispest skin",
    "duck/spatchcocked": "Even breast and leg",

    "beef/standard_constant_roast": "Reliable default",
    "beef/high_heat_sear_then_reduce": "Crusted outside",
    "beef/low_temp_roast_reverse_method": "Evenest colour throughout",
    "beef/low_temp_roast_hot_blast_at_end": "Even, with a crust",
    "beef/closed_oven_off_method": "Old trick, oven-dependent",
    "beef/oven_brisket_covered_no_liquid": "Roast-like brisket",
    "beef/oven_brisket_low_and_slow": "Most tender brisket",
    "beef/pot_roast_chuck_or_similar_braised": "Wet braise",
    "beef/short_rib_braised": "Falls off the bone",
    "beef/chuck_roast_dry_covered_no_liquid": "Sliceable, not shreddy",

    "pork/standard_constant_roast_lean_loin_no_crackling": "Reliable for loin",
    "pork/standard_constant_roast_leg_shoulder_with_crackling": "Leg with crackling",
    "pork/high_heat_start_then_reduce": "Crackling early",
    "pork/low_temp_roast_reverse_method": "Evenest, most forgiving",
    "pork/low_temp_roast_hot_blast_at_end": "Even, with a crisp finish",
    "pork/foil_tented_removed_at_end": "Stops the outside drying",
    "pork/tenderloin_high_heat_throughout": "Quickest, easy to overshoot",
    "pork/shoulder_low_and_slow": "Pulled pork",
    "pork/shoulder_very_low_and_slow": "Most tender, most forgiving",
    "pork/shoulder_covered_then_uncovered": "Moist, crisp at the end",
    "pork/belly_low_and_slow_then_blast": "Crackling on belly",

    "lamb/standard_constant_roast": "Reliable for leg",
    "lamb/high_heat_start_then_reduce": "Browned early, gentle finish",
    "lamb/low_temp_roast_reverse_method": "Evenest colour throughout",
    "lamb/low_temp_roast_hot_blast_at_end": "Even, with a crisp finish",
    "lamb/rack_high_heat_throughout": "Quickest, for a rack",
    "lamb/rack_sear_then_oven_finish": "Restaurant method",
    "lamb/shoulder_low_and_slow": "Pulled lamb",
    "lamb/shoulder_very_low_and_slow": "Most tender, most forgiving",
    "lamb/shoulder_covered_then_uncovered": "Moist, crisp at the end",
    "lamb/breast_low_and_slow_then_blast": "Self-basting, crisp finish",

    "ham/standard_constant_roast_plain": "Reliable default",
    "ham/high_heat_start_then_reduce_plain": "Crackling early",
    "ham/low_and_slow_hot_blast_plain": "Evenest, most tender",
    "ham/sugar_rubbed_roast": "Caramelised crust",
    "ham/marmalade_or_treacle_glazed": "Glazed finish",
    "ham/boneless_netted_rolled": "Boneless, denser",
    "ham/boil_then_roast_plain": "Less salty, traditional",
    "ham/roast_only_plain": "Simplest for cured ham",
    "ham/sugar_rubbed_after_boil_or_roast_base": "Caramelised crust",
    "ham/marmalade_or_treacle_glazed_after_boil_or_roast_base": "Glazed finish",
    "ham/boneless_netted_rolled_cured": "Boneless, denser",
}


# Where each protein's doneness figures live on the temperature charts, so a
# schedule can hand off to "see other doneness" rather than dead-ending on a
# single figure. Not derivable from internal_temp_ref: four birds share one
# ruler section, and beef's ref points at tender_roast while the charts splits
# beef three ways.
CHART_ANCHOR = {
    "chicken": "poultry", "turkey": "poultry",
    "goose": "poultry", "duck": "poultry",
    "beef": "beef-tender-roasting-cuts",
    "pork": "pork", "lamb": "lamb", "ham": "ham",
}


# Methods Helen has decided against keeping, removed at source so that they
# leave every reader of the data together.
EXCLUDE = {"beef/closed_oven_off_method"}


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def classify(t):
    low = t.lower()
    if low.startswith(("same as", "base method")) or low.startswith("add ~"):
        return "relative", {"relative_to": t}
    if "conflicting sources" in low:
        m = re.search(RANGE + r"\s*min/kg", t)
        return "disputed", {"rate_min": num(m.group(1)),
                            "rate_max": num(m.group(2) or m.group(1))}
    if low.startswith("simmer"):
        r = re.findall(RANGE + r"\s*min/kg", t)
        return "staged", {"stages": [
            {"name": "simmer", "rate_min": num(r[0][0]),
             "rate_max": num(r[0][1] or r[0][0])},
            {"name": "roast", "rate_min": num(r[1][0]),
             "rate_max": num(r[1][1] or r[1][0])}]}
    if " for rare" in low and " for medium" in low:
        p = re.findall(RANGE + r"\s*min/kg\s*\+\s*" + RANGE + r"\s*min", t)
        return "by_doneness", {"by_doneness": {
            "rare": {"rate_min": num(p[0][0]), "rate_max": num(p[0][0]),
                     "flat_add": num(p[0][2])},
            "medium": {"rate_min": num(p[1][0]), "rate_max": num(p[1][0]),
                       "flat_add": num(p[1][2])}}}
    m = re.search(RANGE + r"\s*hrs?/kg", t)
    if m:
        return "rate", {"rate_min": num(m.group(1)) * 60,
                        "rate_max": num(m.group(2) or m.group(1)) * 60}
    m = re.search(RANGE + r"\s*(?:min|hrs?)\s+total", t)
    if m and "/kg" not in t.split("total")[0]:
        mult = 60 if "hr" in t.split("total")[0][-8:] else 1
        return "total", {"total_min": num(m.group(1)) * mult,
                         "total_max": num(m.group(2) or m.group(1)) * mult}
    m = re.search(RANGE + r"\s*min/kg", t)
    if m:
        out = {"rate_min": num(m.group(1)), "rate_max": num(m.group(2) or m.group(1))}
        f = re.search(r"\+\s*" + RANGE + r"\s*min", t)
        if f:
            out["flat_add"] = num(f.group(1))
            if f.group(2):
                out["flat_add_max"] = num(f.group(2))
        return "rate", out
    return "unparsed", {}


def yaml_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


lines = [
    "# =============================================================================",
    "# COOKING METHODS — oven temperatures, timings and coverings, as DATA.",
    "# =============================================================================",
    "# GENERATED from food/reference/cooking-methods.html's own tables, which stay",
    "# the human-readable page. Every figure is transcribed by machine, not retyped,",
    "# so nothing has been re-researched and nothing has changed value. Correction",
    "# history has been dropped from the notes (Helen, 2026-08-13: \"keep safety and",
    "# sources, drop correction history\") -- that was scaffolding for a fact-check",
    "# pass that is finished.",
    "#",
    "# `shape` IS THE FIELD THAT MATTERS, and it exists because a timing is not",
    "# always a formula. 52 of the 66 rows are `rate` and a calculator can just",
    "# multiply; the rest are one of five other things, and a calculator that",
    "# averaged them into a confident serving time would be worse than none:",
    "#",
    "#   rate         rate_min/rate_max minutes per kg, plus optional flat_add",
    "#   total        a fixed time that does NOT scale with weight",
    "#   staged       two rates in sequence (simmer, then roast)",
    "#   by_doneness  a different rate per doneness level",
    "#   relative     defined against another row; no figure of its own",
    "#   disputed     sources genuinely disagree; refuse rather than average",
    "#   unparsed     prose, no formula recoverable",
    "#",
    "# Steak, fish and shellfish are absent on purpose: their tables carry cuts and",
    "# recommended methods, with no timings in them at all.",
    "#",
    "# internal_temp_ref points into internal_temperatures.yml, so a schedule can",
    "# finish on a thermometer figure rather than on a clock.",
    "",
]

sections = re.split(r'<h2 class="recipe-section-heading" id="([^"]+)"', html)
counts = {}

for i in range(1, len(sections), 2):
    sid, body = sections[i], sections[i + 1]
    subs = re.findall(r'<p class="recipe-section-subtitle">(.*?)</p>', body, re.S)
    heads = re.findall(r"<thead>\s*<tr>(.*?)</tr>", body, re.S)
    bodies = re.findall(r"<tbody>(.*?)</tbody>", body, re.S)

    methods = []
    for n, (hd, tb) in enumerate(zip(heads, bodies)):
        cols = [text(c) for c in re.findall(r"<th>(.*?)</th>", hd, re.S)]
        if not any(c.startswith("Timing") for c in cols):
            continue
        col = {c: k for k, c in enumerate(cols)}
        ti = next(k for c, k in col.items() if c.startswith("Timing"))
        group = text(subs[n]) if n < len(subs) else None
        for tr in re.findall(r"<tr>(.*?)</tr>", tb, re.S):
            cells = [text(c) for c in re.findall(r"<td>(.*?)</td>", tr, re.S)]
            if len(cells) <= ti:
                continue
            raw = re.sub(r"\s*\([^)]*\)", "", cells[ti]).strip()
            shape, fields = classify(raw)
            if f"{sid}/{slug(cells[0])}" in EXCLUDE:
                continue
            counts[shape] = counts.get(shape, 0) + 1
            m = {"id": slug(cells[0]), "name": cells[0],
                 "shape": shape, "timing": cells[ti]}
            if group:
                m["group"] = group
            for label, key in (("Oven temp", "_oven_raw"), ("Covering", "covering"),
                               ("Temp change", "temp_change"), ("Liquid", "liquid"),
                               ("Temp/covering", "covering")):
                if label in col and len(cells) > col[label]:
                    m[key] = cells[col[label]]
            outcome = OUTCOMES.get(f"{sid}/{m['id']}")
            if outcome:
                m["outcome"] = outcome
            if "_oven_raw" in m:
                oven, basis = fan_only(m.pop("_oven_raw"))
                if oven:
                    m["oven"] = oven
                    m["oven_basis"] = basis
            if "Weight range" in col and len(cells) > col["Weight range"]:
                # The display string as well as the numbers: the page renders a
                # "Weight range" column, and "4–8 kg" is not reconstructable
                # from two floats without guessing the dash and the unit.
                m["weight_range"] = cells[col["Weight range"]]
                w = re.search(RANGE + r"\s*kg", cells[col["Weight range"]])
                if w:
                    m["weight_min"] = num(w.group(1))
                    m["weight_max"] = num(w.group(2) or w.group(1))
            m.update(fields)
            if "Notes" in col and len(cells) > col["Notes"]:
                note, source_note = clean(cells[col["Notes"]])
                if note:
                    m["notes"] = note
                if source_note:
                    m["source_note"] = source_note
            methods.append(m)

    if not methods:
        continue

    lines.append(f"{sid}:")
    lines.append(f"  label: {yaml_str(sid.title())}")
    if sid in TEMP_REF:
        lines.append(f"  internal_temp_ref: {TEMP_REF[sid]}")
    if sid in CHART_ANCHOR:
        lines.append(f"  chart_anchor: {CHART_ANCHOR[sid]}")
    lines.append("  methods:")
    for m in methods:
        first = True
        for key, value in m.items():
            lead = "    - " if first else "      "
            first = False
            if isinstance(value, str):
                lines.append(f"{lead}{key}: {yaml_str(value)}")
            elif isinstance(value, (int, float)):
                lines.append(f"{lead}{key}: {value:g}")
            elif key == "stages":
                lines.append(f"{lead}stages:")
                for st in value:
                    lines.append(f"        - name: {yaml_str(st['name'])}")
                    lines.append(f"          rate_min: {st['rate_min']:g}")
                    lines.append(f"          rate_max: {st['rate_max']:g}")
            elif key == "by_doneness":
                lines.append(f"{lead}by_doneness:")
                for lvl, spec in value.items():
                    lines.append(f"        {lvl}:")
                    for kk, vv in spec.items():
                        lines.append(f"          {kk}: {vv:g}")
    lines.append("")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {OUT} — {sum(counts.values())} methods")
print(f"  sentences moved to source_note: {len(source_sentences)}")
print(f"  correction-history sentences dropped: {len(dropped_sentences)}")
_have = sum(1 for v in [None] for _ in [0])
for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
    print(f"  {k:<12} {v}")
