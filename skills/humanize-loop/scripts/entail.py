"""Local meaning check: does the rewrite still say each sentence of the original? ~100 languages. Nothing leaves the machine.

Usage: python entail.py <original.txt> <rewrite.txt>   exit 1 if any sentence scores low
       python entail.py --selftest                      (stdlib only, no model needed)
Setup: pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install transformers sentencepiece protobuf
       First run downloads mDeBERTa-v3 multilingual NLI (~560 MB) from Hugging Face; only weights come in.

Signal: for each original sentence, the highest entailment probability over 2-paragraph windows of the
rewrite. A low score means "the rewrite may no longer say this": read that sentence against the claim
list. Tested 2026-10-15 (en, pt): caught a dropped idea phrased in plain words ("burnout") and claims
made weaker or stronger; missed a cut conclusion (meaning.py catches that) and one dropped qualifier;
about one false alarm per faithful text, mostly idioms ("here to stay" vs "isn't going anywhere").
So it flags, it never decides. Slow on CPU: ~40 s per 170 words, ~4 min per 400.
"""
import re
import sys

MODEL = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
LOW = 0.5          # entailment below this: sentence may be lost or changed
MIN_SENT_WORDS = 4


def paragraphs(text):
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]
    if len(blocks) < 2:
        blocks = [b.strip() for b in text.split("\n") if b.strip()]
    return blocks


def windows(text):
    """Pairs of adjacent paragraphs, so a claim moved to the next paragraph still counts."""
    paras = paragraphs(text)
    return [" ".join(paras[i:i + 2]) for i in range(max(1, len(paras) - 1))]


def sentences(text):
    parts = re.split(r"(?<=[.!?…])\s+|(?<=[。！？])", re.sub(r"\s+", " ", text).strip())
    return [s for s in parts if len(s.split()) >= MIN_SENT_WORDS or re.search(r"[぀-鿿]{8,}", s)]


def low_scores(scored):
    return [(p, s) for p, s in scored if p < LOW]


def load():
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL, use_safetensors=True).eval()  # never pickle
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
    premises = windows(rewrite)
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
