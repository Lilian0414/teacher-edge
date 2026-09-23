# Hardware UAT

Status: **M1.1 Watcher-to-Pi ingress and edge reboot/systemd hardware UAT
passed; M1.2 Teacher Core deployment hardware UAT passed**.

The M1 ingress path was verified on a real SenseCAP Watcher and Raspberry Pi:
Watcher human detection produced an HTTP notification, the Pi bridge
authenticated it, and returned `200 OK`. No shared-token value or Authorization
header is retained here. The verified teacher-edge M1 main revision was
`77904412bbbfb21f72a63d951163201da79c94b8`; the sanitized observed path was
**real human detection → authenticated `POST /v1/notification/event` → `200
OK`**.

The M1.1 systemd path was subsequently verified on a real Raspberry Pi at
teacher-edge main revision `a5dc33140c15ced0a6e66ff3817f49a8fef7bbcc` (PR #5
merge commit). After reboot, `teacher-edge` was observed as both `enabled` and
`active`, and `/health` succeeded. The real Watcher remained powered on with
its `http alarm` taskflow unchanged; another real human detection traversed the
authenticated `POST /v1/notification/event` ingress and returned `200 OK`.
Device model, OS, firmware, network topology, and test time were not included
in the supplied sanitized result, so they remain evidence limitations rather
than being inferred here.

The M1.1 reboot procedure covers Pi reboot persistence only. The Watcher must
remain powered on and configured with the `http alarm` runtime taskflow during
that test. Rebooting the Watcher currently resets the runtime taskflow to
`sensecraft alarm`; persistent Watcher provisioning is a known limitation and
is outside the M1.1 scope.

