# r7z

> 7-Zip 코어(`a` / `x` 명령)의 Rust 재구현판. 원본 C/C++ `7z`와의 성능 비교를 위해 제작되었습니다.

[![CI](https://github.com/yourname/r7z/actions/workflows/ci.yml/badge.svg)](https://github.com/yourname/r7z/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**언어:** [English](README.md) (기본) · 한국어 · [中文](README.zh.md)

---

## r7z가 더 좋은 점 (한눈에 보기)

| 장점 | r7z (Rust) | 7-Zip (C++) |
|---|---|---|
| **피크 메모리 (시나리오 A)** | **~85 MB** | ~376 MB (1스레드) / ~1.8 GB (16스레드) |
| **메모리 안전성** | 컴파일 타임 보장 (UB/데이터 레이스 없음) | 수동 C++ 메모리 관리 |
| **런타임 의존성** | 단일 정적 바이너리 | 시스템 라이브러리 필요 |
| **크로스 플랫폼 빌드** | 어디서나 `cargo build` | 플랫폼별 빌드 시스템 |
| **할당자 churn** | 제한적이고 예측 가능한 버퍼 | 큰 solid 블록 아레나 |
| **크래시 안전성** | `panic=abort`, 안전 코드에서 세그폴트 없음 | 잘못된 입력에서 발생 가능 |
| **압축률** | A/C에서 7z와 동등 (~0.02% / ~100%) | 기준 |
| **속도** | 느림 (순수 Rust 인코더) | 빠름 (SIMD + 튜닝된 스레드) |

> **솔직한 요약:** `r7z`는 원시 속도 대신 **4~20배 낮은 메모리 사용량**, 메모리 안전성, 손쉬운 크로스 플랫폼 빌드를 제공합니다. 처리량과 멀티스레드 확장성은 여전히 7-Zip이 우세합니다. [벤치마크 리포트](benchmark_report.md) 참고.

---

## 기능

- `a` — 파일/디렉터리를 `.7z` 아카이브에 추가
- `x` — 아카이브 해제
- `l` — 아카이브 메타데이터 목록
- 압축 레벨 `-m 1..9`
- 스레드 수 `-t N` (0 = 모든 코어)
- `indicatif` 기반 진행률 표시
- `rayon` 기반 병렬 파일 스캔

## 프로젝트 구조

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

## 빠른 시작

```bash
cargo build --release
./target/release/r7z a out.7z ./mydir -m 9 -t 8
./target/release/r7z x out.7z -o extracted/ -t 8
./target/release/r7z l out.7z
```

Windows: `target\release\r7z.exe`.

## 벤치마크

```bash
python scripts/gen_testdata.py
python scripts/benchmark.py
```

자세한 결과: [benchmark_report.md](benchmark_report.md)

## 라이선스

MIT — [LICENSE](LICENSE).