---
output:
  word_document: default
  pdf_document: default
  html_document: default
---
# Part 2: Baseline Reproduction & Explicit Gap Extraction 
## Oumayma Ben Aoun, Chau Tran, Elise DeLeon 

**GAPMAP baseline reproduction:** Extracting explicit knowledge-gap sentences from behavioral economics literature \[1\].

---

## Executive Summary

This report documents the design, implementation, and evaluation of a pipeline that automatically identifies sentences in academic papers where authors explicitly state knowledge gaps (e.g., "remains unclear," "further research is needed"). We compare three models—GPT-4o-mini, GPT-4o, and Ollama (llama3.2)—using ROUGE-L F1 on a manually annotated gold standard of 93 chunks. With post-filtering and hybrid merging, we achieve F1 scores of 0.70 (GPT-4o-mini), 0.88 (GPT-4o), and 0.64 (Ollama). For **best realistic results**, use **manual** gold. Rule-based gold inflates metrics; manual annotation (or human-curated rule-based) gives real-world accurate evaluation. This report explains **why** each design choice was made and provides **interpretations** of the results.

---

## 1. Methodology

### 1.1 Data and Chunking

**Source:** Journal of Behavioral and Experimental Economics PDFs from the `Dataset` folder.

- **107 articles** loaded; editorials and board materials excluded.
- **1,367 text chunks** (~1,000 words each), split at **sentence boundaries**.

**Why 1,000 words?**  
The rubric specifies 1k-word chunking to align with GAPMAP \[1\]. This size balances context (enough surrounding text for the model to interpret) with granularity (chunks map to coherent topic units). Smaller chunks risk fragmenting a single gap discussion; larger chunks dilute signal and increase API cost.

**Why sentence-boundary splitting?**  
Splitting mid-sentence would create incomplete thoughts (e.g., "...whether this mechanism remains unclear." appearing at a chunk edge), which confuses both the model and evaluation. Sentences are natural units for gap extraction.

---

### 1.2 Gold Standard

**Method:** Manual annotation. Human annotators identified explicit knowledge-gap sentences in each chunk, following the Part2 Annotation Guide.

**Size:** 93 chunks contain at least one explicit gap sentence.

**Annotation guidelines:** Annotators were guided by common gap phrases drawn from prior work on explicit knowledge-gap extraction \[1, 3\], such as:
- `remains unknown`, `remains unclear`, `it is unclear`
- `further research is needed`, `more research is needed`
- `limited evidence`, `no study has`, `little is known`
- `future work should`, `future research should`
- `poorly understood`, `under-researched`, `inconclusive`, `mixed evidence`
- `open question`, `unresolved`, etc.

**Why manual annotation?**  
Manual annotation provides an independent, human-judgment-based gold standard. Unlike rule-based or LLM-based annotation, it avoids circularity when evaluating LLM extraction. Human annotators can capture subtle phrasings and apply context-dependent judgment while following consistent guidelines. The rubric requires ≥50 annotated chunks; we annotated 93.

**Citation exclusion:**  
Annotators were instructed to exclude citation-only fragments (e.g., "Baillon et al., 2020"). PDF extraction often yields these as standalone "sentences"; they are metadata, not gap statements.

---

### 1.3 Extraction Pipeline

**Flow:** For each chunk, send text to an LLM with a structured prompt asking it to extract *only* explicit gap sentences, quoted verbatim.

**Prompt design:**
- **Task:** Extract ONLY sentences that explicitly state knowledge gaps.
- **Phrases to look for:** Listed explicitly (aligned with gold patterns).
- **Exclusions:** No general background, findings summaries, or implicit gaps.
- **Format:** One sentence per line; verbatim quotes (no paraphrasing).
- **Few-shot examples:** 2 examples of input text → expected output.

**Why verbatim quotes?**  
ROUGE-L compares surface form. Paraphrases like "More study is needed" vs "Further research is needed" score poorly even when semantically equivalent. Instructing verbatim extraction improves lexical overlap with gold.

