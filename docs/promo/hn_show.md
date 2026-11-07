# Hacker News — Show HN draft

**Title:** Show HN: r7z – Rust re-implementation of 7-Zip core, ~4–20× less memory

**URL:** https://github.com/WhAnci/r7z

**Text:**

Hi HN — I rewrote the core of 7-Zip (`a`/`x`) in Rust and benchmarked it against
the original C++ `7z` on three scenarios (500 MB text, 10k small files, 200 MB
random binary).

Headline numbers (single thread, scenario A):
- 7z: 19.4s, 376 MB peak RSS
- r7z: 68.4s, 85 MB peak RSS

So r7z is ~3.5× slower but uses ~4.4× less memory. On 16 threads 7z pulls far
ahead (3.3s) because it has a tuned thread pool; r7z's encoder (sevenz-rust)
is effectively single-threaded today, which is the main bottleneck.

Compression ratios match on A/C (~0.02% / ~100%). On B (many small files) 7z
wins (0.28% vs 1.47%) thanks to solid blocks.

Why bother? Two reasons:
1. Memory: 7z's solid-block arenas balloon to ~1.8 GB at 16 threads. r7z stays
   under 100 MB. Useful on constrained hosts.
2. A pure-Rust 7z reader/writer with no C toolchain at build time.

Honest limitations: no SIMD match finder, no level/thread knobs exposed by the
underlying crate yet. Roadmap in README. Happy to discuss methodology.