# Part 3: Full Project Summary, New Code, and Next Steps

**Authors:** Oumayma Ben Aoun, Chau Tran, Elise DeLeon  

This document is the **Part 3 report**: it records **everything completed in Parts 1–2** (as implemented in this repository), and introduces **new code and workflows** for improvements and GAPMAP-aligned extensions.

### Why Part 3 exists (what it is / is not)

- **Part 2** is the core deliverable: explicit-gap extraction, ROUGE-L evaluation, notebook, gold standard, open vs closed models. That stands on its own.
- **Part 3** is **optional follow-on**: stronger analysis, cleaner gold, a second view of metrics that credit paraphrases, scaffolding for **implicit** gaps (as in full GAPMAP), and instructions for ablations. It does **not** replace the rubric metric unless your instructor agrees.

**What each Part 3 command is *for*:**

| Piece | Purpose in one sentence |
|-------|-------------------------|
| **`clean-gold`** | Remove citation-like junk from gold labels so evaluation is not unfairly penalized. |
| **`semantic-compare`** | Report P/R/F1 when a match counts if **either** ROUGE-L **or** simple word-overlap is high — helps interpret cases where the model is right but wording differs from gold. |
| **`export-agreement`** | List chunks where **all three** models found a gap — useful “high confidence” candidates for reading or downstream use. |
| **`implicit-template` / `implicit-sample`** | Prepare rows (and text excerpts) to **manually** label *implicit* gaps, which Part 2 did not extract. |
| **`ablation-commands`** | Reminder of how to re-run extraction with `--no-post-filter` or `--hybrid` to see what helps. |
| **`implicit-extract`** | Small **demo** of one-chunk implicit extraction via API; not the full implicit benchmark. |
| **`tabi-extract`** | Batch **TABI** outputs (Claim / Grounds / Warrant / Bucket) per chunk → **`Part3_Output/tabi_outputs.csv`** (GPT-4o-class model recommended). |
| **`tabi-validate`** | Optional **RoBERTa-MNLI** entailment score on grounds+warrant → claim (`pip install torch transformers`). |

### Part 3 results (this repository; re-run commands to refresh)

| Step | Result |
|------|--------|
| `clean-gold` | 7 citation-like gold sentences removed; **93** chunks still have ≥1 gap → `Part3_Output/gold_standard_cleaned.csv` |
| `semantic-compare` (threshold 0.55) | GPT-4o-mini F1 0.72; GPT-4o F1 0.90; Ollama F1 0.67 — see `Part3_Output/semantic_compare.txt` for full P/R |
| `export-agreement` | **99** chunks where GPT-4o-mini, GPT-4o, and Ollama **all** predicted ≥1 gap → `Part3_Output/high_confidence_chunks.csv` |

*Interpretation:* Triple agreement (99 chunks) means all three models surfaced at least one candidate gap there; those chunks are strong candidates for qualitative review or literature-mapping. This count is **not** limited to the 93 gold chunks—it is over the full corpus where all three prediction files overlap.

---

## Part A — What We Have Done (Completed Work)

### A.1 Corpus and preprocessing

| Item | Detail |
|------|--------|
| **Source** | Journal of Behavioral and Experimental Economics PDFs under `Dataset/` |
| **Articles** | 107 (editorials/board PDFs skipped) |
| **Chunking** | ~1,000 words, sentence boundaries (GAPMAP-style) |
| **Chunks** | 1,367 global `chunk_id` values |

**Code:** `run_part2.py` — `load_articles()`, `chunk_text()`, `chunk_all()`; mirrored in `Part2_Explicit_Gap_Extraction.ipynb`.

### A.2 Gold standard

| Item | Detail |
|------|--------|
| **Requirement** | ≥50 chunks with ≥1 explicit gap (rubric) |
| **Current** | 93 annotated chunks in `Part2_Output/gold_standard.csv` |
| **Guidelines** | `Part2_Annotation_Guide.md` |
| **Rule-based helper** | `annotate_gold_standard.py` → writes **`gold_standard_rulebased.csv`** only (does **not** overwrite manual `gold_standard.csv`) |