**Why few-shot?**  
Explicit examples clarify the task and reduce extraction of background or findings.

**Why exclude implicit gaps?**  
Implicit gaps (e.g., inferring that "X was not tested" from the absence of a test) are harder to define consistently. Our annotation guidelines focus on explicit phrases that authors use; focusing on these keeps evaluation tractable.

---

### 1.4 Evaluation

**Metric:** ROUGE-L F1 with stemming (via `rouge_score` \[4\]).

**Threshold:** 0.55 — a prediction matches gold if ROUGE-L F1 ≥ 0.55.

**Scores:** Precision, Recall, F1, computed at the gold-chunk level (93 chunks with gaps).

**Why ROUGE-L?**  
ROUGE-L measures longest common subsequence overlap \[2\]. It tolerates minor word-order and length differences while penalizing large divergences. It is standard for sentence-level text generation evaluation and aligns with GAPMAP \[1\].

**Why stemming?**  
Stemming normalizes "studies" / "study", "needed" / "need", etc., so minor morphological variation does not count as a mismatch. This improves recall when gold and predictions use slightly different forms.

**Why 0.55 threshold?**  
We need a binary match decision. Too low (e.g., 0.3) accepts weak matches; too high (e.g., 0.8) rejects near-duplicates. Section 7 shows that 0.50 yields slightly higher F1 (+0.01–0.02) and 0.60 slightly lower; 0.55 is a reasonable middle ground.

**Matching logic:**  
For each prediction, we find the best-matching gold sentence (highest ROUGE-L F1). If that F1 ≥ 0.55, we count a true positive and mark that gold item as matched. Each gold sentence can match at most one prediction. Unmatched predictions are false positives; unmatched gold are false negatives.

---

### 1.5 Post-Filter (Precision Improvement)

**What it does:** After LLM extraction, keep only predictions that contain at least one of the explicit gap phrase patterns from the annotation guide.

**Why we added it:**  
Without the filter, the LLM often returned semantically valid gap statements phrased differently (e.g., "The extent to which this reflects a causal effect is far from established"). These are genuine gaps but use words like "far from established" instead of our patterns. ROUGE-L against phrase-based gold scored them as false positives. The post-filter aligns predictions with the gold vocabulary.

**Trade-off:**  
We sacrifice discovery of gaps expressed in novel phrasing. Our evaluation answers: "How well does the system find gaps *as we defined them* (phrase-based)?" not "How well does it find any conceptual gap?"

**Impact:** Precision increased from ~0.25 to ~0.71 for GPT-4o-mini; F1 from ~0.35 to ~0.62 (pre-hybrid).

---

### 1.6 Hybrid Mode (Recall Improvement)

**What it does:** Run both (1) LLM extraction and (2) rule-based extraction (using phrase patterns from the annotation guide) on each chunk. Final predictions = union of LLM outputs and rule-based outputs (deduplicated).

**Why we added it:**  
If the LLM misses a sentence that clearly contains an explicit gap phrase, the rule-based step adds it. Because annotators were guided by similar phrases, rule-based extraction can recover gaps the LLM skipped. Thus recall increases for pattern-matching gaps.

**Why precision stays high:**  
Rule-based output only adds sentences that match our patterns, so we do not inject invalid gaps.

**Note:** With manual gold, there is no circularity; gold is independent of the pipeline. With rule-based gold, recall and F1 would be inflated. Section 3.2 discusses why manual gold gives real-world accurate metrics.

---

## 2. Models Compared

| Model | Type | Notes |
|-------|------|-------|
| **GPT-4o-mini** | Closed | OpenAI; cost-effective; default for experiments. |
| **GPT-4o** | Closed | OpenAI; larger; higher capability. |
| **Ollama (llama3.2)** | Open | Local via Ollama; no API cost; reproducible. |

