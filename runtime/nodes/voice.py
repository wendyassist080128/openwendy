"""Voice TTS node — ElevenLabs."""
import httpx
import tempfile

async def handle_voice(node_config: dict, inputs: list[str], context: dict) -> str:
    config = context.get("config")
    if not config or not config.elevenlabs.apiKey:
        return ""
    text = "\n".join(i for i in inputs if i)
    if not text.strip():
        return ""
    voice_id = node_config.get("voice_id", config.elevenlabs.voiceId)
    model_id = node_config.get("tts_model", config.elevenlabs.model)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json={"text": text[:5000], "model_id": model_id, "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}, headers={"xi-api-key": config.elevenlabs.apiKey, "Content-Type": "application/json"})
        resp.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False, dir="/tmp")
    tmp.write(resp.content)
    tmp.close()
    return tmp.name
