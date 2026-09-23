# M1.1 hardware UAT summary — 2026-09-24

Revision under test: `a5dc33140c15ced0a6e66ff3817f49a8fef7bbcc`

Result: **PASS**

Verified on the target Raspberry Pi and real SenseCAP Watcher path:

- systemd service enabled and started automatically after Pi reboot;
- localhost `/health` returned HTTP 200 after reboot;
- real Watcher notification reached `POST /v1/notification/event` after reboot and returned HTTP 200;
- killing the uvicorn main process with SIGKILL produced a failed-unit state, then systemd scheduled a restart about five seconds later;
- the restarted bridge became active and `/health` again returned `{"status":"healthy"}`.

This closes the previously pending M1.1 reboot/systemd hardware-UAT item.

Scope note: this UAT establishes reboot persistence and Watcher-to-Pi ingress recovery. It does not establish Teacher Core forwarding, text round-trip, audio round-trip, or outbound Watcher rendering; those remain subsequent milestones.
