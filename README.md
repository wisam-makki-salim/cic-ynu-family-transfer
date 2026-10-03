# Cross-Architecture IoT Malware Family Transfer

This repository reproduces a focused evaluation of the CIC-YNU-IoTMal 2026 dataset. The study first rejects the linked benign-versus-malware task because collection period perfectly separates the two labels. It then evaluates a narrower malware-only question: whether dynamic behavior distinguishes DarkNexus from Mirai when one CPU architecture is entirely absent from training.

The main result is methodological rather than architectural. STRACE relative-frequency features outperform PCAP, SAR, and early fusion, but transfer is uneven. MIPS and MIPSEL are stable; ARM remains weak because 49 DarkNexus and 21 Mirai executions share an identical complete 22-row published STRACE matrix. The rows are progressive call-count snapshots, not timestamped calls, and the release omits syscall order, arguments, return values, paths, and sandbox termination logs. Because some syscall counts disappear from terminal snapshots, the exact preprocessing semantics are not fully documented. No classifier or n-gram transformation derived from those matrices can separate the 70 executions.

## Repository contents

- `run_g4_audit.py`: linked-cohort leakage and validity audit.
- `run_g4_redesign_audit.py`: malware-only redesign checks.
- `run_g7_experiments.py`: feature aggregation, nested architecture validation, and modality ablation.
- `run_g7_sensitivity.py`: MIPSEL date-matched analysis.
- `run_g8_paired_bootstrap.py`: paired fusion contrasts.
- `run_g10_multiseed_threshold_transport.py`: ten-seed stability and source-only threshold transport.
- `run_g10_arm_error_audit.py`: locked ARM error diagnostic.
- `run_arm_raw_matrix_audit.py`: verifies the collision against the complete published ARM STRACE matrices.
- `results/`: summary results, split manifest, feature schema, and audit tables. Raw telemetry and executable bytes are not included.
- `docs/`: gate reports and the publication decision trail.

The manuscript is not included in this public repository. It will be linked here after a public preprint release or journal acceptance, subject to the target journal's sharing policy.

## Data

Download CIC-YNU-IoTMal 2026 from the official Canadian Institute for Cybersecurity page:

https://www.unb.ca/cic/datasets/ynu-iot-2026.html

Place the twelve Parquet files in the paths documented in `DATA_ACQUISITION.md`. The scripts do not redistribute dataset bytes.

## Environment

The frozen run used Python 3.12.14. Install the pinned dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Reproduction order

```bash
python run_g4_audit.py
python run_g4_redesign_audit.py
python run_g7_experiments.py
python run_g7_sensitivity.py
python run_g8_paired_bootstrap.py
python run_g10_multiseed_threshold_transport.py
python run_g10_arm_error_audit.py
python run_arm_raw_matrix_audit.py --arm-strace "/path/to/arm/Parquet Format/strace.parquet"
```

`run_g7_experiments.py` performs the expensive raw-data aggregation once and caches executable-level matrices. Later scripts consume those matrices and predictions. All preprocessing, model selection, probability calibration, and threshold selection are fitted without using the held-out architecture labels.

## Locked claims

The repository supports these claims:

1. In the linked three-modality cohort, benign and malicious executions occur in non-overlapping collection periods.
2. For DarkNexus versus Mirai, STRACE-only random forest is stronger than early multimodal fusion under leave-one-architecture-out evaluation.
3. MIPS and MIPSEL transfer is stable, while ARM transfer is weak and x86 operating points are seed-sensitive.
4. Source-only calibration does not solve threshold transport without a performance trade-off.
5. The complete published ARM STRACE matrix is shared by 49 DarkNexus and 21 Mirai executions, creating an exact observational label collision.

The repository does not support claims of generic malware detection, architecture-invariant performance, causal effects of CPU architecture, a new detection architecture, or a causal diagnosis of QEMU failure versus anti-analysis.

## Citation

See `CITATION.cff` for the software citation. Dataset users should also cite the original CIC-YNU-IoTMal article and the official dataset page. The paper citation will be added after a public preprint release or journal publication.

## License

Code is released under the MIT License. The dataset retains its original terms and is not redistributed here. Research reports and result tables remain the author's scholarly work.
