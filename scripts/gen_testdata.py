#!/usr/bin/env python3
"""Generate benchmark datasets for r7z vs 7z comparison.

Scenarios (non-overlapping, real 7-Zip usage patterns):
  A - 500 MB highly compressible text (log-like)            [baseline]
  B - 10 000 small source-like files (1 KB .. 10 KB)        [baseline]
  C - 200 MB incompressible random binary                    [baseline]
  D - 200 MB software package (binaries + configs)         [NEW]
  E - 500 MB game assets (textures + audio + scripts)      [NEW]
  F - 500 MB user backup (docs + photos + db dump)         [NEW]
  G - 1 GB cold storage archive (level 9, max compression)  [NEW]
  H - 25 MB email/share bundle (small, fast UX)            [NEW]
  I - 1 GB SQL dump (repeated INSERT, high compress)       [NEW, large text]
  J - 1 GB VM disk image (semi-compressible binary)        [NEW, large binary]
  L - 2 GB single huge file (size-limit / streaming test)  [NEW]
"""
import os
import random
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "testdata"
SCN = {k: DATA / k for k in ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "L")}


def ensure_dirs():
    DATA.mkdir(exist_ok=True)
    for d in SCN.values():
        d.mkdir(parents=True, exist_ok=True)


def write_repeated(out: Path, target: int, block: bytes):
    with out.open("wb") as f:
        written = 0
        while written < target:
            to_write = min(len(block), target - written)
            f.write(block[:to_write])
            written += to_write


def gen_A(target_bytes: int = 500 * 1024 * 1024):
    out = SCN["A"] / "biglog.txt"
    line = ("2026-11-08T12:00:00Z INFO  r7z-bench host=bench-01 "
            "msg=the quick brown fox jumps over the lazy dog seq={seq} "
            "payload=AAAAAAAAAA BBBBBBBBBB CCCCCCCCCC\n")
    chunk = bytearray()
    while len(chunk) < 1 * 1024 * 1024:
        chunk.extend(line.format(seq=len(chunk)).encode())
    write_repeated(out, target_bytes, bytes(chunk))
    print(f"A: {out} ({out.stat().st_size} bytes)")


