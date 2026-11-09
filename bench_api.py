#!/usr/bin/env python3
"""Claude-H-4.6 bench-test API.

Exposes:
  POST /v1/completions  - text completion with token/rate enforcement
  GET  /v1/health       - pool + rate + model status
  POST /v1/bench/iq-eq-aq - run the IQ/EQ/AQ benchmark suite

Internal network configuration (see README):
  Rate limit  : 60 req/min per user
  Token limit : 4096 tokens max prompt+completion per request
  Pool size   : 10 connections for the userbase
  Timeout     : 30 s per request
  Backpressure: queue depth 100
"""

import os
import sys
import time
import json
import threading
import importlib.util
from pathlib import Path
from collections import defaultdict, deque
from typing import Any

# Force all model files onto the F drive (C has limited space).
QBM = Path(r"F:\Gotlet\activity\QBM-")
PKGS = QBM / "_pkgs"
sys.path.insert(0, str(QBM))
sys.path.insert(0, str(PKGS))
os.environ.setdefault("TMP", str(QBM / "_tmp"))
os.environ.setdefault("TEMP", str(QBM / "_tmp"))
os.environ.setdefault("PIP_CACHE_DIR", str(QBM / "_pipcache"))

# ---- Internal network configuration ----
RATE_LIMIT_REQ = 60          # requests per minute per user
TOKEN_LIMIT = 4096           # max prompt+completion tokens per request
POOL_SIZE = 10               # connection pool for the userbase
REQUEST_TIMEOUT_S = 30       # per-request wall clock
QUEUE_DEPTH = 100            # backpressure queue depth

# ---- Rate limiter (token-bucket per user) ----
class RateLimiter:
    def __init__(self, rate: int, period: float = 60.0):
        self.rate = rate
        self.period = period
        self.buckets: dict[str, float] = defaultdict(lambda: float(rate))
        self._last: dict[str, float] = defaultdict(lambda: time.time())
        self.lock = threading.Lock()

    def allow(self, user: str) -> bool:
        now = time.time()
        with self.lock:
            self.buckets[user] = min(float(self.rate), self.buckets[user] + now - self._last[user])
            self._last[user] = now
            if self.buckets[user] >= 1.0:
                self.buckets[user] -= 1.0
                return True
            return False


# ---- Connection pool ----
class ConnectionPool:
    def __init__(self, size: int):
        self.size = size
        self._semaphore = threading.Semaphore(size)
        self.active = 0
        self.lock = threading.Lock()

    def acquire(self, timeout: float = REQUEST_TIMEOUT_S) -> bool:
        return self._semaphore.acquire(timeout=timeout)

    def release(self) -> None:
        self._semaphore.release()

    def status(self) -> dict[str, Any]:
        with self.lock:
            return {"size": self.size, "available": self.size - self.active, "active": self.active}


# ---- Token counter ----
def count_tokens(text: str) -> int:
    return len(text.split())


# ---- Model layer ----
spec = importlib.util.spec_from_file_location("gpt_layer", QBM / "ai" / "gpt_layer.py")
gpt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gpt)


class ClaudeHBenchAPI:
    def __init__(self):
        self.rate_limiter = RateLimiter(RATE_LIMIT_REQ)
        self.pool = ConnectionPool(POOL_SIZE)
        self.queue: deque = deque(maxlen=QUEUE_DEPTH)
        self.user_tokens: dict[str, int] = defaultdict(int)

    def complete(self, user: str, prompt: str, max_tokens: int = 1024) -> dict[str, Any]:
        # Rate limit
        if not self.rate_limiter.allow(user):
            return {"error": "rate limit exceeded", "retry_after_s": 1.0}
        # Token limit (prompt + completion)
        prompt_tokens = count_tokens(prompt)
        if prompt_tokens > TOKEN_LIMIT:
            return {"error": "prompt exceeds token limit", "limit": TOKEN_LIMIT, "prompt_tokens": prompt_tokens}
        if prompt_tokens + max_tokens > TOKEN_LIMIT:
            max_tokens = TOKEN_LIMIT - prompt_tokens
        # Connection pool
        if not self.pool.acquire():
            self.queue.append({"user": user, "prompt": prompt, "ts": time.time()})
            return {"error": "pool exhausted", "queued": len(self.queue), "queue_depth": QUEUE_DEPTH}
        try:
            t0 = time.time()
            r = gpt.gpt_layer.query(prompt, max_tokens=max_tokens)
            elapsed_ms = (time.time() - t0) * 1000.0
            self.user_tokens[user] += r.get("tokens_used", 0)
            return {
                "response": r.get("response", ""),
                "model": r.get("model", "unknown"),
                "provider": r.get("provider", "unknown"),
                "tokens_used": r.get("tokens_used", 0),
                "latency_ms": elapsed_ms,
                "user_tokens_total": self.user_tokens[user],
            }
        finally:
            self.pool.release()

    def health(self) -> dict[str, Any]:
        st = gpt.gpt_layer.get_status()
        return {
            "status": "ok",
            "model_loaded": st.get("model_loaded"),
            "model_backend": st.get("model_backend"),
            "pool": self.pool.status(),
            "rate_limit_req_per_min": RATE_LIMIT_REQ,
            "token_limit": TOKEN_LIMIT,
            "timeout_s": REQUEST_TIMEOUT_S,
            "queue_depth": QUEUE_DEPTH,
        }

    def bench_iq_eq_aq(self, user: str) -> dict[str, Any]:
        questions = [
            ("iq", "What is 2 + 2?"),
            ("eq", "How would you comfort a friend who failed a test?"),
            ("aq", "What is the capital of France?"),
        ]
        results = {}
        for kind, prompt in questions:
            t0 = time.time()
            r = self.complete(user, prompt)
            elapsed = (time.time() - t0) * 1000.0
            results[kind] = {
                "response": r.get("response", "")[:120],
                "latency_ms": elapsed,
                "tokens_used": r.get("tokens_used", 0),
            }
        return {"user": user, "results": results, "timestamp": time.time()}


def main() -> int:
    api = ClaudeHBenchAPI()
    print(json.dumps(api.health(), indent=2))
    print("\nSample completion:")
    print(json.dumps(api.complete("probe", "What is the capital of France?"), indent=2))
    print("\nIQ/EQ/AQ bench:")
    print(json.dumps(api.bench_iq_eq_aq("probe"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
