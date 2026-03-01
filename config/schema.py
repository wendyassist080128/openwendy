"""OpenWendy v2 configuration schema."""
from __future__ import annotations
import json
from pathlib import Path
from pydantic import BaseModel, Field

CONFIG_PATH = Path.home() / ".openwendy" / "config.json"


class CloudProvider(BaseModel):
    provider: str = "openai"
    apiKey: str = ""
    model: str = "gpt-4o"


class LocalProvider(BaseModel):
    apiBase: str = "http://localhost:8000/v1"
    apiKey: str = "dummy"
    model: str = "qwen2.5-72b"


class Providers(BaseModel):
    cloud: CloudProvider = Field(default_factory=CloudProvider)
    local: LocalProvider = Field(default_factory=LocalProvider)
    active: str = "local"


class TelegramConfig(BaseModel):
    enabled: bool = False
    token: str = ""


class DiscordConfig(BaseModel):
    enabled: bool = False
    token: str = ""


class ChannelsConfig(BaseModel):
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    discord: DiscordConfig = Field(default_factory=DiscordConfig)


class ElevenLabs(BaseModel):
    apiKey: str = ""
    voiceId: str = "zGjIP4SZlMnY9m93k97r"
    model: str = "eleven_v3"


class Config(BaseModel):
    providers: Providers = Field(default_factory=Providers)
    channels: ChannelsConfig = Field(default_factory=ChannelsConfig)
    elevenlabs: ElevenLabs = Field(default_factory=ElevenLabs)
    onboarded: bool = False

    @classmethod
    def load(cls) -> Config:
        if CONFIG_PATH.exists():
            return cls.model_validate(json.loads(CONFIG_PATH.read_text()))
        return cls()

    def save(self):
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(self.model_dump(), indent=2, ensure_ascii=False))
