# Teacher Edge — verified status

Updated from `main@babd8d35fa9461b6c78cdf11c5bc9ef7946f279d` (2026-09-24). This is the **only current milestone summary** in this repository. See [UAT](UAT.md) for observations and repeatable procedures, [ROADMAP](ROADMAP.md) for future work, and [INTEGRATION_CONTRACT](INTEGRATION_CONTRACT.md) for protocol details.

| Milestone | Verified state | Evidence / boundary |
| --- | --- | --- |
| M1.1 Watcher notification ingress + Pi service recovery | **PASS**, real Watcher and Pi | Authenticated human-detection notification and Pi systemd/reboot recovery; [PR #5](https://github.com/Lilian0414/teacher-edge/pull/5). Watcher taskflow provisioning after a Watcher reboot remains separate. |
| M1.2 pinned Teacher Core on Pi | **PASS**, real Pi | Core service, localhost health, Groq conversation, SQLite persistence and service recovery; Teacher pin `c1b6a03c1894df2d2b8994cf3b9a124ea8b381e5`; [PR #7](https://github.com/Lilian0414/teacher-edge/pull/7). |
| M2 edge → Teacher Core live text round-trip | **PASS**, real Pi | Two turns and device/session mapping reuse; [PR #14](https://github.com/Lilian0414/teacher-edge/pull/14). This is the text path, not Watcher voice. |
| M3.0 stock Watcher PTT transport / presentation | **PASS**, real Watcher and Pi | PTT → `POST /v2/watcher/talk/audio_stream` → `200 OK` → on-device `Teacher Edge audio transport test` and ~2 s deterministic tone. Hardware-tested implementation `6a6aa096fee2a522cf549a8ae835cf2a191a6d31`; [PR #15](https://github.com/Lilian0414/teacher-edge/pull/15). Later PR commits were documentation-only. |
| M3.1 Watcher voice → Teacher STT → Teacher conversation → ElevenLabs TTS → Watcher | **NEXT / pending** | [Issue #10](https://github.com/Lilian0414/teacher-edge/issues/10); no provider-backed Watcher voice loop or full end-to-end voice latency claim. |

PRs #7, #14, and #15 were merged in order using normal merge commits. Teacher owns Conversation, Memory, Learning, Review, and Proactive domain state. Edge owns device transport, runtime, session mapping, and physical presentation. M3.0 demonstrates stock transport and output using a deterministic test tone; it does not exercise STT, Teacher conversation, or ElevenLabs on the PTT path.
