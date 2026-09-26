#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT=Path("/home/carlos/Proyectos/EstacionMeteorologica")
SRC=ROOT/"Results/scientific_discovery/DISCOVERY-001/v21_end_to_end_audit/end_to_end_metrics.csv"
OUT=ROOT/"Results/scientific_discovery/DISCOVERY-001/v21_end_to_end_audit"
d=pd.read_csv(SRC)

agg=d[(d.scope=="aggregate")&(d.effect_sd==1.0)&
      (d.metric.isin(["truth_selected","unique_top1_correct"]))].copy()

fig,ax=plt.subplots(figsize=(7.0,4.4))
for metric,g in agg.groupby("metric"):
    g=g.sort_values("lag_min")
    yerr=[g["rate"]-g["ci95_low"],g["ci95_high"]-g["rate"]]
    label="Exact driver selected" if metric=="truth_selected" else "Unique top-1 ranking"
    ax.errorbar(g["lag_min"],g["rate"],yerr=yerr,marker="o",capsize=3,label=label)
ax.set_xlabel("Injected lag (min)")
ax.set_ylabel("Recovery rate")
ax.set_ylim(0,1.05)
ax.grid(True,alpha=.25)
ax.legend()
fig.tight_layout()
fig.savefig(OUT/"figure_hidden_driver_recovery_1sd.svg")
fig.savefig(OUT/"figure_hidden_driver_recovery_1sd.png",dpi=300)
plt.close(fig)

per=d[(d.scope=="per_driver")&(d.effect_sd==1.0)&
      (d.metric=="truth_selected")].copy()
p=per.pivot(index="truth_driver",columns="lag_min",values="rate")
fig,ax=plt.subplots(figsize=(7.4,4.8))
im=ax.imshow(p.values,aspect="auto",vmin=0,vmax=1)
ax.set_xticks(range(len(p.columns)),[str(int(x)) for x in p.columns])
short=[x.replace("_local_"," ").replace("_avg_"," ").replace("__"," ") for x in p.index]
ax.set_yticks(range(len(p.index)),short)
ax.set_xlabel("Injected lag (min)")
ax.set_title("Exact-driver selection at 1.0 robust SD")
for i in range(p.shape[0]):
    for j in range(p.shape[1]):
        ax.text(j,i,f"{p.iloc[i,j]:.2f}",ha="center",va="center")
fig.colorbar(im,ax=ax,label="Selection rate")
fig.tight_layout()
fig.savefig(OUT/"figure_hidden_driver_per_driver_1sd.svg")
fig.savefig(OUT/"figure_hidden_driver_per_driver_1sd.png",dpi=300)
plt.close(fig)
