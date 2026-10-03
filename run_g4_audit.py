from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parent
FILES = {
    "x86": {
        "pcap": ROOT / "x86/pcap.parquet",
        "sar": ROOT / "x86/sar.parquet",
        "strace": ROOT / "x86/strace.parquet",
    },
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
}
KEYS = ["Hash", "MalwareFamily", "Arch"]


def key_counts(path: Path):
    counts = Counter()
    labels = {}
    for batch in pq.ParquetFile(path).iter_batches(columns=KEYS, batch_size=262144):
        df = batch.to_pandas()
        vc = df["Hash"].value_counts(dropna=False)
        counts.update(vc.to_dict())
        for h, fam, arch in df[KEYS].drop_duplicates().itertuples(index=False, name=None):
            old = labels.get(h)
            val = (fam, arch)
            if old is not None and old != val:
                raise ValueError(f"Conflicting label for {h}: {old} vs {val}")
            labels[h] = val
    return counts, labels


def sar_time_summary(path: Path):
    pieces = []
    for batch in pq.ParquetFile(path).iter_batches(columns=["Hash", "timestamp"], batch_size=262144):
        df = batch.to_pandas()
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
        pieces.append(df.groupby("Hash", dropna=False)["timestamp"].agg(["min", "max", "count"]))
    merged = pd.concat(pieces).groupby(level=0).agg({"min": "min", "max": "max", "count": "sum"})
    merged["sar_span_seconds"] = (merged["max"] - merged["min"]).dt.total_seconds()
    merged = merged.rename(columns={"min": "sar_start", "max": "sar_end", "count": "sar_timestamp_nonmissing"})
    return merged


def schema_dictionary():
    rows = []
    for arch, mods in FILES.items():
        for modality, path in mods.items():
            schema = pq.ParquetFile(path).schema_arrow
            for f in schema:
                role = "candidate_predictor"
                risk = "review"
                if f.name == "Hash": role, risk = "identifier", "exclude_direct_leakage"
                elif f.name == "MalwareFamily": role, risk = "target_source", "exclude_direct_leakage"
                elif f.name == "Arch": role, risk = "domain_metadata", "exclude_primary_predictor"
                elif f.name == "timestamp": role, risk = "collection_metadata", "exclude_absolute_time"
                elif f.name == "interval": role, risk = "collection_metadata", "exclude_or_sensitivity_only"
                rows.append((arch, modality, f.name, str(f.type), role, risk))
    return pd.DataFrame(rows, columns=["architecture", "modality", "feature", "dtype", "role", "leakage_rule"])


