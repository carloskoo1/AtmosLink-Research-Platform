#!/usr/bin/env python3
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path("/home/carlos/Proyectos/EstacionMeteorologica")
OUT = ROOT / "Results/scientific_discovery/DISCOVERY-001/manuscript_figures"
OUT.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(10.8, 5.8))
ax.set_xlim(0, 12)
ax.set_ylim(0, 7)
ax.axis("off")

def box(x, y, w, h, text, face, edge="#243447", lw=1.5):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.04,rounding_size=0.08",
        facecolor=face, edgecolor=edge, linewidth=lw
    )
    ax.add_patch(patch)
    ax.text(x + w/2, y + h/2, text, ha="center", va="center",
            fontsize=9.2, color="#15202b", linespacing=1.25)
    return patch

def arrow(x1, y1, x2, y2, color="#36454f", style="-|>", dashed=False):
    patch = FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle=style,
        mutation_scale=12, linewidth=1.4, color=color,
        linestyle="--" if dashed else "-"
    )
    ax.add_patch(patch)
top = box(0.5, 5.25, 2.3, 1.0, "Telemetry + metadata\nQC and configuration", "#dbeafe")
cand = box(3.35, 5.25, 2.3, 1.0, "Candidate generation\nHuman or bounded LLM", "#ede9fe")
screen = box(6.2, 5.25, 2.3, 1.0, "Deterministic screening\nEvents, direction, multiplicity", "#dcfce7")
review = box(9.05, 5.25, 2.3, 1.0, "Human review + freeze\nRegistered hypothesis", "#fef3c7")

reject = box(5.95, 2.95, 2.8, 1.0, "SCREENED_OUT\nRetained as provenance", "#fee2e2", edge="#991b1b")
holdout = box(9.05, 2.95, 2.3, 1.0, "Protected validation\nNo adaptive reuse", "#e0f2fe", edge="#075985")
states = box(9.05, 0.75, 2.3, 1.0, "CONFIRMED / REJECTED /\nINCONCLUSIVE", "#f3f4f6")

ledger = box(0.5, 1.55, 3.6, 1.25,
             "Versioned audit trail\nProtocols, hashes, seeds, artifacts, claims",
             "#f8fafc")

arrow(2.8, 5.75, 3.35, 5.75)
arrow(5.65, 5.75, 6.2, 5.75)
arrow(8.5, 5.75, 9.05, 5.75)
arrow(7.35, 5.25, 7.35, 3.95, color="#991b1b")
arrow(10.2, 5.25, 10.2, 3.95)
arrow(10.2, 2.95, 10.2, 1.75)
arrow(4.1, 2.15, 5.95, 3.35, dashed=True)
arrow(4.1, 2.15, 9.05, 3.35, dashed=True)
ax.text(4.5, 6.65, "ASDE validity-constrained hypothesis-screening workflow",
        ha="center", va="center", fontsize=12.5, weight="bold")
ax.text(4.5, 4.75,
        "The language model may formulate or critique candidates; it cannot calculate evidence or change states.",
        ha="center", va="center", fontsize=8.7, color="#4b5563")
ax.text(0.55, 0.55,
        "Solid arrows: scientific-state transitions. Dashed arrows: versioned provenance links.",
        fontsize=8.3, color="#4b5563")

fig.tight_layout()
fig.savefig(OUT / "figure_asde_workflow.svg", bbox_inches="tight")
fig.savefig(OUT / "figure_asde_workflow.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print("ASDE_ARCHITECTURE_FIGURE_OK")
