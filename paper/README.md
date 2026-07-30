# Manuscript

The manuscript is grounded in the repository's committed implementation and stored results.

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
