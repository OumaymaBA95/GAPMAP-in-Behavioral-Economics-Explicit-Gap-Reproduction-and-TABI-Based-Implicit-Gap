#!/usr/bin/env python3
"""Rule-based-only baseline + bootstrap distribution figure + FP pattern figure.

Three artifacts produced from existing CSVs (no API, no Ollama, no GPU):

  Part2_Output/baseline_rule_only.txt        rule-based extractor with no LLM,
                                             evaluated on the same 93 gold chunks
                                             with the same ROUGE-L 0.55 + 1,000-sample
                                             chunk-level bootstrap CI as Table 1.

  Part2_Output/bootstrap_samples.csv         1,000 (P, R, F1) tuples per model
                                             AND per the rule-based baseline -- the
                                             raw data behind Table 1's CI column;
                                             used to plot the F1 distribution figure.

  Part2_Output/fp_patterns.csv               top-K leading-5-word stems among each
                                             model's false positives, ranked by count;
                                             used to plot the FP pattern bar chart.

  Final_Paper/figures/bootstrap_f1.pdf       F1 distribution per model + baseline.
  Final_Paper/figures/fp_patterns.pdf        Top-K FP patterns per model.

This script reuses the per-chunk scoring and bootstrap utilities from
``run_bootstrap_and_hybrid.py`` so the baseline is comparable to Table 1 in
exactly the same way the three LLM rows are.
"""
from __future__ import annotations

import json
import os
import random
import re
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import run_part2 as rp2
from run_bootstrap_and_hybrid import (
    aggregate,
    bootstrap_ci,
    load_preds_cell,
    per_chunk_counts,
)

