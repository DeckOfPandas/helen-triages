"""Write _data/food/price_research.yml as a table to read: each food's prices,
its median and bracket, and its confidence (MANUAL §8.2).

    python3 scripts/food_price_table.py [out.md]

Writes tmp/food-price-research.md unless given a path; reads nothing else.
The bracket shown is the range costs.yml gets, by the plugin's rule: the
median with the middle 50% for 6+ prices, with the whole range for 3-5, the
mean of 2, the one price. _plugins/food_costs.rb is what the site uses;
tests/test_food_costs.py holds the two to the same quartiles."""
from __future__ import annotations

import re
import statistics
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "_data" / "food" / "price_research.yml"
SECTION = re.compile(r"^  # --- (.+?) -+\s*$")
FOOD = re.compile(r"^  ([^#\s].*):\s*$")


def money(x: float) -> str:
    return f"£{x:.3f}".rstrip("0") if x < 0.1 else f"£{x:.2f}"


def median_text(vals: list[float]) -> str:
    n = len(vals)
    if n == 1:
        return money(vals[0])
    if n == 2:
        return money(sum(vals) / 2) + " (mean of 2)"
    med = statistics.median(vals)
    if n <= 5:
        return f"{money(med)} ({money(min(vals))}–{money(max(vals))})"
    q1, _, q3 = statistics.quantiles(vals, n=4, method="inclusive")
    return f"{money(med)} (middle 50% {money(q1)}–{money(q3)})"


def confidence(vals: list[float], thin: bool) -> str:
    if thin or len(vals) < 2:
        return "low"
    return "high" if len(vals) >= 4 and max(vals) <= 2 * min(vals) else "medium"


def main(out: Path) -> None:
    text = SOURCE.read_text(encoding="utf-8")
    foods = yaml.safe_load(text)["foods"]
    section_of, section = {}, "Other"
    for line in text.splitlines():
        if m := SECTION.match(line):
            section = m.group(1)
        elif m := FOOD.match(line):
            section_of[m.group(1)] = section
    lines = [f"Prices from `_data/food/price_research.yml`, checked "
             f"{yaml.safe_load(text)['checked']}.\n"]
    current = None
    for food, entry in foods.items():
        if section_of.get(food) != current:
            current = section_of.get(food)
            lines += ["", f"### {current.capitalize()}", "",
                      "| food | prices found | median | confidence |", "|---|---|---|---|"]
        for unit, prices in entry.items():
            if unit in ("thin", "note"):
                continue
            found = [p.split(" ", 1) for p in prices]
            vals = [float(v) for v, *_ in found]
            listed = ", ".join(f"{money(float(v))} {' '.join(s)}" for v, *s in found)
            per = f"/{unit}" if unit in ("kg", "l", "g") else f"{unit}"
            note = f"; {entry['note']}" if entry.get("note") and unit == "each" else ""
            lines.append(f"| {food} ({per}{note}) | {listed} | **{median_text(vals)}** "
                         f"| {confidence(vals, entry.get('thin', False))} |")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tmp" / "food-price-research.md")
