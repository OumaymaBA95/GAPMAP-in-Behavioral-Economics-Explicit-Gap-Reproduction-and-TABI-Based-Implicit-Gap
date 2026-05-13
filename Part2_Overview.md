# Part 2: What This Pipeline Does

A plain-language guide to the explicit gap extraction pipeline for the GAPMAP project.

---

## The Big Picture

**Goal:** Automatically find sentences in your economics papers that say things like "we don't know yet" or "more research is needed" — i.e., **explicit knowledge gaps**.

---

## The Steps (In Order)

### 1. Load the PDFs
- Read your Journal of Behavioral and Experimental Economics PDFs from the `Dataset` folder
- Extract the text from each article

### 2. Chunk the Text
- Split each article into pieces of ~1,000 words
- Splits happen at sentence boundaries (no mid-sentence cuts)
- This matches GAPMAP's setup and keeps context intact for the model

### 3. Create a Gold Standard (You Do This Manually)
- For at least 50 chunks, you manually mark which sentences are explicit gaps
- Example: *"Further research is needed to assess long-term effects."*
- You save this as `gold_standard.csv`
- This is used later to measure how well the model performs

### 4. Ask the LLM to Extract Gaps
- For each chunk, we send the text to an LLM (e.g., GPT-4o-mini)
- The prompt asks it to list all explicit knowledge-gap sentences
- The model returns a list of such sentences per chunk
- We run many chunks in parallel to speed this up

### 5. Evaluate with ROUGE-L
- Compare the model's extracted sentences to your gold standard
- Use ROUGE-L F1 with stemming and a 0.55 threshold
- Compute precision, recall, and F1

### 6. Compare Models
- Run the same pipeline with another model (e.g., Llama)
- Compare which gaps each model finds and how they overlap

---

## Why This Matters for Your Project

- **Part 2 deliverable:** A Python notebook that reproduces GAPMAP's explicit-gap extraction and evaluation
- **Rubric:** You need ROUGE-L F1, 1,000-word chunking, a gold standard of ≥50 samples, and a comparison of at least one open and one closed model

---

## What the "Parallel" Change Does

| Before | After |
|--------|-------|
| Chunks processed one-by-one (chunk 1 → chunk 2 → chunk 3 …) | Several chunks processed at once (e.g., 10 at a time) |
| Slower | Faster |

The logic and outputs stay the same — it just finishes sooner.

---

## Quick Reference: Files

| File | Purpose |
|------|---------|
| `Part2_Explicit_Gap_Extraction.ipynb` | Main pipeline notebook |
| `Part2_Output/chunks_for_annotation.csv` | Template for manual gold annotations |
| `Part2_Output/gold_standard.csv` | Your completed annotations (chunk_id, gold_gap_sentences) |
| `Part2_Output/predictions_gpt4o_mini.csv` | Model extraction results |
