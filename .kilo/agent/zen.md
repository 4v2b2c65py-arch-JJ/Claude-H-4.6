---
description: ZEN (JJ-Model) architecture — personal LLM over recall/node memory with autonomous agents
mode: primary
model: anthropic/claude-sonnet-4-5
steps: 50
hidden: false
permission:
  bash: allow
  edit:
    "**/*": allow
  read: allow
  glob: allow
  grep: allow
  list: allow
  task: allow
  webfetch: allow
  websearch: allow
  skill: allow
  external_directory: ask
  todowrite: allow
  todoread: allow
  question: ask
---
TOP CONTEXT — ZEN (JJ-Model) Architecture

ZEN is a personal LLM over recall/node memory with full environment integration.
Cloned at F:\Gotlet\activity\ZEN (https://github.com/4v2b2c65py-arch-JJ/ZEN.git).

## Ports
| Service | Port |
|---------|------|
| Main API / WebSocket | 3333 |
| Cross-Comm P2P | 4445 |
| Model Proxy | 3334 |
| iDevice bridge | 4444 |

## Architecture (see knowledge-graph.mmd)
- `src/index.ts` — Full-stack supervisor (all services)
- `src/api/server.ts` — WebSocket API on :3333
- `src/memory/vector-memory.ts` — SQLite vector recall memory
- `src/llm/provider.ts` — LLM abstraction (Ollama / OpenAI-compatible)
- `src/mac/integration.ts` — macOS automation (notify, say, clipboard, apps)
- `src/broadspectrum/orchestrator.ts` — Unified tool orchestrator (MCP-exposed)
- `src/dataset/pool.ts` — Dataset pool + pass handoffs + device specifics
- `src/proxy/` — Model proxy on :3334
- `src/gguf/` — GGUF model manager (downloads to models/gguf)
- `src/control/` — Control tagger (scans src/)
- `src/mcp-client/` — MCP client (connects to ext/)
- `src/icloud/` — iCloud expansion packages
- `src/network/kernel/` — raw socket kernel, direct mode
- `src/idevice/` — libimobiledevice bridge for iOS

## New Systems (from knowledge-graph.mmd)
- Cross-Comm P2P :4445 — cross-device sync
- Auto-Work Engine — autonomous task execution
- MetaBrain Scanner — introspection over memory
- Tool Registry — unified tool surface
- BroadSpectrum Orchestrator — routes across all subsystems
- KeyBind Manager — triggers memory + broadcasts Cross-Comm
- Peripheral Manager — captures macOS + broadcasts Cross-Comm
- Shell Vectorial — executes via macOS
- Agent Roles + Spawn Control — hierarchical agent spawning

## MCP Servers (.kilo/mcp.json)
- filesystem, memory, mac (default), transcription (disabled)

## Kilo Commands (.kilo/commands/)
/ask, /code, /instruct, /insume, /mcp, /perplex, /proposition, /read, /recall, /store

## Daemon
- weight_class: daemond, priority: high, keep_alive: true
- hard limits: memory 2048 MB, cpu 200%
- soft limits: memory 1024 MB, cpu 100%

## Integration with Gotlet
- Model: TinyLlama-1.1B-Chat Q4_K_M on F:\Gotlet\activity\QBM-\_models
- Backend: llama-cpp-python, provider llama-cpp+ensemble
- All model files on F drive (C has limited space)
- Run: `cd F:\Gotlet\activity\ZEN && npm install && npm run build && npm start`

## Current Task
$ARGUMENTS