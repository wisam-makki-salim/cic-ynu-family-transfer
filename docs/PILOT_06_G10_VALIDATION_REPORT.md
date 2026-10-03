# Pilot 06 — Multi-seed Stability and Target-label-free Threshold Transport

Date: 2026-10-01  
Dataset: CIC-YNU-IoTMal 2026  
Locked task: DarkNexus versus Mirai with one CPU architecture held out  
Representation: STRACE architecture-common relative syscall frequencies  
Model: class-weighted random forest, 300 trees

## Decision

**PASS WITH MAJOR RESTRICTIONS for a focused dataset-evaluation paper.**  
**FAIL for a deployment-ready detector or broad algorithmic detection paper.**

The required ten-seed stability and target-label-free threshold-transport checks were completed. They confirm strong and stable transfer to MIPS and MIPSEL, but substantial domain sensitivity on ARM and threshold sensitivity on x86. No source-only threshold rule removes this weakness without a trade-off.

## Protocol

Ten fixed seeds (`20261001`–`20261010`) were used. For every seed and outer held-out architecture:

1. `min_samples_leaf` was selected from `{1, 5}` using only leave-one-source-architecture-out predictions from the three training architectures.
2. All imputation and variance filtering were fitted within the relevant training split.
3. Thresholds and calibrators were learned only from source-architecture out-of-fold predictions.
4. The held-out architecture was not used for model selection, calibration, or threshold selection.
5. The target architecture was opened once for evaluation.

Six operating-point rules were evaluated as prespecified sensitivities:

- source mean-optimal threshold;
- source minimax threshold, maximizing the worst source-architecture Macro-F1;
- median of source-architecture-specific optimal thresholds;
- balanced Platt mapping followed by threshold 0.5;
- isotonic mapping followed by threshold 0.5;
- uncalibrated threshold 0.5.

## Ten-seed stability of the locked rule

The locked source-mean threshold produced the following results:

| Held-out architecture | Macro-F1 mean ± SD | Range | DarkNexus recall mean ± SD | Recall range | PR-AUC mean | ROC-AUC mean |
|---|---:|---:|---:|---:|---:|---:|
| ARM | 0.738 ± 0.024 | 0.714–0.779 | 0.327 ± 0.045 | 0.284–0.409 | 0.490 | 0.869 |
| MIPS | 0.948 ± 0.004 | 0.943–0.953 | 0.952 ± 0.000 | 0.952–0.952 | 0.951 | 0.999 |
| MIPSEL | 0.945 ± 0.004 | 0.936–0.947 | 1.000 ± 0.000 | 1.000–1.000 | 0.916 | 0.998 |
| x86 | 0.898 ± 0.042 | 0.816–0.931 | 0.778 ± 0.155 | 0.500–0.900 | 0.922 | 0.998 |
| **All 40 seed–architecture runs** | **0.882** | **0.714–0.953** | **0.764** | **0.284–1.000** | **0.820** | **0.966** |

The originally reported seed is exactly reproduced: ARM 0.714, MIPS 0.943, MIPSEL 0.947, and x86 0.854 Macro-F1. The higher ten-seed average is driven mainly by better x86 results in nine later seeds; it does not erase the original result or justify replacing it with the most favorable seed.

## Threshold-transport comparison

| Source-only rule | Mean Macro-F1 | Mean DarkNexus recall | Worst Macro-F1 | Worst recall | Interpretation |
|---|---:|---:|---:|---:|---|
| Source minimax | **0.883** | 0.770 | 0.714 | 0.284 | Small average gain; no material repair of ARM |
| Source mean-optimal | 0.882 | 0.764 | 0.714 | 0.284 | Locked primary rule |
| Isotonic + 0.5 | 0.880 | 0.750 | 0.701 | 0.261 | No consistent benefit |
| Source-architecture median | 0.869 | 0.730 | 0.687 | 0.239 | Inferior overall |
| Balanced Platt + 0.5 | 0.868 | **0.830** | 0.716 | 0.284 | Recall gain at a Macro-F1 cost |
| Raw 0.5 | 0.803 | 0.568 | 0.492 | 0.000 | Unsuitable under domain shift |

Against the locked rule, the paired mean difference for source minimax was only +0.0011 Macro-F1; a matched-run bootstrap interval was −0.0036 to +0.0063. This does not support replacing the locked primary rule. Balanced Platt calibration increased mean recall by 0.0659 but reduced mean Macro-F1 by 0.0143. It can be reported as a sensitivity illustrating the precision–recall trade-off, not as a superior operating point.

## Scientific interpretation

The multi-seed analysis strengthens one conclusion and weakens another:

- It strengthens the claim that STRACE contains transferable family-ranking information for MIPS and MIPSEL.
- It weakens any claim of architecture-robust classification. ARM remains poor, and x86 thresholded performance varies materially with the random seed despite consistently high ranking metrics.

The threshold problem is not solved by source-only calibration. The small minimax gain is not practically or statistically persuasive, and calibration that raises recall produces additional false positives and lower Macro-F1. Target-label-free adaptation therefore remains an open engineering problem rather than a completed contribution.

## Publication decision

The work may proceed to a full manuscript only if framed as a conservative dataset-evaluation and negative-results study. The paper's center should be:

1. temporal confounding invalidating the linked benign-versus-malware target;
2. a malware-only family-transfer redesign;
3. the negative early-fusion result;
4. multi-seed evidence of architecture-dependent stability;
5. failure of source-only threshold transport to repair the weakest domain.

The manuscript must not claim a deployment-ready detector, architecture invariance, a new model architecture, or a generally superior calibration rule.

## Reproducibility artifacts

- `run_g10_multiseed_threshold_transport.py`
- `g10_validation/PILOT_06_MULTI_SEED_THRESHOLD_RESULTS.csv`
- `g10_validation/PILOT_06_MULTI_SEED_THRESHOLD_SUMMARY.csv`
- `g10_validation/PILOT_06_THRESHOLD_STRATEGY_OVERALL.csv`
- `g10_validation/PILOT_06_MULTI_SEED_THRESHOLD_PREDICTIONS.parquet`
- `g10_validation/PILOT_06_VALIDATION_PROTOCOL.json`

