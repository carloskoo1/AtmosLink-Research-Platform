#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
DIR=ROOT/"Results/scientific_discovery/DISCOVERY-001/v23_hidden_driver_gate_ablation"
m=pd.read_csv(DIR/"gate_ablation_metrics.csv",keep_default_na=False)

# Figure 1: null family-wise error rate
n=m[(m["mode"]=="null")&(m["metric"]=="library_wide_fwer")].copy()
n=n.set_index("method").reindex(["M0","M1","M2","M3"]).reset_index()
fig,ax=plt.subplots(figsize=(6.8,4.4))
yerr=[n["rate"]-pd.to_numeric(n["ci95_low"]),pd.to_numeric(n["ci95_high"])-n["rate"]]
ax.bar(range(len(n)),n["rate"],yerr=yerr,capsize=4)
ax.axhline(0.05,linestyle="--",linewidth=1)
ax.set_xticks(range(len(n)),["M0\nuncorrected","M1\nBonferroni","M2\n+ support","M3\n+ fold direction"])
ax.set_ylabel("Library-wide null FWER")
ax.set_ylim(0,0.27)
ax.grid(True,axis="y",alpha=.25)
fig.tight_layout()
fig.savefig(DIR/"figure_v23_null_fwer.svg")
fig.savefig(DIR/"figure_v23_null_fwer.png",dpi=300)
plt.close(fig)

# Figure 2: exclusive truth selection at 1 SD
x=m[(m["mode"]=="injected")&
    (pd.to_numeric(m["effect_sd"])==1.0)&
    (m["metric"]=="exclusive_truth_selected")].copy()
fig,ax=plt.subplots(figsize=(6.8,4.4))
for method,label in [("M0","M0 uncorrected"),("M1","M1/M2/M3 (identical)")]:
    g=x[x["method"]==method].copy()
    g["lag_num"]=pd.to_numeric(g["lag_min"])
    g=g.sort_values("lag_num")
    yerr=[g["rate"]-pd.to_numeric(g["ci95_low"]),pd.to_numeric(g["ci95_high"])-g["rate"]]
    ax.errorbar(g["lag_num"],g["rate"],yerr=yerr,marker="o",capsize=3,label=label)
ax.set_xlabel("Injected lag (min)")
ax.set_ylabel("Exclusive truth-selection rate")
ax.set_ylim(0,1.0)
ax.set_xticks([15,30,60])
ax.grid(True,alpha=.25)
ax.legend()
fig.tight_layout()
fig.savefig(DIR/"figure_v23_exclusive_truth_1sd.svg")
fig.savefig(DIR/"figure_v23_exclusive_truth_1sd.png",dpi=300)
plt.close(fig)

print("V23_FIGURES_OK")
