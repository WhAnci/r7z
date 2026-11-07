#!/usr/bin/env python3
"""Render benchmark_report.md into readable PNG charts with exact value labels."""
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
colors = {"r7z": "#e05a1a", "7z": "#2b6cb0"}
plt.rcParams.update({"font.size": 11, "axes.titlesize": 13, "axes.labelsize": 11})

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

def hbar(mode, thr, metric, title, xlabel, fname):
    data = vals_for(mode, thr, metric)
    y = np.arange(len(scenarios))
    height = 0.38
    fig, ax = plt.subplots(figsize=(9, max(6, len(scenarios) * 0.55)))
    for i, tool in enumerate(tools):
        bars = ax.barh(y + (i - 0.5) * height, data[tool], height,
                       label=tool, color=colors[tool])
        for b, v in zip(bars, data[tool]):
            ax.annotate(f"{v:.2f}", (v, b.get_y() + b.get_height() / 2),
                        ha="left", va="center", fontsize=9, xytext=(4, 0),
                        textcoords="offset points")
    ax.set_yticks(y)
    ax.set_yticklabels(scenarios)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    ax.legend(loc="lower right")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / fname, dpi=150)
    plt.close(fig)

hbar("compress", 1, "t", "Compression time (1 thread)", "Seconds", "bench_time_compress_1t.png")
hbar("compress", 16, "t", "Compression time (16 threads)", "Seconds", "bench_time_compress_16t.png")
hbar("decompress", 1, "t", "Decompression time (1 thread)", "Seconds", "bench_time_decompress.png")
hbar("compress", 1, "rss", "Peak memory (1 thread, compress)", "MB", "bench_memory.png")

# Speedup ratio chart
r7z_t = vals_for("compress", 1, "t")["r7z"]
sevenz_t = vals_for("compress", 1, "t")["7z"]
speedup = [(s / r) if r > 0 else 0 for s, r in zip(sevenz_t, r7z_t)]
fig, ax = plt.subplots(figsize=(9, max(6, len(scenarios) * 0.55)))
y = np.arange(len(scenarios))
bars = ax.barh(y, speedup, color="#2f855a")
for b, v in zip(bars, speedup):
    ax.annotate(f"{v:.2f}x", (v, b.get_y() + b.get_height() / 2),
                ha="left", va="center", fontsize=9, xytext=(4, 0),
                textcoords="offset points")
ax.axvline(1.0, color="red", linestyle="--", linewidth=1, label="parity (1.0x)")
ax.set_yticks(y)
ax.set_yticklabels(scenarios)
ax.invert_yaxis()
ax.set_xlabel("Speedup (7z_time / r7z_time)")
ax.set_title("r7z vs 7z compression speedup (>1 = r7z faster)")
ax.legend(loc="lower right")
ax.grid(axis="x", alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "bench_speedup.png", dpi=150)
plt.close(fig)

print("charts written to", OUT)