For the repeatable systemd reboot procedure and evidence requirements, see
[`DEPLOYMENT.md`](DEPLOYMENT.md#edge-reboot-uat-hardware-passed-reusable-procedure).

The M1.2 Teacher Core deployment was hardware-verified on a real Raspberry Pi
using Python 3.13.5 and Teacher revision
`c1b6a03c1894df2d2b8994cf3b9a124ea8b381e5`. The installer completed
successfully, and `teacher-core` was observed as `enabled` and `active`.
`GET http://127.0.0.1:8000/health` returned healthy JSON, while the port 8000
listener was bound to `127.0.0.1:8000` and not `0.0.0.0:8000`.

Direct Core UAT created a conversation with `POST /v1/conversations`, then
`POST /v1/conversations/{id}/messages` returned `ok: true` with a real assistant
response through Groq. After a Pi reboot, that conversation and both messages
remained retrievable, demonstrating SQLite persistence; `teacher-core` also
auto-started and remained healthy. Finally, after
`sudo systemctl kill -s SIGKILL teacher-core`, the service and health endpoint
recovered, verifying `Restart=on-failure`. No provider key or other secret is
recorded here.

This was direct Teacher Core UAT. M2 edge-to-Teacher client integration remains
unimplemented, so these results do not demonstrate an edge-mediated Teacher
conversation turn.

This document defines the evidence required before claiming that a Teacher Edge milestone works on real hardware.

## Evidence header

Every UAT run should begin with:

```text
Date / time:
Tester:
teacher-edge commit SHA:
Teacher commit SHA:
Raspberry Pi model / RAM:
Pi OS:
Python:
Watcher model:
Watcher firmware / commit / version:
Bridge transport:
Network topology:
Embedding runtime:
LLM / STT provider:
TTS provider:
```

Do not include API keys, Wi-Fi passwords, pairing secrets, or other credentials.

## UAT-0 — Pi runtime baseline

Preconditions:

- MacBook is not required for runtime
- Pi boots from the intended storage
- Teacher environment is configured on Pi

Steps:

1. Reboot the Pi.
2. Verify Teacher Core becomes reachable locally.
3. Verify any required bridge service starts as expected.
4. Verify Teacher database is readable and persists across restart.
5. Run one known Teacher Core interaction directly from the Pi.
6. If local embeddings are enabled, run a representative embedding / memory retrieval path.

Pass criteria:

- services recover after reboot
- existing durable Teacher state remains available
- no runtime dependency on the MacBook exists
- no secret is printed into normal logs

## UAT-1 — Watcher ↔ Pi connectivity

Steps:

1. Power the Watcher independently from the MacBook.
2. Connect Watcher and Pi through the target network.
3. Establish the selected device session / transport.
4. Restart the bridge.
5. Confirm Watcher can reconnect or recover using the documented flow.

Pass criteria:

- Watcher can reach the Pi edge service
- connection state is visible enough to diagnose failure
- restart does not require reflashing or reconnecting a development laptop

## UAT-2 — Text round-trip

Steps:

1. Start a device session.
2. Send a known text input through the Watcher or the closest real-device control path.
3. Confirm bridge forwards the request to Teacher Core.
4. Confirm Teacher returns an assistant response.
5. Confirm response reaches the device presentation layer.

Pass criteria:

```text
Watcher / device client
→ bridge
→ Teacher Core
→ assistant response
→ bridge
→ Watcher / device client
```

The result must come from Teacher Core rather than an edge-side mock or second LLM path.

## UAT-3 — Voice conversation MVP

This is the first product-level acceptance test.

Preconditions:

- MacBook is powered off or otherwise absent from the runtime path
- Watcher microphone and speaker are functional through the selected firmware path
- Teacher Core is running on Pi
- STT and ElevenLabs credentials are configured on Pi

Steps:

1. Begin one normal conversation interaction on Watcher.
2. Speak a short English utterance.
3. Confirm Watcher audio reaches the Pi.
4. Confirm the audio is transcribed through the canonical speech path.
5. Confirm the transcript is submitted to Teacher conversation logic.
6. Confirm Teacher persists / processes the conversation through its normal path.
7. Confirm assistant text returns to the bridge.
8. Confirm ElevenLabs produces audio from the assistant text.
9. Confirm Watcher displays the response.
10. Confirm Watcher plays the response.

Pass criteria:

> A complete Teacher voice conversation turn succeeds on Watcher while the MacBook is not part of the runtime.

Also record approximate latency for:

```text
end of speech → transcript
transcript → Teacher response
Teacher response → first audible TTS
end-to-end
```

## UAT-4 — Failure / retry safety

Test at least:

- STT request failure
- Teacher Core unavailable
- ElevenLabs failure
- Watcher disconnect after Teacher accepted the message
- Pi bridge restart during an idle device session

Pass criteria:

- TTS retry does not create a duplicate Teacher message
- playback failure does not mutate learning state again
- transport retry does not blindly duplicate a conversation turn when Teacher success is already known
- errors are diagnosable from logs without exposing secrets

## UAT-5 — Review

When implemented:

1. Start a review through the Watcher.
2. Present a real due item from Teacher.
3. Submit an answer through the device interaction path.
4. Confirm Teacher performs grading.
5. Confirm Watcher renders the returned result.
6. Confirm Teacher attempt / scheduling state changes exactly once.

Pass criteria:

- no edge-side grading logic determines correctness
- retry behavior matches Teacher semantics
- device disconnect / replay cannot create duplicate attempts silently

## UAT-6 — Proactive invitation

When implemented:

1. Arrange a Teacher state where an invitation is legitimately eligible.
2. Allow the Pi / Watcher to run without manually opening a laptop UI.
3. Confirm the Watcher receives a physical invitation.
4. Test Start.
5. Test Later.
6. Test Not today / equivalent Teacher decision.
7. Verify quiet-hour / availability suppression once supported by the device presentation layer.

Pass criteria:

- Teacher remains the invitation source of truth
- physical notification does not create a second invitation system
- user decisions persist through Teacher's existing proactive state

## Soak test

Before calling the system suitable for daily use, run an always-on soak test.

Suggested first target: 24 hours.

Record:

- unexpected service restarts
- Watcher disconnects
- memory growth
- disk usage
- Pi temperature
- local embedding latency if enabled
- provider errors
- session recovery behavior

Increase the duration only after the basic 24-hour run is stable.

## M3.0 stock Watcher push-to-talk transport UAT (hardware-UAT partial)

This procedure verifies only the compatibility transport added in M3.0. It must
not be reported as a Teacher voice conversation, STT, or provider-backed TTS test.

1. Deploy the exact candidate teacher-edge SHA on the Pi and record the evidence
   header above, including Watcher model and stock firmware version.
2. Configure the same generated shared token and allowlisted EUI on the Pi and
   Watcher without recording either value in the UAT artifact.
   Confirm the request carries `Authorization`, `API-OBITER-DEVICE-EUI`,
   `Session-Id`, and `Content-Type: application/octet-stream` headers (record
   header names only, never their secret values).
3. Configure Audio Task Composer with the service **base URL only**,
   `http://<pi-lan-address>:<port>`, and retain the existing HTTP-alarm taskflow
   configuration. Stock firmware appends `/v2/watcher/talk/audio_stream`; do not
   include that path in the configured URL or it will be appended twice.
4. With the MacBook absent from the runtime path, press and hold talk, speak a
   short phrase, and release. Record a sanitized Pi log showing the endpoint and
   HTTP status, but not request audio or authorization headers.
5. Confirm the response is `application/octet-stream`, its `Content-Length`
   matches the complete body, and the bytes are compact JSON followed immediately
   by the literal `---sensecraftboundary---\n` and WAV audio. Confirm the Watcher
   uses `data.screen_text` to display `Teacher Edge audio transport test` and
   receives integer `data.mode: 0` and `data.duration: 2000`, then presents the
   text while playing the two-second deterministic tone exactly once.
6. Repeat with an upload larger than the configured limit (lower the limit for a
   safe test) and confirm `413`; interrupt one upload and confirm the service
   stays healthy and accepts the next normal push-to-talk request.
7. Trigger a real human-detection alarm and run one M2 text-boundary check to
   ensure those existing paths still work.

Record the observed transport as: **Watcher stock push-to-talk → authenticated
bounded binary upload → raw JSON + stock separator + WAV test response → Watcher display and
speaker**. Mark this section hardware-UAT passed only after attaching the
secret-free device/host/revision/result evidence. It is currently implemented
and locally testable. Hardware UAT on 2026-09-24 against
`e4333fcb1b87f3bace9c7f664c1f5e90f34835c8` verified the base-URL request path,
`200 OK`, and tone playback, but not visible text presentation. That result is
**partial**, not hardware-UAT passed; visible presentation and the regression
checks above must be repeated with the candidate SHA.

## UAT result template

```markdown
# UAT Result — <milestone> — <date>

## Environment
- teacher-edge SHA:
- Teacher SHA:
- Pi:
- OS:
- Watcher firmware:
- transport:

## Result
PASS / FAIL / PARTIAL

## Evidence
- command / log excerpt:
- device observation:
- screenshots / recordings if applicable:

## Failures / limitations
-

## Follow-up
-
```

A written UAT record is evidence of a specific hardware revision and software SHA. It is not proof that later commits remain valid without retesting.
