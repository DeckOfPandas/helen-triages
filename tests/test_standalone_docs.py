"""The two ingest documents written for a Claude with NO repository.

`model_instructions/INGEST_ONE_RECIPE.md` and `INGEST_ONE_COCKTAIL.md` are
handed to claude.ai when Helen finds a recipe or a drink in the wild. They have
no access to `_data/`, so each one PRINTS the closed vocabularies as literal
text -- 22 tags, 14 star ingredients, 42 garnishes, 23 glasses, 28 canonical
method steps -- and carries a worked example showing the file shape.

THAT IS THE ONLY DELIBERATE DUPLICATION OF DATA IN THIS REPOSITORY, and it is
the same bargain `methods.yml` strikes with its own proposals map and
`glasses.yml` with `all_icons`: copy live data only alongside the test that
keeps the copy honest. Without this module, adding a garnish or retiring a tag
silently makes a document wrong, and nothing looks at markdown.

THE ROT IS ASYMMETRIC AND THAT IS WHY IT MATTERS. A document that omits a new
garnish merely under-serves; a document that still lists a RETIRED tag teaches
a shape the suite rejects, in a session that cannot run the suite, to a reader
who has no way to know. So the drift check runs in one direction on purpose:
everything the document prints must still be declared. It does not require the
document to print everything declared.

WHAT THESE CHECKS HAVE ALREADY CAUGHT, all in documents freshly written by the
agent that wrote this file, none by re-reading:

  - `serves: 2` and `tags: [carbs party]` unquoted in the food example. Chasing
    it found the identical fault in HANDOVER 4's own canonical schema block,
    which had been wrong for nine days and is the most-copied twelve lines in
    that document.
  - The cocktail document told its reader to omit `mood:` (the key is REQUIRED)
    and to write `glass: []` when the source names none (#491: every drink must
    name a glass). Both were real suite failures, found only by copying the
    example into `_cocktail_drafts/` and running pytest.

They began as `tmp/check_doc_example.py` and `tmp/check_cocktail_doc.py`.
Helen, 2026-09-02: "It sounds very much like they should form part of our
suite." They do now, and `tmp/` is not where a guard should live.

THE ASYMMETRY IS NARROWED, NOT ABANDONED, SINCE 2026-09-02. Each vocabulary now
sits between `<!-- vocab:<name> start -->` markers and is rendered by
`scripts/build_ingest_vocab.py` from the same loaders below;
`test_every_vocab_block_matches_its_generator` runs that script's `--check` and
fails if a committed block has drifted in either direction. That is a two-way
guard applied ONLY where the duplication is mechanical. The prose around each
block -- the "meanings you would not guess" bullets, the four garnish rules,
the worked examples -- is judgement, is still hand-written, and is still guarded
one way only. INGEST_INBOX_DESIGN.md §5 is the argument for the split.
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

# Suite marker, so `pytest -m shared` runs this. test_suite_hygiene.py asserts
# every module declares one -- an unmarked file is silently missed by every
# filtered run. `shared` because the pair spans both sites.
pytestmark = pytest.mark.shared


# =============================================================================
# LOADERS -- every rule comes from _data/ or from the suite, never re-typed
# =============================================================================
# A checker carrying its own copy of the contract eventually passes a document
# INTO a shape the real tests reject, while looking green the whole time. Same
# reasoning as scripts/tidy_drafts.py's header states at length.

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
    """EVERY yaml block that is a whole file, not just the worked example.

    Each document carries two: the annotated schema in its section 2, and the
    worked example at the end. THE FIRST ONE IS THE MORE COPIED and was not
    checked at all until 2026-09-02 -- found because a deliberate break aimed
    at the wrong block passed, which is the good outcome of breaking a guard
    on purpose rather than trusting it.
    """
    out = []
    for block in _yaml_blocks(text):
        body = block.strip().strip("-").strip()
        fm = yaml.safe_load(body)
        if not isinstance(fm, dict):
            continue
        # A whole file, OR a FRAGMENT illustrating one key. The cocktail
        # document's section 3 shows a bare `ingredients:` list with no title,
        # and it went unchecked until a deliberate break landed in it and
        # passed -- so match on having something to check, not on being a file.
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

    THE FIRST VERSION OF THE DRIFT SCAN DID NOT NORMALISE WHITESPACE and
    reported twelve stale vocabulary entries, every one of them a line break
    inside a string. HANDOVER 12: be suspicious of your own findings before
    reporting them.

    THE MARKERS CAME OFF FOR THE SAME REASON, 2026-09-02. The garnish scraper
    reads `**Group:** a · b · c` up to the next `*`, and the last group in the
    section is now followed by `<!-- vocab:garnish end -->` with no asterisk
    between them -- so it read `5 drops of olive oil <!-- vocab:garnish end -->`
    as a garnish string and called it undeclared. That is a false finding about
    the SCAFFOLDING, not a weakened check: a marker carries no vocabulary, the
    generator's own test compares the block against `_data/` character for
    character, and every real entry is still checked here. Dropping them is the
    same class of normalisation as dropping the hard wrap that produced them.
    """
    return re.sub(r"\s+", " ", re.sub(r"<!--.*?-->", " ", text, flags=re.S))


