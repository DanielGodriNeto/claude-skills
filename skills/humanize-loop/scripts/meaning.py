"""Stdlib-only meaning guard: did a rewrite drop or invent hard facts? Any language. Nothing leaves the machine.

Usage: python meaning.py <original.txt> <rewrite.txt>   exit 1 if something needs a look
       python meaning.py --selftest

Checks anchors that a rewrite must carry over unchanged: numbers, acronyms and code words
(SGBD, WHERE), hyphenated terms (B-Tree), names (capitalized words mid-sentence) and quotes.
Also flags anchors that appear only in the rewrite (invented specifics) and paragraphs that
shrank a lot (a dropped claim or conclusion). It cannot see a lost idea phrased in plain
words: that is the claim checklist's job (SKILL.md, step 2).
"""
import re
import sys

SHRINK_FLAG = 0.55  # rewrite paragraph shorter than this share of the original: check for a dropped claim
MIN_PARA_WORDS = 12


def sentence_starts(text):
    return {m.end() for m in re.finditer(r"(?:^|[.!?…:]\s+|\n)", text)}


def anchors(text):
    """Map lowercased anchor -> as written. Only words that a synonym swap has no reason to touch."""
    found = {}
    starts = sentence_starts(text)
    patterns = [
        r"\d+(?:[.,]\d+)*\s?%?",                 # numbers, years, percentages
        r"\b[^\W\d_]*[A-Z][^\W\d_]*-[^\W\d_]+\b",  # B-Tree, Full-Text
        r"\b[A-ZÀ-Ý]{2,}\b",                      # SGBD, WHERE, XXI
        r"[\"“«][^\"”»]{2,60}[\"”»]",              # quoted terms
    ]
    for pattern in patterns:
        for m in re.finditer(pattern, text):
            found.setdefault(m.group().strip().lower(), m.group().strip())
    for m in re.finditer(r"\b[A-ZÀ-Ý][^\W\d_]{2,}\b", text):  # names: capitalized, not sentence-initial
        if m.start() not in starts:
            found.setdefault(m.group().lower(), m.group())
    return found


def paragraphs(text):
    blocks = [b for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]
    if len(blocks) < 2:
        blocks = [b for b in text.split("\n") if b.strip()]
    return blocks


def shrunk(original, rewrite):
    """(index, ratio) for paragraphs that lost a lot of length; whole text if paragraph counts differ."""
    po, pr = paragraphs(original), paragraphs(rewrite)
    pairs = list(zip(po, pr)) if len(po) == len(pr) else [(original, rewrite)]
    out = []
    for i, (o, r) in enumerate(pairs, 1):
        no, nr = len(o.split()), len(r.split())
        if no >= MIN_PARA_WORDS and nr / no < SHRINK_FLAG:
            out.append((i, nr / no))
    return out


def compare(original, rewrite):
    ao, ar = anchors(original), anchors(rewrite)
    low = rewrite.lower()
    missing = [v for k, v in ao.items() if k not in low]
    added = [v for k, v in ar.items() if k not in original.lower()]
    return {"missing": missing, "added": added, "shrunk": shrunk(original, rewrite)}


def report(r):
    lines = []
    if r["missing"]:
        lines.append("missing from rewrite: " + ", ".join(r["missing"]))
    if r["added"]:
        lines.append("only in rewrite (invented?): " + ", ".join(r["added"]))
    for i, ratio in r["shrunk"]:
        lines.append(f"paragraph {i} shrank to {ratio:.0%} of the original: check for a dropped claim")
    return "\n".join(lines) or "anchors ok (still run the claim checklist)"


def selftest():
    sql = "O SGBD usa índices B-Tree em colunas do WHERE. Em 2024, 30% das consultas eram lentas."
    good = "Com índices B-Tree nas colunas do WHERE, o SGBD acha tudo mais rápido. Em 2024, 30% das consultas demoravam."
    bad = "Com índices nas colunas certas, o banco acha tudo mais rápido. Em 2023, boa parte das consultas demorava."
    assert compare(sql, good) == {"missing": [], "added": [], "shrunk": []}, compare(sql, good)
    r = compare(sql, bad)
    assert {"SGBD", "B-Tree", "WHERE", "2024", "30%"} <= set(r["missing"]), r
    assert "2023" in r["added"], r
    mill = 'Para Mill, a obra "Sobre a Liberdade" trata da tirania da maioria.'
    assert {"Mill", '"Sobre a Liberdade"'} <= set(compare(mill, "A obra trata da tirania da maioria.")["missing"])
    orig = ("Urban gardens help.\n\nIn conclusion, urban gardening represents a promising approach to building more "
            "resilient and sustainable cities, contributing to both environmental health and social cohesion.")
    cut = "Urban gardens help.\n\nA single garden can change how a whole block feels."
    assert [i for i, _ in compare(orig, cut)["shrunk"]] == [2], compare(orig, cut)
    assert compare("Os dados.", "")["shrunk"] == []  # below MIN_PARA_WORDS: no noise on tiny inputs
    print("selftest ok")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:] == ["--selftest"]:
        return selftest()
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    original, rewrite = (open(p, encoding="utf-8").read() for p in sys.argv[1:])
    r = compare(original, rewrite)
    print(report(r))
    sys.exit(1 if any(r.values()) else 0)


if __name__ == "__main__":
    main()
