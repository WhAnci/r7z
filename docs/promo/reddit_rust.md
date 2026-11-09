# Reddit r/rust draft (Showcase Saturday)

**Title:** [Showcase] r7z - Rust 7-Zip clone with lower memory and faster throughput

**Body:**

I built a Rust re-implementation of 7-Zip core commands (a/x/l/t) and
benchmarked against the original C++ 7z.

Repo: https://github.com/WhAnci/r7z

Highlights:
- Pure Rust, no C toolchain needed (cargo build --release)
- Peak memory ~101 MB vs 7z ~376 MB (single thread)
  (16 threads: 812 MB vs 1811 MB)
- Compression ratios match on text/binary (0.02% / 100%)
- Faster on large text (12.8s vs 16.6s, single thread)
  (16 threads: 1.6s vs 2.6s)
- CLI: r7z a out.7z dir/ -m 9 -t 8
- Shell completions for bash/elvish/fish/powershell/zsh

Trade-off: 7z still wins on many-small-files throughput (~1.7s vs ~42s).

README in English/Korean/Chinese. Contributions welcome - see CONTRIBUTING.md.
