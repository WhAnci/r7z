# Reddit r/rust draft (Showcase Saturday)

**Title:** [Showcase] r7z – Rust 7-Zip clone with 4–20× lower memory usage

**Body:**

I built a Rust re-implementation of 7-Zip's core commands (`a`/`x`) and
benchmarked against the original C++ `7z`.

Repo: https://github.com/yourname/r7z

Highlights:
- Pure Rust, no C toolchain needed (`cargo build --release`)
- Peak memory ~85 MB vs 7z's ~376 MB (single thread) / ~1.8 GB (16 threads)
- Compression ratios match on text/binary (~0.02% / ~100%)
- CLI: `r7z a out.7z dir/ -m 9 -t 8`

Trade-off: slower (~3.5× on large text) because the underlying pure-Rust LZMA2
encoder isn't SIMD/thread-tuned like 7-Zip. Roadmap covers FFI (xz2), SIMD,
and proper multi-threading.

README in English/Korean/Chinese. Contributions welcome — see good-first-issues.