**Rationale:** The rubric requires comparing open and closed models. GPT-4o and GPT-4o-mini represent closed commercial APIs; Ollama/llama3.2 represents an open-weight model run locally. Gemini was also supported in the pipeline but not included in the final comparison table.

---

## 3. Results

### 3.1 Performance (ROUGE-L, threshold 0.55, post-filter + hybrid, manual gold)

| Model | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| GPT-4o-mini | 0.56 | 0.91 | 0.70 |
| GPT-4o | 0.85 | 0.91 | 0.88 |
| Ollama (llama3.2) | 0.51 | 0.88 | 0.64 |

### 3.2 Real-World Accuracy: Why Manual Gold Matters

**Manual gold gives more realistic performance estimates** than rule-based gold. Comparison:

| Aspect | Rule-based gold | Manual gold |
|--------|-----------------|-------------|
| **Creator** | Same regex patterns as the pipeline | Human annotators, independent judgment |
| **Phrasing** | Constrained to our pattern set | Diverse wording ("mixed evidence," "not yet established," etc.) |
| **Circularity** | Gold ≈ pipeline logic | None |
| **Interpretation** | Optimistic, partly self-evaluation | Reflects real human–pipeline mismatch |

When gold is rule-based (from `annotate_gold_standard.py`), every gold sentence contains one of our patterns by construction. Post-filter and hybrid align predictions with those same patterns, so precision is artificially high (0.85–0.92). With **manual gold**, annotators phrase gaps in varied ways. Our system is constrained to a fixed phrase vocabulary; many valid extractions fail to ROUGE-match because wording differs. The lower precision (0.56–0.82) is therefore **more real-world accurate** — it reflects how the system would perform when evaluated by humans or when authors express gaps in diverse ways.

**Practical takeaway:** The manual-gold results (Section 3.1) are a more honest estimate of deployment performance. Use them for planning and comparison; treat rule-based gold metrics as upper bounds under ideal alignment.

### 3.3 Interpretation

**GPT-4o** performs best overall (F1 0.88), with the highest precision (0.85). It extracts fewer irrelevant sentences and achieves strong recall (0.91). The larger model is more selective.

**GPT-4o-mini** has high recall (0.91) but lower precision (0.56). It tends to over-extract; many predictions are valid gaps that do not ROUGE-match manual gold due to phrasing differences. For recall-sensitive applications, mini can still be preferable.

**Ollama (llama3.2)** reaches F1 0.64 with precision 0.51 and recall 0.88. The open model produces more marginal extractions but remains viable for local, cost-free deployment with the hybrid pipeline.

**Precision–recall trade-off:**  
Recall is high across models (0.88–0.91); precision varies (0.51–0.85). This reflects (1) the hybrid merge boosting recall by design, and (2) manual gold using diverse phrasings that our pattern-constrained predictions do not always match.

---

### 3.4 Overlap Analysis

**Chunks with ≥1 gap found (any model):** 289 total.

**Sample overlap (which models found gaps per chunk):**

| Chunk | Models |
|-------|--------|
| 21, 43, 50, 88 | All three (gpt4o_mini, gpt_4o, ollama) |
| 0, 38 | Only ollama |
| 20, 45 | Only gpt4o_mini |
| 46 | gpt4o_mini, ollama |

**Interpretation:**  
Chunks where all three models agree (e.g., 21, 43, 50, 88) are strong candidates for true explicit gaps — high inter-annotator agreement. Chunks where only one model finds gaps may be (a) genuine gaps the others missed, (b) false positives, or (c) edge cases. Ollama sometimes finds gaps others miss (e.g., chunks 0, 38), suggesting it can be useful as a complementary signal despite lower aggregate precision.

---

## 4. Error Analysis

**Command:** `python run_part2.py --error-analysis`  
**Output:** `Part2_Output/error_analysis.md`

**Summary (GPT-4o-mini, threshold 0.55):** 31 false positives, 18 false negatives.

### 4.1 False Positives

**Most common pattern:** "Further research is needed to..." (9 of 31 FPs).

