# Pilot 06 — ARM Error-Cluster Audit

Date: 2026-10-01  
Scope: diagnostic analysis only; no model, feature, threshold, or primary-outcome retuning  
Population: 2,809 ARM executables evaluated across ten fixed seeds

## Decision

**The remaining ARM weakness is primarily a target-domain feature–label collision, not collection-date drift and not ordinary random-forest seed noise.**

Of 88 ARM DarkNexus executables, 52 were misclassified in every seed, 11 changed status across seeds, and only 25 were correctly classified in every seed. By comparison, 2,715 of 2,721 Mirai executables were correct in every seed and six were seed-sensitive; none were wrong in a majority of seeds.

## Finding 1 — no detectable collection-date concentration

DarkNexus and Mirai each occurred across seven ARM collection dates. A 5,000-replicate label-permutation test found no evidence that error rates differed by date:

| Family | Dates | Permutation p-value |
|---|---:|---:|
| DarkNexus | 7 | 0.653 |
| Mirai | 7 | 0.392 |

The ARM failure should therefore not be attributed to a particular collection day on the available evidence.

## Finding 2 — short and behaviorally sparse DarkNexus traces

| Diagnostic variable | Majority-wrong median | Majority-correct median | Cliff's delta | Adjusted q-value |
|---|---:|---:|---:|---:|
| STRACE rows | 22 | 330 | −0.634 | <0.001 |
| Nonzero syscall types | 8 | 23 | −0.606 | <0.001 |
| Maximum syscall share | 0.463 | 0.822 | −0.490 | <0.001 |
| Syscall entropy | 1.541 | 0.985 | +0.548 | <0.001 |
| SAR execution span | 118 s | 118 s | +0.099 | 0.404 |

The identical SAR span but radically shorter STRACE output suggests incomplete or weak behavioral activation rather than a shorter scheduled sandbox run. This remains an inference; the dataset does not directly record activation success.

## Finding 3 — exact cross-label STRACE collision

Unsupervised clustering of Hellinger-transformed syscall profiles selected six DarkNexus clusters without using error labels. Error rates differed sharply across clusters (permutation p = 0.0002). One cluster contained 49 DarkNexus executables and all 49 were misclassified in every seed.

Every executable in this cluster had exactly 22 STRACE rows, eight nonzero syscall types, the same 87-dimensional relative-frequency vector, and the same mean model probability (0.03967).

The exact same STRACE vector and trace length occurred in 21 ARM Mirai executables. These Mirai samples were correctly classified in every seed. Thus, 70 target-domain samples with different family labels are observationally identical under the locked STRACE representation:

| Label | Samples sharing the exact profile |
|---|---:|
| DarkNexus | 49 |
| Mirai | 21 |
| **Total** | **70** |

This collision covers 55.7% of the ARM DarkNexus set. No deterministic classifier using only these 87 relative syscall-frequency features can assign different labels to these 70 samples. Changing the random seed, classifier, or decision threshold cannot resolve the collision without transferring errors from one family to the other.

The collision profile is dominated by process-loading behavior (`mmap2`, `mprotect`, `execve`, `open`, and `readlink`) and lacks the richer `read`, socket, connection, and send activity seen in better-classified DarkNexus profiles. The evidence is consistent with execution stopping or failing near process initialization, but this causal interpretation cannot be proven from the released telemetry alone.

## Scientific consequence

The precise interpretation is:

> Under ARM, more than half of the available DarkNexus executables collapse to a short syscall profile that is also observed in Mirai. The locked STRACE representation therefore contains an irreducible target-domain label collision for these samples.

This strengthens the dataset-evaluation contribution but further weakens any detector claim. It also explains why source-only threshold calibration could not repair ARM: the problem is missing discriminatory information, not only threshold placement.

The finding does not prove that the dataset labels are wrong. Plausible explanations include sandbox activation failure, early execution termination, a shared loader path, or family labels assigned at the binary level despite indistinguishable observed runtime behavior. The released variables do not distinguish among these explanations.

## Locked publication treatment

1. Retain all 88 ARM DarkNexus samples in the primary analysis.
2. Do not delete the 49 collision samples or add `strace_rows` to improve the headline result.
3. Report the collision as a post hoc diagnostic explaining a prespecified failure.
4. Do not claim a causal CPU-architecture effect.
5. A future sensitivity analysis may flag insufficient behavioral activation, but it must remain secondary and cannot replace the locked cohort.

## Reproducibility artifacts

- `run_g10_arm_error_audit.py`
- `g10_validation/arm_error_audit/PILOT_06_ARM_PER_HASH_ERROR_AUDIT.parquet`
- `g10_validation/arm_error_audit/PILOT_06_ARM_ERROR_STATUS.csv`
- `g10_validation/arm_error_audit/PILOT_06_ARM_ERROR_BY_DATE.csv`
- `g10_validation/arm_error_audit/PILOT_06_ARM_DATE_PERMUTATION_TESTS.csv`
- `g10_validation/arm_error_audit/PILOT_06_ARM_CONTINUOUS_ASSOCIATIONS.csv`
- `g10_validation/arm_error_audit/PILOT_06_ARM_PROFILE_CLUSTERS.csv`
- `g10_validation/arm_error_audit/PILOT_06_ARM_PROFILE_SYSCALLS.csv`
- `g10_validation/arm_error_audit/PILOT_06_ARM_EXACT_PROFILE_COLLISIONS.csv`
- `g10_validation/arm_error_audit/PILOT_06_ARM_ERROR_AUDIT_SUMMARY.json`

