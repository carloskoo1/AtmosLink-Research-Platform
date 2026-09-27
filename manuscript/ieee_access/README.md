# ASDE IEEE Access package

This directory is the reproducible IEEE Access rendering of
`docs/IEEE_ASDE_FULL_DRAFT_V2.md`.

## Template provenance

- Official IEEE Access LaTeX template revision: 2026-05-13
- Source: https://ieeeaccess.ieee.org/wp-content/uploads/2026/05/ACCESS_latex_template_20260513-1-1.zip
- ZIP SHA-256: `60c7efc9db8ac9e8bdb31c550ad4e03cb6f258a878ececc0bc690b6203e45a67`
- The official class, bibliography style, logos, and required fonts are vendored here unchanged.

## Rebuild

Requirements: Python environment at `venv/`, pdfLaTeX, BibTeX, Poppler,
and the packages `cite`, `preprint`, and `courier`.

```bash
scripts/build_ieee_asde_package.sh
```

Alternative executable paths can be supplied through `ASDE_PYTHON`,
`ASDE_PDFLATEX`, and `ASDE_BIBTEX`.

The generator records the SHA-256 of Draft v2 inside the generated TeX.
The verifier checks source concordance, structural counts, citation closure,
figure presence, PDF text, page count, and layout warnings. The blank DOI is
intentional because IEEE assigns it after acceptance. Submission readiness
remains governed by the separate release checklist and is not implied by a
successful package build.
