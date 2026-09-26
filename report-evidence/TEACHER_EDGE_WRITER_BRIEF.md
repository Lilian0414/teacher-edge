# Teacher Edge report writer brief

## Evidence status

Measured Teacher Edge ingress evidence is now available for report section 3.3.

Primary measured source:
- `report-evidence/experiments/watcher-pi-ingress-benchmark-2026-09-27.md`

Runtime measured:
- teacher-edge commit `6a6aa096fee2a522cf549a8ae835cf2a191a6d31`
- real SenseCAP Watcher → Raspberry Pi
- `POST /v1/notification/event`

## Values safe to use

For the 2026-09-27 controlled 20-attempt hardware run:

- attempts = 20
- successful ingress events = 20
- failures = 0
- observed success rate = 100.0%
- Wilson 95% CI ≈ 83.9%–100.0%

Pi-observed HTTP request-payload → response-payload turnaround:

- n = 20
- min = 3.809 ms
- median = 4.461 ms
- p95 = 6.682 ms
- max = 7.609 ms

These values may be used in section 3.3 only with the scope and limitations below.

## Required wording boundary

Do **not** call 4.461 ms or 6.682 ms “human detection latency”, “Watcher→Pi end-to-end latency”, “AI response latency”, or “device RTT”.

Preferred description:

> Pi-observed HTTP request-payload-to-response-payload turnaround for the Watcher ingress endpoint.

The Watcher event clock and Pi capture clock were not synchronized, so full `t_event → t_receive` latency was not measured.

The 100.0% figure is the observed result of this 20-attempt run under one LAN condition. Do not present it as a universal reliability guarantee.

## 3.3.2 error classification

Do not invent hardware failure counts: this run had zero observed failures.

Bridge tests may be used descriptively to explain deterministic rejection classes:
- invalid/missing authentication or disallowed device → HTTP 401
- malformed/incomplete payload → HTTP 422

Keep those test cases separate from the real-hardware denominator; test pass counts are not hardware event success-rate samples.

## Other checked-in UAT evidence

Use existing files under `report-evidence/uat/` for qualitative hardware/UAT claims:
- `m11-hardware-uat-summary.md`
- `m2-live-text-roundtrip.md`
- `m30-live-watcher-ptt.md`
- `teacher-core-pi-roundtrip.md`

Do not convert those pass/fail UAT records into latency or success-rate statistics.

## Not yet measured

Do not claim measured values for:
- full camera detection → Pi receive latency
- STT latency
- Teacher conversation latency through the Watcher voice path
- provider-backed TTS latency
- full Watcher voice round-trip latency
