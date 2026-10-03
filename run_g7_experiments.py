#!/usr/bin/env python3
"""Pilot 06 G7: executable-level, architecture-held-out baselines."""

from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    f1_score,
    matthews_corrcoef,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "g7_outputs"
OUT.mkdir(exist_ok=True)
SEED = 20261001
ARCHES = ["arm", "mips", "mipsel", "x86"]
PATHS = {
    "arm": {
        "pcap": ROOT / "arm/Parquet Format/pcap.parquet",
        "sar": ROOT / "arm/Parquet Format/sar.parquet",
        "strace": ROOT / "arm/Parquet Format/strace.parquet",
    },
    "mips": {
        "pcap": ROOT / "upload/pcap (1).parquet",
        "sar": ROOT / "upload/sar (1).parquet",
        "strace": ROOT / "upload/strace (1)(1).parquet",
    },
    "mipsel": {
        "pcap": ROOT / "upload/pcap (2).parquet",
        "sar": ROOT / "upload/sar (2).parquet",
        "strace": ROOT / "upload/strace (2).parquet",
    },
    "x86": {
        "pcap": ROOT / "x86/pcap.parquet",
        "sar": ROOT / "x86/sar.parquet",
        "strace": ROOT / "x86/strace.parquet",
    },
}
ID = {"Hash", "MalwareFamily", "Arch", "timestamp", "interval"}
MALFORMED_SYSCALLS = {
    "Call_fc", "Call_g", "Call_getd", "Call_ioct", "Call_r", "Call_re",
    "Call_s", "Call_tim", "Call_rt_si", "Call_setso", "Call_wri", "Call_umount",
}


def numeric_columns(path: Path) -> set[str]:
    schema = pq.ParquetFile(path).schema_arrow
    return {
        f.name for f in schema
        if f.name not in ID and (pa.types.is_integer(f.type) or pa.types.is_floating(f.type))
    }


def common_columns(modality: str) -> list[str]:
    cols = set.intersection(*(numeric_columns(PATHS[a][modality]) for a in ARCHES))
    if modality == "strace":
        cols = {c for c in cols if c.startswith("Call_") and c not in MALFORMED_SYSCALLS}
    return sorted(cols)


def aggregate_one(path: Path, modality: str, cols: list[str], arch: str) -> pd.DataFrame:
    """Stream selected columns and aggregate by executable without row-count features."""
    cache = OUT / f"features_v2_robust_{arch}_{modality}.parquet"
    if cache.exists():
        return pd.read_parquet(cache)

    pf = pq.ParquetFile(path)
    wanted = ["Hash", "MalwareFamily", *cols]
    if modality != "strace":
        frame = pq.read_table(path, columns=wanted).to_pandas()
        frame = frame[frame["MalwareFamily"].isin(["Mirai", "DarkNexus"])]
        frame[cols] = frame[cols].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
        grp = frame.groupby(["Hash", "MalwareFamily"], sort=False, observed=True)[cols]
        med = grp.median().add_suffix("__median")
        q25 = grp.quantile(0.25).add_suffix("__q25")
        q75 = grp.quantile(0.75).add_suffix("__q75")
        z = pd.concat([med, q25, q75], axis=1)
        z.columns = [f"{modality}__{c}" for c in z.columns]
        out = z.reset_index()
        out["Arch"] = arch
        out.to_parquet(cache, index=False)
        return out

    pieces = []
    batch_size = 200_000
    for batch in pf.iter_batches(batch_size=batch_size, columns=wanted):
        frame = batch.to_pandas()
        frame = frame[frame["MalwareFamily"].isin(["Mirai", "DarkNexus"])]
        if frame.empty:
            continue
        # Partial sufficient statistics. Sum/sumsq/min/max merge exactly across batches.
        values = frame[cols].apply(pd.to_numeric, errors="coerce")
        keyed = pd.concat([frame[["Hash", "MalwareFamily"]].reset_index(drop=True), values.reset_index(drop=True)], axis=1)
        grp = keyed.groupby(["Hash", "MalwareFamily"], sort=False, observed=True)
        sums = grp[cols].sum(min_count=1)
        sums.columns = [f"strace__{c}__sum" for c in cols]
        pieces.append(sums.reset_index())

    allp = pd.concat(pieces, ignore_index=True)
    group = allp.groupby(["Hash", "MalwareFamily"], sort=False, observed=True)
    z = group.sum(min_count=1)
    denom = z.sum(axis=1).replace(0, np.nan)
    z = z.div(denom, axis=0)
    z.columns = [c.replace("__sum", "__relative_frequency") for c in z.columns]
    out = z.reset_index()
    out["Arch"] = arch
    out.to_parquet(cache, index=False)
    return out