def main():
    records = []
    modality_schema = {}
    for arch, mods in FILES.items():
        data = {}
        for modality, path in mods.items():
            data[modality] = key_counts(path)
            modality_schema[(arch, modality)] = set(pq.ParquetFile(path).schema_arrow.names)
        common = set(data["pcap"][0]) & set(data["sar"][0]) & set(data["strace"][0])
        common = {h for h in common if isinstance(h, str) and len(h) == 64 and all(c in "0123456789abcdefABCDEF" for c in h)}
        times = sar_time_summary(mods["sar"])
        for h in sorted(common):
            fam, reported_arch = data["pcap"][1][h]
            if fam == "Unknown":
                continue
            if data["sar"][1][h] != (fam, reported_arch) or data["strace"][1][h] != (fam, reported_arch):
                raise ValueError(f"Cross-modality conflict: {h}")
            t = times.loc[h] if h in times.index else None
            records.append({
                "Hash": h,
                "Arch": arch,
                "MalwareFamily": fam,
                "binary_label": 0 if fam == "Benign" else 1,
                "pcap_rows": data["pcap"][0][h],
                "sar_rows": data["sar"][0][h],
                "strace_rows": data["strace"][0][h],
                "sar_start": None if t is None else t["sar_start"],
                "sar_end": None if t is None else t["sar_end"],
                "sar_timestamp_nonmissing": 0 if t is None else int(t["sar_timestamp_nonmissing"]),
                "sar_span_seconds": None if t is None else t["sar_span_seconds"],
            })
    cohort = pd.DataFrame(records)
    cohort.to_parquet(ROOT / "PILOT_06_COHORT_MANIFEST.parquet", index=False)
    cohort.to_csv(ROOT / "PILOT_06_COHORT_MANIFEST.csv", index=False)

    dd = schema_dictionary()
    dd.to_csv(ROOT / "PILOT_06_FEATURE_DICTIONARY.csv", index=False)

    # Architecture schema mismatch is a reproducibility and domain-shift risk.
    schema_diff = {}
    for modality in ("pcap", "sar", "strace"):
        sets = {a: modality_schema[(a, modality)] for a in FILES}
        union = set.union(*sets.values())
        inter = set.intersection(*sets.values())
        schema_diff[modality] = {
            "intersection_features": len(inter),
            "union_features": len(union),
            "architecture_specific": {a: sorted(sets[a] - inter) for a in FILES},
        }

    # Artifact-only discrimination: each holdout architecture is never seen in training.
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import balanced_accuracy_score, roc_auc_score
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    artifact_cols = ["pcap_rows", "sar_rows", "strace_rows", "sar_span_seconds", "sar_start"]
    model_df = cohort.copy()
    model_df["sar_start_hour"] = pd.to_datetime(model_df["sar_start"], utc=True).astype("int64") / 1e9
    xcols = ["pcap_rows", "sar_rows", "strace_rows", "sar_span_seconds", "sar_start_hour"]
    folds = []
    for holdout in FILES:
        tr = model_df.Arch != holdout
        te = ~tr
        pipe = Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("lr", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=20261001)),
        ])
        pipe.fit(model_df.loc[tr, xcols], model_df.loc[tr, "binary_label"])
        prob = pipe.predict_proba(model_df.loc[te, xcols])[:, 1]
        pred = (prob >= 0.5).astype(int)
        folds.append({
            "holdout_arch": holdout,
            "n": int(te.sum()),
            "malware_prevalence": float(model_df.loc[te, "binary_label"].mean()),
            "roc_auc": float(roc_auc_score(model_df.loc[te, "binary_label"], prob)),
            "balanced_accuracy": float(balanced_accuracy_score(model_df.loc[te, "binary_label"], pred)),
        })

    summary = {
        "n": len(cohort),
        "by_arch_label": cohort.groupby(["Arch", "binary_label"]).size().unstack(fill_value=0).to_dict(orient="index"),
        "by_arch_family": {"|".join(k): int(v) for k, v in cohort.groupby(["Arch", "MalwareFamily"]).size().items()},
        "duplicates_hash": int(cohort.Hash.duplicated().sum()),
        "missing": {c: int(cohort[c].isna().sum()) for c in cohort.columns},
        "row_count_ranges": {
            arch: {
                f"{feature}_{stat}": (None if pd.isna(value) else float(value))
                for (feature, stat), value in row.items()
            }
            for arch, row in cohort.groupby("Arch")[["pcap_rows", "sar_rows", "strace_rows", "sar_span_seconds"]]
            .agg(["min", "median", "max"]).iterrows()
        },
        "artifact_only_leave_one_arch_out": folds,
        "schema_diff": schema_diff,
        "rules": {
            "sampling_unit": "Hash",
            "primary_target": "Benign (0) vs any named malware family (1)",
            "exclude_predictors": ["Hash", "MalwareFamily", "Arch", "timestamp", "interval"],
            "artifact_sensitivity_features": artifact_cols,
        },
    }
    with open(ROOT / "PILOT_06_G4_AUDIT_RESULTS.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps({"n": len(cohort), "folds": folds, "schema_diff": schema_diff}, indent=2))


if __name__ == "__main__":
    main()
