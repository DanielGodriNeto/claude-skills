"""Stdlib-only style lint for AI-sounding prose (pt/en). Nothing leaves the machine.

Usage: python lint.py <file.txt>      prints a report
       python lint.py --selftest       runs the built-in check

Signals, not proof: each one is a pattern detectors and style guides associate
with LLM text (low sentence-length variance, stock phrases, repeated openers,
uniform paragraphs, em dashes). Use the flagged lines as rewrite targets.
"""
import re
import statistics
import sys
from collections import Counter

STOCK = [
    # pt-BR
    "além disso", "vale ressaltar", "vale destacar", "é importante ressaltar", "é importante destacar",
    "é fundamental", "é crucial", "é essencial", "desempenha um papel", "papel fundamental", "papel crucial",
    "no cenário atual", "no mundo atual", "nos dias de hoje", "cada vez mais", "em suma", "em resumo",
    "dessa forma", "desse modo", "nesse sentido", "nesse contexto", "por fim", "em última análise",
    "de forma eficiente", "de maneira eficaz", "robusto", "abrangente", "otimizar", "potencializar",
    "alavancar", "mergulhar", "explorar a fundo", "uma vez que", "garantindo", "permitindo",
    "não apenas", "mas também", "ampla gama", "diversos aspectos", "como um todo",
    # en
    "delve", "furthermore", "moreover", "additionally", "it is important to note", "it's worth noting",
    "plays a crucial role", "plays a vital role", "in today's", "ever-evolving", "landscape", "tapestry",
    "seamless", "robust", "leverage", "comprehensive", "in conclusion", "ultimately", "not only",
    "underscore", "pivotal", "foster", "intricate", "navigate the",
]

CV_FLAG = 0.35         # sentence-length coefficient of variation below this reads uniform
OPENER_FLAG = 0.15     # one opener word starting >15% of sentences
STOCK_PER_1K_FLAG = 6  # stock-phrase hits per 1000 words
DASH_PER_1K_FLAG = 3   # em dashes per 1000 words
PARA_CV_FLAG = 0.25    # paragraph-length CV below this reads uniform
ARTICLES = {"a", "o", "as", "os", "um", "uma", "the", "an"}  # too common to count as a repeated opener


def sentences(text):
    parts = re.split(r"(?<=[.!?…])\s+", re.sub(r"\s+", " ", text).strip())
    return [s for s in parts if len(words(s)) >= 3]


def words(text):
    return re.findall(r"[\wÀ-ÿ'-]+", text.lower())


def cv(values):
    if len(values) < 2 or statistics.mean(values) == 0:
        return 0.0
    return statistics.pstdev(values) / statistics.mean(values)


def stock_hits(text):
    low = text.lower()
    hits = Counter()
    for phrase in STOCK:
        n = len(re.findall(r"(?<![\wÀ-ÿ])" + re.escape(phrase) + r"(?![\wÀ-ÿ])", low))
        if n:
            hits[phrase] = n
    return hits


def analyze(text):
    sents = sentences(text)
    lens = [len(words(s)) for s in sents]
    total = len(words(text)) or 1
    paras = [p for p in re.split(r"\n\s*\n", text) if len(words(p)) >= 15]
    openers = Counter(words(s)[0] for s in sents if words(s) and words(s)[0] not in ARTICLES)
    top_opener, top_n = openers.most_common(1)[0] if openers else ("", 0)
    hits = stock_hits(text)
    return {
        "words": total,
        "sentences": len(sents),
        "sent_mean": statistics.mean(lens) if lens else 0.0,
        "sent_cv": cv(lens),
        "para_cv": cv([len(words(p)) for p in paras]) if len(paras) >= 3 else None,
        "top_opener": top_opener,
        "top_opener_share": top_n / len(sents) if sents else 0.0,
        "stock": hits,
        "stock_per_1k": sum(hits.values()) * 1000 / total,
        "dash_per_1k": text.count("—") * 1000 / total,
        "flagged": [s for s in sents if stock_hits(s)],
    }


def flags(r):
    out = []
    if r["sentences"] >= 5 and r["sent_cv"] < CV_FLAG:
        out.append(f"uniform sentence length (CV {r['sent_cv']:.2f} < {CV_FLAG}): mix short and long sentences")
    if r["sentences"] >= 7 and r["top_opener_share"] > OPENER_FLAG:
        out.append(f"'{r['top_opener']}' opens {r['top_opener_share']:.0%} of sentences")
    if r["stock_per_1k"] > STOCK_PER_1K_FLAG:
        out.append(f"stock phrases {r['stock_per_1k']:.1f}/1k words (> {STOCK_PER_1K_FLAG})")
    if r["dash_per_1k"] > DASH_PER_1K_FLAG:
        out.append(f"em dashes {r['dash_per_1k']:.1f}/1k words (> {DASH_PER_1K_FLAG})")
    if r["para_cv"] is not None and r["para_cv"] < PARA_CV_FLAG:
        out.append(f"uniform paragraph length (CV {r['para_cv']:.2f} < {PARA_CV_FLAG})")
    return out


def report(r):
    lines = [
        f"words {r['words']} | sentences {r['sentences']} | mean sentence {r['sent_mean']:.1f} words"
        f" | sentence CV {r['sent_cv']:.2f}",
        f"FLAGS ({len(flags(r))}):",
        *([f"  - {f}" for f in flags(r)] or ["  none"]),
        "stock phrases: " + (", ".join(f"{p} x{n}" for p, n in r["stock"].most_common()) or "none"),
        "sentences to rewrite:",
        *([f"  > {s}" for s in r["flagged"]] or ["  none"]),
    ]
    return "\n".join(lines)


def selftest():
    ai = ("Além disso, o sistema é robusto. Além disso, a base é abrangente. Além disso, o modelo é eficiente. "
          "Além disso, a consulta é otimizada. Além disso, o índice é essencial. Além disso, vale ressaltar o custo. "
          "Além disso, o projeto é crucial.")
    human = ("Testei a consulta ontem. Demorou. Depois de criar o índice na coluna de data, o tempo caiu de doze "
             "segundos para menos de um, o que me surpreendeu bastante porque a tabela nem é tão grande assim. "
             "Ainda falta medir com dados reais, e o professor pediu o plano de execução. Faço isso amanhã cedo.")
    a, h = analyze(ai), analyze(human)
    assert len(flags(a)) >= 2, flags(a)
    assert flags(h) == [], flags(h)
    assert a["stock"]["além disso"] == 7
    assert analyze("")["sentences"] == 0
    print("selftest ok")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:] == ["--selftest"]:
        return selftest()
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    with open(sys.argv[1], encoding="utf-8") as f:
        print(report(analyze(f.read())))


if __name__ == "__main__":
    main()
