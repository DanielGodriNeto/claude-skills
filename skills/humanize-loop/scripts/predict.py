"""Local predictability check: how easy is each word for a small LM to guess? The text never leaves the machine.

Usage: python predict.py <file.txt>
       python predict.py --selftest
Setup: pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install transformers
       First run downloads Qwen3-0.6B-Base (~1.2 GB) from Hugging Face; only weights come in.

Signal: mean token log-prob under the model (higher = more predictable = reads as machine text).
Detectors like ZeroGPT lean on this; the style lint cannot see it. Calibrated 2026-10-14 on
pt-BR only (AUC 0.99 vs ZeroGPT > 10% on 51 texts); thresholds below are in-sample, so treat
"ok" as a strong hint, not proof. Not calibrated for other languages: use it to compare rounds.
"""
import re
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "Qwen/Qwen3-0.6B-Base"
DOC_MAX = -2.50   # whole-text mean log-prob above this: likely flagged (pt-BR)
PARA_MAX = -2.30  # any paragraph above this: that paragraph likely flagged (pt-BR)
MIN_PARA_WORDS = 30
MAX_TOKENS = 2048  # ponytail: longer texts are scored on their first 2048 tokens; paragraphs still all scored


def load():
    tok = AutoTokenizer.from_pretrained(MODEL)
    return tok, AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float32).eval()


@torch.inference_mode()
def mean_logprob(tok, model, text):
    ids = tok(text, return_tensors="pt").input_ids[:, :MAX_TOKENS]
    if ids.shape[1] < 2:
        return float("nan")
    lprobs = torch.log_softmax(model(ids).logits[0, :-1].float(), -1)
    return lprobs.gather(-1, ids[0, 1:, None]).mean().item()


def paragraphs(text):
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    if len(blocks) < 2:
        blocks = [b.strip() for b in text.split("\n") if b.strip()]
    return [b for b in blocks if len(b.split()) >= MIN_PARA_WORDS]


def verdict(doc, paras):
    hot = [(i, lp) for i, lp in enumerate(paras, 1) if lp > PARA_MAX]
    return doc <= DOC_MAX and not hot, hot


def selftest():
    ok, hot = verdict(-2.8, [-2.9, -2.6])
    assert ok and hot == []
    ok, hot = verdict(-2.4, [-2.9])
    assert not ok
    ok, hot = verdict(-2.7, [-2.9, -2.2])
    assert not ok and hot == [(2, -2.2)]
    assert paragraphs("curto\n\n" + "palavra " * 40) == ["palavra " * 39 + "palavra"]
    print("selftest ok")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:] == ["--selftest"]:
        return selftest()
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    text = open(sys.argv[1], encoding="utf-8").read()
    tok, model = load()
    doc = mean_logprob(tok, model, text)
    paras = [mean_logprob(tok, model, p) for p in paragraphs(text)]
    ok, hot = verdict(doc, paras)
    print(f"predictability: {doc:.2f} (pt-BR limit {DOC_MAX}) -> {'ok' if ok else 'likely flagged'}")
    for i, lp in hot:
        print(f"  paragraph {i}: {lp:.2f} > {PARA_MAX}, rewrite it with less expected word choices")


if __name__ == "__main__":
    main()
