# Pi-local Teacher Core round-trip — 2026-09-24

Teacher revision: `c1b6a03c1894df2d2b8994cf3b9a124ea8b381e5`

Observed on Raspberry Pi:

- `teacher-core.service` enabled
- Core listening only on `127.0.0.1:8000`
- `GET /health` returned healthy JSON
- `POST /v1/conversations` created conversation `9cb69872-c11b-4de6-9285-c911b108a347`
- `POST /v1/conversations/{id}/messages` returned `ok=true`, `retryable=false`, no error, and a non-empty assistant message
- observed assistant text: `Learning English opens doors to new cultures.`

Result: **PASS**

This is direct Teacher Core UAT on the Pi. It establishes the M1.2 runtime baseline needed by M2, but does not by itself prove the edge-mediated text path.
