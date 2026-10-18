"""The two ingest documents written for a Claude with no repository.

`model_instructions/INGEST_ONE_RECIPE.md` and `INGEST_ONE_COCKTAIL.md` are
handed to claude.ai, which cannot read `_data/`, so each prints the closed
vocabularies as literal text and carries a worked example of the file shape.
That is deliberate duplication of data, and this module is what keeps the copy
honest: without it, retiring a tag silently makes a document wrong.

Two guards. Each vocabulary between `<!-- vocab:<name> start -->` markers is
rendered by `scripts/build_ingest_vocab.py` and checked both ways
(`test_every_vocab_block_matches_its_generator`). The hand-written prose and
examples are checked one way only: everything printed must still be declared.
A retired term left in teaches a shape the suite rejects, to a reader who
cannot run the suite; a new term not yet printed merely under-serves.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "model_instructions"
FOOD_DOC = DOCS / "INGEST_ONE_RECIPE.md"
COCKTAIL_DOC = DOCS / "INGEST_ONE_COCKTAIL.md"

pytestmark = pytest.mark.shared


# ---- Loaders: every rule comes from _data/ or from the suite, never re-typed ----
# A checker carrying its own copy of the contract eventually passes a document
# into a shape the real tests reject, while looking green the whole time.

def _doc(path: Path) -> str:
    assert path.is_file(), (
        f"{path.relative_to(ROOT)} is missing. It is handed to sessions with "
        f"no checkout; deleting it is a real decision, so delete this module "
        f"in the same commit rather than letting these checks quietly pass."
    )
    return path.read_text(encoding="utf-8")


def _data(name: str, site: str = "cocktails"):
    return yaml.safe_load((ROOT / "_data" / site / f"{name}.yml").read_text(encoding="utf-8"))


def _yaml_blocks(text: str) -> list[str]:
    return re.findall(r"```yaml\n(.*?)```", text, re.S)


def _file_blocks(text: str) -> list[tuple[str, dict]]:
    """Every yaml block with something to check, not just the worked example.

    Each document carries an annotated schema as well as the worked example,
    and the schema is the one a reader copies first.
    """
    out = []
    for block in _yaml_blocks(text):
        body = block.strip().strip("-").strip()
        fm = yaml.safe_load(body)
        if not isinstance(fm, dict):
            continue
        # A whole file, or a fragment illustrating one key (a bare
        # `ingredients:` list with no title): match on having something to
        # check, not on being a file.
        if "title" in fm or "ingredients" in fm or "ingredient_groups" in fm:
            out.append((block, fm))
    return out


def _example(text: str, marker: str) -> dict:
    """The worked example, found by a string only it contains."""
    block = next((b for b in _yaml_blocks(text) if marker in b), None)
    assert block, f"no worked example containing {marker!r}"
    return yaml.safe_load(block.strip().strip("-").strip())


def _flat(text: str) -> str:
    """Whitespace-normalised and with the `<!-- vocab: -->` markers removed.

    Without the first, a hard wrap inside a printed string reads as a stale
    entry. Without the second, the garnish scraper, which reads
    `**Group:** a · b · c` up to the next `*`, takes the end marker after the
    last group as part of a garnish. A marker carries no vocabulary.
    """
    return re.sub(r"\s+", " ", re.sub(r"<!--.*?-->", " ", text, flags=re.S))


def _declared_garnishes() -> set[str]:
    g = _data("garnish")
    out = {s for grp in g["canonical"].values() for s in grp}
    out.add(g["no_garnish"])
    return out


def _declared_generics() -> set[str]:
    """Every generic `ingredients.yml` declares, through the suite's own loader.

    Imported, not restated: `test_cocktails._declared_generics` knows the
    exclusions (`NOT_GENERIC_LISTS`, the `<family>_characters` suffix), and a
    second copy here drifts from it silently.
    """
    from test_cocktails import _declared_generics as declared, _vocab
    return declared(_vocab())


def _canonical_steps() -> set[str]:
    """Every literal under `canonical:` and every `shapes:` sentence: the
    document prints both, `<X>` and all."""
    methods = _data("methods")
    literal = {s for grp in methods["canonical"].values() for s in grp}
    shapes = {s for grp in (methods.get("shapes") or {}).values() for s in grp}
    return literal | shapes


def _glass_icons() -> set[str]:
    return set(_data("glasses")["icons"])


def _food_taxonomy() -> dict:
    return _data("taxonomy", site="food")


# ---- Both documents ----

@pytest.mark.parametrize("path", [FOOD_DOC, COCKTAIL_DOC], ids=lambda p: p.name)
def test_every_yaml_block_in_a_standalone_doc_parses(path):
    """A document whose example does not load teaches an unusable shape.

    These files are edited as prose, so a stray indent inside a fenced block
    is invisible to the writer and copied verbatim by the reader.
    """
    blocks = _yaml_blocks(_doc(path))
    assert blocks, f"{path.name} contains no ```yaml blocks at all"
    for i, block in enumerate(blocks):
        try:
            yaml.safe_load(block.strip().strip("-").strip())
        except yaml.YAMLError as exc:
            pytest.fail(f"{path.name} yaml block {i + 1} does not parse:\n{exc}")


def test_every_vocab_block_matches_its_generator():
    """The two-way half: what the documents print is what `_data/` declares.

    The same code `--check` runs, imported and not re-implemented, so the
    script and the suite cannot disagree about what stale means. It fails in
    both directions -- a retired garnish still printed, a new one missing --
    because a marked block is mechanical and has a generator to catch it up.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_ingest_vocab import check  # noqa: E402

    diff, problems = check()
    assert not (diff or problems), (
        "a vocabulary block in a standalone document no longer matches "
        "`_data/`:\n\n"
        + "\n".join(problems)
        + ("\n" if problems else "")
        + diff
        + "\nRun: python3 scripts/build_ingest_vocab.py --write\n"
          "Do NOT hand-edit inside a `<!-- vocab:... -->` pair; the script "
          "owns those lines and the prose around them is yours."
    )


