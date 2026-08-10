# Manuscript

The manuscript is grounded in the repository's committed implementation and stored results.

Current reported experiment: 6{,}000 base-regime simulations (200 seeds, \(N\in\{10,30,50,100,200\}\)),
six-class classifier, 276 real baseline-regime segments (374-segment annotation corpus including 98
transition intervals). Optional transition generation adds 30{,}000 synthetic \texttt{X\_to\_Y} clips.

Compile from this directory:

```bash
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

Before submission, replace the bracketed placeholders in `main.tex`, add complete provenance and a
permanent identifier for the real trajectory data, confirm author contributions/funding/competing
interests, and archive an exact software environment.

The confusion-matrix figures are loaded from `../results/` when present.
