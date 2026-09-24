# Roadmap — next work

M1.1, M1.2, M2, and M3.0 are complete; their **current** state and hardware evidence links live only in [STATUS](STATUS.md). The next increment is M3.1. The original planning baseline is preserved in [history/ROADMAP_BEFORE_M31.md](history/ROADMAP_BEFORE_M31.md); this file describes future work.

### M3.1 — End-to-end Teacher voice conversation

Next implementation milestone: [Issue #10](https://github.com/Lilian0414/teacher-edge/issues/10). Current verification state is maintained in [STATUS](STATUS.md).

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

Work on dependent milestones in order. Each new Issue should define scope, non-goals, acceptance criteria, verification, Teacher API / SHA, and hardware / firmware version. See [STATUS](STATUS.md) for the completed milestones and [UAT](UAT.md) for their observed results.
