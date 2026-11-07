#!/usr/bin/env python3
"""Generate benchmark datasets for r7z vs 7z comparison.

Scenarios:
  A - 500 MB highly compressible text (repeated log lines)
  B - 10 000 small source-like files (1 KB .. 10 KB)
  C - 200 MB incompressible random binary
"""
import os
import random
import string
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "testdata"
SCN = {k: DATA / k for k in ("A", "B", "C")}


def ensure_dirs():
    DATA.mkdir(exist_ok=True)
    for d in SCN.values():
        d.mkdir(parents=True, exist_ok=True)


def gen_A(target_bytes: int = 500 * 1024 * 1024):
    """Repeated log-like lines -> very high compressibility."""
    out = SCN["A"] / "biglog.txt"
    line = (
        "2026-11-08T12:00:00Z INFO  r7z-bench host=bench-01 "
        "msg=the quick brown fox jumps over the lazy dog seq={seq} "
        "payload=AAAAAAAAAA BBBBBBBBBB CCCCCCCCCC\n"
    )
    with out.open("wb") as f:
        written = 0
        seq = 0
        chunk = bytearray()
        # Build a ~1 MiB reusable block then replicate (fast).
        block_target = 1 * 1024 * 1024
        while len(chunk) < block_target:
            chunk.extend(line.format(seq=seq).encode())
            seq += 1
        block = bytes(chunk)
        while written < target_bytes:
            to_write = min(len(block), target_bytes - written)
            f.write(block[:to_write])
            written += to_write
    print(f"A: {out} ({out.stat().st_size} bytes)")


def gen_B(n_files: int = 10_000):
    """Many small source-like files."""
    d = SCN["B"]
    # clean
    for p in d.iterdir():
        if p.is_file():
            p.unlink()
    rng = random.Random(42)
    snippets = [
        "fn main() {{ println!(\"hello {i}\"); }}\n",
        "def f(x): return x * {i} + 1\n",
        "console.log('value', {i});\n",
        "int main(){{ return {i}; }}\n",
    ]
    for i in range(n_files):
        size = rng.randint(1024, 10 * 1024)
        # pick a snippet and pad
        base = snippets[i % len(snippets)].format(i=i)
        body = (base * ((size // len(base)) + 1))[:size]
        (d / f"file_{i:05d}.txt").write_text(body)
    total = sum(p.stat().st_size for p in d.iterdir())
    print(f"B: {n_files} files in {d} (total {total} bytes)")


def gen_C(target_bytes: int = 200 * 1024 * 1024):
    """Incompressible random binary."""
    out = SCN["C"] / "random.bin"
    rng = random.Random(7)
    with out.open("wb") as f:
        written = 0
        chunk_size = 4 * 1024 * 1024
        while written < target_bytes:
            to_write = min(chunk_size, target_bytes - written)
            f.write(rng.randbytes(to_write))
            written += to_write
    print(f"C: {out} ({out.stat().st_size} bytes)")


def main():
    ensure_dirs()
    gen_A()
    gen_B()
    gen_C()
    print("done")


if __name__ == "__main__":
    main()
