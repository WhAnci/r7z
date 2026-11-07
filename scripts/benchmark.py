#!/usr/bin/env python3
"""Benchmark r7z (release) against system 7z across scenarios A/B/C on Windows.

Measures: wall-clock time, archive size ratio, peak RSS (Working Set), single vs multi thread.
Writes a markdown report to benchmark_report.md.
"""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "testdata"
REPORT = ROOT / "benchmark_report.md"

R7Z = ROOT / "target" / "release" / "r7z.exe"
SEVENZ = Path("C:/Program Files/7-Zip/7z.exe")
if not SEVENZ.exists():
    SEVENZ = Path(shutil.which("7z") or shutil.which("7zz") or "7z")

PYTHON = Path(sys.executable)


def run(cmd, cwd=None):
    """Run command, return (elapsed_seconds, peak_rss_bytes, returncode, stdout, stderr)."""
    start = time.perf_counter()
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    peak = 0
    p = psutil.Process(proc.pid)
    try:
        while proc.poll() is None:
            try:
                rss = p.memory_info().rss
                # include children? 7z is single proc; r7z single proc
                for c in p.children(recursive=True):
                    try:
                        rss += c.memory_info().rss
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                if rss > peak:
                    peak = rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            time.sleep(0.05)
    except Exception:
        pass
    stdout, stderr = proc.communicate()
    elapsed = time.perf_counter() - start
    # final sample
    try:
        rss = p.memory_info().rss
        if rss > peak:
            peak = rss
    except Exception:
        pass
    return elapsed, peak, proc.returncode, stdout.decode(errors="replace"), stderr.decode(errors="replace")


def size_of(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    if path.is_dir():
        return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())
    return 0


def bench_one(scenario_key, tool, threads, mode):
    src_dir = DATA / scenario_key
    work = ROOT / "bench_work" / f"{scenario_key}_{tool}_{threads}_{mode}"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    SINGLE = {"A": "biglog.txt", "C": "random.bin", "G": "archive.txt",
              "I": "dump.sql", "J": "disk.img", "L": "huge.bin"}
    if scenario_key in SINGLE:
        src = src_dir / SINGLE[scenario_key]
    else:
        src = src_dir

    original_size = size_of(src)

    binpath = str(R7Z if tool == "r7z" else SEVENZ)

    if mode == "compress":
        archive = work / "out.7z"
        if tool == "r7z":
            cmd = [binpath, "a", str(archive), str(src), "-t", str(threads)]
        else:
            if src.is_dir():
                cmd = [binpath, "a", "-mx=5", f"-mmt={threads}", str(archive), str(src) + "\\*"]
            else:
                cmd = [binpath, "a", "-mx=5", f"-mmt={threads}", str(archive), str(src)]
        elapsed, rss, rc, out, err = run(cmd, cwd=work)
        if rc != 0:
            print("COMPRESS FAIL", tool, scenario_key, err[:500])
        ratio = (archive.stat().st_size / original_size * 100) if archive.exists() else float("nan")
        return {"elapsed": elapsed, "rss_bytes": rss, "ratio": ratio, "rc": rc}

    else:  # decompress
        archive = work / "out.7z"
        if tool == "r7z":
            prep = [binpath, "a", str(archive), str(src)]
        else:
            if src.is_dir():
                prep = [binpath, "a", "-mx=5", str(archive), str(src) + "\\*"]
            else:
                prep = [binpath, "a", "-mx=5", str(archive), str(src)]
        subprocess.run(prep, cwd=work, capture_output=True)
        outdir = work / "extracted"
        outdir.mkdir(exist_ok=True)
        if tool == "r7z":
            cmd = [binpath, "x", str(archive), "-o", str(outdir), "-t", str(threads)]
        else:
            cmd = [binpath, "x", f"-o{outdir}", str(archive), f"-mmt={threads}"]
        elapsed, rss, rc, out, err = run(cmd, cwd=work)
        if rc != 0:
            print("DECOMPRESS FAIL", tool, scenario_key, err[:500])
        return {"elapsed": elapsed, "rss_bytes": rss, "rc": rc}


def main():
    if not R7Z.exists():
        print("r7z binary missing; build with: cargo build --release")
    if not SEVENZ.exists():
        print("7z not found; skipping 7z comparisons")

    threads_list = [1, (os.cpu_count() or 4)]
    results = {}
    for sk in ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "L"):
        for tool in ("r7z", "7z"):
            if tool == "7z" and not SEVENZ.exists():
                continue
            for th in threads_list:
                for mode in ("compress", "decompress"):
                    print(f"== {sk} {tool} threads={th} {mode}", flush=True)
                    r = bench_one(sk, tool, th, mode)
                    results[(sk, tool, th, mode)] = r
                    print("   ", r, flush=True)

    lines = ["# Benchmark Report (Windows)", "",
             "| Scenario | Tool | Threads | Mode | Time(s) | PeakRSS(MB) | Ratio(%) | RC |",
             "|---|---|---|---|---|---|---|---|"]
    for (sk, tool, th, mode), r in results.items():
        rss_mb = (r.get("rss_bytes") or 0) / (1024 * 1024)
        ratio = r.get("ratio", "")
        if isinstance(ratio, float):
            ratio = f"{ratio:.2f}"
        lines.append(f"| {sk} | {tool} | {th} | {mode} | {r['elapsed']:.3f} | {rss_mb:.1f} | {ratio} | {r['rc']} |")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("report written to", REPORT)


if __name__ == "__main__":
    main()
