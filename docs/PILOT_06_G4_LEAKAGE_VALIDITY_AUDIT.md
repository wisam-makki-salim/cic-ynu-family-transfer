# Pilot 06 — G4 Leakage and Validity Audit

Date: 2026-10-01  
Dataset: CIC-YNU IoT Malware Sandbox  
Architectures: x86, ARM, MIPS, MIPSEL

## Gate decision

**G4: FAIL FOR THE PROPOSED BENIGN-VS-MALWARE QUESTION**

The three-channel dataset is structurally linkable, but the proposed supervised target is completely confounded with collection time. Benign executions were collected in January 2026, while malware executions were collected between April and September 2025. There is no temporal overlap within any architecture. A classifier using only the absolute SAR start time achieved ROC AUC 1.000 and balanced accuracy 1.000 in every leave-one-architecture-out fold. Consequently, a high-performing detector could identify the collection batch rather than malware behavior.

This is a dataset-design failure for the proposed target, not a model-selection problem. Removing the timestamp column is necessary but insufficient because system state, tool versions, background services, network conditions, and other telemetry can remain proxies for the disjoint collection periods.

## Verified cohort

One record was created per valid SHA-256 `Hash` present in PCAP, SAR, and STRACE. `Unknown` and non-SHA scenario identifiers were excluded.

| Architecture | Benign | Malware | Total |
|---|---:|---:|---:|
| x86 | 2,570 | 1,692 | 4,262 |
| ARM | 1,945 | 2,847 | 4,792 |
| MIPS | 2,433 | 1,612 | 4,045 |
| MIPSEL | 2,375 | 1,549 | 3,924 |
| **Total** | **9,323** | **7,700** | **17,023** |

The manifest contains zero missing key fields and zero repeated hashes across architecture partitions.

## Critical temporal confounding

| Architecture | Malware collection range | Benign collection range | Overlap |
|---|---|---|---|
| x86 | 2025-06-27 to 2025-06-28 | 2026-01-15 to 2026-01-17 | None |
| ARM | 2025-04-26 to 2025-06-26 | 2026-01-03 to 2026-01-04 | None |
| MIPS | 2025-06-28 to 2025-06-29 | 2026-01-05 to 2026-01-06 | None |
| MIPSEL | 2025-06-29 to 2025-09-23 | 2026-01-07 to 2026-01-09 | None |

### Artifact-only leave-one-architecture-out test

Predictors: PCAP row count, SAR row count, STRACE row count, SAR execution span, and absolute SAR start time. No behavioral values were used.

| Held-out architecture | ROC AUC | Balanced accuracy |
|---|---:|---:|
| x86 | 1.000 | 1.000 |
| ARM | 1.000 | 1.000 |
| MIPS | 1.000 | 1.000 |
| MIPSEL | 1.000 | 1.000 |

Absolute time alone produced the same perfect results. PCAP row count alone also transferred strongly: ROC AUC 0.991 for x86, 0.760 for ARM, 0.999 for MIPS, and 0.998 for MIPSEL. STRACE row count alone produced ROC AUC 0.671–0.811. These counts reflect execution duration/activity and collection mechanics; they cannot be treated as ordinary predictors without a fixed observation-window design.

## Feature-space validity

- PCAP has a stable 42-column schema across all four architectures.
- SAR has 334 common columns but 520 columns in the union. Interrupt, interface, serial, softnet, and CPU-frequency fields differ by architecture.
- STRACE has only 90 common columns out of 184 in the union. Architecture-specific syscall names and malformed/truncated labels occur, including examples such as `Call_wri`, `Call_rt_si`, and `Call_cloc`.
- Using the union with missing-value indicators would reveal architecture directly. Cross-architecture models must use a prespecified common feature intersection or a carefully defined semantic mapping.

## Leakage rules fixed by this audit

The following cannot be predictors in a valid primary model:

- `Hash`, `MalwareFamily`, and any derived target encoding;
- `Arch` in architecture-transfer evaluation;
- absolute `timestamp`, calendar fields, or execution order;
- `interval` and modality row counts as ordinary predictors;
- architecture-specific missingness patterns or columns absent from the held-out architecture.

All preprocessing, aggregation, feature selection, scaling, and imputation must be learned within the training architectures only.

## Other validity limits

1. The linked cohort excludes `Unknown`, so results cannot generalize to those executions.
2. Rare malware families cannot support independent classification claims.
3. Architecture holdout changes architecture and executable population simultaneously; it is a domain-generalization test, not a causal architecture effect.
4. PCAP, SAR, and STRACE row counts differ markedly by label and architecture. Random row sampling or row-level splitting is invalid.
5. Dropping explicit collection artifacts does not prove that latent batch effects have been removed.

## Scientific decision

Do **not** proceed to G5 with the binary benign-versus-malware question on the released data. A credible repair requires at least one of the following:

1. obtain or generate temporally interleaved benign and malware executions under the same environment and observation protocol; or
2. redefine the study so the target does not rely on the confounded benign comparison, followed by a new G1/G4 check for that exact question.

The safer rescue candidate is a narrower malware-only cross-architecture study, probably centered on Mirai because it is the only family with substantial support across architectures. That candidate is not yet locked: its class composition, novelty, and valid comparator must be checked before G5.

## Decision log

- Gate: G4
- Status: **FAIL / RETURN TO G1–G4 FOR REDESIGN**
- Key evidence: complete label–time separation; timestamp-only AUC 1.000 in all architecture holdouts; strong row-count predictability; cross-architecture SAR/STRACE schema mismatch.
- Decision: reject the current binary detection design.
- Next action: evaluate a malware-only, cross-architecture question and kill it if class support or novelty is inadequate; alternatively acquire temporally matched benign executions.