def build_features() -> tuple[pd.DataFrame, dict]:
    schemas = {m: common_columns(m) for m in ["pcap", "sar", "strace"]}
    schema_report = {m: {"n_common": len(v), "columns": v} for m, v in schemas.items()}
    (OUT / "feature_schema.json").write_text(json.dumps(schema_report, indent=2), encoding="utf-8")
    arch_frames = []
    for arch in ARCHES:
        mods = [aggregate_one(PATHS[arch][m], m, schemas[m], arch) for m in schemas]
        merged = mods[0]
        for nxt in mods[1:]:
            merged = merged.merge(nxt, on=["Hash", "MalwareFamily", "Arch"], how="inner", validate="one_to_one")
        arch_frames.append(merged)
        print(f"aggregated {arch}: {merged.shape}", flush=True)
    full = pd.concat(arch_frames, ignore_index=True)
    full["y"] = (full["MalwareFamily"] == "DarkNexus").astype(int)
    full.to_parquet(OUT / "PILOT_06_G7_FEATURE_MATRIX_ROBUST.parquet", index=False)
    return full, schema_report


def metric_dict(y, p, threshold):
    pred = (p >= threshold).astype(int)
    result = {
        "macro_f1": f1_score(y, pred, average="macro", zero_division=0),
        "darknexus_recall": recall_score(y, pred, pos_label=1, zero_division=0),
        "balanced_accuracy": balanced_accuracy_score(y, pred),
        "mcc": matthews_corrcoef(y, pred),
        "pr_auc_darknexus": average_precision_score(y, p),
        "roc_auc": roc_auc_score(y, p),
        "threshold": threshold,
        "n": len(y),
        "n_darknexus": int(np.sum(y)),
    }
    return {k: float(v) if isinstance(v, (float, np.floating)) else v for k, v in result.items()}


def make_model(kind: str, param: float):
    if kind == "logistic":
        model = LogisticRegression(C=param, class_weight="balanced", max_iter=4000, solver="liblinear", random_state=SEED)
        return Pipeline([
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=False)),
            ("variance", VarianceThreshold(0.0)),
            ("scale", RobustScaler()),
            ("model", model),
        ])
    model = RandomForestClassifier(
        n_estimators=300, max_features="sqrt", min_samples_leaf=int(param),
        class_weight="balanced_subsample", n_jobs=-1, random_state=SEED,
    )
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median", keep_empty_features=False)),
        ("variance", VarianceThreshold(0.0)),
        ("model", model),
    ])


def tune(df, features, held_out, kind):
    train_arches = [a for a in ARCHES if a != held_out]
    params = [0.01, 0.1, 1.0] if kind == "logistic" else [1, 5]
    best = None
    for param in params:
        oof = []
        for inner_hold in train_arches:
            tr = df[df.Arch.isin([a for a in train_arches if a != inner_hold])]
            va = df[df.Arch == inner_hold]
            model = make_model(kind, param)
            model.fit(tr[features], tr.y)
            p = model.predict_proba(va[features])[:, 1]
            oof.append(pd.DataFrame({"y": va.y.to_numpy(), "p": p, "Arch": inner_hold}))
        oof = pd.concat(oof, ignore_index=True)
        for threshold in np.linspace(0.05, 0.95, 91):
            scores = [f1_score(g.y, g.p >= threshold, average="macro", zero_division=0) for _, g in oof.groupby("Arch")]
            score = float(np.mean(scores))
            candidate = (score, -abs(threshold - 0.5), -float(param), float(param), float(threshold))
            if best is None or candidate > best:
                best = candidate
    return best[3], best[4], best[0]


