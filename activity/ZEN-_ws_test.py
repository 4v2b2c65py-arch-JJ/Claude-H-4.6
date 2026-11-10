#!/usr/bin/env python3
"""Send a chat message through ZEN's WebSocket API to the TinyLlama model.

Properly masks client frames per RFC 6455 (the ws library requires MASK=1
on all client frames).
"""
import socket, base64, json, struct, os, sys

ZEN_WS = ("127.0.0.1", 3333)

def ws_connect(host, port):
    key = base64.b64encode(os.urandom(16)).decode()
    s = socket.create_connection((host, port), timeout=10)
    handshake = (
        f"GET / HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n\r\n"
    ).encode()
    s.sendall(handshake)
    resp = s.recv(4096)
    if b"101" not in resp:
        raise RuntimeError(f"WS handshake failed: {resp[:200]}")
    return s

def ws_send(s, msg):
    """Send a masked text frame (RFC 6455: client frames MUST be masked)."""
    data = json.dumps(msg).encode()
    mask_key = os.urandom(4)
    masked = bytes(b ^ mask_key[i % 4] for i, b in enumerate(data))
    header = bytearray([0x81])  # FIN + text opcode (0x1)
    length = len(data)
    if length < 126:
        header.append(0x80 | length)  # MASK=1 + length
    elif length < 65536:
        header.append(0x80 | 126)  # MASK=1 + 126 (extended)
        header += struct.pack(">H", length)
    else:
        header.append(0x80 | 127)  # MASK=1 + 127 (64-bit)
        header += struct.pack(">Q", length)
    header += mask_key
    s.sendall(bytes(header) + masked)

def _recv_exact(s, n):
    buf = b""
    while len(buf) < n:
        chunk = s.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("socket closed")
        buf += chunk
    return buf

def ws_recv(s, timeout=180):
    """Receive a frame. Handles masked/unmasked server frames."""
    s.settimeout(timeout)
    try:
        b1, b2 = _recv_exact(s, 1)[0], _recv_exact(s, 1)[0]
        opcode = b1 & 0x0F
        masked = b2 & 0x80
        length = b2 & 0x7F
        if length == 126:
            length = struct.unpack(">H", _recv_exact(s, 2))[0]
        elif length == 127:
            length = struct.unpack(">Q", _recv_exact(s, 8))[0]
        mask_key = _recv_exact(s, 4) if masked else b""
        payload = _recv_exact(s, length)
        if mask_key:
            payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))
        if opcode == 0x1:  # text
            return json.loads(payload.decode())
        elif opcode == 0x8:  # close
            return None
        elif opcode == 0x9:  # ping - respond with pong
            s.sendall(bytes([0x8A, 0x80]) + os.urandom(4) + payload)
            return ws_recv(s, timeout)
        return None
    except socket.timeout:
        return None

def main():
    s = ws_connect(*ZEN_WS)
    ws_send(s, {
        "type": "chat",
        "content": "What is the capital of France?",
        "session": "gotlet-test"
    })
    print("Sent chat message, waiting for response...")
    resp = ws_recv(s, timeout=180)
    if resp:
        print("ZEN RESPONSE:")
        print(json.dumps(resp, indent=2)[:800])
    else:
        print("No response (timeout)")
    s.close()

if __name__ == "__main__":
    main()