# GAPMAP × Behavioral Economics

Reproduction of the **explicit knowledge-gap extraction** pipeline from [GAPMAP](https://arxiv.org/abs/2510.25055) (Salem et al., 2025) on behavioral-economics articles, plus a **structured implicit-gap** extension (Claim / Grounds / Warrant) with **RoBERTa-large-MNLI** entailment filtering.

---

## Highlights

| Item | Detail |
|------|--------|
| **Corpus** | 107 research articles (*Journal of Behavioral and Experimental Economics*), chunked into 1,367 sentence-aligned segments (≤≈1,000 words each) |
| **Gold labels** | 93 segments manually annotated for explicit gap sentences |
| **Models (explicit)** | GPT-4o, GPT-4o-mini, Llama 3.2 (via Ollama), plus a cue-phrase / regex baseline |
| **Implicit track** | TABI-style structured outputs → MNLI validation → high-confidence candidate set |
| **Write-up** | NeurIPS-style LaTeX in [`Final_Paper/`](Final_Paper/) → compiled PDF as `Final_Paper/Final Report.pdf` |
| **Slides & script** | `GAPMAP_Presentation (1) (1).pptx`, [`Speaker_Script.md`](Speaker_Script.md) (PDF via [`build_script_pdf.sh`](build_script_pdf.sh)) |

> **Paper PDF:** build from LaTeX (see [`Final_Paper/README.md`](Final_Paper/README.md)) — the bundled `Final Report.pdf` may lag the latest `.tex`; recompile before submission.

---

## Repository layout

| Path | Contents |
|------|----------|
| [`Final_Paper/`](Final_Paper/) | `main.tex`, `references.bib`, figures (`bootstrap_f1.pdf`, `fp_patterns.pdf`), style file |
| [`Part2_Output/`](Part2_Output/) | Gold standard, predictions, bootstrap CIs, ablation logs |
| [`Part3_Output/`](Part3_Output/) | TABI / MNLI outputs, corpus appendix (**paths only**, see below) |
| [`docs/`](docs/) | Minimal site copy for GitHub Pages (`index.md`) |
| Root | `run_part2.py`, `run_part3.py`, notebooks, requirements, auxiliary scripts |

---

## Dataset (`Dataset/` — not committed)

Journal PDFs are **not included** (copyright / size). A full manifest of BibTeX keys, years, slugs, and local paths lives in:

**[`Part3_Output/Appendix_A_Expanded_Corpus_URLs.md`](Part3_Output/Appendix_A_Expanded_Corpus_URLs.md)**

Use that inventory and the journal hubs listed there if you want to rebuild the corpus locally.

---

## Quick start

```bash
cd "/Users/momoba/Desktop/Advanced ML Project "   # note trailing space in folder name if you kept it

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements_part2.txt
# Optional Part 3 extras:
pip install -r requirements_part3_optional.txt
```

Set API keys **only via environment variables** (never commit them):

```bash
export OPENAI_API_KEY="sk-..."     # explicit / implicit OpenAI-backed runs
# Optional: Gemini or Ollama — see docstrings in run_part2.py
```

Explicit-gap pipeline (needs `Dataset/` with PDFs):

```bash
python run_part2.py --help
```

Part 3 extensions / implicit track:

```bash
python run_part3.py --help
```

Rebuild the presenter handout PDF:

```bash
chmod +x build_script_pdf.sh   # once
./build_script_pdf.sh          # writes Speaker_Script.pdf (ignored by git)
```

Build the **final paper**:

```bash
cd Final_Paper
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

(details in [`Final_Paper/README.md`](Final_Paper/README.md))

---

## GitHub Pages

If Pages is enabled with **Deploy from branch → `main` → `/docs`**, [`docs/index.md`](docs/index.md) is rendered as the project landing page.

---

## Citation

Use the bibliography in [`Final_Paper/references.bib`](Final_Paper/references.bib). Primary reference for the reproduced framework:

> Salem, N. M., White, E., Bada, M., & Hunter, L. (2025). [GAPMAP: Mapping Scientific Knowledge Gaps in Biomedical Literature Using Large Language Models](https://arxiv.org/abs/2510.25055). arXiv:2510.25055.

---

## Authors

Course group project — **Oumayma Ben Aoun**, **Chau Tran**, **Elise DeLeon**.

License: unspecified; academic / educational use. Do not redistribute Elsevier-hosted PDFs from this workflow.
