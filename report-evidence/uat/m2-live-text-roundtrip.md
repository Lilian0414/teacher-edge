# M2 live edge-to-Teacher text round-trip — 2026-09-24

teacher-edge PR #14 head: `bb7d25d798cf973e3939a3c7fb967895181aa52c`
Teacher Core revision: `c1b6a03c1894df2d2b8994cf3b9a124ea8b381e5`

Observed on the target Raspberry Pi:

- authenticated request entered `teacher-edge` at `POST /v1/text`;
- edge called Pi-local Teacher Core on `127.0.0.1:8000`;
- first text turn returned HTTP 200 with non-empty assistant text;
- second text turn returned HTTP 200 with non-empty assistant text;
- the same explicit edge session reused the same Teacher conversation ID across both turns.

Result:

```text
turn1_ok = True
turn2_ok = True
session_reused = True
overall = PASS
```

This closes the live Pi UAT gap for the M2 text round-trip. It establishes:

`client -> teacher-edge -> Teacher Core -> assistant text -> teacher-edge -> client`

No claim is made here about Watcher audio, STT, TTS, or playback; those remain M3 work.
