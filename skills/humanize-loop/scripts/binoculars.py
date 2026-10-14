"""Local Binoculars score (Hans et al. 2024, arXiv:2401.12070). The text never leaves the machine.

Usage: python binoculars.py <file.txt>
Setup: pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install transformers
       First run downloads two small Qwen3 models (~2.4 GB) from Hugging Face; only weights come in.

score = log-perplexity under the performer / cross-perplexity between observer and performer.
Lower = more machine-like. Paper thresholds were tuned for Falcon-7B and do not carry over;
THRESHOLD below is provisional for this model pair (see SKILL.md), so compare rounds against each other.
"""
import re
import sys

import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer

OBSERVER = "Qwen/Qwen3-0.6B-Base"
PERFORMER = "Qwen/Qwen3-0.6B"
THRESHOLD = 0.90  # ponytail: provisional, calibrated on a handful of pt-BR samples; recalibrate per language
WINDOW = 1024     # tokens per forward pass; keeps CPU memory flat on long texts
MIN_PARA_TOKENS = 60


def load():
    tok = AutoTokenizer.from_pretrained(OBSERVER)
    obs = AutoModelForCausalLM.from_pretrained(OBSERVER, dtype=torch.float32).eval()
    perf = AutoModelForCausalLM.from_pretrained(PERFORMER, dtype=torch.float32).eval()
    assert obs.config.vocab_size == perf.config.vocab_size, "observer and performer must share a vocabulary"
    return tok, obs, perf


@torch.inference_mode()
def sums(ids, obs, perf):
    """Summed performer NLL and observer->performer cross-entropy over one token window."""
    o = obs(ids).logits[0, :-1].float()
    p = perf(ids).logits[0, :-1].float()
    nll = F.cross_entropy(p, ids[0, 1:], reduction="sum")
    xent = -(F.softmax(o, -1) * F.log_softmax(p, -1)).sum()
    return nll.item(), xent.item()


def score(text, tok, obs, perf):
    ids = tok(text, return_tensors="pt").input_ids
    if ids.shape[1] < 2:
        return None
    nll = xent = 0.0
    for start in range(0, ids.shape[1], WINDOW):
        window = ids[:, start:start + WINDOW]
        if window.shape[1] < 2:
            continue
        n, x = sums(window, obs, perf)
        nll, xent = nll + n, xent + x
    return nll / xent


def verdict(s):
    return "machine-like" if s < THRESHOLD else "human-like"


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    with open(sys.argv[1], encoding="utf-8") as f:
        text = f.read()
    tok, obs, perf = load()
    overall = score(text, tok, obs, perf)
    if overall is None:
        sys.exit("text too short to score")
    print(f"overall {overall:.4f} ({verdict(overall)}, threshold {THRESHOLD}, lower = more machine-like)")
    for i, para in enumerate(re.split(r"\n\s*\n", text), 1):
        if len(tok(para).input_ids) < MIN_PARA_TOKENS:
            continue
        s = score(para, tok, obs, perf)
        print(f"  para {i:>2}  {s:.4f}  {verdict(s):<12}  {para.strip()[:70]}")


if __name__ == "__main__":
    main()
