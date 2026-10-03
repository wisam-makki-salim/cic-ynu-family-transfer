#!/usr/bin/env python3
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
df = pd.read_parquet(ROOT / "PILOT_06_COHORT_MANIFEST.parquet")
df = df[df.MalwareFamily.isin(["Mirai", "DarkNexus"])].copy()
df["target_darknexus"] = (df.MalwareFamily == "DarkNexus").astype(int)
df["start_epoch"] = pd.to_datetime(df.sar_start, utc=True).astype("int64") / 1e9

features = ["pcap_rows", "sar_rows", "strace_rows", "sar_span_seconds", "start_epoch"]
single_features = [["start_epoch"], ["pcap_rows"], ["strace_rows"]]

def fit_eval(cols, train, test):
    pipe = Pipeline([
        ("prep", ColumnTransformer([("num", Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), cols)])),
        ("clf", LogisticRegression(class_weight="balanced", max_iter=2000, random_state=17)),
    ])
    pipe.fit(train[cols], train.target_darknexus)
    prob = pipe.predict_proba(test[cols])[:, 1]
    pred = (prob >= 0.5).astype(int)
    return {
        "roc_auc": float(roc_auc_score(test.target_darknexus, prob)),
        "balanced_accuracy": float(balanced_accuracy_score(test.target_darknexus, pred)),
        "n_test": int(len(test)),
        "n_darknexus_test": int(test.target_darknexus.sum()),
    }

counts = pd.crosstab(df.Arch, df.MalwareFamily).to_dict(orient="index")
ranges = {}
for (arch, fam), g in df.groupby(["Arch", "MalwareFamily"]):
    ranges.setdefault(arch, {})[fam] = {
        "n": int(len(g)),
        "start_min": str(g.sar_start.min()),
        "start_max": str(g.sar_start.max()),
        "unique_dates": sorted(pd.to_datetime(g.sar_start, utc=True).dt.date.astype(str).unique().tolist()),
    }

folds = {}
for arch in sorted(df.Arch.unique()):
    train, test = df[df.Arch != arch], df[df.Arch == arch]
    folds[arch] = {"artifact_all": fit_eval(features, train, test)}
    for cols in single_features:
        folds[arch][cols[0]] = fit_eval(cols, train, test)

out = {
    "candidate": "Mirai_vs_DarkNexus_leave_one_architecture_out",
    "counts": counts,
    "collection_ranges": ranges,
    "artifact_only_folds": folds,
    "notes": [
        "Positive class is DarkNexus.",
        "Metrics are diagnostic leakage/validity tests, not claimed behavioral performance.",
        "Splits are by architecture and sampling unit is executable Hash.",
    ],
}
(ROOT / "PILOT_06_G4_REDESIGN_AUDIT_RESULTS.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))
