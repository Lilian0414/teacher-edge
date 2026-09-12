# Hardware UAT

Status: **M1 Watcher-to-Pi ingress hardware UAT passed before the systemd
deployment; edge and Teacher Core reboot/systemd UAT remain pending**.

The M1 ingress path was verified on a real SenseCAP Watcher and Raspberry Pi:
Watcher human detection produced an HTTP notification, the Pi bridge
authenticated it, and returned `200 OK`. No shared-token value or Authorization
header is retained here. The verified teacher-edge M1 main revision was
`77904412bbbfb21f72a63d951163201da79c94b8`; the sanitized observed path was
**real human detection → authenticated `POST /v1/notification/event` → `200
OK`**. This evidence establishes the M1 transport/auth path; it does not
establish that the newly added systemd service survives reboot. The original
evidence did not include enough other sanitized hardware/software revision
detail to reconstruct the environment, so those details remain an explicit
limitation and must be captured during reboot UAT.

The M1.1 reboot procedure covers Pi reboot persistence only. The Watcher must
remain powered on and configured with the `http alarm` runtime taskflow during
that test. Rebooting the Watcher currently resets the runtime taskflow to
`sensecraft alarm`; persistent Watcher provisioning is a known limitation and
is outside the M1.1 scope.

For the repeatable systemd reboot procedure and required evidence, see
[`DEPLOYMENT.md`](DEPLOYMENT.md#reboot-uat-must-run-on-the-real-pi).

M1.2 adds pinned Teacher Core service, migration, localhost binding, and
persistent-database deployment artifacts. The separate
[Teacher Core reboot/provider procedure](DEPLOYMENT.md#teacher-core-reboot-and-provider-uat-real-pi-only)
must pass on the target Pi before those properties are called hardware verified.
It records the exact Teacher SHA and one direct real conversation turn without
implementing an edge TeacherClient.

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
