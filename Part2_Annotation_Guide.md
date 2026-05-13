# Part 2: Gold Standard Annotation Guide

We need to manually annotate **at least 50 chunks** with explicit knowledge-gap sentences. This guide explains how.

---

## Step 1: Open the Template

Open `Part2_Output/chunks_for_annotation.csv` in Excel, Google Sheets, or any spreadsheet editor.

---

## Step 2: What Counts as an Explicit Gap?

An **explicit knowledge gap** is a sentence or short phrase where the authors **directly state** that something is unknown, missing, or needs more research.

### ✅ Include (examples)

| Phrase / pattern | Example |
|------------------|---------|
| "remains unknown" | *It remains unknown whether long-term effects persist.* |
| "it is unclear" | *It is unclear whether these findings generalize.* |
| "further research is needed" | *Further research is needed to assess scalability.* |
| "limited evidence" | *There is limited evidence on the durability of interventions.* |
| "no study has" | *No study has evaluated this in field settings.* |
| "notable gaps remain" | *Notable gaps remain in the literature.* |
| "future work should" | *Future work should examine cultural differences.* |
| "we lack data on" | *We lack data on long-term outcomes.* |
| Hedging | *May lead to unintended consequences.* |

### ❌ Exclude

- General background (e.g., "Financial literacy is important")
- Statements of what the paper *did* find
- Implicit gaps (things you infer but authors didn't say)

---

## Step 3: How to Annotate

1. Read the `text_preview` for each chunk.
2. Identify **all** sentences that explicitly state a knowledge gap.
3. In the `gold_gap_sentences` column, list them **separated by semicolons (;)**

### Example

**Chunk text (excerpt):**  
*"...in our experiment, it remains unclear whether individuals experience cognitive dissonance as a result of the treatments. Future work should examine this in field settings."*

**gold_gap_sentences:**  
`It remains unclear whether individuals experience cognitive dissonance as a result of the treatments; Future work should examine this in field settings`

---

## Step 4: Save as Gold Standard

1. Keep columns: `chunk_id`, `gold_gap_sentences`
2. Save as `Part2_Output/gold_standard.csv`
3. For chunks with **no** explicit gaps, leave `gold_gap_sentences` empty (or write `NONE`)

---

## Step 5: Minimum Requirement

- The template includes **all chunks from all articles** (~1,367 total)
- **At least 50 chunks** must have at least one gap sentence for evaluation
- You can annotate more for a stronger evaluation

---

## Quick Checklist

- [ ] Opened `chunks_for_annotation.csv`
- [ ] Annotated ≥50 chunks
- [ ] Used semicolons to separate multiple gaps per chunk
- [ ] Saved as `gold_standard.csv` in `Part2_Output/`