### A.3 Explicit gap extraction

| Item | Detail |
|------|--------|
| **Task** | Extract sentences where authors *explicitly* state knowledge gaps |
| **Prompt** | Few-shot, exclusions, verbatim quotes — `EXTRACT_SYSTEM_PROMPT` in `run_part2.py` |
| **Post-filter** | Keep predictions matching regex gap patterns (`filter_predictions`) |
| **Hybrid** | Union of LLM output + `rule_based_extract()` (optional at extract time; notebook merges after OpenAI/Ollama) |
| **Models** | GPT-4o-mini, GPT-4o (OpenAI), Llama 3.2 (Ollama) |

**Outputs:** `Part2_Output/predictions_gpt4o_mini.csv`, `predictions_gpt_4o.csv`, `predictions_ollama.csv` — columns `chunk_id`, `predictions` (JSON list).

### A.4 Evaluation

| Item | Detail |
|------|--------|
| **Metric** | ROUGE-L F1 with stemming |
| **Match threshold** | 0.55 (rubric); sensitivity 0.50 / 0.60 in `threshold_tuning.txt` |
| **Script** | `python run_part2.py --compare` |
| **Extras** | `--error-analysis` → `error_analysis.md`; `--threshold-tuning` |

### A.5 Results (ROUGE-L @ 0.55, post-filter + hybrid, manual gold)

From `Part2_Output/comparison_results.txt`:

| Model | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| GPT-4o-mini | **0.8524** | **0.9086** | **0.8796** |
| GPT-4o | **0.9152** | **0.8882** | **0.9015** |
| Ollama (llama3.2) | **0.7448** | **0.8720** | **0.8034** |

*These are the current manual-gold numbers for this repository; re-run `python run_part2.py --compare` after any gold/prediction update.*

### A.6 Deliverables (Part 2)

| Artifact | Path |
|----------|------|
| Main report | `Part2_Report.md` |
| Notebook | `Part2_Explicit_Gap_Extraction.ipynb` |
| Pipeline CLI | `run_part2.py` |
| Outputs | `Part2_Output/*` |

### A.7 Design limitations (drive Part 3)

- Phrase-constrained post-filter and hybrid can inflate alignment with rule-like gold.
- ROUGE-L penalizes valid paraphrases.
- Gold may still contain citation-like noise; explicit-only scope vs full GAPMAP (implicit gaps).

---

## Part B — New Code for Next Steps (`run_part3.py`)

All Part 3 utilities live in **`run_part3.py`** (project root). They write under **`Part3_Output/`**.

### B.1 Commands

| Command | Purpose |
|---------|---------|
| `clean-gold` | Reads `Part2_Output/gold_standard.csv`, drops citation-like sentences per `;`, writes **`Part3_Output/gold_standard_cleaned.csv`**. |
| `semantic-compare` | P/R/F1 using **max(ROUGE-L F1, bag-of-words cosine)** between each pred–gold pair (credits some paraphrases). Optional `--threshold` (default 0.55). Writes **`Part3_Output/semantic_compare.txt`**. |
| `export-agreement` | Lists `chunk_id` where **gpt4o_mini, gpt_4o, and ollama** all have non-empty predictions → **`Part3_Output/high_confidence_chunks.csv`**. |
| `implicit-template --n 50` | First *n* gold `chunk_id`s with empty **`implicit_gap_sentence`** → **`Part3_Output/implicit_gold_template.csv`** for manual implicit labels. |
| `implicit-sample --n 50` | Same IDs plus **text excerpt** + filename → **`Part3_Output/implicit_annotation_sample.csv`** (for human implicit-gap annotation). |
| `ablation-commands` | Writes **`Part3_Output/ablation_commands.txt`** with example `run_part2.py` invocations (`--no-post-filter`, `--hybrid`). |
| `implicit-extract --chunk-id ID` | **Demo:** one-chunk **implicit** gap via OpenAI (needs `OPENAI_API_KEY`). Uses `IMPLICIT_SYSTEM_PROMPT` in `run_part3.py`. |
| `tabi-extract` | **Batch TABI** (Claim / Grounds / Warrant / Bucket) → **`--out`** (default **`Part3_Output/tabi_outputs.csv`**). Flags: **`--max-chunks`**, **`--chunk-ids-csv`**, **`--resume`**, **`--dedupe`**, **`--sleep`**. |
| `tabi-validate --input FILE` | Adds **`mnli_entailment_prob`** / **`mnli_entailment_pass`** (RoBERTa-MNLI; needs **`torch`**, **`transformers`**). Writes **`*_validated.csv`**. |

