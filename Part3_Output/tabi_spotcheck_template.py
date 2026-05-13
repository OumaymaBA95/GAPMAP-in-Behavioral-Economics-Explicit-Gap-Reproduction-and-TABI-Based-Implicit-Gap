#!/usr/bin/env python3
"""Generate a 20-row stratified spot-check CSV from tabi_high_confidence_mnli07.csv.

Produces Part3_Output/tabi_spotcheck_20.csv with columns:
  chunk_id, article_filename, claim, grounds, warrant, mnli_entailment_prob,
  human_label  (annotator fills: real_gap / not_a_gap / unclear)
  notes        (annotator fills: free text, optional)

Stratified by MNLI score quartiles (5 rows from each quartile of the
filtered population) so the spot check covers the full confidence range
rather than only the top-MNLI rows.

Usage:
  cd "/Users/momoba/Desktop/Advanced ML Project "
  .venv/bin/python Part3_Output/tabi_spotcheck_template.py
"""
from pathlib import Path
import pandas as pd

SRC = Path("Part3_Output/tabi_high_confidence_mnli07.csv")
OUT = Path("Part3_Output/tabi_spotcheck_20.csv")
SEED = 7


def main():
    df = pd.read_csv(SRC)
    df = df.sort_values("mnli_entailment_prob").reset_index(drop=True)
    n = len(df)
    bins = [0, n // 4, n // 2, 3 * n // 4, n]
    rows = []
    for i in range(4):
        lo, hi = bins[i], bins[i + 1]
        sub = df.iloc[lo:hi]
        rows.append(sub.sample(n=5, random_state=SEED + i))
    sample = pd.concat(rows, ignore_index=True)
    sample = sample.sample(frac=1, random_state=SEED).reset_index(drop=True)
    keep = ["chunk_id", "article_filename", "claim", "grounds", "warrant",
            "mnli_entailment_prob"]
    sample = sample[keep]
    sample["human_label"] = ""
    sample["notes"] = ""
    OUT.parent.mkdir(exist_ok=True)
    sample.to_csv(OUT, index=False)
    print(f"Wrote {OUT} ({len(sample)} rows; MNLI range "
          f"{sample['mnli_entailment_prob'].min():.4f}-"
          f"{sample['mnli_entailment_prob'].max():.4f})")


if __name__ == "__main__":
    main()
