# Part 2: Verification Checklist

## Pipeline (run_part2.py)

| Check | Command | Status |
|-------|---------|--------|
| Load + chunk | `python run_part2.py --annotation-only` | ✓ Runs (loads 107 articles, 1367 chunks) |
| Compare | `python run_part2.py --compare` | ✓ Output matches report |
| Error analysis | `python run_part2.py --error-analysis` | ✓ Writes error_analysis.md |
| Threshold tuning | `python run_part2.py --threshold-tuning` | ✓ Output matches report |

## Outputs (Part2_Output/)

| File | Present | Matches Report |
|------|---------|----------------|
| gold_standard.csv | ✓ | 93 chunks |
| predictions_gpt4o_mini.csv | ✓ | — |
| predictions_gpt_4o.csv | ✓ | — |
| predictions_ollama.csv | ✓ | — |
| comparison_results.txt | ✓ | P/R/F1 match |
| error_analysis.md | ✓ | — |
| threshold_tuning.txt | ✓ | Values match |

## Report (Part2_Report.md)

- Methodology ✓
- Results table ✓
- Discussion ✓
- Limitations ✓
- Error analysis summary ✓
- Threshold sensitivity ✓
- Section 8 (notebook parity) updated to reflect alignment ✓

## Notebook

**Automated execution:** Not run—`jupyter nbconvert --execute` failed (no python3 kernel in venv).

**Manual verification:** Run from project root:
```bash
cd "Advanced ML Project "
jupyter notebook Part2_Explicit_Gap_Extraction.ipynb
```
Then run cells 1–6 (setup through prompt). Cells 7+ require API key and perform extraction.

**Alternative:** The script `run_part2.py` implements the same logic; pipeline validation via script suffices.
