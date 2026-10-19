# Revision v1.3.0

This release records the submission audit while preserving all locked estimates and claim boundaries.

## Changes

- Added validator checks for the four architecture-level cohort sizes and all 7,587 linked malware executions.
- Added validator checks that balanced accuracy and Matthews correlation coefficient are present for every primary outer fold.
- Linked the 133 raw ARM `Call_*` columns to the 87 architecture-common STRACE model variables and made clear that the 70-sample collision holds over the complete 22×133 published matrix.
- Redesigned Figure 4 to separate absolute class counts from within-family collision prevalence, preventing the much larger Mirai class from obscuring the DarkNexus result.
- Added the raw ARM audit and figure generator to the repository validation target.
- Removed obsolete duplicate figure exports and refreshed the repository checksum manifest.

## Claim boundary

No late-fusion, feature-selection, gradient-boosting, or cross-modal collision result was added because the public freeze does not contain the executable-level feature cache or held-out probability files needed to reproduce those analyses. The release does not infer results from summary tables and does not alter the primary model, folds, thresholds, or estimates.
