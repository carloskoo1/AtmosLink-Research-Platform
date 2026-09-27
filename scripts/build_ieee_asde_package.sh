#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/manuscript/ieee_access"
PYTHON="${ASDE_PYTHON:-$ROOT/venv/bin/python}"
PDFLATEX="${ASDE_PDFLATEX:-pdflatex}"
BIBTEX="${ASDE_BIBTEX:-bibtex}"

command -v "$PDFLATEX" >/dev/null || {
  echo "ERROR: pdfLaTeX is required by the official IEEE Access class." >&2
  exit 2
}
command -v "$BIBTEX" >/dev/null || {
  echo "ERROR: BibTeX is required." >&2
  exit 2
}

"$PYTHON" "$ROOT/scripts/build_ieee_asde_latex.py"
(
  cd "$OUT"
  "$PDFLATEX" -interaction=nonstopmode -halt-on-error asde_ieee_access.tex
  "$BIBTEX" asde_ieee_access
  "$PDFLATEX" -interaction=nonstopmode -halt-on-error asde_ieee_access.tex
  "$PDFLATEX" -interaction=nonstopmode -halt-on-error asde_ieee_access.tex
)
"$PYTHON" "$ROOT/scripts/verify_ieee_asde_package.py"
