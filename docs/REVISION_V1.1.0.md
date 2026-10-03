# Revision v1.1.0

This revision responds to an external-validity and representation audit without changing the locked predictive results.

## Added evidence

- Verified the ARM cross-label collision against the complete published STRACE matrices.
- Confirmed that all 49 DarkNexus and 21 Mirai collision samples share one identical 22-row matrix.
- Established that the rows are cumulative call-count snapshots with a maximum row sum of 20, not 22 timestamped calls.
- Documented the absence of sequence indices, timestamps, syscall arguments, return values, paths, and termination logs.
- Added a reproducible raw-matrix audit script and released its hash-level output.

## Manuscript changes

- Added a validity-first methodological pipeline.
- Expanded and integrated related work on IoT datasets, cross-architecture malware analysis, behavioral variability, execution duration, and evasion.
- Reframed the ARM result as an observational identifiability bound: no n-gram derived from identical released matrices can separate the conflicting labels.
- Distinguished established fusion evidence from the untested curse-of-dimensionality hypothesis.
- Added an additional-family feasibility appendix. Gafgyt is present in all architectures but has only five linked ARM hashes, precluding reliable four-domain inference.
- Explicitly retained the short-trace cause as unknown; the release cannot distinguish emulator failure, missing dependencies, normal exit, evasion, or collection truncation.

The revision does not claim that QEMU failure or anti-analysis caused the collision, does not report an underpowered third-family score, and does not alter the frozen v1.0.0 result tables.