# ---- The food document ----

def test_every_recipe_block_in_the_food_doc_uses_declared_tags_and_stars():
    """Both blocks, the annotated schema and the worked example: the schema
    block is the one a reader meets first and copies."""
    blocks = _file_blocks(_doc(FOOD_DOC))
    assert len(blocks) >= 2, (
        f"expected the schema block AND the worked example, found "
        f"{len(blocks)}. An empty scan must never read as 'nothing wrong'."
    )
    tax = _food_taxonomy()
    declared = set(tax["tags"]["mood"]) | set(tax["tags"]["practicalities"])

    problems = []
    for _, fm in blocks:
        title = fm.get("title", "?")
        for t in fm.get("tags") or []:
            if t not in declared:
                problems.append(f"{title}: undeclared tag {t!r}")
        star = fm.get("star_ingredient")
        if star is not None and star not in tax["star_ingredients"]:
            problems.append(f"{title}: undeclared star_ingredient {star!r}")
    assert not problems, (
        "the food document prints a block a reader would copy verbatim, "
        "using a term taxonomy.yml does not declare:\n  " + "\n  ".join(problems)
    )


def test_the_food_docs_example_obeys_the_schema_it_describes():
    """The rules the document states in prose, applied to its own example."""
    fm = _example(_doc(FOOD_DOC), "Crispy Sage Butter Gnocchi")
    problems = []

    if list(fm.get("meta") or {}) != ["rewritten", "awaiting_fix", "proofread"]:
        problems.append(f"meta keys/order: {list(fm.get('meta') or {})}")
    if not all(v is False for v in (fm.get("meta") or {}).values()):
        problems.append(f"meta values must all be False: {fm.get('meta')}")
    if ("serves" in fm) == ("makes" in fm):
        problems.append("serves xor makes")
    if ("method" in fm) == ("method_groups" in fm):
        problems.append("method xor method_groups")
    if fm.get("method_short") != [""]:
        problems.append(f'method_short must be [""]: {fm.get("method_short")!r}')

    steps = fm.get("method") or []
    if len(steps) % 2:
        problems.append("method is not in QQ original / QQ Claude pairs")
    for i in range(0, len(steps) - 1, 2):
        if not steps[i].startswith("QQ original "):
            problems.append(f"step {i + 1} is not a `QQ original` line")
        if not steps[i + 1].startswith("QQ Claude "):
            problems.append(f"step {i + 2} is not a `QQ Claude` line")

    for group in fm.get("ingredient_groups") or []:
        for item in group.get("items") or []:
            if "item" not in item:
                problems.append(f"ingredient with no `item`: {item}")
            elif re.match(r"^[\d~½¼¾]", str(item["item"])):
                problems.append(f"quantity inside item text: {item['item']!r}")

    assert not problems, (
        "the food document's worked example breaks rules the document "
        "itself states:\n  " + "\n  ".join(problems)
    )


