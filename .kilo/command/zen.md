---
description: Query the ZEN (JJ-Model) architecture and route through TinyLlama
agent: zen
subtask: true
---
Query the ZEN (JJ-Model) architecture at F:\Gotlet\activity\ZEN.

ZEN is a personal LLM over recall/node memory with:
- WebSocket API on :3333, Model Proxy on :3334, Cross-Comm P2P on :4445
- SQLite vector memory, macOS integration, autonomous agent engine
- BroadSpectrum Orchestrator, GGUF model manager, MCP client
- Kilo commands: /ask, /code, /instruct, /insume, /mcp, /perplex, /proposition, /read, /recall, /store

Model backend: TinyLlama-1.1B-Chat Q4_K_M on F:\Gotlet\activity\QBM-\_models via llama-cpp-python.

Task: $ARGUMENTS