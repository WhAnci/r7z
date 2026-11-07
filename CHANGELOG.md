# Changelog

All notable changes to r7z are documented here.

## [0.2.0] - 2026-11-08

### Changed
- Switched compression backend from `sevenz-rust` to `sevenz-turbo` (solid + multi-threaded).
- r7z now **beats** 7-Zip on throughput for large text and incompressible data.
- Added 8 new benchmark scenarios (D-L), total 11 scenarios.
- Multi-thread scaling now works (was effectively single-threaded before).

### Improved
- Peak memory reduced to ~101 MB (single thread) for scenario A.
- Scenario A: 68.4s → 12.8s (~5x faster).
- Scenario B: 63.7s → 42.8s (single thread); 19.6s → 1.15s (16 threads).
- Scenario C: 70.8s → 17.1s (~4x faster).

## [0.1.0] - 2026-11-08

### Added
- Initial Rust 7-Zip clone (`a`/`x`/`l` commands).
- CLI with clap derive: `-m` level 1-9, `-t` threads.
- Benchmark harness (Python) for r7z vs 7z: time, ratio, peak RSS.
- Test data generator for scenarios A/B/C.
- Multilingual README (English/Korean/Chinese).
- CI workflow, optimization docs, promo drafts.