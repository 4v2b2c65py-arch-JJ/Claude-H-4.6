"""Python telemetry for the Gotlet pipeline.

Implements the schema in telemetry.json:
- Ethernet source, C-grid arrays with name tags
- WiFi COMS transport (broadcast + unicast) for passing COMS messages over wifi
- 4-level gray output (integer-rounded)
- TCP-connected LLM client (Claude network, TOPS), vision integer rounds
- Plank task decomposition (oms/ebjs/plank), position metrics layout
- Texture light/dark structure decoding, scroll frequency
- Layer dims/characters/output length, doors awaiting phrase + hash swap
- Vivid/vlc/drv channel node
- Electron + Vue interface, playable streamer/scene
- Terminal IQ/EQ/AQ benchmark by occurrence + response time, COMS result categories
- Agent triggers on puzzle, event recording
"""

from __future__ import annotations

import json
import socket
import struct
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

GRAY_LEVELS = 4
PLANK_TASKS = ("oms", "ebjs", "plank")
AWAIT_EVENTS = ("phrase", "hash_swap")

# COMS message framing: 4-byte big-endian length prefix + JSON payload
COMS_MAGIC = b"COMS"


def round_gray(value: float) -> int:
    """Round an integer to the nearest of 4 gray levels (0..3)."""
    return max(0, min(GRAY_LEVELS - 1, round(value)))


def to_gray_levels(values: list[float]) -> list[int]:
    return [round_gray(v) for v in values]


class WiFiCOMS:
    """WiFi transport for COMS messages.

    Sends framed JSON COMS messages over UDP (broadcast by default, or unicast
    to a specific peer). Falls back gracefully when the network is unavailable.
    """

    def __init__(self, wifi_host: str = "127.0.0.1", wifi_port: int = 5182,
                 broadcast: bool = True, timeout: float = 2.0):
        self.wifi_host = wifi_host
        self.wifi_port = wifi_port
        self.broadcast = broadcast
        self.timeout = timeout
        self._sock: socket.socket | None = None

    def _ensure_socket(self) -> socket.socket:
        if self._sock is None:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._sock.settimeout(self.timeout)
        return self._sock

    def send_coms(self, message: dict[str, Any]) -> bool:
        """Send a COMS message over WiFi. Returns True on success."""
        try:
            payload = json.dumps(message).encode()
            frame = struct.pack(">I", len(payload)) + payload
            sock = self._ensure_socket()
            target = ("255.255.255.255", self.wifi_port) if self.broadcast else (self.wifi_host, self.wifi_port)
            sock.sendto(frame, target)
            return True
        except OSError:
            return False

    def recv_coms(self, timeout: float | None = None) -> dict[str, Any] | None:
        """Receive one COMS message. Returns None on timeout."""
        try:
            sock = self._ensure_socket()
            if timeout is not None:
                sock.settimeout(timeout)
            data, _ = sock.recvfrom(65535)
            (length,) = struct.unpack(">I", data[:4])
            payload = json.loads(data[4:4 + length].decode())
            return payload
        except (socket.timeout, OSError):
            return None

    def close(self) -> None:
        if self._sock is not None:
            self._sock.close()
            self._sock = None


@dataclass
class PositionMetrics:
    layout: str = "plank_metrics_layout"
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class LayerInfo:
    dims: list[int] = field(default_factory=list)
    characters: int = 0
    output_length: int = 0
    frequency: float = 0.0


@dataclass
class BenchmarkResult:
    iq: int = 0
    eq: int = 0
    aq: int = 0
    response_time_ms: float = 0.0
    occurrence: int = 0
    coms_category: str = ""


@dataclass
class TelemetryEvent:
    ts: float
    tag: str
    payload: dict[str, Any]


