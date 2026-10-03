#!/usr/bin/env python3
"""Pilot 06: 10-seed RF stability and target-label-free threshold transport.

All hyperparameter, calibration, and threshold decisions use source-architecture
out-of-fold predictions only. The held-out architecture is opened once per run.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.feature_selection import VarianceThreshold
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, balanced_accuracy_score,
                             f1_score, matthews_corrcoef, recall_score,
                             roc_auc_score)
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "g10_validation"
OUT.mkdir(exist_ok=True)
ARCHES = ["arm", "mips", "mipsel", "x86"]
SEEDS = [20261001, 20261002, 20261003, 20261004, 20261005,
         20261006, 20261007, 20261008, 20261009, 20261010]
PARAMS = [1, 5]
GRID = np.linspace(0.01, 0.99, 99)


def model(seed: int, leaf: int) -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median", keep_empty_features=False)),
        ("variance", VarianceThreshold(0.0)),
        ("model", RandomForestClassifier(
            n_estimators=300, max_features="sqrt", min_samples_leaf=leaf,
            class_weight="balanced_subsample", n_jobs=-1, random_state=seed)),
    ])


def macro(y, p, t):
    return f1_score(y, p >= t, average="macro", zero_division=0)


def threshold_rules(oof: pd.DataFrame) -> dict[str, float]:
    by_t = []
    for t in GRID:
        scores = [macro(g.y, g.p, t) for _, g in oof.groupby("Arch")]
        by_t.append((t, float(np.mean(scores)), float(np.min(scores))))
    tab = pd.DataFrame(by_t, columns=["threshold", "mean_macro_f1", "min_macro_f1"])
    mean_best = tab.sort_values(["mean_macro_f1", "threshold"], ascending=[False, True]).iloc[0]
    minimax = tab.sort_values(["min_macro_f1", "mean_macro_f1", "threshold"], ascending=[False, False, True]).iloc[0]
    per_arch = []
    for _, g in oof.groupby("Arch"):
        scores = [(macro(g.y, g.p, t), -abs(t-.5), t) for t in GRID]
        per_arch.append(max(scores)[2])
    return {
        "source_mean_opt": float(mean_best.threshold),
        "source_minimax": float(minimax.threshold),
        "source_arch_median": float(np.median(per_arch)),
    }


def choose_leaf(df, feats, held, seed):
    source = [a for a in ARCHES if a != held]
    candidates = []
    cache = {}
    for leaf in PARAMS:
        parts = []
        for inner in source:
            tr = df[df.Arch.isin([a for a in source if a != inner])]
            va = df[df.Arch == inner]
            fit = model(seed, leaf).fit(tr[feats], tr.y)
            parts.append(pd.DataFrame({"y": va.y.to_numpy(),
                                       "p": fit.predict_proba(va[feats])[:, 1],
                                       "Arch": inner}))
        oof = pd.concat(parts, ignore_index=True)
        cache[leaf] = oof
        rules = threshold_rules(oof)
        score = np.mean([macro(g.y, g.p, rules["source_mean_opt"])
                         for _, g in oof.groupby("Arch")])
        candidates.append((float(score), -leaf, leaf))
    leaf = max(candidates)[2]
    return leaf, cache[leaf]


def evaluate(y, p, threshold):
    pred = p >= threshold
    return {
        "macro_f1": macro(y, p, threshold),
        "darknexus_recall": recall_score(y, pred, zero_division=0),
        "balanced_accuracy": balanced_accuracy_score(y, pred),
        "mcc": matthews_corrcoef(y, pred),
        "pr_auc_darknexus": average_precision_score(y, p),
        "roc_auc": roc_auc_score(y, p),
        "predicted_positive_rate": float(np.mean(pred)),
    }


def main():
    df = pd.read_parquet(ROOT / "g7_outputs/PILOT_06_G7_FEATURE_MATRIX_ROBUST.parquet")
    feats = [c for c in df if c.startswith("strace__")]
    df = df.copy()
    df[feats] = df[feats].replace([np.inf, -np.inf], np.nan)
    rows, pred_rows = [], []
    for seed in SEEDS:
        for held in ARCHES:
            print(f"seed={seed} held={held}", flush=True)
            leaf, oof = choose_leaf(df, feats, held, seed)
            rules = threshold_rules(oof)

            # Calibration is learned exclusively from source-architecture OOF predictions.
            platt = LogisticRegression(solver="lbfgs", class_weight="balanced", random_state=seed)
            platt.fit(oof[["p"]], oof.y)
            isotonic = IsotonicRegression(out_of_bounds="clip").fit(oof.p, oof.y)

            tr, te = df[df.Arch != held], df[df.Arch == held]
            fit = model(seed, leaf).fit(tr[feats], tr.y)
            raw = fit.predict_proba(te[feats])[:, 1]
            strategies = {
                **{k: (raw, t) for k, t in rules.items()},
                "platt_balanced_0.5": (platt.predict_proba(raw.reshape(-1, 1))[:, 1], .5),
                "isotonic_0.5": (isotonic.predict(raw), .5),
                "raw_0.5": (raw, .5),
            }
            for strategy, (prob, threshold) in strategies.items():
                metrics = evaluate(te.y.to_numpy(), prob, threshold)
                rows.append({"seed": seed, "held_out_arch": held, "strategy": strategy,
                             "min_samples_leaf": leaf, "threshold": threshold,
                             "n": len(te), "n_darknexus": int(te.y.sum()), **metrics})
                pred_rows.append(pd.DataFrame({
                    "Hash": te.Hash.to_numpy(), "Arch": held, "y": te.y.to_numpy(),
                    "seed": seed, "strategy": strategy, "prob_darknexus": prob,
                    "threshold": threshold}))
            pd.DataFrame(rows).to_csv(OUT / "PILOT_06_MULTI_SEED_THRESHOLD_RESULTS.csv", index=False)

    result = pd.DataFrame(rows)
    predictions = pd.concat(pred_rows, ignore_index=True)
    predictions.to_parquet(OUT / "PILOT_06_MULTI_SEED_THRESHOLD_PREDICTIONS.parquet", index=False)
    summary = result.groupby(["strategy", "held_out_arch"], as_index=False).agg(
        macro_f1_mean=("macro_f1", "mean"), macro_f1_sd=("macro_f1", "std"),
        macro_f1_min=("macro_f1", "min"), macro_f1_max=("macro_f1", "max"),
        recall_mean=("darknexus_recall", "mean"), recall_sd=("darknexus_recall", "std"),
        balanced_accuracy_mean=("balanced_accuracy", "mean"),
        mcc_mean=("mcc", "mean"), pr_auc_mean=("pr_auc_darknexus", "mean"),
        roc_auc_mean=("roc_auc", "mean"), threshold_mean=("threshold", "mean"),
        threshold_sd=("threshold", "std"))
    summary.to_csv(OUT / "PILOT_06_MULTI_SEED_THRESHOLD_SUMMARY.csv", index=False)
    overall = result.groupby("strategy", as_index=False).agg(
        mean_macro_f1=("macro_f1", "mean"), sd_all_runs=("macro_f1", "std"),
        mean_darknexus_recall=("darknexus_recall", "mean"),
        worst_macro_f1=("macro_f1", "min"), worst_recall=("darknexus_recall", "min"),
        mean_pr_auc=("pr_auc_darknexus", "mean"), mean_roc_auc=("roc_auc", "mean"))
    overall.to_csv(OUT / "PILOT_06_THRESHOLD_STRATEGY_OVERALL.csv", index=False)
    meta = {"seeds": SEEDS, "n_seeds": len(SEEDS), "architectures": ARCHES,
            "feature_set": "STRACE relative frequency", "rf_trees": 300,
            "candidate_min_samples_leaf": PARAMS,
            "target_labels_used_for_selection_or_calibration": False,
            "note": "All selection/calibration uses source-architecture OOF predictions only."}
    (OUT / "PILOT_06_VALIDATION_PROTOCOL.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(overall.sort_values("mean_macro_f1", ascending=False).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
