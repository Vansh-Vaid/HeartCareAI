# HeartCareAI IEEE LaTeX Paper

This folder contains an IEEE conference-style LaTeX source project for the HeartCareAI application.

## Files

- `main.tex` - full paper source
- `references.bib` - BibTeX references
- `figures/` - architecture diagram and model/chart figures
- `figures/screenshots/` - real HeartCareAI website screenshots and extra placeholder slots
- `appendix/extra_screenshots.md` - screenshot checklist and notes

## Compile

Use a LaTeX distribution that includes `IEEEtran`:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

or:

```bash
latexmk -pdf main.tex
```

## Important Notes

HeartCareAI is described as a screening support and educational research application. The paper intentionally avoids claiming that it is a diagnostic medical device.

The author block has been filled with the contributor details. The paper already includes the uploaded website screenshots for the main, login, screening, result, report, overview, and doctors pages.

## Originality Note

The manuscript is written in original, project-specific wording and uses citations for external ideas, tools, and reporting guidance. No IEEE template sample paragraphs have been copied. A plagiarism score cannot be guaranteed across all private checkers, so run the final PDF through your institution's preferred checker before submission and review any highlighted source matches.
