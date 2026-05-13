#!/usr/bin/env python3
"""
Rule-based gold standard annotation for explicit knowledge gaps.
Uses pattern matching (no LLM) to avoid circular evaluation.
"""
import re
from pathlib import Path
from run_part2 import load_articles, chunk_all

# Explicit gap patterns (case-insensitive) from Part2_Annotation_Guide
GAP_PATTERNS = [
    r"remains unknown",
    r"remains unclear",
    r"it is unclear",
    r"it remains unclear",
    r"further research (is )?needed",
    r"further research (is )?required",
    r"more research (is )?needed",
    r"limited evidence",
    r"no study has",
    r"no studies have",
    r"notable gaps remain",
    r"future work should",
    r"future research should",
    r"we lack (data|evidence|information)",
    r"little is known",
    r"poorly understood",
    r"remains (to be )?explored",
    r"merits further (study|research)",
    r"warrants further (study|research)",
    r"open (question|questions)",
    r"unresolved",
    r"under-researched",
    r"understudied",
    r"scant evidence",
    r"scarce (evidence|data)",
    r"inconclusive",
    r"mixed evidence",
    r"may lead to unintended",  # hedging
]

def _is_citation_fragment(s: str) -> bool:
    """Filter out citation-only fragments (e.g. 'Baillon et al., 2020')."""
    s = s.strip()
    if len(s) < 40:  # short fragment
        # Citation pattern: "Name et al., 2020" or "Name & Name, 2020" or ends with "2020)."
        if re.search(r"et\s+al\.|&\s*[A-Za-z]|,\s*\d{4}\)?\.?$", s):
            return True
    return False


def extract_gap_sentences(text: str) -> list[str]:
    """Extract sentences containing explicit gap patterns."""
    from nltk.tokenize import sent_tokenize
    nltk_data = Path(__file__).parent / "nltk_data"
    import nltk
    nltk.data.path.insert(0, str(nltk_data))
    nltk.download("punkt", quiet=True, download_dir=str(nltk_data))
    nltk.download("punkt_tab", quiet=True, download_dir=str(nltk_data))

    sentences = sent_tokenize(text)
    gaps = []
    combined = re.compile("|".join(f"({p})" for p in GAP_PATTERNS), re.I)
    for sent in sentences:
        if combined.search(sent):
            cleaned = sent.strip()
            if len(cleaned) > 15 and not _is_citation_fragment(cleaned):
                gaps.append(cleaned)
    return gaps

def main():
    from run_part2 import OUTPUT_DIR
    import pandas as pd

    print("Loading articles...")
    articles = load_articles()
    print(f"Loaded {len(articles)} articles")

    print("Chunking...")
    chunks = chunk_all(articles)
    print(f"Created {len(chunks)} chunks")

    print("Extracting explicit gaps (rule-based)...")
    records = []
    for c in chunks:
        gaps = extract_gap_sentences(c["text"])
        records.append({
            "chunk_id": c["chunk_id"],
            "gold_gap_sentences": "; ".join(gaps) if gaps else ""
        })

    df = pd.DataFrame(records)
    annotated_count = (df["gold_gap_sentences"].str.len() > 0).sum()
    print(f"Chunks with ≥1 gap: {annotated_count}")

    # Save to separate file — NEVER overwrite gold_standard.csv (manual annotations)
    out_path = OUTPUT_DIR / "gold_standard_rulebased.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved to {out_path}")
    print("Note: Use gold_standard.csv for evaluation. Copy to gold_standard.csv only if you intend to replace manual annotations.")

if __name__ == "__main__":
    main()
