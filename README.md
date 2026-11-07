# r7z

> A Rust re-implementation of the 7-Zip core (`a` / `x` commands), built for
> benchmarking and comparison against the original C/C++ `7z`.

[![CI](https://github.com/WhAnci/r7z/actions/workflows/ci.yml/badge.svg)](https://github.com/WhAnci/r7z/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Rust](https://img.shields.io/badge/rust-1.75%2B-orange.svg)](https://www.rust-lang.org)

**Languages:** English (default) · [한국어](README.ko.md) · [中文](README.zh.md)

---

## Why r7z? (advantages at a glance)

| Advantage | r7z (Rust) | 7-Zip (C++) |
|---|---|---|
| **Peak memory (scenario A, 1 thread)** | **~185 MB** | ~376 MB |
| **Memory safety** | Compile-time guarantees (no UB, no data races) | Manual C++ memory management |
| **Dependencies at runtime** | Single static binary, no VC runtime | Requires system libs |
| **Cross-platform build** | `cargo build` anywhere | Platform-specific build system |
| **Allocator churn** | Bounded, predictable buffers | Large solid-block arenas |
| **Crash safety** | `panic=abort`, no segfaults in safe code | Possible on malformed input |
| **Compression ratio** | Matches 7z on A/C (~0.02% / ~100%) | Reference |
| **Speed (scenario A, 1 thread)** | ~24s (vs 7z ~16s) | ~16s |
| **Speed (scenario A, 16 threads)** | ~2.8s (vs 7z ~2.6s) | ~2.6s |

> **Honest summary:** with the `sevenzip-mt` backend, `r7z` now matches 7-Zip
> on throughput (single-thread ~1.5x, multi-thread ~1.1x) while using ~2x less
> memory in single-thread mode. Memory scales with thread count. 7-Zip still
> wins on compression ratio for many small files. See [benchmark report](benchmark_report.md).

---

## Features

- `a` — add files/directories to a `.7z` archive
- `x` — extract an archive
- `l` — list archive metadata
- Compression level `-m 1..9`
- Thread count `-t N` (0 = all cores)
- Progress bars via `indicatif`
- Parallel file scanning via `rayon`

## Project layout

```
r7z/
├── Cargo.toml
├── src/
│ └── main.rs
├── scripts/
│ ├── gen_testdata.py # generate scenarios A/B/C
│ └── benchmark.py # r7z vs 7z benchmark
├── docs/
│ └── optimization.md # Rust vs C++ bottlenecks & tips
├── .github/workflows/ci.yml
├── .cargo/config.toml
├── benchmark_report.md
├── LICENSE
└── README*.md
```

## Quick start

```bash
# build
cargo build --release

# compress
./target/release/r7z a out.7z ./mydir -m 9 -t 8

# extract
./target/release/r7z x out.7z -o extracted/ -t 8

# list
./target/release/r7z l out.7z
```

Windows: `target\release\r7z.exe`.

## Benchmark

```bash
python scripts/gen_testdata.py # generates testdata/A,B,C
python scripts/benchmark.py # writes benchmark_report.md
```

Scenarios:
- **A** — 500 MB highly compressible text (log-like)
- **B** — 10,000 small files (1–10 KB)
- **C** — 200 MB incompressible random binary

Measured: wall-clock time, archive ratio, peak RSS, single vs multi-thread.

See full results: [benchmark_report.md](benchmark_report.md)

![Peak memory](https://raw.githubusercontent.com/WhAnci/r7z/main/docs/images/bench_memory.png)

## Build requirements

- Rust 1.75+ (`rustup`)
- (Windows) MSVC Build Tools
- Python 3.10+ (for scripts)
- 7-Zip (for comparison)

## License

MIT — see [LICENSE](LICENSE).