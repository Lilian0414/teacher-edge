# Teacher Edge Watcher→Pi ingress benchmark — 2026-09-27

## Purpose

Provide checked-in measured evidence for report section 3.3 covering the currently implemented stock Watcher Human Detection → HTTP alarm → Raspberry Pi ingress path.

This benchmark does **not** measure full human-detection-to-Pi latency because the Watcher event clock and Raspberry Pi capture clock were not synchronized. The latency metric below is deliberately scoped to the Pi-observed HTTP request-payload → response-payload turnaround on port 8834.

## Runtime provenance

- Raspberry Pi runtime checkout: `/home/lilianma/teacher-edge`
- Runtime commit: `6a6aa096fee2a522cf549a8ae835cf2a191a6d31`
- Runtime state during provenance check: detached HEAD; local `report-evidence/` was untracked
- Teacher Edge endpoint: `POST /v1/notification/event`
- Pi ingress address during the run: `10.144.1.225:8834`
- Watcher source address observed in journal: `10.144.1.106`
- Watcher path: stock Human Detection taskflow → `alarm trigger` → `http alarm`
- `notification_proxy` target: `http://10.144.1.225:8834`
- Authentication token was configured on Watcher and Pi but is intentionally omitted.

## Procedure

A controlled real-hardware run used 20 manual human-detection presentations. Attempts were separated so the configured 5 s silence period would not turn one continuous presence into multiple counted attempts.

Two Pi-side captures were recorded concurrently:

1. `journalctl -u teacher-edge` for accepted `POST /v1/notification/event` responses.
2. `tcpdump -i any -n -tt -l 'tcp port 8834'` for packet timestamps.

Success was counted only from completed `POST /v1/notification/event HTTP/1.1" 200 OK` entries during the benchmark window.

The packet-analysis script paired positive-length client→server payload traffic with the first positive-length server→client payload traffic for the same client/server socket tuple. Therefore the reported latency is a Pi-observed HTTP turnaround measurement, not camera inference latency, network-only RTT, application-only processing time, or end-to-end user-perceived latency.

## Results

### Event success

- Attempts: 20
- Successful HTTP ingress events: 20
- Failures: 0
- Observed success rate: 100.0%
- Wilson 95% confidence interval for 20/20: approximately 83.9%–100.0%

This is the observed rate for this 20-attempt hardware run under one local-network condition; it is not a universal reliability guarantee.

### Pi-observed HTTP turnaround

- Samples: 20
- Minimum: 3.809 ms
- Median: 4.461 ms
- p95: 6.682 ms
- Maximum: 7.609 ms

Raw samples in milliseconds:

`3.809, 4.361, 4.364, 4.370, 4.374, 4.388, 4.395, 4.423, 4.442, 4.461, 4.461, 4.498, 4.607, 4.934, 5.429, 5.436, 5.449, 6.490, 6.579, 7.609`

## Error classification boundary

This run contained no observed hardware-ingress failures, so it does not provide an empirical distribution of failure modes.

The implemented bridge still has deterministic error categories covered separately by repository tests, including authentication/device rejection (HTTP 401) and malformed or incomplete payload rejection (HTTP 422). Those test cases must not be mixed into the denominator of the 20-attempt real-hardware success rate.

## Limitations

- Watcher and Pi clocks were not synchronized, so `t_event → t_receive` was not measured.
- The reported latency starts after request payload traffic is observed on the Pi and ends when response payload traffic is observed leaving the Pi.
- One Watcher, one Raspberry Pi, one LAN condition, and 20 attempts were measured.
- No fault-injection run was included in this benchmark.
- This evidence does not measure Teacher conversation latency, STT, provider-backed TTS, Watcher playback, or the full M3.1 voice round trip.
