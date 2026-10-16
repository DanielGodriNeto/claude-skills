"""Local meaning check: does the rewrite still say each sentence of the original? ~100 languages. Nothing leaves the machine.

Usage: python entail.py <original.txt> <rewrite.txt>   exit 1 if any sentence scores low
       python entail.py --selftest                      (stdlib only, no model needed)
Setup: pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install transformers sentencepiece protobuf
       First run downloads mDeBERTa-v3 multilingual NLI (~560 MB, pinned commit, safetensors only) from
       Hugging Face; only weights come in.

Signal: for each original sentence, the highest entailment probability over 2-paragraph windows of the
rewrite (windows over 384 tokens are split into overlapping sentence runs, so nothing is truncated).
A low score means "the rewrite may no longer say this": read that sentence against the claim
list. Tested 2026-10-15 (en, pt): caught a dropped idea phrased in plain words ("burnout") and claims
made weaker or stronger; missed a cut conclusion (meaning.py catches that; 2-sentence windows also caught it but tripled false
alarms on long texts) and one dropped qualifier (only the claim list catches those);
about one false alarm per faithful text, mostly idioms ("here to stay" vs "isn't going anywhere").
So it flags, it never decides. Each sentence is matched only against nearby rewrite paragraphs and
untouched sentences are skipped: ~40 s per 170 words on CPU, linear in length, much less when few sentences changed.
"""
import re
import sys

MODEL = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
REVISION = "b5113eb38ab63efdd7f280f8c144ea8b13f978ce"  # pinned commit: a new upload is never pulled silently
LOW = 0.5          # entailment below this: sentence may be lost or changed
MIN_SENT_WORDS = 4
PREMISE_TOKENS = 384  # 512 model limit minus room for the hypothesis sentence
REACH = 2             # compare each sentence only with rewrite paragraphs this close to its own position


def paragraphs(text):
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]
    if len(blocks) < 2:
        blocks = [b.strip() for b in text.split("\n") if b.strip()]
    return blocks


def windows(text):
    """(start paragraph, text) for pairs of adjacent paragraphs, so a claim moved to the next paragraph still counts."""
    paras = paragraphs(text)
    return [(i, " ".join(paras[i:i + 2])) for i in range(max(1, len(paras) - 1))]


def fit(tagged, length, budget=PREMISE_TOKENS):
    """Split windows longer than the model can read into overlapping sentence runs, so nothing is truncated."""
    out = []
    for k, w in tagged:
        if length(w) <= budget:
            out.append((k, w))
            continue
        chunk = []
        for s in re.split(r"(?<=[.!?…])\s+|(?<=[。！？])", w):  # \s+ so "3.5" is not split
            if chunk and length(" ".join(chunk + [s])) > budget:
                out.append((k, " ".join(chunk)))
                chunk = chunk[-1:]  # overlap one sentence: a claim spanning the cut is still seen whole
            chunk.append(s)
        out.append((k, " ".join(c for c in chunk if c)))
    return out


def nearby(tagged, para_index, n_orig, n_rewrite, reach=REACH):
    """Windows within `reach` paragraphs of where this original paragraph should land in the rewrite.
    Keeps long documents linear in cost; claims moved further than that show up as flags."""
    if n_orig < 2 or n_rewrite < 2:
        return [w for _, w in tagged]
    target = round(para_index * (n_rewrite - 1) / (n_orig - 1))
    return [w for k, w in tagged if target - reach <= k <= target + reach - 1] or [w for _, w in tagged]


def norm(text):
    return re.sub(r"\W+", " ", text.lower()).strip()


def unchanged(rewrite):
    """Whole rewrite sentences, normalized: a substring match would skip "X." rewritten as "X, but not anymore."."""
    return {norm(s) for s in sentences(rewrite)}


def sentences(text):
    parts = re.split(r"(?<=[.!?…])\s+|(?<=[。！？])", re.sub(r"\s+", " ", text).strip())
    return [s for s in parts if len(s.split()) >= MIN_SENT_WORDS or re.search(r"[぀-鿿]{8,}", s)]


def low_scores(scored):
    return [(p, s) for p, s in scored if p < LOW]


def load():
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL, revision=REVISION, use_safetensors=True).eval()  # never pickle
    return tok, model, model.config.label2id["entailment"]


def entailment(tok, model, ent_id, premises, hypothesis):
    import torch
    with torch.inference_mode():
        enc = tok(premises, [hypothesis] * len(premises), truncation="only_first", max_length=512,
                  padding=True, return_tensors="pt")
        return torch.softmax(model(**enc).logits, -1)[:, ent_id].max().item()


def selftest():
    text = "Primeiro parágrafo aqui.\n\nSegundo parágrafo aqui.\n\nTerceiro parágrafo aqui."
    assert windows(text) == [(0, "Primeiro parágrafo aqui. Segundo parágrafo aqui."),
                             (1, "Segundo parágrafo aqui. Terceiro parágrafo aqui.")], windows(text)
    assert windows("Só um parágrafo.") == [(0, "Só um parágrafo.")]
    assert sentences("Remote work is here to stay. Ok then. It changed how teams run.") == [
        "Remote work is here to stay.", "It changed how teams run."]
    assert len(sentences("远程工作已经彻底改变了组织的运作方式。远程工作将会长期存在下去。")) == 2
    words = lambda t: len(t.split())
    assert fit([(0, "a b. c d.")], words, budget=10) == [(0, "a b. c d.")]
    long_w = "Um dois três. Quatro cinco seis. Sete oito nove."
    assert fit([(3, long_w)], words, budget=6) == [(3, "Um dois três. Quatro cinco seis."), (3, "Quatro cinco seis. Sete oito nove.")]
    tagged = [(k, f"w{k}") for k in range(19)]  # 20-paragraph rewrite
    assert nearby(tagged, 0, 20, 20) == ["w0", "w1"]
    assert nearby(tagged, 10, 20, 20) == ["w8", "w9", "w10", "w11"]  # paragraphs 8-12 around position 10
    assert nearby(tagged, 3, 1, 20) == [w for _, w in tagged]  # one-paragraph original: compare with everything
    assert norm("Já, é  ISSO!") == norm("já é isso")
    same = unchanged("It changed how teams run, but not anymore. Remote work is here to stay.")
    assert norm("It changed how teams run.") not in same  # extended sentence must reach the model
    assert norm("Remote work is HERE to stay!") in same
    assert low_scores([(0.9, "a"), (0.2, "b"), (0.5, "c")]) == [(0.2, "b")]
    print("selftest ok")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:] == ["--selftest"]:
        return selftest()
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    original, rewrite = (open(p, encoding="utf-8").read() for p in sys.argv[1:])
    tok, model, ent_id = load()
    tagged = fit(windows(rewrite), lambda t: len(tok(t).input_ids))
    paras_o, n_rewrite, same = paragraphs(original), len(paragraphs(rewrite)), unchanged(rewrite)
    scored = []
    for i, para in enumerate(paras_o):
        for s in sentences(para):
            if norm(s) in same:  # untouched sentence: nothing to check, skip the model
                scored.append((1.0, s))
                continue
            premises = nearby(tagged, i, len(paras_o), n_rewrite)
            scored.append((entailment(tok, model, ent_id, premises, s), s))
    low = low_scores(scored)
    print(f"{len(scored) - len(low)}/{len(scored)} original sentences still entailed (limit {LOW})")
    for p, s in low:
        print(f"  {p:.2f}  {s}")
    if low:
        print("check these against the claim list: lost, weakened, or just reworded?")
    sys.exit(1 if low else 0)


if __name__ == "__main__":
    main()
