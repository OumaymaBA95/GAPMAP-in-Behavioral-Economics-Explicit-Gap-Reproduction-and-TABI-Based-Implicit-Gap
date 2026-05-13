---
layout: default
title: GAPMAP Baseline Reproduction
---

# GAPMAP Baseline Reproduction: Extracting Explicit Knowledge-Gap Sentences from Behavioral Economics Literature

## Executive Summary
This project implements and evaluates a pipeline to automatically identify explicit knowledge-gap sentences in behavioral economics literature, following the GAPMAP framework. We compare GPT-4o-mini, GPT-4o, and Ollama (llama3.2) using ROUGE-L F1 on a manually annotated gold standard. The best F1 scores are 0.70 (GPT-4o-mini), 0.88 (GPT-4o), and 0.64 (Ollama). Manual annotation provides the most realistic evaluation. This page summarizes methodology, results, and key design choices.

## Methodology
- **Data:** 107 articles from the Journal of Behavioral and Experimental Economics, chunked into 1,367 ~1,000-word segments at sentence boundaries.
- **Gold Standard:** 93 chunks manually annotated for explicit gap sentences using a phrase-based guide (e.g., "remains unknown", "further research is needed").
- **Pipeline:** Each chunk is sent to an LLM with a structured prompt to extract only explicit gap sentences (verbatim). Post-filtering and hybrid merging (LLM + rule-based) are used to improve precision and recall.
- **Evaluation:** ROUGE-L F1 with stemming, threshold 0.55. Precision, recall, and F1 are reported at the chunk level.

## Results
| Model | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| GPT-4o-mini | 0.56 | 0.91 | 0.70 |
| GPT-4o | 0.85 | 0.91 | 0.88 |
| Ollama (llama3.2) | 0.51 | 0.88 | 0.64 |

- **Manual gold** gives more realistic performance than rule-based gold.
- **Hybrid pipeline** (LLM + rule-based) boosts recall without sacrificing precision.

## Key Design Choices
- **1,000-word chunking** at sentence boundaries for context and granularity.
- **Manual annotation** for gold standard to avoid circularity.
- **Post-filter** to align predictions with gold phrases.
- **Hybrid mode** to merge LLM and rule-based outputs.
- **ROUGE-L F1 with stemming** and 0.55 threshold for evaluation.

## Files
- `run_part2.py`: Main pipeline
- `annotate_gold_standard.py`: Rule-based extraction utility
- `Part2_Output/gold_standard.csv`: Gold annotations
- `Part2_Output/predictions_*.csv`: Model outputs
- `Part2_Output/comparison_results.txt`: Full comparison output
- `Part2_Output/error_analysis.md`: FP/FN analysis
- `Part2_Output/threshold_tuning.txt`: Threshold sensitivity
- `Part2_Explicit_Gap_Extraction.ipynb`: Notebook version
- `Part2_Notebook_Parity.md`: Notebook vs script comparison

## Conclusion
The pipeline extracts explicit knowledge-gap sentences from behavioral economics PDFs with F1 scores of 0.70–0.88. GPT-4o achieves the best balance; Ollama is a viable open-weight alternative. Manual-gold metrics are more real-world accurate than rule-based gold. Prompt engineering, post-filtering, and hybrid merging were key to aligning LLM output with the gold standard.

## References
1. Salem, N. M., White, E., Bada, M., & Hunter, L. (2025). GAPMAP: Mapping Scientific Knowledge Gaps in Biomedical Literature Using Large Language Models. *arXiv preprint arXiv:2510.25055*.
2. Lin, C.-Y. (2004). ROUGE: A Package for Automatic Evaluation of Summaries. In *Proceedings of the Workshop on Text Summarization Branches Out (WAS 2004)*.
3. Boguslav, M. R., Cohen, K. B., & Hunter, L. (2023). Creating a corpus of knowledge gap statements for scientific literature. *Journal of Biomedical Semantics*, 14, 11.
4. *rouge_score* (2024). Python package for ROUGE metrics.
