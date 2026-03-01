"""OpenWendy v2 — FastAPI server."""
from __future__ import annotations
import json
import subprocess
import signal
import sys
import os
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.schema import Config, CONFIG_PATH

app = FastAPI(title="OpenWendy v2")

STATIC_DIR = Path(__file__).parent / "static"
PIPELINES_DIR = Path(__file__).resolve().parent.parent / "pipelines"
PIPELINES_DIR.mkdir(exist_ok=True)

# Runtime process state
_runtime_proc = None
_log_lines: list[str] = []
_log_subscribers: list[asyncio.Queue] = []


# ── Static files ──
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Root ──
@app.get("/", response_class=HTMLResponse)
async def root():
    config = Config.load()
    if config.onboarded:
        return RedirectResponse("/dashboard")
    return (STATIC_DIR / "index.html").read_text()


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return (STATIC_DIR / "dashboard.html").read_text()


# ── Config API ──
@app.get("/api/config")
async def get_config():
    config = Config.load()
    return config.model_dump()


@app.post("/api/config/save")
async def save_config(request: Request):
    data = await request.json()
    config = Config.model_validate(data)
    config.save()
    return {"ok": True}


# ── Pipelines API ──
@app.get("/api/pipelines")
async def list_pipelines():
    files = sorted(PIPELINES_DIR.glob("*.json"))
    return [f.stem for f in files]


@app.get("/api/pipelines/{name}")
async def get_pipeline(name: str):
    f = PIPELINES_DIR / f"{name}.json"
    if not f.exists():
        return JSONResponse({"error": "not found"}, 404)
    return json.loads(f.read_text())


@app.post("/api/pipelines/{name}")
async def save_pipeline(name: str, request: Request):
    data = await request.json()
    f = PIPELINES_DIR / f"{name}.json"
    f.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return {"ok": True}


@app.delete("/api/pipelines/{name}")
async def delete_pipeline(name: str):
    f = PIPELINES_DIR / f"{name}.json"
    if f.exists():
        f.unlink()
    return {"ok": True}


# ── Runtime API ──
@app.post("/api/runtime/start")
async def runtime_start(request: Request):
    global _runtime_proc, _log_lines
    if _runtime_proc and _runtime_proc.poll() is None:
        return {"ok": True, "pid": _runtime_proc.pid, "already": True}

    body = await request.json() if (await request.body()) else {}
    pipeline_name = body.get("pipeline", "default")
    pipeline_path = PIPELINES_DIR / f"{pipeline_name}.json"

    # Ensure default pipeline exists
    if not pipeline_path.exists():
        _ensure_default_pipeline()
        pipeline_path = PIPELINES_DIR / "default.json"

    _log_lines = []
    gateway_py = Path(__file__).resolve().parent.parent / "runtime" / "gateway.py"
    _runtime_proc = subprocess.Popen(
        [sys.executable, str(gateway_py), "--pipeline", str(pipeline_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=str(Path(__file__).resolve().parent.parent),
    )

    # Background log reader
    asyncio.get_event_loop().run_in_executor(None, _read_logs)
    return {"ok": True, "pid": _runtime_proc.pid}


@app.post("/api/runtime/stop")
async def runtime_stop():
    global _runtime_proc
    if _runtime_proc and _runtime_proc.poll() is None:
        _runtime_proc.send_signal(signal.SIGTERM)
        _runtime_proc.wait(timeout=5)
        _broadcast_log("[OpenWendy] Runtime stopped.")
    _runtime_proc = None
    return {"ok": True}


@app.get("/api/runtime/status")
async def runtime_status():
    running = _runtime_proc is not None and _runtime_proc.poll() is None
    return {"running": running, "pid": _runtime_proc.pid if running else None}


@app.get("/api/runtime/logs")
async def runtime_logs():
    queue: asyncio.Queue = asyncio.Queue()
    _log_subscribers.append(queue)

    async def event_stream():
        # Send existing logs
        for line in _log_lines[-200:]:
            yield f"data: {line}\n\n"
        try:
            while True:
                line = await asyncio.wait_for(queue.get(), timeout=30)
                yield f"data: {line}\n\n"
        except asyncio.TimeoutError:
            yield "data: [keepalive]\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if queue in _log_subscribers:
                _log_subscribers.remove(queue)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _read_logs():
    global _runtime_proc
    if not _runtime_proc:
        return
    try:
        for line in iter(_runtime_proc.stdout.readline, ""):
            if not line:
                break
            line = line.rstrip()
            _broadcast_log(line)
    except Exception:
        pass
    _broadcast_log("[OpenWendy] Process exited.")


def _broadcast_log(line: str):
    _log_lines.append(line)
    if len(_log_lines) > 2000:
        _log_lines[:] = _log_lines[-1000:]
    for q in list(_log_subscribers):
        try:
            q.put_nowait(line)
        except Exception:
            pass


def _ensure_default_pipeline():
    f = PIPELINES_DIR / "default.json"
    if not f.exists():
        default = {
            "name": "Default",
            "nodes": [
                {"id": "1", "type": "input", "label": "Input", "config": {"source": "ChatApp", "type": "text"}, "pos_x": 50, "pos_y": 200},
                {"id": "2", "type": "wendy", "label": "Wendy", "config": {"role": "main", "model": "auto", "prompt": "You are Wendy, a helpful AI assistant."}, "pos_x": 320, "pos_y": 200},
                {"id": "3", "type": "output", "label": "Output", "config": {"target": "ChatApp", "format": "text"}, "pos_x": 590, "pos_y": 200},
            ],
            "edges": [
                {"from": "1", "to": "2"},
                {"from": "2", "to": "3"},
            ],
        }
        f.write_text(json.dumps(default, indent=2))


def start_server(port: int = 18888):
    _ensure_default_pipeline()
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
