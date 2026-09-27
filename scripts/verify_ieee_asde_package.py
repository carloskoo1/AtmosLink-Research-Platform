#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/IEEE_ASDE_FULL_DRAFT_V2.md"
PKG = ROOT / "manuscript/ieee_access"
TEX = PKG / "asde_ieee_access.tex"
BIB = PKG / "references.bib"
PDF = PKG / "asde_ieee_access.pdf"
LOG = PKG / "asde_ieee_access.log"

EXPECTED = {
    "tables": 10,
    "figures": 5,
    "biographies": 5,
    "references": 31,
}
ERRORS: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        ERRORS.append(message)


def command_output(*args: str) -> str:
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT)
    except (OSError, subprocess.CalledProcessError) as exc:
        ERRORS.append(f"command failed: {' '.join(args)}: {exc}")
        return ""


def main() -> int:
    for path in (SOURCE, TEX, BIB, PDF, LOG):
        require(path.is_file(), f"missing required file: {path.relative_to(ROOT)}")
    if ERRORS:
        return finish()

    source = SOURCE.read_text(encoding="utf-8")
    tex = TEX.read_text(encoding="utf-8")
    bib = BIB.read_text(encoding="utf-8")
    log = LOG.read_text(encoding="utf-8", errors="replace")

    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    require(f"% Source SHA-256: {digest}" in tex, "TeX/source SHA-256 mismatch")
    require(tex.count(r"\begin{table*}") == EXPECTED["tables"], "table count mismatch")
    require(tex.count(r"\begin{figure*}") == EXPECTED["figures"], "figure count mismatch")
    require(
        tex.count(r"\begin{IEEEbiographynophoto}") == EXPECTED["biographies"],
        "biography count mismatch",
    )

    cite_keys = set()
    for group in re.findall(r"\\cite\{([^}]+)\}", tex):
        cite_keys.update(key.strip() for key in group.split(","))
    bib_keys = set(re.findall(r"^@[A-Za-z]+\{([^,]+),", bib, re.M))
    require(len(bib_keys) == EXPECTED["references"], "bibliography entry count mismatch")
    require(not (cite_keys - bib_keys), f"undefined citation keys: {sorted(cite_keys - bib_keys)}")
    require(not (bib_keys - cite_keys), f"uncited bibliography keys: {sorted(bib_keys - cite_keys)}")

    for match in re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", tex):
        require((PKG / match).is_file(), f"missing figure asset: {match}")

    abstract = re.search(r"## Abstract\n(.*?)\n\n## Index Terms", source, re.S)
    abstract_words = len(re.findall(r"\b[\w'-]+\b", abstract.group(1))) if abstract else 0
    require(150 <= abstract_words <= 250, f"abstract has {abstract_words} words")
    require(not re.search(r"\b(?:TODO|TBD|FIXME)\b", tex), "placeholder token in TeX")
    require("Citation `" not in log, "undefined citation reported by LaTeX")
    require("Reference `" not in log, "undefined reference reported by LaTeX")
    require("There were undefined references" not in log, "undefined references remain")
    paragraph_overfull = re.findall(
        r"Overfull \\hbox \([^)]*\) in paragraph at lines ([0-9-]+)", log
    )
    require(
        all(lines == "48--48" for lines in paragraph_overfull),
        f"content-level overfull box remains at lines: {paragraph_overfull}",
    )

    pdfinfo = command_output("pdfinfo", str(PDF))
    pages_match = re.search(r"^Pages:\s+(\d+)", pdfinfo, re.M)
    pages = int(pages_match.group(1)) if pages_match else 0
    require(1 <= pages <= 20, f"unexpected page count: {pages}")

    text = command_output("pdftotext", str(PDF), "-")
    required_pdf_text = [
        "ASDE: An Auditable Workflow",
        "CARLOS JESÚS KOO LABRÍN",
        "VÍCTOR SÁNCHEZ CÁCERES",
        "NÉSTOR E. MUÑOZ ABANTO",
        "MARISOL TAPIA ROMERO",
        "CARLOS ENRIQUE KOO BARTRA",
        "ACKNOWLEDGMENT AND GENERATIVE-AI DISCLOSURE",
    ]
    for token in required_pdf_text:
        require(token in text, f"expected text absent from PDF: {token}")

    print(f"source_sha256={digest}")
    print(f"abstract_words={abstract_words}")
    print(f"tables={tex.count(r'\begin{table*}')}")
    print(f"figures={tex.count(r'\begin{figure*}')}")
    print(f"references={len(bib_keys)}")
    print(f"biographies={tex.count(r'\begin{IEEEbiographynophoto}')}")
    print(f"pages={pages}")
    return finish()


def finish() -> int:
    if ERRORS:
        print("IEEE_ASDE_PACKAGE_FAIL", file=sys.stderr)
        for error in ERRORS:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("IEEE_ASDE_PACKAGE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
