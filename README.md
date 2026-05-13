# GAPMAP × Behavioral Economics

Reproduction of the **explicit knowledge-gap extraction** pipeline from [GAPMAP](https://arxiv.org/abs/2510.25055) (Salem et al., 2025) on behavioral-economics articles, plus a **structured implicit-gap** extension (Claim / Grounds / Warrant) with **RoBERTa-large-MNLI** entailment filtering.

## Highlights

| Topic | Detail |
|-------|--------|
| **Corpus** | 107 research articles (*Journal of Behavioral and Experimental Economics*), chunked into 1,367 sentence-aligned segments (≤ ~1,000 words each) |
| **Gold labels** | 93 segments manually annotated for explicit gap sentences |
| **Models (explicit)** | GPT-4o, GPT-4o-mini, Llama 3.2 (via Ollama), plus a cue-phrase / regex baseline |
| **Implicit track** | TABI-style structured outputs → MNLI validation → high-confidence candidate set |
| **Write-up** | NeurIPS-style LaTeX in [`Final_Paper/`](Final_Paper/) — compiled PDF: `Final_Paper/Final Report.pdf` |
| **Slides & script** | `GAPMAP_Presentation (1) (1).pptx`, [`Speaker_Script.md`](Speaker_Script.md) — PDF via [`build_script_pdf.sh`](build_script_pdf.sh) |
| **Paper build** | See [`Final_Paper/README.md`](Final_Paper/README.md). Rebuild from `main.tex` before submission; bundled PDF may lag the latest `.tex`. |

## Repository layout

| Topic | Detail |
|-------|--------|
| [`Final_Paper/`](Final_Paper/) | `main.tex`, `references.bib`, figures (`bootstrap_f1.pdf`, `fp_patterns.pdf`), style file |
| [`Part2_Output/`](Part2_Output/) | Gold standard, predictions, bootstrap CIs, ablation logs |
| [`Part3_Output/`](Part3_Output/) | TABI / MNLI outputs, corpus appendix (paths/metadata only — see Dataset below) |
| [`docs/`](docs/) | GitHub Pages copy (`index.md`) |
| **Root** | `run_part2.py`, `run_part3.py`, notebooks, `requirements_*.txt`, helper scripts |

## Dataset

| Topic | Detail |
|-------|--------|
| **Committed?** | **No.** JBEE PDFs are not included (copyright / repo size). |
| **Manifest** | Full inventory: [`Part3_Output/Appendix_A_Expanded_Corpus_URLs.md`](Part3_Output/Appendix_A_Expanded_Corpus_URLs.md) (BibTeX keys, years, slugs, local paths). |
| **Rebuild** | Use that file and the listed journal hubs to assemble a local `Dataset/` folder if rerunning pipelines. |

## Quick start

**Navigate to your clone.**

```bash
cd path/to/your/clone/of/this/repo
```

**Create a virtual environment and install dependencies.**

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements_part2.txt
pip install -r requirements_part3_optional.txt
```

**Configure API keys (environment only — never commit keys).**

```bash
export OPENAI_API_KEY="sk-..."
# Optional: Gemini or Ollama — see docstrings in run_part2.py
```

**Run the explicit-gap pipeline** (needs `Dataset/` with PDFs).

```bash
python run_part2.py --help
```

**Run Part 3** (extensions / implicit track).

```bash
python run_part3.py --help
```

**Rebuild the presenter handout PDF** (output is gitignored).

```bash
chmod +x build_script_pdf.sh
./build_script_pdf.sh
```

**Build the final paper from LaTeX.**

```bash
cd Final_Paper
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

## GitHub Pages

| Topic | Detail |
|-------|--------|
| **Enable** | Repo **Settings → Pages → Deploy from branch** |
| **Source** | Branch `main`, folder `/docs` |
| **Content** | [`docs/index.md`](docs/index.md) |

## Citation

| Topic | Detail |
|-------|--------|
| **BibTeX** | Use [`Final_Paper/references.bib`](Final_Paper/references.bib) |
| **GAPMAP** | Salem, N. M., White, E., Bada, M., & Hunter, L. (2025). [GAPMAP: Mapping Scientific Knowledge Gaps in Biomedical Literature Using Large Language Models](https://arxiv.org/abs/2510.25055). *arXiv:2510.25055.* |

## Authors & use

| Topic | Detail |
|-------|--------|
| **Team** | Oumayma Ben Aoun, Chau Tran, Elise DeLeon |
| **License** | Unspecified; academic / educational use |
| **Note** | Do not redistribute Elsevier-hosted PDFs from this workflow |