def gen_B(n_files: int = 10_000):
    d = SCN["B"]
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
        base = snippets[i % len(snippets)].format(i=i)
        body = (base * ((size // len(base)) + 1))[:size]
        (d / f"file_{i:05d}.txt").write_text(body)
    total = sum(p.stat().st_size for p in d.iterdir())
    print(f"B: {n_files} files in {d} (total {total} bytes)")


def gen_C(target_bytes: int = 200 * 1024 * 1024):
    out = SCN["C"] / "random.bin"
    rng = random.Random(7)
    with out.open("wb") as f:
        written = 0
        while written < target_bytes:
            n = min(4 * 1024 * 1024, target_bytes - written)
            f.write(rng.randbytes(n))
            written += n
    print(f"C: {out} ({out.stat().st_size} bytes)")


def gen_D(target_bytes: int = 200 * 1024 * 1024):
    """Software package: 500 binary files (exe/dll-like) + configs."""
    d = SCN["D"]
    for p in d.iterdir():
        if p.is_file():
            p.unlink()
    rng = random.Random(100)
    n_files = 500
    per = target_bytes // n_files
    for i in range(n_files):
        # semi-compressible binary (code-like)
        data = rng.randbytes(per // 2) + bytes([0] * (per // 2))
        (d / f"module_{i:04d}.bin").write_bytes(data)
    # add config files
    for i in range(50):
        (d / f"config_{i:03d}.ini").write_text(f"[section{i}]\nkey=value{i}\n" * 20)
    total = sum(p.stat().st_size for p in d.iterdir())
    print(f"D: {len(list(d.iterdir()))} files in {d} (total {total} bytes)")


def gen_E(target_bytes: int = 500 * 1024 * 1024):
    """Game assets: textures (random) + audio (semi) + scripts (text)."""
    d = SCN["E"]
    for p in d.iterdir():
        if p.is_file():
            p.unlink()
    rng = random.Random(200)
    # textures: 50 files, 5MB each, incompressible
    for i in range(50):
        (d / f"texture_{i:03d}.dds").write_bytes(rng.randbytes(5 * 1024 * 1024))
    # audio: 20 files, 10MB each, semi-compressible
    for i in range(20):
        (d / f"audio_{i:03d}.wav").write_bytes(rng.randbytes(5 * 1024 * 1024) + bytes([0] * (5 * 1024 * 1024)))
    # scripts: 1000 small text files
    for i in range(1000):
        (d / f"script_{i:04d}.lua").write_text(f"-- script {i}\nfunction f{i}() return {i} end\n" * 10)
    total = sum(p.stat().st_size for p in d.iterdir())
    print(f"E: {len(list(d.iterdir()))} files in {d} (total {total} bytes)")


def gen_F(target_bytes: int = 500 * 1024 * 1024):
    """User backup: docs + photos + db dump."""
    d = SCN["F"]
    for p in d.iterdir():
        if p.is_file():
            p.unlink()
    rng = random.Random(300)
    # docs: 200 text files
    for i in range(200):
        (d / f"doc_{i:04d}.txt").write_text(("Lorem ipsum dolor sit amet. " * 100 + "\n") * 5)
    # photos: 50 incompressible
    for i in range(50):
        (d / f"photo_{i:04d}.jpg").write_bytes(rng.randbytes(2 * 1024 * 1024))
    # db dump: one large text file
    line = "INSERT INTO t VALUES ({i}, 'data{i}', 123.45);\n"
    chunk = bytearray()
    while len(chunk) < 100 * 1024 * 1024:
        chunk.extend(line.format(i=len(chunk)).encode())
    (d / "dump.sql").write_bytes(bytes(chunk))
    total = sum(p.stat().st_size for p in d.iterdir())
    print(f"F: {len(list(d.iterdir()))} files in {d} (total {total} bytes)")


def gen_G(target_bytes: int = 1024 * 1024 * 1024):
    """Cold storage: 1GB repeated text, level 9."""
    out = SCN["G"] / "archive.txt"
    line = "COLD STORAGE RECORD {i}: " + "X" * 80 + "\n"
    chunk = bytearray()
    while len(chunk) < 2 * 1024 * 1024:
        chunk.extend(line.format(i=len(chunk)).encode())
    write_repeated(out, target_bytes, bytes(chunk))
    print(f"G: {out} ({out.stat().st_size} bytes)")


def gen_H():
    """Email/share bundle: 25MB mixed small files."""
    d = SCN["H"]
    for p in d.iterdir():
        if p.is_file():
            p.unlink()
    rng = random.Random(400)
    for i in range(30):
        (d / f"file_{i:03d}.pdf").write_bytes(rng.randbytes(500 * 1024))
    for i in range(20):
        (d / f"image_{i:03d}.png").write_bytes(rng.randbytes(300 * 1024))
    (d / "readme.txt").write_text("Shared bundle.\n" * 100)
    total = sum(p.stat().st_size for p in d.iterdir())
    print(f"H: {len(list(d.iterdir()))} files in {d} (total {total} bytes)")


def gen_I(target_bytes: int = 1024 * 1024 * 1024):
    """SQL dump: 1GB repeated INSERT statements."""
    out = SCN["I"] / "dump.sql"
    line = "INSERT INTO users (id, name, email, created) VALUES ({i}, 'user{i}', 'u{i}@x.com', '2026-01-01');\n"
    chunk = bytearray()
    while len(chunk) < 4 * 1024 * 1024:
        chunk.extend(line.format(i=len(chunk)).encode())
    write_repeated(out, target_bytes, bytes(chunk))
    print(f"I: {out} ({out.stat().st_size} bytes)")


def gen_J(target_bytes: int = 1024 * 1024 * 1024):
    """VM disk image: 1GB semi-compressible binary."""
    out = SCN["J"] / "disk.img"
    rng = random.Random(500)
    with out.open("wb") as f:
        written = 0
        while written < target_bytes:
            n = min(8 * 1024 * 1024, target_bytes - written)
            # mix of zeros (free space) and random (used blocks)
            block = bytes([0] * (n // 2)) + rng.randbytes(n // 2)
            f.write(block)
            written += n
    print(f"J: {out} ({out.stat().st_size} bytes)")


def gen_L(target_bytes: int = 2 * 1024 * 1024 * 1024):
    """Huge single file: 2GB (size-limit / streaming test)."""
    out = SCN["L"] / "huge.bin"
    rng = random.Random(600)
    with out.open("wb") as f:
        written = 0
        while written < target_bytes:
            n = min(16 * 1024 * 1024, target_bytes - written)
            f.write(rng.randbytes(n))
            written += n
    print(f"L: {out} ({out.stat().st_size} bytes)")


def main():
    ensure_dirs()
    gen_A()
    gen_B()
    gen_C()
    gen_D()
    gen_E()
    gen_F()
    gen_G()
    gen_H()
    gen_I()
    gen_J()
    gen_L()
    print("done")


if __name__ == "__main__":
    main()
