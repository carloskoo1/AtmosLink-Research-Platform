#!/usr/bin/env python3
from pathlib import Path
import hashlib
import re
import shutil
import pypandoc

ROOT = Path("/home/carlos/Proyectos/EstacionMeteorologica")
SOURCE = ROOT / "docs/IEEE_ASDE_FULL_DRAFT_V2_ES.md"
BIB = ROOT / "docs/IEEE_ASDE_REFERENCES_WORKING.bib"
OUT = ROOT / "manuscript/ieee_access"
TEX = OUT / "asde_ieee_access_es.tex"

FIGURES = {
    "1": "figures/fig1_asde_workflow.png",
    "2": "figures/fig2_known_driver_recovery.png",
    "3": "figures/fig3_hidden_driver_recovery.png",
    "4": "figures/fig4_gate_ablation.png",
    "5": "figures/fig5_driver_heterogeneity.png",
}

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def normalize(text):
    return (text.replace("\u2011", "-").replace("\u2013", "--")
            .replace("\u2014", "---").replace("\u2212", "-"))

def pandoc_fragment(text):
    return pypandoc.convert_text(
        normalize(text), "latex",
        format="markdown+raw_tex+tex_math_dollars",
        extra_args=["--wrap=none"],
    ).strip()
def citation_repl(match):
    keys = [x.strip() for x in match.group(1).split(",")]
    return "\\cite{" + ",".join(keys) + "}"

def convert_citations(text):
    key = r"[A-Z0-9][A-Z0-9-]+-\d{4}"
    return re.sub(r"\[((?:" + key + r")(?:,\s*" + key + r")*)\]",
                  citation_repl, text)