def test_the_food_docs_example_quotes_every_scalar_and_list_member():
    """No unquoted `serves: 2` or `tags: [carbs party]` in the worked example.

    /tidy-drafts repairs quoting mechanically downstream, so an unquoted
    example is copied for a long time before anybody notices.
    """
    from test_front_matter import SCALAR_STRING_FIELDS  # noqa: E402

    block = next(b for b in _yaml_blocks(_doc(FOOD_DOC))
                 if "Crispy Sage Butter Gnocchi" in b)
    problems = []
    for line in block.split("\n"):
        m = re.match(r"^([a-z_]+):\s*(.+?)\s*$", line)
        if not m:
            continue
        key, value = m.groups()
        if key in SCALAR_STRING_FIELDS and not value.startswith(('"', "'")):
            problems.append(f"{key}: {value} -- must be quoted")
        if key in ("tags", "main_ingredients") and value.startswith("["):
            for member in re.findall(r"[\[,]\s*([^,\]]+)", value):
                if not member.strip().startswith(('"', "'")):
                    problems.append(f"{key} member {member.strip()!r} unquoted")
    assert not problems, (
        "unquoted value(s) in the food document's worked example:\n  "
        + "\n  ".join(problems)
    )


def test_every_tag_and_star_the_food_doc_prints_is_still_declared():
    """The drift check: the document's reference lists vs `taxonomy.yml`.

    One direction only, deliberately. A retired term left in the document
    teaches a value the suite rejects, to a reader who cannot run the suite.
    A new term the document lacks merely under-serves, and requiring it would
    make every taxonomy addition a second edit for no safety gain.
    """
    flat = _flat(_doc(FOOD_DOC))
    tax = _food_taxonomy()
    declared_tags = set(tax["tags"]["mood"]) | set(tax["tags"]["practicalities"])

    section = flat.split("pick from these")[1].split("Meanings you would not")[0]
    printed = {t.strip(" `*") for t in re.findall(r"`([^`]+)`", section)}
    printed = {t for t in printed if t}
    assert len(printed) >= 20, (
        f"only found {len(printed)} tags printed in the food document; the "
        f"scraper has gone stale against the document's own formatting. "
        f"An empty scan must never read as 'nothing wrong'."
    )
    stale = sorted(t for t in printed if t not in declared_tags)
    assert not stale, (
        f"the food document prints tag(s) that taxonomy.yml no longer "
        f"declares: {stale}"
    )

    star_section = flat.split("one of these 14, or omit")[1].split("It is the one thing")[0]
    printed_stars = {s.strip(" `*") for s in re.findall(r"`([^`]+)`", star_section)}
    printed_stars = {s for s in printed_stars if s}
    assert len(printed_stars) >= 12, (
        f"only found {len(printed_stars)} star ingredients printed; scraper stale"
    )
    stale_stars = sorted(s for s in printed_stars if s not in tax["star_ingredients"])
    assert not stale_stars, (
        f"the food document prints star ingredient(s) that taxonomy.yml no "
        f"longer declares: {stale_stars}"
    )


