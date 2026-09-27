#!/usr/bin/env python3
from pathlib import Path
import re, sys

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
DRAFT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/"docs/IEEE_ASDE_FULL_DRAFT_V0.md"
BIB=ROOT/"docs/IEEE_ASDE_REFERENCES_WORKING.bib"

draft=DRAFT.read_text()
bib=BIB.read_text()

# Draft v0 uses bracketed symbolic keys before final IEEE numbering.
used=set()
for block in re.findall(r"\[([^\]]+)\]",draft):
    for token in block.split(","):
        key=token.strip()
        if re.fullmatch(r"[A-Z0-9][A-Z0-9-]+-\d{4}",key):
            used.add(key)

defined=set(re.findall(r"@\w+\{([^,]+),",bib))
missing=sorted(used-defined)
unused=sorted(defined-used)

print("used_keys",len(used))
print("defined_keys",len(defined))
print("missing",missing)
print("unused",unused)

if missing:
    raise SystemExit(1)
print("REFERENCE_KEY_COVERAGE_PASS")
