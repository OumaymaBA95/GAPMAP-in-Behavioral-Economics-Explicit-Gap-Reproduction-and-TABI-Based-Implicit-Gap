# Part 2: Next Steps Checklist

Use this checklist to complete Part 2 of your GAPMAP project.

---

## ✅ Done

- [x] Pipeline created (load PDFs, chunk, extract, evaluate)
- [x] Pipeline now uses all 107 articles (all Dataset subfolders)
- [x] Chunks generated (1,367 total, all in annotation template)
- [x] Annotation template saved: `Part2_Output/chunks_for_annotation.csv`
- [x] Gold standard created (93 chunks, rule-based): `Part2_Output/gold_standard.csv`
- [x] Extractions run: GPT-4o-mini, GPT-4o, Ollama (llama3.2)
- [x] Model comparison: P/R/F1 + overlap table
- [x] Progress report: `Part2_Report.md`

---

## 📋 Your Tasks

### 1. Annotate the Gold Standard

- **Auto-annotate** (rule-based, no API): `python annotate_gold_standard.py` → creates `gold_standard.csv` with 93 chunks
- **Regenerate template** (if needed): `python run_part2.py --annotation-only`
- **File:** `Part2_Output/chunks_for_annotation.csv`
- **Guide:** See `Part2_Annotation_Guide.md`
- **Requirement:** Annotate at least 50 chunks with explicit gap sentences
- **Save as:** `Part2_Output/gold_standard.csv` (columns: `chunk_id`, `gold_gap_sentences`)

### 2. Set Your API Key (FREE or Paid)

**FREE — Google Gemini (no credit card):**
```bash
export GEMINI_API_KEY=your-key
```
Get a free key at: https://aistudio.google.com/apikey

**Paid — OpenAI:**
```bash
export OPENAI_API_KEY=sk-your-key-here
```

Or add the key in the notebook API key cell before running extraction.

### 3. Run the Notebook

1. Open `Part2_Explicit_Gap_Extraction.ipynb` in Jupyter
2. Run cells 1–4 (setup, load PDFs, chunk, create template)
3. Run the **GPT extraction** cell (Section 6) — uses parallel API calls
4. Run the **evaluation** cell (Section 9) — computes P/R/F1

### 4. (Optional) Add Llama for Model Comparison

- Install Ollama locally and run `ollama run llama3.1`, or
- Use HuggingFace Inference API with an HF token
- Uncomment and run the Llama extraction cell
- Run the model overlap cell (Section 10)

### 5. Prepare Progress Report ✅

- [x] `Part2_Report.md` — methodology, P/R/F1, overlap table, discussion
- [x] `Part2_Output/comparison_results.txt` — full comparison output

---

## Part 3 (Report 3 — extensions)

- **`Part3_Report.md`** — Full summary of completed work **and** new code / next steps.
- **`run_part3.py`** — Part 3 CLI: `clean-gold`, `semantic-compare`, `export-agreement`, `implicit-template`, `implicit-sample`, `ablation-commands`, `implicit-extract`.
- Linked from the end of `Part2_Report.md`.

---

## File Reference

| File | Purpose |
|------|---------|
| `Part2_Report.md` | **Part 2 progress report (deliverable)** |
| `Part3_Report.md` | **Part 3 / Report 3 — improvements & roadmap** |
| `run_part2.py` | Main pipeline script |
| `Part2_Explicit_Gap_Extraction.ipynb` | Notebook version |
| `Part2_Output/chunks_for_annotation.csv` | Template to annotate |
| `Part2_Output/gold_standard.csv` | Gold annotations (93 chunks) |
| `Part2_Output/predictions_gpt4o_mini.csv` | GPT-4o-mini output |
| `Part2_Output/predictions_gpt_4o.csv` | GPT-4o output |
| `Part2_Output/predictions_ollama.csv` | Ollama (llama3.2) output |
| `Part2_Output/comparison_results.txt` | Model comparison output |
| `Part2_Annotation_Guide.md` | How to annotate |
| `Part2_Overview.md` | What the pipeline does |
