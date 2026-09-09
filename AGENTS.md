# AGENTS.md

This repository is the edge / physical-device layer for `Lilian0414/teacher`.

## Product boundary

`teacher-edge` owns device connectivity, Raspberry Pi runtime concerns, audio transport, TTS delivery, device state, deployment, and hardware verification.

It does **not** own Teacher's learning-domain behavior. Do not duplicate or fork Conversation, Memory, Learning Signal, Learning Item, Review, grading, scheduling, or Proactive logic into this repository.

When an implementation appears to require a Teacher Core change, first identify the missing API or contract explicitly. Keep the cross-repository change minimal and document which repository owns each behavior.

## Development workflow

For every implementation task:

1. Inspect the repository and relevant upstream Teacher API before changing code.
2. Confirm the task scope, non-goals, acceptance criteria, and verification plan from the GitHub Issue/spec.
3. Implement only the coherent task assigned to you.
4. Run repository-native verification relevant to the change.
5. Commit the implementation.
6. Report changed files, verification performed, known limitations, and commit SHA.
7. STOP.

Do not create a pull request and do not merge. PR publication is handled separately.

If a PR or publication step fails after a valid implementation commit exists, do not reimplement the task.

## Architecture constraints

- Watcher is a thin physical client, not the learning brain.
- Raspberry Pi is the edge host and secret-bearing runtime.
- Teacher Core remains the source of truth for learning state.
- Prefer a narrow device bridge between Watcher-facing transport and Teacher Core.
- Keep Teacher Core on localhost when possible; expose only the bridge to the LAN.
- Do not place Groq, ElevenLabs, or other provider secrets in Watcher firmware.
- Do not create a second learning database in `teacher-edge`.
- Device/session state may be persisted here only when it is genuinely device/runtime state rather than learning state.
- Treat camera, wake word, gesture, and proactive device behavior as later layers; do not block the basic text/audio round-trip on them.

## MVP acceptance target

The first complete milestone is:

> With the MacBook powered off, a user can complete one Teacher voice conversation turn through the SenseCAP Watcher, with the Raspberry Pi hosting the edge runtime and Teacher Core, and with the response rendered and spoken back on the Watcher.

The MVP does not require wake word, camera understanding, gestures, or fully local generative inference.

## Evidence rules

Do not describe planned components as implemented. Documentation and reports must distinguish among:

- planned
- implemented
- verified locally
- hardware-UAT passed
- PR available
- CI green
- merged

For hardware-facing work, include enough evidence to identify the tested device, host, software revision, transport path, and observed result.

## Security and configuration

- Secrets belong on the Raspberry Pi or an approved secret store, never in source control or Watcher firmware.
- `.env`, tokens, device credentials, generated audio, local databases, and UAT artifacts containing private data must not be committed unless explicitly sanitized.
- Prefer explicit allowlisted device/API boundaries over exposing the full Teacher Core to the LAN.

## Cross-repository compatibility

When consuming Teacher APIs:

- document the endpoint and payload assumptions in `docs/INTEGRATION_CONTRACT.md`;
- avoid depending on undocumented UI behavior from the Teacher Textual client;
- consume Teacher Core as an HTTP service;
- add contract/integration tests where practical;
- if Teacher changes are required, reference the Teacher commit/PR that provides the compatible API.
