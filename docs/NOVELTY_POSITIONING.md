# Novelty positioning against the August 2026 adjacent preprint

Adjacent work: Zhang, Xing, Guo, and Li, *Evaluation Pitfalls and Multimodal Baselines for the CIC-YNU-IoTMal2026 IoT Malware Dataset*, Research Square, posted 26 August 2026, DOI 10.21203/rs.3.rs-10427932/v1.

| Dimension | Zhang et al. | This study | Publication position |
|---|---|---|---|
| Primary target | Benign versus attack; Unknown treatment varied | DarkNexus versus Mirai after rejecting benign target | Distinct target and interpretation |
| Temporal validity | Notes temporal aspects remain unexplored because released PCAP features lack global timestamps | Uses linked SAR timestamps; finds complete benign–malware collection-period separation | Distinguishable contribution |
| Unit of analysis | Window and executable levels | Executable hash only for the final study | Overlap; no novelty claim |
| Multimodal baseline | PCAP, SAR, STRACE, fusion | Same modalities with robust aggregation | Overlap; no first-analysis claim |
| Architecture protocol | Ten-seed leave-one-architecture-out | Nested leave-one-architecture-out plus ten-seed validation | Strong overlap |
| ARM weakness | Benign-domain shift in attack detection | DarkNexus false negatives in family transfer | Related phenomenon, different label contrast |
| Threshold analysis | Target calibration and few-shot adaptation | Source-only mean, minimax, source-median, Platt, and isotonic rules | Partial overlap; narrower zero-target-label question |
| Exact collisions | Negligible PCAP-window binary-label collisions | One executable-level STRACE family-label collision: 49 DarkNexus and 21 Mirai | Distinct representation and target |
| Dormant/short traces | Short network footprints among missed attacks, dominated by dormant Mirai | Short identical ARM STRACE profiles among missed DarkNexus | Complementary, not a first dormant-sample claim |
| Fusion conclusion | Fusion unstable under ARM attack detection | Early fusion significantly worse than STRACE in family transfer | Distinct contrast under a different task |

## Claims retained

- Complete temporal confounding of the linked benign-versus-malware cohort.
- Malware-only DarkNexus-versus-Mirai transfer under strict architecture holdout.
- Negative early-fusion result for that family-transfer question.
- Exact executable-level ARM STRACE collision between two malware-family labels.

## Claims removed

- First systematic evaluation of CIC-YNU-IoTMal2026.
- First multimodal baseline for the dataset.
- First leave-one-architecture-out evaluation.
- General discovery that ARM is fragile.
- General discovery that threshold calibration can fail.
- General discovery of dormant malware in the dataset.

## Editorial implication

The manuscript must cite Zhang et al. in the Introduction, Related Work, and Discussion. Reviewers should be able to see immediately that the contribution is a narrower malware-family validity study rather than a competing broad dataset audit.

