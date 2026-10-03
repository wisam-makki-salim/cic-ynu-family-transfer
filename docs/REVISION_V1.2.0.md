# Revision v1.2.0

This revision addresses the final pre-submission review while preserving all locked results.

## Changes

- Expanded the introduction with the operational role of family-level IoT malware evidence at the edge.
- Added a dedicated distribution-shift and adaptation subsection.
- Increased the integrated reference set from 23 to 30 verified sources.
- Added explicit in-text references to Figures 1 through 4 and standardized their captions.
- Characterized the collision matrix using the observed syscall support: `execve`, `open`, `mmap2`, `cacheflush`, `mprotect`, `readlink`, `brk`, `close`, and `munmap`.
- Corrected the description of the 22 rows from strictly cumulative traces to progressive call-count snapshots because `execve` and `open` disappear from the terminal snapshots.
- Strengthened the limitation arising from a single QEMU/OpenWrt environment and prohibited field-performance interpretation.

## Claim boundary

The revision does not claim that the 20-call prefix proves normal termination, dependency failure, QEMU failure, or anti-analysis. It also does not claim that bibliographic expansion or formatting alone guarantees acceptance in a Q1 journal.
