# r7z

> 7-Zip 核心（`a` / `x` 命令）的 Rust 重新实现，用于与原版 C/C++ `7z` 进行性能对比。

[![CI](https://github.com/yourname/r7z/actions/workflows/ci.yml/badge.svg)](https://github.com/yourname/r7z/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**语言：** [English](README.md) (默认) · [한국어](README.ko.md) · 中文

---

## r7z 的优势（一目了然）

| 优势 | r7z (Rust) | 7-Zip (C++) |
|---|---|---|
| **峰值内存（场景 A）** | **~85 MB** | ~376 MB (1 线程) / ~1.8 GB (16 线程) |
| **内存安全** | 编译期保证（无 UB、无数据竞争） | 手动 C++ 内存管理 |
| **运行时依赖** | 单一静态二进制 | 需要系统库 |
| **跨平台构建** | 任意平台 `cargo build` | 平台相关构建系统 |
| **分配器抖动** | 有界、可预测的缓冲区 | 大型 solid 块 arena |
| **崩溃安全性** | `panic=abort`，安全代码无段错误 | 异常输入可能触发 |
| **压缩率** | A/C 与 7z 相当 (~0.02% / ~100%) | 基准 |
| **速度** | 较慢（已改进，A 约 1.8 倍） | 更快（SIMD + 调优线程） |

> **坦诚总结：** `r7z` 用原始速度换取 **4–20 倍更低的内存占用**、内存安全与简单的跨平台构建。吞吐量与多线程扩展性仍然是 7-Zip 的强项。详见 [基准报告](benchmark_report.md)。

---

## 功能

- `a` — 将文件/目录加入 `.7z` 压缩包
- `x` — 解压压缩包
- `l` — 列出压缩包元数据
- 压缩级别 `-m 1..9`
- 线程数 `-t N`（0 = 所有核心）
- 基于 `indicatif` 的进度条
- 基于 `rayon` 的并行文件扫描

## 项目结构

```
r7z/
├── Cargo.toml
├── src/
│ └── main.rs
├── scripts/
│ ├── gen_testdata.py
│ └── benchmark.py
├── docs/
│ └── optimization.md
├── .github/workflows/ci.yml
├── .cargo/config.toml
├── benchmark_report.md
├── LICENSE
└── README*.md
```

## 快速开始

```bash
cargo build --release
./target/release/r7z a out.7z ./mydir -m 9 -t 8
./target/release/r7z x out.7z -o extracted/ -t 8
./target/release/r7z l out.7z
```

Windows: `target\release\r7z.exe`。

## 基准测试

```bash
python scripts/gen_testdata.py
python scripts/benchmark.py
```

详细结果：[benchmark_report.md](benchmark_report.md)

## 许可证

MIT — [LICENSE](LICENSE)。