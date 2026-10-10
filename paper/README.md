# Paper

**An Empty Region of Technical Strategy Space: 18,765 Pre-Registered Variants
Across Cryptocurrency and FX**

## Regenerating every number

```bash
cd /path/to/sweep-registry
python3 paper/analysis.py
```

Writes to `paper/build/`:

| file | contents |
|---|---|
| `stats.txt` | every figure quoted in the paper, labelled |
| `tableA1.tex` | all scored sweeps |
| `tableA2.tex` | variant distributions |
| `tableA3.tex` | cost sensitivity |
| `fig1.pdf` | distribution of variant Sharpe ratios by sweep |

Nothing is hard-coded. Sweep set, family labels, market assignment and every
statistic are derived from `sweeps/*/preregistration.json`, `result.json` and
`diagnostics.json`. Add, void or re-score a sweep and the outputs change.

`--no-figure` skips the plot if matplotlib is unavailable.

## Building the PDF

```bash
cd paper
cp build/*.tex build/fig1.pdf .
pdflatex sweep-registry-paper.tex
pdflatex sweep-registry-paper.tex    # twice, for the longtable layout
```

## Checking the paper against the registry

`stats.txt` is the audit trail. Any figure in the text should appear there
with the same value. The ones most worth checking:

- variants enumerated 18,765 / scored 17,946
- 27 of 29 sweeps below chance expectation, sign test p = 1.624e-06
- median minimum detectable Sharpe 3.4918
- 16 of 26 sweeps with negative median gross Sharpe
- kurtosis underestimated in 29 of 29, median factor 354
- spearman(kurtosis, DSR) = −0.786

If the script and the text disagree, the script is right.

## Status

Preprint. Not peer reviewed. An AI assistant was used for drafting and
editing; all data collection, code, analysis and conclusions are the author's
own.
