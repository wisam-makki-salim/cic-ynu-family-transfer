# Pilot 06 — G7 Execution, G8 Critical Review, and G9 Novelty Recheck

Date: 2026-10-01  
Dataset: CIC-YNU-IoTMal 2026  
Unit of analysis: executable SHA-256 hash  
Locked task: DarkNexus versus Mirai with one CPU architecture completely held out

## G7 — Reproducible execution

**Status: PASS WITH RESTRICTIONS**

The final analysis used 7,587 linked executables: 7,368 Mirai and 219 DarkNexus. PCAP, SAR, and STRACE were present for every included hash. The four outer tests held out ARM, MIPS, MIPSEL, and x86 in turn. Preprocessing, hyperparameter selection, and threshold selection were fitted only on the three training architectures.

### Representations

- PCAP: median, 25th percentile, and 75th percentile for 39 architecture-common numeric variables. No packet-window count was retained.
- SAR: median, 25th percentile, and 75th percentile for 313 architecture-common numeric variables. Absolute timestamps and interval counts were excluded.
- STRACE: relative frequencies for 87 architecture-common, non-malformed system-call variables. Total trace length was not retained.
- Fusion: early concatenation after fold-internal median imputation and variance filtering.

Models were class-weighted logistic regression and class-weighted random forest. Random forest was the stronger comparator. Five hundred class-stratified executable-level bootstrap replicates were used for each outer-fold confidence interval.

### Primary result

STRACE-only random forest was the strongest model.

| Held-out architecture | Macro-F1 | 95% CI | DarkNexus recall | 95% CI | PR-AUC | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| ARM | 0.714 | 0.651–0.764 | 0.295 | 0.193–0.386 | 0.448 | 0.818 |
| MIPS | 0.943 | 0.911–0.970 | 0.952 | 0.881–1.000 | 0.951 | 0.999 |
| MIPSEL | 0.947 | 0.917–0.975 | 1.000 | 1.000–1.000 | 0.918 | 0.998 |
| x86 | 0.854 | 0.793–0.909 | 0.580 | 0.440–0.720 | 0.932 | 0.998 |
| **Mean across architectures** | **0.865** | — | **0.707** | — | **0.812** | **0.953** |

The large difference between ranking metrics and thresholded recall on ARM and x86 shows that probability ranking transfers better than the operating threshold.

### Modality ablation

| Representation | Model | Mean Macro-F1 | Minimum fold Macro-F1 | Mean DarkNexus recall |
|---|---|---:|---:|---:|
| STRACE | Random forest | **0.865** | **0.714** | **0.707** |
| PCAP + STRACE | Random forest | 0.851 | 0.708 | 0.676 |
| SAR + STRACE | Random forest | 0.842 | 0.707 | 0.673 |
| PCAP + SAR + STRACE | Random forest | 0.840 | 0.694 | 0.672 |
| SAR | Random forest | 0.661 | 0.492 | 0.451 |
| PCAP + SAR | Random forest | 0.662 | 0.492 | 0.438 |
| PCAP | Random forest | 0.521 | 0.494 | 0.080 |

Fusion did not improve the primary outcome. Against STRACE alone, the paired mean Macro-F1 differences were:

- all modalities: −0.0243, bootstrap 95% CI −0.0404 to −0.0109;
- PCAP + STRACE: −0.0135, bootstrap 95% CI −0.0267 to −0.0023;
- SAR + STRACE: −0.0225, bootstrap 95% CI −0.0376 to −0.0093.

The prespecified fusion-benefit hypothesis is therefore rejected.

### MIPSEL date-matched sensitivity

Restricting MIPSEL to 29 June 2025 retained all 39 DarkNexus and 1,469 of 1,483 Mirai executables. STRACE-only random forest remained effectively unchanged: Macro-F1 0.947, DarkNexus recall 1.000, PR-AUC 0.918, and ROC-AUC 0.998. The MIPSEL finding is not explained by the small September-only Mirai subset.

## G8 — Independent critical review

**Status: PASS WITH MAJOR RESTRICTIONS**

The result survives the locked leakage controls, robust aggregation, modality ablation, paired bootstrap comparison, and MIPSEL date-matching check. It does not support a generic malware detector or a claim that CPU architecture caused the performance differences.

Material limitations:

1. Only 219 DarkNexus executables are available, with 39–88 positive examples per held-out architecture.
2. ARM transfer is weak. DarkNexus recall is only 0.295 despite acceptable ranking, so a single global operating threshold is not deployment-ready.
3. Different hashes occur in different architectures. Architecture shift is inseparable from executable-population shift.
4. The labels originate from the dataset and were not independently re-attributed.
5. Sandbox behavior may reflect activation failures and environment sensitivity.
6. Random forest is stochastic, although the fixed seed and bootstrap quantify sampling uncertainty. A multi-seed stability analysis would strengthen a submission.

Decision: retain the result as a conservative family-transfer and modality-ablation study. Do not market it as a new detection architecture. Before journal submission, add multi-seed stability and investigate threshold transport or calibration without target labels.

## G9 — Final novelty recheck

**Status: PASS WITH SEVERE NOVELTY RESTRICTION**

The August 2026 preprint *Evaluation Pitfalls and Multimodal Baselines for the CIC-YNU-IoTMal2026 IoT Malware Dataset* already covers executable-level evaluation, multimodal baselines, leave-one-architecture-out detection, architecture fragility, and the strength of STRACE. It therefore invalidates any broad novelty claim based on those elements alone.

The remaining distinguishable contribution is limited to:

- exposing the complete collection-period confounding of the dataset's benign-versus-malware linked cohort;
- replacing that invalid target with a malware-only DarkNexus-versus-Mirai question;
- quantifying family discrimination under strict architecture holdout;
- showing that robust early fusion reduces rather than improves Macro-F1 relative to STRACE alone;
- showing that the MIPSEL result survives date matching.

This is enough for a focused dataset-evaluation or negative-results paper only if the adjacent preprint and newer family-classification papers are discussed directly. Claims of first multimodal analysis, first cross-architecture evaluation, or first executable-level audit are prohibited.

## Gate decision

- G7: **PASS WITH RESTRICTIONS**
- G8: **PASS WITH MAJOR RESTRICTIONS**
- G9: **PASS WITH SEVERE NOVELTY RESTRICTION**
- Next action: G10 publication package, after adding a multi-seed stability check if targeting a full journal article.

## Sources

- Official dataset page: https://www.unb.ca/cic/datasets/ynu-iot-2026.html
- Dataset article: https://doi.org/10.1016/j.is.2026.102722
- Adjacent preprint: https://doi.org/10.21203/rs.3.rs-10427932/v1