### B.2 Example shell session

```bash
cd "/Users/momoba/Desktop/Advanced ML Project "
.venv/bin/python run_part3.py clean-gold
.venv/bin/python run_part3.py semantic-compare --threshold 0.55
.venv/bin/python run_part3.py export-agreement
.venv/bin/python run_part3.py implicit-template --n 50
.venv/bin/python run_part3.py implicit-sample --n 50
.venv/bin/python run_part3.py ablation-commands

# Optional: implicit demo (paid API)
export OPENAI_API_KEY=sk-...
.venv/bin/python run_part3.py implicit-extract --chunk-id 21

# Full GAPMAP-style TABI batch (paid API — test with --max-chunks 20 first)
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o
.venv/bin/python run_part3.py tabi-extract --backend openai --max-chunks 20 --sleep 0.3

# Optional entailment pass (downloads RoBERTa-large-MNLI ~1.5GB on first run)
pip install torch transformers
.venv/bin/python run_part3.py tabi-validate --input Part3_Output/tabi_outputs.csv --threshold 0.4
```

### B.3 Ablation workflow (re-extraction)

`run_part2.py` already supports **`--no-post-filter`** and **`--hybrid`**. To compare:

1. Run extraction with one setting; **rename** the saved `predictions_*.csv` so it is not overwritten.
2. Run again with another flag combination (see `Part3_Output/ablation_commands.txt`).
3. Run `python run_part2.py --compare` (or evaluate against `gold_standard_cleaned.csv` by temporarily swapping filenames if you want a cleaned-gold experiment).

### B.4 Implicit gap direction (GAPMAP)

GAPMAP treats **implicit** gaps as inferable from discourse, not only from cue phrases \[1\]. `IMPLICIT_SYSTEM_PROMPT` in `run_part3.py` gives a minimal instruction set; **`implicit_annotation_sample.csv`** supports building 30–50 manual implicit labels, then you can extend `run_part3.py` or the notebook with a batch `implicit-extract` loop and evaluate analogously to explicit ROUGE.

For **structured** implicit extraction aligned with Salem et al., use **`tabi-extract`** (JSON **Claim / Grounds / Warrant / Bucket**, 3-shot in `TABI_SYSTEM_PROMPT`) and optionally **`tabi-validate`** for RoBERTa-MNLI entailment on **premise = grounds + warrant**, **hypothesis = claim**.

---

## Part C — Checklist (Part 3 completion)

- [ ] Run `clean-gold`; inspect `gold_standard_cleaned.csv`; optionally adopt as primary gold for one experiment.
- [ ] Run `semantic-compare`; append a short comparison paragraph to this report or to `Part2_Report.md`.
- [ ] Run `export-agreement`; report count of triple-agreement chunks.
- [ ] Fill `implicit_gold_template.csv` or `implicit_annotation_sample.csv` for a pilot; run `implicit-extract` or batch API calls.
- [ ] Execute at least one **ablation** (post-filter off and/or hybrid off); save metrics in `Part3_Output/`.
- [ ] **Optional — full GAPMAP extension:** expand PDFs → set **`GAPMAP_DATASET`** → run **`tabi-extract`** → **`tabi-validate`** → cite rows in your narrative (`Part E` below).

---

## Part E — Full GAPMAP Part 3 workflow (corpus + TABI batch + narrative)