def test_the_food_docs_source_type_table_uses_declared_types():
    """The citation table's first column, against the declared source types.

    The list above the table is generated and the table is not: its other
    columns are the citation's shape and an example, which are judgement. So
    it gets the one-way check: what it prints must still be declared.
    `magazine` is the near-miss.
    """
    from test_source_attribution import VALID_TYPES  # noqa: E402

    flat = _flat(_doc(FOOD_DOC))
    section = flat.split("`magazine` is not one of them")[1].split("**The date is")[0]
    printed = {t for t in re.findall(r"\|\s*`([a-z]+)`\s*\|", section)}
    assert len(printed) >= 6, (
        f"only found {len(printed)} source type(s) in the food document's "
        f"citation table; the scraper has gone stale against its formatting. "
        f"An empty scan must never read as 'nothing wrong'."
    )
    stale = sorted(t for t in printed if t not in VALID_TYPES)
    assert not stale, (
        f"the food document's citation table prints source_type(s) that are "
        f"not among the eight: {stale}"
    )


# ---- The cocktail document ----

def test_every_drink_block_in_the_cocktail_doc_obeys_the_schema_it_describes():
    """Every drink block, the annotated schema as well as the worked example.

    `mood` is required and must be `[]` (scripts/derive_cocktail_moods.py
    derives it, so a hand-written one is reverted next run), and every drink
    names a glass (#491).
    """
    blocks = _file_blocks(_doc(COCKTAIL_DOC))
    assert len(blocks) >= 2, (
        f"expected the schema block AND the worked example, found "
        f"{len(blocks)}. An empty scan must never read as 'nothing wrong'."
    )
    problems = []
    for _, fm in blocks:
        problems += _drink_problems(fm)
    assert not problems, (
        "a drink block in the cocktail document breaks rules the document "
        "itself states:\n  " + "\n  ".join(problems)
    )


def _drink_problems(fm: dict) -> list[str]:
    problems = []

    # A fragment has no title and is only checked for what it shows.
    if "title" in fm:
        if "mood" not in fm:
            problems.append("no `mood` key -- it is required even when empty")
        elif fm["mood"] != []:
            problems.append(f"mood must be [] and is derived: {fm['mood']!r}")
        if not (fm.get("glass") or []):
            problems.append("no glass -- #491, every drink names one")
        # `who knows`, not `QQ`: `QQ` is not in the ship vocabulary
        # (test_cocktails.py::test_meta_ship_is_a_rung_or_off_scale), so an
        # example writing it teaches a file that fails the suite on arrival.
        if fm.get("meta", {}).get("ship") != "who knows":
            problems.append(
                f'meta.ship must be "who knows": '
                f"{fm.get('meta', {}).get('ship')!r}"
            )
        # An ingest cannot know whether Helen has made the drink, so
        # `made_before` is always false on a fresh file (#722).
        if fm.get("meta", {}).get("made_before") is not False:
            problems.append(
                f"meta.made_before must be false: "
                f"{fm.get('meta', {}).get('made_before')!r}"
            )
        # The `meta` keys and their order are the schema's own list, not
        # re-typed; the three gate flags (#668) are all False on a new file.
        from test_cocktails import (  # noqa: E402
            META_KEYS_IN_ORDER, keys_out_of_page_order,
        )
        # Page order (#1213): a block out of order teaches every file copied
        # from it to arrive out of order. The predicate is the suite's own.
        out_of_order = keys_out_of_page_order(list(fm))
        if out_of_order:
            problems.append(
                f"top-level keys are not in page order: "
                f"{' '.join(out_of_order[0])} -- want "
                f"{' '.join(out_of_order[1])}"
            )
        meta = fm.get("meta") or {}
        if list(meta) != META_KEYS_IN_ORDER:
            problems.append(f"meta keys/order: {list(meta)} != {META_KEYS_IN_ORDER}")
        for flag in ("rewritten", "awaiting_fix", "proofread"):
            if flag in meta and meta[flag] is not False:
                problems.append(f"meta.{flag} must be False on a new drink: {meta[flag]!r}")

    # A glass must be canonical, not merely drawable: `rocks` has an icon and
    # is still the wrong spelling -- glasses.yml's `canonical_glasses` maps it
    # to `old fashioned`.
    corrections = _data("glasses")["canonical_glasses"]
    for g in fm.get("glass") or []:
        if g in corrections:
            problems.append(
                f"glass {g!r} is a spelling glasses.yml corrects to "
                f"{corrections[g]!r} -- the document must print the right one"
            )
        elif g not in _glass_icons():
            problems.append(f"glass {g!r} has no icon")
    for g in fm.get("garnish") or []:
        if g not in _declared_garnishes():
            problems.append(f"undeclared garnish {g!r}")

    us = re.compile(r"\b(oz|ounce|ounces|tsp|teaspoon|teaspoons|tbsp|"
                    r"tablespoon|tablespoons|cup|cups)\b")
    for item in fm.get("ingredients") or []:
        amount = str(item.get("amount", ""))
        if us.search(amount):
            problems.append(f"US unit in the example: {amount!r}")
        if re.fullmatch(r"[\d.]+", amount.strip()):
            problems.append(f"bare number with no unit: {amount!r}")
        # A `QQ`, a `QQ <the source's words>`, or a generic the document
        # itself prints in `vocab:generics`, which a repo-less reader can look
        # up. What is refused is the guess in between: `agave nectar` beside
        # `agave syrup`, `rye whiskey` beside `rye`.
        generic = str(item.get("generic") or "").strip()
        if not (generic == "QQ" or generic.startswith("QQ ")
                or generic in _declared_generics()):
            problems.append(f"a block guessed a generic: {item.get('generic')!r}")

    return [f"{fm.get('title', '?')}: {p}" for p in problems]