def _declared_garnishes() -> set[str]:
    g = _data("garnish")
    out = {s for grp in g["canonical"].values() for s in grp}
    out.add(g["no_garnish"])
    return out


def _canonical_steps() -> set[str]:
    return {s for grp in _data("methods")["canonical"].values() for s in grp}


def _glass_icons() -> set[str]:
    return set(_data("glasses")["icons"])


def _food_taxonomy() -> dict:
    return _data("taxonomy", site="food")


# =============================================================================
# BOTH DOCUMENTS
# =============================================================================

@pytest.mark.parametrize("path", [FOOD_DOC, COCKTAIL_DOC], ids=lambda p: p.name)
def test_every_yaml_block_in_a_standalone_doc_parses(path):
    """A document whose example does not load teaches an unusable shape.

    Cheapest possible check and it earns its place: these files are edited as
    prose, so a stray indent inside a fenced block is invisible to the writer
    and fatal to the reader, who will copy it verbatim.
    """
    blocks = _yaml_blocks(_doc(path))
    assert blocks, f"{path.name} contains no ```yaml blocks at all"
    for i, block in enumerate(blocks):
        try:
            yaml.safe_load(block.strip().strip("-").strip())
        except yaml.YAMLError as exc:
            pytest.fail(f"{path.name} yaml block {i + 1} does not parse:\n{exc}")


