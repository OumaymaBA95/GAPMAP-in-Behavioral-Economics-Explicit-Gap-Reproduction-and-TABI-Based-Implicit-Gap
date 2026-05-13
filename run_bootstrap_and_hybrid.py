#!/usr/bin/env python3
"""Bootstrap confidence intervals on the headline P/R/F1 (Table 1) and a paired
hybrid-merge ablation on the local Ollama predictions.

Both pieces are computed from existing artifacts (no API calls, no Ollama calls):
  - predictions_{gpt_4o, gpt4o_mini, ollama}.csv  (filter ON, hybrid OFF)
  - gold_standard.csv

Bootstrap procedure: resample the 93 gold chunk_ids with replacement, recompute
TP/FP/FN by summing the per-chunk counts of the resampled chunks, then derive
P/R/F1. We do this B=1000 times and report 2.5/50/97.5 percentiles per metric.

Hybrid ablation: the existing predictions_ollama.csv is filter ON, hybrid OFF.
For 'hybrid ON' we union those predictions per chunk with rule_based_extract()
applied to the same chunk text and dedupe. Both configurations are evaluated on
the same 93 gold chunks (paired), so the delta isolates the hybrid-merge knob.

Outputs:
  Part2_Output/bootstrap_ci.txt
  Part2_Output/ablation_ollama_hybrid.txt
"""
import json
from pathlib import Path
import random

import numpy as np
import pandas as pd
from rouge_score import rouge_scorer
from tqdm import tqdm

import run_part2 as rp2

OUT = Path("Part2_Output")
B = int(__import__("os").environ.get("BOOTSTRAP_B", "1000"))
SEED = 7
THRESHOLD = 0.55


def load_preds_cell(x):
    if isinstance(x, str):
        try:
            return json.loads(x)
        except Exception:
            return []
    return x if isinstance(x, list) else []


def per_chunk_counts(preds_records, gold_by_chunk, gold_ids):
    """Return dict chunk_id -> (tp, fp, fn) restricted to gold_ids."""
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    counts = {}
    for p in preds_records:
        cid = int(p["chunk_id"])
        if cid not in gold_ids:
            continue
        preds = load_preds_cell(p["predictions"])
        gold_list = [g.strip() for g in str(gold_by_chunk.get(cid, "")).split(";") if g.strip()]
        tp = fp = 0
        matched = set()
        for pred in preds:
            best_idx, best_f1 = None, 0.0
            for i, gold in enumerate(gold_list):
                f1 = scorer.score(gold, pred)["rougeL"].fmeasure
                if f1 >= THRESHOLD and f1 > best_f1:
                    best_idx, best_f1 = i, f1
            if best_idx is not None:
                matched.add(best_idx)
                tp += 1
            else:
                fp += 1
        fn = len(gold_list) - len(matched)
        counts[cid] = (tp, fp, fn)
    for cid in gold_ids:
        counts.setdefault(cid, (0, 0, len([g for g in str(gold_by_chunk.get(cid, "")).split(";") if g.strip()])))
    return counts


def aggregate(counts_dict, chunk_ids):
    tp = fp = fn = 0
    for cid in chunk_ids:
        a, b, c = counts_dict[cid]
        tp += a; fp += b; fn += c
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f1, tp, fp, fn


def bootstrap_ci(counts_dict, gold_ids, B=B, seed=SEED):
    rng = random.Random(seed)
    ids_list = sorted(gold_ids)
    n = len(ids_list)
    samples = np.zeros((B, 3))
    for b in range(B):
        sampled = [ids_list[rng.randrange(n)] for _ in range(n)]
        p, r, f1, *_ = aggregate(counts_dict, sampled)
        samples[b] = (p, r, f1)
    point = aggregate(counts_dict, ids_list)
    return {
        "point": point[:3],
        "tp_fp_fn": point[3:],
        "p_lo": np.percentile(samples[:, 0], 2.5),
        "p_hi": np.percentile(samples[:, 0], 97.5),
        "r_lo": np.percentile(samples[:, 1], 2.5),
        "r_hi": np.percentile(samples[:, 1], 97.5),
        "f1_lo": np.percentile(samples[:, 2], 2.5),
        "f1_hi": np.percentile(samples[:, 2], 97.5),
        "samples": samples,
    }