def test_every_vocabulary_the_cocktail_doc_prints_is_still_declared():
    """Garnishes, glasses and method steps, against the live `_data/`.

    One way only: what is printed must still be declared. This vocabulary
    moves, and the document cannot feel it.
    """
    flat = _flat(_doc(COCKTAIL_DOC))

    section = flat.split("### `garnish`")[1].split("Four rules")[0]
    printed = set()
    for chunk in re.findall(r"\*\*[A-Za-z ]+:\*\*([^*]+)", section):
        printed.update(g.strip() for g in chunk.split("·"))
    printed = {g for g in printed if g and not g.startswith("`")}
    assert len(printed) >= 30, (
        f"only found {len(printed)} garnishes printed in the cocktail "
        f"document; the scraper has gone stale against its formatting."
    )
    stale = sorted(g for g in printed if g not in _declared_garnishes())
    assert not stale, f"document prints undeclared garnish(es): {stale}"

    steps = set(re.findall(r"`([A-Z][^`]*?\.)`", flat))
    assert len(steps) >= 20, f"only found {len(steps)} method steps printed"
    # A filled `shapes:` sentence in the prose ("...other than the cola with
    # ice.") is canonical too; the slot matches one run of text.
    shape_res = [
        re.compile("^" + re.escape(h) + r"(.+)" + re.escape(t) + "$")
        for s in _canonical_steps() if "<X>" in s
        for h, _, t in [s.partition("<X>")]
    ]
    stale_steps = sorted(
        s for s in steps
        if s not in _canonical_steps() and not any(rx.match(s) for rx in shape_res)
    )
    assert not stale_steps, (
        f"document prints method step(s) methods.yml no longer declares: "
        f"{stale_steps}"
    )

    glass_section = flat.split("### `glass` — use these spellings")[1].split("**These spellings")[0]
    glasses = {g.strip() for g in re.findall(r"`([^`]+)`", glass_section)}
    glasses = {g for g in glasses if g}
    assert len(glasses) >= 15, f"only found {len(glasses)} glasses printed"
    stale_glass = sorted(g for g in glasses if g not in _glass_icons())
    assert not stale_glass, f"document prints glass(es) with no icon: {stale_glass}"


