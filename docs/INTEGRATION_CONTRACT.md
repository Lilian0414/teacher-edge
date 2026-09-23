# Teacher ↔ Edge Integration Contract

Status: **deployment contract verified for the pinned Teacher revision; M2 text client
contract implemented and live edge→Core UAT passed; M3.0 stock Watcher transport/presentation hardware-UAT passed**.

This document describes the boundary between `teacher-edge` and `Lilian0414/teacher`.

## M3.0 implemented stock Watcher push-to-talk compatibility

`POST /v2/watcher/talk/audio_stream` is a **transport-only compatibility
endpoint**. It accepts a non-empty binary Watcher upload (`application/octet-stream`
or WAV), authenticates the existing bare-token or Bearer credential, and applies
the existing device allowlist. The stock `API-OBITER-DEVICE-EUI` header is the
primary device identity. The `deviceEui` query parameter and `X-Device-Eui`
header remain compatibility fallbacks; `device_eui` and `deviceSn` query
spellings are also tolerated for deployed clients. The stock `Session-Id`
header is accepted but is not used by this transport-only stub.

Uploads are buffered only up to `TEACHER_EDGE_WATCHER_AUDIO_MAX_BYTES` (default
2,000,000 bytes). Declared or streamed over-limit bodies return `413`; empty,
invalid-length, and disconnected bodies return a bounded 4xx response. Unsupported
media types return `415`.

A successful response is `application/octet-stream` containing compact JSON
bytes, the literal `---sensecraftboundary---\n` separator, and a deterministic
16-kHz, mono, 16-bit PCM WAV test tone, in that order. Its `Content-Length` is
the total byte length of all three segments. The JSON returns `code: 200` and
`data.stt_result`, `data.screen_text`, integer `data.mode: 0` (chat), and integer
`data.duration: 2000` (milliseconds, matching the test WAV). Stock firmware
presents `data.screen_text` during the audio response; the two-second test tone
therefore provides an observable presentation interval (the former 150 ms tone
was audible but too short for reliable visual UAT). This endpoint does not call STT, Teacher Core, conversation logic, or a
TTS provider; its response proves only stock firmware upload/JSON/audio framing.
On real hardware, PR #15 head `6a6aa096fee2a522cf549a8ae835cf2a191a6d31`
was verified to return `200 OK`, present `Teacher Edge audio transport test`
on the Watcher display, and play the deterministic two-second tone. The M1 alarm
endpoint and M2 text endpoint are unchanged.

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

M1.2 deploys, but does not consume, Teacher Core using this runtime contract:

```text
Teacher repository: Lilian0414/teacher
Teacher base branch: main
Teacher base SHA: c1b6a03c1894df2d2b8994cf3b9a124ea8b381e5
Entry point: companion-core
Health: GET http://127.0.0.1:8000/health
Later M2 endpoints: POST /v1/conversations
                    POST /v1/conversations/{conversation_id}/messages
```

Manual deployment UAT uses the pinned Core OpenAPI schema. M2 now documents and
contract-tests the exact request/response assumptions consumed by the edge client
in section 12 below.

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

## 12. M2 implemented Teacher conversation contract

Status: **implemented; live Raspberry Pi → Teacher Core text round-trip UAT passed**.

Compatibility baseline:

```text
teacher-edge stacked base: PR #7 head 5eacb2413ee2af63635c4f5992f51f9c19c1cdeb
Teacher repository: Lilian0414/teacher
Teacher runtime: the immutable revision installed by the PR #7 deployment pin
Network origin: http://127.0.0.1:8000 (fixed; non-loopback origins are rejected)
```

The adapter consumes exactly these two calls:

### Create conversation

```http
POST /v1/conversations
Content-Type: application/json

{}
```

Successful responses may be any 2xx status and must contain a non-empty string
conversation ID. Additional fields are ignored:

```json
{"id":"<teacher-conversation-id>"}
```

### Send conversation message

```http
POST /v1/conversations/{conversation_id}/messages
Content-Type: application/json

{"content":"<user text>"}
```

Successful generation responses may be any 2xx status and contain:

```json
{"ok":true,"assistant_message":{"content":"<assistant text>"},"retryable":false}
```

Generation failures are also valid 2xx responses. The user message may already be
persisted by Teacher, so the edge preserves Teacher's authoritative retryability
without replaying the request or exposing the provider error:

```json
{"ok":false,"assistant_message":null,"error":"<provider detail>","retryable":true}
```

Additional response fields, including user-message metadata, are ignored. The edge
does not interpret either message, persist message history, or implement any
Conversation, Memory, Learning, grading, scheduling, Review, or Proactive behavior.

### Edge text transport

Authenticated devices can exercise the synthetic round trip with
`POST /v1/text`. Its JSON fields are `request_id`, `device_eui`, `text`, and the
optional `session_id`. Explicit session IDs are namespaced by `device_eui`, so the
same session string used by two devices cannot share a conversation. When omitted,
`device_eui` is the session fallback. The response fields are `conversation_id` and
`assistant_text`. A session ID maps transiently and in memory to a Teacher
conversation ID; loss of the edge process only loses that transport mapping.

Timeouts, connection errors, Teacher 5xx responses, and 2xx failure envelopes whose
`retryable` field is true are classified as retryable and returned to the device as
a sanitized 503. Teacher 4xx and malformed 2xx responses, plus failure envelopes
whose `retryable` field is false, are non-retryable and become a sanitized 502. The
edge does not automatically replay either POST because Teacher exposes no
idempotency contract; a timeout may have occurred after Teacher committed the
operation. Logs contain only endpoint paths, status codes, error classes, and
retryability—not request or response bodies, authorization values, or provider
errors.