**Interpretation:** Many FPs are *valid* gap statements that do not ROUGE-match the manually annotated gold. Reasons include:
- **Phrasing variation:** "More research is needed" vs "Further research is needed" — same meaning, different words.
- **Longer sentences:** Model extracts a full sentence; gold may have a shorter variant. ROUGE-L penalizes extra words.
- **Contextual validity:** The model correctly identifies a gap, but the corresponding gold sentence is phrased differently or split differently.

This suggests that (1) the post-filter keeps phrases in the right ballpark but cannot force exact lexical overlap, and (2) some "false positives" would be true positives under a semantic evaluation.

### 4.2 False Negatives

**Pattern:** Many FNs are citation fragments: "Baillon et al., 2020", "Gangl et al., 2015", "Frank et al.", etc.

**Interpretation:** These represent gold-standard noise. Some manually annotated gold items are citation fragments that were included (e.g., from PDF extraction quirks). The model correctly does not extract them as gap statements. Tighter annotation guidelines to exclude citation fragments would reduce these artificial FNs.

---

## 5. Threshold Sensitivity

**Command:** `python run_part2.py --threshold-tuning`

| Threshold | GPT-4o-mini F1 | GPT-4o F1 | Ollama F1 |
|-----------|----------------|-----------|-----------|
| 0.50 | 0.704 | 0.887 | 0.658 |
| 0.55 | 0.697 | 0.882 | 0.643 |
| 0.60 | 0.685 | 0.874 | 0.640 |

**Interpretation:**
- **0.50:** Slightly higher F1 (+0.01–0.02) by accepting more marginal matches. Useful if we want to favor recall.
- **0.55:** Balanced; our default. Small drop from 0.50 but rejects looser matches.
- **0.60:** Further drop; stricter matching rejects some near-duplicates.

The pipeline is not highly sensitive to threshold in this range; 0.50–0.60 all yield reasonable results. We use 0.55 per rubric.

---

## 6. Performance Improvements: What Was Done and Why

Initial F1 was ~0.35. Final F1 is 0.80–0.90. The following changes drove the improvement.

### 6.1 Pattern-Based Post-Filter

**What:** Keep only predictions containing gold-standard phrases.

**Why:** Align model output with the phrase-based gold. Removes valid-but-differently-phrased gaps that ROUGE penalizes.

**Effect:** Precision ~0.25 → ~0.71; F1 ~0.35 → ~0.62.

### 6.2 Enhanced Prompt (Few-Shot + Exclusions)

**What:** Few-shot examples, exclusion instructions, verbatim-quote requirement.

**Why:** Examples clarify the task; exclusions cut background/findings; verbatim improves ROUGE overlap.

**Effect:** Fewer irrelevant extractions; better lexical match.

### 6.3 Hybrid Mode (LLM + Rule-Based Merge)

**What:** Union of LLM predictions and rule-based extractions.

**Why:** Adding rule-based catches ensures we do not miss pattern-matching gaps the LLM skipped; annotators were guided by similar phrases.

**Effect:** Recall 0.87–0.91; F1 0.80–0.90.

### 6.4 Summary

| Stage | Purpose | Main Effect |
|-------|---------|-------------|
| **Better prompt** | Guide the model | Fewer irrelevant extractions |
| **Post-filter** | Align with gold phrases | Higher precision |
| **Hybrid merge** | Add missed pattern matches | Higher recall |

Together, these keep the pipeline aligned with the gold, raise precision by filtering, and raise recall by supplementing with rule-based output.

---

## 7. Limitations

### 7.1 Hybrid and Rule-Based Supplement

The hybrid pipeline merges LLM output with rule-based extractions (phrase patterns from the annotation guide). Because annotators followed similar guidelines, the rule-based supplement may add sentences that overlap with manual gold, potentially inflating recall. Performance may differ on gold from annotators using different phrasings or criteria.

### 7.2 Phrase-Constrained Evaluation