def cell_tex(value):
    value = normalize(value.strip())
    value = re.sub(r"\*\*(.*?)\*\*", r"\1", value)
    replacements = {
        "&": r"\&", "%": r"\%", "#": r"\#", "_": r"\_",
        "ρ": r"$\rho$", "≥": r"$\geq$", "±": r"$\pm$",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value

def convert_tables(text):
    lines = text.splitlines()
    out = []
    i = 0
    table_no = 0
    while i < len(lines):
        m = re.fullmatch(r"\*\*(?:TABLE|CUADRO) ([IVX]+)\*\*", lines[i].strip())
        if not m:
            out.append(lines[i])
            i += 1
            continue
        numeral = m.group(1)
        table_no += 1
        title = lines[i + 1].strip().strip("*")
        j = i + 2
        while j < len(lines) and not lines[j].strip():
            j += 1
        rows = []
        while j < len(lines) and lines[j].lstrip().startswith("|"):
            rows.append([x.strip() for x in lines[j].strip().strip("|").split("|")])
            j += 1
        header = rows[0]
        data = rows[2:]
        ncol = len(header)
        if ncol <= 3:
            spec = r">{\raggedright\arraybackslash}X " * ncol
        else:
            spec = r">{\raggedright\arraybackslash}X " + (
                r">{\centering\arraybackslash}X " * (ncol - 1)
            )
        latex = [
            r"\begin{table*}[t]",
            r"\caption{" + cell_tex(title) + "}",
            r"\label{tab:" + numeral.lower() + "}",
            r"\centering",
            r"\scriptsize",
            r"\setlength{\tabcolsep}{3pt}",
            r"\renewcommand{\arraystretch}{1.15}",
            r"\begin{tabularx}{\textwidth}{" + spec.strip() + "}",
            r"\toprule",
            " & ".join(cell_tex(x) for x in header) + r" \\",
            r"\midrule",
        ]
        latex.extend(" & ".join(cell_tex(x) for x in row) + r" \\"
                     for row in data)
        latex.extend([
            r"\bottomrule",
            r"\end{tabularx}",
            r"\end{table*}",
        ])
        out.extend(["", *latex, ""])
        i = j
    if table_no != 10:
        raise RuntimeError(f"Expected 10 tables, converted {table_no}")
    return "\n".join(out)

def convert_figures(text):
    pattern = re.compile(
        r"!\[[^]]*\]\([^)]+\)\n\n"
        r"\*\*Fig\.\s*(\d+)\.\*\*\s*([^\n]+)"
    )
    seen = []
    def repl(match):
        number, caption = match.group(1), normalize(match.group(2))
        seen.append(number)
        path = FIGURES[number]
        return "\n".join([
            r"\begin{figure*}[t]",
            r"\centering",
            rf"\includegraphics[width=0.94\textwidth]{{{path}}}",
            rf"\caption{{{cell_tex(caption)}}}",
            rf"\label{{fig:{number}}}",
            r"\end{figure*}",
        ])
    converted = pattern.sub(repl, text)
    if seen != ["1", "2", "3", "4", "5"]:
        raise RuntimeError(f"Unexpected figure sequence: {seen}")
    return converted

def prepare_body(source):
    body = re.search(
        r"# I\. Introducción\n(.*?)\n# Mapa clave de referencia de trabajo",
        source, re.S,
    ).group(1)
    body = re.sub(
        r"^> \*\*Submission metadata still requiring author confirmation:.*$",
        "", body, flags=re.M,
    )
    body = "# Introducción\n\n" + body
    body = re.sub(r":\n(?=- )", ":\n\n", body)
    body = re.sub(r"^# [IVX]+\. ", "# ", body, flags=re.M)
    body = re.sub(r"^## [A-Z]\. ", "## ", body, flags=re.M)
    body = body.replace(
        "# Disponibilidad de datos y códigos",
        "# Disponibilidad de datos y código {.unnumbered}",
    ).replace(
        "# Reconocimiento y Divulgación Generativa-AI",
        "# Agradecimientos y declaración sobre IA generativa {.unnumbered}",
    )
    body = convert_citations(body)
    body = convert_tables(body)
    body = convert_figures(body)
    latex = pandoc_fragment(body)
    latex = re.sub(
        r"(\\section\{Introducción\}\\label\{[^}]+\}\n\n)Los ",
        r"\1\\PARstart{L}{os }", latex, count=1,
    )
    latex = latex.replace(
        "CANDIDATE -\\textgreater{} SCREENED\\_OUT\n\nor\n\n"
        "CANDIDATE -\\textgreater{} HUMAN\\_REVIEWED -\\textgreater{} HYPOTHESIS "
        "-\\textgreater{} FROZEN -\\textgreater{} VALIDATING -\\textgreater{} "
        "CONFIRMED \\textbar{} REJECTED \\textbar{} INCONCLUSIVE.",
        r"\begin{center}\small\texttt{CANDIDATE} $\rightarrow$ \texttt{SCREENED\_OUT}\\[2pt]"
        r"\textit{or}\\[2pt]\texttt{CANDIDATE} $\rightarrow$ \texttt{HUMAN\_REVIEWED} "
        r"$\rightarrow$ \texttt{HYPOTHESIS} $\rightarrow$ \texttt{FROZEN}\\"
        r"$\rightarrow$ \texttt{VALIDATING} $\rightarrow$ "
        r"\{\texttt{CONFIRMED},\texttt{REJECTED},\texttt{INCONCLUSIVE}\}\end{center}",
    )
    latex = latex.replace("safety/feasibility", r"safety/\allowbreak feasibility")
    latex = latex.replace(r"PRESS\_JUMP", r"PRESS\_\allowbreak JUMP")
    return latex

def extract_biographies(source):
    block = source.split("# Biografías de los autores", 1)[1].strip()
    matches = list(re.finditer(
        r"\*\*([^*]+)\*\*\s*(.*?)(?=\n\n\*\*|\Z)",
        block, re.S,
    ))
    if len(matches) != 5:
        raise RuntimeError(f"Expected 5 biographies, found {len(matches)}")
    result = []
    for match in matches:
        name = pandoc_fragment(match.group(1)).replace("\n", " ")
        bio = pandoc_fragment(match.group(2))
        result.append(
            "\n".join([
                rf"\begin{{IEEEbiographynophoto}}{{{name}}}",
                bio,
                r"\end{IEEEbiographynophoto}",
            ])
        )
    return "\n\n".join(result)
def build():
    source = SOURCE.read_text(encoding="utf-8")
    abstract = re.search(
        r"## Resumen\n(.*?)\n\n## Términos índice", source, re.S
    ).group(1).strip()
    keywords = re.search(
        r"## Términos índice\n(.*?)\n\n# I\.", source, re.S
    ).group(1).strip().rstrip(".")
    body = prepare_body(source)
    biographies = extract_biographies(source)

    abstract_tex = pandoc_fragment(abstract)
    keywords_tex = pandoc_fragment(keywords)
    digest = sha256(SOURCE)

    header = rf"""\documentclass{{ieeeaccess}}
\def\thevol{{14}}
\def\theyear{{2026}}
% Official IEEE Access template revision: 2026-05-13.
% Generated from docs/IEEE_ASDE_FULL_DRAFT_V2_ES.md
% Working translation; the English manuscript remains the submission master.
% Source SHA-256: {digest}
\usepackage[utf8]{{inputenc}}
\usepackage{{cite}}
\usepackage{{amsmath,amssymb,amsfonts}}
\usepackage{{graphicx}}
\usepackage{{textcomp}}
\usepackage{{array,booktabs,tabularx}}
\usepackage{{url}}
\usepackage{{bm}}
\providecommand{{\tightlist}}{{\setlength{{\itemsep}}{{0pt}}\setlength{{\parskip}}{{0pt}}}}
\makeatletter
\AtBeginDocument{{\DeclareMathVersion{{bold}}
\SetSymbolFont{{operators}}{{bold}}{{T1}}{{times}}{{b}}{{n}}
\SetSymbolFont{{NewLetters}}{{bold}}{{T1}}{{times}}{{b}}{{it}}
\SetMathAlphabet{{\mathrm}}{{bold}}{{T1}}{{times}}{{b}}{{n}}
\SetMathAlphabet{{\mathit}}{{bold}}{{T1}}{{times}}{{b}}{{it}}
\SetMathAlphabet{{\mathbf}}{{bold}}{{T1}}{{times}}{{b}}{{n}}
\SetMathAlphabet{{\mathtt}}{{bold}}{{OT1}}{{pcr}}{{b}}{{n}}
\SetSymbolFont{{symbols}}{{bold}}{{OMS}}{{cmsy}}{{b}}{{n}}
\renewcommand\boldmath{{\@nomath\boldmath\mathversion{{bold}}}}}}
\makeatother
\begin{{document}}
\title{{ASDE: Un flujo de trabajo auditable para el cribado de hipótesis en telemetría ambiental--radio de larga duración}}
"""
    authors = r"""\author{\uppercase{Carlos Jes\'us Koo Labr\'in}\authorrefmark{1},
\uppercase{V\'ictor S\'anchez C\'aceres}\authorrefmark{1},
\uppercase{N\'estor E. Mu\~noz Abanto}\authorrefmark{1},
\uppercase{Marisol Tapia Romero}\authorrefmark{1}, AND
\uppercase{Carlos Enrique Koo Bartra}\authorrefmark{2}}
\address[1]{Universidad Nacional de Cajamarca, Cajamarca, Per\'u (correo electrónico: ckoo@unc.edu.pe)}
\address[2]{Universidad Privada del Norte, Trujillo, Per\'u}
\markboth{Koo Labr\'in \headeretal: ASDE: Flujo auditable para el cribado de hipótesis}
{Koo Labr\'in \headeretal: ASDE: Flujo auditable para el cribado de hipótesis}
\corresp{Autor de correspondencia: Carlos Jes\'us Koo Labr\'in (correo electrónico: ckoo@unc.edu.pe).}
"""
    front = "\n".join([
        authors,
        r"\history{TRADUCCIÓN DE TRABAJO --- NO DESTINADA A ENVÍO EDITORIAL. La versión inglesa es el manuscrito fuente oficial.}",
        r"\begin{abstract}",
        abstract_tex,
        r"\end{abstract}",
        r"\begin{keywords}",
        keywords_tex,
        r"\end{keywords}",
        r"\doi{}",  # DOI is assigned by IEEE after acceptance.
        r"\titlepgskip=-21pt",
        r"\maketitle",
    ])
    tail = "\n".join([
        r"\bibliographystyle{IEEEtran}",
        r"\bibliography{references}",
        biographies,
        r"\EOD",
        r"\end{document}",
        "",
    ])
    OUT.mkdir(parents=True, exist_ok=True)
    TEX.write_text(header + front + "\n" + body + "\n" + tail,
                   encoding="utf-8")
    shutil.copyfile(BIB, OUT / "references.bib")
    print(f"IEEE_ASDE_TEX_OK source_sha256={digest}")
    print(f"tex={TEX}")
if __name__ == "__main__":
    build()
