#!/usr/bin/env python3
"""Validate the internal consistency of frozen summary artifacts."""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
R = ROOT / "results"

g7 = pd.read_csv(R / "PILOT_06_G7_RESULTS.csv")
primary = g7[(g7.feature_set == "strace") & (g7.model == "random_forest")]
assert len(primary) == 4
assert abs(primary.macro_f1.mean() - 0.8646027) < 1e-5

multi = pd.read_csv(R / "PILOT_06_MULTI_SEED_THRESHOLD_RESULTS.csv")
locked = multi[multi.strategy == "source_mean_opt"]
assert len(locked) == 40
assert abs(locked.macro_f1.mean() - 0.8821726) < 1e-5

collision = pd.read_csv(R / "PILOT_06_ARM_EXACT_PROFILE_COLLISIONS.csv")
assert len(collision) == 1
assert int(collision.n_darknexus.iloc[0]) == 49
assert int(collision.n_mirai.iloc[0]) == 21

audit = json.loads((R / "PILOT_06_ARM_ERROR_AUDIT_SUMMARY.json").read_text())
assert audit["samples_in_cross_label_collisions"] == 70

print("Frozen results are internally consistent.")

