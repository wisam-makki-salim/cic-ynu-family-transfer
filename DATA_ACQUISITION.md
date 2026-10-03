# Data acquisition and integrity

## Official source

CIC-YNU-IoTMal 2026 is available from:

https://www.unb.ca/cic/datasets/ynu-iot-2026.html

Dataset article:

S. Dadkhah et al., “CIC-YNU-IoTMal: A comprehensive multilayer dataset for static and dynamic analysis of IoT malware behavior,” *Information Systems*, 102722, 2026.

## Expected local layout

```text
arm/Parquet Format/pcap.parquet
arm/Parquet Format/sar.parquet
arm/Parquet Format/strace.parquet
upload/pcap (1).parquet
upload/sar (1).parquet
upload/strace (1)(1).parquet
upload/pcap (2).parquet
upload/sar (2).parquet
upload/strace (2).parquet
x86/pcap.parquet
x86/sar.parquet
x86/strace.parquet
```

Files suffixed `(1)` are MIPS and files suffixed `(2)` are MIPSEL. The code verifies the embedded `Arch` field and does not rely only on filenames.

## SHA-256 checksums used in the frozen run

```text
0fd7ba0173201a7bb9daa46f46e733ea5b7c85d0e07303df2c04a118126d39a3  arm/Parquet Format/pcap.parquet
20d42b2785af2442ddddd2d997d2b65e58e9f84c73735429a04217b6c69a532f  arm/Parquet Format/sar.parquet
ba9f2e91e0e9a2dc9731f61f6591b8a2b7bde8e70585252a020f35f7e2e44106  arm/Parquet Format/strace.parquet
6af2346136a0d8d903e63f54d90aee4fec30bf9a5cf668d0eae4e0304f0da5ad  upload/pcap (1).parquet
497c1d7665db48f74b178a072c4ee0613e004cb3683ba7c770357dfc9fb18281  upload/sar (1).parquet
878fbf76ca864908b51aeeb9df3f38fba4395fd992c8e8c6193c580b46fcf7f6  upload/strace (1)(1).parquet
0f7ed84a58b6292962ee9a47aed7b3551363892ca4ed8a2be17fa7090fc5ef2a  upload/pcap (2).parquet
bd6eafebd08f5422df901169570d29b6fbec209e6b0f710368cfe797758aa67b  upload/sar (2).parquet
690ca06f534584e3ac1d73c4c0ac0877dddbb49f59665c48a35212e7e1fb7e9b  upload/strace (2).parquet
5e6b03998dbb960f8e6b1d08b8bb34e03a946da70333a0340d89c0b00fe5b352  x86/pcap.parquet
30de5c903d154f509e3732900704fbc1c37748bed3e6f99f55114d3b03733540  x86/sar.parquet
34a254d6b320a235887d8a8504d021f4f47d367072f5d4c82b788fbee80636be  x86/strace.parquet
```

If official files are repackaged without changing their tabular content, byte-level hashes may differ. In that case, record the new hashes and rerun the schema and linkage audits before model execution.

## Exclusions

- Dataset bytes are not stored in this repository.
- `Unknown` is excluded because it is absent from the linked STRACE cohort and lacks a defensible family attribution.
- Non-SHA scenario identifiers are excluded.
- The analysis unit is one executable hash, never a telemetry row.