def fmt(ci, label):
    p, r, f1 = ci["point"]
    return (
        f"{label:<25} P={p:.4f} [{ci['p_lo']:.4f}, {ci['p_hi']:.4f}]  "
        f"R={r:.4f} [{ci['r_lo']:.4f}, {ci['r_hi']:.4f}]  "
        f"F1={f1:.4f} [{ci['f1_lo']:.4f}, {ci['f1_hi']:.4f}]"
    )


def main():
    gold_df = pd.read_csv(OUT / "gold_standard.csv")
    gold_df = gold_df[gold_df["gold_gap_sentences"].notna() & (gold_df["gold_gap_sentences"].astype(str).str.strip() != "")]
    gold_by_chunk = gold_df.set_index("chunk_id")["gold_gap_sentences"].to_dict()
    gold_ids = set(int(c) for c in gold_df["chunk_id"])
    print(f"Gold chunks: {len(gold_ids)}")

    files = {
        "GPT-4o":          OUT / "predictions_gpt_4o.csv",
        "GPT-4o-mini":     OUT / "predictions_gpt4o_mini.csv",
        "Ollama (Llama 3.2)": OUT / "predictions_ollama.csv",
    }

    print("Computing per-chunk (TP, FP, FN) for each model...")
    per_model_counts = {}
    for label, path in files.items():
        recs = pd.read_csv(path).to_dict("records")
        per_model_counts[label] = per_chunk_counts(recs, gold_by_chunk, gold_ids)

    print(f"Bootstrap {B} resamples per model...")
    cis = {label: bootstrap_ci(per_model_counts[label], gold_ids) for label in files}

    out_lines = [
        f"=== Bootstrap 95% CIs on Table 1 (B={B} chunk-level resamples, seed={SEED}, ROUGE-L 0.55) ===\n",
        f"  Gold chunks N={len(gold_ids)} (resampled with replacement)\n\n",
    ]
    for label in files:
        out_lines.append(fmt(cis[label], label) + "\n")

    out_lines.append("\n--- Significance: probability that GPT-4o F1 > X model F1 across paired resamples ---\n")
    rng = random.Random(SEED)
    ids_list = sorted(gold_ids)
    n = len(ids_list)
    paired = {label: np.zeros(B) for label in files}
    for b in range(B):
        sampled = [ids_list[rng.randrange(n)] for _ in range(n)]
        for label in files:
            _, _, f1, *_ = aggregate(per_model_counts[label], sampled)
            paired[label][b] = f1
    for other in ["GPT-4o-mini", "Ollama (Llama 3.2)"]:
        wins = (paired["GPT-4o"] > paired[other]).mean()
        diffs = paired["GPT-4o"] - paired[other]
        out_lines.append(
            f"  GPT-4o > {other:<22}: P(GPT-4o wins)={wins:.4f}  "
            f"\u0394F1 mean={diffs.mean():.4f}  95% CI [{np.percentile(diffs, 2.5):.4f}, {np.percentile(diffs, 97.5):.4f}]\n"
        )

    txt = "".join(out_lines)
    print("\n" + txt)
    (OUT / "bootstrap_ci.txt").write_text(txt)
    print(f"Wrote {OUT / 'bootstrap_ci.txt'}")

    print("\n=== Hybrid-merge ablation on Ollama (paired, free) ===")
    print("Re-loading articles + chunking to recover chunk text for hybrid merge...")
    articles = rp2.load_articles()
    chunks = rp2.chunk_all(articles)
    chunk_text_by_id = {c["chunk_id"]: c["text"] for c in chunks if c["chunk_id"] in gold_ids}

    ollama_recs = pd.read_csv(OUT / "predictions_ollama.csv").to_dict("records")
    hybrid_recs = []
    for rec in ollama_recs:
        cid = int(rec["chunk_id"])
        if cid not in gold_ids:
            hybrid_recs.append(rec)
            continue
        llm_preds = load_preds_cell(rec["predictions"])
        rule_preds = rp2.rule_based_extract(chunk_text_by_id.get(cid, ""))
        merged = list(dict.fromkeys([s.strip() for s in (llm_preds + rule_preds) if s and str(s).strip()]))
        hybrid_recs.append({"chunk_id": cid, "predictions": json.dumps(merged)})

    base_counts   = per_chunk_counts(ollama_recs, gold_by_chunk, gold_ids)
    hybrid_counts = per_chunk_counts(hybrid_recs, gold_by_chunk, gold_ids)
    base_pt   = aggregate(base_counts,   sorted(gold_ids))
    hybrid_pt = aggregate(hybrid_counts, sorted(gold_ids))
    base_ci   = bootstrap_ci(base_counts,   gold_ids)
    hybrid_ci = bootstrap_ci(hybrid_counts, gold_ids)

    diffs_p = bootstrap_ci(hybrid_counts, gold_ids)["samples"][:, 0] - bootstrap_ci(base_counts, gold_ids, seed=SEED)["samples"][:, 0]

    rng = random.Random(SEED)
    paired_diff = np.zeros((B, 3))
    for b in range(B):
        sampled = [ids_list[rng.randrange(n)] for _ in range(n)]
        bP, bR, bF, *_ = aggregate(base_counts, sampled)
        hP, hR, hF, *_ = aggregate(hybrid_counts, sampled)
        paired_diff[b] = (hP - bP, hR - bR, hF - bF)

    h_lines = [
        f"=== Ollama hybrid-merge ablation (93 gold chunks, paired, ROUGE-L {THRESHOLD}) ===\n\n",
        f"{'Config':<35} {'TP':>4} {'FP':>4} {'FN':>4} {'Prec':>8} {'Rec':>8} {'F1':>8}\n",
        "-" * 80 + "\n",
        f"{'hybrid OFF (filter ON, baseline)':<35} {base_pt[3]:>4d} {base_pt[4]:>4d} {base_pt[5]:>4d} "
        f"{base_pt[0]:>8.4f} {base_pt[1]:>8.4f} {base_pt[2]:>8.4f}\n",
        f"{'hybrid ON  (filter ON + rule_based)':<35} {hybrid_pt[3]:>4d} {hybrid_pt[4]:>4d} {hybrid_pt[5]:>4d} "
        f"{hybrid_pt[0]:>8.4f} {hybrid_pt[1]:>8.4f} {hybrid_pt[2]:>8.4f}\n",
        "\n",
        f"Paired bootstrap (B={B}) hybrid - baseline:\n",
        f"  \u0394P  mean={paired_diff[:, 0].mean():+.4f}  95% CI [{np.percentile(paired_diff[:, 0], 2.5):+.4f}, {np.percentile(paired_diff[:, 0], 97.5):+.4f}]\n",
        f"  \u0394R  mean={paired_diff[:, 1].mean():+.4f}  95% CI [{np.percentile(paired_diff[:, 1], 2.5):+.4f}, {np.percentile(paired_diff[:, 1], 97.5):+.4f}]\n",
        f"  \u0394F1 mean={paired_diff[:, 2].mean():+.4f}  95% CI [{np.percentile(paired_diff[:, 2], 2.5):+.4f}, {np.percentile(paired_diff[:, 2], 97.5):+.4f}]\n",
        f"\nIndependent (non-paired) bootstrap CIs for each row:\n",
        fmt(base_ci,   "  hybrid OFF") + "\n",
        fmt(hybrid_ci, "  hybrid ON ") + "\n",
    ]
    txt2 = "".join(h_lines)
    print("\n" + txt2)
    (OUT / "ablation_ollama_hybrid.txt").write_text(txt2)
    print(f"Wrote {OUT / 'ablation_ollama_hybrid.txt'}")


if __name__ == "__main__":
    main()
