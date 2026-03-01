# 🌸 OpenWendy v2

Standalone AI pipeline runtime with browser-based dashboard.

## Quick Start

```bash
git clone <repo>
cd openwendy
pip install -r requirements.txt
python main.py
```

→ Opens browser at `http://localhost:18888`
→ First launch: onboarding wizard (model setup + channel config)
→ After setup: pipeline dashboard with Drawflow editor

## Features

- **Visual Pipeline Editor** — Drag & drop nodes (Input, Wendy LLM, Filter, Voice TTS, Image Gen, etc.)
- **Multi-Model Support** — Cloud (OpenAI, Anthropic, OpenRouter, DeepSeek) or local (vLLM)
- **Telegram/Discord Bot** — Connect your pipeline to chat channels
- **Live Logs** — SSE-based real-time log streaming
- **Save/Load Pipelines** — JSON-based pipeline storage

## Architecture

```
openwendy/
├── main.py              # Entry point
├── server/app.py        # FastAPI server (port 18888)
├── server/static/       # Frontend (wizard + dashboard)
├── runtime/gateway.py   # Bot runner
├── runtime/runner.py    # Pipeline executor
├── runtime/nodes/       # Node handlers
├── config/schema.py     # Pydantic config
└── pipelines/           # Saved pipeline JSONs
```

Config stored at `~/.openwendy/config.json`.
