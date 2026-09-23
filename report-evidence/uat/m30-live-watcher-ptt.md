# M3.0 stock Watcher PTT live transport — 2026-09-24

teacher-edge candidate: PR #15 / `e4333fcb1b87f3bace9c7f664c1f5e90f34835c8`

## Result

**PARTIAL**

Observed on real SenseCAP Watcher + Raspberry Pi:

- Watcher Audio Task Composer was configured over BLE.
- With the service URL set to the full path, stock firmware appended its own path and produced:
  `POST /v2/watcher/talk/audio_stream/v2/watcher/talk/audio_stream` → 404.
- Reconfiguring Audio Task Composer to the **base URL only** (`http://<pi>:8834`) caused the stock Watcher to request:
  `POST /v2/watcher/talk/audio_stream`
- Pi journal then recorded:
  `POST /v2/watcher/talk/audio_stream HTTP/1.1` → **200 OK**
- The Watcher speaker played the returned short deterministic test tone.
- The Watcher **did not display** `Teacher Edge audio transport test`.

## What this proves

The physical Watcher microphone transport reaches teacher-edge, the M3.0 endpoint returns HTTP 200, and the returned WAV/audio framing is accepted well enough for the stock Watcher speaker to play it.

## Remaining blocker

The display/presentation metadata path is not hardware-verified. The current assumption that `data.screen_text` from this response produces visible stock-Watcher text did not hold in this UAT.

Do not mark M3.0 hardware UAT PASS until the display behavior is understood and either fixed or the acceptance/documentation is corrected based on verified stock-firmware behavior.

Important firmware behavior found during UAT: the configured Audio Task Composer URL must be the service **base URL**, because stock firmware appends `/v2/watcher/talk/audio_stream` itself.
