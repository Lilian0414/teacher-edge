# M1.1 crash-recovery evidence — 2026-09-24

teacher-edge main revision under test: `a5dc33140c15ced0a6e66ff3817f49a8fef7bbcc`

Observed sequence:

```text
02:18:48 systemd: Sent SIGKILL to main process 1696 (uvicorn)
02:18:48 systemd: Main process exited, code=killed, status=9/KILL
02:18:48 systemd: Failed with result 'signal'
02:18:53 systemd: Scheduled restart job, restart counter is at 1
02:18:53 systemd: Started teacher-edge.service
02:18:54 uvicorn: Application startup complete
02:18:55 GET /health HTTP/1.1 -> 200 OK
```

Post-recovery checks:

- `systemctl is-active teacher-edge` -> `active`
- `GET http://127.0.0.1:8834/health` -> `{"status":"healthy"}`

Result: **PASS**

This demonstrates that the tracked systemd deployment recovers from an unexpected bridge-process failure through `Restart=on-failure`.