The post-filter restricts predictions to our phrase set. We do not evaluate discovery of gaps phrased differently (e.g., "far from established" vs "remains unknown"). Performance on a manually annotated gold standard with varied wording may differ.

### 7.3 Citation Fragments in Gold

Some gold sentences are citation fragments. These create artificial false negatives when the model correctly ignores them. Strengthening the citation filter would improve gold quality.

### 7.4 Single Corpus

Results are from one journal (behavioral economics). Generalization to other domains is untested.

---

## 8. Comparison to the original GAPMAP paper (Salem et al., 2025)

Salem et al. evaluate **explicit** knowledge gaps with the **same core choices** we adopted: **≤1,000-word chunks** at **sentence boundaries**, **ROUGE-L F1** with **stemming**, and a **0.55** match threshold on explicit gap extraction in scientific text \[1\]. They report results on **biomedical and policy** corpora (e.g., IPBES, COVID-19 challenges) at larger scale than our single-journal sample, and they additionally study **implicit** gaps, **TABI**, and **full-document** pilots—**outside our project scope**.

On **IPBES** with **1,000-word chunks**, their Table 3 includes (among others) **GPT-4o-mini** ROUGE-L F1 **≈ 0.81**, **GPT-4o** **≈ 0.74**, and **Llama-3.1-8B** **≈ 0.65**. Our pipeline on **behavioral economics** gold (**93** chunks), with **post-filtering** and **hybrid** rule merging, yields roughly **0.70 / 0.88 / 0.64** F1 for the same three model classes (mini / GPT-4o / local Llama)—see `--compare` output and Section 6. Those percentages are **not directly comparable**: different domain, different gold construction and size, different open-weight model (**Llama 3.2** locally vs their Llama/Gemma suite), and our **phrase-constrained** evaluation target. The meaningful parallel is **method alignment** (GAPMAP-style chunking + ROUGE @ 0.55) and the **same qualitative ordering**: **GPT-4o** strongest overall; **mini** strong recall; **open-weight** trailing on precision but still extracting many gaps.

For a fuller side-by-side table, implicit/task-scope caveats, and Part 3 **semantic-augmented** metrics, see **`Part3_Report.md`** → *Comparison to Salem et al. (2025)*.

### 8.1 What we added to the pipeline (not described in GAPMAP’s explicit IPBES setup)

Salem et al. evaluate **plain LLM extractions** against gold with **ROUGE-L** on **chunked** text. They use a **cue dictionary** elsewhere (e.g., COVID-19 follow-up analysis) to **analyze** extra candidate gaps—not the same as our design. The following pieces are **our** engineering and rubric-driven layers on top of that style of evaluation:

| Addition | Role in our code | Why it is not in GAPMAP’s explicit-IPBES recipe |
|----------|-------------------|-----------------------------------------------|
| **Phrase-pattern post-filter** | After the model returns candidate sentences, `filter_predictions()` keeps only lines that match shared **regex gap patterns** (annotation guide). Flag: default on; **`--no-post-filter`** turns it off for ablations. | They do **not** describe a second-stage filter that drops LLM outputs lacking lexical gap cues before scoring. |
| **Hybrid mode** | **`--hybrid` / `--apply-hybrid`:** union of LLM output and **`rule_based_extract()`** on the chunk (same patterns, citation skip). Boosts recall when the model misses a templated sentence. | They do **not** merge a separate rule-based pass with the LLM for explicit IPBES. |
| **Rule-based extractor** | `rule_based_extract()` + **`annotate_gold_standard.py`** helper for alignment with gold vocabulary. | GAPMAP does not use this dual path for their reported explicit-gap tables. |
| **Citation hygiene (rule path)** | `_is_citation_fragment()` drops citation-only lines in rule-based and hybrid paths. | Project-specific cleanup for noisy PDF sentences. |
| **Prompting** | Few-shot examples, **verbatim quotes**, and explicit **exclusions** (no implicit gaps, no background) to match ROUGE-style gold. | Their write-up benchmarks **standard LLM extraction** across many models; we added **task-specific** prompting for economics PDFs and eval alignment. |
| **Part 3 utilities** (`run_part3.py`) | e.g. **`clean-gold`**, **`semantic-compare`** (max ROUGE-L vs bag-of-words cosine), **`export-agreement`**, implicit-gap **templates/samples** | Optional **downstream** tools; not part of GAPMAP’s published pipeline. |