**1. Corpus.** Put new PDFs in a project subfolder (any nested structure under it is fine). Point the loaders at it:

```bash
export GAPMAP_DATASET=Dataset_expanded   # relative to project root, or use an absolute path
```

`run_part2.py` (`load_articles`) reads all `**/*.pdf`, skips filenames containing `Editorial` or `Board`, and keeps articles with ≥500 words. Then **`python run_part2.py --annotation-only`** regenerates `chunks_for_annotation.csv` so chunk counts match the expanded corpus.

**2. TABI batch.** Run inference over chunks (cost scales with chunks × API):

```bash
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o
.venv/bin/python run_part3.py tabi-extract --backend openai --out Part3_Output/tabi_outputs.csv --sleep 0.25
```

Test paths without spending API credits: **`tabi-extract --dry-run --max-chunks 5 --out Part3_Output/tabi_outputs_sample.csv`** (writes placeholder rows; ~1 minute to load PDFs).

Use **`--max-chunks 50`** while debugging; **`--resume`** to continue after interruption or after a quota/rate-limit stop (**retries previously failed rows**); **`--chunk-ids-csv my_ids.csv`** to restrict to a topic subset; **`--dedupe`** to drop near-duplicate **claim** strings across chunks.

Local option: **`--backend ollama`** (requires `ollama serve` and **`OLLAMA_MODEL`**).

**3. Optional entailment layer** (GAPMAP-style numeric check). Install **`requirements_part3_optional.txt`**, then:

```bash
.venv/bin/python run_part3.py tabi-validate --input Part3_Output/tabi_outputs.csv --threshold 0.4
```

Produces **`tabi_outputs_validated.csv`** with **`mnli_entailment_prob`** and **`mnli_entailment_pass`**.

**4. Align the write-up.** In the Part 3 report, replace placeholder metrics with **row counts** and **tables aggregated from your CSV** (e.g., precision/recall/F1 only after you define **gold** triples on a held-out sample—`tabi-extract` alone does not compute F1). Point to **`Part3_Output/tabi_outputs.csv`** (and `*_validated.csv`) as the primary artifact.

**Recommended “best” final output (high-confidence set).** Export a conservative subset using MNLI + bucket:

```bash
.venv/bin/python run_part3.py tabi-high-confidence --mnli-threshold 0.6 --bucket more_probable --out Part3_Output/tabi_high_confidence_mnli06.csv
```

This gives a smaller list you can cite as “high-confidence implicit gaps” (and keep the full `tabi_outputs.csv` as the complete candidate set).

### Part E.6 Results from TABI + entailment validation (this repository)

After running TABI on the full economics corpus (**1,367 chunks**), we obtained:

- **TABI extraction output**: `Part3_Output/tabi_outputs.csv`  
  - **1,367** rows, **0** parse errors  
  - **1,361 / 1,367** chunks produced a non-`NONE` implicit-gap **Claim**
- **Entailment validation** (RoBERTa-MNLI, threshold **0.4**): `Part3_Output/tabi_outputs_validated.csv`  
  - **919 / 1,367** rows with `mnli_entailment_pass = True`
- **High-confidence implicit gaps** (recommended final set):  
  - MNLI ≥ **0.6** + `bucket=more_probable`: **842** rows → `Part3_Output/tabi_high_confidence_mnli06.csv`  
  - MNLI ≥ **0.7** + `bucket=more_probable`: **784** rows → `Part3_Output/tabi_high_confidence_mnli07.csv`

**Example high-confidence TABI outputs** (from the MNLI ≥ 0.7 set; `bucket=more_probable`):

- **Example 1** (chunk_id **270**, `Extreme-temperatures--Gender-differenc_2025_...pdf`, MNLI **0.994**)  
  - **Claim**: The specific mechanisms driving gender differences in well-being responses to high temperatures are unclear.  
  - **Grounds**: “the specific reasons for gender differences in well-being responses to high temperatures remain unclear”  
  - **Warrant**: The text explicitly states that the reasons for gender differences are not understood, indicating a gap in understanding the underlying mechanisms.

