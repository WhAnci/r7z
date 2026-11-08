# r7z

> 7-Zip 核心（`a` / `x` 命令）的 Rust 重新实现，用于与原版 C/C++ `7z` 进行性能对比。

[![CI](https://github.com/WhAnci/r7z/actions/workflows/ci.yml/badge.svg)](https://github.com/WhAnci/r7z/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Rust](https://img.shields.io/badge/rust-1.75%2B-orange.svg)](https://www.rust-lang.org)

**语言：** [English](README.md) (默认) · [한국어](README.ko.md) · 中文

![Demo](docs/demo.gif)

---

## 权衡 (r7z vs 7-Zip)

| | r7z (Rust) | 7-Zip (C++) |
|---|---|---|
| **速度 (大文本, 1 线程)** | ~12.8s | ~16.6s |
| **速度 (大文本, 16 线程)** | ~1.6s | ~2.6s |
| **速度 (大量小文件)** | 较慢 (~42s) | 较快 (~1.7s) |
| **峰值内存 (1 线程)** | ~101 MB | ~376 MB |
| **峰值内存 (16 线程)** | ~812 MB | ~1811 MB |
| **压缩率** | 与 7z 相当 | 基准 |
| **内存安全** | 编译期 | 手动管理 |
| **运行时依赖** | 无 (静态二进制) | 系统库 |
| **跨平台构建** | `cargo build` | 平台相关 |
| **崩溃安全** | `panic=abort` | 异常输入可能触发 |

> **总结：** r7z 在大文本/不可压/混合数据上更快，内存少 2-4 倍。
> 大量小文件处理上 7-Zip 仍占优。详见 [基准报告](benchmark_report.md)。

---

## 功能

- `a` — 将文件/目录加入 `.7z` 压缩包
- `x` — 解压压缩包
- `l` — 列出压缩包元数据
- `t` — 测试压缩包完整性
- 压缩级别 `-m 1..9`（别名 `--mx`）
- 线程数 `-t N`（0 = 所有核心，别名 `--mmt`）
- 密码加密 `-p <password>`
- 自动确认 `-y`
- Shell 自动补全：`r7z completions <bash|zsh|fish|powershell>`
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
# 构建
cargo build --release

# 压缩
./target/release/r7z a out.7z ./mydir -m 9 -t 8

# 解压
./target/release/r7z x out.7z -o extracted/ -t 8

# 列表
./target/release/r7z l out.7z
```

Windows: `target\release\r7z.exe`。

## 基准测试

```bash
python scripts/gen_testdata.py # generates testdata/A,B,C
python scripts/benchmark.py # writes benchmark_report.md
```

场景 (11 个，完整结果见 benchmark_report.md)：
- **A** — 500 MB 高可压文本
- **B** — 10,000 个小文件 (1-10 KB)
- **C** — 200 MB 不可压随机数据
- **D** — 200 MB 软件包 (二进制)
- **E** — 472 MB 游戏资源
- **F** — 213 MB 用户备份
- **G** — 1 GB 冷存储 (级别 9)
- **H** — 22 MB 邮件/分享包
- **I** — 1 GB SQL 转储
- **J** — 1 GB VM 磁盘镜像
- **L** — 2 GB 单个超大文件

实测：墙钟时间、压缩比、峰值 RSS、单线程 vs 多线程。

详细结果：[benchmark_report.md](benchmark_report.md)


![压缩时间 (1 线程)](https://raw.githubusercontent.com/WhAnci/r7z/main/docs/images/bench_time_compress_1t.png)

![压缩时间 (16 线程)](https://raw.githubusercontent.com/WhAnci/r7z/main/docs/images/bench_time_compress_16t.png)

![速度提升 (r7z vs 7z)](https://raw.githubusercontent.com/WhAnci/r7z/main/docs/images/bench_speedup.png)

![解压时间](https://raw.githubusercontent.com/WhAnci/r7z/main/docs/images/bench_time_decompress.png)

![峰值内存](https://raw.githubusercontent.com/WhAnci/r7z/main/docs/images/bench_memory.png)


## 构建要求

- Rust 1.75+ (`rustup`)
- (Windows) MSVC Build Tools
- Python 3.10+ (用于脚本)
- 7-Zip (用于对比)

## 基准测试摘要（单线程，压缩）

| 场景 | r7z 时间 | 7z 时间 | r7z 内存 | 7z 内存 | r7z 比率 | 7z 比率 |
|---|---|---|---|---|---|---|
| A 大文本 (500MB) | 12.8s | 16.6s | 101MB | 376MB | 0.02% | 0.02% |
| B 小文件 (10k) | 42.8s | 1.7s | 116MB | 381MB | 0.28% | 0.28% |
| C 随机 (200MB) | 17.1s | 64.5s | 101MB | 377MB | 100% | 100% |
| D 软件包 (200MB) | 10.0s | 26.0s | 102MB | 377MB | 50% | 50% |
| E 游戏资产 (472MB) | 37.9s | 102.9s | 103MB | 377MB | 78% | 78% |
| F 用户备份 (213MB) | 14.3s | 35.5s | 102MB | 377MB | 51% | 50% |
| G 冷存储 (1GB) | 43.7s | 53.0s | 101MB | 376MB | 0.02% | 0.02% |
| H 邮件/共享 (22MB) | 1.8s | 3.3s | 102MB | 257MB | 100% | 100% |
| I SQL 转储 (1GB) | 55.0s | 65.9s | 101MB | 377MB | 0.02% | 0.02% |
| J 虚拟机镜像 (1GB) | 32.2s | 122.5s | 101MB | 377MB | 50% | 50% |
| L 超大文件 (2GB) | 184.1s | 654.9s | 101MB | 377MB | 100% | 100% |

> r7z 在大文本/不可压/混合数据上比 7z 更快，内存少 2-4 倍。
> 7z 在大量小文件 (场景 B) 上仍然更快。


## 许可证

MIT — [LICENSE](LICENSE)。