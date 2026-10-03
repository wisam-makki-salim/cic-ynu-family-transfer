#!/usr/bin/env python3
"""Paired executable-level bootstrap contrasts for Pilot 06 G8."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'g7_outputs'; SEED=20261001; B=2000
p=pd.read_parquet(OUT/'PILOT_06_G7_PREDICTIONS.parquet')
p=p[p.model=='random_forest'].copy()
base=p[p.feature_set=='strace'][['Hash','Arch','MalwareFamily','prob_darknexus','threshold']].rename(columns={'prob_darknexus':'p_base','threshold':'t_base'})
contrasts={}
for alt in ['fusion_all','fusion_minus_sar','fusion_minus_pcap']:
    q=p[p.feature_set==alt][['Hash','Arch','prob_darknexus','threshold']].rename(columns={'prob_darknexus':'p_alt','threshold':'t_alt'})
    d=base.merge(q,on=['Hash','Arch'],validate='one_to_one')
    d['y']=(d.MalwareFamily=='DarkNexus').astype(int)
    rng=np.random.default_rng(SEED); fold_obs={}; boot_means=[]
    for arch,g in d.groupby('Arch'):
        b=f1_score(g.y,g.p_base>=g.t_base,average='macro',zero_division=0)
        a=f1_score(g.y,g.p_alt>=g.t_alt,average='macro',zero_division=0)
        fold_obs[arch]={'strace_macro_f1':float(b),'alternative_macro_f1':float(a),'delta_alt_minus_strace':float(a-b)}
    for _ in range(B):
        ds=[]
        for arch,g in d.groupby('Arch'):
            y=g.y.to_numpy(); i0=np.where(y==0)[0]; i1=np.where(y==1)[0]
            idx=np.r_[rng.choice(i0,len(i0),True),rng.choice(i1,len(i1),True)]
            s=g.iloc[idx]
            b=f1_score(s.y,s.p_base>=s.t_base,average='macro',zero_division=0)
            a=f1_score(s.y,s.p_alt>=s.t_alt,average='macro',zero_division=0)
            ds.append(a-b)
        boot_means.append(float(np.mean(ds)))
    obs=float(np.mean([v['delta_alt_minus_strace'] for v in fold_obs.values()]))
    contrasts[alt]={'mean_delta_alt_minus_strace':obs,'bootstrap_95_ci':[float(x) for x in np.quantile(boot_means,[.025,.975])],
                    'probability_delta_gt_zero':float(np.mean(np.array(boot_means)>0)),'folds':fold_obs}
(OUT/'PILOT_06_G8_PAIRED_CONTRASTS.json').write_text(json.dumps(contrasts,indent=2),encoding='utf-8')
print(json.dumps(contrasts,indent=2))
