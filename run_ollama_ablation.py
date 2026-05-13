#!/usr/bin/env python3
"""One-off ablation: run Ollama Llama 3.2 with --no-post-filter on a random
subset of gold chunks and report P/R/F1 vs the same raw output with the
post-filter applied. Designed to be tractable on CPU-only Macs.

Tunables (env vars):
  OLLAMA_ABLATION_N=20        # how many gold chunks to sample
  OLLAMA_ABLATION_SEED=7      # sampling seed
  OLLAMA_ABLATION_MAXCHARS=3500   # prompt truncation
  OLLAMA_ABLATION_TIMEOUT=600     # per-chunk timeout in seconds

Usage:
  cd "/Users/momoba/Desktop/Advanced ML Project "
  .venv/bin/python run_ollama_ablation.py

Writes:
  Part2_Output/predictions_ollama_nofilter_goldonly.csv
  Part2_Output/ablation_ollama_postfilter.txt
"""
import json
import os
import random
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd
from tqdm import tqdm

import run_part2 as rp2

OUT = Path("Part2_Output")
OUT.mkdir(exist_ok=True)

N        = int(os.environ.get("OLLAMA_ABLATION_N", "20"))
SEED     = int(os.environ.get("OLLAMA_ABLATION_SEED", "7"))
MAXCHARS = int(os.environ.get("OLLAMA_ABLATION_MAXCHARS", "3500"))
TIMEOUT  = int(os.environ.get("OLLAMA_ABLATION_TIMEOUT", "600"))
MODEL    = os.environ.get("OLLAMA_MODEL", "llama3.2")
HOST     = os.environ.get("OLLAMA_HOST", "http://localhost:11434")


def extract_one(chunk_text):
    """Single Ollama call with our own (longer) timeout and shorter prompt.
    Returns list[str] of predicted sentences (raw, no post-filter)."""
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": rp2.EXTRACT_SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract explicit knowledge gap statements:\n\n{chunk_text[:MAXCHARS]}"},
        ],
        "stream": False,
    }).encode()
    req = urllib.request.Request(f"{HOST}/api/chat", data=payload, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        out = json.loads(r.read().decode())
    content = (out.get("message", {}).get("content") or "").strip()
    if content.upper() == "NONE":
        return []
    return [l.strip() for l in content.split("\n") if l.strip() and l.strip().upper() != "NONE"]


def main():
    gold_path = OUT / "gold_standard.csv"
    gold_df = pd.read_csv(gold_path)
    gold_df = gold_df[gold_df["gold_gap_sentences"].notna() & (gold_df["gold_gap_sentences"].astype(str).str.strip() != "")]
    gold_ids_all = set(gold_df["chunk_id"].astype(int))
    print(f"Gold chunks total: {len(gold_ids_all)}")

    print("Loading PDFs and chunking (this re-creates chunk_id -> text mapping)...")
    articles = rp2.load_articles()
    chunks = rp2.chunk_all(articles)
    chunks_in_gold = [c for c in chunks if c["chunk_id"] in gold_ids_all]
    rng = random.Random(SEED)
    chunks_to_run = rng.sample(chunks_in_gold, min(N, len(chunks_in_gold)))
    chunks_to_run.sort(key=lambda c: c["chunk_id"])
    sampled_ids = {c["chunk_id"] for c in chunks_to_run}
    print(f"Sampling {len(chunks_to_run)} of {len(chunks_in_gold)} gold chunks (seed={SEED}, maxchars={MAXCHARS}, timeout={TIMEOUT}s)")

    raw_preds = []
    failures = 0
    for c in tqdm(chunks_to_run, desc=f"Ollama({MODEL}) no-filter"):
        try:
            t0 = time.time()
            lines = extract_one(c["text"])
            elapsed = time.time() - t0
            raw_preds.append({"chunk_id": c["chunk_id"], "predictions": json.dumps(lines)})
            tqdm.write(f"  chunk {c['chunk_id']}: {len(lines)} preds in {elapsed:.1f}s")
        except Exception as e:
            failures += 1
            raw_preds.append({"chunk_id": c["chunk_id"], "predictions": "[]"})
            tqdm.write(f"  chunk {c['chunk_id']}: FAIL ({e})")
    raw_preds_sorted = sorted(raw_preds, key=lambda x: x["chunk_id"])
    raw_path = OUT / "predictions_ollama_nofilter_goldonly.csv"
    pd.DataFrame(raw_preds_sorted).to_csv(raw_path, index=False)
    print(f"Wrote {raw_path}  (failures={failures}/{len(chunks_to_run)})")
    if failures == len(chunks_to_run):
        print("\nALL chunks failed; metrics would be all-zero. Exiting before writing ablation.")
        return

    from rouge_score import rouge_scorer

    gold_by_chunk = gold_df.set_index("chunk_id")["gold_gap_sentences"].to_dict()

    def load_preds(x):
        if isinstance(x, str):
            try:
                return json.loads(x)
            except Exception:
                return []
        return x if isinstance(x, list) else []

    def evaluate(preds_records, label):
        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
        threshold = 0.55
        tp = fp = fn = 0
        for p in preds_records:
            cid = p["chunk_id"]
            if cid not in sampled_ids:
                continue
            preds = load_preds(p["predictions"])
            gold_list = [g.strip() for g in str(gold_by_chunk.get(cid, "")).split(";") if g.strip()]
            matched = set()
            for pred in preds:
                best_idx, best_f1 = None, 0.0
                for i, gold in enumerate(gold_list):
                    f1 = scorer.score(gold, pred)["rougeL"].fmeasure
                    if f1 >= threshold and f1 > best_f1:
                        best_idx, best_f1 = i, f1
                if best_idx is not None:
                    matched.add(best_idx)
                    tp += 1
                else:
                    fp += 1
            fn += len(gold_list) - len(matched)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        return label, tp, fp, fn, prec, rec, f1

    results = []
    results.append(evaluate(raw_preds_sorted, "Ollama, post-filter OFF (raw)"))

    filtered = []
    for p in raw_preds_sorted:
        kept = rp2.filter_predictions(load_preds(p["predictions"]), use_filter=True)
        filtered.append({"chunk_id": p["chunk_id"], "predictions": json.dumps(kept)})
    results.append(evaluate(filtered, "Ollama, post-filter ON (same raw)"))

    on_disk = pd.read_csv(OUT / "predictions_ollama.csv").to_dict("records")
    results.append(evaluate(on_disk, "On-disk predictions_ollama.csv (ref)"))

    out_lines = [f"=== Ollama post-filter ablation ({len(chunks_to_run)} sampled gold chunks, ROUGE-L 0.55) ===\n"]
    out_lines.append(f"  N={len(chunks_to_run)}  seed={SEED}  maxchars={MAXCHARS}  timeout={TIMEOUT}s  failures={failures}\n\n")
    out_lines.append(f"{'Config':<45} {'TP':>4} {'FP':>4} {'FN':>4} {'Prec':>8} {'Rec':>8} {'F1':>8}\n")
    out_lines.append("-" * 90 + "\n")
    for label, tp, fp, fn, p, r, f in results:
        out_lines.append(f"{label:<45} {tp:>4} {fp:>4} {fn:>4} {p:>8.4f} {r:>8.4f} {f:>8.4f}\n")
    txt = "".join(out_lines)
    print(txt)
    (OUT / "ablation_ollama_postfilter.txt").write_text(txt)
    print(f"Wrote {OUT / 'ablation_ollama_postfilter.txt'}")


if __name__ == "__main__":
    main()