OUT = Path("Part2_Output")
FIG_DIR = Path("Final_Paper/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

B = int(os.environ.get("BOOTSTRAP_B", "1000"))
SEED = 7
THRESHOLD = 0.55
TOP_FP_K = 6  # how many leading-5-word patterns per model to display


# ------------------------------------------------------------------ helpers ---

def fmt_ci(label: str, ci: dict) -> str:
    p, r, f1 = ci["point"]
    return (
        f"{label:<32} P={p:.4f} [{ci['p_lo']:.4f}, {ci['p_hi']:.4f}]  "
        f"R={r:.4f} [{ci['r_lo']:.4f}, {ci['r_hi']:.4f}]  "
        f"F1={f1:.4f} [{ci['f1_lo']:.4f}, {ci['f1_hi']:.4f}]"
    )


def first_n_words(s: str, n: int = 5) -> str:
    """Lowercased leading n-word stem (stripping punctuation), used as a coarse
    cluster key for FP grouping. Different from a regex pattern; we just want a
    stable bucket for "Further research is needed to..." vs. "Further research
    is needed for...".
    """
    s = re.sub(r"[^a-zA-Z0-9 ]+", " ", str(s).lower())
    words = s.split()
    return " ".join(words[:n])


# ---------------------------------------------------------- load gold + chunks -

def load_gold():
    gold_df = pd.read_csv(OUT / "gold_standard.csv")
    gold_df = gold_df[
        gold_df["gold_gap_sentences"].notna()
        & (gold_df["gold_gap_sentences"].astype(str).str.strip() != "")
    ]
    gold_by_chunk = gold_df.set_index("chunk_id")["gold_gap_sentences"].to_dict()
    gold_ids = set(int(c) for c in gold_df["chunk_id"])
    return gold_by_chunk, gold_ids


# --------------------------------------------------- 1) rule-based-only baseline

def run_rule_baseline(gold_by_chunk, gold_ids):
    print("Loading articles + chunking to apply rule_based_extract on chunk text...")
    articles = rp2.load_articles()
    chunks = rp2.chunk_all(articles)
    text_by_id = {c["chunk_id"]: c["text"] for c in chunks if c["chunk_id"] in gold_ids}

    rule_recs = []
    for cid in sorted(gold_ids):
        preds = rp2.rule_based_extract(text_by_id.get(cid, ""))
        rule_recs.append({"chunk_id": cid, "predictions": json.dumps(preds)})
    pd.DataFrame(rule_recs).to_csv(OUT / "predictions_rule_only.csv", index=False)

    counts = per_chunk_counts(rule_recs, gold_by_chunk, gold_ids)
    ci = bootstrap_ci(counts, gold_ids, B=B, seed=SEED)
    return rule_recs, counts, ci


# ----------------------------------- 2) bootstrap samples for all four models --

def bootstrap_samples_for_all(per_model_counts, gold_ids):
    """Re-bootstrap with a SINGLE rng for paired resampling so every model is
    evaluated on the same resampled chunk indices at iteration b. Returns a
    dict label -> ndarray shape (B, 3) columns (P, R, F1) and the chunk-id list.
    """
    rng = random.Random(SEED)
    ids_list = sorted(gold_ids)
    n = len(ids_list)
    out = {label: np.zeros((B, 3)) for label in per_model_counts}
    for b in range(B):
        sampled = [ids_list[rng.randrange(n)] for _ in range(n)]
        for label, counts in per_model_counts.items():
            p, r, f1, *_ = aggregate(counts, sampled)
            out[label][b] = (p, r, f1)
    return out


# --------------------------------------------------- 3) FP pattern extraction --

def fp_patterns_for_model(preds_records, gold_by_chunk, gold_ids):
    """Return Counter of leading-5-word stems among false-positive predictions
    (a prediction is FP if no gold sentence in its chunk reaches ROUGE-L 0.55).
    """
    from rouge_score import rouge_scorer

    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    counter: Counter = Counter()
    for p in preds_records:
        cid = int(p["chunk_id"])
        if cid not in gold_ids:
            continue
        preds = load_preds_cell(p["predictions"])
        gold_list = [
            g.strip()
            for g in str(gold_by_chunk.get(cid, "")).split(";")
            if g.strip()
        ]
        for pred in preds:
            best = 0.0
            for gold in gold_list:
                f1 = scorer.score(gold, pred)["rougeL"].fmeasure
                if f1 > best:
                    best = f1
            if best < THRESHOLD:
                counter[first_n_words(pred)] += 1
    return counter


# -------------------------------------------------------------- figure 2 (F1) --

def plot_bootstrap_f1(samples_per_label, out_path: Path) -> None:
    """Overlapping histograms of bootstrap F1 per label."""
    labels = list(samples_per_label.keys())
    colors = {
        "GPT-4o":              "#1f4e79",  # deep blue
        "GPT-4o-mini":         "#9c2f2f",  # red (heavy-tailed)
        "Ollama (Llama 3.2)":  "#2e7d32",  # green
        "Rule-based only":     "#6c6c6c",  # grey baseline
    }
    fig, ax = plt.subplots(figsize=(6.8, 3.4))
    bins = np.linspace(0.0, 1.0, 41)
    for label in labels:
        f1 = samples_per_label[label][:, 2]
        c = colors.get(label, "#444444")
        ax.hist(
            f1, bins=bins, alpha=0.55, label=label,
            color=c, edgecolor=c, linewidth=0.6,
        )
        med = float(np.median(f1))
        ax.axvline(med, color=c, linewidth=1.0, linestyle="--", alpha=0.85)
    ax.set_xlim(0.0, 1.0)
    ax.set_xlabel(r"F1 (ROUGE-L $\geq 0.55$, 1,000 paired chunk-level resamples)")
    ax.set_ylabel("Bootstrap count")
    ax.set_title("Bootstrap F1 distribution per method (paired resamples, B = 1,000)")
    ax.grid(alpha=0.25, linewidth=0.5)
    ax.legend(loc="upper left", fontsize=8, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(out_path, format="pdf")
    plt.close(fig)


# ---------------------------------------------------- figure 3 (FP patterns) --

def plot_fp_patterns(fp_counters: dict, out_path: Path, top_k: int = TOP_FP_K) -> None:
    """Grouped horizontal bar chart of top-K FP leading-5-word patterns per model."""
    union_top: Counter = Counter()
    for c in fp_counters.values():
        for k, v in c.most_common(top_k):
            union_top[k] = max(union_top[k], v)
    patterns = [k for k, _ in union_top.most_common(top_k)]

    labels = list(fp_counters.keys())
    colors = {
        "GPT-4o":              "#1f4e79",
        "GPT-4o-mini":         "#9c2f2f",
        "Ollama (Llama 3.2)":  "#2e7d32",
    }

    n_pat = len(patterns)
    n_mod = len(labels)
    bar_h = 0.8 / max(n_mod, 1)
    fig, ax = plt.subplots(figsize=(7.2, 0.42 * n_pat + 1.4))
    y = np.arange(n_pat)
    for i, label in enumerate(labels):
        counts = [fp_counters[label].get(p, 0) for p in patterns]
        ax.barh(
            y + (i - (n_mod - 1) / 2) * bar_h,
            counts,
            height=bar_h,
            color=colors.get(label, "#666666"),
            label=label,
            edgecolor="white",
            linewidth=0.4,
        )
    ax.set_yticks(y)
    pretty_pat = [f"\u201c{p}\u2026\u201d" for p in patterns]
    ax.set_yticklabels(pretty_pat, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel(r"False-positive count on 93 gold chunks (ROUGE-L $\geq 0.55$)")
    ax.set_title("Top false-positive cue patterns per model")
    ax.grid(alpha=0.25, axis="x", linewidth=0.5)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(out_path, format="pdf")
    plt.close(fig)


# --------------------------------------------------------------------- main ----

def main():
    gold_by_chunk, gold_ids = load_gold()
    print(f"Gold chunks: {len(gold_ids)}")

    # ------ rule-based-only baseline -----------------------------------------
    rule_recs, rule_counts, rule_ci = run_rule_baseline(gold_by_chunk, gold_ids)

    # ------ load each model's predictions and compute per-chunk counts -------
    files = {
        "GPT-4o":              OUT / "predictions_gpt_4o.csv",
        "GPT-4o-mini":         OUT / "predictions_gpt4o_mini.csv",
        "Ollama (Llama 3.2)":  OUT / "predictions_ollama.csv",
    }
    print("Computing per-chunk (TP, FP, FN) for each LLM...")
    per_model_counts = {}
    per_model_recs = {}
    for label, path in files.items():
        recs = pd.read_csv(path).to_dict("records")
        per_model_recs[label] = recs
        per_model_counts[label] = per_chunk_counts(recs, gold_by_chunk, gold_ids)
    per_model_counts["Rule-based only"] = rule_counts
    per_model_recs["Rule-based only"] = rule_recs

    # ------ paired bootstrap samples (B=1000) for ALL FOUR labels ------------
    print(f"Paired bootstrap (B={B}) for 3 LLMs + rule-based baseline...")
    samples = bootstrap_samples_for_all(per_model_counts, gold_ids)

    # write the raw samples CSV (useful both for the figure and for any
    # reviewer who wants to recompute paired deltas)
    rows = []
    for label, arr in samples.items():
        for b in range(arr.shape[0]):
            rows.append({
                "model": label, "iter": b,
                "P": float(arr[b, 0]), "R": float(arr[b, 1]), "F1": float(arr[b, 2]),
            })
    pd.DataFrame(rows).to_csv(OUT / "bootstrap_samples.csv", index=False)
    print(f"Wrote {OUT / 'bootstrap_samples.csv'}  ({len(rows)} rows)")

    # ------ rule-baseline summary file --------------------------------------
    rule_lines = [
        f"=== Rule-based-only baseline (no LLM) on 93 gold chunks ===\n",
        f"  Method: rp2.rule_based_extract(chunk_text)  (cue regex applied to sentences)\n",
        f"  Eval:   ROUGE-L F1 >= {THRESHOLD}, stemming\n",
        f"  CI:     1,000-sample chunk-level bootstrap, seed={SEED}\n\n",
        fmt_ci("Rule-based only (no LLM)", rule_ci) + "\n",
        f"  TP={rule_ci['tp_fp_fn'][0]:d}  FP={rule_ci['tp_fp_fn'][1]:d}  FN={rule_ci['tp_fp_fn'][2]:d}\n",
        "\n",
        "For comparison (from bootstrap_ci.txt, same procedure):\n",
        "  GPT-4o                    F1=0.8822 [0.8377, 0.9234]\n",
        "  GPT-4o-mini               F1=0.6971 [0.5389, 0.8988]\n",
        "  Ollama (Llama 3.2)        F1=0.6426 [0.5792, 0.7111]\n",
    ]
    (OUT / "baseline_rule_only.txt").write_text("".join(rule_lines))
    print("\n" + "".join(rule_lines))
    print(f"Wrote {OUT / 'baseline_rule_only.txt'}")

    # ------ FP pattern extraction per model (LLMs only; baseline excluded) ---
    print("\nComputing top FP patterns per model...")
    fp_counters = {}
    for label in ["GPT-4o", "GPT-4o-mini", "Ollama (Llama 3.2)"]:
        fp_counters[label] = fp_patterns_for_model(
            per_model_recs[label], gold_by_chunk, gold_ids,
        )
        print(f"  {label}: {sum(fp_counters[label].values())} FPs total, "
              f"top: {fp_counters[label].most_common(3)}")

    # ------ FP pattern CSV ---------------------------------------------------
    fp_rows = []
    for label, c in fp_counters.items():
        for pattern, count in c.most_common(20):
            fp_rows.append({"model": label, "pattern": pattern, "fp_count": count})
    pd.DataFrame(fp_rows).to_csv(OUT / "fp_patterns.csv", index=False)
    print(f"Wrote {OUT / 'fp_patterns.csv'}")

    # ------ figures ----------------------------------------------------------
    print("\nRendering figures...")
    fig_f1 = FIG_DIR / "bootstrap_f1.pdf"
    plot_bootstrap_f1(samples, fig_f1)
    print(f"Wrote {fig_f1}")

    fig_fp = FIG_DIR / "fp_patterns.pdf"
    plot_fp_patterns(fp_counters, fig_fp, top_k=TOP_FP_K)
    print(f"Wrote {fig_fp}")


if __name__ == "__main__":
    main()
