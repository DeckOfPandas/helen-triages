#!/usr/bin/env python3
"""Read-only audit: food ingredient names written more than one way for one thing.

    python3 scripts/audit_ingredient_names.py    # writes tmp/item-synonyms.md

Run after a big ingest. Each `item:` name (before the first comma or bracket)
is folded: accents, hyphens, plurals, word order, filler words, and a lexicon
of synonym phrases (fat-free = non-fat = 0% fat, US/UK names). A group is
names that fold alike but differ in a synonym, an order or a spelling; plurals
and filler alone do not make one. A ruling on a group becomes a house spelling
in tests/conftest.py (SPELLINGS) or a closed list in tests/test_style.py
(DECISIONS §5). Reads _food_recipes/ and _food_drafts/; writes only tmp/.
"""
import collections
import pathlib
import re
import unicodedata

SYNONYMS = [  # (pattern, canonical token): applied in order, on the folded name
    (r"\b(?:non ?fat|fat ?free|0 ?% ?(?:fat)?|zero ?fat|no ?fat|virtually fat ?free)\b", "FATFREE"),
    (r"\b(?:low ?fat|reduced ?fat|half ?fat|lighter|light|lite|semi ?skimmed)\b", "LOWFAT"),
    (r"\b(?:full ?fat|whole ?fat)\b", "FULLFAT"),
    (r"\bgreek ?style\b", "greek"),
    (r"\bplain (?=yoghurt|yogurt)", "natural "),
    (r"\byogurt\b", "yoghurt"),
    (r"\bheavy cream\b|\bwhipping cream\b(?=x)", "double cream"),
    (r"\bthickened cream\b", "double cream"),
    (r"\blight cream\b", "single cream"),
    (r"\ball ?purpose flour\b", "plain flour"),
    (r"\bself ?rising\b", "self raising"),
    (r"\bcilantro\b", "coriander"),
    (r"\b(?:scallions?|green onions?|salad onions?)\b", "spring onion"),
    (r"\beggplants?\b", "aubergine"),
    (r"\bzucchinis?\b", "courgette"),
    (r"\bcorn ?starch\b|\bcorn flour\b", "cornflour"),
    (r"\b(?:powdered|confectioners'?) sugar\b", "icing sugar"),
    (r"\bsuperfine sugar\b", "caster sugar"),
    (r"\bshrimps?\b(?! paste)", "prawn"),
    (r"\b(?:ground beef|minced beef|beef mince)\b", "beef mince"),
    (r"\b(?:ground pork|minced pork|pork mince)\b", "pork mince"),
    (r"\b(?:ground lamb|minced lamb|lamb mince)\b", "lamb mince"),
    (r"\b(?:red pepper flakes|crushed chill(?:i|ie)s?|crushed red pepper|chill?i flakes|dried chill?i flakes)\b", "chilli flakes"),
    (r"\bchili\b", "chilli"),
    (r"\bcanola\b", "rapeseed"),
    (r"\barugula\b", "rocket"),
    (r"\bgarbanzo(?: bean)?s?\b", "chickpea"),
    (r"\bbouillon cubes?\b", "stock cube"),
    (r"\bwhole ?wheat\b", "wholemeal"),
    (r"\bevoo\b", "extra-virgin olive oil"),
    (r"\b(?:maldon(?: sea)? salt|sea salt flakes|flaky (?:sea )?salt|flaked sea salt)\b", "flaked sea salt"),
    (r"\b(?:italian|flat ?leaf) parsley\b", "flat leaf parsley"),
    (r"\bbell peppers?\b", "pepper"),
    (r"\bbaking soda\b|\bbicarb(?:onate)?(?: of soda)?\b", "bicarbonate of soda"),
    (r"\bdemarara\b", "demerara"),
    (r"\bcaster ?sugar\b", "caster sugar"),
    (r"\bcreme fraiche\b", "creme fraiche"),
]
DROP = {"fresh", "freshly", "large", "small", "medium", "good", "quality", "good-quality",
        "organic", "free", "range", "chopped", "finely", "roughly", "sliced", "grated",
        "ripe", "about", "a", "of", "the", "or", "and", "some", "extra", "more", "to",
        "serve", "taste", "for", "plus", "pot", "tub", "pack", "jar", "tin", "can",
        "shop", "bought", "readymade", "ready", "made", "homemade"}


def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def singular(w):
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if re.search(r"(ch|sh|x|o)es$", w):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def name_of(item):
    s = re.split(r"[,(]| - | – ", item, maxsplit=1)[0].strip().strip("\"'")
    s = re.sub(r"^\[([^\]]*)\]\([^)]*\)", r"\1", s)
    return s


def key(name):
    s = fold(name).replace("-", " ")
    for pat, rep in SYNONYMS:
        s = re.sub(pat, rep, s)
    words = [singular(w) for w in re.findall(r"[a-z0-9%']+|[A-Z]+", s) if w not in DROP]
    words += [w for w in re.findall(r"\b[A-Z]{5,}\b", s)]
    return " ".join(sorted(set(words)))


uses = collections.defaultdict(collections.Counter)
where = collections.defaultdict(set)
for d, kind in (("_food_recipes", "P"), ("_food_drafts", "D")):
    for p in pathlib.Path(d).rglob("*.md"):
        for line in p.read_text(encoding="utf-8").splitlines():
            m = re.match(r'\s*(?:-\s+)?item:\s*"?(.*?)"?\s*$', line)
            if not m or "QQ" in line:
                continue
            n = name_of(m.group(1))
            if not n or len(n) > 60:
                continue
            k = key(n)
            if not k:
                continue
            uses[k][n.lower()] += 1
            where[(k, n.lower())].add(kind)

def light(name):
    """Folded, hyphens as spaces, singular, filler dropped, word order KEPT, no synonyms."""
    s = fold(name).replace("-", " ")
    return " ".join(singular(w) for w in re.findall(r"[a-z0-9%']+", s) if w not in DROP)


groups = []
for k, c in uses.items():
    if len({light(s) for s in c}) > 1:
        groups.append((sum(c.values()), k, c))
groups.sort(key=lambda g: -g[0])
out = [f"# Ingredient names written more than one way ({len(groups)} groups)", "",
       "P = published, D = draft", ""]
for total, k, c in groups:
    out.append(f"- **{k}** ({total}): " + "; ".join(
        f"`{s}` {n}{''.join(sorted(where[(k, s)]))}" for s, n in c.most_common()))
pathlib.Path("tmp").mkdir(exist_ok=True)
pathlib.Path("tmp/item-synonyms.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print(len(uses), "distinct folded names;", len(groups), "groups written more than one way")
