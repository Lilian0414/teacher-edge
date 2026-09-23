# teacher-edge

`teacher-edge` 是 [Lilian0414/teacher](https://github.com/Lilian0414/teacher) 的實體裝置與邊緣執行層。

它不重新實作 Teacher；它負責讓 Teacher 的既有 Conversation、Memory、Learning、Review 與 Proactive learning loop 能在沒有 MacBook 參與的情況下，透過 Raspberry Pi 與 SenseCAP Watcher 成為常駐的實體 AI learning companion。

> **Teacher is the learning brain. Raspberry Pi is the edge host. Watcher is the physical interface.**

## Target setup

```text
SenseCAP Watcher
  microphone / display / speaker / camera / touch
              │
              │ Wi-Fi / device transport
              ▼
Raspberry Pi 5 16GB
  teacher-edge device bridge
  Teacher FastAPI Core
  SQLite
  local embedding runtime (target: Ollama)
  proactive / device background jobs
              │
      ┌───────┼────────┐
      ▼       ▼        ▼
    Groq   ElevenLabs  optional remote services
   LLM/STT      TTS
```

目前硬體目標為 Raspberry Pi 5 16GB + SSD + 主動散熱，以及 SenseCAP Watcher W1-A。

## Repository boundary

這個 repository 預計負責：

- Raspberry Pi 上的 device bridge / gateway
- Watcher 與 Pi 之間的連線、裝置 session 與事件 transport
- audio ingress / egress
- ElevenLabs TTS integration
- wake word / VAD 等 edge-side audio processing（後續階段）
- Watcher display / speaker / touch / camera event 的 device-facing integration
- Raspberry Pi deployment、systemd、configuration 與 hardware UAT
- Teacher Core 的 edge-side client / adapter

這個 repository **不負責**：

- 重新實作 Teacher 的 Conversation / Memory / Learning / Review / Proactive domain logic
- 在 Watcher firmware 內放 Groq、ElevenLabs 等 provider secrets
- 為硬體另外建立一套 learning state
- MVP 階段重新設計 Teacher database schema
- MVP 階段追求完全離線的大型生成式 LLM

## MVP

第一個完整硬體里程碑只有一件事：

> **MacBook 關機時，使用者可以透過 Watcher 完成一輪 Teacher 語音對話。**

預期資料流：

```text
Watcher microphone
    ↓
teacher-edge on Raspberry Pi
    ↓
Teacher speech / conversation API
    ↓
Teacher response
    ↓
ElevenLabs TTS
    ↓
Watcher speaker + display
```

第一版不要求 wake word、camera understanding、gesture 或 proactive notification；這些在基本 round-trip 穩定後再加入。

## Repository layout

```text
teacher-edge/
├── bridge/                 # Raspberry Pi device gateway / Teacher adapter
├── deploy/
│   └── raspberry-pi/       # systemd / install / config
├── tests/
├── docs/
│   ├── STATUS.md
│   ├── ARCHITECTURE.md
│   ├── HARDWARE.md
│   ├── INTEGRATION_CONTRACT.md
│   ├── ROADMAP.md
│   └── UAT.md
├── AGENTS.md
└── README.md
```

此處為目前 repository 目錄；未實作的 device feature 以 [ROADMAP](docs/ROADMAP.md) 為準。

## Current status

M1.1、M1.2、M2 與 M3.0 已分階段通過實機驗收；完整 provider-backed Watcher 語音對話為下一階段 M3.1。最新里程碑、測試 SHA 與明確邊界只維護在 [`docs/STATUS.md`](docs/STATUS.md)。

架構、協定、部署、可重複 UAT 與後續工作分別見 [ARCHITECTURE](docs/ARCHITECTURE.md)、[INTEGRATION_CONTRACT](docs/INTEGRATION_CONTRACT.md)、[DEPLOYMENT](docs/DEPLOYMENT.md)、[UAT](docs/UAT.md) 與 [ROADMAP](docs/ROADMAP.md)。

## Run the notification ingress on Raspberry Pi

Python 3.11+ is required. Keep real values in the Pi environment (or an untracked
`.env` consumed by the service manager):

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
export TEACHER_EDGE_SHARED_TOKEN='<local-shared-token>'
export TEACHER_EDGE_ALLOWED_DEVICE_EUIS='<watcher-device-eui>'
uvicorn bridge.app:app --host 0.0.0.0 --port 8834
```

Seeed stock firmware sends the Watcher `notification_proxy.token` unchanged in
the `Authorization` header; it does not add a fixed `Bearer` scheme. Set
`TEACHER_EDGE_SHARED_TOKEN` to exactly the same value as
`notification_proxy.token`. A Watcher configured with a bare token therefore
sends, and the bridge accepts, `Authorization: <local-shared-token>`. Generate
and manage this shared token yourself on the Raspberry Pi and Watcher; do not
depend on factory/generated device credentials or commit the real value.

Sanitized request example:

```bash
curl -X POST http://PI_LAN_IP:8834/v1/notification/event \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <local-shared-token>' \
  -d '{"requestId":"example-request","deviceEui":"<watcher-device-eui>","events":{"timestamp":1788983266392,"text":"human detected","data":{"inference":{"boxes":[[145,262,240,308,83,0]],"classes_name":["person"]}}}}'
```

**This notification endpoint** validates and normalizes event metadata, then acknowledges with `{"code":200}`. It does not call Teacher Core or render a response. Other endpoints have separate behavior in [INTEGRATION_CONTRACT](docs/INTEGRATION_CONTRACT.md).

For reboot-safe Raspberry Pi installation and operational commands, see
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).
