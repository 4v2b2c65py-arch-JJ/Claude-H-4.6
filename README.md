# Claude-H-4.6

Bench-test harness and API for the Claude-H model family, with internal-network
rate limiting, token quotas, and connection pooling for the userbase.

## Credits

- **Author**: 4v2b2c65py-arch-JJ
- **License**: Apache-2.0
- **Built on**: Kilo CLI, TinyLlama-1.1B-Chat (GGUF Q4_K_M), llama-cpp-python

## Requirements (Data Storage)

| Field | Value | Notes |
|-------|-------|-------|
| **Storage backend** | F:\Gotlet\activity\QBM-\_models | Model weights (668 MB GGUF) |
| **Cache dir** | F:\Gotlet\activity\QBM-\_hf | HuggingFace hub cache |
| **Package dir** | F:\Gotlet\activity\QBM-\_pkgs | Python deps (~400 MB) |
| **Temp dir** | F:\Gotlet\activity\QBM-\_tmp | Build/download scratch |
| **Pip cache** | F:\Gotlet\activity\QBM-\_pipcache | Wheel cache |
| **Feed log** | F:\Gotlet\activity\feed.log | RMS feed loop status |
| **Min free space** | 2.0 GB | On the F drive |
| **C drive** | Avoid | Low storage; pip cache + temp redirected to F |

## Internal Network Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| **Rate limit** | 60 req/min | Per-user burst |
| **Token limit** | 4096 tokens | Max prompt+completion per request |
| **Pool size** | 10 connections | Connection pool for userbase |
| **Timeout** | 30 s | Per-request wall clock |
| **Backpressure** | Queue depth 100 | Excess requests queued |

## Quick Start

```bash
git clone https://github.com/4v2b2c65py-arch-JJ/Claude-H-4.6.git
cd Claude-H-4.6
python bench_api.py --model TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF
```

## Bench API

See `bench_api.py`. Exposes:

- `POST /v1/completions` — text completion with token/rate enforcement
- `GET  /v1/health` — pool + rate + model status
- `POST /v1/bench/iq-eq-aq` — run the IQ/EQ/AQ benchmark suite## AGI Benchmark Results (same network)

Model: TinyLlama-1.1B-Chat Q4_K_M via llama-cpp-python, provider `llama-cpp+ensemble`, CPU-only.

| Task | Latency | Result |
|------|---------|--------|
| reasoning | 143 s | Partial — verbose, no clean answer |
| coding | 101 s | Factorial function skeleton, incomplete |
| planning | 267 s | Plausible debug steps |
| factual | 3 s | Correct ("The capital of France is Paris.") |
| math | 14 s | Wrong (12 * 8 = 84, correct is 96) |

**Assessment**: Structured text + code skeletons work; factual recall is reliable;
arithmetic and multi-step reasoning are not. Not reliable AGI at 1.1B on CPU.
