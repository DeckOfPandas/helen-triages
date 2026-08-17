"""The cocktails collection's own rules.

`tests/conftest.py` is explicitly the FOOD suite, and says so: the food schema
does not apply to a cocktail. This is the sibling it anticipated.

WHY THIS FILE SKIPS RATHER THAN FAILS ON AN EMPTY CORPUS, and why that is not
the vacuity trap tests/test_suite_hygiene.py exists to catch. `_cocktail_drafts/`
is its own private git repo, gitignored from this one, so on a clean checkout
of the public repo the directory is genuinely ABSENT -- not empty, absent. That
is a legitimate state and the right response is to skip loudly with a message
saying so.

What is NOT legitimate is the directory being present and yielding nothing,
which would mean the loader has gone stale. So: skip when the collection is
not here, assert non-empty when it is. The distinction is the whole point --
"this machine does not have the drinks" and "I looked and found nothing" must
never produce the same green.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
DRAFTS = ROOT / "_cocktail_drafts"
VOCAB = ROOT / "_data" / "cocktails" / "ingredients.yml"

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---", re.S)

# The families #314 governs. A `generic` on one of these has to come from the
# declared list; a `generic` on a lime juice does not, because the rest of the
# ingredient vocabulary has not been argued out yet.
IS_RUM = re.compile(r"\brum|\brhum|cacha|clairin", re.I)


def _load():
    if not DRAFTS.is_dir():
        pytest.skip(
            "_cocktail_drafts/ is not present. It is a separate private repo "
            "(helen-triages-cocktails-private), gitignored here, so a clean "
            "checkout of the public repo legitimately has no drinks to check. "
            "Clone it into _cocktail_drafts/ to run these."
        )
    out = []
    for path in sorted(DRAFTS.glob("*.md")):
        match = FRONT_MATTER.match(path.read_text(encoding="utf-8"))
        if match:
            out.append((path.stem, yaml.safe_load(match.group(1)) or {}))
    assert out, (
        f"{DRAFTS.name}/ exists but yielded no parseable drinks. The directory "
        f"is here, so this is not the absent-collection case -- either every "
        f"file lost its front matter, or this loader has gone stale. Do not "
        f"let it report green."
    )
    return out


def _vocab():
    if not VOCAB.exists():
        pytest.skip("_data/cocktails/ingredients.yml does not exist yet.")
    return yaml.safe_load(VOCAB.read_text(encoding="utf-8")) or {}


def _rum_generics():
    """(drink, item, generic) for every rum-family ingredient carrying one."""
    out = []
    for slug, fm in _load():
        for item in (fm.get("ingredients") or []):
            if not isinstance(item, dict):
                continue
            name, generic = item.get("item") or "", item.get("generic")
            if generic and IS_RUM.search(name):
                out.append((slug, name, generic))
    return out


def test_no_drink_uses_a_retired_rum_style():
    """`light`, `gold` and `dark` are retired by issue #314.

    Checked FIRST and separately from "not declared", the same way
    test_star_ingredient_is_declared handles retired stars: a value that used
    to mean something must fail with its retirement reason attached, not blend
    into the generic not-declared pile where nobody learns why it went.
    """
    retired = _vocab().get("retired_rum_styles") or {}
    assert retired, (
        "_data/cocktails/ingredients.yml declares no retired_rum_styles, so "
        "this check has nothing to enforce. If the retirements were reversed, "
        "delete this test deliberately rather than leaving it passing."
    )
    offenders = [
        f"{slug}: {name!r} -> {generic!r} ({retired[generic]})"
        for slug, name, generic in _rum_generics()
        if generic in retired
    ]
    assert not offenders, (
        "Retired rum style(s) still in use:\n  " + "\n  ".join(offenders)
        + "\n\nRe-type against rum_styles in _data/cocktails/ingredients.yml. "
          "Which rum a drink actually wants is Helen's own knowledge and is "
          "not recoverable from the spreadsheet -- use QQ, do not guess."
    )


def test_every_rum_generic_is_declared():
    """A rum's `generic` is either a declared style, a permitted untyped
    bottle, or the literal `QQ` meaning "not typed yet".

    QQ is allowed here and nowhere near a published recipe: these are drafts,
    and 32 of the 55 rums in the collection genuinely need Helen's call. What
    is not allowed is a fourth thing -- a plausible-looking style nobody
    declared, which is exactly how a typo mints a new category silently.
    """
    vocab = _vocab()
    allowed = set(vocab.get("rum_styles") or []) | set(vocab.get("rum_untyped") or [])
    assert allowed, "ingredients.yml declares no rum styles at all."

    found = _rum_generics()
    assert found, (
        "No rum-family ingredient carries a `generic` at all. The collection "
        "is rum-heavy, so this almost certainly means IS_RUM or the loader has "
        "stopped matching rather than that the data changed."
    )
    retired = set(vocab.get("retired_rum_styles") or {})
    unknown = sorted({
        f"{slug}: {name!r} -> {generic!r}"
        for slug, name, generic in found
        if generic != "QQ" and generic not in allowed and generic not in retired
    })
    assert not unknown, (
        "Undeclared rum style(s):\n  " + "\n  ".join(unknown)
        + f"\n\nDeclared: {sorted(allowed)}.\n"
          "Either it is a typo, or the style is real and belongs in "
          "_data/cocktails/ingredients.yml -- issue #314 is the spec."
    )


def test_glass_is_a_list():
    """`glass` became an ordered list on 2026-08-17 so a drink could name more
    than one acceptable serve. A leftover scalar still renders -- Liquid
    iterates a string's characters happily enough to produce nothing visible --
    so nothing else would catch one.
    """
    offenders = [
        f"{slug}: glass is a {type(fm['glass']).__name__}"
        for slug, fm in _load()
        if "glass" in fm and not isinstance(fm["glass"], list)
    ]
    assert not offenders, (
        "glass must be a list, first entry preferred:\n  " + "\n  ".join(offenders)
    )
