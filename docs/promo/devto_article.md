# dev.to article draft

**Title:** r7z - Rust 7-Zip clone with lower memory and faster throughput
**Tags:** rust, performance, compression, cli
**Cover image:** docs/images/bench_memory.png

---

7-Zip is legendary for compression ratio and speed. It is also legendary for
eating RAM: compressing a 500 MB log file at 16 threads peaks at ~1.8 GB.

I wondered how much of that is the algorithm and how much is the
implementation. So I wrote r7z, a Rust clone of the core a/x/l/t commands,
and measured.

## The numbers (scenario A: 500 MB highly compressible text)

| Metric | r7z | 7z |
|---|---|---|
| Time (1 thread) | 12.8 s | 16.6 s |
| Time (16 threads) | 1.6 s | 2.6 s |
| Peak RSS (1 thread) | 101 MB | 376 MB |
| Peak RSS (16 threads) | 812 MB | 1811 MB |
| Ratio | 0.02% | 0.02% |

r7z is faster on large text and uses 2-4x less memory, while matching the ratio.
On many-small-files workloads 7z still wins (~1.7s vs ~42s).

## Takeaways

1. Ratios are essentially identical - the algorithm dominates.
2. Memory is an implementation choice. 7z solid-block arenas and per-thread
   buffers scale with thread count; r7z bounded buffers do not.
3. Rust can win on throughput too when the encoder is well-tuned.

## Features

- a/x/l/t commands, -m 1..9, -t N, -p, -o, -y
- Shell completions (bash/elvish/fish/powershell/zsh)
- Progress bars, parallel file scanning
- Pure Rust, cargo build --release, no C toolchain

Repo: https://github.com/WhAnci/r7z (English/Korean/Chinese README)
