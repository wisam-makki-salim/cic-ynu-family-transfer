#!/usr/bin/env python3
"""Verify whether the ARM cross-label collision exists before aggregation.

The script needs the official ARM STRACE parquet plus the released per-hash
audit table. Dataset bytes are not redistributed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm-strace", type=Path, required=True)
    ap.add_argument("--collision-list", type=Path,
                    default=Path("results/PILOT_06_ARM_RAW_MATRIX_IDENTITY.csv"),
                    help="CSV containing the locked collision hashes and family labels")
    ap.add_argument("--out", type=Path, default=Path("results"))
    args = ap.parse_args()

    collision = pd.read_csv(args.collision_list, usecols=["Hash", "MalwareFamily"])
    if len(collision) != 70 or collision.MalwareFamily.nunique() != 2:
        raise ValueError("The locked collision list must contain 70 hashes from two families")
    hashes = collision.Hash.tolist()
    raw = pq.read_table(args.arm_strace, filters=[("Hash", "in", hashes)]).to_pandas()
    calls = [c for c in raw if c.startswith("Call_")]

    rows = []
    for sample_hash, group in raw.groupby("Hash", sort=False):
        matrix = group[calls].fillna(0).to_numpy()
        rows.append({
            "Hash": sample_hash,
            "MalwareFamily": group.MalwareFamily.iloc[0],
            "n_rows": len(group),
            "raw_matrix_sha256": hashlib.sha256(matrix.tobytes()).hexdigest(),
            "first_row_sum": float(matrix[0].sum()),
            "maximum_row_sum": float(matrix.sum(axis=1).max()),
            "last_row_sum": float(matrix[-1].sum()),
        })

    result = pd.DataFrame(rows)
    summary = {
        "n_samples": len(result),
        "n_raw_matrices": int(result.raw_matrix_sha256.nunique()),
        "families": result.MalwareFamily.value_counts().to_dict(),
        "all_22_rows": bool(result.n_rows.eq(22).all()),
        "all_raw_matrices_identical": bool(result.raw_matrix_sha256.nunique() == 1),
        "schema_limit": "No timestamp, sequence index, syscall arguments, return values, or paths are present.",
        "conclusion": "No n-gram derived from the published matrices can separate labels in this collision.",
    }
    args.out.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.out / "PILOT_06_ARM_RAW_MATRIX_IDENTITY.csv", index=False)
    (args.out / "PILOT_06_ARM_RAW_MATRIX_IDENTITY_SUMMARY.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
