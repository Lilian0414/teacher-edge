# M3.0 stock Watcher PTT live transport — 2026-09-24

teacher-edge candidate: PR #15
final hardware-UAT candidate: `6a6aa096fee2a522cf549a8ae835cf2a191a6d31`

## Result

**PASS**

Observed on real SenseCAP Watcher + Raspberry Pi:

- Watcher Audio Task Composer was configured over BLE.
- Configuring the full endpoint caused stock firmware to append its own path and produce:
  `POST /v2/watcher/talk/audio_stream/v2/watcher/talk/audio_stream` → 404.
- Reconfiguring Audio Task Composer to the **base URL only** (`http://<pi>:8834`) caused the stock Watcher to request:
  `POST /v2/watcher/talk/audio_stream`.
- Pi journal recorded:
  `POST /v2/watcher/talk/audio_stream HTTP/1.1` → **200 OK**.
- On the earlier 150 ms candidate, the Watcher played the short deterministic tone but visible text presentation could not be confirmed.
- Candidate `6a6aa096fee2a522cf549a8ae835cf2a191a6d31` extended the deterministic response interval to 2 seconds.
- Re-test on real hardware confirmed all of the following:
  - request reached the expected stock endpoint;
  - HTTP response was 200 OK;
  - the Watcher played the approximately 2-second deterministic test tone;
  - the Watcher visibly displayed `Teacher Edge audio transport test`.

## What this proves

The physical stock Watcher push-to-talk transport reaches teacher-edge, the endpoint accepts the microphone upload, the stock-compatible JSON/separator/WAV response framing is accepted, the Watcher speaker plays returned audio, and `data.screen_text` is visibly presented on device.

This is a transport/presentation UAT only. It does **not** claim STT, Teacher conversation logic, or provider-backed TTS; those remain M3.1 scope.

Important firmware behavior verified during UAT: Audio Task Composer must be configured with the service **base URL**, because stock firmware appends `/v2/watcher/talk/audio_stream` itself.
