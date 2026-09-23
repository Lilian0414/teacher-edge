# M1.1 post-reboot Watcher ingress evidence — 2026-09-24

teacher-edge main revision under test: `a5dc33140c15ced0a6e66ff3817f49a8fef7bbcc`

Sanitized observed journal sequence after Raspberry Pi reboot:

```text
systemd: Started teacher-edge.service - Teacher Edge Watcher HTTP bridge.
uvicorn: Application startup complete.
uvicorn: Uvicorn running on 0.0.0.0:8834
GET /health HTTP/1.1 -> 200 OK
POST /v1/notification/event HTTP/1.1 -> 200 OK
```

The Watcher source address and secrets are intentionally omitted.

## What this establishes

- the systemd unit started the bridge after Pi reboot;
- localhost health returned HTTP 200 after restart;
- a real Watcher event reached the Pi ingress after reboot;
- the authenticated Watcher notification endpoint returned HTTP 200.

## Remaining M1.1 check

Crash-recovery evidence is still required: send SIGKILL to the service, wait for systemd `Restart=on-failure`, then verify the service returns to active and `/health` succeeds.
