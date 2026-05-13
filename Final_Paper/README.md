## Final Paper (LaTeX → PDF)

This folder contains a NeurIPS-style LaTeX final paper for Part 3.

### Compile

From the project root:

```bash
cd "Final_Paper"
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Output: `main.pdf`