- **Example 2** (chunk_id **681**, `What-works-in-financial-education--Experime_2025_...pdf`, MNLI **0.993**)  
  - **Claim**: The impact of financial education on advanced financial concepts like credit and investment is underexplored.  
  - **Grounds**: “issues related to credit, investment, and specialized areas remain comparatively underexplored”  
  - **Warrant**: The text highlights a focus on foundational skills, suggesting a gap in understanding the effects of financial education on more advanced financial topics.

- **Example 3** (chunk_id **433**, `Drivers-of-tax-compliance--Survey-evidence_2025_...pdf`, MNLI **0.993**)  
  - **Claim**: The psychological mechanisms linking patriotic sentiments to tax compliance are underexplored.  
  - **Grounds**: “the psychological mechanisms linking patriotic sentiments to tax compliance remain underexplored”  
  - **Warrant**: The text explicitly states that while patriotism influences tax behavior, the underlying psychological processes are not well understood, indicating a gap in the research.

### Innovation & Failure Analysis (Part 3 rubric mapping)

This section explicitly addresses the Part 3 requirement: **(i) diagnose failures on the new data, (ii) propose + implement a fix, and (iii) justify it with results.**

- **Failure analysis (explicit pipeline):** `Part2_Output/error_analysis.md` shows that many “errors” are driven by **PDF artifacts** (citation fragments and broken lines) and **surface-form mismatch** (ROUGE penalizing correct paraphrases).  
  - *Example failure mode:* false negatives containing citation-only fragments like “Baillon et al., 2020”.

- **Fix 1 — Gold hygiene:** implemented `clean-gold` (`run_part3.py`) to remove citation-like junk from gold labels and write `Part3_Output/gold_standard_cleaned.csv`.  
  - *Justification:* removes evaluation noise that is not a model failure (it is a PDF extraction artifact).

- **Fix 2 — Metric limitation:** implemented `semantic-compare` to credit some paraphrases using **max(ROUGE-L, bag-of-words cosine)**, writing `Part3_Output/semantic_compare.txt`.  
  - *Justification:* improves interpretability of results when the model is “right in meaning” but differs lexically from the gold.

- **Failure analysis (implicit/TABI extension):** the main failure mode of raw implicit extraction is **over-generation** (the model can produce an implicit “gap” for almost any chunk, even when evidence is thin).  

- **Fix 3 — Calibrated high-confidence implicit gaps:** implemented `tabi-validate` (RoBERTa-MNLI entailment) and `tabi-high-confidence` exports to convert “many candidates” into a conservative set of text-supported implicit gaps:  
  - `Part3_Output/tabi_outputs_validated.csv` (entailment columns)  
  - `Part3_Output/tabi_high_confidence_mnli06.csv` (**842** rows, MNLI ≥ 0.6)  
  - `Part3_Output/tabi_high_confidence_mnli07.csv` (**784** rows, MNLI ≥ 0.7)  
  - *Justification:* this functions as a practical filter for implicit-gap quality in the absence of a full human implicit gold standard, mirroring GAPMAP’s emphasis on structured reasoning + validation for implicit inference.

**5. URLs / provenance.** List journal hubs and seed DOIs in **`Part3_Output/Appendix_A_Expanded_Corpus_URLs.md`** (or move into the PDF appendix).

---

## Comparison to Salem et al. (2025) — the original GAPMAP paper

Salem et al. introduce **GAPMAP**: explicit *and* implicit knowledge-gap extraction in **biomedical / policy** text, with **~1,500 documents** across **four datasets**, models from **OpenAI (e.g., GPT-4o, GPT-4o-mini, GPT-5)** and **open weights (Llama 3.x, Gemma 2)**, plus **TABI** for structured implicit-gap inference and a **full-manuscript pilot** with author surveys. Our repository **begins** from the **explicit-gap** slice on **economics** PDFs; **`tabi-extract` / `tabi-validate`** add an optional **TABI-aligned** implicit track for your own corpus and gold—still **not** identical to their biomedical benchmarks or author surveys.

