# Hardware Baseline

Hardware inventory and assumptions only; current milestones live in [STATUS](STATUS.md).

## Raspberry Pi host

Target host:

- Raspberry Pi 5
- 16 GB RAM
- SSD storage
- active cooling

Intended role:

- always-on Teacher host
- `teacher-edge` device bridge host
- local SQLite storage for Teacher
- optional local embedding runtime
- service supervision through systemd

### Host assumptions to verify during setup

Record these before implementation depends on them:

- Raspberry Pi OS / Debian release
- CPU architecture (`aarch64` expected)
- Python version available for Teacher
- SSD mount path and filesystem
- network interface / static hostname
- Ollama availability on the selected OS image
- audio and camera are **not** assumed to be directly attached to the Pi for MVP

The MacBook is a development / maintenance machine, not a required runtime component.

## Physical client

Target device: Seeed Studio SenseCAP Watcher W1-A.

The project intends to use the Watcher as a thin physical interface for:

- microphone input
- speaker output
- display output
- local interaction controls
- camera / presence / gesture events in later phases

The exact firmware path is intentionally undecided until a spike verifies what can be reused safely and what transport the device can expose to the Pi.

## Power and placement

The final installation should support an always-on arrangement:

```text
wall power
  ├─ Raspberry Pi 5 + SSD + active cooling
  └─ SenseCAP Watcher
```

MVP should not depend on a laptop USB connection after provisioning.

## Storage

Teacher's durable database should live on the Pi SSD rather than relying on a microSD card for long-term writes.

Backups are a later operational task, but deployment design should keep database and configuration paths explicit so they can be backed up independently from application code.

## Thermal / reliability assumptions

Because the Pi may run continuously and may host local embedding inference, active cooling is part of the target baseline rather than an optional optimization.

Hardware UAT should record:

- sustained service uptime
- CPU temperature under representative interaction
- available memory
- disk free space
- whether local embedding causes unacceptable latency or throttling

## Hardware-specific non-goals for MVP

The first milestone does not require:

- custom PCB
- battery operation
- completely offline inference
- local generative LLM on the Pi
- continuous camera streaming to Teacher
- full-time audio streaming to cloud services

## Information still to capture

When physical setup starts, extend this document with the actual tested values rather than assumptions:

```text
Pi model:
RAM:
OS image:
Kernel:
Python:
SSD model / filesystem:
Hostname:
LAN address strategy:
Watcher firmware / version:
Watcher transport:
Power arrangement:
Cooling arrangement:
```

Do not record API keys, Wi-Fi passwords, pairing secrets, or other credentials in this document.