def test_every_vocab_block_matches_its_generator():
    """The two-way half: what the documents print IS what `_data/` declares.

    THE SAME CODE `--check` RUNS, imported rather than re-implemented, so the
    script and the suite cannot disagree about what stale means -- the failure
    that would matter here is a green test beside a script that says otherwise.

    It fails in both directions, which the one-way checks below deliberately do
    not: a retired garnish still printed, AND a newly declared one missing. The
    distinction is that a marked block is mechanical duplication with a
    generator behind it, so "the document has not caught up" is a five-second
    fix rather than a two-repo edit -- which is the trade the one-way rule was
    protecting the PROSE from, and prose is not what is inside these markers.
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


# =============================================================================
# THE FOOD DOCUMENT
# =============================================================================

def test_every_recipe_block_in_the_food_doc_uses_declared_tags_and_stars():
    """BOTH blocks -- the annotated schema and the worked example.

    The schema block is the one a reader meets first and copies, and checking
    only the example is how HANDOVER §4's own canonical block sat wrong for
    nine days with a retired tag in it.
    """
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
    """The rules the document itself states, applied to its own example.

    Every one of these is a rule the document spells out in prose a few
    paragraphs above the example, which is exactly the gap HANDOVER 12's
    "you will write down a rule instead of following it" describes.
    """
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
    """Unquoted `serves: 2` is what this check was written for.

    It found exactly that, plus `tags: [carbs party]`, on its first run --
    and chasing it turned up the identical fault in HANDOVER 4's canonical
    schema block, which had been wrong for nine days. /tidy-drafts repairs
    quoting mechanically, which is precisely why nobody had noticed.
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

    ONE DIRECTION ONLY, deliberately. A retired term left in the document is
    the harmful case -- it teaches a value the suite rejects, to a reader who
    cannot run the suite. A newly declared term the document has not caught up
    with merely under-serves, and requiring the document to be exhaustive would
    make every taxonomy addition a two-repo edit for no safety gain.
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
    """The citation table's first column, against the eight real types.

    THE LIST ABOVE THE TABLE IS GENERATED AND THE TABLE ITSELF IS NOT: its
    other two columns are the citation's shape and an example, which are
    judgement and prose. So the table gets the same one-way check every other
    hand-written vocabulary in these documents gets -- what it prints must
    still be declared. `magazine` is the near-miss, and it has been typed by
    hand once already; test_source_attribution.py's header tells that story.
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


# =============================================================================
# THE COCKTAIL DOCUMENT
# =============================================================================

def test_every_drink_block_in_the_cocktail_doc_obeys_the_schema_it_describes():
    """Including the two rules whose absence made the first draft fail.

    `mood` is REQUIRED and must be `[]` (it is derived by
    scripts/derive_cocktail_moods.py, so a hand-written one is reverted next
    run), and every drink must name a glass (#491). The document's first
    version got both backwards and only pytest said so.

    BOTH BLOCKS, not just the worked example -- the annotated schema in section
    2 is the one a reader meets first and copies, and it went unchecked until a
    deliberate break aimed at it passed.
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

    # A FRAGMENT has no title and is only checked for what it shows.
    if "title" in fm:
        if "mood" not in fm:
            problems.append("no `mood` key -- it is required even when empty")
        elif fm["mood"] != []:
            problems.append(f"mood must be [] and is derived: {fm['mood']!r}")
        if not (fm.get("glass") or []):
            problems.append("no glass -- #491, every drink names one")
        # `who knows`, NOT `QQ`, SINCE 2026-09-05. Helen: "Should drinks I
        # haven't made yet have ship who knows? I think that's clearer than QQ
        # or leaving it unset, because it's a positive presence." `QQ` is no
        # longer in the ship vocabulary at all --
        # test_cocktails.py::test_meta_ship_is_a_rung_or_who_knows -- so a
        # document example still writing it would teach a repo-less reader to
        # produce a file that fails the suite on arrival.
        if fm.get("meta", {}).get("ship") != "who knows":
            problems.append(
                f'meta.ship must be "who knows": '
                f"{fm.get('meta', {}).get('ship')!r}"
            )
        # AND THE FIELD THAT NOW CARRIES THE ABSENCE. An ingest cannot know
        # whether Helen has poured the drink, so it is always false on a fresh
        # file (#722); the value gates no publication either way.
        if fm.get("meta", {}).get("made_before") is not False:
            problems.append(
                f"meta.made_before must be false: "
                f"{fm.get('meta', {}).get('made_before')!r}"
            )
        # THE THREE GATE FLAGS JOINED THE DRINK SCHEMA ON 2026-09-02 (#668), and
        # a drink file without them fails test_cocktails.py's meta-order guard
        # the moment it lands. The document's examples are what a repo-less
        # reader copies, so they carry the flags -- read from the schema's own
        # list rather than re-typed, the same rule every block in this file
        # follows -- and all three are False on a new file, as on a recipe.
        from test_cocktails import META_KEYS_IN_ORDER  # noqa: E402
        meta = fm.get("meta") or {}
        if list(meta) != META_KEYS_IN_ORDER:
            problems.append(f"meta keys/order: {list(meta)} != {META_KEYS_IN_ORDER}")
        for flag in ("rewritten", "awaiting_fix", "proofread"):
            if flag in meta and meta[flag] is not False:
                problems.append(f"meta.{flag} must be False on a new drink: {meta[flag]!r}")

    # A GLASS MUST BE CANONICAL, NOT MERELY DRAWABLE. `rocks` has an icon and
    # is still the wrong spelling -- glasses.yml's `canonical_glasses` maps it
    # to `old fashioned`. Checking "has an icon" passed a deliberate break on
    # 2026-09-02, which is exactly what breaking a guard on purpose is for.
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
        if item.get("generic") != "QQ":
            problems.append(f"a block guessed a generic: {item.get('generic')!r}")

    return [f"{fm.get('title', '?')}: {p}" for p in problems]


def test_every_vocabulary_the_cocktail_doc_prints_is_still_declared():
    """Garnishes, glasses and method steps, against the live `_data/`.

    This is the check with the most to guard: 42 garnish strings, 23 glass
    names and 28 canonical steps, all printed as prose. `garnish.yml` went from
    65 distinct strings to 49 in two days, and `methods.yml` lost 15 more the
    week after -- so this vocabulary moves, and the document cannot feel it.
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
    stale_steps = sorted(s for s in steps if s not in _canonical_steps())
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
    """Ruling D11: the document's grouping is DATA, not a map in a script.

    THE FILE ALREADY HELD THE ANSWER and the ruling's wording ("a `group:` key
    per entry") is what it looks like from outside. `canonical:` is a mapping of
    group name to list, so every declared garnish already sits in exactly one
    group -- adding a per-entry key would mean turning each entry from a string
    into a dict, which is the one change that would break
    `_declared_garnishes()` in test_cocktails.py, in silence, for every drink.
    INGEST_INBOX_DESIGN §5 allows the alternative outright: "a `groups:` map
    from group name to list is acceptable". This is that map.

    WHAT CHANGED IS THE CONTRACT, WHICH IS WHY THIS TEST EXISTS. garnish.yml
    said the grouping was "for reading only" and it is now printed verbatim
    into INGEST_ONE_COCKTAIL.md by scripts/build_ingest_vocab.py. A garnish
    listed under two groups would print twice; a group renamed would rename a
    heading in a document handed to a session that cannot check it.
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

    A drink writing `rocks` is corrected to `old fashioned`; the document
    prints that table so a repo-less reader gets it right first time. If the
    map gains an entry and the document does not, the document teaches a
    spelling that will be silently rewritten -- which is confusing rather than
    fatal, so this checks only that what IS printed is still true.
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
