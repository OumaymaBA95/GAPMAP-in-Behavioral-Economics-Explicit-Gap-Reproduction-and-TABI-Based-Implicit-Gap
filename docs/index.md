---
layout: default
title: GAPMAP × Behavioral Economics
---

# GAPMAP in behavioral economics — explicit-gap reproduction & TABI implicit gaps

Course project rebuilding the explicit-gap extraction pipeline from [GAPMAP](https://arxiv.org/abs/2510.25055) (Salem et al., 2025) on **107** articles from the *Journal of Behavioral and Experimental Economics*, plus an extension using **structured implicit-gap prompts** validated with RoBERTa-MNLI.

## Key artifacts (in this repository)

| What | Where |
|------|--------|
| Final paper (LaTeX + figures + BibTeX) | `Final_Paper/` — see `Final_Paper/README.md` for build |
| Compiled paper PDF | `Final_Paper/Final Report.pdf` |
| Speaker script | `Speaker_Script.md` (PDF: run `./build_script_pdf.sh`) |
| Corpus inventory (paths; PDFs not in repo) | `Part3_Output/Appendix_A_Expanded_Corpus_URLs.md` |
| Evaluation outputs | `Part2_Output/`, `Part3_Output/` CSVs and logs |
| Scripts | `run_part2.py`, `run_part3.py`, `annotate_gold_standard.py`, etc. |

## Reproduce locally

1. Clone the repo. **Do not expect `Dataset/`** — JBEE PDFs are not redistributed; use the appendix inventory to source or rebuild the corpus.
2. Create a virtualenv and install from `requirements_part2.txt` (and optional `requirements_part3_optional.txt` as needed).
3. Set API keys via **environment variables** only (never commit keys). See docstrings in `run_part2.py` / `run_part3.py`.
4. Build the paper from `Final_Paper/` as described in `Final_Paper/README.md`.

## Citation

Use the BibTeX in `Final_Paper/references.bib` for GAPMAP and related work.
