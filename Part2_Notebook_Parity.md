# Part 2: Notebook vs Script Parity

Comparison of `Part2_Explicit_Gap_Extraction.ipynb` and `run_part2.py`.

---

## Summary

| Aspect | Notebook | Script |
|--------|----------|--------|
| **Data loading** | `load_all_articles()` — matches script when run from project root | `load_articles()` — 107 articles |
| **Chunking** | Same 1,000-word logic | 1,367 chunks |
| **Prompt** | `EXTRACT_SYSTEM_PROMPT` (imported from run_part2) | `EXTRACT_SYSTEM_PROMPT` (few-shot, exclusions) |
| **Post-filter** | Yes (filter_predictions) | Yes (pattern-based) |
| **Hybrid** | Yes (rule_based_extract merge) | Yes (LLM + rule-based merge) |
| **Evaluation** | Same ROUGE-L 0.55, stemming | Same |

**Notebook now aligned:** Run from project root; uses script prompt, post-filter, and hybrid.

---

## Key Differences

### 1. Data Scope

- **Notebook:** Loads from `DATASET_BASE = PROJECT_ROOT / "Dataset"`. Last run: 30 articles, 374 chunks.
- **Script:** Same path; loads 107 articles, 1,367 chunks. Excludes Editorial/Board PDFs, requires >500 words.

**Recommendation:** Run the notebook from the project root (`/Users/momoba/Desktop/Advanced ML Project /`) so `Path(".").resolve()` matches the script’s base path.

### 2. Extraction Prompt

**Notebook:**
```
Explicit knowledge gaps: "remains unknown", "it is unclear", "further research is needed",
"no randomized controlled trial has evaluated", "limited evidence", "future work should".
Hedging: "may lead to", "could cause", "might indicate".
```

**Script:** Adds few-shot examples, exclusion rules (no background/findings/implicit gaps), and “quote verbatim” instructions.

### 3. Post-Filter and Hybrid

- **Notebook:** No post-filter; no rule-based merge.
- **Script:** Post-filter keeps only predictions matching gold-standard patterns. Hybrid adds rule-based extractions.

### 4. Annotation Template

- **Notebook:** `text_preview` = first 1,500 chars.
- **Script:** `text_preview` = first 500 chars.

### 5. Evaluation Logic

Both use ROUGE-L with stemming and a 0.55 threshold. Matching (pred → best gold, one-to-one) is equivalent.

---

## How to Align Notebook with Script

1. **Set PROJECT_ROOT:** Use `Path(__file__).parent.resolve()` if running from script dir, or ensure notebook runs from project root.
2. **Use script prompt:** Replace `EXPLICIT_GAP_SYSTEM_PROMPT` with `EXTRACT_SYSTEM_PROMPT` from `run_part2.py`.
3. **Add post-filter:** After LLM extraction, apply `filter_predictions()` before evaluation.
4. **Add hybrid (optional):** Merge rule-based extractions with LLM predictions.

---

## Verdict

The script is the current reference pipeline (post-filter + hybrid). The notebook reproduces the same evaluation logic but uses an older prompt and lacks post-filter and hybrid. For parity, run the script or update the notebook to match the script’s prompt and post-processing.
