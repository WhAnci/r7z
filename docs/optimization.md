# Optimization Guide: Rust vs C++ 7-Zip

Bottlenecks observed in `r7z` (pure-Rust, `sevenz-rust`) and how to close the gap
with the original C++ 7-Zip engine.

## 1. LZMA2 encoder is the hot path
`sevenz-rust` is pure Rust; 7-Zip uses hand-tuned SIMD (SSE/AVX) range coder
and match finder.
- Enable `target-cpu=native` (see `.cargo/config.toml`) to let LLVM auto-vectorise.
- For byte-for-byte 7-Zip parity / max speed, switch to `xz2` (liblzma FFI).

## 2. Match finder memory
LZMA2 hash chain / binary tree can allocate hundreds of MB at level 9.
Pre-allocate with `Vec::with_capacity`, reuse buffers, use `mimalloc`/`jemallocator`.

## 3. I/O buffering
Default 8 KiB buffers bottleneck on fast NVMe. Use 1-4 MiB `BufReader`/`BufWriter`
or memory-map inputs with `memmap2`.

## 4. Many tiny files (scenario B)
Per-file task spawning dominates. Batch into chunks (`par_chunks`) and use a
single producer with a bounded channel.

## 5. Solid block sizing
Too-large blocks hurt random access and memory. Tune block size (~64-256 MiB).

## 6. Progress reporting
`indicatif` redraws cost CPU. Throttle or disable in benchmark mode.

## 7. Threading model
Set `num_threads` explicitly; avoid nested parallelism.

## 8. SIMD
Add `std::simd` / `wide` for CRC-32 and match-finding hot loops.

## 9. PGO
Build with profile-generate then profile-use for 5-15% encoder gains.

## 10. Memory measurement
Use `/usr/bin/time -v` (Linux) or Working Set (Windows); compare with `jemalloc`.