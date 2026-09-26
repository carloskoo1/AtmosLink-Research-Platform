#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
SRC=ROOT/"Results/scientific_discovery/DISCOVERY-001/v12_audit/familywise_recovery.csv"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/v12_audit"
df=pd.read_csv(SRC)

fig,ax=plt.subplots(figsize=(7.2,4.4))
for lag,g in df.groupby("lag_min"):
    g=g.sort_values("effect_sd")
    yerr=[g["familywise_recovery_rate"]-g["ci95_low"],
          g["ci95_high"]-g["familywise_recovery_rate"]]
    ax.errorbar(g["effect_sd"],g["familywise_recovery_rate"],
                yerr=yerr,marker="o",capsize=3,label=f"Lag {int(lag)} min")
ax.set_xlabel("Injected RF effect magnitude (robust SD)")
ax.set_ylabel("Family-wise recovery rate")
ax.set_ylim(-0.02,1.05)
ax.grid(True,alpha=.25)
ax.legend()
fig.tight_layout()
fig.savefig(OUT/"figure_familywise_recovery.svg")
fig.savefig(OUT/"figure_familywise_recovery.png",dpi=300)
plt.close(fig)

surf=pd.read_csv(OUT/"detection_surface.csv")
for effect in [0.5,1.0]:
    p=surf[surf["effect_sd"]==effect].pivot(
        index="lag_min",columns="horizon_min",values="recovery_rate"
    ).sort_index()
    fig,ax=plt.subplots(figsize=(5.8,4.2))
    im=ax.imshow(p.values,aspect="auto",vmin=0,vmax=1)
    ax.set_xticks(range(len(p.columns)),[str(int(x)) for x in p.columns])
    ax.set_yticks(range(len(p.index)),[str(int(x)) for x in p.index])
    ax.set_xlabel("Analysis horizon (min)")
    ax.set_ylabel("Injected lag (min)")
    ax.set_title(f"Recovery surface, effect = {effect:.1f} robust SD")
    for i in range(p.shape[0]):
        for j in range(p.shape[1]):
            ax.text(j,i,f"{p.iloc[i,j]:.2f}",ha="center",va="center")
    fig.colorbar(im,ax=ax,label="Recovery rate")
    fig.tight_layout()
    tag=str(effect).replace(".","p")
    fig.savefig(OUT/f"figure_detection_surface_{tag}sd.svg")
    fig.savefig(OUT/f"figure_detection_surface_{tag}sd.png",dpi=300)
    plt.close(fig)

abl=ROOT/"Results/scientific_discovery/DISCOVERY-001/v14_audit_ablation/ablation_summary.csv"
if abl.exists():
    a=pd.read_csv(abl)
    f=a[a["metric"]=="false_positive_rate"].copy()
    order=["M0_naive_uncorrected","M1_bonferroni_only","M2_bonferroni_support","M3_ASDE_full"]
    f=f.set_index("method").reindex(order).reset_index()
    fig,ax=plt.subplots(figsize=(7.0,4.4))
    yerr=[f["rate"]-f["ci95_low"],f["ci95_high"]-f["rate"]]
    ax.bar(range(len(f)),f["rate"],yerr=yerr,capsize=4)
    ax.axhline(0.05,linestyle="--",linewidth=1)
    ax.set_xticks(range(len(f)),["Naive","Bonferroni","Bonf.+support","ASDE full"])
    ax.set_ylabel("Empirical family-wise false-positive rate")
    ax.set_ylim(0,0.12)
    ax.grid(True,axis="y",alpha=.25)
    fig.tight_layout()
    out=ROOT/"Results/scientific_discovery/DISCOVERY-001/v14_audit_ablation"
    fig.savefig(out/"figure_ablation_false_positive.svg")
    fig.savefig(out/"figure_ablation_false_positive.png",dpi=300)
    plt.close(fig)
