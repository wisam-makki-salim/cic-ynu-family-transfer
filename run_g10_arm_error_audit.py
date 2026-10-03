#!/usr/bin/env python3
"""Diagnostic ARM error audit for Pilot 06; never used for model retuning."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, spearmanr
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "g10_validation" / "arm_error_audit"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20261001


def cliffs_delta(x, y):
    x, y = np.asarray(x), np.asarray(y)
    # U converts exactly to the common-language effect, then to Cliff's delta.
    u = mannwhitneyu(x, y, alternative="two-sided").statistic
    return float(2 * u / (len(x) * len(y)) - 1)


def perm_group_test(values, groups, n_perm=5000):
    values, groups = np.asarray(values), np.asarray(groups)
    uniq = np.unique(groups)
    grand = values.mean()
    obs = sum(np.sum(groups == g) * (values[groups == g].mean() - grand) ** 2 for g in uniq)
    rng = np.random.default_rng(SEED)
    exceed = 0
    for _ in range(n_perm):
        p = rng.permutation(values)
        stat = sum(np.sum(groups == g) * (p[groups == g].mean() - p.mean()) ** 2 for g in uniq)
        exceed += stat >= obs
    return float(obs), float((exceed + 1) / (n_perm + 1))


def bh_adjust(p):
    p = np.asarray(p, dtype=float)
    order = np.argsort(p)
    ranked = p[order]
    adj = np.minimum.accumulate((ranked * len(p) / np.arange(1, len(p) + 1))[::-1])[::-1]
    out = np.empty_like(adj); out[order] = np.minimum(adj, 1)
    return out


def main():
    pred = pd.read_parquet(ROOT / "g10_validation/PILOT_06_MULTI_SEED_THRESHOLD_PREDICTIONS.parquet")
    pred = pred[(pred.Arch == "arm") & (pred.strategy == "source_mean_opt")].copy()
    pred["pred"] = pred.prob_darknexus >= pred.threshold
    pred["error"] = pred.pred.astype(int) != pred.y
    per_hash = pred.groupby(["Hash", "y"], as_index=False).agg(
        error_rate=("error", "mean"), error_count=("error", "sum"),
        mean_probability=("prob_darknexus", "mean"), probability_sd=("prob_darknexus", "std"),
        mean_threshold=("threshold", "mean"))
    per_hash["error_status"] = np.select(
        [per_hash.error_count == 0, per_hash.error_count == 10],
        ["always_correct", "always_wrong"], default="seed_sensitive")

    manifest = pd.read_parquet(ROOT / "PILOT_06_COHORT_MANIFEST.parquet")
    manifest = manifest[(manifest.Arch.str.lower() == "arm") & manifest.MalwareFamily.isin(["Mirai", "DarkNexus"])].copy()
    manifest["collection_date"] = pd.to_datetime(manifest.sar_start, utc=True).dt.date.astype(str)
    feature = pd.read_parquet(ROOT / "g7_outputs/PILOT_06_G7_FEATURE_MATRIX_ROBUST.parquet")
    sf = [c for c in feature if c.startswith("strace__")]
    arm = per_hash.merge(manifest, on="Hash", validate="one_to_one").merge(
        feature[["Hash", "MalwareFamily", *sf]], on=["Hash", "MalwareFamily"], validate="one_to_one")
    x = arm[sf].fillna(0).clip(lower=0)
    arm["syscall_nonzero"] = (x > 0).sum(axis=1)
    arm["syscall_max_share"] = x.max(axis=1)
    arm["syscall_entropy"] = -(x.where(x > 0) * np.log(x.where(x > 0))).sum(axis=1)
    arm["log_strace_rows"] = np.log1p(arm.strace_rows)
    arm["strace_signature"] = arm[sf].fillna(0).round(12).astype(str).agg("|".join, axis=1)
    arm.to_parquet(OUT / "PILOT_06_ARM_PER_HASH_ERROR_AUDIT.parquet", index=False)

    signature = arm.groupby("strace_signature", as_index=False).agg(
        n=("Hash", "size"), n_families=("MalwareFamily", "nunique"),
        n_darknexus=("y", "sum"), mean_error_rate=("error_rate", "mean"),
        strace_rows=("strace_rows", "first"))
    collisions = signature[signature.n_families > 1].copy()
    collisions["n_mirai"] = collisions.n - collisions.n_darknexus
    collisions.to_csv(OUT / "PILOT_06_ARM_EXACT_PROFILE_COLLISIONS.csv", index=False)

    status = arm.groupby(["MalwareFamily", "error_status"], as_index=False).size()
    status["class_fraction"] = status["size"] / status.groupby("MalwareFamily")["size"].transform("sum")
    status.to_csv(OUT / "PILOT_06_ARM_ERROR_STATUS.csv", index=False)

    date = arm.groupby(["MalwareFamily", "collection_date"], as_index=False).agg(
        n=("Hash", "size"), mean_error_rate=("error_rate", "mean"),
        always_wrong=("error_status", lambda s: int((s == "always_wrong").sum())),
        seed_sensitive=("error_status", lambda s: int((s == "seed_sensitive").sum())))
    date.to_csv(OUT / "PILOT_06_ARM_ERROR_BY_DATE.csv", index=False)

    continuous = []
    metrics = ["strace_rows", "syscall_nonzero", "syscall_max_share", "syscall_entropy", "sar_span_seconds"]
    for fam, g in arm.groupby("MalwareFamily"):
        wrong = g[g.error_rate >= .5]
        correct = g[g.error_rate < .5]
        for m in metrics:
            a, b = wrong[m].dropna(), correct[m].dropna()
            u = mannwhitneyu(a, b, alternative="two-sided") if len(a) and len(b) else None
            rho, rp = spearmanr(g[m], g.error_rate, nan_policy="omit")
            continuous.append({"MalwareFamily": fam, "metric": m,
                "n_majority_wrong": len(a), "n_majority_correct": len(b),
                "wrong_median": float(a.median()) if len(a) else np.nan,
                "correct_median": float(b.median()) if len(b) else np.nan,
                "cliffs_delta_wrong_vs_correct": cliffs_delta(a, b) if len(a) and len(b) else np.nan,
                "mannwhitney_p": float(u.pvalue) if u else np.nan,
                "spearman_error_rate": float(rho), "spearman_p": float(rp)})
    cont = pd.DataFrame(continuous)
    cont["mannwhitney_q"] = cont.groupby("MalwareFamily").mannwhitney_p.transform(bh_adjust)
    cont["spearman_q"] = cont.groupby("MalwareFamily").spearman_p.transform(bh_adjust)
    cont.to_csv(OUT / "PILOT_06_ARM_CONTINUOUS_ASSOCIATIONS.csv", index=False)

    date_tests, cluster_rows, syscall_rows = [], [], []
    for fam, g in arm.groupby("MalwareFamily"):
        if g.collection_date.nunique() > 1:
            stat, p = perm_group_test(g.error_rate, g.collection_date)
            date_tests.append({"MalwareFamily": fam, "n_dates": g.collection_date.nunique(),
                               "between_date_stat": stat, "permutation_p": p})

        # Hellinger geometry for compositional syscall profiles. k is selected by
        # silhouette without consulting error labels.
        z = np.sqrt(g[sf].fillna(0).clip(lower=0).to_numpy())
        candidates = []
        max_k = min(6, len(g) - 1)
        for k in range(2, max_k + 1):
            labels = KMeans(n_clusters=k, random_state=SEED, n_init=20).fit_predict(z)
            candidates.append((silhouette_score(z, labels), -k, k, labels))
        sil, _, k, labels = max(candidates, key=lambda q: (q[0], q[1]))
        gg = g.copy(); gg["profile_cluster"] = labels
        stat, p = perm_group_test(gg.error_rate, gg.profile_cluster)
        means = gg.groupby("profile_cluster").error_rate.mean()
        worst = int(means.idxmax())
        for cl, cg in gg.groupby("profile_cluster"):
            cluster_rows.append({"MalwareFamily": fam, "selected_k": k, "silhouette": sil,
                "cluster": int(cl), "n": len(cg), "mean_error_rate": cg.error_rate.mean(),
                "always_wrong": int((cg.error_status == "always_wrong").sum()),
                "profile_error_permutation_p": p, "worst_error_cluster": int(cl) == worst})
        inside, outside = gg[gg.profile_cluster == worst], gg[gg.profile_cluster != worst]
        for col in sf:
            a, b = inside[col].fillna(0), outside[col].fillna(0)
            u = mannwhitneyu(a, b, alternative="two-sided")
            syscall_rows.append({"MalwareFamily": fam, "syscall": col.replace("strace__", "").replace("__relative_frequency", ""),
                "worst_cluster": worst, "inside_mean": a.mean(), "outside_mean": b.mean(),
                "mean_difference": a.mean() - b.mean(), "cliffs_delta": cliffs_delta(a, b), "p": u.pvalue})

    pd.DataFrame(date_tests).to_csv(OUT / "PILOT_06_ARM_DATE_PERMUTATION_TESTS.csv", index=False)
    clusters = pd.DataFrame(cluster_rows)
    clusters.to_csv(OUT / "PILOT_06_ARM_PROFILE_CLUSTERS.csv", index=False)
    calls = pd.DataFrame(syscall_rows)
    calls["q"] = calls.groupby("MalwareFamily").p.transform(bh_adjust)
    calls["abs_mean_difference"] = calls.mean_difference.abs()
    calls.sort_values(["MalwareFamily", "abs_mean_difference"], ascending=[True, False]).to_csv(
        OUT / "PILOT_06_ARM_PROFILE_SYSCALLS.csv", index=False)

    summary = {
        "scope": "diagnostic only; no retuning or outcome modification",
        "n_arm": int(len(arm)), "n_seeds": 10,
        "class_counts": arm.MalwareFamily.value_counts().to_dict(),
        "exact_cross_label_profile_collisions": int(len(collisions)),
        "samples_in_cross_label_collisions": int(collisions.n.sum()),
        "darknexus_in_cross_label_collisions": int(collisions.n_darknexus.sum()),
        "mirai_in_cross_label_collisions": int(collisions.n_mirai.sum()),
        "error_status": status.to_dict(orient="records"),
        "date_tests": date_tests,
        "profile_cluster_tests": clusters.groupby("MalwareFamily").first()[
            ["selected_k", "silhouette", "profile_error_permutation_p"]].reset_index().to_dict(orient="records")}
    (OUT / "PILOT_06_ARM_ERROR_AUDIT_SUMMARY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    print("\nCONTINUOUS\n", cont.round(4).to_string(index=False), flush=True)
    print("\nCLUSTERS\n", clusters.round(4).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
