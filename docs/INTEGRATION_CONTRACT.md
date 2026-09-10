# Teacher ↔ Edge Integration Contract

Status: **initial contract / must be re-verified against the exact Teacher revision used for implementation**.

This document describes the boundary between `teacher-edge` and `Lilian0414/teacher`.

## 0. Implemented Watcher ingress contract

M1 implements the device-facing boundary only:

- `GET /health` returns `{"status":"healthy"}`.
- `POST /v1/notification/event` accepts the Watcher HTTP alarm JSON shape and
  returns `{"code":200}` after authentication and normalization.
- Seeed stock firmware copies the Watcher `notification_proxy.token` unchanged
  into the `Authorization` header rather than imposing a fixed `Bearer` scheme.
  `TEACHER_EDGE_SHARED_TOKEN` must therefore exactly match the configured
  `notification_proxy.token`. The bridge compares it in constant time and
  accepts the stock bare-token form as well as a `Bearer ` prefix.
- The shared token must be explicitly generated and managed on the Raspberry Pi
  and Watcher. Deployments must not rely on factory/generated credentials or
  commit an actual credential to this repository.
- `TEACHER_EDGE_ALLOWED_DEVICE_EUIS` may contain a comma-separated allowlist. An
  empty list permits any device EUI with the valid shared token.
- The request becomes an in-process `DeviceEvent` with source, device ID, event
  type, timestamp, text, inference, and original request ID.

No Teacher endpoint is consumed by M1, so there is no Teacher revision or API
schema dependency to pin. A later Teacher adapter must complete the version
compatibility record below before making calls.

## 1. Ownership rule

`teacher-edge` consumes Teacher Core as an HTTP service.

It must not import Teacher ORM models, repositories, UI internals, or duplicate learning-domain logic merely to avoid an API call.

If the required behavior cannot be expressed through the current Teacher API, open a scoped Teacher issue for the smallest missing API contract rather than copying the behavior here.

## 2. Known upstream API capabilities

At bootstrap time, Teacher already exposes HTTP boundaries for at least:

- creating a conversation
- sending a message to a conversation
- speech transcription
- review answer submission
- proactive invitation checking / response / completion

The first edge milestone only depends on the smallest subset required for one ordinary conversation turn.

Expected conceptual flow:

```text
POST Teacher speech transcription
    ↓ transcript
POST Teacher conversation message
    ↓ assistant response
```

Exact paths, request bodies, response schemas, status codes, retry semantics, and error behavior must be verified against the pinned Teacher revision before implementing the client.

## 3. Runtime placement

Preferred topology:

```text
teacher-edge bridge  →  http://127.0.0.1:<teacher-port>
Teacher Core
```

Teacher Core should remain localhost-only unless a concrete requirement proves otherwise.

Watcher clients should talk to the bridge, not directly to Teacher Core.

## 4. Bridge responsibilities

The bridge may:

- authenticate / identify the physical device
- accept Watcher audio or interaction events
- convert device transport into Teacher HTTP requests
- maintain transient device session state
- route transcript to the correct Teacher interaction mode
- call ElevenLabs TTS for Teacher response text
- return display and playback payloads to Watcher
- handle device-facing retries and connection recovery

The bridge must not:

- decide whether a message becomes a Learning Item
- perform review grading independently from Teacher
- alter review schedules independently from Teacher
- maintain a second memory store for learning context
- reinterpret Teacher results in a way that changes learning semantics

## 5. Conversation session mapping

A Watcher interaction session will need a mapping to a Teacher conversation ID.

Initial preference:

- bridge creates / obtains a Teacher conversation when a device conversation starts;
- bridge keeps the current Teacher conversation ID as transient edge session state;
- Teacher remains the durable owner of conversation messages;
- ending / replacing a device session should call the appropriate Teacher conversation lifecycle boundary once the exact API is verified.

Do not introduce a persistent edge conversation database unless reconnect requirements demonstrate that transient mapping is insufficient.

## 6. Speech

Initial target:

```text
Watcher audio
   ↓
bridge
   ↓
Teacher speech transcription boundary
   ↓
text transcript
```

For MVP, reuse Teacher's existing STT path rather than creating a second Groq transcription implementation in `teacher-edge`.

If later latency or streaming requirements require a dedicated edge STT adapter, treat that as an explicit architecture change and preserve one canonical transcript path into Teacher conversation / review logic.

## 7. TTS

TTS is edge presentation behavior.

Initial target provider: ElevenLabs.

Conceptual flow:

```text
Teacher assistant text
   ↓
teacher-edge TTS adapter
   ↓
ElevenLabs
   ↓
audio payload / stream
   ↓
Watcher speaker
```

Teacher learning state must not depend on whether TTS succeeds. A failed playback should be retriable without creating a duplicate Teacher message or duplicate learning effect.

## 8. Review mode

Later review integration should preserve Teacher as the source of truth:

```text
Teacher returns review item
   ↓
Watcher presents prompt
   ↓
user speech / input
   ↓
transcript
   ↓
Teacher review answer endpoint
   ↓
Teacher grading + state mutation
   ↓
Watcher renders result
```

No independent grading logic belongs in the bridge.

## 9. Proactive mode

Later proactive integration should consume Teacher's existing invitation semantics rather than inventing edge-only reminders.

The edge layer may decide **how to notify** the user physically; Teacher decides the learning invitation state and its domain response.

Examples of presentation-only edge behavior:

- wake the Watcher display
- play a soft notification sound
- render Start / Later / Not today
- send the selected response back to Teacher

## 10. Version compatibility

Every implementation issue that depends on Teacher should record:

```text
Teacher repository:
Teacher base branch:
Teacher base SHA:
Consumed endpoints:
Required schema assumptions:
```

Hardware UAT must record the actual Teacher SHA used.

Do not claim compatibility with "latest Teacher" without testing that revision.

## 11. Failure semantics to preserve

Edge retries must distinguish transport failure from Teacher domain success.

Examples:

- Teacher accepted and persisted a message, but TTS failed → retry TTS only.
- Watcher disconnected after Teacher returned a response → restore presentation if practical; do not blindly resend the conversation message.
- STT failed before a transcript existed → safe to retry transcription of the same captured audio.
- Teacher request timed out with unknown commit state → inspect / use idempotency semantics provided by Teacher before resending.

Concrete retry rules should be implemented only after the exact Teacher API behavior is inspected.
