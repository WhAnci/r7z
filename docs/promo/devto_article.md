# dev.to article draft

**Title:** I rewrote 7-Zip in Rust — here's what I learned about memory

**Tags:** rust, performance, compression, cli

**Cover image:** docs/images/bench_memory.png

---

7-Zip is legendary for compression ratio and speed. It's also legendary for
eating RAM: compressing a 500 MB log file at 16 threads peaks at ~1.8 GB.

I wondered: how much of that is the algorithm, and how much is the
implementation? So I wrote `r7z`, a Rust clone of the core `a`/`x` commands,
and measured.

## The numbers

| Metric | r7z | 7z |
|---|---|---|
| Time (500 MB text, 1 thread) | 68.4 s | 19.4 s |
| Peak RSS (same) | 85 MB | 376 MB |
| Peak RSS (16 threads) | 85 MB | 1.8 GB |
| Ratio | 0.02% | 0.02% |

## Takeaways

1. **Ratios are essentially identical** — the algorithm dominates.
2. **Memory is an implementation choice.** 7z's solid-block arenas and per-thread
   buffers scale with thread count. r7z's bounded buffers don't.
3. **Speed is where C++ still wins** — SIMD range coder, tuned match finder,
   and a custom work-stealing pool. Pure Rust can't match that yet without
   `target-cpu=native`, SIMD intrinsics, or FFI to liblzma.

## What's next

- FFI path via `xz2` for parity speed
- SIMD CRC-32 / match finder
- Real multi-threading (currently single-threaded encoder)
- Solid-block size knob

Repo: https://github.com/WhAnci/r7z (English/Korean/Chinese README)