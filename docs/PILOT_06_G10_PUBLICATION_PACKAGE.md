# Pilot 06 — G10 Publication Package

Date: 2026-10-01

## Recommended title

**Cross-Architecture Transfer of Dynamic IoT Malware Family Signatures: A Leakage-Aware Mirai–DarkNexus Study on CIC-YNU-IoTMal2026**

Alternative results-led title:

**When More Telemetry Hurts: STRACE Outperforms Multimodal Fusion for Cross-Architecture Mirai–DarkNexus Discrimination**

The first title is safer for a journal submission. The second is suitable only if multi-seed testing confirms the fusion degradation.

## Problem

The CIC-YNU-IoTMal2026 release invites benign-versus-malware, multimodal, and cross-architecture experiments. In the linked three-modality cohort, benign and malicious executions were collected in non-overlapping periods. A conventional detector can therefore learn collection period rather than malware behavior. The engineering problem is to identify a target and evaluation protocol that measures transferable behavioral information without this confounding.

## Evidence gap

Existing work already provides executable-level, multimodal, and leave-one-architecture-out baselines for this dataset. It does not settle whether two malware families can be distinguished on a completely unseen architecture after rejecting the temporally confounded benign target, nor whether adding network and system-activity telemetry improves a system-call baseline in that restricted task.

## Locked research question

How accurately do architecture-common dynamic behavioral features distinguish DarkNexus from Mirai on a completely held-out CPU architecture, and does multimodal fusion improve Macro-F1 and DarkNexus recall over the strongest unimodal baseline without exploiting collection artifacts?

## Dataset and provenance

- Dataset: CIC-YNU-IoTMal 2026.
- Official source: https://www.unb.ca/cic/datasets/ynu-iot-2026.html
- Dataset article: https://doi.org/10.1016/j.is.2026.102722
- Modalities: PCAP, SAR, STRACE.
- Architectures: ARM, MIPS, MIPSEL, x86.
- Analysis cohort: 7,587 hashes present in all three modalities.
- Classes: 7,368 Mirai and 219 DarkNexus.

## Methods

- Sampling unit: executable SHA-256 hash.
- Outer validation: four leave-one-architecture-out folds.
- Inner validation: architecture-grouped selection among the three training architectures.
- Threshold selection: training architectures only, optimizing mean inner-fold Macro-F1.
- PCAP and SAR: median, 25th percentile, and 75th percentile for architecture-common numeric variables.
- STRACE: relative architecture-common syscall frequencies; malformed labels and total trace length excluded.
- Models: class-weighted logistic regression and class-weighted random forest.
- Primary metric: mean Macro-F1 across outer folds.
- Secondary metrics: DarkNexus recall, balanced accuracy, MCC, DarkNexus PR-AUC, ROC-AUC.
- Uncertainty: 500 class-stratified bootstrap replicates per outer fold.
- Fusion contrast: 2,000 paired bootstrap replicates across outer folds.

## Main results

The strongest model was STRACE-only random forest:

- mean Macro-F1: 0.865;
- minimum architecture Macro-F1: 0.714 on ARM;
- mean DarkNexus recall: 0.707;
- mean DarkNexus PR-AUC: 0.812;
- mean ROC-AUC: 0.953.

Full fusion reached mean Macro-F1 0.840 and reduced Macro-F1 relative to STRACE by 0.0243. The paired bootstrap 95% confidence interval was −0.0404 to −0.0109. PCAP + STRACE also underperformed STRACE by 0.0135, with 95% CI −0.0267 to −0.0023.

Generalization was heterogeneous. DarkNexus recall was 0.295 on ARM, 0.952 on MIPS, 1.000 on MIPSEL, and 0.580 on x86. High ROC-AUC with weaker thresholded recall on ARM and x86 indicates an operating-point transport problem rather than complete loss of ranking information.

## Robustness checks completed

