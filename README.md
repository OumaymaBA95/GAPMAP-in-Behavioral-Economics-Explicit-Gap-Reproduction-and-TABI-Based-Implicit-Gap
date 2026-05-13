# GAPMAP × Behavioral Economics

- **Project** — Reproduce GAPMAP-style explicit gap extraction ([Salem et al., arXiv:2510.25055](https://arxiv.org/abs/2510.25055)) on behavioral-economics text, plus a structured implicit-gap track (Claim / Grounds / Warrant) gated by RoBERTa-large-MNLI.
- **Corpus** — 107 JBEE papers → 1,367 sentence-aligned segments (~1,000 words max per segment).
- **Gold labels** — 93 segments annotated for explicit knowledge-gap sentences.
- **Explicit baselines** — GPT-4o, GPT-4o-mini, Llama 3.2 (Ollama), cue-phrase regex, post-filter / hybrid diagnostics in `Part2_Output/`.
- **Implicit outputs** — TABI-style CSVs and validation artifacts in `Part3_Output/`; corpus inventory paths in `Part3_Output/Appendix_A_Expanded_Corpus_URLs.md`.
- **Paper** — LaTeX in `Final_Paper/` (NeurIPS template); compile with `pdflatex` + `bibtex` (`Final_Paper/README.md`).
- **Talk** — `GAPMAP_Presentation (1) (1).pptx` plus `Speaker_Script.md`; run `./build_script_pdf.sh` for a local speaker PDF (ignored by git).
- **Runnable entry points** — `run_part2.py` and `run_part3.py` (`--help` in each).
- **Environment** — `python -m venv .venv` → `pip install -r requirements_part2.txt` → optional `pip install -r requirements_part3_optional.txt`.
- **Secrets** — Use `OPENAI_API_KEY` (etc.) via shell/env only — never paste keys into committed files or notebooks.
- **PDF corpus** — Not shipped (copyright/size); recreate `Dataset/` using the appendix file if you rerun end-to-end.
- **Citation** — `Final_Paper/references.bib` for BibTeX; cite GAPMAP as arXiv:2510.25055.
- **Credits** — Oumayma Ben Aoun, Chau Tran, Elise DeLeon.
- **Reuse** — Academic / coursework; do not redistribute Elsevier-hosted PDFs from this workflow.