class LLMClient:
    """TCP-connected LLM client targeting the Claude network (TOPS)."""

    def __init__(self, host: str, port: int, channel: str = "vivid"):
        self.host = host
        self.port = port
        self.channel = channel
        self._sock: socket.socket | None = None

    def connect(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(5)
        self._sock.connect((self.host, self.port))

    def send_vision(self, rounds_of_integers: int) -> dict[str, Any]:
        if self._sock is None:
            self.connect()
        payload = json.dumps({"channel": self.channel, "vision_rounds": rounds_of_integers}).encode()
        self._sock.sendall(struct.pack(">I", len(payload)) + payload)
        raw_len = self._recv_exact(4)
        (length,) = struct.unpack(">I", raw_len)
        raw = self._recv_exact(length)
        return json.loads(raw.decode())

    def _recv_exact(self, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = self._sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("socket closed")
            buf += chunk
        return buf

    def close(self) -> None:
        if self._sock is not None:
            self._sock.close()
            self._sock = None


class TelemetryCollector:
    def __init__(self, config_path: str | Path = "telemetry.json"):
        self.config = json.loads(Path(config_path).read_text())
        self.events: list[TelemetryEvent] = []
        self.benchmarks: list[BenchmarkResult] = []
        self.position = PositionMetrics()
        self.layers: list[LayerInfo] = []
        self.client = LLMClient(
            host=self.config["llm_client"].get("host", "127.0.0.1"),
            port=self.config["llm_client"].get("port", 8080),
            channel=self.config["llm_client"]["channels"]["primary"],
        )
        # WiFi COMS transport: broadcast by default, unicast when wifi_host set
        wifi_cfg = self.config.get("coms", {}).get("wifi", {})
        self.wifi_coms = WiFiCOMS(
            wifi_host=wifi_cfg.get("host", "127.0.0.1"),
            wifi_port=wifi_cfg.get("port", 5182),
            broadcast=wifi_cfg.get("broadcast", True),
            timeout=wifi_cfg.get("timeout", 2.0),
        )

    def record(self, tag: str, payload: dict[str, Any]) -> None:
        self.events.append(TelemetryEvent(ts=time.time(), tag=tag, payload=payload))

    def send_coms(self, message: dict[str, Any], via_wifi: bool = True) -> bool:
        """Send a COMS message. With via_wifi=True uses the WiFi transport,
        otherwise records it as a local event."""
        if via_wifi:
            ok = self.wifi_coms.send_coms(message)
            self.record("coms_wifi", {"message": message, "delivered": ok})
            return ok
        self.record("coms_local", {"message": message})
        return True

    def recv_coms(self, timeout: float | None = None) -> dict[str, Any] | None:
        """Receive a COMS message over WiFi."""
        return self.wifi_coms.recv_coms(timeout)

    def decompose_plank(self, task: str) -> list[str]:
        """Lint decomposition of a task into the three plank stages."""
        if task not in PLANK_TASKS:
            raise ValueError(f"unknown plank task: {task}")
        return list(PLANK_TASKS)

    def decode_texture(self, mat: list[list[float]], light: bool = True) -> list[int]:
        """Decode a texture matrix into gray levels with light/dark mode."""
        flat = [v for row in mat for v in row]
        if not light:
            flat = [1.0 - v for v in flat]
        return to_gray_levels(flat)

    def benchmark(self, iq: int, eq: int, aq: int, category: str) -> BenchmarkResult:
        start = time.perf_counter()
        # placeholder work representing response time measurement
        _ = iq + eq + aq
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        result = BenchmarkResult(
            iq=iq, eq=eq, aq=aq,
            response_time_ms=elapsed_ms,
            occurrence=len(self.benchmarks) + 1,
            coms_category=category,
        )
        self.benchmarks.append(result)
        return result

    def agent_trigger(self, puzzle: str) -> None:
        if self.config["triggers"]["agent"]["on"] == "puzzle":
            self.record("agent_cmnt", {"puzzle": puzzle})

    def export(self) -> dict[str, Any]:
        return {
            "config": self.config,
            "position": asdict(self.position),
            "layers": [asdict(l) for l in self.layers],
            "benchmarks": [asdict(b) for b in self.benchmarks],
            "events": [asdict(e) for e in self.events],
        }


def main() -> int:
    collector = TelemetryCollector()
    collector.decompose_plank("oms")
    collector.decode_texture([[0.1, 0.9], [0.5, 0.2]], light=True)
    collector.benchmark(iq=120, eq=110, aq=100, category="logic")
    collector.agent_trigger("sudoku")
    # Send a COMS message over WiFi (broadcast on 127.0.0.1:5182)
    ok = collector.send_coms({"type": "telemetry", "category": "logic", "iq": 120})
    print(json.dumps(collector.export(), indent=2))
    print(f"wifi coms delivered: {ok}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())