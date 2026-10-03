# CURRENT HANDOFF

## Project
Research OS: Wisam AutoResearch v1
Pilot: 06
Date: 2026-10-02

## Current state
Current gate: G7 manuscript revision
Status: PASS WITH RESTRICTIONS

## Locked research question
Can architecture-common dynamic features distinguish DarkNexus from Mirai when one CPU architecture is completely absent from training?

## Dataset
Name: CIC-YNU-IoTMal2026
Source: Canadian Institute for Cybersecurity
Version: 2026 release
Local files: linked PCAP, SAR, and STRACE parquet files for ARM, MIPS, MIPSEL, and x86
Analysis cohort: 7,587 linked executable hashes

## Locked protocol
Primary outcome: executable-level macro-F1
Primary exposure: held-out CPU architecture
Primary model: class-weighted random forest using 87 common STRACE relative-frequency features
Inference: nested leave-one-architecture-out evaluation
Robustness: modality ablation, paired bootstrap, ten seeds, source-only threshold transport, date matching, locked ARM diagnostic
Leakage rule: no held-out architecture labels in preprocessing, model selection, calibration, or threshold selection

## Results so far
Primary estimate: single-seed mean macro-F1 0.865; ten-seed mean 0.882
Uncertainty: full fusion minus STRACE -0.0243, 95% paired bootstrap interval -0.0404 to -0.0109
Robustness: MIPS and MIPSEL stable; ARM remains weak
Interpretation boundary: the complete published 22-row STRACE matrix is identical for 49 DarkNexus and 21 Mirai ARM hashes; the cause of the short observation is not identifiable

## Decisions already made
- Permanently reject benign-versus-malware modeling because collection period determines the label.
- Retain DarkNexus-versus-Mirai as a narrow family-transfer question.
- Do not claim that n-grams, QEMU failure, or anti-analysis explain or repair the collision.
- Do not report a third-family model from five ARM Gafgyt samples.
- Treat the single QEMU/OpenWrt environment as an external-validity limitation.

## Do NOT redo
- G3 linkage audit
- Locked G7 experiments
- Multi-seed and threshold-transport analysis
- Raw ARM collision identity audit

## Open issues
- Select the target journal and convert to its exact submission template.
- Obtain physical-device or independent-emulator validation if a broader deployment claim is desired.
- Conduct final citation metadata and language audit before submission.

## Required next action
Choose the target journal, then format the manuscript and cover letter to that journal without changing the locked claims.
