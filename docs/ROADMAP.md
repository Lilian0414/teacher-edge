# Roadmap

Status: **planning baseline**.

The roadmap is intentionally staged so hardware uncertainty is resolved before large implementation changes.

## M0 — Hardware / firmware discovery spike

Goal: determine the smallest reliable path from SenseCAP Watcher to Raspberry Pi.

Questions to answer with evidence:

- What firmware is currently installed on the Watcher?
- Can it be extended safely, or should a different open firmware base be used?
- What microphone audio format can be captured and transported?
- What speaker formats can the device play?
- Can the display be controlled by the chosen firmware path?
- Which interaction controls are available?
- What transport is simplest for MVP: HTTP, WebSocket, or another supported mechanism?
- Can the device reconnect cleanly after Pi / Wi-Fi restart?

Deliverable:

- documented tested firmware / toolchain
- one minimal Watcher ↔ Pi connectivity proof
- recommendation for the MVP transport

Non-goals:

- Teacher integration
- ElevenLabs integration
- camera understanding
- wake word

## M1 — Raspberry Pi host baseline

Goal: make the Pi a reproducible Teacher host.

Scope:

- record actual Pi OS / Python / SSD / network baseline
- run Teacher Core on Pi
- run Teacher migrations and verify database persistence
- verify required outbound provider connectivity
- test local Ollama embedding path if practical
- define service user, paths, environment configuration, and systemd strategy

Acceptance criteria:

- Teacher Core starts on Pi without MacBook runtime dependency
- restart preserves Teacher database state
- secrets are not committed
- exact Teacher SHA is recorded

### M1 Watcher HTTP ingress increment

Implemented locally: the hardware-spike transport is represented by a FastAPI
health endpoint and authenticated `POST /v1/notification/event`, with typed
payload normalization. This increment does not complete the broader Pi host
baseline above and does not implement the M2 Teacher text round-trip.

### M1.2 Teacher Core Pi service increment

Hardware-UAT passed: reproducible artifacts installed the pinned Teacher
revision on a real Pi as an unprivileged, localhost-only systemd service with
external configuration, persistent SQLite, and repeatable Alembic migration.
Service enablement, health, a direct Groq-backed Core turn, reboot persistence,
localhost-only binding, and on-failure recovery were verified. No edge
TeacherClient is included; that integration remains M2 work.

## M2 — Device bridge skeleton + text round-trip

Goal: prove the architecture before audio complexity.

Scope:

- create `teacher-edge` bridge service
- implement health endpoint / device session skeleton
- implement Teacher HTTP client against pinned Teacher API
- send a synthetic / text device input through bridge to Teacher
- return Teacher assistant text as a device response

Acceptance criteria:

```text
Watcher or test client
→ Pi bridge
→ Teacher Core
→ assistant text
→ Pi bridge
→ client
```

No duplicate learning logic exists in the bridge.

## M3 — Voice conversation MVP

Goal: complete one full voice conversation turn without the MacBook.

Scope:

- Watcher microphone capture
- audio transport to Pi
- reuse Teacher STT boundary
- transcript → Teacher conversation
- ElevenLabs TTS adapter on Pi
- return playback + display content to Watcher
- transport / playback error handling

Primary acceptance criterion:

> With the MacBook powered off, the user speaks through the Watcher and receives the Teacher response on the Watcher display and speaker.

Verification must also confirm that the Teacher conversation / learning pipeline is the one that processed the turn.

## M4 — Review on Watcher

Goal: expose existing Teacher review semantics through the physical client.

Scope:

- present review question
- speech or supported device input for answer
- submit through Teacher review API
- render correct / incorrect / retry state
- preserve Teacher grading and scheduling semantics

Non-goal:

- independent edge grading

## M5 — Proactive physical companion

Goal: make Teacher's proactive system meaningful on an always-on device.

Scope:

- consume Teacher proactive check / invitation semantics
- physically notify on Watcher
- render Start / Later / Not today
- submit decisions to Teacher
- define interruption / quiet-hour presentation behavior

Acceptance criteria:

- Teacher remains the owner of invitation state
- device notification does not create duplicate invitations or review attempts
- Pi restart / Watcher reconnect does not corrupt proactive state

## M6 — Ambient input

Only after normal voice + review + proactive are stable.

Candidate work:

- local wake word
- VAD
- presence detection
- simple camera-derived events
- gestures mapped to presentation intents
- idle / sleep / wake behavior

Prefer local event detection and small semantic events over continuous camera streaming to a cloud model.

## M7 — Reliability / productization

Candidate work:

- device pairing / authentication
- reconnect and state restoration
- OTA / firmware update strategy
- Pi backup / recovery
- structured logs and diagnostics
- latency metrics
- long-running soak test
- provider fallback behavior

## Issue sequencing rule

Only one coherent implementation writer should work on a dependent path at a time.

Do not parallelize M2/M3 against unresolved M0 transport decisions. Do not start Review / Proactive UI before the basic Teacher round-trip is reliable.

Each issue should include:

- scope
- non-goals
- acceptance criteria
- verification
- relevant Teacher SHA / API contract
- relevant hardware / firmware version
