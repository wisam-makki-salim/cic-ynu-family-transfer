#!/usr/bin/env python3
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parent
R, F = ROOT / "results", ROOT / "figures"
F.mkdir(exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

# Figure 1: validity-first methodological pipeline.
fig, ax = plt.subplots(figsize=(12, 4.6))
ax.set_xlim(0, 12); ax.set_ylim(0, 5); ax.axis("off")
boxes = [
    (0.3, 3.2, "Raw modalities\nPCAP · SAR · STRACE", "#e8f1fa"),
    (3.0, 3.2, "Hash-level linkage\nand schema audit", "#e8f1fa"),
    (5.7, 3.2, "Validity gate\ntime/entity confounding", "#fdebd3"),
    (8.4, 3.2, "Target redesign\nmalware-family task", "#e4f4ea"),
    (8.4, 1.0, "Nested LOAO\nsource-only selection", "#e4f4ea"),
    (5.7, 1.0, "Modality ablation\nand 10-seed stress test", "#e4f4ea"),
    (3.0, 1.0, "Locked ARM\nerror diagnosis", "#fdebd3"),
    (0.3, 1.0, "Raw-matrix collision\nand identifiability bound", "#f7d9d9"),
]
for x, y, label, color in boxes:
    ax.add_patch(FancyBboxPatch((x, y), 2.0, 1.0, boxstyle="round,pad=0.04,rounding_size=0.08",
                                linewidth=1.2, edgecolor="#34495e", facecolor=color))
    ax.text(x+1, y+.5, label, ha="center", va="center", fontsize=10)
path = [(2.3,3.7,3.0,3.7),(5.0,3.7,5.7,3.7),(7.7,3.7,8.4,3.7),
        (9.4,3.2,9.4,2.0),(8.4,1.5,7.7,1.5),(5.7,1.5,5.0,1.5),(3.0,1.5,2.3,1.5)]
for x1,y1,x2,y2 in path:
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle="-|>",mutation_scale=13,
                                 linewidth=1.2,color="#34495e"))
ax.text(6.7, 2.85, "Rejected: benign vs malware", ha="center", va="center",
        fontsize=9, color="#9b2c2c", style="italic")
fig.tight_layout(); fig.savefig(F / "figure_1_methodology_pipeline.png", dpi=300, bbox_inches="tight"); plt.close(fig)

# Figure 2: ten-seed transfer by architecture.
d = pd.read_csv(R / "PILOT_06_MULTI_SEED_THRESHOLD_SUMMARY.csv")
d = d[d.strategy == "source_mean_opt"].set_index("held_out_arch").loc[["arm", "mips", "mipsel", "x86"]]
x = np.arange(4)
fig, ax = plt.subplots(figsize=(7.2, 4.2))
ax.errorbar(x - .08, d.macro_f1_mean, yerr=d.macro_f1_sd, marker="o", capsize=4, lw=1.8, label="Macro-F1")
ax.errorbar(x + .08, d.recall_mean, yerr=d.recall_sd, marker="s", capsize=4, lw=1.8, label="DarkNexus recall")
ax.set_xticks(x, ["ARM", "MIPS", "MIPSEL", "x86"]); ax.set_ylim(0, 1.05)
ax.set_ylabel("Mean across ten seeds"); ax.set_title("Cross-architecture transfer is heterogeneous")
ax.legend(frameon=False, loc="lower right"); fig.tight_layout()
fig.savefig(F / "figure_2_multiseed_transfer.png", dpi=220); plt.close(fig)

# Figure 3: modality ablation.
s = pd.read_csv(R / "PILOT_06_G7_SUMMARY.csv")
s = s[s.model == "random_forest"].copy()
labels = {"strace":"STRACE", "fusion_minus_sar":"PCAP + STRACE", "fusion_minus_pcap":"SAR + STRACE",
          "fusion_all":"All modalities", "sar":"SAR", "fusion_minus_strace":"PCAP + SAR", "pcap":"PCAP"}
s["label"] = s.feature_set.map(labels); s = s.sort_values("mean_macro_f1")
fig, ax = plt.subplots(figsize=(7.2, 4.5))
colors = ["#163A5F" if v == "STRACE" else "#8FA9BF" for v in s.label]
ax.barh(s.label, s.mean_macro_f1, color=colors)
ax.set_xlim(0.45, 0.9); ax.set_xlabel("Mean leave-one-architecture-out Macro-F1")
ax.set_title("Early fusion does not improve the strongest modality")
for i, v in enumerate(s.mean_macro_f1): ax.text(v + .006, i, f"{v:.3f}", va="center", fontsize=9)
fig.tight_layout(); fig.savefig(F / "figure_3_modality_ablation.png", dpi=220); plt.close(fig)

# Figure 4: ARM collision composition.
fig, ax = plt.subplots(figsize=(6.8, 3.9))
cats = ["DarkNexus\n(n=88)", "Mirai\n(n=2,721)"]
collision = np.array([49, 21]); other = np.array([39, 2700])
ax.bar(cats, collision, label="Exact cross-label profile", color="#B44949")
ax.bar(cats, other, bottom=collision, label="Other profiles", color="#B8C8D6")
ax.set_yscale("log"); ax.set_ylabel("Executables (log scale)")
ax.set_title("One short STRACE profile carries conflicting ARM labels")
ax.legend(frameon=False)
for i, v in enumerate(collision): ax.text(i, max(v/2,1), str(v), ha="center", va="center", color="white", fontweight="bold")
fig.tight_layout(); fig.savefig(F / "figure_4_arm_collision.png", dpi=220); plt.close(fig)

print("Figures written to", F)
