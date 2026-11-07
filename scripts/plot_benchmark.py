#!/usr/bin/env python3
"""Render benchmark_report.md into PNG charts with exact value labels."""
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "benchmark_report.md"
OUT = ROOT / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True)

rows = []
for line in REPORT.read_text(encoding="utf-8").splitlines():
    if not line.startswith("|") or "---" in line or "Scenario" in line:
        continue
    cols = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cols) < 7:
        continue
    scn, tool, thr, mode, t, rss, ratio = cols[:7]
    rows.append(dict(scn=scn, tool=tool, thr=int(thr), mode=mode,
                     t=float(t), rss=float(rss) if rss else 0.0))

scenarios = sorted(set(r["scn"] for r in rows))
tools = ["r7z", "7z"]
colors = {"r7z": "#f74c00", "7z": "#1f77b4"}

def vals_for(mode, thr, metric):
    out = {}
    for tool in tools:
        out[tool] = []
        for scn in scenarios:
            matches = [r for r in rows if r["scn"] == scn and r["tool"] == tool
                       and r["mode"] == mode and r["thr"] == thr]
            if metric == "t":
                out[tool].append(matches[0]["t"] if matches else 0)
            else:
                out[tool].append(matches[0]["rss"] / 1024 if matches else 0)
    return out

def make_chart(mode, thr, metric, title, ylabel, fname):
    data = vals_for(mode, thr, metric)
    x = np.arange(len(scenarios))
    width = 0.38
    fig, ax = plt.subplots(figsize=(max(10, len(scenarios) * 1.1), 5.5))
    for i, tool in enumerate(tools):
        bars = ax.bar(x + (i - 0.5) * width, data[tool], width,
                      label=tool, color=colors[tool])
        for b, v in zip(bars, data[tool]):
            ax.annotate(f"{v:.2f}", (b.get_x() + b.get_width() / 2, b.get_height()),
                        ha="center", va="bottom", fontsize=7, rotation=90)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, rotation=45, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / fname, dpi=140)
    plt.close(fig)

make_chart("compress", 1, "t", "Compression time (single thread)", "Seconds", "bench_time_compress_1t.png")
make_chart("compress", 16, "t", "Compression time (16 threads)", "Seconds", "bench_time_compress_16t.png")
make_chart("decompress", 1, "t", "Decompression time (single thread)", "Seconds", "bench_time_decompress.png")
make_chart("compress", 1, "rss", "Peak memory (single thread, compress)", "MB", "bench_memory.png")

# Speedup ratio chart (7z_time / r7z_time) for compress, single thread
r7z_t = vals_for("compress", 1, "t")["r7z"]
sevenz_t = vals_for("compress", 1, "t")["7z"]
speedup = [ (s / r) if r > 0 else 0 for s, r in zip(sevenz_t, r7z_t) ]
fig, ax = plt.subplots(figsize=(max(10, len(scenarios) * 1.1), 5))
bars = ax.bar(scenarios, speedup, color="#2ca02c")
for b, v in zip(bars, speedup):
    ax.annotate(f"{v:.2f}x", (b.get_x() + b.get_width() / 2, b.get_height()),
                ha="center", va="bottom", fontsize=8)
ax.axhline(1.0, color="red", linestyle="--", linewidth=1, label="parity (1.0x)")
ax.set_xticklabels(scenarios, rotation=45, ha="right")
ax.set_ylabel("Speedup (7z_time / r7z_time)")
ax.set_title("r7z vs 7z compression speedup (>1 = r7z faster)")
ax.legend()
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "bench_speedup.png", dpi=140)
plt.close(fig)

print("charts written to", OUT)