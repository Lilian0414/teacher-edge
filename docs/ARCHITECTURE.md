# Target Architecture

Status: **proposed / not yet implemented in this repository**.

This document defines the intended system boundary before implementation begins.

## 1. System roles

### Teacher Core

Source repository: `Lilian0414/teacher`.

Teacher Core owns learning-domain behavior and durable learning state:

- Conversation
- Memory extraction / recall
- Learning Signal processing
- Learning Item lifecycle
- Review, grading, attempts, and scheduling
- Proactive practice semantics
- learner preferences and availability
- Teacher database schema

`teacher-edge` must call this behavior rather than reproduce it.

### Raspberry Pi edge host

Target host: Raspberry Pi 5 16GB with SSD and active cooling.

The Pi is the always-on runtime that can host:

- Teacher FastAPI Core
- Teacher SQLite database
- `teacher-edge` device bridge
- local embedding runtime such as Ollama
- device/session state
- edge-side audio processing added in later phases
- systemd-managed services

Provider secrets belong here, not on the Watcher.

### SenseCAP Watcher

The Watcher is the physical human interface. It should remain intentionally thin.

Target responsibilities:

- microphone capture
- speaker playback
- display rendering
- touch / button / rotary interaction where supported by the selected firmware path
- camera-derived device events in later phases
- connection state and minimal device-local UI state

It should not own learning logic, learning persistence, provider secrets, or an independent AI memory.

## 2. Target topology

```text
                       Internet
             ┌────────────┼─────────────┐
             │            │             │
             ▼            ▼             ▼
          Groq         ElevenLabs    optional APIs
        LLM / STT          TTS
             │            │
             └──────┬─────┘
                    │
          Raspberry Pi 5 16GB
  ┌─────────────────────────────────────┐
  │ teacher-edge Device Bridge          │  LAN-facing
  │   - device session                  │
  │   - audio ingress/egress            │
  │   - Teacher API adapter             │
  │   - TTS adapter                     │
  │   - device presentation state       │
  │                                     │
  │ Teacher FastAPI Core                │  localhost
  │   - conversation                    │
  │   - memory                          │
  │   - learning / review               │
  │   - proactive                       │
  │                                     │
  │ SQLite                              │
  │ Ollama / local embedding (target)   │
  └──────────────────┬──────────────────┘
                     │ Wi-Fi / LAN
                     ▼
              SenseCAP Watcher
       microphone / display / speaker
```

## 3. Core boundary rule

The bridge translates **device interaction** into **Teacher API calls**.

Example voice conversation flow:

```text
Watcher records utterance
    ↓
Device Bridge receives audio
    ↓
Teacher speech transcription API
    ↓
transcript
    ↓
Teacher conversation API
    ↓
Teacher performs its existing context / memory / learning work
    ↓
assistant text response
    ↓
ElevenLabs TTS
    ↓
audio + display payload returned to Watcher
```

The bridge may orchestrate the calls, but it must not decide what counts as a Learning Item, how an answer is graded, or when a review becomes due.

## 4. Network boundary

Preferred deployment:

```text
Watcher
   │ LAN
   ▼
0.0.0.0:<bridge-port>
teacher-edge bridge
   │ localhost
   ▼
127.0.0.1:<teacher-port>
Teacher Core
```

This preserves Teacher's existing localhost-oriented trust boundary and avoids exposing the full learning API directly to every LAN client.

The bridge should eventually implement explicit device authentication / pairing. The exact mechanism is intentionally undecided until the Watcher firmware / transport path is selected.

## 5. State ownership

| State | Owner |
| --- | --- |
| conversations / messages | Teacher Core |
| memories / embeddings metadata | Teacher Core |
| learning items / occurrences / attempts | Teacher Core |
| review scheduling | Teacher Core |
| proactive practice state | Teacher Core |
| provider secrets | Raspberry Pi runtime |
| Watcher connection/session | teacher-edge |
| transient playback / display state | teacher-edge / Watcher |
| wake-word or VAD state | teacher-edge, later phase |
| camera-derived presence / gesture event | Watcher / teacher-edge, later phase |

A new database in `teacher-edge` is not assumed. Add persistence only when a concrete edge-owned state requires it.

## 6. Model / provider placement

Initial target:

```text
Groq       → generative LLM + STT
ElevenLabs → TTS
Ollama     → local embedding runtime on Pi, if verified practical
```

This is a deployment choice, not a Teacher domain change. Provider adapters should remain replaceable.

The 16GB Pi has enough memory headroom for lightweight local inference, but MVP should optimize for interaction reliability and latency rather than forcing all inference local.

## 7. Why a separate repository

The separate repository makes the presentation / hardware layer independently evolvable.

Teacher can continue to support its Textual client while `teacher-edge` adds a physical client:

```text
Textual UI ──────┐
                 ├──→ Teacher Core → one learning state
Watcher / Edge ──┘
```

This prevents hardware experiments from contaminating Teacher's learning-domain implementation and makes it possible to replace the Watcher later without renaming or rewriting the learning engine.

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