**What aligns with GAPMAP (directly comparable in setup, not in absolute scores).**

| Design choice | GAPMAP (explicit, IPBES-style track) | This repository |
|---------------|--------------------------------------|-----------------|
| Chunking | ≤1,000 words, **sentence boundaries** | Same (`run_part2.py`, notebook) |
| Explicit-gap match metric | **ROUGE-L F1**, stemming, threshold **0.55** | Same (`run_part2.py --compare`) |
| Open vs closed models | Both families benchmarked | GPT-4o-mini, GPT-4o vs Ollama (Llama 3.2) |

**What we added to the pipeline (beyond GAPMAP’s described explicit extraction).** Salem et al. score **direct LLM outputs** against gold with ROUGE-L on **1k-word chunks**. They use Boguslav-style **ignorance cues** in **other** analyses (e.g., validating extra COVID predictions)—not the same as our stack. Items below are **our** extensions in **`run_part2.py`** / **`run_part3.py`**:

| Addition | Purpose |
|----------|---------|
| **Regex post-filter** (`filter_predictions`) | Drop LLM lines that do not match curated gap-like phrases → aligns predictions with phrase-based gold; **`--no-post-filter`** ablates it. |
| **Hybrid merge** (`--hybrid`, `rule_based_extract`) | Union of LLM sentences + pattern-based sentence scan on the chunk → recall boost. |
| **Citation skip in rule path** (`_is_citation_fragment`) | Reduce false rule hits from PDF citation fragments. |
| **Few-shot + verbatim-quote prompt** | Economics-specific examples and exclusions; matches surface-form evaluation. |
| **Part 3** (`clean-gold`, `semantic-compare`, `export-agreement`, implicit templates, etc.) | Gold hygiene, semantic-augmented metric, triple-model agreement lists, scaffolding for implicit labels—not in GAPMAP’s codebase narrative. |
| **`tabi-extract` / `tabi-validate`** | Batch **TABI** JSON quadruples + optional **RoBERTa-MNLI** check on your corpus (not their released biomedical gold). |

For **explicit** extraction on the **IPBES** corpus under **1,000-word chunks**, Salem et al. report (Table 3) ROUGE-L precision/recall/F1 such as **GPT-4o-mini ≈ 0.80 / 0.83 / 0.81**, **GPT-4o ≈ 0.87 / 0.65 / 0.74**, and **Llama-3.1-8B ≈ 0.78 / 0.56 / 0.65** (among others). Our **Journal of Behavioral and Experimental Economics** run on **93** manually annotated gold chunks—with **post-filter**, **hybrid** rule merge, and domain-specific writing—achieves ROUGE-L @ 0.55 of **0.852 / 0.909 / 0.880** (GPT-4o-mini), **0.915 / 0.888 / 0.902** (GPT-4o), and **0.745 / 0.872 / 0.803** (Ollama) — see `Part2_Output/comparison_results.txt`. **Semantic-augmented** scores in `Part3_Output/semantic_compare.txt` (max of ROUGE-L and bag-of-words cosine) are **0.717 / 0.900 / 0.670** F1 for the same three models — still **not** IPBES numbers, but closer to interpreting paraphrase.

### How well did we do relative to GAPMAP (what we can compare)

**Explicit (closest apples-to-apples):** We matched GAPMAP’s explicit evaluation recipe (1k-word chunks + ROUGE-L + threshold 0.55) and see the same high-level pattern (frontier closed models strong; open-weight local model weaker but viable). Absolute F1 is not directly comparable because the corpora and gold standards differ.

