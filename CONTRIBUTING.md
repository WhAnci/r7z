# Contributing to r7z

Thanks for your interest! r7z is a small, focused project.

## Getting started

```bash
git clone https://github.com/WhAnci/r7z
cd r7z
cargo build --release
cargo test --release
cargo fmt --check
cargo clippy -- -D warnings
```

## Guidelines

- Keep PRs focused and small.
- Match existing code style (rustfmt default).
- Add tests for new behavior where practical.
- Update README/optimization docs when changing user-facing behavior.
- Be honest in benchmarks — methodology and limitations matter more than headlines.

## Good first issues

- Expose compression level to `sevenz-rust` encoder (or switch to `xz2` FFI).
- Real multi-threaded compression.
- SIMD CRC-32 / match finder.
- `--quiet` flag to disable progress bars.
- Shell completions via `clap_complete`.

## Code of conduct

Be kind and constructive. See CODE_OF_CONDUCT.md.