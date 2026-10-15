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
So it flags, it never decides. Slow on CPU: ~40 s per 170 words, ~4 min per 400.
"""
import re
import sys

MODEL = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
REVISION = "b5113eb38ab63efdd7f280f8c144ea8b13f978ce"  # pinned commit: a new upload is never pulled silently
LOW = 0.5          # entailment below this: sentence may be lost or changed
MIN_SENT_WORDS = 4
PREMISE_TOKENS = 384  # 512 model limit minus room for the hypothesis sentence


def paragraphs(text):
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]
    if len(blocks) < 2:
        blocks = [b.strip() for b in text.split("\n") if b.strip()]
    return blocks


def windows(text):
    """Pairs of adjacent paragraphs, so a claim moved to the next paragraph still counts."""
    paras = paragraphs(text)
    return [" ".join(paras[i:i + 2]) for i in range(max(1, len(paras) - 1))]


def fit(windows, length, budget=PREMISE_TOKENS):
    """Split windows longer than the model can read into overlapping sentence runs, so nothing is truncated."""
    out = []
    for w in windows:
        if length(w) <= budget:
            out.append(w)
            continue
        chunk = []
        for s in re.split(r"(?<=[.!?…])\s+|(?<=[。！？])", w):  # \s+ so "3.5" is not split
            if chunk and length(" ".join(chunk + [s])) > budget:
                out.append(" ".join(chunk))
                chunk = chunk[-1:]  # overlap one sentence: a claim spanning the cut is still seen whole
            chunk.append(s)
        out.append(" ".join(c for c in chunk if c))
    return out


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
    assert windows(text) == ["Primeiro parágrafo aqui. Segundo parágrafo aqui.",
                             "Segundo parágrafo aqui. Terceiro parágrafo aqui."], windows(text)
    assert windows("Só um parágrafo.") == ["Só um parágrafo."]
    assert sentences("Remote work is here to stay. Ok then. It changed how teams run.") == [
        "Remote work is here to stay.", "It changed how teams run."]
    assert len(sentences("远程工作已经彻底改变了组织的运作方式。远程工作将会长期存在下去。")) == 2
    words = lambda t: len(t.split())
    assert fit(["a b. c d."], words, budget=10) == ["a b. c d."]
    long_w = "Um dois três. Quatro cinco seis. Sete oito nove."
    assert fit([long_w], words, budget=6) == ["Um dois três. Quatro cinco seis.", "Quatro cinco seis. Sete oito nove."], fit([long_w], words, budget=6)
    assert all(words(c) <= 6 for c in fit([long_w], words, budget=6))
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
    premises = fit(windows(rewrite), lambda t: len(tok(t).input_ids))
    scored = [(entailment(tok, model, ent_id, premises, s), s) for s in sentences(original)]
    low = low_scores(scored)
    print(f"{len(scored) - len(low)}/{len(scored)} original sentences still entailed (limit {LOW})")
    for p, s in low:
        print(f"  {p:.2f}  {s}")
    if low:
        print("check these against the claim list: lost, weakened, or just reworded?")
    sys.exit(1 if low else 0)


if __name__ == "__main__":
    main()