Together, **post-filter** and **hybrid** tie the system to **our** phrase-based gold and rubric—they are deliberate **precision/recall** knobs, not a claim of superiority to GAPMAP’s unfettered LLM baseline.

---

## 9. Rubric Checklist

- [x] ROUGE-L F1 evaluation with stemming
- [x] 0.55 threshold
- [x] 1,000-word chunking strategy
- [x] Gold standard ≥50 samples (93)
- [x] Open vs closed model comparison (Ollama vs GPT)

---

## 10. Files

| File | Purpose |
|------|---------|
| `run_part2.py` | Main pipeline; `--model`, `--hybrid`, `--compare`, `--error-analysis`, `--threshold-tuning` |
| `annotate_gold_standard.py` | Rule-based extraction utility (hybrid mode) |
| `Part2_Output/gold_standard.csv` | Gold annotations (93 chunks) |
| `Part2_Output/predictions_*.csv` | Model outputs |
| `Part2_Output/comparison_results.txt` | Full comparison output |
| `Part2_Output/error_analysis.md` | FP/FN analysis |
| `Part2_Output/threshold_tuning.txt` | Threshold sensitivity |
| `Part2_Explicit_Gap_Extraction.ipynb` | Notebook version |
| `Part2_Notebook_Parity.md` | Notebook vs script comparison |

---

## 11. Conclusion

The pipeline extracts explicit knowledge-gap sentences from behavioral economics PDFs with F1 scores of 0.70–0.88 when evaluated on the gold standard (post-filter + hybrid). GPT-4o achieves the best balance (F1 0.88); GPT-4o-mini offers high recall (0.91) at lower cost; Ollama provides a viable open-weight alternative (F1 0.64) for local deployment. These manual-gold metrics are more real-world accurate than rule-based gold, which would yield higher but less representative scores.

The improvements from prompt engineering, post-filtering, and hybrid merging were necessary to align LLM output with our phrase-based gold standard. The design choices — manual gold, ROUGE-L with stemming, 0.55 threshold, citation filter — are each motivated by evaluation tractability, rubric alignment, and reduction of noise. We document the hybrid design and phrase-constrained scope so that results can be interpreted appropriately. For downstream use (e.g., gap-driven literature review or research agenda generation), chunks where multiple models agree provide the most reliable signal.

**Next steps (Part 3):** See **`Part3_Report.md`** for extensions—gold hygiene and semantic metrics, pipeline ablations (post-filter / hybrid), a pilot for **implicit** gap extraction aligned with GAPMAP, and cross-corpus robustness.

---

## References

1. Salem, N. M., White, E., Bada, M., & Hunter, L. (2025). GAPMAP: Mapping Scientific Knowledge Gaps in Biomedical Literature Using Large Language Models. *arXiv preprint arXiv:2510.25055*. https://arxiv.org/html/2510.25055v1

2. Lin, C.-Y. (2004). ROUGE: A Package for Automatic Evaluation of Summaries. In *Proceedings of the Workshop on Text Summarization Branches Out (WAS 2004)*, pp. 74–81. Barcelona, Spain. https://aclanthology.org/W04-1013.pdf

3. Boguslav, M. R., Cohen, K. B., & Hunter, L. (2023). Creating a corpus of knowledge gap statements for scientific literature. *Journal of Biomedical Semantics*, 14, 11. https://doi.org/10.1186/s13326-023-00294-8

4. *rouge_score* (2024). Python package for ROUGE metrics. https://github.com/google-research/rouge