def test_every_declared_garnish_has_exactly_one_group():
    """The cocktail document's garnish grouping is data: `canonical:` maps a
    group name to a list, and every declared garnish sits in exactly one.

    scripts/build_ingest_vocab.py prints the groups verbatim into
    INGEST_ONE_COCKTAIL.md, so a garnish under two groups prints twice. An
    entry stays a string: a per-entry dict breaks `_declared_garnishes()` in
    test_cocktails.py, silently, for every drink.
    """
    vocab = _data("garnish")
    groups = vocab.get("canonical") or {}
    assert groups, (
        "garnish.yml has no `canonical:` mapping, so the grouping this test "
        "guards -- and the block the cocktail document prints -- has nothing "
        "behind it. An empty scan must never read as 'nothing wrong'."
    )

    seen = {}
    problems = []
    for group, members in groups.items():
        assert isinstance(members, list) and members, (
            f"garnish group {group!r} is not a non-empty list."
        )
        for garnish in members:
            if garnish in seen:
                problems.append(
                    f"{garnish!r} is in both {seen[garnish]!r} and {group!r}"
                )
            seen[garnish] = group

    marker = vocab.get("no_garnish")
    if marker in seen:
        problems.append(
            f"the no-garnish marker {marker!r} is declared under "
            f"{seen[marker]!r}. It is the DECISION that a drink takes none, "
            f"never a garnish, and printing it in a group would teach a "
            f"reader to write it beside a real one."
        )

    assert not problems, (
        "every declared garnish must sit in exactly one group -- the cocktail "
        "document prints those groups verbatim:\n  " + "\n  ".join(problems)
    )
    assert set(seen) == _declared_garnishes() - {marker}, (
        "the grouped garnishes and `_declared_garnishes()` disagree, which "
        "means one of the two derivations has gone stale."
    )


def test_the_cocktail_docs_correction_map_matches_glasses_yml():
    """The wrong-spelling table is a copy of `canonical_glasses`.

    The document prints it so a repo-less reader writes `old fashioned`, not
    `rocks`, first time. One way only: an entry the document lacks is a
    spelling silently rewritten later, which is confusing and not fatal.
    """
    flat = _flat(_doc(COCKTAIL_DOC))
    live = _data("glasses")["canonical_glasses"]
    rows = re.findall(r"\|\s*([a-z, \-]+?)\s*\|\s*\*\*([a-z ]+?)\*\*\s*\|", flat)
    assert rows, "no correction-map rows found in the cocktail document"

    problems = []
    for wrongs, right in rows:
        for wrong in (w.strip() for w in wrongs.split(",")):
            if wrong not in live:
                problems.append(f"{wrong!r} is not in canonical_glasses")
            elif live[wrong] != right:
                problems.append(f"{wrong!r} maps to {live[wrong]!r}, document says {right!r}")
    assert not problems, (
        "the cocktail document's glass correction table disagrees with "
        "glasses.yml:\n  " + "\n  ".join(problems)
    )


# ---- The instructions a web chat is given ----

WEB_DOC = DOCS / "CLAUDE_WEB_INGEST.md"


def test_the_web_instructions_still_match_the_envelope():
    """The instruction block in CLAUDE_WEB_INGEST.md §2 restates facts about
    the envelope that live elsewhere. If any of them moves, the web chat is
    taught the wrong shape and every envelope it produces is rejected.
    """
    text = _doc(WEB_DOC)
    block = text.split("## 2. Instructions for the web chat", 1)[1]
    for needle, where in [
        ("INGEST_ONE_RECIPE.md", "the food document's name"),
        ("INGEST_ONE_COCKTAIL.md", "the cocktail document's name"),
        ("`ingest: <slug>`", "the issue title INGEST_INBOX_DESIGN.md §6 fixes"),
        ("## What I could not know", "the hand-back heading the parser requires"),
        ("FOUR backticks", "the outer fence that lets the inner yaml fence copy raw"),
    ]:
        assert needle in block, (
            f"CLAUDE_WEB_INGEST.md §2 no longer says {needle!r} ({where}). The "
            f"web chat is told only what that block says."
        )
    for p in (FOOD_DOC, COCKTAIL_DOC):
        assert "## 0. How to hand this back" in _doc(p), (
            f"{p.name} lost its §0; the web instructions defer to it for the "
            f"envelope shape."
        )
