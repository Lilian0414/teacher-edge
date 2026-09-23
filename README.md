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

`bridge/` 的 Watcher HTTP ingress 與其 focused tests 已實作；其餘目錄仍是 target layout。

## Current status

目前已完成 **Watcher ingress、Teacher Core Pi deployment、M2 edge→Teacher text round-trip，以及 M3.0 stock Watcher PTT transport/presentation 的實機驗收**。下一個未完成里程碑是 M3.1 完整語音閉環。

- Teacher Core：既有專案，另 repo 維護
- Raspberry Pi host：FastAPI ingress 的 systemd reboot UAT 已於實機通過；pinned Teacher Core systemd deployment 的安裝、reboot、provider、SQLite persistence、localhost-only binding 與 failure recovery UAT 亦已在實機通過
- Watcher integration：`POST /v1/notification/event` ingress 已實作；M2 `POST /v1/text` 已透過真實 Pi 上的 Teacher Core 完成兩輪 conversation/session reuse 驗收；M3.0 `POST /v2/watcher/talk/audio_stream` 已由 stock Watcher 真機驗證 upload、200 response、`screen_text` 顯示與 WAV 播放
- ElevenLabs TTS：已選為 M3.1 目標 provider；M3.0 僅使用 deterministic WAV 驗證 stock transport/presentation，尚未把 provider TTS 接入 Watcher voice round-trip
- Hardware UAT：M1.1 已驗證 reboot 後 ingress 與 real human-detection alarm；M1.2 已驗證 pinned Teacher Core install、health、Groq direct conversation、SQLite reboot persistence、localhost-only listener 與 failure recovery；M2 已驗證 edge → Teacher Core → assistant text 的 live Pi round-trip；M3.0 已在 PR #15 head `6a6aa096fee2a522cf549a8ae835cf2a191a6d31` 驗證 stock Watcher PTT → authenticated audio upload → `200 OK` → 2 秒 deterministic tone + `Teacher Edge audio transport test` 畫面顯示
- Next：Issue #10 / M3.1 才會接上 Teacher STT、Teacher conversation、ElevenLabs TTS，形成真正的 Watcher 語音 Teacher round-trip

詳見 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)、[`docs/INTEGRATION_CONTRACT.md`](docs/INTEGRATION_CONTRACT.md)、[`docs/ROADMAP.md`](docs/ROADMAP.md) 與 [`docs/UAT.md`](docs/UAT.md)。

## Run the M1 ingress on Raspberry Pi

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

The bridge only validates, normalizes, and logs non-secret event metadata in M1,
then acknowledges a successful notification with `{"code":200}`. It does not call
Teacher Core, persist events, or send an outbound rendered response to the Watcher.

For reboot-safe Raspberry Pi installation and operational commands, see
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).
