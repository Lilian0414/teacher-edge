# Historical architecture decision checklist

> **Historical / superseded.** This is the earlier open-question checklist, not a statement that every item is still undecided. Stock firmware, HTTP, push-to-talk and transport framing were subsequently tested. Current boundaries live in [ARCHITECTURE](../ARCHITECTURE.md), [INTEGRATION_CONTRACT](../INTEGRATION_CONTRACT.md), and [STATUS](../STATUS.md).

## 8. Deferred architecture decisions

Do not lock these choices before the hardware spike provides evidence:

- custom firmware vs extending an existing Watcher firmware stack
- HTTP vs WebSocket vs another persistent transport between Watcher and Pi
- push-to-talk vs wake word for the first usable product
- exact audio codec / chunking strategy
- exact device authentication / pairing mechanism
- whether local Ollama embedding latency on Pi is acceptable for normal use
- whether TTS should stream or return a complete audio object for MVP

Each decision should be recorded after a spike or implementation issue produces evidence.
