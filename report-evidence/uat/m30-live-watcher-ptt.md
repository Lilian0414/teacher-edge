# M3.0 stock Watcher PTT live transport — 2026-09-24

teacher-edge candidate: PR #15 / `e4333fcb1b87f3bace9c7f664c1f5e90f34835c8`

Observed on real SenseCAP Watcher + Raspberry Pi:

- Watcher Audio Task Composer was configured over BLE.
- With the service URL set to the full path, stock firmware appended its own path and produced:
  `POST /v2/watcher/talk/audio_stream/v2/watcher/talk/audio_stream` → 404.
- Reconfiguring Audio Task Composer to the **base URL only** (`http://<pi>:8834`) caused the stock Watcher to request:
  `POST /v2/watcher/talk/audio_stream`
- Pi journal then recorded:
  `POST /v2/watcher/talk/audio_stream HTTP/1.1` → **200 OK**

This proves the physical Watcher microphone transport reaches teacher-edge and the M3.0 endpoint returns HTTP 200 on real hardware.

Remaining device-side acceptance still to record:
- whether `Teacher Edge audio transport test` appears on the Watcher display;
- whether the deterministic ~150 ms WAV test tone is played.

Important firmware behavior found during UAT: the configured Audio Task Composer URL must be the service **base URL**, because stock firmware appends `/v2/watcher/talk/audio_stream` itself.
