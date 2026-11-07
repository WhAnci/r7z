#!/usr/bin/env python3
"""Render benchmark_report.md into PNG charts for README / social media.

Produces:
  docs/images/bench_time.png   - compress/decompress time by scenario
  docs/images/bench_memory.png - peak RSS by scenario
"""
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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

scenarios = ["A", "B", "C"]
tools = ["r7z", "7z"]
colors = {"r7z": "#f74c00", "7z": "#1f77b4"}

# --- compress time ---
fig, ax = plt.subplots(figsize=(9, 5))
x = range(len(scenarios))
width = 0.38
for i, tool in enumerate(tools):
    vals = []
    for scn in scenarios:
        matches = [r for r in rows if r["scn"] == scn and r["tool"] == tool
                   and r["mode"] == "compress" and r["thr"] == 1]
        vals.append(matches[0]["t"] if matches else 0)
    ax.bar([xi + (i - 0.5) * width for xi in x], vals, width,
           label=tool, color=colors[tool])
ax.set_xticks(list(x))
ax.set_xticklabels([f"Scenario {s}" for s in scenarios])
ax.set_ylabel("Wall-clock time (s)")
ax.set_title("Compression time (single thread)")
ax.legend()
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "bench_time_compress.png", dpi=140)
plt.close(fig)

# --- decompress time ---
fig, ax = plt.subplots(figsize=(9, 5))
for i, tool in enumerate(tools):
    vals = []
    for scn in scenarios:
        matches = [r for r in rows if r["scn"] == scn and r["tool"] == tool
                   and r["mode"] == "decompress" and r["thr"] == 1]
        vals.append(matches[0]["t"] if matches else 0)
    ax.bar([xi + (i - 0.5) * width for xi in x], vals, width,
           label=tool, color=colors[tool])
ax.set_xticks(list(x))
ax.set_xticklabels([f"Scenario {s}" for s in scenarios])
ax.set_ylabel("Wall-clock time (s)")
ax.set_title("Decompression time (single thread)")
ax.legend()
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "bench_time_decompress.png", dpi=140)
plt.close(fig)

# --- peak memory (compress, single thread) ---
fig, ax = plt.subplots(figsize=(9, 5))
for i, tool in enumerate(tools):
    vals = []
    for scn in scenarios:
        matches = [r for r in rows if r["scn"] == scn and r["tool"] == tool
                   and r["mode"] == "compress" and r["thr"] == 1]
        vals.append(matches[0]["rss"] / 1024 if matches else 0)
    ax.bar([xi + (i - 0.5) * width for xi in x], vals, width,
           label=tool, color=colors[tool])
ax.set_xticks(list(x))
ax.set_xticklabels([f"Scenario {s}" for s in scenarios])
ax.set_ylabel("Peak RSS (MB)")
ax.set_title("Peak memory usage (single thread, compress)")
ax.legend()
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "bench_memory.png", dpi=140)
plt.close(fig)

print("charts written to", OUT)