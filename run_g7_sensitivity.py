#!/usr/bin/env python3
"""Date-matched MIPSEL sensitivity analysis for Pilot 06."""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, balanced_accuracy_score, f1_score, matthews_corrcoef, recall_score, roc_auc_score

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "g7_outputs"
SEED = 20261001

manifest = pd.read_parquet(ROOT / "PILOT_06_COHORT_MANIFEST.parquet")
manifest["date"] = pd.to_datetime(manifest["sar_start"], utc=True).dt.date.astype(str)
keep = manifest[(manifest.Arch.str.lower() == "mipsel") & manifest.MalwareFamily.isin(["Mirai", "DarkNexus"]) & (manifest.date == "2025-06-29")][["Hash", "date"]]
pred = pd.read_parquet(OUT / "PILOT_06_G7_PREDICTIONS.parquet")
pred = pred[(pred.Arch == "mipsel")].merge(keep, on="Hash", how="inner", validate="many_to_one")
pred["y"] = (pred.MalwareFamily == "DarkNexus").astype(int)

def metrics(g):
    y=g.y.to_numpy(); p=g.prob_darknexus.to_numpy(); t=float(g.threshold.iloc[0]); yh=p>=t
    return {
        "n": len(g), "n_darknexus": int(y.sum()), "n_mirai": int((1-y).sum()), "threshold": t,
        "macro_f1": f1_score(y,yh,average="macro",zero_division=0),
        "darknexus_recall": recall_score(y,yh,zero_division=0),
        "balanced_accuracy": balanced_accuracy_score(y,yh), "mcc": matthews_corrcoef(y,yh),
        "pr_auc_darknexus": average_precision_score(y,p), "roc_auc": roc_auc_score(y,p),
    }

rows=[]
for (fs,model),g in pred.groupby(["feature_set","model"],sort=False):
    base={"feature_set":fs,"model":model,**metrics(g)}
    rng=np.random.default_rng(SEED); boot=[]
    i0=np.where(g.y.to_numpy()==0)[0]; i1=np.where(g.y.to_numpy()==1)[0]
    for _ in range(500):
        idx=np.r_[rng.choice(i0,len(i0),True),rng.choice(i1,len(i1),True)]
        boot.append(metrics(g.iloc[idx]))
    for key in ["macro_f1","darknexus_recall","balanced_accuracy","mcc","pr_auc_darknexus","roc_auc"]:
        base[key+"_ci_low"],base[key+"_ci_high"]=np.quantile([b[key] for b in boot],[.025,.975])
    rows.append(base)

out=pd.DataFrame(rows).sort_values("macro_f1",ascending=False)
out.to_csv(OUT / "PILOT_06_G7_MIPSEL_DATE_MATCHED.csv",index=False)
print(keep.merge(manifest[["Hash","MalwareFamily"]],on="Hash").MalwareFamily.value_counts().to_string())
print(out[["feature_set","model","n","n_darknexus","macro_f1","darknexus_recall","pr_auc_darknexus","roc_auc"]].to_string(index=False))