def bootstrap_ci(y, p, threshold, n_boot=500):
    rng = np.random.default_rng(SEED)
    vals = {k: [] for k in ["macro_f1", "darknexus_recall", "balanced_accuracy", "mcc", "pr_auc_darknexus", "roc_auc"]}
    y = np.asarray(y); p = np.asarray(p)
    idx0, idx1 = np.where(y == 0)[0], np.where(y == 1)[0]
    for _ in range(n_boot):
        idx = np.r_[rng.choice(idx0, len(idx0), replace=True), rng.choice(idx1, len(idx1), replace=True)]
        m = metric_dict(y[idx], p[idx], threshold)
        for k in vals: vals[k].append(m[k])
    return {k: [float(np.quantile(v, .025)), float(np.quantile(v, .975))] for k, v in vals.items()}


def run_experiments(df):
    feature_sets = {
        "pcap": [c for c in df if c.startswith("pcap__")],
        "sar": [c for c in df if c.startswith("sar__")],
        "strace": [c for c in df if c.startswith("strace__")],
    }
    feature_sets["fusion_all"] = sum(feature_sets.values(), [])
    feature_sets["fusion_minus_pcap"] = feature_sets["sar"] + feature_sets["strace"]
    feature_sets["fusion_minus_sar"] = feature_sets["pcap"] + feature_sets["strace"]
    feature_sets["fusion_minus_strace"] = feature_sets["pcap"] + feature_sets["sar"]
    all_features = sorted(set(sum(feature_sets.values(), [])))
    inf_count = int(np.isinf(df[all_features].to_numpy(dtype=float, copy=False)).sum())
    df = df.copy()
    df[all_features] = df[all_features].replace([np.inf, -np.inf], np.nan)
    (OUT / "nonfinite_audit.json").write_text(
        json.dumps({"infinite_values_replaced_with_nan": inf_count,
                    "imputation_rule": "training-fold median only"}, indent=2), encoding="utf-8")
    rows, predictions = [], []
    for fs_name, features in feature_sets.items():
        for kind in ["logistic", "random_forest"]:
            for held in ARCHES:
                print(f"fit {fs_name} {kind} hold={held}", flush=True)
                param, threshold, inner = tune(df, features, held, kind)
                tr, te = df[df.Arch != held], df[df.Arch == held]
                model = make_model(kind, param)
                model.fit(tr[features], tr.y)
                p = model.predict_proba(te[features])[:, 1]
                m = metric_dict(te.y.to_numpy(), p, threshold)
                ci = bootstrap_ci(te.y.to_numpy(), p, threshold)
                row = {"feature_set": fs_name, "model": kind, "held_out_arch": held,
                       "hyperparameter": param, "inner_mean_macro_f1": inner, **m,
                       **{f"{k}_ci_low": v[0] for k, v in ci.items()},
                       **{f"{k}_ci_high": v[1] for k, v in ci.items()}}
                rows.append(row)
                predictions.append(pd.DataFrame({"Hash": te.Hash, "MalwareFamily": te.MalwareFamily,
                    "Arch": te.Arch, "feature_set": fs_name, "model": kind,
                    "prob_darknexus": p, "threshold": threshold}))
                pd.DataFrame(rows).to_csv(OUT / "PILOT_06_G7_RESULTS.csv", index=False)
    pred = pd.concat(predictions, ignore_index=True)
    pred.to_parquet(OUT / "PILOT_06_G7_PREDICTIONS.parquet", index=False)
    return pd.DataFrame(rows), pred


def main():
    np.random.seed(SEED)
    feature_file = OUT / "PILOT_06_G7_FEATURE_MATRIX_ROBUST.parquet"
    if feature_file.exists():
        df = pd.read_parquet(feature_file)
        schema = json.loads((OUT / "feature_schema.json").read_text())
    else:
        df, schema = build_features()
    results, predictions = run_experiments(df)
    summary = results.groupby(["feature_set", "model"], as_index=False).agg(
        mean_macro_f1=("macro_f1", "mean"), min_macro_f1=("macro_f1", "min"),
        mean_darknexus_recall=("darknexus_recall", "mean"),
        mean_balanced_accuracy=("balanced_accuracy", "mean"), mean_mcc=("mcc", "mean"),
        mean_pr_auc=("pr_auc_darknexus", "mean"), mean_roc_auc=("roc_auc", "mean"),
    ).sort_values("mean_macro_f1", ascending=False)
    summary.to_csv(OUT / "PILOT_06_G7_SUMMARY.csv", index=False)
    print(summary.to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