**Implicit (not apples-to-apples, but method-aligned):** GAPMAP evaluates implicit gaps against **their** manually annotated biomedical implicit datasets. We instead report **internal validation statistics** on our economics corpus: TABI produced **1,361/1,367** non-`NONE` claims with **0 parse errors**, and RoBERTa-MNLI entailment at threshold **0.4** passed **919/1,367** rows. We then exported conservative “high-confidence” subsets: **842** rows at MNLI ≥ **0.6** and **784** rows at MNLI ≥ **0.7** (both `bucket=more_probable`). These numbers should be interpreted as **coverage + confidence filtering**, not as accuracy/F1 against a human implicit gold standard.

### What we implemented that GAPMAP didn’t describe in their explicit benchmark

Beyond GAPMAP’s explicit-IPBES setup (LLM → ROUGE-L scoring), we added:

- **Phrase-pattern post-filter** (`filter_predictions`): align extracted explicit sentences with the gold vocabulary.
- **Hybrid explicit extraction** (`--hybrid`): union of LLM output with a rule-based sentence scan to boost recall.
- **Gold hygiene** (`clean-gold`): remove citation-like noise from gold labels (PDF artifact).
- **Semantic-augmented scoring** (`semantic-compare`): max(ROUGE-L, bag-of-words cosine) to credit paraphrases.
- **Agreement export** (`export-agreement`): “high-confidence” chunks where multiple models predict a gap.
- **Operational tooling**: `GAPMAP_DATASET` to swap corpora; Part 3 notebook (`Part3_GAPMAP_Extensions.ipynb`) to run and view all outputs.
- **Implicit extension utilities** not present in the paper’s explicit benchmark narrative: TABI batch extraction + entailment validation + **high-confidence export** (`tabi-high-confidence`).

**Why the headline F1 numbers should not be read as “better” or “worse” than Table 3.**

1. **Corpus and labels:** IPBES uses hundreds of labeled gap **statements** in structured biodiversity assessments; our gold is **manual** gap sentences on economics chunks (~93 positive chunks). Different density, style, and annotation rules change precision/recall tradeoffs.
2. **Pipeline:** We use a **phrase post-filter** and optional **hybrid** union with rule-based extraction to align with our rubric and gold; GAPMAP’s explicit IPBES experiment is a **straight LLM extraction** comparison (plus they study additional datasets such as COVID-19 “scientific challenges” with **different metrics**—e.g., cue-dictionary validation and accuracy—not the same ROUGE table).
3. **Models:** Our local **Llama 3.2** via Ollama is not the same checkpoint or scale as GAPMAP’s **Llama 3.3-70B**, **Llama-4-17B**, or **Gemma-2-9B**.
4. **Scope:** Salem et al. report implicit-gap benchmarks on **their** annotated biomedical corpora and **author surveys** on full manuscripts. Our **`tabi-extract`** / **`tabi-validate`** implement a **similar inference + entailment recipe** on **your** PDFs; numeric agreement with their Table 5 **still requires your own labeled sample**, not automatic from the batch CSV alone.

**Takeaway for cross-paper discussion:** We **inherit GAPMAP’s explicit-gap evaluation recipe** (chunking + ROUGE-L @ 0.55) and reproduce the **qualitative pattern** that **frontier closed models** (here GPT-4o) achieve **strong F1**, while **smaller open weights** remain **useful but weaker on precision**, consistent with GAPMAP’s discussion of open/closed parity on **lexically signaled** gaps. Any numeric side-by-side should be framed as **methodological alignment** and **directional** comparison, not a claim of beating or matching their published benchmarks on their datasets.

---

## Part D — References

1. Salem, N. M., White, E., Bada, M., & Hunter, L. (2025). *GAPMAP: Mapping Scientific Knowledge Gaps in Biomedical Literature Using Large Language Models.* arXiv:2510.25055. https://arxiv.org/html/2510.25055v1  

2. Lin, C.-Y. (2004). ROUGE. *WAS 2004.* https://aclanthology.org/W04-1013.pdf  

3. Boguslav, M. R., Cohen, K. B., & Hunter, L. (2023). *Journal of Biomedical Semantics*, 14, 11. https://doi.org/10.1186/s13326-023-00294-8  

---

*End of Part 3 report. Primary implementation file for new steps: **`run_part3.py`**.*
