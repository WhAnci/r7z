# Hacker News - Show HN draft

**Title:** Show HN: r7z - Rust re-implementation of 7-Zip core, lower memory and faster on large text

**URL:** https://github.com/WhAnci/r7z

**Text:**

Hi HN - I rewrote the core of 7-Zip (a/x/l/t) in Rust and benchmarked it
against the original C++ 7z.

Headline numbers (scenario A: 500 MB highly compressible text, single thread):
- 7z: 16.6s, 376 MB peak RSS
- r7z: 12.8s, 101 MB peak RSS

On 16 threads: 7z 2.6s / 1811 MB, r7z 1.6s / 812 MB.

Compression ratios match (0.02%). On large incompressible data r7z is also
faster (17.1s vs 64.5s on 200 MB random).

On many-small-files workloads 7z still wins (1.7s vs 42.8s on 10k files).

Why bother?
1. Memory: 7z solid-block arenas balloon to ~1.8 GB at 16 threads. r7z stays
   under ~1 GB and ~100 MB on a single thread.
2. A pure-Rust 7z reader/writer with no C toolchain at build time.
3. Multilingual README (English/Korean/Chinese).

Limitations: no SIMD match finder yet, single-threaded encoder in sevenz-turbo.
Roadmap in README. Happy to discuss methodology.
