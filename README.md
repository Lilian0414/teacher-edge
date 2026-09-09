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

## Planned repository layout

```text
teacher-edge/
├── bridge/                 # Raspberry Pi device gateway / Teacher adapter
├── watcher/                # Watcher-side firmware or client integration
├── deploy/
│   └── raspberry-pi/       # systemd / install / config
├── tests/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── HARDWARE.md
│   ├── INTEGRATION_CONTRACT.md
│   ├── ROADMAP.md
│   └── UAT.md
├── AGENTS.md
└── README.md
```

以上是 target layout；在有實作證據前，不應把規劃內容描述成已完成。

## Current status

目前為 **architecture / hardware integration bootstrap** 階段。

- Teacher Core：既有專案，另 repo 維護
- Raspberry Pi host：硬體已具備，尚未在本 repo 建立 runtime
- Watcher integration：尚未實作
- ElevenLabs TTS：已選為目標 provider，尚未在本 repo 串接
- Hardware UAT：尚未開始

詳見 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)、[`docs/INTEGRATION_CONTRACT.md`](docs/INTEGRATION_CONTRACT.md)、[`docs/ROADMAP.md`](docs/ROADMAP.md) 與 [`docs/UAT.md`](docs/UAT.md)。