- timestamp and collection-artifact-only falsification baselines;
- robust instead of mean-based PCAP/SAR aggregation;
- strict exclusion of row counts and total trace length;
- unimodal and leave-one-modality-out ablations;
- executable-level bootstrap confidence intervals;
- paired bootstrap comparison of fusion against STRACE;
- MIPSEL date matching, retaining all 39 DarkNexus and 1,469 same-day Mirai samples.

## Interpretation

System-call composition contains transferable family information for this restricted pair, but transfer is not uniform across architectures. Extra telemetry does not automatically add useful information. In this experiment, early fusion introduces noise or architecture-specific variation and performs worse than the simpler STRACE representation.

The findings do not show generic malware detection, causal effects of CPU architecture, or deployment-ready performance. Architecture holdout also changes the executable population because hashes do not repeat across architectures.

## Defensible contribution

1. A documented rejection of the dataset's temporally confounded linked benign-versus-malware target.
2. A malware-only, executable-level family-transfer protocol across four architectures.
3. A negative multimodal result showing that robust early fusion reduces Macro-F1 relative to STRACE alone.
4. A diagnosis of threshold-transfer fragility, especially for ARM and x86.
5. Reproducible code, per-fold predictions, uncertainty estimates, ablations, and a date-matched sensitivity analysis.

## Claims that are prohibited

- first multimodal analysis of CIC-YNU-IoTMal2026;
- first cross-architecture evaluation of the dataset;
- generic IoT malware detection;
- architecture-invariant performance;
- causal attribution of errors to CPU architecture;
- proof that STRACE will dominate fusion in other datasets or family pairs.

## Post-package validation completed

The required ten-seed random-forest stability analysis and target-label-free threshold-transport analysis are complete. Across 40 seed-architecture runs, the locked source-mean rule achieved mean Macro-F1 0.882 and mean DarkNexus recall 0.764. MIPS and MIPSEL were stable, ARM remained weak, and x86 thresholded recall ranged from 0.500 to 0.900. Source minimax thresholding changed mean Macro-F1 by only +0.0011 relative to the locked rule, while balanced Platt mapping raised recall but reduced Macro-F1. No source-only rule solved threshold transport without a trade-off. See `PILOT_06_G10_VALIDATION_REPORT.md`.

The subsequent locked ARM diagnostic found that 49 DarkNexus and 21 Mirai executables share an exactly identical 87-dimensional STRACE profile and an identical 22-row trace. The model necessarily assigns these samples the same probability. This collision covers 55.7% of ARM DarkNexus and explains most persistent false negatives. Errors did not concentrate by collection date. See `PILOT_06_G10_ARM_ERROR_AUDIT.md`.

## Remaining work before submission

Required for a full paper:

1. Compare the final protocol and results line by line with the August 2026 adjacent preprint and the recent family-classification paper.
2. Freeze a public repository with environment versions, checksums, code, feature schema, split manifest, results, and a data-acquisition note. Do not redistribute restricted dataset bytes.

Optional extension:

- late probability fusion can be tested once as a prespecified secondary analysis. It should be reported as exploratory and must not replace the negative early-fusion result.

## Publication strategy

Best fit is a focused dataset-evaluation, reproducibility, or cybersecurity methods paper. A full high-impact detection paper is not supported because the adjacent preprint already owns the broad audit and cross-architecture baseline space, while the current positive class is small.

Potential venue classes to verify at submission time:

- Computers & Security;
- Journal of Information Security and Applications;
- Internet of Things;
- a reproducibility or dataset track at a cybersecurity conference.

Journal scope, fees, indexing, and current review model must be checked immediately before submission.

## G10 decision

**Status: PASS WITH MAJOR RESTRICTIONS**

The study has a defensible, narrow publication path as a dataset-evaluation and negative-results paper. Multi-seed validation confirms stable MIPS/MIPSEL transfer but persistent ARM weakness and x86 operating-point sensitivity. Threshold transport remains unsolved. A full manuscript may now be drafted only under this restricted framing; the work does not support a broad detection or deployment claim.
